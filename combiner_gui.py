import streamlit as st
import cv2
import numpy as np
from PIL import Image
import io

def generate_displacement_map(apparel_img):
    gray = cv2.cvtColor(apparel_img, cv2.COLOR_BGR2GRAY)
    displacement = cv2.GaussianBlur(gray, (21, 21), 0)
    return displacement

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

def overlay_logo(apparel_img, logo_img, position, scale=0.3, wrap=False, wrap_intensity=15):
    apparel = np.array(apparel_img.convert("RGB"))[:, :, ::-1]  # PIL to BGR
    logo = np.array(logo_img.convert("RGBA"))  # Keep alpha

    # Resize logo
    logo_h = int(apparel.shape[0] * scale)
    logo_w = int(logo.shape[1] * logo_h / logo.shape[0])
    logo = cv2.resize(logo, (logo_w, logo_h), interpolation=cv2.INTER_AREA)

    alpha = logo[:, :, 3] / 255.0
    logo_rgb = logo[:, :, :3]

    if wrap:
        displacement_map = generate_displacement_map(apparel)
        logo_rgb = apply_displacement_map(logo_rgb, displacement_map, intensity=wrap_intensity)

    x, y = position
    roi = apparel[y:y+logo_h, x:x+logo_w]

    for c in range(3):
        roi[:, :, c] = (logo_rgb[:, :, c] * alpha + roi[:, :, c] * (1 - alpha)).astype(np.uint8)

    apparel[y:y+logo_h, x:x+logo_w] = roi
    return cv2.cvtColor(apparel, cv2.COLOR_BGR2RGB)

# --- Streamlit UI ---
st.title("Apparel Logo Overlay Tool")

apparel_file = st.file_uploader("Upload Apparel Image", type=["jpg", "jpeg", "png"])
logo_file = st.file_uploader("Upload Logo Image", type=["png"])

scale = st.slider("Logo Scale (relative to apparel height)", 0.01, 0.9, 0.25)
x = st.number_input("X Position (in pixels)", 0, 2000, 100)
y = st.number_input("Y Position (in pixels)", 0, 2000, 100)

wrap = st.checkbox("Apply Wrapping (simulate fabric texture)?")
wrap_intensity = st.slider("Wrap Intensity", 0, 50, 15) if wrap else 0

if apparel_file and logo_file:
    apparel_img = Image.open(apparel_file)
    logo_img = Image.open(logo_file)

    if st.button("Generate Overlay"):
        output = overlay_logo(apparel_img, logo_img, (x, y), scale=scale, wrap=wrap, wrap_intensity=wrap_intensity)
        st.image(output, caption="Mockup Preview", use_container_width=True)

        # Download
        output_pil = Image.fromarray(output)
        buf = io.BytesIO()
        output_pil.save(buf, format="PNG")
        byte_im = buf.getvalue()
        st.download_button("Download Image", byte_im, file_name="mockup_output.png")

