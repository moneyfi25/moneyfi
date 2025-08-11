#!/usr/bin/env python3
"""
Cross-platform GUI for Marker PDF processing tool
Supports Windows, macOS, and Linux
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import subprocess
import threading
import queue
import os
import sys
import json
from pathlib import Path
import re
from datetime import datetime

class MarkerPDFGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Marker PDF Processing Tool")
        self.root.geometry("1000x800")
        self.root.minsize(900, 700)
        
        # Variables
        self.input_files = []
        self.output_dir = tk.StringVar()
        self.page_range = tk.StringVar(value="")
        self.output_format = tk.StringVar(value="markdown")
        
        # Basic options
        self.use_llm = tk.BooleanVar(value=False)
        self.force_ocr = tk.BooleanVar(value=False)
        self.strip_existing_ocr = tk.BooleanVar(value=False)
        self.disable_image_extraction = tk.BooleanVar(value=False)
        self.disable_links = tk.BooleanVar(value=False)
        self.disable_ocr = tk.BooleanVar(value=False)
        self.paginate_output = tk.BooleanVar(value=False)
        self.debug = tk.BooleanVar(value=False)
        
        # LLM Service options
        self.llm_service = tk.StringVar(value="GoogleGeminiService")
        self.gemini_api_key = tk.StringVar()
        self.claude_api_key = tk.StringVar()
        self.openai_api_key = tk.StringVar()
        self.ollama_base_url = tk.StringVar(value="http://localhost:11434")
        self.ollama_model = tk.StringVar(value="llama3.2-vision")
        
        # Advanced options
        self.config_json = tk.StringVar()
        self.disable_multiprocessing = tk.BooleanVar(value=False)
        self.disable_tqdm = tk.BooleanVar(value=False)
        self.extract_images = tk.BooleanVar(value=True)
        self.lowres_image_dpi = tk.IntVar(value=96)
        self.highres_image_dpi = tk.IntVar(value=192)
        self.max_concurrency = tk.IntVar(value=3)
        
        # Processing state
        self.is_processing = False
        self.current_process = None
        self.log_queue = queue.Queue()
        
        self.setup_ui()
        self.check_marker_installation()
        
    def setup_ui(self):
        # Create main notebook for tabs
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Main tab
        main_frame = ttk.Frame(notebook)
        notebook.add(main_frame, text="Basic Settings")
        
        # Advanced tab
        advanced_frame = ttk.Frame(notebook)
        notebook.add(advanced_frame, text="Advanced Options")
        
        # Progress tab
        progress_frame = ttk.Frame(notebook)
        notebook.add(progress_frame, text="Progress & Logs")
        
        self.setup_main_tab(main_frame)
        self.setup_advanced_tab(advanced_frame)
        self.setup_progress_tab(progress_frame)
        
    def setup_main_tab(self, parent):
        # File selection frame
        file_frame = ttk.LabelFrame(parent, text="Input Files", padding="5")
        file_frame.pack(fill='x', padx=5, pady=5)
        
        # File selection buttons
        btn_frame = ttk.Frame(file_frame)
        btn_frame.pack(fill='x', pady=(0, 5))
        
        ttk.Button(btn_frame, text="Select Files", 
                  command=self.select_files).pack(side='left', padx=(0, 5))
        ttk.Button(btn_frame, text="Select Folder", 
                  command=self.select_folder).pack(side='left', padx=(0, 5))
        ttk.Button(btn_frame, text="Clear All", 
                  command=self.clear_files).pack(side='left', padx=(0, 5))
        
        # File list
        list_frame = ttk.Frame(file_frame)
        list_frame.pack(fill='both', expand=True)
        
        self.file_listbox = tk.Listbox(list_frame, height=6)
        file_scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.file_listbox.yview)
        self.file_listbox.configure(yscrollcommand=file_scrollbar.set)
        
        self.file_listbox.pack(side='left', fill='both', expand=True)
        file_scrollbar.pack(side='right', fill='y')
        
        # Output directory frame
        output_frame = ttk.LabelFrame(parent, text="Output Directory", padding="5")
        output_frame.pack(fill='x', padx=5, pady=5)
        
        output_entry_frame = ttk.Frame(output_frame)
        output_entry_frame.pack(fill='x')
        
        ttk.Entry(output_entry_frame, textvariable=self.output_dir, width=60).pack(side='left', fill='x', expand=True)
        ttk.Button(output_entry_frame, text="Browse", 
                  command=self.select_output_dir).pack(side='right', padx=(5, 0))
        
        # Basic options frame
        options_frame = ttk.LabelFrame(parent, text="Basic Processing Options", padding="5")
        options_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Create two columns for options
        left_options = ttk.Frame(options_frame)
        left_options.pack(side='left', fill='both', expand=True, padx=(0, 10))
        
        right_options = ttk.Frame(options_frame)
        right_options.pack(side='right', fill='both', expand=True)
        
        # Left column options
        ttk.Label(left_options, text="Page Range:").pack(anchor='w')
        ttk.Entry(left_options, textvariable=self.page_range, width=30).pack(fill='x', pady=(0, 5))
        ttk.Label(left_options, text='Examples: "0-5", "0,3,5-10", leave empty for all').pack(anchor='w', pady=(0, 10))
        
        ttk.Label(left_options, text="Output Format:").pack(anchor='w')
        format_combo = ttk.Combobox(left_options, textvariable=self.output_format, 
                                   values=["markdown", "json", "html", "chunks"], state="readonly")
        format_combo.pack(fill='x', pady=(0, 10))
        
        # Basic checkboxes - left column
        ttk.Checkbutton(left_options, text="Use LLM Enhancement", 
                       variable=self.use_llm, command=self.on_llm_toggle).pack(anchor='w', pady=2)
        ttk.Checkbutton(left_options, text="Force OCR", 
                       variable=self.force_ocr).pack(anchor='w', pady=2)
        ttk.Checkbutton(left_options, text="Strip Existing OCR", 
                       variable=self.strip_existing_ocr).pack(anchor='w', pady=2)
        ttk.Checkbutton(left_options, text="Disable OCR", 
                       variable=self.disable_ocr).pack(anchor='w', pady=2)
        
        # Right column checkboxes
        ttk.Checkbutton(right_options, text="Disable Image Extraction", 
                       variable=self.disable_image_extraction).pack(anchor='w', pady=2)
        ttk.Checkbutton(right_options, text="Disable Links", 
                       variable=self.disable_links).pack(anchor='w', pady=2)
        ttk.Checkbutton(right_options, text="Paginate Output", 
                       variable=self.paginate_output).pack(anchor='w', pady=2)
        ttk.Checkbutton(right_options, text="Debug Mode", 
                       variable=self.debug).pack(anchor='w', pady=2)
        
        # LLM Configuration frame
        self.llm_frame = ttk.LabelFrame(parent, text="LLM Configuration (when LLM Enhancement is enabled)", padding="5")
        self.llm_frame.pack(fill='x', padx=5, pady=5)
        
        # LLM Service selection
        ttk.Label(self.llm_frame, text="LLM Service:").pack(anchor='w')
        service_combo = ttk.Combobox(self.llm_frame, textvariable=self.llm_service, 
                                    values=["GoogleGeminiService", "ClaudeService", "OpenAIService", "OllamaService"], 
                                    state="readonly")
        service_combo.pack(fill='x', pady=(0, 10))
        service_combo.bind('<<ComboboxSelected>>', self.on_llm_service_change)
        
        # API Key frames
        self.api_key_frames = {}
        
        # Gemini API Key
        gemini_frame = ttk.Frame(self.llm_frame)
        ttk.Label(gemini_frame, text="Gemini API Key:").pack(anchor='w')
        ttk.Entry(gemini_frame, textvariable=self.gemini_api_key, show='*', width=50).pack(fill='x')
        self.api_key_frames['GoogleGeminiService'] = gemini_frame
        
        # Claude API Key
        claude_frame = ttk.Frame(self.llm_frame)
        ttk.Label(claude_frame, text="Claude API Key:").pack(anchor='w')
        ttk.Entry(claude_frame, textvariable=self.claude_api_key, show='*', width=50).pack(fill='x')
        self.api_key_frames['ClaudeService'] = claude_frame
        
        # OpenAI API Key
        openai_frame = ttk.Frame(self.llm_frame)
        ttk.Label(openai_frame, text="OpenAI API Key:").pack(anchor='w')
        ttk.Entry(openai_frame, textvariable=self.openai_api_key, show='*', width=50).pack(fill='x')
        self.api_key_frames['OpenAIService'] = openai_frame
        
        # Ollama settings
        ollama_frame = ttk.Frame(self.llm_frame)
        ttk.Label(ollama_frame, text="Ollama Base URL:").pack(anchor='w')
        ttk.Entry(ollama_frame, textvariable=self.ollama_base_url, width=50).pack(fill='x', pady=(0, 5))
        ttk.Label(ollama_frame, text="Ollama Model:").pack(anchor='w')
        ttk.Entry(ollama_frame, textvariable=self.ollama_model, width=50).pack(fill='x')
        self.api_key_frames['OllamaService'] = ollama_frame
        
        # Show initial LLM config
        self.on_llm_service_change()
        self.on_llm_toggle()
        
        # Control buttons
        control_frame = ttk.Frame(parent)
        control_frame.pack(fill='x', padx=5, pady=10)
        
        self.process_btn = ttk.Button(control_frame, text="Start Processing", 
                                     command=self.start_processing)
        self.process_btn.pack(side='left', padx=(0, 5))
        
        self.stop_btn = ttk.Button(control_frame, text="Stop Processing", 
                                  command=self.stop_processing, state='disabled')
        self.stop_btn.pack(side='left', padx=(0, 5))
        
        ttk.Button(control_frame, text="Open Output Folder", 
                  command=self.open_output_folder).pack(side='right')
        
    def setup_advanced_tab(self, parent):
        # Create scrollable frame
        canvas = tk.Canvas(parent)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Advanced Configuration Options
        config_frame = ttk.LabelFrame(scrollable_frame, text="Configuration", padding="5")
        config_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(config_frame, text="Config JSON File:").pack(anchor='w')
        config_entry_frame = ttk.Frame(config_frame)
        config_entry_frame.pack(fill='x', pady=(0, 5))
        ttk.Entry(config_entry_frame, textvariable=self.config_json).pack(side='left', fill='x', expand=True)
        ttk.Button(config_entry_frame, text="Browse", command=self.select_config_json).pack(side='right', padx=(5, 0))
        
        # Performance Options
        perf_frame = ttk.LabelFrame(scrollable_frame, text="Performance Options", padding="5")
        perf_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Checkbutton(perf_frame, text="Disable Multiprocessing", 
                       variable=self.disable_multiprocessing).pack(anchor='w', pady=2)
        ttk.Checkbutton(perf_frame, text="Disable Progress Bars", 
                       variable=self.disable_tqdm).pack(anchor='w', pady=2)
        
        # Create two columns for numeric options
        numeric_frame = ttk.Frame(perf_frame)
        numeric_frame.pack(fill='x', pady=5)
        
        left_numeric = ttk.Frame(numeric_frame)
        left_numeric.pack(side='left', fill='both', expand=True, padx=(0, 10))
        
        right_numeric = ttk.Frame(numeric_frame)
        right_numeric.pack(side='right', fill='both', expand=True)
        
        # Left column
        ttk.Label(left_numeric, text="Low-res Image DPI:").pack(anchor='w')
        ttk.Entry(left_numeric, textvariable=self.lowres_image_dpi, width=10).pack(anchor='w', pady=(0, 5))
        
        ttk.Label(left_numeric, text="High-res Image DPI:").pack(anchor='w')
        ttk.Entry(left_numeric, textvariable=self.highres_image_dpi, width=10).pack(anchor='w', pady=(0, 5))
        
        # Right column
        ttk.Label(right_numeric, text="Max Concurrency:").pack(anchor='w')
        ttk.Entry(right_numeric, textvariable=self.max_concurrency, width=10).pack(anchor='w', pady=(0, 5))
        
        # Image Options
        image_frame = ttk.LabelFrame(scrollable_frame, text="Image Options", padding="5")
        image_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Checkbutton(image_frame, text="Extract Images", 
                       variable=self.extract_images).pack(anchor='w', pady=2)
        
        # Pack the canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Bind mousewheel to canvas
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
    def setup_progress_tab(self, parent):
        # Progress frame
        progress_info_frame = ttk.LabelFrame(parent, text="Progress Information", padding="5")
        progress_info_frame.pack(fill='x', padx=5, pady=5)
        
        # Overall progress
        ttk.Label(progress_info_frame, text="Overall Progress:").pack(anchor='w')
        self.overall_progress = ttk.Progressbar(progress_info_frame, mode='determinate')
        self.overall_progress.pack(fill='x', pady=(0, 5))
        
        self.overall_label = ttk.Label(progress_info_frame, text="Ready")
        self.overall_label.pack(anchor='w', pady=(0, 5))
        
        # Current file progress
        ttk.Label(progress_info_frame, text="Current File:").pack(anchor='w')
        self.current_progress = ttk.Progressbar(progress_info_frame, mode='indeterminate')
        self.current_progress.pack(fill='x', pady=(0, 5))
        
        self.current_label = ttk.Label(progress_info_frame, text="No file processing")
        self.current_label.pack(anchor='w')
        
        # Log frame
        log_frame = ttk.LabelFrame(parent, text="Processing Logs", padding="5")
        log_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Log text area
        self.log_text = scrolledtext.ScrolledText(log_frame, height=20, wrap='word')
        self.log_text.pack(fill='both', expand=True)
        
        # Log control buttons
        log_btn_frame = ttk.Frame(log_frame)
        log_btn_frame.pack(fill='x', pady=(5, 0))
        
        ttk.Button(log_btn_frame, text="Clear Logs", 
                  command=self.clear_logs).pack(side='left')
        ttk.Button(log_btn_frame, text="Save Logs", 
                  command=self.save_logs).pack(side='left', padx=(5, 0))
        
    def on_llm_toggle(self):
        """Show/hide LLM configuration based on checkbox"""
        if self.use_llm.get():
            self.llm_frame.pack(fill='x', padx=5, pady=5)
        else:
            self.llm_frame.pack_forget()
    
    def on_llm_service_change(self, event=None):
        """Show appropriate API key fields based on selected service"""
        # Hide all API key frames
        for frame in self.api_key_frames.values():
            frame.pack_forget()
        
        # Show the relevant frame
        service = self.llm_service.get()
        if service in self.api_key_frames:
            self.api_key_frames[service].pack(fill='x', pady=(0, 5))
    
    def select_config_json(self):
        """Select config JSON file"""
        filename = filedialog.askopenfilename(
            title="Select Config JSON File",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            self.config_json.set(filename)
    
    def check_marker_installation(self):
        """Check if marker is installed and accessible"""
        try:
            result = subprocess.run(['marker_single', '--help'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                self.log_message("Warning: marker_single command not found. Please install marker.")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            self.log_message("Warning: marker_single command not found. Please install marker from: https://github.com/datalab-to/marker")
            
    def select_files(self):
        """Select individual PDF files"""
        files = filedialog.askopenfilenames(
            title="Select PDF Files",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        for file in files:
            if file not in self.input_files:
                self.input_files.append(file)
        self.update_file_list()
        
    def select_folder(self):
        """Select folder containing PDF files"""
        folder = filedialog.askdirectory(title="Select Folder with PDF Files")
        if folder:
            pdf_files = list(Path(folder).glob("*.pdf"))
            for pdf_file in pdf_files:
                file_path = str(pdf_file)
                if file_path not in self.input_files:
                    self.input_files.append(file_path)
            self.update_file_list()
            
    def clear_files(self):
        """Clear all selected files"""
        self.input_files.clear()
        self.update_file_list()
        
    def update_file_list(self):
        """Update the file listbox"""
        self.file_listbox.delete(0, tk.END)
        for file in self.input_files:
            self.file_listbox.insert(tk.END, os.path.basename(file))
            
    def select_output_dir(self):
        """Select output directory"""
        directory = filedialog.askdirectory(title="Select Output Directory")
        if directory:
            self.output_dir.set(directory)
            
    def log_message(self, message):
        """Add message to log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        # Thread-safe logging
        self.root.after(0, lambda: self.log_text.insert(tk.END, log_entry))
        self.root.after(0, lambda: self.log_text.see(tk.END))
        
    def clear_logs(self):
        """Clear the log text area"""
        self.log_text.delete(1.0, tk.END)
        
    def save_logs(self):
        """Save logs to file"""
        content = self.log_text.get(1.0, tk.END)
        if content.strip():
            filename = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
            )
            if filename:
                with open(filename, 'w') as f:
                    f.write(content)
                messagebox.showinfo("Success", f"Logs saved to {filename}")
                
    def build_command(self, pdf_file):
        """Build marker command for a single PDF file"""
        cmd = ['marker_single', pdf_file]
        
        # Basic options
        if self.page_range.get().strip():
            cmd.extend(['--page_range', self.page_range.get().strip()])
            
        cmd.extend(['--output_format', self.output_format.get()])
        
        if self.output_dir.get():
            cmd.extend(['--output_dir', self.output_dir.get()])
            
        if self.paginate_output.get():
            cmd.append('--paginate_output')
            
        if self.force_ocr.get():
            cmd.append('--force_ocr')
            
        if self.strip_existing_ocr.get():
            cmd.append('--strip_existing_ocr')
            
        if self.disable_image_extraction.get():
            cmd.append('--disable_image_extraction')
            
        if self.disable_links.get():
            cmd.append('--disable_links')
            
        if self.disable_ocr.get():
            cmd.append('--disable_ocr')
            
        if self.debug.get():
            cmd.append('--debug')
        
        # LLM options
        if self.use_llm.get():
            cmd.append('--use_llm')
            
            # Add LLM service
            service_map = {
                'GoogleGeminiService': 'marker.services.gemini.GoogleGeminiService',
                'ClaudeService': 'marker.services.claude.ClaudeService',
                'OpenAIService': 'marker.services.openai.OpenAIService',
                'OllamaService': 'marker.services.ollama.OllamaService'
            }
            
            service = self.llm_service.get()
            if service in service_map:
                cmd.extend(['--llm_service', service_map[service]])
            
            # Add API keys based on service
            if service == 'GoogleGeminiService' and self.gemini_api_key.get():
                cmd.extend(['--gemini_api_key', self.gemini_api_key.get()])
            elif service == 'ClaudeService' and self.claude_api_key.get():
                cmd.extend(['--claude_api_key', self.claude_api_key.get()])
            elif service == 'OpenAIService' and self.openai_api_key.get():
                cmd.extend(['--openai_api_key', self.openai_api_key.get()])
            elif service == 'OllamaService':
                if self.ollama_base_url.get():
                    cmd.extend(['--ollama_base_url', self.ollama_base_url.get()])
                if self.ollama_model.get():
                    cmd.extend(['--ollama_model', self.ollama_model.get()])
        
        # Advanced options
        if self.config_json.get():
            cmd.extend(['--config_json', self.config_json.get()])
            
        if self.disable_multiprocessing.get():
            cmd.append('--disable_multiprocessing')
            
        if self.disable_tqdm.get():
            cmd.append('--disable_tqdm')
            
        if not self.extract_images.get():
            cmd.extend(['--extract_images', 'False'])
            
        if self.lowres_image_dpi.get() != 96:
            cmd.extend(['--lowres_image_dpi', str(self.lowres_image_dpi.get())])
            
        if self.highres_image_dpi.get() != 192:
            cmd.extend(['--highres_image_dpi', str(self.highres_image_dpi.get())])
            
        if self.max_concurrency.get() != 3:
            cmd.extend(['--max_concurrency', str(self.max_concurrency.get())])
            
        return cmd
        
    def start_processing(self):
        """Start processing selected PDF files"""
        if not self.input_files:
            messagebox.showerror("Error", "Please select at least one PDF file.")
            return
            
        if not self.output_dir.get():
            messagebox.showerror("Error", "Please select an output directory.")
            return
        
        # Validate LLM settings if LLM is enabled
        if self.use_llm.get():
            service = self.llm_service.get()
            if service == 'GoogleGeminiService' and not self.gemini_api_key.get():
                messagebox.showerror("Error", "Please enter your Gemini API key.")
                return
            elif service == 'ClaudeService' and not self.claude_api_key.get():
                messagebox.showerror("Error", "Please enter your Claude API key.")
                return
            elif service == 'OpenAIService' and not self.openai_api_key.get():
                messagebox.showerror("Error", "Please enter your OpenAI API key.")
                return
            
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir.get(), exist_ok=True)
        
        self.is_processing = True
        self.process_btn.config(state='disabled')
        self.stop_btn.config(state='normal')
        
        # Reset progress bars
        self.overall_progress.config(maximum=len(self.input_files), value=0)
        self.current_progress.start()
        
        self.log_message(f"Starting processing of {len(self.input_files)} files...")
        
        # Start processing in separate thread
        self.processing_thread = threading.Thread(target=self.process_files)
        self.processing_thread.daemon = True
        self.processing_thread.start()
        
    def process_files(self):
        """Process all selected PDF files"""
        successful = 0
        failed = 0
        
        for i, pdf_file in enumerate(self.input_files):
            if not self.is_processing:  # Check if stopped
                break
                
            filename = os.path.basename(pdf_file)
            self.root.after(0, lambda f=filename: self.current_label.config(text=f"Processing: {f}"))
            self.log_message(f"Processing file {i+1}/{len(self.input_files)}: {filename}")
            
            try:
                cmd = self.build_command(pdf_file)
                self.log_message(f"Command: {' '.join(cmd)}")
                
                # Run the marker command
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    universal_newlines=True,
                    bufsize=1
                )
                
                self.current_process = process
                
                # Read output line by line
                while True:
                    output = process.stdout.readline()
                    if output == '' and process.poll() is not None:
                        break
                    if output:
                        self.log_message(output.strip())
                        
                        # Try to extract page information from output
                        page_match = re.search(r'page (\d+)', output.lower())
                        if page_match:
                            page_num = page_match.group(1)
                            self.root.after(0, lambda p=page_num, f=filename: 
                                          self.current_label.config(text=f"Processing: {f} (Page {p})"))
                
                # Wait for process to complete
                return_code = process.wait()
                
                if return_code == 0:
                    successful += 1
                    self.log_message(f"✓ Successfully processed: {filename}")
                else:
                    failed += 1
                    self.log_message(f"✗ Failed to process: {filename} (return code: {return_code})")
                    
            except Exception as e:
                failed += 1
                self.log_message(f"✗ Error processing {filename}: {str(e)}")
            
            # Update overall progress
            self.root.after(0, lambda v=i+1: self.overall_progress.config(value=v))
            self.root.after(0, lambda: self.overall_label.config(
                text=f"Processed {i+1}/{len(self.input_files)} files"))
        
        # Processing complete
        self.root.after(0, self.processing_complete)
        self.log_message(f"Processing complete! Successful: {successful}, Failed: {failed}")
        
    def processing_complete(self):
        """Called when processing is complete"""
        self.is_processing = False
        self.current_process = None
        self.process_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        self.current_progress.stop()
        self.current_label.config(text="Processing complete")
        
        messagebox.showinfo("Complete", "Processing finished! Check the logs for details.")
        
    def stop_processing(self):
        """Stop the current processing"""
        self.is_processing = False
        if self.current_process:
            self.current_process.terminate()
            self.current_process = None
        self.log_message("Processing stopped by user.")
        self.processing_complete()
        
    def open_output_folder(self):
        """Open the output folder in file explorer"""
        if self.output_dir.get() and os.path.exists(self.output_dir.get()):
            if sys.platform == "win32":
                os.startfile(self.output_dir.get())
            elif sys.platform == "darwin":
                subprocess.run(["open", self.output_dir.get()])
            else:  # linux
                subprocess.run(["xdg-open", self.output_dir.get()])
        else:
            messagebox.showerror("Error", "Output directory does not exist.")

def main():
    root = tk.Tk()
    app = MarkerPDFGUI(root)
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()