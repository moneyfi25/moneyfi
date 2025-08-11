#!/usr/bin/env python3
"""
Policy Processor GUI Application
A robust cross-platform tool for processing policy documents using OpenAI API
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import json
import os
import sys
from pathlib import Path
import threading
import configparser
import logging
from typing import Dict, Any, Optional
import re
from datetime import datetime

# Third-party imports (install via: pip install openai PyPDF2 markdown)
try:
    import openai
    from openai import OpenAI
except ImportError:
    messagebox.showerror("Missing Dependency", "Please install openai: pip install openai")
    sys.exit(1)

try:
    import PyPDF2
except ImportError:
    messagebox.showerror("Missing Dependency", "Please install PyPDF2: pip install PyPDF2")
    sys.exit(1)

try:
    import markdown
except ImportError:
    messagebox.showerror("Missing Dependency", "Please install markdown: pip install markdown")
    sys.exit(1)

class PolicyProcessorGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Policy Processor - OpenAI Integration")
        self.root.geometry("1000x800")
        self.root.minsize(800, 600)
        
        # Configure style for better compatibility
        try:
            style = ttk.Style()
            style.theme_use('clam')  # More compatible theme
        except Exception:
            pass  # Use default theme if clam is not available
        
        # Configure logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
        
        # Configuration file path
        self.config_file = Path.home() / '.policy_processor_config.ini'
        self.config = configparser.ConfigParser()
        
        # OpenAI client
        self.openai_client = None
        
        # Available models
        self.models = [
            "gpt-4o",
            "gpt-4o-mini", 
            "gpt-4-turbo",
            "gpt-4",
            "gpt-3.5-turbo",
            "o1-preview",
            "o1-mini"
        ]
        
        # Variables
        self.api_key_var = tk.StringVar()
        self.model_var = tk.StringVar(value=self.models[0])
        self.input_type_var = tk.StringVar(value="file")
        
        try:
            self.setup_ui()
            self.load_config()
        except Exception as e:
            self.logger.error(f"Error during initialization: {e}")
            messagebox.showerror("Initialization Error", f"Failed to initialize GUI: {str(e)}")
            sys.exit(1)
        
    def setup_ui(self):
        """Setup the user interface"""
        try:
            # Create notebook for tabs
            self.notebook = ttk.Notebook(self.root)
            self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
            
            # Setup tabs
            self.setup_main_tab()
            self.setup_config_tab()
            self.setup_output_tab()
        except Exception as e:
            self.logger.error(f"Error setting up UI: {e}")
            raise
        
    def setup_main_tab(self):
        """Setup the main processing tab"""
        main_frame = ttk.Frame(self.notebook)
        self.notebook.add(main_frame, text="Process Policy")
        
        # Input section
        input_frame = ttk.LabelFrame(main_frame, text="Input", padding="10")
        input_frame.pack(fill="x", padx=5, pady=5)
        
        # Input type selection
        ttk.Label(input_frame, text="Input Type:").pack(anchor="w")
        input_type_frame = ttk.Frame(input_frame)
        input_type_frame.pack(fill="x", pady=5)
        
        ttk.Radiobutton(input_type_frame, text="File Upload", variable=self.input_type_var, 
                       value="file").pack(side="left")
        ttk.Radiobutton(input_type_frame, text="Text Input", variable=self.input_type_var, 
                       value="text").pack(side="left", padx=(20, 0))
        
        # File selection frame
        self.file_frame = ttk.Frame(input_frame)
        self.file_frame.pack(fill="x", pady=5)
        
        ttk.Label(self.file_frame, text="Policy File:").pack(anchor="w")
        file_select_frame = ttk.Frame(self.file_frame)
        file_select_frame.pack(fill="x", pady=2)
        
        self.file_path_var = tk.StringVar()
        self.file_entry = ttk.Entry(file_select_frame, textvariable=self.file_path_var, 
                                   state="readonly")
        self.file_entry.pack(side="left", fill="x", expand=True)
        
        ttk.Button(file_select_frame, text="Browse", 
                  command=self.browse_file).pack(side="right", padx=(5, 0))
        
        # Text input frame
        self.text_frame = ttk.Frame(input_frame)
        self.text_frame.pack(fill="both", expand=True, pady=5)
        
        ttk.Label(self.text_frame, text="Policy Text:").pack(anchor="w")
        self.text_input = scrolledtext.ScrolledText(self.text_frame, height=10, wrap="word")
        self.text_input.pack(fill="both", expand=True, pady=2)
        
        # Prompt section
        prompt_frame = ttk.LabelFrame(main_frame, text="Processing Prompt", padding="10")
        prompt_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Prompt source selection
        prompt_source_frame = ttk.Frame(prompt_frame)
        prompt_source_frame.pack(fill="x", pady=(0, 5))
        
        self.prompt_source_var = tk.StringVar(value="text")
        ttk.Radiobutton(prompt_source_frame, text="Text Input", variable=self.prompt_source_var, 
                       value="text", command=self.on_prompt_source_change).pack(side="left")
        ttk.Radiobutton(prompt_source_frame, text="File Input", variable=self.prompt_source_var, 
                       value="file", command=self.on_prompt_source_change).pack(side="left", padx=(20, 0))
        
        # Prompt file selection frame
        self.prompt_file_frame = ttk.Frame(prompt_frame)
        
        ttk.Label(self.prompt_file_frame, text="Prompt File:").pack(anchor="w")
        prompt_file_select_frame = ttk.Frame(self.prompt_file_frame)
        prompt_file_select_frame.pack(fill="x", pady=2)
        
        self.prompt_file_path_var = tk.StringVar()
        self.prompt_file_entry = ttk.Entry(prompt_file_select_frame, textvariable=self.prompt_file_path_var, 
                                          state="readonly")
        self.prompt_file_entry.pack(side="left", fill="x", expand=True)
        
        ttk.Button(prompt_file_select_frame, text="Browse", 
                  command=self.browse_prompt_file).pack(side="right", padx=(5, 0))
        
        ttk.Button(prompt_file_select_frame, text="View/Edit", 
                  command=self.view_edit_prompt_file).pack(side="right", padx=(5, 0))
        
        # Prompt text frame
        self.prompt_text_frame = ttk.Frame(prompt_frame)
        self.prompt_text_frame.pack(fill="both", expand=True, pady=5)
        
        ttk.Label(self.prompt_text_frame, text="Custom Prompt:").pack(anchor="w")
        self.prompt_text = scrolledtext.ScrolledText(self.prompt_text_frame, height=5, wrap="word")
        self.prompt_text.pack(fill="both", expand=True, pady=2)
        
        # Default comprehensive insurance policy prompt
        default_prompt = """### 🧠 ROLE:
