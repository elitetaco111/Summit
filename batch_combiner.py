import streamlit as st
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import io
import os
import zipfile
from streamlit_drawable_canvas import st_canvas

#TO RUN: streamlit run batch_combiner.py

def generate_displacement_map(apparel_img):
    gray = cv2.cvtColor(apparel_img, cv2.COLOR_BGR2GRAY)
    displacement = cv2.GaussianBlur(gray, (21, 21), 0)
    return displacement

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
def overlay_logo(apparel_img, logo_img, position, scale=0.3, apply_light_map=False, wrap_intensity=15):
    # Get images as arrays
    apparel = np.array(apparel_img.convert("RGB"))[:, :, ::-1]  # Convert to BGR
    logo = np.array(logo_img.convert("RGBA"))  # Keep alpha (transparency)

    # Resize logo
    logo_h = int(apparel.shape[0] * scale)
    logo_w = int(logo.shape[1] * logo_h / logo.shape[0])
    logo = cv2.resize(logo, (logo_w, logo_h), interpolation=cv2.INTER_AREA)

    # Separate the alpha channel from the logo
    alpha = logo[:, :, 3] / 255.0  # Normalize alpha to [0, 1]
    logo_rgb = logo[:, :, :3][:, :, ::-1]  # Convert logo to BGR

    # Pre-multiply the RGB values by the alpha channel
    logo_rgb = (logo_rgb * alpha[:, :, None]).astype(np.uint8)

    # Get center position coordinates
    center_x, center_y = position

    # Calculate top-left position from center
    x = int(center_x - logo_w / 2)
    y = int(center_y - logo_h / 2)

    # Ensure position is within bounds
    x = max(0, min(apparel.shape[1] - logo_w, x))
    y = max(0, min(apparel.shape[0] - logo_h, y))

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

