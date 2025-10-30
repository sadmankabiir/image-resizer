import streamlit as st
from image_resizer import resize_images, resize_folder, ResizeMode, get_image_info
from config import get_config, get_resize_mode_info, get_all_resize_modes, NAMING_PATTERNS
import tempfile
import os
import zipfile
import time
from typing import List
import hashlib
from PIL import Image
from io import BytesIO
try:
    from streamlit_cropper import st_cropper
except Exception:
    st_cropper = None

st.set_page_config(
    page_title="Advanced Image Resizer",
    page_icon="🖼️",
    layout="wide"
)

st.title("🖼️ Advanced Image Resizer")
st.markdown("---")

# Initialize session state
if 'processing' not in st.session_state:
    st.session_state.processing = False
if 'progress' not in st.session_state:
    st.session_state.progress = 0
if 'resized_files' not in st.session_state:
    # Store resized images in memory: list of (filename, bytes)
    st.session_state.resized_files = []
if 'cropped_images' not in st.session_state:
    # Mapping: original filename -> PNG bytes of cropped image
    st.session_state.cropped_images = {}
if 'temp_output_dir' not in st.session_state:
    # Temporary directory for processing (persists across reruns)
    st.session_state.temp_output_dir = None

# Sidebar for advanced settings
st.sidebar.title("⚙️ Advanced Settings")

# Input method selection
input_method = st.radio("Choose input method:", ["Upload individual files", "Upload folder as ZIP"])

uploaded_files = None
folder_uploaded = False

if input_method == "Upload individual files":
    config = get_config()
    uploaded_files = st.file_uploader(
        "Choose images", 
        accept_multiple_files=True, 
        type=config['ui']['supported_formats']
    )
else:
    uploaded_folder = st.file_uploader("Choose a ZIP file containing images", type=['zip'])
    folder_uploaded = uploaded_folder is not None

# Main settings column
col1, col2 = st.columns(2)

with col1:
    st.subheader("📏 Size Settings")
    width = st.number_input("Width", min_value=1, value=800, help="Target width in pixels")
    height = st.number_input("Height", min_value=1, value=600, help="Target height in pixels")
    
    # Resize mode selection
    resize_modes = get_all_resize_modes()
    mode_options = [f"{info['icon']} {info['name']}" for info in resize_modes.values()]
    selected_mode = st.selectbox(
        "Resize Mode", 
        options=list(resize_modes.keys()),
        format_func=lambda x: f"{resize_modes[x]['icon']} {resize_modes[x]['name']}",
        help="How the image should be resized to fit the target dimensions"
    )
    
    # Show mode description
    mode_info = get_resize_mode_info(selected_mode)
    st.caption(f"ℹ️ {mode_info['description']}")

with col2:
    st.subheader("🎨 Output Settings")
    quality = st.slider("Quality (for JPEG/WEBP)", min_value=1, max_value=100, value=85)
    format_option = st.selectbox("Output Format", ['JPEG', 'PNG', 'WEBP'])
    
    preserve_aspect = st.checkbox("Preserve Aspect Ratio", value=True, 
                                 help="Maintain the original aspect ratio")
    preserve_metadata = st.checkbox("Preserve Metadata", value=False,
                                  help="Keep EXIF data and other metadata")

# Advanced settings in sidebar
st.sidebar.subheader("🔧 Advanced Options")

# Naming pattern
naming_patterns = list(NAMING_PATTERNS.keys())
selected_pattern = st.sidebar.selectbox(
    "Naming Pattern",
    options=naming_patterns,
    help="How to name the output files"
)
naming_pattern = NAMING_PATTERNS[selected_pattern]

# Custom naming pattern
if selected_pattern == "Custom":
    custom_pattern = st.sidebar.text_input(
        "Custom Pattern",
        value="{name}_{width}x{height}_resized",
        help="Available variables: {name}, {original_name}, {index}, {width}, {height}"
    )
    naming_pattern = custom_pattern