You are an expert insurance policy analyst. Your job is to extract structured data from Indian insurance policy brochures, used for financial advisory systems.

---

### 📌 INSTRUCTIONS:
✅ DO:
- Extract values exactly as written. Use `null` if not found.
- Normalize as per format instructions below.
- Include all keys even if values are missing.
- Return only the JSON object with no extra commentary.

❌ DO NOT:
- Assume missing values.
- Add extra fields.
- Return partial JSON or markdown.

---

### 🔎 VALUE NORMALIZATION – FIELD-WISE POSSIBLE VALUES
- `"premium_modes"`: ["Annual", "Half-Yearly", "Quarterly", "Monthly", "Single"]
- `"returns_type"`: "Guaranteed", "Bonus-Linked", "Return of Premium", "No Returns", "Market-Linked"
- `"risk_profile"`: "Low", "Medium", "High"
- `"bonus_type"`: ["Reversionary", "Terminal", "Cash", "Not Applicable"]
- `"guaranteed_income"`: true / false
- `"loan_available"`: true / false
- `"partial_withdrawal"`: true / false
- `"waiver_of_premium_on_death"`: true / false
- `"commutation_allowed"`: true / false
- `"fund_switching_allowed"`: true / false
- `"income_frequency"`: ["Monthly", "Quarterly", "Half-Yearly", "Yearly"]
- `"payout_options"`: ["Lump Sum", "Installments", "Combination"]
- `"life_assured_type"`: ["Child", "Parent", "Individual", "Joint"]
- `"tax_benefits"`: ["Section 80C", "Section 10(10D)"]
- `"riders_available"`: ["Critical Illness", "Accidental Death", "Waiver of Premium", "Surgical Care", "Hospital Cash"]

---

