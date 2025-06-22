import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageTk
import os
import numpy as np

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

def draw_custom_mask(image):
    top = tk.Toplevel()
    top.title("Draw Freehand Mask")

    canvas = tk.Canvas(top, width=image.width, height=image.height, cursor="cross")
    canvas.pack()

    # ✅ Prevent image garbage collection
    top.tk_image = ImageTk.PhotoImage(image)
    canvas.create_image(0, 0, anchor='nw', image=top.tk_image)

    draw_points = []

    def on_press(event):
        draw_points.clear()
        draw_points.append((event.x, event.y))

    def on_drag(event):
        x, y = event.x, event.y
        draw_points.append((x, y))
        if len(draw_points) > 1:
            canvas.create_line(draw_points[-2][0], draw_points[-2][1], x, y, fill="red", width=2)

    def on_release(event):
        if len(draw_points) < 3:
            messagebox.showerror("Error", "Draw a closed shape with at least 3 points.")
            return

        # Create polygon mask
        mask = Image.new("L", image.size, 0)
        ImageDraw.Draw(mask).polygon(draw_points, fill=255)

        # Apply mask to alpha channel
        image_rgba = image.convert("RGBA")
        np_image = np.array(image_rgba)
        np_mask = np.array(mask)
        np_image[..., 3] = np.where(np_mask == 255, np_image[..., 3], 0)

        result = Image.fromarray(np_image)
        save_path = os.path.splitext(input_entry.get())[0] + "_custom_masked.png"
        result.save(save_path)
        messagebox.showinfo("Saved", f"Image saved as {save_path}")
        top.destroy()

    canvas.bind("<ButtonPress-1>", on_press)
    canvas.bind("<B1-Motion>", on_drag)
    canvas.bind("<ButtonRelease-1>", on_release)

def select_file():
    file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.jpeg *.png")])
    if file_path:
        input_entry.delete(0, tk.END)
        input_entry.insert(0, file_path)

def process_image(mode):
    input_path = input_entry.get()
    if not input_path or not os.path.exists(input_path):
        messagebox.showerror("Error", "Please select a valid image file.")
        return

    image = Image.open(input_path).convert("RGBA")

    if mode == "round":
        edited_image = round_image_border(image)
        suffix = "_rounded"
    elif mode == "grayscale":
        edited_image = apply_grayscale(image)
        suffix = "_grayscale"
    elif mode == "blur":
        edited_image = apply_blur(image)
        suffix = "_blur"
    elif mode == "brighten":
        edited_image = apply_brightness(image)
        suffix = "_brightened"
    elif mode == "remove_bg":
        edited_image = remove_background(image)
        suffix = "_nobg"
    elif mode == "custom_mask":
        draw_custom_mask(image)
        return
    else:
        return

    output_path = os.path.splitext(input_path)[0] + suffix + ".png"
    edited_image.save(output_path)
    messagebox.showinfo("Success", f"Image saved as {output_path}")

# GUI
app = tk.Tk()
app.title("Image Editor GUI")
app.geometry("600x340")

frame = tk.Frame(app, padx=10, pady=10)
frame.pack(expand=True, fill=tk.BOTH)

input_label = tk.Label(frame, text="Select an image:")
input_label.pack(anchor='w')

input_entry = tk.Entry(frame, width=50)
input_entry.pack(side=tk.LEFT, padx=(0, 5))

browse_button = tk.Button(frame, text="Browse", command=select_file)
browse_button.pack(side=tk.LEFT)

buttons_frame = tk.Frame(app)
buttons_frame.pack(pady=20)

tk.Button(buttons_frame, text="Round Border", command=lambda: process_image("round")).grid(row=0, column=0, padx=5)
tk.Button(buttons_frame, text="Grayscale", command=lambda: process_image("grayscale")).grid(row=0, column=1, padx=5)
tk.Button(buttons_frame, text="Blur", command=lambda: process_image("blur")).grid(row=0, column=2, padx=5)
tk.Button(buttons_frame, text="Brighten", command=lambda: process_image("brighten")).grid(row=0, column=3, padx=5)
tk.Button(buttons_frame, text="Remove Background", command=lambda: process_image("remove_bg")).grid(row=0, column=4, padx=5)
tk.Button(buttons_frame, text="Freehand Mask", command=lambda: process_image("custom_mask")).grid(row=1, column=2, pady=10)

app.mainloop()
