from PIL import Image
import numpy as np

def process(image: Image) -> Image:
    # Convert image to RGB
    image = image.convert('RGB')
    width, height = image.size

    # Define fixed colours and the background colour
    fixed_colours = ['#071821', '#86C06C', '#E0F8CF', '#FF00E1']
    background_colour = '#00FF00'

    # Convert hex to RGB tuples
    fixed_colours_rgb = [tuple(int(colour[i:i + 2], 16) for i in (1, 3, 5)) for colour in fixed_colours]
    background_colour_rgb = tuple(int(background_colour[i:i + 2], 16) for i in (1, 3, 5))

    # Create a new image with extended height and fill with the background color
    new_height = height * 2  # Extend height
    new_image = Image.new("RGB", (width, new_height), background_colour_rgb)

    # Paste the original image on the top of the new image
    new_image.paste(image, (0, 0))

    # Fill the extended area with the background color
    for x in range(width):
        for y in range(height, new_height):
            new_image.putpixel((x, y), background_colour_rgb)

    # Find all unique non-fixed colors in the original image
    image_array = np.array(image)
    unique_colors = np.unique(image_array.reshape(-1, image_array.shape[2]), axis=0)
    non_fixed_colors = [tuple(color) for color in unique_colors if tuple(color) not in fixed_colours_rgb]

    # Take the first three non-fixed colors
    selected_colors = non_fixed_colors[:3]

    # Create a mapping from non-fixed colors to fixed colors
    color_mapping = {selected_colors[i]: fixed_colours_rgb[i] for i in range(len(selected_colors))}

    # Copy pixels with these non-fixed colors into the new area and convert them to fixed colors
    for x in range(width):
        for y in range(height):
            pixel = image.getpixel((x, y))
            if pixel in color_mapping:
                new_pixel = color_mapping[pixel]
                # Paste the new color in the extended area
                new_image.putpixel((x, y + height), new_pixel)

    return new_image

# Example usage:
# image = Image.open("your_image_path_here.png")
# processed_image = process(image)
# processed_image.save("processed_image.png")