### 🔁 VALUE NORMALIZATION EXAMPLES
| Brochure Text                                | Normalized JSON                              |
|---------------------------------------------|----------------------------------------------|
| "Entry age: 0 to 55 years"                   | "min_entry_age": 0, "max_entry_age": 55      |
| "Paid every 3 years: 15%"                    | "survival_benefit_schedule": [{"year": 3, "payout": "15%"}] |
| "Waiver of Premium on parent's death"        | "waiver_of_premium_on_death": true           |
| "Guaranteed maturity benefit of ₹2 Lakhs"    | "maturity_benefit": "₹2 Lakhs guaranteed"    |
| "Income: ₹5,000 per month for 15 years"      | "income_frequency": "Monthly", "guaranteed_income": true |

---

### 🔍 FOCUS AREAS FOR INSURANCE PLANS:
You must accurately extract and prioritize the following fields:
- returns_type, maturity_benefit, guaranteed_income, death_benefit, premium_modes

---

### 🏗️ OUTPUT FORMAT (JSON SCHEMA):
{
  "policy_name": "",
  "insurer": "",
  "plan_category": "",
  "plan_type": "",
  "uin_code": "",
  "is_open_for_sale": true,
  "objectives": [],
  "target_audience": [],
  "investment_style": [],
  "min_entry_age": null,
  "max_entry_age": null,
  "min_maturity_age": null,
  "max_maturity_age": null,
  "min_policy_term": null,
  "max_policy_term": null,
  "premium_payment_term": [],
  "premium_modes": [],
  "min_annual_premium": null,
  "max_annual_premium": null,
  "min_sum_assured": null,
  "max_sum_assured": null,
  "grace_period": "",
  "revival_period": "",
  "risk_profile": "",
  "returns_type": "",
  "fund_options": [],
  "bonus_type": "",
  "guaranteed_income": false,
  "maturity_benefit": "",
  "death_benefit": "",
  "surrender_value": "",
  "loan_available": false,
  "partial_withdrawal": false,
  "riders_available": [],
  "waiver_of_premium_on_death": false,
  "payout_options": [],
  "income_frequency": "",
  "survival_benefit_schedule": [
    {
      "year": null,
      "payout": ""
    }
  ],
  "tax_benefits": [],
  "vesting_age": null,
  "annuity_options": [],
  "commutation_allowed": null,
  "life_assured_type": "",
  "fund_switching_allowed": null,
  "policy_admin_charges": "",
  "mortality_charges": "",
  "fund_management_charges": "",
  "brochure_url": "",
  "notes": "",
  "last_updated": "{{ PROCESSING_DATETIME }}"
}

