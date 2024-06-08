from PIL import Image
import hashlib

def hash_patch(patch):
    """Generate a hash for an 8x8 patch of an image."""
    hash_obj = hashlib.md5()
    hash_obj.update(patch.tobytes())
    return hash_obj.hexdigest()

def process(image: Image) -> Image:
    """Process the image, color the upper-left pixel of duplicate patches pink."""
    pixels = image.load()
    width, height = image.size
    seen_patches = set()

    for y in range(0, height, 8):
        for x in range(0, width, 8):
            if x + 8 <= width and y + 8 <= height:
                patch = image.crop((x, y, x + 8, y + 8))
                patch_hash = hash_patch(patch)

                if patch_hash in seen_patches:
                    pixels[x, y] = (255, 105, 180)  # RGB value for pink
                else:
                    pixels[x, y] = (0, 255, 255)  # RGB value for cyan
                    seen_patches.add(patch_hash)

    return image
