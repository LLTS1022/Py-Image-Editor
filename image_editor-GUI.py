import streamlit as st
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter
from streamlit_drawable_canvas import st_canvas
import numpy as np
import io

st.set_page_config(page_title="Image Editor", layout="centered")
st.title("🖼️ Image Editor with Freehand Mask")

# Core processing functions
def round_image_border(image):
    width, height = image.size
    radius = min(width, height) // 2
    mask = Image.new("L", (width, height), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse(
        ((width - 2 * radius) // 2, (height - 2 * radius) // 2,
         (width + 2 * radius) // 2, (height + 2 * radius) // 2),
        fill=255
    )
    result = Image.new("RGBA", (width, height))
    result.paste(image, (0, 0), mask=mask)
    return result

def apply_grayscale(image):
    return image.convert("L").convert("RGBA")

def apply_blur(image):
    return image.filter(ImageFilter.GaussianBlur(5))

def apply_brightness(image, factor=1.5):
    enhancer = ImageEnhance.Brightness(image)
    return enhancer.enhance(factor)

def remove_background(image, tolerance=60):
    image = image.convert("RGBA")
    arr = np.array(image)
    corners = np.array([
        arr[0,0,:3],
        arr[0,-1,:3],
        arr[-1,0,:3],
        arr[-1,-1,:3]
    ])
    bg_color = np.mean(corners, axis=0)
    dist = np.sqrt(np.sum((arr[:,:,:3] - bg_color)**2, axis=2))
    mask = dist < tolerance
    arr[mask, 3] = 0
    return Image.fromarray(arr)

def apply_drawn_mask(base_image, mask_data):
    if mask_data is None:
        return base_image
    mask_array = np.array(mask_data)
    if mask_array.ndim == 3:
        mask_array = mask_array[:, :, 3]  # Use alpha channel
    mask_binary = (mask_array > 0).astype(np.uint8)

    base_np = np.array(base_image.convert("RGBA"))
    base_np[..., 3] = base_np[..., 3] * mask_binary  # Apply mask to alpha
    return Image.fromarray(base_np)

# Upload and edit interface
uploaded = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png"])
if uploaded:
    image = Image.open(uploaded).convert("RGBA")
    st.image(image, caption="Original Image", use_column_width=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Round Border"):
            image = round_image_border(image)
    with col2:
        if st.button("Grayscale"):
            image = apply_grayscale(image)
    with col3:
        if st.button("Blur"):
            image = apply_blur(image)

    if st.button("Brighten"):
        image = apply_brightness(image)

    if st.button("Remove Background"):
        image = remove_background(image)

    st.subheader("✏️ Draw to Mask Background (Freehand)")
    canvas_result = st_canvas(
        fill_color="rgba(255, 0, 0, 150)",
        stroke_width=20,
        stroke_color="#ffffff",
        background_image=image,
        update_streamlit=True,
        height=image.height,
        width=image.width,
        drawing_mode="freedraw",
        key="canvas"
    )

    if st.button("Apply Freehand Mask"):
        if canvas_result.image_data is not None:
            image = apply_drawn_mask(image, canvas_result.image_data)
            st.success("Mask applied!")

    st.image(image, caption="Edited Image", use_column_width=True)

    buf = io.BytesIO()
    image.save(buf, format="PNG")
    st.download_button("Download Result", buf.getvalue(), "edited.png", "image/png")
