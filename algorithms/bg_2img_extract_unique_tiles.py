from PIL import Image
import os


def process(img: Image, params: str = "") -> Image:
    # Open the second image using the path provided in the params string
    if not os.path.exists(params):
        # raise FileNotFoundError(f"The image path specified in params '{params}' does not exist.")
        img.extra_data = "Failed to open 2nd image"
        return img


    # try:
    img2 = Image.open(params).convert('RGB')
    # except:
    #     return  None, "Failed to open the image"

    # Extract 8x8 tiles from both images
    def get_8x8_tiles(image: Image):
        width, height = image.size
        tiles = []
        for y in range(0, height, 8):
            for x in range(0, width, 8):
                if x + 8 <= width and y + 8 <= height:  # Ensure we don't go out of bounds
                    tile = image.crop((x, y, x + 8, y + 8))
                    tiles.append(tile)
        return tiles

    tiles1 = get_8x8_tiles(img)
    tiles2 = get_8x8_tiles(img2)

    # Combine both sets of tiles and find unique ones
    all_tiles = tiles1 + tiles2
    unique_tiles = []

    # Compare tiles for uniqueness (by pixel data)
    for tile in all_tiles:
        if not any([list(tile.getdata()) == list(unique_tile.getdata()) for unique_tile in unique_tiles]):
            unique_tiles.append(tile)

    # Determine the number of rows needed based on the maximum width of 160 pixels
    max_width = 160
    tiles_per_row = max_width // 8
    num_rows = (len(unique_tiles) + tiles_per_row - 1) // tiles_per_row  # Ceiling division

    # Create a new blank image to hold the unique tiles
    new_img_width = min(len(unique_tiles), tiles_per_row) * 8
    new_img_height = num_rows * 8
    new_image = Image.new('RGB', (new_img_width, new_img_height))

    # Paste the unique tiles into the new image
    for index, tile in enumerate(unique_tiles):
        x = (index % tiles_per_row) * 8
        y = (index // tiles_per_row) * 8
        new_image.paste(tile, (x, y))

    return new_image
