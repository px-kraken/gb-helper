import json
import uuid

from PIL import Image

from misc.arg_parse import argdict, auto_cast


def get_h_px_index(h_tile, frame, tile_width=8):
    res = h_tile * frame * tile_width
    return res


def get_v_px_index(v_tile, layer, animation, state, tile_height=16):
    res = v_tile * layer * animation * state * tile_height
    return res


def process(image: Image.Image, params: str = "") -> Image.Image:
    """
    Processes the given image, slicing it into frames based on 8x16 patches, and
    generates a JSON structure similar to the provided example. Each 8x16 patch is
    considered one frame. That frame consists of two 8x8 tiles stacked vertically:

        Top tile: top 8x8 region
        Bottom tile: bottom 8x8 region

    The final JSON is saved to "output.json".

    An adaptation is made so that if all pixels of a tile are (0, 255, 0),
    that tile is skipped (not included in the JSON).
    """

    # Basic configuration
    img_width, img_height = image.size

    args = argdict(params)

    fname = args.setdefault('fname', 'TBD')
    is_ref = args.setdefault('isref', 'TBD' == 'true')

    name = fname.split('\\')[-1][:-4]  # args.setdefault('name','TBD')
    checksum = args.setdefault('chksum', 'TBD')
    tile_width = args.setdefault('twidth', 8)
    tile_height = args.setdefault('theight', 16)
    state_count = args.setdefault('states', 1)
    anim_count = args.setdefault('anims', 1)
    layer_count = args.setdefault('layers', 1)
    hor_tiles_per_frame = args.setdefault('htiles', 1)
    vert_tiles_per_frame = args.setdefault('vtiles', 1)
    layer_palettes = list((auto_cast(a.strip()) for a in args.setdefault('palettes', "1,").split(",")))

    if hor_tiles_per_frame <= 2:
        h_compensation = 0
    else:
        h_compensation = (hor_tiles_per_frame - 2) * -4

    # Check if image dimensions are multiples of the frame size
    if img_width % tile_width != 0 or img_height % tile_height != 0:
        raise ValueError("Image dimensions must be multiples of 8x16 to form frames.")

    frame_count_per_anim = list(
        auto_cast(a.strip())
        for a in args.setdefault('frames', str(img_width // (hor_tiles_per_frame * 8)) + ",").split(",")
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
        "checksum": checksum,  # Could be computed if needed
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
                            # Compute where in the source image this tile is
                            h_px_index = (h_tile_index + frame_index * hor_tiles_per_frame) * tile_width
                            v_px_index = (v_tile_index * 2 + layer_index) * (animation_index + 1) \
                                         * (state_index + 1) * tile_height

                            # === NEW CODE BLOCK: Skip tiles that are purely (0,255,0) ===
                            # Crop the tile region
                            tile_box = (
                                h_px_index,
                                v_px_index,
                                h_px_index + tile_width,
                                v_px_index + tile_height
                            )
                            tile_region = image.crop(tile_box)
                            # Extract the pixel data
                            tile_pixels = tile_region.getdata()

                            # Check if all pixels are (0, 255, 0)
                            all_green = all(px == (0, 255, 0) for px in tile_pixels)
                            if all_green:
                                # Skip adding this tile to the frame
                                continue
                            # === END: Skip logic ===

                            data['numTiles'] += 1

                            tile = {
                                "_comment": (
                                        "item: %i   state: %i   anim: %i   frame: %i   tile: %i   layer: %i"
                                        % (
                                            data['numTiles'],
                                            state_index,
                                            animation_index,
                                            frame_index,
                                            tile_in_frame,
                                            layer_index
                                        )
                                ),
                                "id": gen_id(),
                                "x": h_tile_index * tile_width + h_compensation,
                                "y": v_tile_index * tile_height,
                                "sliceX": h_px_index,
                                "sliceY": v_px_index,
                                "palette": 0,
                                "flipX": False,
                                "flipY": False,
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
