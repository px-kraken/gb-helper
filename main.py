import tkinter as tk
from typing import Callable

from PIL import Image

import algorithms
from misc.dynamic_import import modules
from ui import ImageProcessingApp

algos = modules(algorithms)


def dummy_processing(image: Image.Image) -> Image.Image:
    """
    Dummy processing function.
    Replace with actual image processing logic.
    """
    return image  # This does nothing, replace with actual processing.


# Define available processing algorithms
processing_algorithms = {"Dummy Processing": dummy_processing, }
try:
    processing_algorithms.update({algo_str: getattr(getattr(algorithms, algo_str), 'process')
                                  for algo_str in dir(algorithms) if algo_str[0] != "_"})
except Exception as e:
    raise Exception("Make sure that algorithms have process function defined. Original error: " + str(e))

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageProcessingApp(root, processing_algorithms, dummy_processing)
    root.mainloop()
