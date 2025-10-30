from PIL import Image, ImageOps
import os
import concurrent.futures
from typing import List, Tuple, Optional, Callable
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ResizeMode:
    FIT = "fit"
    FILL = "fill"
    CROP = "crop"
    STRETCH = "stretch"

def get_image_files_from_folder(folder_path: str) -> List[str]:
    """
    Get all image files from a folder.
    
    :param folder_path: Path to the folder containing images
    :return: List of image file paths
    """
    supported_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp', '.gif'}
    image_files = []
    
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if os.path.splitext(file.lower())[1] in supported_extensions:
                image_files.append(os.path.join(root, file))
    
    return image_files

def calculate_dimensions(original_size: Tuple[int, int], target_size: Tuple[int, int], 
                        mode: str = ResizeMode.FIT, preserve_aspect: bool = True) -> Tuple[int, int]:
    """
    Calculate output dimensions based on resize mode and aspect ratio settings.
    
    :param original_size: Original (width, height)
    :param target_size: Target (width, height)
    :param mode: Resize mode (fit, fill, crop, stretch)
    :param preserve_aspect: Whether to preserve aspect ratio
    :return: Final (width, height)
    """
    orig_w, orig_h = original_size
    target_w, target_h = target_size
    
    if mode == ResizeMode.STRETCH or not preserve_aspect:
        return target_w, target_h
    
    orig_ratio = orig_w / orig_h
    target_ratio = target_w / target_h
    
    if mode == ResizeMode.FIT:
        if orig_ratio > target_ratio:
            return target_w, int(target_w / orig_ratio)
        else:
            return int(target_h * orig_ratio), target_h
    
    elif mode == ResizeMode.FILL:
        if orig_ratio > target_ratio:
            return int(target_h * orig_ratio), target_h
        else:
            return target_w, int(target_w / orig_ratio)
    
    elif mode == ResizeMode.CROP:
        if orig_ratio > target_ratio:
            crop_h = int(orig_w / target_ratio)
            return target_w, target_h
        else:
            crop_w = int(orig_h * target_ratio)
            return target_w, target_h
    
    return target_w, target_h

def resize_single_image(image_path: str, output_path: str, width: int, height: int, 
                       quality: int = 85, format: str = 'JPEG', mode: str = ResizeMode.FIT,
                       preserve_aspect: bool = True, preserve_metadata: bool = False,
                       crop_box: Optional[Tuple[int, int, int, int]] = None) -> bool:
    """
    Resize a single image with advanced options.
    
    :param image_path: Path to input image
    :param output_path: Path to save resized image
    :param width: Target width
    :param height: Target height
    :param quality: JPEG quality (0-100)
    :param format: Output format
    :param mode: Resize mode
    :param preserve_aspect: Whether to preserve aspect ratio
    :param preserve_metadata: Whether to preserve EXIF metadata
    :return: Success status
    """
    try:
        with Image.open(image_path) as img:
            original_size = img.size
            
            # Handle transparency for JPEG output
            if format.upper() == 'JPEG' and img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            
            # Apply explicit crop box if provided
            if crop_box is not None:
                try:
                    # Ensure box is within image bounds
                    l, t, r, b = crop_box
                    l = max(0, min(l, img.width))
                    t = max(0, min(t, img.height))
                    r = max(l, min(r, img.width))
                    b = max(t, min(b, img.height))
                    img = img.crop((l, t, r, b))
                except Exception as e:
                    logger.warning(f"Invalid crop box {crop_box} for {image_path}: {e}")

            # Calculate dimensions after optional crop
            final_size = calculate_dimensions(img.size, (width, height), mode, preserve_aspect)

            # Resize based on mode
            if mode == ResizeMode.CROP and crop_box is None:
                # Crop to aspect ratio first, then resize
                img = ImageOps.fit(img, final_size, Image.Resampling.LANCZOS)
            else:
                img = img.resize(final_size, Image.Resampling.LANCZOS)
            
            # Prepare save options
            save_kwargs = {'format': format}
            if format.upper() == 'JPEG':
                save_kwargs['quality'] = quality
                save_kwargs['optimize'] = True
            elif format.upper() == 'PNG':
                save_kwargs['optimize'] = True
            elif format.upper() == 'WEBP':
                save_kwargs['quality'] = quality
                save_kwargs['optimize'] = True
            
            # Preserve metadata if requested
            if preserve_metadata and hasattr(img, 'info'):
                save_kwargs.update(img.info)
            
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            img.save(output_path, **save_kwargs)
            logger.info(f"Successfully resized {image_path} to {final_size}")
            return True
            
    except Exception as e:
        logger.error(f"Error resizing {image_path}: {e}")
        return False

