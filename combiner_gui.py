import streamlit as st
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import io
from streamlit_drawable_canvas import st_canvas

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
def apply_fabric_wrap_blend(logo_img, apparel_img, alpha, position, intensity=0.4):
    # Crop fabric region where logo will go
    x, y = position
    h, w = logo_img.shape[:2]
    fabric_crop = apparel_img[y:y+h, x:x+w]

    # Convert fabric to grayscale (light map)
    light_map = cv2.cvtColor(fabric_crop, cv2.COLOR_BGR2GRAY)
    light_map = cv2.GaussianBlur(light_map, (21, 21), 0)
    light_map = light_map.astype(np.float32) / 255.0  # Normalize

    #Normalize RGB to [0, 1]
    rgb = logo_img.astype(np.float32) / 255.0  # Already BGR format
    
    #Apply blending: combine the logo with the light map
    blended_rgb = np.zeros_like(rgb)
    for c in range(3):  # Loop over RGB channels
        blended_rgb[:, :, c] = rgb[:, :, c] * (1.0 - intensity) + rgb[:, :, c] * light_map * intensity

    #Convert back to uint8 - no need to recombine with alpha as we'll do that later
    blended_rgb = np.clip(blended_rgb * 255, 0, 255).astype(np.uint8)
    return blended_rgb

#function to apply a perspective warp to the logo (e.g. 3/4 turn left)
def apply_perspective_warp(logo_img, src_points, dest_points):
    """
    Applies a perspective warp to the logo image, preserving transparency.

    :param logo_img: The logo image as a NumPy array with an alpha channel (RGBA).
    :param src_points: Four source points (corners of the logo) as a list of (x, y) tuples.
    :param dest_points: Four destination points (where the corners should map to) as a list of (x, y) tuples.
    :return: The warped logo image as a NumPy array with an alpha channel (RGBA).
    """
    h, w = logo_img.shape[:2]
    src = np.array(src_points, dtype=np.float32)
    dest = np.array(dest_points, dtype=np.float32)

    # Separate the RGB and alpha channels
    rgb = logo_img[:, :, :3]
    alpha = logo_img[:, :, 3]

    # Compute the perspective transform matrix
    matrix = cv2.getPerspectiveTransform(src, dest)

    # Apply the perspective warp to the RGB channels
    warped_rgb = cv2.warpPerspective(rgb, matrix, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0))

    # Apply the perspective warp to the alpha channel
    warped_alpha = cv2.warpPerspective(alpha, matrix, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)

    # Combine the warped RGB and alpha channels
    warped_logo = np.dstack((warped_rgb, warped_alpha))

    return warped_logo

#main function to combine the image and logo
def overlay_logo(apparel_img, logo_img, position, scale=0.3, wrap=False, wrap_intensity=15, perspective_points=None):
    #get images as arrays
    apparel = np.array(apparel_img.convert("RGB"))[:, :, ::-1]  #get BGR version
    logo = np.array(logo_img.convert("RGBA"))  #Keep alpha (transparency)

    #Resize logo
    logo_h = int(apparel.shape[0] * scale)
    logo_w = int(logo.shape[1] * logo_h / logo.shape[0])
    logo = cv2.resize(logo, (logo_w, logo_h), interpolation=cv2.INTER_AREA)

    #seperate the alpha channel from the logo
    alpha = logo[:, :, 3] / 255.0
    logo_rgb = logo[:, :, :3][:, :, ::-1] #convert logo to BGR
    x, y = position

    #wrapper logic
    if wrap:
        if wrap_method == "Displacement":
            displacement_map = generate_displacement_map(apparel)
            logo_rgb = apply_displacement_map(logo_rgb, displacement_map, intensity=wrap_intensity)
        
        elif wrap_method == "Light Map":
            apparel_bgr = np.array(apparel_img.convert("RGB"))[:, :, ::-1]  # PIL to BGR
            #passing both apparel and logo to the blending as BGR images
            logo_rgb = apply_fabric_wrap_blend(logo_rgb, apparel_bgr, alpha, position, intensity=wrap_intensity / 100.0)

        elif wrap_method == "Perspective Warp" and perspective_points:
            adjusted_dest_points = perspective_points

            # Define source points relative to the logo's dimensions
            src_points = [(0, 0), (logo_w, 0), (logo_w, logo_h), (0, logo_h)]

            # Apply the perspective warp
            logo = apply_perspective_warp(logo, src_points, adjusted_dest_points)

    ##### (logic1) (position of logo is top left corner of logo)################################
    roi = apparel[y:y+logo.shape[0], x:x+logo.shape[1]]

    # Blend the logo into the apparel image
    for c in range(3):
        roi[:, :, c] = (logo_rgb[:, :, c] * alpha + roi[:, :, c] * (1 - alpha)).astype(np.uint8)

    apparel[y:y+logo.shape[0], x:x+logo.shape[1]] = roi
    #####
    #####(logic2) (position of logo is the center of the logo)##################################
    # x_centered = int(x - logo_w / 2)
    # y_centered = int(y - logo_h / 2)

    # #Clip the coordinates to ensure the logo stays within the bounds of the apparel
    # x_centered = max(0, min(x_centered, apparel.shape[1] - logo_w))
    # y_centered = max(0, min(y_centered, apparel.shape[0] - logo_h))

    # #Define the Region of Interest (ROI) for where the logo will go on the apparel
    # roi = apparel[y_centered:y_centered+logo_h, x_centered:x_centered+logo_w]

    # #Apply alpha blending (transparency)
    # for c in range(3):  # Loop over the 3 color channels (RGB)
    #     roi[:, :, c] = (logo_rgb[:, :, c] * alpha + roi[:, :, c] * (1 - alpha)).astype(np.uint8)

    # # Put the blended logo back into the apparel image
    # apparel[y_centered:y_centered+logo_h, x_centered:x_centered+logo_w] = roi
    ###############################################################################################

    return cv2.cvtColor(apparel, cv2.COLOR_BGR2RGB)

