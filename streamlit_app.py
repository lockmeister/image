# streamlit_app.py

# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "streamlit",
#     "pillow",
# ]
# ///

import streamlit as st
from PIL import Image
import io
import zipfile
import time
from pathlib import Path

# Initialize session state variables if they don't exist
if 'processed_images' not in st.session_state:
    st.session_state.processed_images = {}
if 'current_color' not in st.session_state:
    st.session_state.current_color = "#FF0000"

@st.cache_data
def transform_color(pixel, target_color):
    """Transform a pixel's color while preserving white and transparency."""
    # Check if pixel is pure white (RGB 255,255,255)
    if isinstance(pixel, int):  # Handle grayscale images
        if pixel == 255:
            return 255
        brightness = pixel / 255
        return tuple(int(brightness * c) for c in target_color)
    
    # Handle RGBA images
    if len(pixel) == 4:
        r, g, b, a = pixel
        if r == 255 and g == 255 and b == 255:
            return (255, 255, 255, a)  # Preserve white with alpha
        brightness = (r + g + b) / (255 * 3)
        new_r = int(target_color[0] * brightness)
        new_g = int(target_color[1] * brightness)
        new_b = int(target_color[2] * brightness)
        return (new_r, new_g, new_b, a)
    
    # Handle RGB images
    r, g, b = pixel[:3]
    if r == 255 and g == 255 and b == 255:
        return (255, 255, 255)  # Preserve white
    brightness = (r + g + b) / (255 * 3)
    new_r = int(target_color[0] * brightness)
    new_g = int(target_color[1] * brightness)
    new_b = int(target_color[2] * brightness)
    return (new_r, new_g, new_b)

def process_image(img, target_color, progress_callback=None):
    """Process a single image, changing its color while preserving gradients."""
    try:
        # Convert to RGBA if image has transparency, otherwise to RGB
        if img.mode not in ('RGB', 'RGBA'):
            if img.mode in ('P', 'LA', 'PA'):
                img = img.convert('RGBA')
            else:
                img = img.convert('RGB')
            
        width, height = img.size
        new_img = Image.new(img.mode, (width, height))
        
        total_pixels = width * height
        for y in range(height):
            for x in range(width):
                pixel = img.getpixel((x, y))
                new_pixel = transform_color(pixel, target_color)
                new_img.putpixel((x, y), new_pixel)
            
            if progress_callback and y % 10 == 0:  # Update progress every 10 rows
                progress = (y * width * 100) / total_pixels
                progress_callback(progress)
                
        return new_img
    except Exception as e:
        st.error(f"Error processing image: {str(e)}")
        return None

def main():
    # Set page config for a wider layout
    st.set_page_config(
        page_title="Batch Image Color Transformer",
        page_icon="🎨",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    st.title("Batch Image Color Transformer")
    st.write("Upload multiple images and transform them all at once while preserving gradients.")

    # Color picker
    color = st.color_picker("Choose target color", st.session_state.current_color)
    
    # Check if color changed
    if color != st.session_state.current_color:
        st.session_state.current_color = color
        st.session_state.processed_images = {}  # Clear cached processed images
    
    # Convert hex color to RGB
    target_color = tuple(int(color[i:i+2], 16) for i in (1, 3, 5))

    # File uploader for bitmap files
    uploaded_files = st.file_uploader(
        "Choose bitmap (.bmp) files",
        type=['bmp'],
        accept_multiple_files=True,
        help="Select multiple .bmp files by holding Ctrl/Cmd while clicking"
    )

    if uploaded_files:
        # Process all images
        with st.spinner("Processing images..."):
            # Create a progress bar for overall progress
            overall_progress = st.progress(0)
            current_file_progress = st.progress(0)
            status_text = st.empty()
            
            processed_images = []
            
            # Create columns for the grid layout
            cols = st.columns(3)
            
            for idx, uploaded_file in enumerate(uploaded_files):
                # Update status
                status_text.text(f"Processing {uploaded_file.name} ({idx + 1}/{len(uploaded_files)})")
                
                # Check if image is already processed with current color
                cache_key = (uploaded_file.name, color)
                if cache_key not in st.session_state.processed_images:
                    # Process image
                    original_img = Image.open(uploaded_file)
                    
                    def update_progress(progress):
                        current_file_progress.progress(int(progress))
                    
                    transformed_img = process_image(original_img, target_color, update_progress)
                    
                    if transformed_img:
                        # Store in session state
                        img_byte_arr = io.BytesIO()
                        transformed_img.save(img_byte_arr, format='BMP')
                        st.session_state.processed_images[cache_key] = {
                            'original': original_img,
                            'transformed': transformed_img,
                            'bytes': img_byte_arr.getvalue(),
                            'format': 'BMP'
                        }
                
                if cache_key in st.session_state.processed_images:
                    # Get from cache
                    img_data = st.session_state.processed_images[cache_key]
                    processed_images.append((
                        uploaded_file.name,
                        img_data['bytes'],
                        img_data['format']
                    ))
                    
                    # Display in grid
                    col_idx = idx % 3
                    with cols[col_idx]:
                        st.write(f"Image {idx + 1}: {uploaded_file.name}")
                        st.image(img_data['original'], caption="Original", use_column_width=True)
                        st.image(img_data['transformed'], caption="Transformed", use_column_width=True)
                        
                        # Individual download button
                        st.download_button(
                            label=f"Download {uploaded_file.name}",
                            data=img_data['bytes'],
                            file_name=f"transformed_{uploaded_file.name}",
                            mime="image/bmp"
                        )
                
                # Update overall progress
                overall_progress.progress(int((idx + 1) * 100 / len(uploaded_files)))
                
            # Clear progress indicators
            time.sleep(0.5)  # Small delay to show completion
            status_text.empty()
            overall_progress.empty()
            current_file_progress.empty()
            
            # Create zip file containing all processed images
            if len(processed_images) > 1:
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                    for filename, image_data, _ in processed_images:
                        zip_file.writestr(f"transformed_{filename}", image_data)
                
                # Add download button for zip file
                st.download_button(
                    label="📦 Download all transformed images (ZIP)",
                    data=zip_buffer.getvalue(),
                    file_name="transformed_images.zip",
                    mime="application/zip",
                )

if __name__ == "__main__":
    main()