def resize_images(image_files: List[str], output_dir: str, width: int, height: int, 
                  quality: int = 85, format: str = 'JPEG', mode: str = ResizeMode.FIT,
                  preserve_aspect: bool = True, preserve_metadata: bool = False,
                  naming_pattern: str = "{name}_resized", max_workers: int = None,
                  progress_callback: Optional[Callable] = None,
                  crop_boxes: Optional[dict] = None) -> List[str]:
    """
    Resize a list of images with advanced options and parallel processing.

    :param image_files: List of file paths to images
    :param output_dir: Directory to save resized images
    :param width: Target width
    :param height: Target height
    :param quality: JPEG quality (0-100)
    :param format: Output format ('JPEG', 'PNG', 'WEBP')
    :param mode: Resize mode (fit, fill, crop, stretch)
    :param preserve_aspect: Whether to preserve aspect ratio
    :param preserve_metadata: Whether to preserve EXIF metadata
    :param naming_pattern: Naming pattern for output files
    :param max_workers: Maximum number of worker threads
    :param progress_callback: Optional callback for progress updates
    :return: List of successfully resized file paths
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    resized_files = []
    total_files = len(image_files)
    
    # Determine number of workers
    if max_workers is None:
        max_workers = min(4, os.cpu_count() or 2)
    
    def process_image(image_path: str) -> Optional[str]:
        base_name = os.path.basename(image_path)
        name, ext = os.path.splitext(base_name)
        
        # Apply naming pattern
        try:
            output_name = naming_pattern.format(
                name=name,
                original_name=base_name,
                index=image_files.index(image_path) + 1,
                width=width,
                height=height
            )
        except KeyError:
            output_name = f"{name}_resized"
        
        output_path = os.path.join(output_dir, f"{output_name}.{format.lower()}")
        
        # Map a crop box, if provided, either by full path or by base name
        crop_box = None
        if crop_boxes:
            crop_box = crop_boxes.get(image_path) or crop_boxes.get(base_name)

        success = resize_single_image(
            image_path, output_path, width, height, quality, format,
            mode, preserve_aspect, preserve_metadata, crop_box
        )
        
        if success:
            return output_path
        return None
    
    # Process images in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_path = {executor.submit(process_image, img_path): img_path for img_path in image_files}
        
        for i, future in enumerate(concurrent.futures.as_completed(future_to_path)):
            result = future.result()
            if result:
                resized_files.append(result)
            
            # Update progress
            if progress_callback:
                progress_callback(i + 1, total_files)
    
    logger.info(f"Successfully resized {len(resized_files)}/{total_files} images")
    return resized_files

def resize_folder(folder_path: str, output_dir: str, width: int, height: int,
                  quality: int = 85, format: str = 'JPEG', mode: str = ResizeMode.FIT,
                  preserve_aspect: bool = True, preserve_metadata: bool = False,
                  naming_pattern: str = "{name}_resized", max_workers: int = None,
                  progress_callback: Optional[Callable] = None) -> List[str]:
    """
    Resize all images in a folder with advanced options.

    :param folder_path: Path to the folder containing images
    :param output_dir: Directory to save resized images
    :param width: Target width
    :param height: Target height
    :param quality: JPEG quality (0-100)
    :param format: Output format ('JPEG', 'PNG', 'WEBP')
    :param mode: Resize mode (fit, fill, crop, stretch)
    :param preserve_aspect: Whether to preserve aspect ratio
    :param preserve_metadata: Whether to preserve EXIF metadata
    :param naming_pattern: Naming pattern for output files
    :param max_workers: Maximum number of worker threads
    :param progress_callback: Optional callback for progress updates
    :return: List of successfully resized file paths
    """
    image_files = get_image_files_from_folder(folder_path)
    return resize_images(
        image_files, output_dir, width, height, quality, format, mode,
        preserve_aspect, preserve_metadata, naming_pattern, max_workers, progress_callback
    )

def get_image_info(image_path: str) -> dict:
    """
    Get detailed information about an image.
    
    :param image_path: Path to the image file
    :return: Dictionary with image information
    """
    try:
        with Image.open(image_path) as img:
            return {
                'path': image_path,
                'format': img.format,
                'mode': img.mode,
                'size': img.size,
                'file_size': os.path.getsize(image_path),
                'has_transparency': img.mode in ('RGBA', 'LA') or 'transparency' in img.info
            }
    except Exception as e:
        logger.error(f"Error getting info for {image_path}: {e}")
        return {}
