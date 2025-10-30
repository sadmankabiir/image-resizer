import streamlit as st
from image_resizer import resize_images, resize_folder, ResizeMode, get_image_info
from config import get_config, get_resize_mode_info, get_all_resize_modes, NAMING_PATTERNS
import tempfile
import os
import zipfile
import time
from typing import List

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
    st.session_state.resized_files = []

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
        cols = st.columns(min(4, len(uploaded_files)))
        for i, file in enumerate(uploaded_files):
            with cols[i % 4]:
                st.image(file, caption=file.name, use_column_width=True)
    
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
        with tempfile.TemporaryDirectory() as temp_dir:
            image_paths = []
            for uploaded_file in uploaded_files:
                temp_path = os.path.join(temp_dir, uploaded_file.name)
                with open(temp_path, 'wb') as f:
                    f.write(uploaded_file.getbuffer())
                image_paths.append(temp_path)

            output_dir = "resized_images"
            
            # Update progress
            status_text.text("🔄 Processing images...")
            
            resized_files = resize_images(
                image_paths, output_dir, width, height, quality, format_option,
                selected_mode, preserve_aspect, preserve_metadata, naming_pattern,
                max_workers, progress_callback
            )
            
            st.session_state.resized_files = resized_files
            st.session_state.processing = False
            st.session_state.progress = 1.0
            progress_bar.progress(1.0)
            st.rerun()
    
    elif input_method == "Upload folder as ZIP" and folder_uploaded:
        with tempfile.TemporaryDirectory() as temp_dir:
            # Extract ZIP file
            status_text.text("📂 Extracting ZIP file...")
            with zipfile.ZipFile(uploaded_folder, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            output_dir = "resized_images"
            
            # Update progress
            status_text.text("🔄 Processing images...")
            
            resized_files = resize_folder(
                temp_dir, output_dir, width, height, quality, format_option,
                selected_mode, preserve_aspect, preserve_metadata, naming_pattern,
                max_workers, progress_callback
            )
            
            st.session_state.resized_files = resized_files
            st.session_state.processing = False
            st.session_state.progress = 1.0
            progress_bar.progress(1.0)
            st.rerun()

# Show results
if st.session_state.resized_files and not st.session_state.processing:
    st.success(f"✅ Successfully resized {len(st.session_state.resized_files)} images!")
    
    # Create ZIP for all files
    output_dir = "resized_images"
    zip_path = os.path.join(output_dir, "all_resized_images.zip")
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for resized_file in st.session_state.resized_files:
            zipf.write(resized_file, os.path.basename(resized_file))

    # Download all as ZIP button
    col1, col2 = st.columns([1, 1])
    with col1:
        with open(zip_path, 'rb') as f:
            st.download_button(
                label="📦 Download All as ZIP",
                data=f,
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
    for i, resized_file in enumerate(st.session_state.resized_files):
        with cols[i % 3]:
            try:
                with open(resized_file, 'rb') as f:
                    st.download_button(
                        label=f"📥 {os.path.basename(resized_file)}",
                        data=f,
                        file_name=os.path.basename(resized_file),
                        mime="image/*"
                    )
            except FileNotFoundError:
                st.error(f"File not found: {os.path.basename(resized_file)}")

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
