from PIL import Image
import numpy as np

def process(image: Image) -> Image:
    # Background and fixed colors in RGB
    background_color = (0, 255, 0)  # #00FF00
    fixed_colors = np.array([
        (7, 24, 33),  # #071821
        (134, 192, 108),  # #86C06C
        (224, 248, 207)  # #E0F8CF
    ])

    width, height = image.size

    # Convert image to numpy array
    img_array = np.array(image)

    # Find all unique colors in the image
    unique_colors = np.unique(img_array.reshape(-1, img_array.shape[2]), axis=0)

    # Remove the background color and fixed colors from unique colors
    new_colors = set(tuple(color) for color in unique_colors) - {tuple(background_color)} - set(tuple(color) for color in fixed_colors)
    new_colors = np.array(list(new_colors))

    # Start with a new image filled with the background color
    new_img_array = np.full((height, width, 3), background_color, dtype=np.uint8)

    # Copy the original image into the new image
    new_img_array[0:height, 0:width] = img_array

    for i in range(0, len(new_colors), 3):
        # Calculate the number of new colors to process in this batch
        batch_size = min(3, len(new_colors) - i)

        # Create a new extended image array
        new_height = new_img_array.shape[0] + height
        extended_img_array = np.full((new_height, width, 3), background_color, dtype=np.uint8)

        # Copy the existing new_img_array into the extended image array
        extended_img_array[0:new_img_array.shape[0], 0:width] = new_img_array
        new_img_array = extended_img_array

        # Process each new color and replace with the corresponding fixed color
        for color_index in range(batch_size):
            new_color = new_colors[i + color_index]
            fixed_color = fixed_colors[color_index % len(fixed_colors)]

            # Create a mask for the current new color
            mask = np.all(img_array == new_color, axis=-1)

            # Apply the mask to the new area
            new_img_array[-height:, :, :][mask] = fixed_color

    # Replace all new colors in the original image area with the background color
    for new_color in new_colors:
        mask = np.all(new_img_array[0:height, :, :] == new_color, axis=-1)
        new_img_array[0:height, :, :][mask] = background_color

    # Convert the numpy array back to a PIL Image
    final_image = Image.fromarray(new_img_array)

    return final_image
