import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
from tkinterdnd2 import TkinterDnD, DND_FILES
import re

# Hi Romča, I love you :)

def analyze_language(text):
    """
    Checks if there are ANY letters (A-Z) before the first ';;;;;;' delimiter.
    Returns: (is_english, reason)
    """
    if '=' not in text:
        return False, "No value found"
    
    value = text.split('=', 1)[1]
    
    # Split by multi-language delimiter and get ONLY the first segment
    segments = value.split(';;;;;;')
    first_segment = segments[0].strip() if segments else value
    
    # Check if there are ANY alphabetic letters (a-z or A-Z) in the first segment
    has_letters = bool(re.search(r'[a-zA-Z]', first_segment))
    
    if has_letters:
        return True, "Contains letters in English segment"
    else:
        if len(first_segment) == 0:
            return False, "Empty English segment"
        else:
            return False, "No letters in English segment"

def get_keys(file_path):
    encodings = ['utf-16', 'utf-8-sig', 'utf-8', 'cp1252']
    found_keys = {}
    
    for enc in encodings:
        try:
            with open(file_path, 'rb') as f:
                content = f.read().decode(enc)
                for line_num, line in enumerate(content.splitlines(), 1):
                    # Skip empty lines or comments
                    if not line.strip() or line.strip().startswith('#') or line.strip().startswith(';'):
                        continue
                        
                    if '=' in line:
                        key = line.split('=')[0].strip()
                        if key:
                            found_keys[key] = {"text": line.strip(), "line": line_num}
                return found_keys
        except:
            continue
    return {}

