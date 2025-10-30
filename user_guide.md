# Advanced Image Resizer User Guide

## Overview

This application allows you to resize multiple images at once using a powerful web interface built with Streamlit. It supports various image formats and provides advanced options for customizing the output size, quality, format, and processing behavior.

## Features

### Core Features

- Upload multiple images simultaneously or entire folders as ZIP
- Multiple resize modes: Fit, Fill, Crop, and Stretch
- Aspect ratio preservation options
- Custom naming patterns for output files
- Parallel processing for faster batch operations
- Real-time progress tracking

### Advanced Options

- Metadata preservation (EXIF data)
- Custom naming patterns with variables
- Adjustable parallel worker threads
- Multiple output formats (JPEG, PNG, WEBP)
- Quality control for lossy formats
- Support for transparency handling

### User Interface

- Intuitive two-column layout
- Image preview before processing
- Progress bar with percentage
- Individual and batch download options
- Responsive design for various screen sizes

## Installation

1. Ensure you have Python 3.8+ installed.
2. Clone or download the project files.
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Basic Usage

1. Run the application:
   ```bash
   streamlit run app.py
   ```
2. Open the provided URL in your browser (usually http://localhost:8501).
3. Choose your input method:
   - **Upload individual files**: Select multiple images directly
   - **Upload folder as ZIP**: Upload a ZIP file containing images
4. Configure basic settings:
   - **Width/Height**: Target dimensions in pixels
   - **Resize Mode**: How to fit images to target dimensions
   - **Output Format**: JPEG, PNG, or WEBP
   - **Quality**: Compression quality (1-100 for JPEG/WEBP)
5. Click "🚀 Resize Images" to process.
6. Download results individually or as a ZIP file.

### Advanced Settings (Sidebar)

#### Resize Modes

- **📐 Fit**: Fit image within dimensions, preserving aspect ratio
- **🔲 Fill**: Fill dimensions, may crop parts of the image
- **✂️ Crop**: Crop to exact dimensions, preserving aspect ratio
- **↔️ Stretch**: Stretch to exact dimensions, may distort image

#### Naming Patterns

Available variables for custom naming:

- `{name}`: Original filename without extension
- `{original_name}`: Complete original filename
- `{index}`: Sequential number (starting from 1)
- `{width}`: Target width
- `{height}`: Target height

Example patterns:

- `{name}_resized` → `photo_resized.jpg`
- `{name}_{width}x{height}` → `photo_800x600.jpg`
- `img_{index:03d}` → `img_001.jpg`, `img_002.jpg`

#### Performance Settings

- **Parallel Workers**: Number of threads (1-8) for processing
- **Preserve Aspect Ratio**: Maintain original proportions
- **Preserve Metadata**: Keep EXIF data and other metadata

## Supported Formats

### Input Formats

- JPEG (.jpg, .jpeg)
- PNG (.png)
- BMP (.bmp)
- TIFF (.tiff)
- WEBP (.webp)
- GIF (.gif)

### Output Formats

- JPEG: Best for photographs, supports quality control
- PNG: Best for graphics with transparency, lossless
- WEBP: Modern format with good compression and quality

## Performance Tips

1. **Parallel Processing**: Increase worker threads for faster batch processing
2. **File Size**: Large images (>10MB) may take longer to process
3. **Batch Size**: For optimal performance, process 50-100 images at a time
4. **Memory Usage**: Monitor system memory when processing many large images

## Troubleshooting

### Common Issues

1. **Memory Errors**: Reduce parallel workers or process smaller batches
2. **Slow Processing**: Check if images are very large or if system resources are limited
3. **Format Issues**: Ensure input files are valid image formats
4. **Permission Errors**: Check write permissions for the output directory

### Error Messages

- "Please upload at least one image": No files were selected
- "File not found": Output file was not created successfully
- "Error resizing [filename]": Specific image processing error

## Technical Details

### Image Processing

- Uses PIL/Pillow library with LANCZOS resampling
- High-quality image processing with optimization
- Automatic transparency handling for incompatible formats
- Memory-efficient processing for large batches

### File Management

- Temporary files are automatically cleaned up
- Output directory: `resized_images/`
- ZIP files are created for easy batch downloads
- Original files are never modified

## Keyboard Shortcuts

- **Tab**: Navigate between form fields
- **Enter**: Submit form when focused on button
- **Space**: Toggle checkboxes

## Browser Compatibility

Works best with modern browsers:

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Updates and Support

The application includes:

- Automatic error logging
- Progress tracking for long operations
- Responsive design for mobile devices
- Accessibility features

For issues or feature requests, check the application logs or contact support.
