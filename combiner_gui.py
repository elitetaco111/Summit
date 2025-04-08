import streamlit as st
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import io

def generate_displacement_map(apparel_img):
    gray = cv2.cvtColor(apparel_img, cv2.COLOR_BGR2GRAY)
    displacement = cv2.GaussianBlur(gray, (21, 21), 0)
    return displacement

#displacement map logic on the logo
def apply_displacement_map(logo_img, displacement_map, intensity=10):
    h, w = logo_img.shape[:2]
    displacement_map = cv2.resize(displacement_map, (w, h)).astype(np.float32) / 255.0
    shift_x = (displacement_map - 0.5) * intensity
    shift_y = (displacement_map - 0.5) * intensity
    map_x, map_y = np.meshgrid(np.arange(w), np.arange(h))
    map_x = (map_x + shift_x).astype(np.float32)
    map_y = (map_y + shift_y).astype(np.float32)
    displaced = cv2.remap(logo_img, map_x, map_y, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    return displaced

#light blend logic on the logo
def apply_fabric_wrap_blend(logo_img, apparel_img, position, intensity=0.4):
    # Crop fabric region where logo will go
    x, y = position
    h, w = logo_img.shape[:2]
    fabric_crop = apparel_img[y:y+h, x:x+w]

    # Convert fabric to grayscale (light map)
    light_map = cv2.cvtColor(fabric_crop, cv2.COLOR_BGR2GRAY)
    light_map = cv2.GaussianBlur(light_map, (21, 21), 0)
    light_map = light_map.astype(np.float32) / 255.0  # Normalize

    # Normalize logo to float
    logo_float = logo_img.astype(np.float32) / 255.0

    # Apply blending: darker shadows on logo using multiply-like effect
    for c in range(3):
        logo_float[:, :, c] *= (1.0 - intensity * (1.0 - light_map))

    # Convert back to uint8
    wrapped_logo = np.clip(logo_float * 255, 0, 255).astype(np.uint8)
    return wrapped_logo

#main function to combine the image and logo
def overlay_logo(apparel_img, logo_img, position, scale=0.3, wrap=False, wrap_intensity=15):
    apparel = np.array(apparel_img.convert("RGB"))[:, :, ::-1]  # PIL to BGR
    logo = np.array(logo_img.convert("RGBA"))  # Keep alpha

    #Resize logo
    logo_h = int(apparel.shape[0] * scale)
    logo_w = int(logo.shape[1] * logo_h / logo.shape[0])
    logo = cv2.resize(logo, (logo_w, logo_h), interpolation=cv2.INTER_AREA)

    alpha = logo[:, :, 3] / 255.0
    logo_rgb = logo[:, :, :3]

    if wrap:
        if wrap_method == "Displacement (Warp)":
            displacement_map = generate_displacement_map(apparel)
            logo_rgb = apply_displacement_map(logo_rgb, displacement_map, intensity=wrap_intensity)
        
        elif wrap_method == "Light Map (Blend Shadows)":
            apparel_bgr = np.array(apparel_img.convert("RGB"))[:, :, ::-1]  # PIL to BGR
            logo_rgb = apply_fabric_wrap_blend(logo_rgb, apparel_bgr, position, intensity=wrap_intensity / 100.0)

    x, y = position
    roi = apparel[y:y+logo_h, x:x+logo_w]

    for c in range(3):
        roi[:, :, c] = (logo_rgb[:, :, c] * alpha + roi[:, :, c] * (1 - alpha)).astype(np.uint8)

    apparel[y:y+logo_h, x:x+logo_w] = roi
    return cv2.cvtColor(apparel, cv2.COLOR_BGR2RGB)

#gets the image coordinates dynamically based on image size and logo size
def get_position_coords(position_name, apparel_size, logo_size):
    aw, ah = apparel_size
    lw, lh = logo_size

    if position_name == "Center":
        return ((aw - lw) // 2, (ah - lh) // 2)
    elif position_name == "Upper Left":
        return (50, 50)
    elif position_name == "Upper Right":
        return (aw - lw - 50, 50)
    elif position_name == "Bottom Left":
        return (50, ah - lh - 50)
    elif position_name == "Bottom Right":
        return (aw - lw - 50, ah - lh - 50)
    else:
        return (0, 0)

#draws lines on the image to help with positioning the logo when using custom
def draw_guides2(image_pil, step=250):
    image = image_pil.copy()
    draw = ImageDraw.Draw(image)
    w, h = image.size
    font = ImageFont.load_default()

    # Draw vertical lines
    for x in range(0, w, step):
        draw.line([(x, 0), (x, h)], fill=(255, 0, 0), width=1)
        draw.text((x + 5, 5), f"x={x}", fill=(255, 0, 0), font=font)

    # Draw horizontal lines
    for y in range(0, h, step):
        draw.line([(0, y), (w, y)], fill=(0, 255, 0), width=1)
        draw.text((5, y + 5), f"y={y}", fill=(0, 255, 0), font=font)
    return image

def draw_guides(image_pil, step=250):
    image = image_pil.copy()
    draw = ImageDraw.Draw(image)
    w, h = image.size

    #set font size based on image width
    font_size = w / 100
    if font_size < 14:
        font_size = 14 #set min font size to 20px

    #Set step based on image width
    if w < 1000:
        step = 100
    elif w < 2000:
        step = 250
    elif w < 3500:
        step = 500
    # Load a font
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except:
        font = ImageFont.load_default()

    # Draw vertical lines and label them
    for x in range(0, w, step):
        draw.line([(x, 0), (x, h)], fill=(255, 0, 0), width=1)
        draw.text((x + 5, 5), f"x={x}", fill=(255, 0, 0), font=font)

    # Draw horizontal lines and label them
    for y in range(0, h, step):
        draw.line([(0, y), (w, y)], fill=(0, 255, 0), width=1)
        draw.text((5, y + 5), f"y={y}", fill=(0, 255, 0), font=font)

    return image
# --- Streamlit UI ---
st.title("Apparel Logo Overlay Tool")

apparel_file = st.file_uploader("Upload Apparel Image", type=["jpg", "jpeg", "png"])
#guideline drawer when image uploaded
# if apparel_file:
#     apparel_img = Image.open(apparel_file).convert("RGBA")

#     # Show the guide preview
#     st.markdown("#### Apparel Image with Coordinate Guides")
#     guide_img = draw_guides(apparel_img, step=250)
#     st.image(guide_img, caption="Use these guides to help with custom logo placement.")

#logo uploader
logo_file = st.file_uploader("Upload Logo Image", type=["png"])

#scale slider
scale = st.slider("Logo Scale (relative to apparel height)", 0.05, 0.6, 0.25)
#position selector
position_option = st.selectbox("Logo Position", [
    "Center", "Upper Left", "Upper Right", "Bottom Left", "Bottom Right", "Custom"
])

#custom position options
if position_option == "Custom" and apparel_file:
    apparel_img = Image.open(apparel_file).convert("RGBA")

    # Show the guide preview
    st.markdown("#### Apparel Image with Coordinate Guides")
    guide_img = draw_guides(apparel_img, step=250)
    st.image(guide_img, caption="Use these guides to help with custom logo placement.")
    st.caption(f"Apparel image size: {apparel_img.width}px wide by {apparel_img.height}px tall")
    x = st.number_input("X Position (in pixels)", 0, 2000, 100, key="custom_x")
    y = st.number_input("Y Position (in pixels)", 0, 2000, 100, key="custom_y")
else:
    x = y = None  # Placeholder

#wrapper selector and intensity slider
wrap = st.checkbox("Apply Wrapping (simulate fabric texture)?")

if wrap:
    wrap_method = st.selectbox("Wrapping Method", [
        "Displacement (Warp)", 
        "Light Map (Blend Shadows)"
    ])
    wrap_intensity = st.slider("Wrap Intensity", 0, 100, 15)
else:
    wrap_method = None
    wrap_intensity = 0

#main func once files are uploaded and button pressed
if apparel_file and logo_file:
    apparel_img = Image.open(apparel_file)
    logo_img = Image.open(logo_file)

    if st.button("Generate Overlay"):
        output = None

        #Resize logo first to get its dimensions
        logo_h = int(apparel_img.height * scale)
        logo_w = int(logo_img.width * logo_h / logo_img.height)

        if position_option == "Custom":
            position = (x, y)
        else:
            position = get_position_coords(position_option, (apparel_img.width, apparel_img.height), (logo_w, logo_h))

        output = overlay_logo(
            apparel_img, logo_img, position,
            scale=scale, wrap=wrap, wrap_intensity=wrap_intensity
        )
        
        st.image(output, caption="Mockup Preview", use_container_width=True)

        #Download logic
        output_pil = Image.fromarray(output)
        buf = io.BytesIO()
        output_pil.save(buf, format="PNG")
        byte_im = buf.getvalue()
        st.download_button("Download Image", byte_im, file_name="mockup_output.png")