# Performance settings
max_workers = st.sidebar.slider(
    "Parallel Workers",
    min_value=1,
    max_value=8,
    value=4,
    help="Number of parallel processing threads"
)

# Preview uploaded images
if uploaded_files or folder_uploaded:
    st.subheader("📋 Preview")
    
    if input_method == "Upload individual files" and uploaded_files:
        if selected_mode == ResizeMode.CROP:
            if st_cropper is None:
                st.warning("Interactive cropping requires 'streamlit-cropper'. Please install dependencies and reload.")
            else:
                st.info("Drag the crop frame for each image. It follows the selected width × height ratio.")
                
                # Ensure non-zero aspect; default to 1:1 if invalid
                ar_w = max(1, int(width))
                ar_h = max(1, int(height))
                
                # Render all croppers in sequence (streamlit-cropper doesn't work well in tabs)
                for i, file in enumerate(uploaded_files):
                    st.markdown("---")
                    st.markdown(f"### {i+1}. Adjust crop for: **{file.name}**")
                    
                    # Reset file pointer and load image fresh from bytes
                    file.seek(0)
                    img_bytes = file.read()
                    img = Image.open(BytesIO(img_bytes)).convert("RGB")
                    
                    # Create two columns: cropper on left, preview on right
                    col_crop, col_preview = st.columns([1, 1])
                    
                    with col_crop:
                        cropped_img = st_cropper(
                            img,
                            aspect_ratio=(ar_w, ar_h),
                            box_color='#FF6F61',
                            realtime_update=True,
                            return_type='image',
                            key=f"cropper_{i}_{hashlib.md5(file.name.encode('utf-8')).hexdigest()}"
                        )
                    
                    with col_preview:
                        if isinstance(cropped_img, Image.Image):
                            st.markdown("**Cropped Preview:**")
                            prev = cropped_img.copy()
                            st.image(prev, use_container_width=True)
                            # Persist cropped image (as PNG) for processing
                            buf = BytesIO()
                            prev.save(buf, format='PNG')
                            st.session_state.cropped_images[file.name] = buf.getvalue()
                        else:
                            # If the component returns a non-image (unexpected), clear stored crop
                            st.session_state.cropped_images.pop(file.name, None)
        else:
            cols = st.columns(min(4, len(uploaded_files)))
            for i, file in enumerate(uploaded_files):
                with cols[i % 4]:
                    st.image(file, caption=file.name, width='stretch')
    
    elif input_method == "Upload folder as ZIP" and folder_uploaded:
        st.info(f"📁 ZIP file uploaded: {uploaded_folder.name}")
        # Could extract and show preview here if needed

# Process button
if st.button("🚀 Resize Images", disabled=st.session_state.processing):
    if (input_method == "Upload individual files" and uploaded_files) or \
       (input_method == "Upload folder as ZIP" and folder_uploaded):
        
        st.session_state.processing = True
        st.session_state.progress = 0
        st.rerun()
    
    else:
        st.error("Please upload at least one image or a ZIP file containing images.")