#gets the image coordinates dynamically based on image size and logo size
def get_position_coords(position_name, apparel_size, logo_size):
    aw, ah = apparel_size
    lw, lh = logo_size
    # Return center coordinates for each position
    if position_name == "Center":
        #return (aw // 2, ah // 2)
        return (500,350)
    elif position_name == "Upper Left":
        #return (lw // 2 + 50, lh // 2 + 50)
        return (350, 250)
    elif position_name == "Upper Right":
        #return (aw - lw // 2 - 50, lh // 2 + 50)
        return (650, 250)
    elif position_name == "Bottom Left":
        #return (lw // 2 + 50, ah - lh // 2 - 50)
        return (350,600)
    elif position_name == "Bottom Right":
        #return (aw - lw // 2 - 50, ah - lh // 2 - 50)
        return (650, 600)
    else:
        return (aw // 2, ah // 2)  # Default to center

#draws lines on the image to help with positioning the logo when using custom
def draw_guides(image_pil, step=250):
    image = image_pil.copy()
    draw = ImageDraw.Draw(image)
    w, h = image.size

    #set font size based on image width
    font_size = w / 70
    if font_size < 20:
        font_size = 20 #set min font size to 20px

    #Calc steps for 10 equal sections
    x_step = w // 10
    y_step = h // 10

    #Load font
    try:
        font = ImageFont.truetype("arial.ttf", int(font_size))
    except:
        font = ImageFont.load_default()

    #Draw vertical lines and label them (9 lines for 10 sections)
    for i in range(1, 10):
        x = i * x_step
        # Make center vertical line more noticeable
        if i == 5:  # Center vertical line
            draw.line([(x, 0), (x, h)], fill=(0, 0, 0), width=3)  #thicker
            draw.text((x + 5, 5), f"x={x}", fill=(0, 0, 0), font=font)
        else:
            draw.line([(x, 0), (x, h)], fill=(255, 0, 0), width=1)
            draw.text((x + 5, 5), f"x={x}", fill=(255, 0, 0), font=font)

    # Draw horizontal lines and label them (9 lines for 10 sections)
    for i in range(1, 10):
        y = i * y_step
        # Make center horizontal line more noticeable
        if i == 5:  # Center horizontal line
            draw.line([(0, y), (w, y)], fill=(0, 0, 0), width=3)  #thicker
            draw.text((5, y + 5), f"y={y}", fill=(0, 0, 0), font=font)
        else:
            draw.line([(0, y), (w, y)], fill=(0, 0, 255), width=1)
            draw.text((5, y + 5), f"y={y}", fill=(0, 0, 255), font=font)

    # Draw a crosshair at the center point
    cx, cy = w//2, h//2
    draw.line([(cx-20, cy), (cx+20, cy)], fill=(255, 0, 255), width=2)
    draw.line([(cx, cy-20), (cx, cy+20)], fill=(255, 0, 255), width=2)
    draw.text((cx+10, cy+10), "Center", fill=(255, 0, 255), font=font)

    return image

# --- Streamlit UI --- #
st.title("Batch Apparel Logo Overlay Tool")

# Upload folder of apparel images
st.markdown("### Upload Apparel Images")
apparel_files = st.file_uploader("Upload multiple apparel images", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

# Logo uploader
st.markdown("### Upload Logo")
logo_file = st.file_uploader("Upload Logo Image", type=["png"])

# Light map wrap toggle and intensity slider
apply_light_map = st.checkbox("Apply Light Map Wrapping (simulate fabric texture)")
if apply_light_map:
    wrap_intensity = st.slider("Light Map Intensity", 0, 100, 45)
else:
    wrap_intensity = 15

# Logo scaling and positioning
scale = st.slider("Logo Scale (relative to apparel image)", 0.01, 0.99, 0.35)
position_option = st.selectbox("Logo Position", [
    "Center", "Upper Left", "Upper Right", "Bottom Left", "Bottom Right", "Custom"
])

# Custom position options
custom_position = None
if position_option == "Custom" and apparel_files:
    # Show the guide preview using the first image
    sample_img = Image.open(apparel_files[0]).convert("RGBA")
    st.markdown("#### Sample Apparel Image with Coordinate Guides")
    guide_img = draw_guides(sample_img)
    st.image(guide_img, caption="Use these guides to place the center of your logo.")
    st.caption(f"Sample image size: {sample_img.width}px wide by {sample_img.height}px tall")
    
    # Default to center of image
    default_x = sample_img.width // 2
    default_y = sample_img.height // 2
    
    x = st.number_input("X Position (center of logo, in pixels)", 0, sample_img.width, default_x, key="custom_x")
    y = st.number_input("Y Position (center of logo, in pixels)", 0, sample_img.height, default_y, key="custom_y")
    custom_position = (x, y)

# Processing logic
if apparel_files and logo_file and len(apparel_files) > 0:
    logo_img = Image.open(logo_file)
    
    if st.button("Process All Images"):
        # Create a progress bar
        progress_bar = st.progress(0)
        processed_images = []
        file_names = []
        
        # Process each apparel image
        for i, apparel_file in enumerate(apparel_files):
            apparel_img = Image.open(apparel_file)
            file_names.append(apparel_file.name)
            
            # Calculate logo dimensions for positioning
            logo_h = int(apparel_img.height * scale)
            logo_w = int(logo_img.width * logo_h / logo_img.height)
            
            # Determine position
            if position_option == "Custom" and custom_position:
                position = custom_position
            else:
                position = get_position_coords(position_option, (apparel_img.width, apparel_img.height), (logo_w, logo_h))
            
            # Apply overlay
            output = overlay_logo(
                apparel_img, logo_img, position,
                scale=scale, apply_light_map=apply_light_map, wrap_intensity=wrap_intensity
            )
            
            processed_images.append(output)
            progress_bar.progress((i + 1) / len(apparel_files))
        
        # Display results
        st.markdown("### Processed Images")
        
        # Display images in a grid (3 columns)
        cols = st.columns(3)
        for i, output in enumerate(processed_images):
            with cols[i % 3]:
                st.image(output, caption=file_names[i], use_container_width=True)
        
        # Create ZIP file for download
        if processed_images:
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w") as zip_file:
                for i, output in enumerate(processed_images):
                    img_pil = Image.fromarray(output)
                    img_buffer = io.BytesIO()
                    img_pil.save(img_buffer, format="PNG")
                    img_buffer.seek(0)
                    
                    # Create filename: original_name + _logo.png
                    base_name = os.path.splitext(file_names[i])[0]
                    new_filename = f"{base_name}_logo.png"
                    
                    zip_file.writestr(new_filename, img_buffer.getvalue())
            
            zip_buffer.seek(0)
            st.download_button(
                label="Download All Processed Images (ZIP)",
                data=zip_buffer,
                file_name="processed_apparel_logos.zip",
                mime="application/zip"
            )