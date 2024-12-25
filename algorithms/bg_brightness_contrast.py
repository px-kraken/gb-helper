from typing import Dict, Any

import numpy as np
from PIL import Image, ImageEnhance


def process(image: Image.Image, params: str = "") -> Image.Image:
    # Define the color palette
    palette = np.array([
        [224, 248, 208],  # Lightest gray
        [136, 192, 112],  # Light gray
        [52, 104, 86],  # Dark gray
        [8, 24, 32]  # Black
    ])

    # image = image.resize((160, 160), Image.NEAREST)
    # image = image.crop((0, 8, 160, image.height - 8))

    # Define brightness and contrast adjustments
    brightness_levels = [1.0, 1.2, 1.4]
    contrast_levels = [1.0, 1.2, 1.4]

    # Dimensions for output image
    original_width, original_height = image.size
    output_width, output_height = original_width * 3, original_height * 3
    output_image = Image.new("RGB", (output_width, output_height))

    # Function to find the closest color from the palette
    def find_closest_color(pixel):
        # Ensure pixel has 3 components (RGB)
        pixel = np.array(pixel[:3]) if len(pixel) > 3 else np.array(pixel)
        distances = np.sqrt(((palette - pixel) ** 2).sum(axis=1))
        closest_color = palette[np.argmin(distances)]
        return tuple(closest_color.astype(int))

    # Process each brightness and contrast variation
    for i, brightness_factor in enumerate(brightness_levels):
        for j, contrast_factor in enumerate(contrast_levels):
            # Apply brightness and contrast
            enhancer_b = ImageEnhance.Brightness(image)
            enhancer_c = ImageEnhance.Contrast(enhancer_b.enhance(brightness_factor))
            adjusted_image = enhancer_c.enhance(contrast_factor)

            # Reduce colors to palette
            adjusted_array = np.array(adjusted_image)
            quantized_array = np.apply_along_axis(find_closest_color, 2, adjusted_array)
            quantized_image = Image.fromarray(np.uint8(quantized_array), "RGB")

            # Paste into the output grid
            x_offset = i * original_width
            y_offset = j * original_height
            output_image.paste(quantized_image, (x_offset, y_offset))

    return output_image


# Retry processing the uploaded image
# output_image = dummy_processing(input_image)
#+ output_image.show()
