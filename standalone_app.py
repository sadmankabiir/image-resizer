#!/usr/bin/env python3
"""
Standalone Image Resizer with GUI
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import threading
from PIL import Image, ImageTk
import tempfile
import zipfile
from image_resizer import resize_images, resize_folder, ResizeMode, get_image_info
from config import get_config, get_resize_mode_info, get_all_resize_modes, NAMING_PATTERNS

class ImageResizerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Advanced Image Resizer")
        self.root.geometry("800x600")
        
        # Variables
        self.input_files = []
        self.output_dir = os.path.join(os.getcwd(), "resized_images")
        self.processing = False
        
        self.setup_ui()
        
    def setup_ui(self):
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Input section
        ttk.Label(main_frame, text="Input Files:", font=('Arial', 10, 'bold')).grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        input_frame = ttk.Frame(main_frame)
        input_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Button(input_frame, text="Add Images", command=self.add_images).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(input_frame, text="Add Folder (ZIP)", command=self.add_zip_folder).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(input_frame, text="Clear All", command=self.clear_files).pack(side=tk.LEFT)
        
        # Files list
        self.files_listbox = tk.Listbox(main_frame, height=6)
        self.files_listbox.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Size settings
        ttk.Label(main_frame, text="Size Settings:", font=('Arial', 10, 'bold')).grid(row=3, column=0, sticky=tk.W, pady=(10, 5))
        
        size_frame = ttk.Frame(main_frame)
        size_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(size_frame, text="Width:").grid(row=0, column=0, sticky=tk.W)
        self.width_var = tk.IntVar(value=800)
        ttk.Spinbox(size_frame, from_=1, to=5000, textvariable=self.width_var, width=10).grid(row=0, column=1, padx=(5, 15))
        
        ttk.Label(size_frame, text="Height:").grid(row=0, column=2, sticky=tk.W)
        self.height_var = tk.IntVar(value=600)
        ttk.Spinbox(size_frame, from_=1, to=5000, textvariable=self.height_var, width=10).grid(row=0, column=3, padx=(5, 0))
        
        # Resize mode
        ttk.Label(size_frame, text="Mode:").grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        self.mode_var = tk.StringVar(value="stretch")
        mode_combo = ttk.Combobox(size_frame, textvariable=self.mode_var, width=15)
        mode_combo['values'] = list(get_all_resize_modes().keys())
        mode_combo.grid(row=1, column=1, columnspan=2, sticky=tk.W, padx=(5, 0), pady=(5, 0))
        
        # Output settings
        ttk.Label(main_frame, text="Output Settings:", font=('Arial', 10, 'bold')).grid(row=5, column=0, sticky=tk.W, pady=(10, 5))
        
        output_frame = ttk.Frame(main_frame)
        output_frame.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(output_frame, text="Format:").grid(row=0, column=0, sticky=tk.W)
        self.format_var = tk.StringVar(value="JPEG")
        format_combo = ttk.Combobox(output_frame, textvariable=self.format_var, width=10)
        format_combo['values'] = ['JPEG', 'PNG', 'WEBP']
        format_combo.grid(row=0, column=1, sticky=tk.W, padx=(5, 15))
        
        ttk.Label(output_frame, text="Quality:").grid(row=0, column=2, sticky=tk.W)
        self.quality_var = tk.IntVar(value=85)
        ttk.Scale(output_frame, from_=1, to=100, variable=self.quality_var, orient=tk.HORIZONTAL, length=100).grid(row=0, column=3, padx=(5, 5))
        self.quality_label = ttk.Label(output_frame, text="85")
        self.quality_label.grid(row=0, column=4)
        self.quality_var.trace('w', lambda *args: self.quality_label.config(text=str(self.quality_var.get())))
        
        self.preserve_aspect_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(output_frame, text="Preserve Aspect Ratio", variable=self.preserve_aspect_var).grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=(5, 0))
        
        self.preserve_metadata_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(output_frame, text="Preserve Metadata", variable=self.preserve_metadata_var).grid(row=1, column=2, columnspan=2, sticky=tk.W, pady=(5, 0))
        
        # Output directory
        dir_frame = ttk.Frame(main_frame)
        dir_frame.grid(row=7, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(dir_frame, text="Output Directory:").pack(side=tk.LEFT)
        self.dir_label = ttk.Label(dir_frame, text=self.output_dir)
        self.dir_label.pack(side=tk.LEFT, padx=(5, 5))
        ttk.Button(dir_frame, text="Browse", command=self.browse_output_dir).pack(side=tk.LEFT)
        
        # Progress
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(main_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.grid(row=8, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 5))
        
        self.status_label = ttk.Label(main_frame, text="Ready")
        self.status_label.grid(row=9, column=0, columnspan=3, sticky=tk.W)
        
        # Process button
        self.process_button = ttk.Button(main_frame, text="Resize Images", command=self.process_images)
        self.process_button.grid(row=10, column=0, columnspan=3, pady=(10, 0))
        
    def add_images(self):
        files = filedialog.askopenfilenames(
            title="Select Images",
            filetypes=[
                ("Image files", "*.jpg *.jpeg *.png *.webp *.bmp *.tiff *.gif"),
                ("All files", "*.*")
            ]
        )
        if files:
            self.input_files.extend(files)
            self.update_files_list()
            
    def add_zip_folder(self):
        zip_file = filedialog.askopenfilename(
            title="Select ZIP File",
            filetypes=[("ZIP files", "*.zip")]
        )
        if zip_file:
            try:
                # Extract ZIP to temp directory
                with tempfile.TemporaryDirectory() as temp_dir:
                    with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                        zip_ref.extractall(temp_dir)
                    
                    # Find all image files
                    for root, dirs, files in os.walk(temp_dir):
                        for file in files:
                            if file.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff', '.gif')):
                                self.input_files.append(os.path.join(root, file))
                    
                    self.update_files_list()
            except zipfile.BadZipFile:
                messagebox.showerror("Error", "Invalid ZIP file. Please select a valid ZIP file.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to extract ZIP file: {e}")
                
    def clear_files(self):
        self.input_files.clear()
        self.update_files_list()
        
    def update_files_list(self):
        self.files_listbox.delete(0, tk.END)
        for file in self.input_files:
            self.files_listbox.insert(tk.END, os.path.basename(file))
            
    def browse_output_dir(self):
        directory = filedialog.askdirectory(title="Select Output Directory")
        if directory:
            self.output_dir = directory
            self.dir_label.config(text=directory)
            
    def progress_callback(self, current, total):
        progress = (current / total) * 100
        self.progress_var.set(progress)
        self.status_label.config(text=f"Processing {current}/{total} images...")
        self.root.update_idletasks()
        
    def process_images(self):
        if not self.input_files:
            messagebox.showwarning("No Files", "Please add images to resize.")
            return
            
        if self.processing:
            return
            
        self.processing = True
        self.process_button.config(state='disabled')
        self.progress_var.set(0)
        
        # Run processing in separate thread
        thread = threading.Thread(target=self._process_images_thread)
        thread.daemon = True
        thread.start()
        
    def _process_images_thread(self):
        try:
            # Create output directory if it doesn't exist
            os.makedirs(self.output_dir, exist_ok=True)
            
            # Process images
            resized_files = resize_images(
                self.input_files,
                self.output_dir,
                self.width_var.get(),
                self.height_var.get(),
                self.quality_var.get(),
                self.format_var.get(),
                self.mode_var.get(),
                self.preserve_aspect_var.get(),
                self.preserve_metadata_var.get(),
                "{name}_{width}x{height}_resized",
                4,
                self.progress_callback
            )
            
            # Update UI on main thread
            self.root.after(0, self._processing_complete, len(resized_files))
            
        except Exception as e:
            self.root.after(0, self._processing_error, str(e))
            
    def _processing_complete(self, count):
        self.processing = False
        self.process_button.config(state='normal')
        self.status_label.config(text=f"Complete! Resized {count} images.")
        result = messagebox.showinfo("Success", f"Successfully resized {count} images!\n\nOpen output folder?")
        if result == 'ok':
            self._open_output_folder()
    
    def _open_output_folder(self):
        try:
            if os.name == 'nt':
                os.startfile(self.output_dir)
            elif os.name == 'posix':
                os.system(f'open "{self.output_dir}"')
            else:
                os.system(f'xdg-open "{self.output_dir}"')
        except Exception as e:
            messagebox.showerror("Error", f"Could not open folder: {e}")
        
    def _processing_error(self, error_msg):
        self.processing = False
        self.process_button.config(state='normal')
        self.status_label.config(text="Error occurred")
        messagebox.showerror("Error", f"An error occurred: {error_msg}")

def main():
    root = tk.Tk()
    app = ImageResizerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()