from PIL import Image
import sys
from pathlib import Path

def dominant_color(image: Image.Image, k=5):
    # simple approach: resize and average by quantize
    small = image.resize((160, 160))
    result = small.convert('P', palette=Image.ADAPTIVE, colors=k).convert('RGB')
    # count colors
    colors = result.getcolors(160*160)
    colors_sorted = sorted(colors, key=lambda x: x[0], reverse=True)
    return colors_sorted[0][1]

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: color_analysis.py IMAGE [ZONE=x0,y0,x1,y1]')
        raise SystemExit(2)
    path = Path(sys.argv[1])
    img = Image.open(path).convert('RGB')
    if len(sys.argv) == 3 and sys.argv[2].startswith('ZONE='):
        coords = list(map(int, sys.argv[2].split('=')[1].split(',')))
        img = img.crop(tuple(coords))
    col = dominant_color(img)
    print(f'{path} -> {col}')
