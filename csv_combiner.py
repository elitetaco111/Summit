import streamlit as st
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import io
import os
import zipfile
import pandas as pd

#TO RUN: streamlit run csv_combiner.py

# Ensure the script connects to the correct folders
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
GRAPHICS_FOLDER = os.path.join(CURRENT_DIR, "Graphics")
GARMENTS_FOLDER = os.path.join(CURRENT_DIR, "Garments")

# Adjustable pixels per inch value
PIXELS_PER_INCH = 96  # Default value, can be adjusted as needed

# Function to create and save an alpha mask
def save_alpha_mask(image, output_path):
    """
    Save the alpha mask of the given image.
    """
    alpha = image.split()[-1]  # Extract the alpha channel
    alpha.save(output_path)

# Function to process the CSV file
def process_csv(csv_file, apply_light_map, wrap_intensity):
    """
    Process the CSV file to overlay logos on garments based on the provided data.
    """
    # Read the CSV file
    data = pd.read_csv(csv_file)

    # Create a folder for output images
    output_folder = os.path.join(CURRENT_DIR, "Output")
    os.makedirs(output_folder, exist_ok=True)

    # Dictionary to track generated alpha masks
    alpha_masks = {}

    # Create a ZIP buffer for downloading
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
        # Process each row in the CSV
        for index, row in data.iterrows():
            # Append .png to the design and garment values
            design = f"{row['Design']}.png"
            garment = f"{row['Garment']}.png"
            width_in_inches = row["Width"]
            style_number = row["Style Number"]

            # Load the graphic and garment images
            graphic_path = os.path.join(GRAPHICS_FOLDER, design)
            garment_path = os.path.join(GARMENTS_FOLDER, garment)

            if not os.path.exists(graphic_path):
                st.error(f"Graphic file not found: {graphic_path}")
                continue
            if not os.path.exists(garment_path):
                st.error(f"Garment file not found: {garment_path}")
                continue

            graphic_img = Image.open(graphic_path).convert("RGBA")
            garment_img = Image.open(garment_path).convert("RGBA")

            # Check if the alpha mask for this garment has already been created
            if garment not in alpha_masks:
                alpha_mask_path = os.path.join(output_folder, f"{os.path.splitext(garment)[0]}_alpha.png")
                save_alpha_mask(garment_img, alpha_mask_path)
                alpha_masks[garment] = alpha_mask_path  # Store the path to the alpha mask
            else:
                alpha_mask_path = alpha_masks[garment]  # Reuse the existing alpha mask

            # Calculate the logo width in pixels based on the Width column
            logo_width_pixels = int((width_in_inches / 12) * 400)

            # Calculate the logo height based on the aspect ratio
            aspect_ratio = graphic_img.height / graphic_img.width
            logo_height_pixels = int(logo_width_pixels * aspect_ratio)

            # Resize the logo to the calculated width and height
            graphic_img = graphic_img.resize((logo_width_pixels, logo_height_pixels), Image.Resampling.LANCZOS)

            # Overlay the graphic on the garment
            position = (garment_img.width // 2, garment_img.height // 2 - 100)  # Adjust position
            result_img = overlay_logo(
                garment_img, graphic_img, position, apply_light_map=apply_light_map, wrap_intensity=wrap_intensity
            )

            # Apply the alpha mask to the final result
            result_img_pil = Image.fromarray(result_img).convert("RGBA")
            alpha_mask = Image.open(alpha_mask_path).convert("L")  # Load the alpha mask as grayscale
            result_img_pil.putalpha(alpha_mask)

            # Save the result image with the style number as the filename
            output_path = os.path.join(output_folder, f"{style_number}.png")
            result_img_pil.save(output_path)

            # Add the result image to the ZIP file
            with open(output_path, "rb") as img_file:
                zip_file.writestr(f"{style_number}.png", img_file.read())

    zip_buffer.seek(0)
    return zip_buffer

#light blend logic on the logo
def apply_fabric_wrap_blend(logo_img, apparel_img, alpha, position, intensity=0.4):
    # Crop fabric region where logo will go
    x, y = position
    h, w = logo_img.shape[:2]
    # Adjust position to top-left for cropping (position is center)
    x_tl = int(x - w / 2)
    y_tl = int(y - h / 2)
    # Ensure we don't go out of bounds
    x_tl = max(0, min(apparel_img.shape[1] - w, x_tl))
    y_tl = max(0, min(apparel_img.shape[0] - h, y_tl))
    
    fabric_crop = apparel_img[y_tl:y_tl + h, x_tl:x_tl + w]

    # Convert fabric to grayscale (light map)
    light_map = cv2.cvtColor(fabric_crop, cv2.COLOR_BGR2GRAY)

    # Normalize the light map so the darkest pixel is 0 and the lightest is 1
    min_val, max_val = np.min(light_map), np.max(light_map)
    if max_val > min_val:  # Avoid division by zero
        light_map = (light_map - min_val) / (max_val - min_val)
    else:
        light_map = np.zeros_like(light_map)  # If all pixels are the same, use a uniform map

    # Apply Gaussian blur to smooth the light map
    light_map = cv2.GaussianBlur(light_map, (21, 21), 0)

    # Normalize RGB to [0, 1]
    rgb = logo_img.astype(np.float32) / 255.0  # Already BGR format

    # Apply blending: combine the logo with the light map
    blended_rgb = np.zeros_like(rgb)
    for c in range(3):  # Loop over RGB channels
        blended_rgb[:, :, c] = rgb[:, :, c] * (1.0 - intensity) + rgb[:, :, c] * light_map * intensity

    # Convert back to uint8 - no need to recombine with alpha as we'll do that later
    blended_rgb = np.clip(blended_rgb * 255, 0, 255).astype(np.uint8)
    return blended_rgb

#main function to combine the image and logo
def overlay_logo(apparel_img, logo_img, position, apply_light_map=False, wrap_intensity=15):
    """
    Overlay the resized logo on the garment image at the specified position.
    """
    # Get images as arrays
    apparel = np.array(apparel_img.convert("RGB"))[:, :, ::-1]  # Convert to BGR
    logo = np.array(logo_img.convert("RGBA"))  # Keep alpha (transparency)

    # Separate the alpha channel from the logo
    alpha = logo[:, :, 3] / 255.0  # Normalize alpha to [0, 1]
    logo_rgb = logo[:, :, :3][:, :, ::-1]  # Convert logo to BGR

    # Pre-multiply the RGB values by the alpha channel
    logo_rgb = (logo_rgb * alpha[:, :, None]).astype(np.uint8)

    # Get center position coordinates
    center_x, center_y = position

    # Calculate top-left position from center
    x = int(center_x - logo.shape[1] / 2)
    y = int(center_y - logo.shape[0] / 2)

    # Ensure position is within bounds
    x = max(0, min(apparel.shape[1] - logo.shape[1], x))
    y = max(0, min(apparel.shape[0] - logo.shape[0], y))

    # Apply light map wrap if selected
    if apply_light_map:
        apparel_bgr = np.array(apparel_img.convert("RGB"))[:, :, ::-1]  # PIL to BGR
        # Pass both apparel and logo to the blending as BGR images with center position
        logo_rgb = apply_fabric_wrap_blend(logo_rgb, apparel_bgr, alpha, (center_x, center_y), intensity=wrap_intensity / 100.0)

    # Position logo and blend it into apparel
    roi = apparel[y:y + logo.shape[0], x:x + logo.shape[1]]

    # Blend the logo into the apparel image
    for c in range(3):
        roi[:, :, c] = (logo_rgb[:, :, c] + roi[:, :, c] * (1 - alpha)).astype(np.uint8)

    apparel[y:y + logo.shape[0], x:x + logo.shape[1]] = roi

    return cv2.cvtColor(apparel, cv2.COLOR_BGR2RGB)

# Print the current working directory for debugging
print("Current working directory:", os.getcwd())
print("Graphics folder path:", GRAPHICS_FOLDER)
print("Garments folder path:", GARMENTS_FOLDER)

# --- Streamlit UI --- #
st.title("Batch Apparel Logo Overlay Tool")

# Upload CSV file
st.markdown("### Upload CSV File")
csv_file = st.file_uploader("Upload CSV File", type=["csv"])

# Light map wrap toggle and intensity slider
apply_light_map = st.checkbox("Apply Light Map Wrapping (simulate fabric texture)")
if apply_light_map:
    wrap_intensity = st.slider("Light Map Intensity", 0, 100, 45)
else:
    wrap_intensity = 15

if csv_file:
    if st.button("Process"):
        zip_buffer = process_csv(csv_file, apply_light_map, wrap_intensity)
        st.success("Processing complete. Download the results below.")

        # Provide a download button for the ZIP file
        st.download_button(
            label="Download All Processed Images (ZIP)",
            data=zip_buffer,
            file_name="processed_apparel_logos.zip",
            mime="application/zip",
        )