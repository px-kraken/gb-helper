from PIL import Image, ImageDraw, ImageFont
import matplotlib.pyplot as plt
import random

import numpy as np
import hashlib


def get_ndarray_hash(array: np.ndarray, algorithm: str = 'md5') -> str:
    """
    Computes the hash for a given NumPy ndarray using the specified algorithm.

    Parameters:
    array (np.ndarray): The input array to hash.
    algorithm (str): The hashing algorithm to use (default is 'md5').

    Returns:
    str: The hexadecimal hash string of the ndarray.
    """
    # Check if the provided algorithm is supported by hashlib
    if algorithm not in hashlib.algorithms_available:
        raise ValueError(f"Hashing algorithm '{algorithm}' is not available.")

    # Create a new hash object using the specified algorithm
    hash_obj = hashlib.new(algorithm)

    # Update the hash object with the array data
    hash_obj.update(array.tobytes())

    # Update the hash object with the array's shape and data type
    hash_obj.update(str(array.shape).encode())
    hash_obj.update(str(array.dtype).encode())

    # Return the hexadecimal digest
    return hash_obj.hexdigest()


# Function to divide the image into tiles
def divide_into_tiles(image_array, tile_width, tile_height):
    tiles = []
    for i in range(0, image_array.shape[0], tile_height):
        row = []
        for j in range(0, image_array.shape[1], tile_width):
            tile = image_array[i:i + tile_height, j:j + tile_width]
            if tile.shape[:2] == (tile_height, tile_width):  # Ensure it's the correct shape
                row.append(tile)
        if row:
            tiles.append(row)
    return np.array(tiles)


# Function to flip a tile
def flip_tile(tile, flip_type):
    if flip_type == 'H':
        return np.fliplr(tile)
    elif flip_type == 'V':
        return np.flipud(tile)
    elif flip_type == 'HV':
        return np.flipud(np.fliplr(tile))
    else:
        return tile


# Function to generate a random color
def generate_color():
    return tuple([random.randint(0, 255) for _ in range(3)])


# Function to check if a tile is already seen
def find_tile_identifier(tile, seen_tiles):
    flips = ['R', 'H', 'V', 'HV']
    for flip in flips:
        flipped_tile = flip_tile(tile, flip)
        for seen_tile, info in seen_tiles.items():
            if get_ndarray_hash(flipped_tile) == seen_tile:
                # hash = get_ndarray_hash(seen_tile)
                return info[0], info[1], flip  # Return color, number, and flip type
    return None, None, None

    # Function to process the tiles


def process_tiles(tiles):
    height, width = len(tiles), len(tiles[0])
    # new_row_tiles = list(np.zeros((height, width, 3), dtype=int))
    new_row_tiles = [[0 for _ in range(width)] for _ in range(height)]

    # new_row_tiles = [[]]
    seen_tiles = {}
    number_counter = 1

    for i in range(height):
        for j in range(width):
            tile = tiles[i][j]
            color, number, flip = find_tile_identifier(tile, seen_tiles)
            if color is None:
                color = generate_color()
                number = number_counter
                number_counter += 1
                hash = get_ndarray_hash(tile)
                seen_tiles[hash] = (color, number)

            new_row_tiles[i][j] = number, flip, tuple(color)
            flip_label = f"{number}{flip}"
            print(f"Tile at ({i},{j}) labeled as {flip_label}")

    return new_row_tiles, seen_tiles


def process(image: Image) -> Image:
    # Convert the image to a numpy array without changing it to grayscale
    image_array = np.array(image)

    # Define the tile size
    tile_width = 8
    tile_height = 16

    # Divide the image into tiles
    tiles = divide_into_tiles(image_array, tile_width, tile_height)

    # Process the tiles to get the output
    new_row_tiles, seen_tiles = process_tiles(tiles)

    # Create an output image with alternating new and original rows
    output_image_height = image_array.shape[0] * 2
    output_image = Image.new('RGB', (image_array.shape[1], output_image_height))

    # Load a very small font for labeling
    try:
        font = ImageFont.truetype("resources/04B_03__.ttf", 8)
    except IOError:
        font = ImageFont.load_default()

    # Draw the tiles with alternating rows
    for i in range(len(tiles)):
        for j in range(len(tiles[0])):
            original_tile = tiles[i][j]
            current_tile_infos = new_row_tiles[i][j]
            number, flip, color = current_tile_infos

            # Create new tile image
            new_tile_image = Image.new('RGB', (tile_width, tile_height), color)
            draw = ImageDraw.Draw(new_tile_image)

            # Get the identifier and label
            tile_key = get_ndarray_hash(
                original_tile)  # tuple(map(tuple, original_tile))  # tuple(map(tuple, original_tile))
            # if tile_key in seen_tiles:
            #     identifier = seen_tiles[tile_key]
            #     number, flip = identifier[1], find_tile_identifier(original_tile, seen_tiles)[2]
            number_str = str(number)
            flip_str = flip if flip is not None else ''

            # Draw the number and flip indication
            draw.fontmode = 1
            draw.text((0, 1), number_str, fill='white', font=font)
            draw.text((0, 7), flip_str, fill='white', font=font)

            # Calculate positions
            original_tile_position = (j * tile_width, (i * 2 + 1) * tile_height)
            new_tile_position = (j * tile_width, i * 2 * tile_height)

            # Paste new tile and original tile
            output_image.paste(new_tile_image, new_tile_position)
            original_tile_rgb = Image.fromarray(original_tile)
            output_image.paste(original_tile_rgb, original_tile_position)

    return output_image

# Example usage:
# image = Image.open('/path/to/your/image.png')
# processed_image = process(image)
# processed_image.show()  # or processed_image.save('/path/to/save/processed_image.png')
