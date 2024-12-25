import uuid
from PIL import Image

from misc.arg_parse import argdict, auto_cast


def get_h_px_index(h_tile, frame, tile_width=8):
    res = h_tile * frame * tile_width
    return res


def get_v_px_index(v_tile, layer, animation, state, tile_height=16):
    res = v_tile * layer * animation * state * tile_height
    return res


def flip_horizontal(pixels, width, height):
    """
    Given a list/tuple of pixels of size (width*height),
    return a new tuple with each row reversed (horizontal flip).
    """
    new_pixels = []
    for row in range(height):
        row_data = pixels[row * width : (row + 1) * width]
        row_data = row_data[::-1]  # reverse
        new_pixels.extend(row_data)
    return tuple(new_pixels)


def flip_vertical(pixels, width, height):
    """
    Given a list/tuple of pixels of size (width*height),
    return a new tuple with rows in reverse order (vertical flip).
    """
    new_pixels = []
    for row in range(height - 1, -1, -1):
        row_data = pixels[row * width : (row + 1) * width]
        new_pixels.extend(row_data)
    return tuple(new_pixels)


def dedupe_tile(tile_pixels, seen_tiles, tile_width, tile_height, dedupeflips, h_px_index, v_px_index):
    """
    Attempt to deduplicate a tile using either exact matching or flip-aware matching.

    :param tile_pixels: (list or tuple) The raw pixel data for the tile.
    :param seen_tiles: (dict) Maps pixel-data variants -> (sliceX, sliceY, flipX, flipY)
    :param tile_width: The tile width (e.g. 8).
    :param tile_height: The tile height (e.g. 16).
    :param dedupeflips: (bool) If True, we check all flip variants. Otherwise, only no-flip.
    :param h_px_index: The tile's "would-be" sliceX if new.
    :param v_px_index: The tile's "would-be" sliceY if new.

    :return:
       (sliceX, sliceY, flipX, flipY, found_flag)

       If found_flag = True, then we have deduplicated and these are the correct
       slice coordinates and flips. If found_flag = False, this tile is new.
    """
    tile_pixels_noflip = tuple(tile_pixels)

    if not dedupeflips:
        # Dedupe is true, but flips are not considered
        if tile_pixels_noflip in seen_tiles:
            # Found an exact match
            sliceX, sliceY, flipX, flipY = seen_tiles[tile_pixels_noflip]
            return sliceX, sliceY, flipX, flipY, True
        else:
            # Not found; return no flips
            return h_px_index, v_px_index, False, False, False

    # If dedupeflips = True, generate all variants
    tile_pixels_hflip = flip_horizontal(tile_pixels_noflip, tile_width, tile_height)
    tile_pixels_vflip = flip_vertical(tile_pixels_noflip, tile_width, tile_height)
    tile_pixels_hvflip = flip_horizontal(tile_pixels_vflip, tile_width, tile_height)

    # 1) No flip
    if tile_pixels_noflip in seen_tiles:
        sliceX, sliceY, flipX, flipY = seen_tiles[tile_pixels_noflip]
        return sliceX, sliceY, flipX, flipY, True

    # 2) H-flip
    if tile_pixels_hflip in seen_tiles:
        sliceX, sliceY, orig_flipX, orig_flipY = seen_tiles[tile_pixels_hflip]
        return sliceX, sliceY, (not orig_flipX), orig_flipY, True

    # 3) V-flip
    if tile_pixels_vflip in seen_tiles:
        sliceX, sliceY, orig_flipX, orig_flipY = seen_tiles[tile_pixels_vflip]
        return sliceX, sliceY, orig_flipX, (not orig_flipY), True

    # 4) HV-flip
    if tile_pixels_hvflip in seen_tiles:
        sliceX, sliceY, orig_flipX, orig_flipY = seen_tiles[tile_pixels_hvflip]
        return sliceX, sliceY, (not orig_flipX), (not orig_flipY), True

    # Not found; tile is new, so store all flip variants
    seen_tiles[tile_pixels_noflip] = (h_px_index, v_px_index, False, False)
    seen_tiles[tile_pixels_hflip] = (h_px_index, v_px_index, True, False)
    seen_tiles[tile_pixels_vflip] = (h_px_index, v_px_index, False, True)
    seen_tiles[tile_pixels_hvflip] = (h_px_index, v_px_index, True, True)

    return h_px_index, v_px_index, False, False, False


