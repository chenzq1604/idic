"""生成应用图标 - 蓝色渐变风格，匹配网页设计"""
import os
from PIL import Image, ImageDraw, ImageFont

base_dir = os.path.dirname(os.path.abspath(__file__))
public_dir = os.path.join(base_dir, "public")
os.makedirs(public_dir, exist_ok=True)

size = 256
img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

# 圆角矩形背景 - 蓝色渐变
for y in range(size):
    for x in range(size):
        # 检查是否在圆角矩形内
        r = 50
        in_rect = True
        if x < r and y < r:
            if (x - r) ** 2 + (y - r) ** 2 > r ** 2:
                in_rect = False
        elif x > size - r - 1 and y < r:
            if (x - (size - r - 1)) ** 2 + (y - r) ** 2 > r ** 2:
                in_rect = False
        elif x < r and y > size - r - 1:
            if (x - r) ** 2 + (y - (size - r - 1)) ** 2 > r ** 2:
                in_rect = False
        elif x > size - r - 1 and y > size - r - 1:
            if (x - (size - r - 1)) ** 2 + (y - (size - r - 1)) ** 2 > r ** 2:
                in_rect = False

        if in_rect:
            ratio = y / size
            red = int(79 * (1 - ratio) + 0 * ratio)
            green = int(172 * (1 - ratio) + 242 * ratio)
            blue = int(254 * (1 - ratio) + 254 * ratio)
            img.putpixel((x, y), (red, green, blue, 255))

# 画一本打开的书
book_cx, book_cy = 128, 100
book_w, book_h = 140, 90

# 左页
left_page = [
    (book_cx - 5, book_cy - book_h // 2),
    (book_cx - book_w, book_cy - book_h // 2 + 15),
    (book_cx - book_w, book_cy + book_h // 2 - 10),
    (book_cx - 5, book_cy + book_h // 2),
]
draw.polygon(left_page, fill=(255, 255, 255, 230))

# 右页
right_page = [
    (book_cx + 5, book_cy - book_h // 2),
    (book_cx + book_w, book_cy - book_h // 2 + 15),
    (book_cx + book_w, book_cy + book_h // 2 - 10),
    (book_cx + 5, book_cy + book_h // 2),
]
draw.polygon(right_page, fill=(255, 255, 255, 230))

# 书脊
draw.line([(book_cx, book_cy - book_h // 2 - 2), (book_cx, book_cy + book_h // 2 + 2)], 
          fill=(200, 220, 255, 200), width=4)

# 左页文字线条
for i in range(5):
    y = book_cy - 30 + i * 14
    draw.line([(book_cx - 15, y), (book_cx - 110, y + 5)], 
              fill=(79, 172, 254, 120), width=2)

# 右页文字线条
for i in range(5):
    y = book_cy - 30 + i * 14
    draw.line([(book_cx + 15, y), (book_cx + 110, y + 5)], 
              fill=(79, 172, 254, 120), width=2)

# "iDic" 文字
try:
    font_large = ImageFont.truetype("arial.ttf", 52)
    font_small = ImageFont.truetype("arial.ttf", 20)
except:
    try:
        font_large = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 52)
        font_small = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 20)
    except:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()

# "iDic" 在书的下方
text = "iDic"
bbox = draw.textbbox((0, 0), text, font=font_large)
tw = bbox[2] - bbox[0]
draw.text(((size - tw) // 2, 170), text, fill=(255, 255, 255, 255), font=font_large)

# 保存
sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
ico_path = os.path.join(public_dir, "icon.ico")
img.save(ico_path, format="ICO", sizes=sizes)

png_path = os.path.join(public_dir, "icon.png")
img.save(png_path, format="PNG")

print(f"图标已生成: {ico_path}")
print(f"预览: {png_path}")