#gets the image coordinates dynamically based on image size and logo size
def get_position_coords(position_name, apparel_size, logo_size):
    aw, ah = apparel_size
    lw, lh = logo_size
    #accounts for size of logo to get the centered position
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

    return image

# --- Streamlit UI --- ## --- Streamlit UI --- ## --- Streamlit UI --- ## --- Streamlit UI --- #
st.title("Apparel Logo Overlay Tool")

#apparel uploader
apparel_file = st.file_uploader("Upload Apparel Image", type=["jpg", "jpeg", "png"])

#logo uploader
logo_file = st.file_uploader("Upload Logo Image", type=["png"])

#wrapper selector and intensity slider
wrap = st.checkbox("Apply Wrapping (simulate fabric texture)?")
perspective_points = None  #init perspective points
if wrap:
    wrap_method = st.selectbox("Wrapping Method", [
        "Displacement", 
        "Light Map",
        "Perspective Warp"
    ])
    wrap_intensity = st.slider("Wrap Intensity", 0, 100, 15)
    if wrap_method == "Perspective Warp":
        apparel_img = Image.open(apparel_file).convert("RGBA")
        st.markdown("#### Define Perspective Warp Points")
        st.caption("Specify the destination points for the four corners of the logo.")
        col1, col2 = st.columns(2)
        with col1:
            x1 = st.number_input("Top-Left X", 0, (apparel_img.width), 100)
            y1 = st.number_input("Top-Left Y", 0, (apparel_img.height), 100)
            x2 = st.number_input("Top-Right X", 0, (apparel_img.width), 200)
            y2 = st.number_input("Top-Right Y", 0, (apparel_img.height), 100)

        with col2:
            x3 = st.number_input("Bottom-Right X", 0, (apparel_img.width), 200)
            y3 = st.number_input("Bottom-Right Y", 0, (apparel_img.height), 200)
            x4 = st.number_input("Bottom-Left X", 0, (apparel_img.width), 100)
            y4 = st.number_input("Bottom-Left Y", 0, (apparel_img.height), 200)

        perspective_points = [(x1, y1), (x2, y2), (x3, y3), (x4, y4)]
        if perspective_points:
            preview_img = apparel_img.copy()
            draw = ImageDraw.Draw(preview_img)
            for point in perspective_points:
                draw.ellipse((point[0] - 5, point[1] - 5, point[0] + 5, point[1] + 5), fill="red", outline="red")
            st.image(draw_guides(preview_img), caption="Preview of Selected Points")
else:
    wrap_method = None
    wrap_intensity = 0

#only show position information if not using perspective warp
if wrap_method != "Perspective Warp":
    scale = st.slider("Logo Scale (relative to apparel image)", 0.01, 0.99, 0.25)
    #position selector
    position_option = st.selectbox("Logo Position", [
        "Center", "Upper Left", "Upper Right", "Bottom Left", "Bottom Right", "Custom"
    ])

    #custom position options
    if position_option == "Custom" and apparel_file:
        apparel_img = Image.open(apparel_file).convert("RGBA")
        # Show the guide preview
        st.markdown("#### Apparel Image with Coordinate Guides")
        guide_img = draw_guides(apparel_img)
        st.image(guide_img, caption="Use these guides to help with custom logo placement.")
        st.caption(f"Apparel image size: {apparel_img.width}px wide by {apparel_img.height}px tall")
        x = st.number_input("X Position (in pixels)", 0, (apparel_img.width), 100, key="custom_x")
        y = st.number_input("Y Position (in pixels)", 0, (apparel_img.height), 100, key="custom_y")

# --- Streamlit UI --- ## --- Streamlit UI --- ## --- Streamlit UI --- ## --- Streamlit UI --- #

#main func once files are uploaded and button pressed
if apparel_file and logo_file:
    apparel_img = Image.open(apparel_file)
    logo_img = Image.open(logo_file)

    if st.button("Generate Overlay"):
        output = None

        #Resize logo first to get its dimensions
        if wrap_method != "Perspective Warp":
            logo_h = int(apparel_img.height * scale)
            logo_w = int(logo_img.width * logo_h / logo_img.height)

            if position_option == "Custom":
                position = (x, y)
            else:
                position = get_position_coords(position_option, (apparel_img.width, apparel_img.height), (logo_w, logo_h))

        output = overlay_logo(
            apparel_img, logo_img, position,
            scale=scale, wrap=wrap, wrap_intensity=wrap_intensity,
            perspective_points=perspective_points
        )
        
        st.image(output, caption="Mockup Preview", use_container_width=True)

        #Download logic
        output_pil = Image.fromarray(output)
        buf = io.BytesIO()
        output_pil.save(buf, format="PNG")
        byte_im = buf.getvalue()
        st.download_button("Download Image", byte_im, file_name="mockup_output.png")

#EOF