# Show progress bar
if st.session_state.processing:
    progress_bar = st.progress(st.session_state.progress)
    status_text = st.empty()

    def progress_callback(current: int, total: int):
        progress = (current / total) if total else 0.0
        progress = max(0.0, min(progress, 1.0))
        st.session_state.progress = progress
        progress_bar.progress(progress)
        status_text.text(f'🔄 Processing... {int(progress * 100)}%')

    
    if input_method == "Upload individual files" and uploaded_files:
        with tempfile.TemporaryDirectory() as temp_input_dir:
            with tempfile.TemporaryDirectory() as temp_output_dir:
                image_paths = []
                for uploaded_file in uploaded_files:
                    temp_path = os.path.join(temp_input_dir, uploaded_file.name)
                    # Use cropped image bytes if in crop mode and available
                    if selected_mode == ResizeMode.CROP and uploaded_file.name in st.session_state.cropped_images:
                        data_bytes = st.session_state.cropped_images[uploaded_file.name]
                    else:
                        data_bytes = uploaded_file.getbuffer()
                    with open(temp_path, 'wb') as f:
                        f.write(data_bytes)
                    image_paths.append(temp_path)
                
                # Update progress
                status_text.text("🔄 Processing images...")
                
                # If crop mode and all images have pre-cropped versions, resize to exact size
                call_mode = selected_mode
                call_preserve_aspect = preserve_aspect
                if selected_mode == ResizeMode.CROP:
                    cropped_count = sum(1 for uf in uploaded_files if uf.name in st.session_state.cropped_images)
                    if cropped_count == len(uploaded_files) and len(uploaded_files) > 0:
                        call_mode = ResizeMode.STRETCH
                        call_preserve_aspect = False

                resized_file_paths = resize_images(
                    image_paths, temp_output_dir, width, height, quality, format_option,
                    call_mode, call_preserve_aspect, preserve_metadata, naming_pattern,
                    max_workers, progress_callback
                )
                
                # Load resized images into memory
                st.session_state.resized_files = []
                for file_path in resized_file_paths:
                    with open(file_path, 'rb') as f:
                        file_bytes = f.read()
                    filename = os.path.basename(file_path)
                    st.session_state.resized_files.append((filename, file_bytes))
                
                st.session_state.processing = False
                st.session_state.progress = 1.0
                progress_bar.progress(1.0)
                st.rerun()
    
    elif input_method == "Upload folder as ZIP" and folder_uploaded:
        with tempfile.TemporaryDirectory() as temp_input_dir:
            with tempfile.TemporaryDirectory() as temp_output_dir:
                # Extract ZIP file
                status_text.text("📂 Extracting ZIP file...")
                with zipfile.ZipFile(uploaded_folder, 'r') as zip_ref:
                    zip_ref.extractall(temp_input_dir)
                
                # Update progress
                status_text.text("🔄 Processing images...")
                
                resized_file_paths = resize_folder(
                    temp_input_dir, temp_output_dir, width, height, quality, format_option,
                    selected_mode, preserve_aspect, preserve_metadata, naming_pattern,
                    max_workers, progress_callback
                )
                
                # Load resized images into memory
                st.session_state.resized_files = []
                for file_path in resized_file_paths:
                    with open(file_path, 'rb') as f:
                        file_bytes = f.read()
                    filename = os.path.basename(file_path)
                    st.session_state.resized_files.append((filename, file_bytes))
                
                st.session_state.processing = False
                st.session_state.progress = 1.0
                progress_bar.progress(1.0)
                st.rerun()

# Show results
if st.session_state.resized_files and not st.session_state.processing:
    st.success(f"✅ Successfully resized {len(st.session_state.resized_files)} images!")
    
    # Create ZIP in memory for all files
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for filename, file_bytes in st.session_state.resized_files:
            zipf.writestr(filename, file_bytes)
    zip_buffer.seek(0)

    # Download all as ZIP button
    col1, col2 = st.columns([1, 1])
    with col1:
        st.download_button(
            label="📦 Download All as ZIP",
            data=zip_buffer.getvalue(),
            file_name="resized_images.zip",
            mime="application/zip"
        )
    
    with col2:
        if st.button("🗑️ Clear Results"):
            st.session_state.resized_files = []
            st.session_state.progress = 0
            st.rerun()

    st.divider()
    st.subheader("📥 Individual Downloads:")
    
    # Provide individual download links in a grid
    cols = st.columns(3)
    for i, (filename, file_bytes) in enumerate(st.session_state.resized_files):
        with cols[i % 3]:
            st.download_button(
                label=f"📥 {filename}",
                data=file_bytes,
                file_name=filename,
                mime="image/*",
                key=f"download_{i}_{filename}"
            )

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666;'>
        <p>🖼️ Advanced Image Resizer | Supports JPEG, PNG, WEBP, BMP, TIFF, GIF</p>
        <p>💡 Tip: Use the sidebar for advanced options like custom naming patterns and parallel processing</p>
    </div>
    """,
    unsafe_allow_html=True
)