# ============================================
# TAB 1: FILE COMPARATOR
# ============================================
class CompareTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        
        tk.Label(self, text="Compare Two Files", font=("Arial", 14, "bold")).pack(pady=10)
        tk.Label(self, text="Find new keys in File B that don't exist in File A", 
                 font=("Arial", 9), fg="gray").pack(pady=5)

        # --- File A Section ---
        tk.Label(self, text="File A (Reference):", font=("Arial", 10, "bold")).pack(anchor="w", padx=20)
        frame_a = tk.Frame(self)
        frame_a.pack(fill="x", padx=20, pady=5)
        self.entry_a = tk.Entry(frame_a, font=("Consolas", 9))
        self.entry_a.pack(side="left", fill="x", expand=True, padx=(0, 5))
        tk.Button(frame_a, text="Browse", command=lambda: self.browse(self.entry_a)).pack(side="right")
        
        # Enable Drag & Drop for Entry A
        self.entry_a.drop_target_register(DND_FILES)
        self.entry_a.dnd_bind('<<Drop>>', lambda e: self.on_drop(e, self.entry_a))
        self.entry_a.dnd_bind('<<DragEnter>>', lambda e: self.on_drag_enter(e, self.entry_a))
        self.entry_a.dnd_bind('<<DragLeave>>', lambda e: self.on_drag_leave(e, self.entry_a))

        # --- File B Section ---
        tk.Label(self, text="File B (New File):", font=("Arial", 10, "bold")).pack(anchor="w", padx=20, pady=(10, 0))
        frame_b = tk.Frame(self)
        frame_b.pack(fill="x", padx=20, pady=5)
        self.entry_b = tk.Entry(frame_b, font=("Consolas", 9))
        self.entry_b.pack(side="left", fill="x", expand=True, padx=(0, 5))
        tk.Button(frame_b, text="Browse", command=lambda: self.browse(self.entry_b)).pack(side="right")
        
        # Enable Drag & Drop for Entry B
        self.entry_b.drop_target_register(DND_FILES)
        self.entry_b.dnd_bind('<<Drop>>', lambda e: self.on_drop(e, self.entry_b))
        self.entry_b.dnd_bind('<<DragEnter>>', lambda e: self.on_drag_enter(e, self.entry_b))
        self.entry_b.dnd_bind('<<DragLeave>>', lambda e: self.on_drag_leave(e, self.entry_b))

        # --- Compare Button ---
        self.compare_btn = tk.Button(self, text="COMPARE FILES", command=self.compare, 
                                     bg="#2e7d32", fg="white", font=("Arial", 11, "bold"), pady=10)
        self.compare_btn.pack(pady=20, fill="x", padx=100)

        # --- Results Area ---
        tk.Label(self, text="Differences Found in File B:", font=("Arial", 10)).pack(anchor="w", padx=20)
        self.result_area = scrolledtext.ScrolledText(self, width=80, height=15, font=("Consolas", 10))
        self.result_area.pack(pady=5, padx=20, fill="both", expand=True)

    def browse(self, entry_widget):
        filename = filedialog.askopenfilename()
        if filename:
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, filename)

    def on_drop(self, event, entry_widget):
        """Handle file drop event"""
        path = event.data
        if path.startswith('{') and path.endswith('}'):
            path = path[1:-1]
        entry_widget.delete(0, tk.END)
        entry_widget.insert(0, path)
        entry_widget.config(bg="white")

    def on_drag_enter(self, event, entry_widget):
        """Visual feedback when dragging over the entry"""
        entry_widget.config(bg="#e3f2fd")

    def on_drag_leave(self, event, entry_widget):
        """Reset background when drag leaves the entry"""
        entry_widget.config(bg="white")

    def compare(self):
        path_a = self.entry_a.get()
        path_b = self.entry_b.get()

        if not path_a or not path_b:
            messagebox.showwarning("Input Error", "Please select both files before comparing.")
            return

        dict_a = get_keys(path_a)
        dict_b = get_keys(path_b)
        new_keys = [k for k in dict_b if k not in dict_a]

        self.result_area.delete(1.0, tk.END)
        
        # --- Language Analysis ---
        no_english_keys = []
        english_keys = []
        
        for k in new_keys:
            is_eng, reason = analyze_language(dict_b[k]["text"])
            if is_eng:
                english_keys.append(k)
            else:
                no_english_keys.append((k, reason))
        
        no_english_count = len(no_english_keys)
        has_english_count = len(english_keys)
        lang_status = f"{has_english_count} English, {no_english_count} Non-English"

        # --- Header Output ---
        header = f"SUMMARY:\n"
        header += f"  - File A unique IDs: {len(dict_a)}\n"
        header += f"  - File B unique IDs: {len(dict_b)}\n"
        header += f"  - New entries found: {len(new_keys)}\n"
        header += f"  - Language Check:  {lang_status}\n"
            
        header += "=" * 70 + "\n\n"
        self.result_area.insert(tk.END, header)

        if not new_keys:
            self.result_area.insert(tk.END, ">>> No differences found. File B contains no new keys.")
        else:
            for i, k in enumerate(new_keys, 1):
                line_info = dict_b[k]
                is_eng, reason = analyze_language(line_info['text'])
                
                entry_text = f"Entry #{i}\n"
                entry_text += f"Line {line_info['line']}\n"
                
                # No warning banner shown anymore
                if is_eng:
                    entry_text += f"[OK] English detected\n"
                else:
                    entry_text += f"[!] No English letters before delimiter\n"
                
                entry_text += f"\n{line_info['text']}\n"
                entry_text += "-" * 50 + "\n\n"
                
                self.result_area.insert(tk.END, entry_text)
            
            self.result_area.yview_moveto(0)

