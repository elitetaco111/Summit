# Example using OpenCV for perspective transform
import cv2
import numpy as np

def warp_logo(logo, target_points):
    h, w = logo.shape[:2]
    src_pts = np.array([[0, 0], [w, 0], [w, h], [0, h]], dtype='float32')
    dst_pts = np.array(target_points, dtype='float32')

    matrix = cv2.getPerspectiveTransform(src_pts, dst_pts)
    warped = cv2.warpPerspective(logo, matrix, (w, h), borderMode=cv2.BORDER_TRANSPARENT)
    return warped

def blend_logo_with_texture(apparel_img, logo_img, position):
    x, y = position
    h, w = logo_img.shape[:2]

    roi = apparel_img[y:y+h, x:x+w]
    
    # Convert to float for blending
    apparel_float = roi.astype(float)
    logo_float = logo_img.astype(float)

    # Multiply blend mode (or try others)
    blended = (apparel_float * logo_float / 255).astype(np.uint8)

    apparel_img[y:y+h, x:x+w] = blended
    return apparel_img

def generate_displacement_map(apparel_img):
    gray = cv2.cvtColor(apparel_img, cv2.COLOR_BGR2GRAY)
    displacement = cv2.GaussianBlur(gray, (21, 21), 0)  # Smooth out details
    return displacement

def apply_displacement_map(logo_img, displacement_map, intensity=10):
    h, w = logo_img.shape[:2]

    # Normalize displacement map
    displacement_map = cv2.resize(displacement_map, (w, h)).astype(np.float32) / 255.0

    # Calculate X and Y shifts (could be different)
    shift_x = (displacement_map - 0.5) * intensity
    shift_y = (displacement_map - 0.5) * intensity

    # Generate grid of coordinates
    map_x, map_y = np.meshgrid(np.arange(w), np.arange(h))
    map_x = (map_x + shift_x).astype(np.float32)
    map_y = (map_y + shift_y).astype(np.float32)

    # Remap logo pixels
    displaced = cv2.remap(logo_img, map_x, map_y, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    return displaced

def overlay_logo_on_apparel(apparel_path, logo_path, output_path, position=(100, 100), scale=0.3, displacement_intensity=10):
    # Load images
    apparel = cv2.imread(apparel_path, cv2.IMREAD_COLOR)
    logo = cv2.imread(logo_path, cv2.IMREAD_UNCHANGED)  # Keep alpha channel

    # Resize logo
    logo_h = int(apparel.shape[0] * scale)
    logo_w = int(logo.shape[1] * logo_h / logo.shape[0])
    logo = cv2.resize(logo, (logo_w, logo_h), interpolation=cv2.INTER_AREA)

    # Extract alpha channel from logo
    if logo.shape[2] == 4:
        alpha = logo[:, :, 3] / 255.0
        logo_rgb = logo[:, :, :3]
    else:
        alpha = np.ones((logo.shape[0], logo.shape[1]))
        logo_rgb = logo

    # Generate displacement map from apparel
    displacement = generate_displacement_map(apparel)
    displaced_logo = apply_displacement_map(logo_rgb, displacement, intensity=displacement_intensity)

    # Blend logo with apparel
    x, y = position
    roi = apparel[y:y+logo_h, x:x+logo_w]

    for c in range(3):
        roi[:, :, c] = (displaced_logo[:, :, c] * alpha + roi[:, :, c] * (1 - alpha)).astype(np.uint8)

    apparel[y:y+logo_h, x:x+logo_w] = roi

    # Save output
    cv2.imwrite(output_path, apparel)


overlay_logo_on_apparel(
    apparel_path="front.png",
    logo_path="front_g.png",
    output_path="mockup_output.jpg",
    position=(150, 100),
    scale=0.25,
    displacement_intensity=20
)
