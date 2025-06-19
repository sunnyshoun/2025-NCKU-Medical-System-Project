import math
from PIL import Image, ImageDraw

def draw_circle_with_right_opening(thickness=10, save_as=None, background=0):
    size = thickness * 4
    img_padding = 1 if thickness < 6 else 0
    img = Image.new('L', (size + thickness//4 + img_padding, size + thickness//4 + img_padding), background)
    draw = ImageDraw.Draw(img)

    outer_bbox = [0, 0, size, size]
    inner_padding = thickness
    inner_bbox = [inner_padding, inner_padding, size - inner_padding, size - inner_padding]

    draw.ellipse(outer_bbox, fill=255)
    draw.ellipse(inner_bbox, fill=0)

    draw.rectangle([size//2, (size - thickness)//2, size, (size + thickness)//2], fill=0)

    if save_as:
        img.save(save_as)

    return img

def paste_square_image_centered(src_img: Image.Image, target_size=(128, 64), background=0):
    if src_img.width != src_img.height:
        raise ValueError("Source image is not square: {0}x{1}".format(src_img.width, src_img.height))

    canvas = Image.new('L', target_size, background)

    x_offset = (target_size[0] - src_img.width) // 2
    y_offset = (target_size[1] - src_img.height) // 2

    canvas.paste(src_img, (x_offset, y_offset))

    return canvas

def draw_loading_frames() -> list[Image.Image]:
    frames = []
    num_dots = 5
    dot_radius = 4
    spacing = 16
    jump_height = 10
    frame_count = 12
    size = spacing * (num_dots - 1) + dot_radius * 2 + 8
    base_y = 32
    for frame in range(frame_count):
        img = Image.new('L', (size, size), 0)
        draw = ImageDraw.Draw(img)
        phase = frame * (2 * math.pi / frame_count)
        offset_x = dot_radius + 6
        for i in range(num_dots):
            x = offset_x + i * spacing
            offset = (i * 2 * math.pi / num_dots) + phase
            y_offset = math.sin(offset) * jump_height
            y = base_y - y_offset
            draw.ellipse(
                [x - dot_radius, y - dot_radius, x + dot_radius, y + dot_radius],
                fill=255
            )
        canvas = paste_square_image_centered(img, target_size=(128, 64))
        frames.append(canvas)
    return frames

def draw_bluetooth_icon() -> Image.Image:
    img = Image.new('1', (128, 64), 0)
    draw = ImageDraw.Draw(img)
    
    cx, cy = 64, 32

    top = (cx, cy - 20)
    bottom = (cx, cy + 20)
    right_upper = (cx + 10, cy - 10)
    right_lower = (cx + 10, cy + 10)
    left_upper = (cx - 10, cy - 10)
    left_lower = (cx - 10, cy + 10)
    
    draw.line([cx, cy-21, cx, cy+21], fill=1, width=3)
    draw.line([top, right_upper], fill=1, width=3)
    draw.line([right_upper, left_lower], fill=1, width=3)
    draw.line([bottom, right_lower], fill=1, width=3)
    draw.line([right_lower, left_upper], fill=1, width=3)

    return img

def draw_volume_icon() -> Image.Image:
    img = Image.new('1', (128, 64), 0)
    draw = ImageDraw.Draw(img)

    draw.polygon([(40, 26), (50, 26), (58, 20), (58, 44), (50, 38), (40, 38)], fill=1)
    draw.arc((57, 20, 72, 44), start=300, end=60, fill=1, width=2)
    draw.arc((67, 16, 82, 48), start=300, end=60, fill=1, width=2)
    return img

def draw_start_icon() -> Image.Image:
    img = Image.new('1', (128, 64), 0)
    draw = ImageDraw.Draw(img)
    triangle = [(54, 22), (54, 42), (74, 32)]
    draw.polygon(triangle, fill=1)
    return img

def draw_phone_icon() -> Image.Image:
    img = Image.new('1', (128, 64), 0)
    draw = ImageDraw.Draw(img)
    
    phone_width, phone_height = 16, 28
    top_left = (64 - phone_width // 2, 32 - phone_height // 2)
    bottom_right = (top_left[0] + phone_width, top_left[1] + phone_height)
    draw.rectangle([top_left, bottom_right], fill=1, outline=1, width=2)
    
    screen_offset = 2
    draw.rectangle(
        [(top_left[0] + screen_offset, top_left[1] + screen_offset),
         (bottom_right[0] - screen_offset, bottom_right[1] - screen_offset)],
        fill=0
    )
    
    button_width, button_height = 4, 2
    button_x = top_left[0] + phone_width // 2 - button_width // 2
    button_y = bottom_right[1] - button_height - 2
    draw.rectangle(
        [(button_x, button_y), (button_x + button_width, button_y + button_height)],
        fill=1
    )

    return img

def draw_phone_connected_icon() -> Image.Image:
    img = draw_phone_icon()
    draw = ImageDraw.Draw(img)
    
    signal_x = 64 + 12
    signal_y = 32 - 10
    for i in range(3):
        arc_size = 6 + i * 3
        draw.arc(
            [signal_x + i * 3, signal_y - arc_size // 2,
             signal_x + arc_size, signal_y + arc_size // 2],
            start=270, end=0,
            fill=1, width=1
        )

    return img

def check(img: Image.Image) -> Image.Image:
    draw = ImageDraw.Draw(img)
    draw.line([(5, 15), (10, 20)], fill=1, width=2)
    draw.line([(10, 20), (20, 5)], fill=1, width=2)
    return img

def cross(img: Image.Image) -> Image.Image:
    draw = ImageDraw.Draw(img)
    draw.line([(5, 5), (20, 20)], fill=1, width=2)
    draw.line([(20, 5), (5, 20)], fill=1, width=2)
    return img