# ============================================
# TAB 2: LANGUAGE SCANNER
# ============================================
class ScanTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        
        tk.Label(self, text="Scan File for Non-English Entries", font=("Arial", 14, "bold")).pack(pady=10)
        tk.Label(self, text="Check a single file for entries without English words", 
                 font=("Arial", 9), fg="gray").pack(pady=5)

        # --- File Section ---
        tk.Label(self, text="File to Scan:", font=("Arial", 10, "bold")).pack(anchor="w", padx=20)
        frame_file = tk.Frame(self)
        frame_file.pack(fill="x", padx=20, pady=5)
        self.entry_file = tk.Entry(frame_file, font=("Consolas", 9))
        self.entry_file.pack(side="left", fill="x", expand=True, padx=(0, 5))
        tk.Button(frame_file, text="Browse", command=self.browse).pack(side="right")
        
        # Enable Drag & Drop for Entry
        self.entry_file.drop_target_register(DND_FILES)
        self.entry_file.dnd_bind('<<Drop>>', lambda e: self.on_drop(e))
        self.entry_file.dnd_bind('<<DragEnter>>', lambda e: self.on_drag_enter(e))
        self.entry_file.dnd_bind('<<DragLeave>>', lambda e: self.on_drag_leave(e))

        # --- Scan Button ---
        self.scan_btn = tk.Button(self, text="SCAN FILE", command=self.scan, 
                                  bg="#1565c0", fg="white", font=("Arial", 11, "bold"), pady=10)
        self.scan_btn.pack(pady=20, fill="x", padx=100)

        # --- Filter Options ---
        filter_frame = tk.Frame(self)
        filter_frame.pack(padx=20, pady=5)
        
        self.filter_var = tk.BooleanVar(value=True)
        tk.Checkbutton(filter_frame, text="Show only entries WITHOUT English words", 
                       variable=self.filter_var, font=("Arial", 9)).pack(side="left")

        # --- Results Area ---
        tk.Label(self, text="Scan Results:", font=("Arial", 10)).pack(anchor="w", padx=20)
        self.result_area = scrolledtext.ScrolledText(self, width=80, height=15, font=("Consolas", 10))
        self.result_area.pack(pady=5, padx=20, fill="both", expand=True)

    def browse(self):
        filename = filedialog.askopenfilename()
        if filename:
            self.entry_file.delete(0, tk.END)
            self.entry_file.insert(0, filename)

    def on_drop(self, event):
        """Handle file drop event"""
        path = event.data
        if path.startswith('{') and path.endswith('}'):
            path = path[1:-1]
        self.entry_file.delete(0, tk.END)
        self.entry_file.insert(0, path)
        self.entry_file.config(bg="white")

    def on_drag_enter(self, event):
        """Visual feedback when dragging over the entry"""
        self.entry_file.config(bg="#e3f2fd")

    def on_drag_leave(self, event):
        """Reset background when drag leaves the entry"""
        self.entry_file.config(bg="white")

    def scan(self):
        path = self.entry_file.get()

        if not path:
            messagebox.showwarning("Input Error", "Please select a file to scan.")
            return

        dict_file = get_keys(path)

        self.result_area.delete(1.0, tk.END)
        
        # --- Analyze All Keys ---
        english_keys = []
        no_english_keys = []
        
        for k, info in dict_file.items():
            is_eng, reason = analyze_language(info["text"])
            if is_eng:
                english_keys.append((k, info, reason))
            else:
                no_english_keys.append((k, info, reason))
        
        total_count = len(dict_file)
        no_english_count = len(no_english_keys)
        has_english_count = len(english_keys)

        # --- Header Output ---
        header = f"SCAN SUMMARY:\n"
        header += f"  - File: {path}\n"
        header += f"  - Total entries: {total_count}\n"
        header += f"  - With English letters: {has_english_count}\n"
        header += f"  - WITHOUT English letters: {no_english_count}\n"
            
        header += "=" * 70 + "\n\n"
        self.result_area.insert(tk.END, header)

        # --- Display Results ---
        keys_to_show = no_english_keys if self.filter_var.get() else english_keys + no_english_keys
        
        if not keys_to_show:
            self.result_area.insert(tk.END, ">>> No entries match the current filter.")
        else:
            for i, (k, info, reason) in enumerate(keys_to_show, 1):
                is_eng = k in [x[0] for x in english_keys]
                
                entry_text = f"Entry #{i}\n"
                entry_text += f"Key: {k}\n"
                entry_text += f"Line {info['line']}\n"
                
                # No warning banner shown anymore
                if is_eng:
                    entry_text += f"[OK] English detected\n"
                else:
                    entry_text += f"[!] No English letters before delimiter\n"
                
                entry_text += f"\n{info['text']}\n"
                entry_text += "-" * 50 + "\n\n"
                
                self.result_area.insert(tk.END, entry_text)
            
            self.result_area.yview_moveto(0)

# ============================================
# MAIN APP WITH TABS
# ============================================
class ComparisonApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ini key comparator")
        self.root.geometry("800x650")

        tk.Label(root, text="ini comparator for my sweetie :3", font=("Arial", 14, "bold")).pack(pady=10)

        # --- Create Notebook (Tabs) ---
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # --- Tab 1: Compare ---
        self.compare_tab = CompareTab(self.notebook)
        self.notebook.add(self.compare_tab, text="📊 Compare Files")

        # --- Tab 2: Scan ---
        self.scan_tab = ScanTab(self.notebook)
        self.notebook.add(self.scan_tab, text="🔍 Scan Language")

        # Style the tabs
        style = ttk.Style()
        style.configure('TNotebook.Tab', font=('Arial', 10, 'bold'), padding=[20, 5])

if __name__ == "__main__":
    # Initialize with TkinterDnD.Tk() instead of tk.Tk() to enable DnD
    root = TkinterDnD.Tk()
    app = ComparisonApp(root)
    root.mainloop()