from PIL import Image, ImageDraw

BLUE_BG  = (15, 17, 26)
BLUE_ACC = (79, 142, 247)

def make_icon(size):
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    d   = ImageDraw.Draw(img)

    r = max(4, size // 6)
    d.rounded_rectangle([0, 0, size-1, size-1], radius=r, fill=BLUE_ACC)

    m  = size // 2
    h  = int(size * 0.38)
    lx = int(size * 0.30)
    rx = int(size * 0.72)
    d.polygon([(lx, m - h), (rx, m), (lx, m + h)], fill=BLUE_BG)

    return img

icons_dir = r"E:\Programacion\Estensiones de navegador\Anime autoplay\host-animeav1-autoplay\icons"
for sz in [16, 48, 128]:
    make_icon(sz).save(f"{icons_dir}\\icon{sz}.png")
    print(f"icon{sz}.png OK")
