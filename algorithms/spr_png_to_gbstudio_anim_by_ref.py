import json
import os
import shutil
from copy import copy

from PIL import Image

from algorithms import spr_png_to_gbstudio_anim_o1
from misc.arg_parse import argdict

import random
import string


def rnd_str(length: int) -> str:
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def process(image: Image, params: str = "") -> Image:
    args = argdict(copy(params))

    fname = args.setdefault('fname', 'TBD')
    is_ref = args.setdefault('isref', 'TBD') == 'True'

    override = args.setdefault('override', 'TBD') == 'True'
    processing = args.setdefault('processing', 'TBD') == 'True'

    image = spr_png_to_gbstudio_anim_o1.process(image, params)

    image.no_save = True

    if processing:

        if is_ref:
            extension = "." + fname[::-1].split('.', 1)[0][::-1]
            name = fname[::-1].split('\\', 1)[0][::-1].replace(extension, '')
            path = fname.replace(extension, '').replace(name, '')
            fixed_name = name.replace(' ', '_')

            fname = path + "\\" + fixed_name + extension
        else:
            fname = 'output.json'

        json_name = fname.replace('assets', 'project').replace('png', 'gbsres')

        file_exists = os.path.exists(json_name)

        # Dump the JSON to a file
        if file_exists and not override:
            image.extra_data = f"Skipping {fname}: Output file already exists and force_override is False."
            return image

        new_json_data = image.extra_data
        if file_exists:
            shutil.copy(json_name, json_name + rnd_str(6) + ".bu")

            with open(json_name, "r") as f:
                original_json_data = json.load(f)

            new_json_data["_resourceType"] = original_json_data["_resourceType"]
            new_json_data["id"] = original_json_data["id"]
            new_json_data["name"] = original_json_data["name"]
            new_json_data["symbol"] = original_json_data["symbol"]
            new_json_data["filename"] = original_json_data["filename"]
            new_json_data["checksum"] = original_json_data["checksum"]
            new_json_data["width"] = original_json_data["width"]
            new_json_data["height"] = original_json_data["height"]

        with open(json_name, "w") as f:
            json.dump(new_json_data, f, indent=2)

        image.extra_data = f"Successfully wrote {json_name}: Ref: {is_ref} Existing: {file_exists}" + str(image.extra_data)

    return image