IMPORTANT: Return ONLY the JSON object above with extracted values. No markdown, no code blocks, no explanations."""
        
        self.prompt_text.insert("1.0", default_prompt)
        
        # Initialize prompt source display
        self.on_prompt_source_change()
        
        # Control buttons
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill="x", padx=5, pady=5)
        
        self.process_btn = ttk.Button(control_frame, text="Process Policy", 
                                     command=self.process_policy)
        self.process_btn.pack(side="left")
        
        self.clear_btn = ttk.Button(control_frame, text="Clear All", 
                                   command=self.clear_all)
        self.clear_btn.pack(side="left", padx=(10, 0))
        
        # Progress section
        progress_frame = ttk.Frame(control_frame)
        progress_frame.pack(side="right", fill="x", expand=True, padx=(20, 0))
        
        # Progress bar
        self.progress_bar = ttk.Progressbar(progress_frame, mode='determinate', length=200)
        self.progress_bar.pack(side="top", fill="x")
        
        # Progress label
        self.progress_label = ttk.Label(progress_frame, text="Ready")
        self.progress_label.pack(side="bottom")
        
        # Progress value for determinate mode
        self.progress_value = 0
        
        # Bind input type change (with compatibility check)
        try:
            # Try new method first (Python 3.6+)
            self.input_type_var.trace_add('write', self.on_input_type_change)
        except AttributeError:
            # Fallback to old method for older Python versions
            self.input_type_var.trace('w', self.on_input_type_change)
        
        self.on_input_type_change()
        
    def setup_config_tab(self):
        """Setup the configuration tab"""
        config_frame = ttk.Frame(self.notebook)
        self.notebook.add(config_frame, text="Configuration")
        
        # API Configuration
        api_frame = ttk.LabelFrame(config_frame, text="OpenAI API Configuration", padding="10")
        api_frame.pack(fill="x", padx=5, pady=5)
        
        # API Key
        ttk.Label(api_frame, text="API Key:").pack(anchor="w")
        key_frame = ttk.Frame(api_frame)
        key_frame.pack(fill="x", pady=5)
        
        self.api_key_entry = ttk.Entry(key_frame, textvariable=self.api_key_var, show="*")
        self.api_key_entry.pack(side="left", fill="x", expand=True)
        
        ttk.Button(key_frame, text="Show/Hide", 
                  command=self.toggle_api_key_visibility).pack(side="right", padx=(5, 0))
        
        # API Key buttons
        key_btn_frame = ttk.Frame(api_frame)
        key_btn_frame.pack(fill="x", pady=5)
        
        self.test_btn = ttk.Button(key_btn_frame, text="Test API Key", 
                                  command=self.test_api_key)
        self.test_btn.pack(side="left")
        
        self.save_btn = ttk.Button(key_btn_frame, text="Save Configuration", 
                                  command=self.save_config)
        self.save_btn.pack(side="left", padx=(10, 0))
        
        # Model Selection
        ttk.Label(api_frame, text="Model:").pack(anchor="w", pady=(20, 0))
        self.model_combo = ttk.Combobox(api_frame, textvariable=self.model_var, 
                                       values=self.models, state="readonly")
        self.model_combo.pack(fill="x", pady=5)
        
        # Status
        self.status_frame = ttk.LabelFrame(config_frame, text="Status", padding="10")
        self.status_frame.pack(fill="x", padx=5, pady=5)
        
        self.status_label = ttk.Label(self.status_frame, text="API Status: Not tested")
        self.status_label.pack(anchor="w")
        
    def setup_output_tab(self):
        """Setup the output tab"""
        output_frame = ttk.Frame(self.notebook)
        self.notebook.add(output_frame, text="Output")
        
        # Output controls
        output_control_frame = ttk.Frame(output_frame)
        output_control_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Button(output_control_frame, text="Save JSON", 
                  command=self.save_output).pack(side="left")
        ttk.Button(output_control_frame, text="Copy to Clipboard", 
                  command=self.copy_to_clipboard).pack(side="left", padx=(10, 0))
        ttk.Button(output_control_frame, text="Validate JSON", 
                  command=self.validate_json).pack(side="left", padx=(10, 0))
        ttk.Button(output_control_frame, text="Format JSON", 
                  command=self.format_json).pack(side="left", padx=(10, 0))
        ttk.Button(output_control_frame, text="Clear Output", 
                  command=self.clear_output).pack(side="left", padx=(10, 0))
        
        # JSON validation status
        self.json_status_label = ttk.Label(output_control_frame, text="", foreground="green")
        self.json_status_label.pack(side="right")
        
        # Output text area
        self.output_text = scrolledtext.ScrolledText(output_frame, wrap="word")
        self.output_text.pack(fill="both", expand=True, padx=5, pady=(0, 5))
        
    def on_input_type_change(self, *args):
        """Handle input type change"""
        try:
            if self.input_type_var.get() == "file":
                self.file_frame.pack(fill="x", pady=5)
                self.text_frame.pack_forget()
            else:
                self.text_frame.pack(fill="both", expand=True, pady=5)
                self.file_frame.pack_forget()
        except Exception as e:
            self.logger.error(f"Error changing input type: {e}")

    def on_prompt_source_change(self):
        """Handle prompt source change"""
        try:
            if self.prompt_source_var.get() == "file":
                self.prompt_file_frame.pack(fill="x", pady=5)
                self.prompt_text_frame.pack_forget()
            else:
                self.prompt_text_frame.pack(fill="both", expand=True, pady=5)
                self.prompt_file_frame.pack_forget()
        except Exception as e:
            self.logger.error(f"Error changing prompt source: {e}")
            
    def view_edit_prompt_file(self):
        """View and edit the selected prompt file"""
        prompt_file_path = self.prompt_file_path_var.get().strip()
        
        if not prompt_file_path:
            messagebox.showwarning("Warning", "Please select a prompt file first")
            return
            
        try:
            # Read the file content
            file_content = self.read_file_content(prompt_file_path)
            
            # Create a new window for editing
            edit_window = tk.Toplevel(self.root)
            edit_window.title(f"Edit Prompt File - {os.path.basename(prompt_file_path)}")
            edit_window.geometry("800x600")
            edit_window.minsize(600, 400)
            
            # Create the text editor
            text_frame = ttk.Frame(edit_window)
            text_frame.pack(fill="both", expand=True, padx=10, pady=10)
            
            ttk.Label(text_frame, text=f"Editing: {prompt_file_path}").pack(anchor="w", pady=(0, 5))
            
            # Text editor with scrollbar
            text_editor = scrolledtext.ScrolledText(text_frame, wrap="word", font=("Consolas", 10))
            text_editor.pack(fill="both", expand=True)
            text_editor.insert("1.0", file_content)
            
            # Button frame
            button_frame = ttk.Frame(edit_window)
            button_frame.pack(fill="x", padx=10, pady=(0, 10))
            
            def save_file():
                """Save the edited content back to file"""
                try:
                    new_content = text_editor.get("1.0", "end-1c")
                    with open(prompt_file_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    messagebox.showinfo("Success", "File saved successfully!")
                    edit_window.destroy()
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to save file: {str(e)}")
            
            def save_as_file():
                """Save the edited content to a new file"""
                try:
                    new_content = text_editor.get("1.0", "end-1c")
                    filename = filedialog.asksaveasfilename(
                        defaultextension=".txt",
                        filetypes=[("Text Files", "*.txt"), ("Markdown Files", "*.md"), ("All Files", "*.*")],
                        title="Save Prompt As"
                    )
                    if filename:
                        with open(filename, 'w', encoding='utf-8') as f:
                            f.write(new_content)
                        # Update the prompt file path to the new file
                        self.prompt_file_path_var.set(filename)
                        messagebox.showinfo("Success", f"File saved as {filename}")
                        edit_window.destroy()
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to save file: {str(e)}")
            
            def load_to_text_editor():
                """Load the content to the main text editor and switch to text mode"""
                content = text_editor.get("1.0", "end-1c")
                self.prompt_text.delete("1.0", "end")
                self.prompt_text.insert("1.0", content)
                self.prompt_source_var.set("text")
                self.on_prompt_source_change()
                messagebox.showinfo("Success", "Content loaded to text editor!")
                edit_window.destroy()
            
            ttk.Button(button_frame, text="Save", command=save_file).pack(side="left")
            ttk.Button(button_frame, text="Save As...", command=save_as_file).pack(side="left", padx=(10, 0))
            ttk.Button(button_frame, text="Load to Text Editor", command=load_to_text_editor).pack(side="left", padx=(10, 0))
            ttk.Button(button_frame, text="Cancel", command=edit_window.destroy).pack(side="right")
            
            # Focus on the text editor
            text_editor.focus_set()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open file: {str(e)}")
            
    def browse_prompt_file(self):
        """Browse and select a prompt file"""
        filetypes = [
            ("Text Files", "*.txt *.md"),
            ("Text Files", "*.txt"),
            ("Markdown Files", "*.md"),
            ("All Files", "*.*")
        ]
        
        filename = filedialog.askopenfilename(
            title="Select Prompt File",
            filetypes=filetypes
        )
        
        if filename:
            self.prompt_file_path_var.set(filename)
            
    def update_progress(self, value, message="Processing..."):
        """Update progress bar and message"""
        self.progress_value = value
        self.progress_bar['value'] = value
        self.progress_label.config(text=message)
        self.root.update_idletasks()
        
    def reset_progress(self):
        """Reset progress bar"""
        self.progress_bar['value'] = 0
        self.progress_label.config(text="Ready")
        self.root.update_idletasks()
            
    def browse_file(self):
        """Browse and select a file"""
        filetypes = [
            ("All Supported", "*.pdf *.txt *.md"),
            ("PDF Files", "*.pdf"),
            ("Text Files", "*.txt"),
            ("Markdown Files", "*.md"),
            ("All Files", "*.*")
        ]
        
        filename = filedialog.askopenfilename(
            title="Select Policy File",
            filetypes=filetypes
        )
        
        if filename:
            self.file_path_var.set(filename)
            
    def toggle_api_key_visibility(self):
        """Toggle API key visibility"""
        current_show = self.api_key_entry.cget("show")
        if current_show == "*":
            self.api_key_entry.config(show="")
        else:
            self.api_key_entry.config(show="*")
            
    def load_config(self):
        """Load configuration from file"""
        try:
            if self.config_file.exists():
                self.config.read(self.config_file)
                if 'openai' in self.config:
                    api_key = self.config.get('openai', 'api_key', fallback='')
                    model = self.config.get('openai', 'model', fallback=self.models[0])
                    
                    self.api_key_var.set(api_key)
                    self.model_var.set(model)
                    
                    if api_key:
                        self.openai_client = OpenAI(api_key=api_key)
                        
        except Exception as e:
            self.logger.error(f"Error loading config: {e}")
            
    def save_config(self):
        """Save configuration to file"""
        try:
            self.config['openai'] = {
                'api_key': self.api_key_var.get(),
                'model': self.model_var.get()
            }
            
            with open(self.config_file, 'w') as f:
                self.config.write(f)
                
            messagebox.showinfo("Success", "Configuration saved successfully!")
            
        except Exception as e:
            self.logger.error(f"Error saving config: {e}")
            messagebox.showerror("Error", f"Failed to save configuration: {str(e)}")
            
    def test_api_key(self):
        """Test the OpenAI API key"""
        api_key = self.api_key_var.get().strip()
        
        if not api_key:
            messagebox.showerror("Error", "Please enter an API key")
            return
            
        def test_key():
            try:
                self.progress_bar.start(10)
                self.test_btn.config(state="disabled")
                
                client = OpenAI(api_key=api_key)
                
                # Test with a simple request
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": "Hello"}],
                    max_tokens=5
                )
                
                self.openai_client = client
                self.root.after(0, lambda: self.status_label.config(text="API Status: ✅ Valid"))
                self.root.after(0, lambda: messagebox.showinfo("Success", "API key is valid!"))
                
            except Exception as e:
                error_msg = str(e)
                if "invalid" in error_msg.lower() or "authentication" in error_msg.lower():
                    status_text = "API Status: ❌ Invalid API Key"
                else:
                    status_text = f"API Status: ❌ Error: {error_msg[:50]}..."
                    
                self.root.after(0, lambda: self.status_label.config(text=status_text))
                self.root.after(0, lambda: messagebox.showerror("Error", f"API key test failed: {error_msg}"))
                
            finally:
                self.root.after(0, lambda: self.progress_bar.stop())
                self.root.after(0, lambda: self.test_btn.config(state="normal"))
                
        thread = threading.Thread(target=test_key, daemon=True)
        thread.start()
        
    def read_file_content(self, file_path: str) -> str:
        """Read content from various file formats"""
        file_path = Path(file_path)
        
        try:
            if file_path.suffix.lower() == '.pdf':
                return self.read_pdf(file_path)
            elif file_path.suffix.lower() == '.md':
                return self.read_markdown(file_path)
            else:  # .txt or other text files
                return self.read_text(file_path)
                
        except Exception as e:
            raise Exception(f"Error reading file {file_path}: {str(e)}")
            
    def read_pdf(self, file_path: Path) -> str:
        """Read PDF file content"""
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            content = ""
            
            for page in pdf_reader.pages:
                content += page.extract_text() + "\n"
                
            return content.strip()
            
    def read_markdown(self, file_path: Path) -> str:
        """Read Markdown file content"""
        with open(file_path, 'r', encoding='utf-8') as file:
            md_content = file.read()
            # Convert to HTML then strip tags for plain text
            html = markdown.markdown(md_content)
            # Simple HTML tag removal
            clean_text = re.sub('<[^<]+?>', '', html)
            return clean_text.strip()
            
    def read_text(self, file_path: Path) -> str:
        """Read text file content"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read().strip()
        except UnicodeDecodeError:
            # Try with different encoding
            with open(file_path, 'r', encoding='latin-1') as file:
                return file.read().strip()
                
    def extract_json_from_response(self, response_text: str) -> str:
        """Extract clean JSON from AI response, handling markdown and other formatting"""
        try:
            # First, try to parse the response directly as JSON
            json.loads(response_text)
            return response_text
        except json.JSONDecodeError:
            pass
        
        # Remove markdown code blocks
        cleaned = re.sub(r'```json\s*\n?', '', response_text)
        cleaned = re.sub(r'```\s*\n?', '', cleaned)
        
        # Try to find JSON object in the text
        json_pattern = r'\{.*\}'
        matches = re.findall(json_pattern, cleaned, re.DOTALL)
        
        for match in matches:
            try:
                # Validate that it's proper JSON
                json.loads(match)
                return match
            except json.JSONDecodeError:
                continue
        
        # If no valid JSON found, try to extract from nested structure
        try:
            parsed = json.loads(response_text)
            if isinstance(parsed, dict):
                # Check for common nested patterns
                if 'analysis' in parsed and isinstance(parsed['analysis'], str):
                    return self.extract_json_from_response(parsed['analysis'])
                elif 'content' in parsed and isinstance(parsed['content'], str):
                    return self.extract_json_from_response(parsed['content'])
                elif 'response' in parsed and isinstance(parsed['response'], str):
                    return self.extract_json_from_response(parsed['response'])
        except json.JSONDecodeError:
            pass
        
        # Last resort: return the cleaned text
        return cleaned.strip()
                
    def process_policy(self):
        """Process the policy document"""
        # Validation
        if not self.openai_client:
            messagebox.showerror("Error", "Please configure and test your OpenAI API key first")
            return
            
        # Get content
        try:
            if self.input_type_var.get() == "file":
                file_path = self.file_path_var.get().strip()
                if not file_path:
                    messagebox.showerror("Error", "Please select a file")
                    return
                content = self.read_file_content(file_path)
            else:
                content = self.text_input.get("1.0", "end-1c").strip()
                if not content:
                    messagebox.showerror("Error", "Please enter policy text")
                    return
                    
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read content: {str(e)}")
            return
            
        # Get prompt
        try:
            if self.prompt_source_var.get() == "file":
                prompt_file_path = self.prompt_file_path_var.get().strip()
                if not prompt_file_path:
                    messagebox.showerror("Error", "Please select a prompt file")
                    return
                custom_prompt = self.read_file_content(prompt_file_path)
            else:
                custom_prompt = self.prompt_text.get("1.0", "end-1c").strip()
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read prompt: {str(e)}")
            return
            
        # Process in background thread
        def process():
            try:
                # Update progress
                self.root.after(0, lambda: self.update_progress(10, "Initializing..."))
                self.root.after(0, lambda: self.process_btn.config(state="disabled"))
                
                # Update progress
                self.root.after(0, lambda: self.update_progress(25, "Preparing request..."))
                
                # Construct prompt with dynamic timestamp
                current_time = datetime.now().isoformat() + 'Z'
                full_prompt = custom_prompt.replace("{{ PROCESSING_DATETIME }}", current_time)
                full_prompt = f"{full_prompt}\n\nPolicy Document:\n{content}"
                
                # Update progress
                self.root.after(0, lambda: self.update_progress(40, "Sending to OpenAI..."))
                
                # Make API call
                response = self.openai_client.chat.completions.create(
                    model=self.model_var.get(),
                    messages=[
                        {"role": "system", "content": "You are a policy analysis expert. Always respond with valid JSON only. Do not include markdown formatting or code blocks."},
                        {"role": "user", "content": full_prompt}
                    ],
                    temperature=0.1,
                    max_tokens=4000
                )
                
                # Update progress
                self.root.after(0, lambda: self.update_progress(70, "Processing response..."))
                
                result = response.choices[0].message.content.strip()
                
                # Extract clean JSON
                clean_json = self.extract_json_from_response(result)
                
                # Update progress
                self.root.after(0, lambda: self.update_progress(90, "Formatting output..."))
                
                # Validate and format JSON
                try:
                    parsed_json = json.loads(clean_json)
                    # Update the last_updated field with current processing time
                    if isinstance(parsed_json, dict):
                        current_time = datetime.now().isoformat() + 'Z'
                        parsed_json['last_updated'] = current_time
                    
                    formatted_result = json.dumps(parsed_json, indent=2, ensure_ascii=False)
                except json.JSONDecodeError as e:
                    # If JSON is still invalid, show original response with error info
                    current_time = datetime.now().isoformat() + 'Z'
                    formatted_result = json.dumps({
                        "error": "Failed to parse JSON response",
                        "json_error": str(e),
                        "raw_response": clean_json,
                        "original_response": result,
                        "processing_time": current_time
                    }, indent=2)
                
                # Update progress
                self.root.after(0, lambda: self.update_progress(100, "Complete!"))
                
                # Update UI
                self.root.after(0, lambda: self.update_output(formatted_result))
                self.root.after(0, lambda: self.notebook.select(2))  # Switch to output tab
                
                # Reset progress after a delay
                self.root.after(2000, self.reset_progress)
                
            except Exception as e:
                error_msg = f"Processing failed: {str(e)}"
                self.root.after(0, lambda: messagebox.showerror("Error", error_msg))
                self.root.after(0, self.reset_progress)
                
            finally:
                self.root.after(0, lambda: self.process_btn.config(state="normal"))
                
        thread = threading.Thread(target=process, daemon=True)
        thread.start()
        
    def update_output(self, content: str):
        """Update the output text area"""
        self.output_text.delete("1.0", "end")
        self.output_text.insert("1.0", content)
        
        # Auto-validate JSON
        self.validate_json_silent()
        
    def validate_json(self):
        """Validate JSON in output and show result"""
        content = self.output_text.get("1.0", "end-1c").strip()
        
        if not content:
            messagebox.showwarning("Warning", "No content to validate")
            return
            
        try:
            json.loads(content)
            self.json_status_label.config(text="✅ Valid JSON", foreground="green")
            messagebox.showinfo("Validation", "JSON is valid!")
        except json.JSONDecodeError as e:
            self.json_status_label.config(text="❌ Invalid JSON", foreground="red")
            messagebox.showerror("Validation Error", f"Invalid JSON: {str(e)}")
            
    def validate_json_silent(self):
        """Silently validate JSON and update status"""
        content = self.output_text.get("1.0", "end-1c").strip()
        
        if not content:
            self.json_status_label.config(text="", foreground="black")
            return
            
        try:
            json.loads(content)
            self.json_status_label.config(text="✅ Valid JSON", foreground="green")
        except json.JSONDecodeError:
            self.json_status_label.config(text="❌ Invalid JSON", foreground="red")
            
    def format_json(self):
        """Format JSON in output area"""
        content = self.output_text.get("1.0", "end-1c").strip()
        
        if not content:
            messagebox.showwarning("Warning", "No content to format")
            return
            
        try:
            parsed = json.loads(content)
            formatted = json.dumps(parsed, indent=2, ensure_ascii=False)
            self.output_text.delete("1.0", "end")
            self.output_text.insert("1.0", formatted)
            self.json_status_label.config(text="✅ Valid JSON", foreground="green")
        except json.JSONDecodeError as e:
            messagebox.showerror("Format Error", f"Cannot format invalid JSON: {str(e)}")
            
    def save_output(self):
        """Save output to file"""
        content = self.output_text.get("1.0", "end-1c").strip()
        
        if not content:
            messagebox.showwarning("Warning", "No output to save")
            return
            
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("Text files", "*.txt"), ("All files", "*.*")],
            title="Save Output"
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(content)
                messagebox.showinfo("Success", f"Output saved to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file: {str(e)}")
                
    def copy_to_clipboard(self):
        """Copy output to clipboard"""
        content = self.output_text.get("1.0", "end-1c").strip()
        
        if not content:
            messagebox.showwarning("Warning", "No output to copy")
            return
            
        self.root.clipboard_clear()
        self.root.clipboard_append(content)
        messagebox.showinfo("Success", "Output copied to clipboard")
        
    def clear_output(self):
        """Clear output text area"""
        self.output_text.delete("1.0", "end")
        self.json_status_label.config(text="", foreground="black")
        
    def clear_all(self):
        """Clear all inputs"""
        self.file_path_var.set("")
        self.prompt_file_path_var.set("")
        self.text_input.delete("1.0", "end")
        self.clear_output()
        self.reset_progress()
        
    def run(self):
        """Start the application"""
        self.root.mainloop()

def main():
    """Main entry point"""
    try:
        app = PolicyProcessorGUI()
        app.run()
    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
    except Exception as e:
        print(f"Application error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()