def process(image: Image.Image, params: str = "") -> Image.Image:
    """
    Processes the given image, slicing it into frames based on 8x16 patches, and
    generates a JSON structure similar to the provided example. Each 8x16 patch is
    considered one frame. That frame consists of two 8x8 tiles stacked vertically:

        Top tile: top 8x8 region
        Bottom tile: bottom 8x8 region

    The final JSON is saved to "output.json".
    """

    # Basic configuration
    img_width, img_height = image.size

    args = argdict(params)

    fname = args.setdefault('fname', 'TBD')


    name = fname.split('\\')[-1][:-4]  # e.g. "sprite.png" -> "sprite"
    checksum = args.setdefault('chksum', 'TBD')
    tile_width = args.setdefault('twidth', 8)
    tile_height = args.setdefault('theight', 16)
    state_count = args.setdefault('states', 1)
    anim_count = args.setdefault('anims', 1)
    layer_count = args.setdefault('layers', 1)
    hor_tiles_per_frame = args.setdefault('htiles', 1)
    vert_tiles_per_frame = args.setdefault('vtiles', 1)
    layer_palettes = list(
        auto_cast(a.strip())
        for a in args.setdefault('palettes', "1,").split(",")
    )

    # NEW ARGS for deduplication
    dedupeflips = args.setdefault('dedupef,,', 'n') == 'y'
    dedupe = args.setdefault('dedupe', 'n') == 'y' if not dedupeflips else True

    # Horizontal offset compensation
    if hor_tiles_per_frame <= 2:
        h_compensation = 0
    else:
        h_compensation = (hor_tiles_per_frame - 2) * -4

    # Ensure image dimensions are multiples of the tile dimensions
    if img_width % tile_width != 0 or img_height % tile_height != 0:
        raise ValueError("Image dimensions must be multiples of 8x16 to form frames.")

    frame_count_per_anim = list(
        auto_cast(a.strip())
        for a in args.setdefault(
            'frames',
            str(img_width // (hor_tiles_per_frame * 8)) + ","
        ).split(",")
    )

    def gen_id():
        return str(uuid.uuid4())

    # Prepare the main JSON structure
    data = {
        "_resourceType": "sprite",
        "id": gen_id(),
        "name": name,
        "symbol": "sprite_" + name.replace(" ", "_"),
        "numFrames": 0,
        "filename": name + ".png",  # Placeholder filename
        "checksum": checksum,       # Could be computed if needed
        "width": img_width,
        "height": img_height,
        "states": [],
        "numTiles": 0,  # Will fill in after counting
        "canvasWidth": hor_tiles_per_frame * tile_width,
        "canvasHeight": vert_tiles_per_frame * tile_height,
        "boundsX": 0,
        "boundsY": 0,
        "boundsWidth": hor_tiles_per_frame * tile_width,
        "boundsHeight": vert_tiles_per_frame * tile_height,
        "animSpeed": 15
    }

    # Dictionary to track previously seen tile data (for deduplication)
    # Key = tuple of pixel data (possibly flips) -> (sliceX, sliceY, flipX, flipY)
    seen_tiles = {}

    for state_index in range(state_count):

        state = {
            "id": gen_id(),
            "name": "",
            "animationType": "fixed",
            "flipLeft": False,
            "animations": []
        }

        for animation_index in range(anim_count):
            # Prepare the animation
            animation = {
                "id": gen_id(),
                "frames": []
            }

            frame_count = frame_count_per_anim[animation_index]

            for frame_index in range(frame_count):
                data['numFrames'] += 1
                frame = {
                    "id": gen_id(),
                    "tiles": []
                }

                tile_in_frame = 0
                for v_tile_index in range(vert_tiles_per_frame):
                    for h_tile_index in range(hor_tiles_per_frame):
                        for layer_index in range(layer_count):
                            comment = ""

                            # Compute where in the source image this tile is
                            h_px_index = (h_tile_index + frame_index * hor_tiles_per_frame) * tile_width
                            v_px_index = (v_tile_index * 2 + layer_index) * \
                                         (animation_index + 1) * (state_index + 1) * tile_height

                            # Crop the tile region
                            tile_box = (h_px_index, v_px_index, h_px_index + tile_width, v_px_index + tile_height)
                            tile_region = image.crop(tile_box)
                            tile_pixels = list(tile_region.getdata())

                            # 1) If it's all green, skip
                            if all(px == (0, 255, 0) for px in tile_pixels):
                                continue

                            # 2) Deduplicate if asked
                            if dedupe:
                                # This will either return a known or new slice coords + flips
                                this_sliceX, this_sliceY, this_flipX, this_flipY, found_flag = dedupe_tile(
                                    tile_pixels, seen_tiles, tile_width, tile_height, dedupeflips, h_px_index,
                                    v_px_index)
                                if found_flag:
                                    comment += f"deduped with {h_px_index}, {v_px_index} "
                            else:
                                # No deduplication at all
                                this_sliceX, this_sliceY = h_px_index, v_px_index
                                this_flipX, this_flipY = False, False
                                found_flag = False  # Not used, but for clarity

                            # If brand-new tile (not deduped), store it (only in the no-dedupe scenario)
                            # Actually, our dedupe_tile() function handles storing. If dedupe is off, no store needed.
                            # Increase the global tile count
                            data['numTiles'] += 1

                            tile = {
                                "_comment": (comment + "item: %i  state: %i  anim: %i  frame: %i  tile: %i  layer: %i" %
                                (data['numTiles'], state_index, animation_index, frame_index, tile_in_frame, layer_index)
                                ),
                                "id": gen_id(),
                                # Position for final composition
                                "x": h_tile_index * tile_width + h_compensation,
                                "y": v_tile_index * tile_height,
                                # Possibly reused slice coords
                                "sliceX": this_sliceX,
                                "sliceY": this_sliceY,
                                "palette": 0,
                                "flipX": this_flipX,
                                "flipY": this_flipY,
                                "objPalette": "OBP0",
                                "paletteIndex": layer_palettes[layer_index],
                                "priority": False
                            }
                            tile_in_frame += 1
                            frame["tiles"].append(tile)

                animation["frames"].append(frame)
            state["animations"].append(animation)
        data["states"].append(state)

    image.extra_data = data
    return image
