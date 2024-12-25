from PIL import Image


def process(image: Image, params: str = "") -> Image:

    params = params if not params == '' else "1"
    gap_size = int(params)

    # Get original image dimensions
    width, height = image.size

    # Calculate new dimensions including the gaps
    new_width = width + (width - 1) * gap_size
    new_height = height + (height - 1) * gap_size

    # Create a new blank image with the new dimensions
    new_image = Image.new("RGBA", (new_width, new_height), (255, 255, 255, 0))

    # Copy pixels from the original image to the new image with gaps
    for y in range(height):
        for x in range(width):
            # Calculate new positions in the image considering the gap size
            new_x = x + x * gap_size
            new_y = y + y * gap_size
            new_image.putpixel((new_x, new_y), image.getpixel((x, y)))

    return new_image