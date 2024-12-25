import os
import time
from typing import Dict, Any, Callable
from PIL import Image, ImageDraw, ImageTk
from tqdm import tqdm
import numpy as np
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

# Type alias for the dictionary holding tile data
TileData = Dict[bytes, Dict[str, Any]]


def extract_unique_tiles(image: Image.Image, tile_size: int) -> TileData:
    width, height = image.size
    tiles: TileData = {}

    for y in range(0, height, tile_size):
        for x in range(0, width, tile_size):
            tile = image.crop((x, y, x + tile_size, y + tile_size))
            tile_data = np.array(tile).tobytes()
            if tile_data in tiles:
                tiles[tile_data]['count'] += 1
                tiles[tile_data]['positions'].append((x, y))
            else:
                tiles[tile_data] = {'tile': tile, 'count': 1, 'positions': [(x, y)]}

    return tiles


def create_combined_image_with_borders_sorted(original_image: Image.Image, tiles: TileData, tile_size: int,
                                              gap: int) -> Image.Image:
    width, height = original_image.size
    unique_tiles = sorted(tiles.values(), key=lambda t: t['count'])

    # Calculate the new image height
    rows_needed = (len(unique_tiles) * (tile_size + gap)) // width + 1
    new_image_height = height + (tile_size + 20) * rows_needed
    new_image = Image.new('RGB', (width, new_image_height), 'white')
    new_image.paste(original_image, (0, 0))
    draw = ImageDraw.Draw(new_image)

    # Draw borders on the original image
    for tile_data in tiles.values():
        count = tile_data['count']
        if count <= 3:
            if count == 1:
                border_color = 'pink'
            elif count == 2:
                border_color = 'orange'
            elif count == 3:
                border_color = 'yellow'

            for (x, y) in tile_data['positions']:
                draw.rectangle([(x, y), (x + tile_size - 1, y + tile_size - 1)], outline=border_color, width=1)

    # Place tiles and their counts below the original image
    x_offset = 0
    y_offset = height + gap
    for tile_data in unique_tiles:
        tile = tile_data['tile']
        count = tile_data['count']

        new_image.paste(tile, (x_offset, y_offset))
        draw.text((x_offset, y_offset + tile_size + 2), str(count), fill='black')

        x_offset += tile_size + gap
        if x_offset + tile_size > width:
            x_offset = 0
            y_offset += tile_size + 20

    return new_image


def process(img: Image, params: str = ""):
    img = create_combined_image_with_borders_sorted(img, extract_unique_tiles(img, 8), 8, 5)
    return img
