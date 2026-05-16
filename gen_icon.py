"""从 idic1.jpg 生成应用图标 (icon.ico 和 icon.png)"""
import os
from PIL import Image

base_dir = os.path.dirname(os.path.abspath(__file__))
public_dir = os.path.join(base_dir, "public")
os.makedirs(public_dir, exist_ok=True)

jpg_path = os.path.join(base_dir, "idic1.jpg")
img = Image.open(jpg_path)

if img.mode != "RGBA":
    img = img.convert("RGBA")

img_resized = img.resize((256, 256), Image.LANCZOS)

sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
ico_path = os.path.join(public_dir, "icon.ico")
img_resized.save(ico_path, format="ICO", sizes=sizes)

png_path = os.path.join(public_dir, "icon.png")
img_resized.save(png_path, format="PNG")

print(f"图标已生成: {ico_path}")
print(f"预览: {png_path}")
