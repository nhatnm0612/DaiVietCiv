#!/usr/bin/env python3
"""Pack DaiVietCiv/Images into Unciv/libGDX game.png + game.atlas."""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    sys.exit(
        "Can Pillow: python3 -m venv .venv && .venv/bin/pip install Pillow\n"
        "roi chay: .venv/bin/python pack_atlas.py"
    )

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}
MAX_SIZE = 2048


@dataclass
class Sprite:
    name: str
    image: Image.Image
    width: int
    height: int
    x: int = 0
    y: int = 0


def collect_images(images_dir: Path) -> list[Sprite]:
    sprites: list[Sprite] = []
    for path in sorted(images_dir.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in IMAGE_EXTS:
            continue
        if path.name.startswith("."):
            continue
        image = Image.open(path).convert("RGBA")
        name = path.relative_to(images_dir).with_suffix("").as_posix()
        sprites.append(Sprite(name=name, image=image, width=image.width, height=image.height))
    if not sprites:
        sys.exit(f"Khong tim thay anh nao trong {images_dir}")
    return sprites


def pack_sprites(sprites: list[Sprite], padding: int) -> tuple[int, int]:
    """Shelf packer: left-to-right, wrap to next row when exceeding MAX_SIZE."""
    ordered = sorted(sprites, key=lambda s: (-s.height, -s.width, s.name))
    cursor_x = padding
    cursor_y = padding
    row_height = 0
    sheet_w = padding
    sheet_h = padding

    for sprite in ordered:
        if sprite.width + 2 * padding > MAX_SIZE or sprite.height + 2 * padding > MAX_SIZE:
            sys.exit(
                f"Anh '{sprite.name}' ({sprite.width}x{sprite.height}) lon hon gioi han {MAX_SIZE}px"
            )
        if cursor_x + sprite.width + padding > MAX_SIZE:
            cursor_x = padding
            cursor_y += row_height + padding
            row_height = 0
        if cursor_y + sprite.height + padding > MAX_SIZE:
            sys.exit("Khong du cho trong 1 atlas 2048x2048. Tach them thu muc Images.xyz.")

        sprite.x = cursor_x
        sprite.y = cursor_y
        cursor_x += sprite.width + padding
        row_height = max(row_height, sprite.height)
        sheet_w = max(sheet_w, sprite.x + sprite.width + padding)
        sheet_h = max(sheet_h, sprite.y + sprite.height + padding)

    return sheet_w, sheet_h


def compose_sheet(sprites: list[Sprite], width: int, height: int) -> Image.Image:
    sheet = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    for sprite in sprites:
        sheet.paste(sprite.image, (sprite.x, sprite.y), sprite.image)
    return sheet


def write_atlas(path: Path, png_name: str, width: int, height: int, sprites: list[Sprite]) -> None:
    lines = [
        "",
        png_name,
        f"size: {width},{height}",
        "format: RGBA8888",
        "filter: Linear,Linear",
        "repeat: none",
    ]
    for sprite in sorted(sprites, key=lambda s: s.name):
        lines.extend(
            [
                sprite.name,
                "  rotate: false",
                f"  xy: {sprite.x}, {sprite.y}",
                f"  size: {sprite.width}, {sprite.height}",
                f"  orig: {sprite.width}, {sprite.height}",
                "  offset: 0, 0",
                "  index: -1",
            ]
        )
    path.write_text("\n".join(lines) + "\n", encoding="ascii")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ghep anh trong Images thanh game.png + game.atlas")
    root = Path(__file__).resolve().parent
    parser.add_argument("--images", type=Path, default=root / "Images")
    parser.add_argument("--out", type=Path, default=root)
    parser.add_argument("--padding", type=int, default=8)
    parser.add_argument("--name", default="game", help="Ten file atlas (mac dinh: game)")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    images_dir = args.images.resolve()
    out_dir = args.out.resolve()
    if not images_dir.is_dir():
        sys.exit(f"Khong thay thu muc anh: {images_dir}")

    sprites = collect_images(images_dir)
    width, height = pack_sprites(sprites, max(0, args.padding))
    sheet = compose_sheet(sprites, width, height)

    png_name = f"{args.name}.png"
    atlas_path = out_dir / f"{args.name}.atlas"
    png_path = out_dir / png_name
    out_dir.mkdir(parents=True, exist_ok=True)
    sheet.save(png_path, format="PNG")
    write_atlas(atlas_path, png_name, width, height, sprites)

    print(f"Packed {len(sprites)} anh -> {png_path} ({width}x{height})")
    print(f"Atlas: {atlas_path}")
    for sprite in sorted(sprites, key=lambda s: s.name):
        print(f"  {sprite.name}: {sprite.width}x{sprite.height} @ {sprite.x},{sprite.y}")


if __name__ == "__main__":
    main()
