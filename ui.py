import os
import time
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

from PIL import Image, ImageTk
from tqdm import tqdm


class ImageProcessingApp:
    def __init__(self, root: tk.Tk, processing_algorithms, default_algorithm):
        self.root = root
        self.processing_algorithms = processing_algorithms
        self.default_algorithm = default_algorithm
        self.root.title("Image Processing App")
        self.root.geometry("1200x800")

        self.input_folder = 'input'
        self.output_folder = 'output'
        self.selected_subfolder = tk.StringVar()
        self.selected_algorithm = tk.StringVar(value="Dummy Processing")
        self.selected_upsampling = tk.IntVar(value=1)
        self.force_override = tk.BooleanVar(value=False)

        self.image_files = []
        self.current_image_index = 0

        self.create_widgets()
        self.style_widgets()
        self.populate_subfolders()
        self.algorithm_menu.bind("<<ComboboxSelected>>", self.show_preview)

    def create_widgets(self):
        frame = ttk.Frame(self.root, padding="0 0 0 0")
        frame.pack(fill=tk.BOTH, expand=True)

        left_frame = ttk.Frame(frame)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=0, pady=0)

        right_frame = ttk.Frame(frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=0, pady=0, expand=True)

        # Subfolder selection
        subfolder_frame = ttk.LabelFrame(left_frame, text="Select Subfolder", padding="10 10 10 10")
        subfolder_frame.pack(fill=tk.X, padx=10, pady=5)
        self.subfolder_frame = subfolder_frame  # Save reference for dynamic radio button creation

        # Algorithm selection
        algorithm_frame = ttk.LabelFrame(left_frame, text="Processing", padding="10 10 10 10")
        algorithm_frame.pack(fill=tk.X, padx=10, pady=5)

        self.algorithm_menu = ttk.Combobox(algorithm_frame, textvariable=self.selected_algorithm,
                                           values=list(self.processing_algorithms.keys()))
        self.algorithm_menu.pack(fill=tk.X, padx=5, side="top")

        # Process button
        self.process_button = ttk.Button(algorithm_frame, text="Process All Images", command=self.process_all_images)
        self.process_button.pack(expand=True, padx=5, pady=10, side="left", fill=tk.BOTH)

        # Override checkbox
        self.override_checkbox = ttk.Checkbutton(algorithm_frame, text="Override existing files",
                                                 variable=self.force_override)
        self.override_checkbox.pack(padx=10, pady=10, side="left")

        # Progress bar
        self.progress_bar = ttk.Progressbar(left_frame, orient="horizontal", mode="determinate")
        self.progress_bar.pack(fill=tk.X, padx=10, pady=10)

        # Log text box
        log_frame = ttk.LabelFrame(left_frame, text="Log", padding="10 10 10 10")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, height=15, state='disabled')
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # Preview area
        self.preview_area = ttk.Frame(right_frame)
        self.preview_area.pack(fill=tk.X, expand=True, padx=0, pady=0)

        # Upsampling options
        self.upsampling_frame = ttk.LabelFrame(right_frame, text="Upsampling", padding="10 10 10 10")
        self.upsampling_frame.pack(fill=tk.X, pady=10, side='bottom')
        for value, text in [(1, "1x"), (2, "4x"), (4, "8x"), (8, "16x")]:
            rb = ttk.Radiobutton(self.upsampling_frame, text=text, variable=self.selected_upsampling, value=value,
                                 command=self.update_upsampling)
            rb.pack(side=tk.LEFT, padx=10)

        # Navigation buttons
        nav_frame = ttk.Frame(right_frame)
        nav_frame.pack(fill=tk.X, pady=0, side="bottom", )

        self.prev_button = ttk.Button(nav_frame, text="Previous", command=self.show_previous_image)
        self.prev_button.pack(side=tk.LEFT, padx=(0, 0), pady=0)

        self.process_image_button = ttk.Button(nav_frame, text="Process Image", command=self.process_current_image)
        self.process_image_button.pack(side=tk.LEFT, padx=0, pady=0)

        self.next_button = ttk.Button(nav_frame, text="Next", command=self.show_next_image)
        self.next_button.pack(side=tk.RIGHT, padx=(0, 0), pady=0)

        # Center the process image button between previous and next
        self.process_image_button.pack_configure(
            padx=(self.prev_button.winfo_reqwidth() + 20, self.next_button.winfo_reqwidth() + 20))

    def style_widgets(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TButton', font=('Helvetica', 12), padding=10)
        style.configure('TLabel', font=('Helvetica', 12))
        style.configure('TEntry', font=('Helvetica', 12))
        style.configure('TCombobox', font=('Helvetica', 12))
        style.configure('TFrame', padding=10)
        style.configure('TLabelframe', font=('Helvetica', 12))
        style.configure('TCheckbutton', font=('Helvetica', 12))

    def populate_subfolders(self):
        # Clear existing radio buttons
        for widget in self.subfolder_frame.winfo_children():
            widget.destroy()

        subfolders = [f.name for f in os.scandir(self.input_folder) if f.is_dir()]
        if not subfolders:
            messagebox.showwarning("No Subfolders", "No subfolders found in the input folder.")
            return

        for subfolder in subfolders:
            ttk.Radiobutton(self.subfolder_frame, text=subfolder, variable=self.selected_subfolder, value=subfolder,
                            command=self.show_preview).pack(anchor=tk.W, padx=5, pady=2)

        if subfolders:
            self.selected_subfolder.set(subfolders[0])  # Select the first subfolder by default
            self.show_preview()

    def show_preview(self, event=None):
        if not self.selected_subfolder.get():
            return

        input_subfolder = self.selected_subfolder.get()
        algorithm_name = self.selected_algorithm.get()
        algorithm = self.processing_algorithms.get(algorithm_name, self.default_algorithm)

        input_folder_path = os.path.join(self.input_folder, input_subfolder)
        self.image_files = [f for f in os.listdir(input_folder_path) if
                            f.lower().endswith(('png', 'jpg', 'jpeg', 'bmp', 'gif'))]
        if not self.image_files:
            self.log_message(f"No image files found in the input subfolder '{input_subfolder}'.")
            return

        self.current_image_index = 0
        self.display_image(algorithm)

    def update_upsampling(self):
        algorithm_name = self.selected_algorithm.get()
        algorithm = self.processing_algorithms.get(algorithm_name, self.default_algorithm)
        self.display_image(algorithm)

    def display_image(self, algorithm):
        if not self.image_files:
            return

        def dual_function(fn_a, fn_b):
            return lambda *x: (fn_a(*x), fn_b(*x))

        input_subfolder = self.selected_subfolder.get()
        input_folder_path = os.path.join(self.input_folder, input_subfolder)
        image_path = os.path.join(input_folder_path, self.image_files[self.current_image_index])

        image = Image.open(image_path).convert('RGB')

        # Get upsampling factor
        upsampling_factor = self.selected_upsampling.get()

        # Nearest neighbor upscaling for original and processed images
        original_upscaled = image.resize((image.width * upsampling_factor, image.height * upsampling_factor),
                                         Image.NEAREST)
        processed_image = algorithm(image)
        processed_upscaled = processed_image.resize(
            (processed_image.width * upsampling_factor, processed_image.height * upsampling_factor), Image.NEAREST)

        # Clear the preview area
        for widget in self.preview_area.winfo_children():
            widget.destroy()

        # Original image section
        original_frame = ttk.LabelFrame(self.preview_area, text="Original Image", padding="10 10 10 10")
        original_frame.pack(fill=tk.BOTH, expand=True, padx=0, pady=(0, 0), side="top")

        original_canvas = tk.Canvas(original_frame)

        preview_frame = ttk.LabelFrame(self.preview_area, text="Preview Image", padding="10 10 10 10")
        preview_canvas = tk.Canvas(preview_frame)

        original_scrollbar_y = ttk.Scrollbar(original_frame, orient="vertical",
                                             command=dual_function(preview_canvas.yview, original_canvas.yview))
        original_scrollbar_x = ttk.Scrollbar(original_frame, orient="horizontal",
                                             command=dual_function(preview_canvas.xview, original_canvas.xview))
        original_canvas.configure(yscrollcommand=original_scrollbar_y.set, xscrollcommand=original_scrollbar_x.set)

        original_scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        original_scrollbar_x.pack(side=tk.TOP, fill=tk.X)
        original_canvas.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

        original_inner_frame = ttk.Frame(original_canvas)
        original_canvas.create_window((0, 0), window=original_inner_frame, anchor="nw")
        original_inner_frame.bind("<Configure>",
                                  lambda e: original_canvas.configure(scrollregion=original_canvas.bbox("all")))

        original_image_label = tk.Label(original_inner_frame)
        original_image_label.pack()
        original_img_tk = ImageTk.PhotoImage(original_upscaled)
        original_image_label.config(image=original_img_tk)
        original_image_label.image = original_img_tk

        # Processed image section
        # preview_frame = ttk.LabelFrame(self.preview_area, text="Preview Image", padding="10 10 10 10")
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=0, pady=(10,0))

        preview_scrollbar_y = ttk.Scrollbar(preview_frame, orient="vertical",
                                            command=dual_function(preview_canvas.yview, original_canvas.yview))
        preview_scrollbar_x = ttk.Scrollbar(preview_frame, orient="horizontal",
                                            command=dual_function(preview_canvas.xview, original_canvas.xview))
        preview_canvas.configure(yscrollcommand=preview_scrollbar_y.set, xscrollcommand=preview_scrollbar_x.set)

        preview_scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        preview_scrollbar_x.pack(side=tk.TOP, fill=tk.X)
        preview_canvas.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

        preview_inner_frame = ttk.Frame(preview_canvas)
        preview_canvas.create_window((0, 0), window=preview_inner_frame, anchor="nw")
        preview_inner_frame.bind("<Configure>",
                                 lambda e: preview_canvas.configure(scrollregion=preview_canvas.bbox("all")))

        preview_image_label = tk.Label(preview_inner_frame)
        preview_image_label.pack()
        preview_img_tk = ImageTk.PhotoImage(processed_upscaled)
        preview_image_label.config(image=preview_img_tk)
        preview_image_label.image = preview_img_tk

        # Set canvas size to ensure the scrollbars appear as needed
        original_canvas.update_idletasks()
        preview_canvas.update_idletasks()
        original_canvas.configure(scrollregion=original_canvas.bbox("all"))
        preview_canvas.configure(scrollregion=preview_canvas.bbox("all"))

    def show_previous_image(self):
        if not self.image_files:
            return

        self.current_image_index = (self.current_image_index - 1) % len(self.image_files)
        algorithm_name = self.selected_algorithm.get()
        algorithm = self.processing_algorithms.get(algorithm_name, self.default_algorithm)
        self.display_image(algorithm)

    def show_next_image(self):
        if not self.image_files:
            return

        self.current_image_index = (self.current_image_index + 1) % len(self.image_files)
        algorithm_name = self.selected_algorithm.get()
        algorithm = self.processing_algorithms.get(algorithm_name, self.default_algorithm)
        self.display_image(algorithm)

    def process_current_image(self):
        if not self.image_files:
            return

        input_subfolder = self.selected_subfolder.get()
        output_subfolder = input_subfolder
        algorithm_name = self.selected_algorithm.get()
        algorithm = self.processing_algorithms.get(algorithm_name, self.default_algorithm)

        input_folder_path = os.path.join(self.input_folder, input_subfolder)
        image_name = self.image_files[self.current_image_index]
        input_image_path = os.path.join(input_folder_path, image_name)

        output_folder_path = os.path.join(self.output_folder, output_subfolder)
        if not os.path.exists(output_folder_path):
            os.makedirs(output_folder_path)

        name, ext = os.path.splitext(image_name)
        output_image_name = f"{name}_processed{ext}"
        output_image_path = os.path.join(output_folder_path, output_image_name)

        if os.path.exists(output_image_path) and not self.force_override.get():
            self.log_message(f"Skipping {image_name}: Output file already exists and force_override is False.")
            return

        try:
            image = Image.open(input_image_path).convert('RGB')
            processed_image = algorithm(image)
            processed_image.save(output_image_path)
            self.log_message(f"Processed and saved image as {output_image_name}")
        except Exception as e:
            self.log_message(f"Error processing {image_name}: {e}")

    def process_all_images(self):
        if not self.selected_subfolder.get():
            self.log_message("No subfolder selected for processing.")
            return

        input_subfolder = self.selected_subfolder.get()
        output_subfolder = input_subfolder
        algorithm_name = self.selected_algorithm.get()
        algorithm = self.processing_algorithms.get(algorithm_name, self.default_algorithm)

        self.progress_bar.start()
        self.log_message(f"Started processing images in '{input_subfolder}'.")

        input_folder_path = os.path.join(self.input_folder, input_subfolder)
        image_files = [f for f in os.listdir(input_folder_path) if
                       f.lower().endswith(('png', 'jpg', 'jpeg', 'bmp', 'gif'))]

        total_files = len(image_files)
        for i, image_name in enumerate(tqdm(image_files, desc="Processing images", unit="image")):
            input_image_path = os.path.join(input_folder_path, image_name)
            output_folder_path = os.path.join(self.output_folder, output_subfolder)
            if not os.path.exists(output_folder_path):
                os.makedirs(output_folder_path)

            name, ext = os.path.splitext(image_name)
            output_image_name = f"{name}_processed{ext}"
            output_image_path = os.path.join(output_folder_path, output_image_name)

            if os.path.exists(output_image_path) and not self.force_override.get():
                self.log_message(f"Skipping {image_name}: Output file already exists and force_override is False.")
                continue

            try:
                image = Image.open(input_image_path).convert('RGB')
                processed_image = algorithm(image)
                processed_image.save(output_image_path)
                self.log_message(f"Processed and saved image as {output_image_name}")
            except Exception as e:
                self.log_message(f"Error processing {image_name}: {e}")

        self.progress_bar.stop()
        self.log_message(f"All images in '{input_subfolder}' have been processed.")

    def log_message(self, message: str):
        current_time = time.strftime("%Y-%m-%d %H:%M:%S")
        full_message = f"{current_time}: {message}\n"

        self.log_text.config(state='normal')
        self.log_text.insert('1.0', full_message)
        self.log_text.config(state='disabled')
