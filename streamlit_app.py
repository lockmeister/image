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

def transform_color(pixel, target_color):
    """Transform a pixel's color while preserving its relative brightness."""
    if isinstance(pixel, int):  # Handle grayscale images
        brightness = pixel / 255
        return tuple(int(brightness * c) for c in target_color)
    
    r, g, b = pixel[:3]
    brightness = (r + g + b) / (255 * 3)
    
    new_r = int(target_color[0] * brightness)
    new_g = int(target_color[1] * brightness)
    new_b = int(target_color[2] * brightness)
    
    if len(pixel) > 3:
        return (new_r, new_g, new_b, pixel[3])
    return (new_r, new_g, new_b)

def process_image(img, target_color):
    """Process a single image, changing its color while preserving gradients."""
    if img.mode not in ('RGB', 'RGBA'):
        img = img.convert('RGB')
        
    width, height = img.size
    new_img = Image.new(img.mode, (width, height))
    
    for x in range(width):
        for y in range(height):
            pixel = img.getpixel((x, y))
            new_pixel = transform_color(pixel, target_color)
            new_img.putpixel((x, y), new_pixel)
    
    return new_img

st.title("Bitmap Color Transformer")
st.write("Upload an image and choose a new color to transform it while preserving gradients.")

# Color picker
color = st.color_picker("Choose target color", "#FF0000")
# Convert hex color to RGB
target_color = tuple(int(color[i:i+2], 16) for i in (1, 3, 5))

# File uploader
uploaded_file = st.file_uploader("Choose an image file", type=['png', 'jpg', 'jpeg', 'bmp'])

if uploaded_file is not None:
    # Display original image
    original_img = Image.open(uploaded_file)
    st.write("Original Image:")
    st.image(original_img)
    
    # Process and display transformed image
    transformed_img = process_image(original_img, target_color)
    st.write("Transformed Image:")
    st.image(transformed_img)
    
    # Add download button
    buf = io.BytesIO()
    transformed_img.save(buf, format='PNG')
    st.download_button(
        label="Download transformed image",
        data=buf.getvalue(),
        file_name="transformed_image.png",
        mime="image/png"
    )
