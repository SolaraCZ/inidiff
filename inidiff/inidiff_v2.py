import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os


def get_keys(file_path):
    """Parses an INI file and returns a dictionary of keys."""
    encodings = ['utf-16', 'utf-8-sig', 'utf-8', 'cp1250', 'cp1252']
    found_keys = {}
    
    if not os.path.exists(file_path):
        return None

    for enc in encodings:
        try:
            with open(file_path, 'rb') as f:
                content = f.read().decode(enc)
                for line_num, line in enumerate(content.splitlines(), 1):
                    line = line.strip()
                    if not line or line.startswith(';') or line.startswith('#') or line.startswith('['):
                        continue
                    
                    if '=' in line:
                        parts = line.split('=', 1)
                        raw_key = parts[0].strip()
                        value = parts[1].strip() if len(parts) > 1 else ""
                        
                        if raw_key:
                            key_id = raw_key.lower()
                            found_keys[key_id] = {
                                "text": line.strip(), 
                                "value": value,
                                "line": line_num,
                                "display_key": raw_key
                            }
                return found_keys
        except Exception:
            continue
    return {}

# --- TAB 1: SINGLE FILE COMPARISON ---

class SingleFileTab(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        
        self.configure(bg="#f0f0f0")
        
        # Input Frame
        input_frame = tk.Frame(self, bg="#f0f0f0", pady=10)
        input_frame.pack(fill="x", padx=20)

        tk.Label(input_frame, text="File A (Reference):", font=("Arial", 10, "bold"), bg="#f0f0f0").grid(row=0, column=0, sticky="w")
        self.entry_a = tk.Entry(input_frame, width=60, font=("Arial", 10))
        self.entry_a.grid(row=1, column=0, padx=5, pady=2)
        tk.Button(input_frame, text="Browse", command=lambda: self.browse(self.entry_a)).grid(row=1, column=1)

        tk.Label(input_frame, text="File B (New File):", font=("Arial", 10, "bold"), bg="#f0f0f0").grid(row=2, column=0, sticky="w", pady=(10,0))
        self.entry_b = tk.Entry(input_frame, width=60, font=("Arial", 10))
        self.entry_b.grid(row=3, column=0, padx=5, pady=2)
        tk.Button(input_frame, text="Browse", command=lambda: self.browse(self.entry_b)).grid(row=3, column=1)

        # Buttons
        btn_frame = tk.Frame(self, bg="#f0f0f0")
        btn_frame.pack(pady=10)
        
        self.compare_btn = tk.Button(btn_frame, text="COMPARE FILES", command=self.compare, 
                                     bg="#2e7d32", fg="white", font=("Arial", 11, "bold"), pady=5, padx=20)
        self.compare_btn.pack(side="left", padx=5)
        
        self.export_btn = tk.Button(btn_frame, text="EXPORT TO TXT", command=self.export_results, 
                                    bg="#0277bd", fg="white", font=("Arial", 10), pady=5, padx=10)
        self.export_btn.pack(side="left", padx=5)

        # Results
        tk.Label(self, text="Key Differences:", font=("Arial", 10, "bold"), bg="#f0f0f0").pack(anchor="w", padx=20)
        self.result_area = scrolledtext.ScrolledText(self, width=80, height=20, font=("Consolas", 10))
        self.result_area.pack(pady=5, padx=20, fill="both", expand=True)

        # Tags
        self.result_area.tag_config("header", font=("Consolas", 11, "bold"), foreground="#1a237e")
        self.result_area.tag_config("new", foreground="#2e7d32", font=("Consolas", 10, "bold"))
        self.result_area.tag_config("removed", foreground="#c62828", font=("Consolas", 10, "bold"))
        self.result_area.tag_config("info", foreground="#555555")

    def browse(self, entry_widget):
        filename = filedialog.askopenfilename(filetypes=[("INI Files", "*.ini"), ("All Files", "*.*")])
        if filename:
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, filename)

    def export_results(self):
        content = self.result_area.get(1.0, tk.END)
        if not content.strip():
            messagebox.showinfo("Info", "No results to export.")
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt")])
        if file_path:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            messagebox.showinfo("Success", "Report saved!")

    def compare(self):
        path_a = self.entry_a.get()
        path_b = self.entry_b.get()

        if not path_a or not path_b:
            messagebox.showwarning("Input Error", "Please select both files.")
            return

        dict_a = get_keys(path_a)
        dict_b = get_keys(path_b)

        keys_a = set(dict_a.keys())
        keys_b = set(dict_b.keys())

        new_keys = sorted(list(keys_b - keys_a))
        missing_keys = sorted(list(keys_a - keys_b))

        self.result_area.delete(1.0, tk.END)
        
        header = f"KEY COMPARISON\nFile A: {len(dict_a)} keys | File B: {len(dict_b)} keys\n"
        header += "=" * 60 + "\n"
        self.insert_text(header, "header")

        if not new_keys and not missing_keys:
            self.insert_text("\n>>> No structural differences found.", "header")
            return

        if new_keys:
            self.insert_text(f"\n[NEW KEYS IN FILE B] ({len(new_keys)}):\n", "new")
            for k in new_keys:
                info = dict_b[k]
                self.insert_text(f"  + {info['display_key']}\n", "new")
                self.insert_text(f"      Line {info['line']}: {info['text']}\n", "info")

        if missing_keys:
            self.insert_text(f"\n[MISSING IN FILE B] ({len(missing_keys)}):\n", "removed")
            for k in missing_keys:
                info = dict_a[k]
                self.insert_text(f"  - {info['display_key']}\n", "removed")
                self.insert_text(f"      Was at Line {info['line']}: {info['text']}\n", "info")

    def insert_text(self, text, tag=None):
        self.result_area.insert(tk.END, text, tag)

# --- TAB 2: FOLDER SCANNER ---

class FolderScanTab(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        
        self.configure(bg="#f0f0f0")

        # Input Frame
        input_frame = tk.Frame(self, bg="#f0f0f0", pady=10)
        input_frame.pack(fill="x", padx=20)

        tk.Label(input_frame, text="Old Version Folder:", font=("Arial", 10, "bold"), bg="#f0f0f0").grid(row=0, column=0, sticky="w")
        self.entry_a = tk.Entry(input_frame, width=60, font=("Arial", 10))
        self.entry_a.grid(row=1, column=0, padx=5, pady=2)
        tk.Button(input_frame, text="Browse", command=lambda: self.browse_folder(self.entry_a)).grid(row=1, column=1)

        tk.Label(input_frame, text="New Version Folder:", font=("Arial", 10, "bold"), bg="#f0f0f0").grid(row=2, column=0, sticky="w", pady=(10,0))
        self.entry_b = tk.Entry(input_frame, width=60, font=("Arial", 10))
        self.entry_b.grid(row=3, column=0, padx=5, pady=2)
        tk.Button(input_frame, text="Browse", command=lambda: self.browse_folder(self.entry_b)).grid(row=3, column=1)

        # Buttons
        btn_frame = tk.Frame(self, bg="#f0f0f0")
        btn_frame.pack(pady=10)
        
        self.scan_btn = tk.Button(btn_frame, text="SCAN FOLDERS", command=self.start_scan, 
                                  bg="#2e7d32", fg="white", font=("Arial", 11, "bold"), pady=5, padx=20)
        self.scan_btn.pack(side="left", padx=5)
        
        self.export_txt_btn = tk.Button(btn_frame, text="EXPORT TXT", command=self.export_txt, 
                                    bg="#0277bd", fg="white", font=("Arial", 10), pady=5, padx=10)
        self.export_txt_btn.pack(side="left", padx=5)

        # Results
        tk.Label(self, text="Scan Results:", font=("Arial", 10, "bold"), bg="#f0f0f0").pack(anchor="w", padx=20)
        self.result_area = scrolledtext.ScrolledText(self, width=80, height=20, font=("Consolas", 10))
        self.result_area.pack(pady=5, padx=20, fill="both", expand=True)
        
        # Tags
        self.result_area.tag_config("header", font=("Consolas", 11, "bold"), foreground="#1a237e")
        self.result_area.tag_config("file_path", font=("Consolas", 10, "bold"), foreground="#0277bd")
        self.result_area.tag_config("new_file", font=("Consolas", 10, "bold"), foreground="#d32f2f")
        self.result_area.tag_config("new_key", foreground="#2e7d32")
        self.result_area.tag_config("changed_key", foreground="#ef6c00")
        self.result_area.tag_config("info", foreground="#555555")

    def browse_folder(self, entry_widget):
        folder = filedialog.askdirectory()
        if folder:
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, folder)

    def export_txt(self):
        content = self.result_area.get(1.0, tk.END)
        if not content.strip():
            messagebox.showinfo("Info", "No results to export.")
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt")])
        if file_path:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            messagebox.showinfo("Done", "Text Report saved!")

    def start_scan(self):
        folder_a = self.entry_a.get()
        folder_b = self.entry_b.get()
        if not folder_a or not folder_b:
            messagebox.showwarning("Error", "Select both folders.")
            return
        
        self.result_area.delete(1.0, tk.END)
        self.result_area.insert(tk.END, "Scanning... grouping files by NAME.\n", "info")
        self.update_idletasks()
        self.compare_folders_by_name(folder_a, folder_b)

    def build_file_database(self, root_folder):
        """
        Returns a tuple:
        1. A dictionary: { "filename_lower": { "paths": [...], "keys": { key_id: data } } }
        2. Int: Total physical files found
        """
        db = {}
        physical_count = 0
        
        for dirpath, _, filenames in os.walk(root_folder):
            for f in filenames:
                if not f.lower().endswith('.ini'):
                    continue
                
                # FILTERS
                f_lower = f.lower()
                if f_lower == 'mod.ini':
                    continue
                if f_lower == 'stringtableexpress.ini':
                    continue
                
                name_part = os.path.splitext(f)[0]
                if name_part.lower() == 'stringtable.express':
                    continue

                full_path = os.path.join(dirpath, f)
                physical_count += 1
                
                # Initialize entry in DB if not exists
                if f_lower not in db:
                    db[f_lower] = {"paths": [], "keys": {}}
                
                # Add path to list
                db[f_lower]["paths"].append(full_path)
                
                # Parse and merge keys
                keys = get_keys(full_path)
                if keys:
                    for k_id, k_data in keys.items():
                        # If key already exists from another file with same name, it gets overwritten here
                        # But we also store the specific source path for this key
                        entry = k_data.copy()
                        entry['source_path'] = full_path
                        db[f_lower]["keys"][k_id] = entry
                        
        return db, physical_count

    def compare_folders_by_name(self, root_a, root_b):
        # 1. Build Databases
        db_a, count_a = self.build_file_database(root_a)
        db_b, count_b = self.build_file_database(root_b)

        self.result_area.delete(1.0, tk.END)
        
        stats = {"new_files": 0, "changed_files": 0, "new_keys": 0}
        
        matched_files_a = set()

        # 2. Iterate New Files (B) by unique filename
        for filename_lower, data_b in sorted(db_b.items()):
            data_a = db_a.get(filename_lower)
            
            keys_b = data_b["keys"]
            
            # For display, pick the first path found in B
            # (Or we could list all, but usually one is enough for context)
            display_path = os.path.relpath(data_b["paths"][0], root_b)

            # --- CASE 1: NEW FILE ---
            if not data_a:
                stats["new_files"] += 1
                stats["new_keys"] += len(keys_b)
                
                self.insert_text(f"\n{'='*60}\n", "info")
                self.insert_text(f"[NEW FILE] {filename_lower}\n", "new_file")
                # Show where it was found
                self.insert_text(f"Found in: {display_path}\n", "info")
                self.insert_text(f"{'='*60}\n", "info")
                
                self.insert_text(f"   All Keys ({len(keys_b)}):\n", "new_key")
                
                for k in sorted(keys_b.keys()):
                    info = keys_b[k]
                    self.insert_text(f"     + {info['display_key']}\n", "new_key")
                    # Show specific path if multiple files have same name
                    source_display = os.path.relpath(info['source_path'], root_b)
                    self.insert_text(f"       Line ({info['line']}): {info['value']}\n", "info")
                continue

            # --- CASE 2: EXISTING FILE ---
            matched_files_a.add(filename_lower)
            
            keys_a = data_a["keys"]
            
            set_a = set(keys_a.keys())
            set_b = set(keys_b.keys())
            
            new_keys = sorted(list(set_b - set_a))
            
            changed_values = []
            common_keys = set_a & set_b
            for k in common_keys:
                if keys_a[k]['value'] != keys_b[k]['value']:
                    changed_values.append(k)

            if new_keys or changed_values:
                stats["changed_files"] += 1
                stats["new_keys"] += len(new_keys)
                
                self.insert_text(f"\n{'='*60}\n", "info")
                self.insert_text(f"[MODIFIED] {filename_lower}\n", "file_path")
                self.insert_text(f"{'='*60}\n", "info")

                if new_keys:
                    self.insert_text(f"   New Keys ({len(new_keys)}):\n", "new_key")
                    for k in new_keys:
                        info = keys_b[k]
                        source_display = os.path.relpath(info['source_path'], root_b)
                        self.insert_text(f"     + {info['display_key']}\n", "new_key")
                        self.insert_text(f"       Path: {source_display}\n", "info")
                        self.insert_text(f"       Line ({info['line']}): {info['value']}\n", "info")

                if changed_values:
                    self.insert_text(f"   Changed Values ({len(changed_values)}):\n", "changed_key")
                    for k in changed_values:
                        info_a = keys_a[k]
                        info_b = keys_b[k]
                        
                        path_a_disp = os.path.relpath(info_a['source_path'], root_a)
                        path_b_disp = os.path.relpath(info_b['source_path'], root_b)
                        
                        self.insert_text(f"     ~ {info_b['display_key']}\n", "changed_key")
                        self.insert_text(f"       Old (Line {info_a['line']}): {info_a['value']}\n", "info")
                        self.insert_text(f"       New (Line {info_b['line']}): {info_b['value']}\n", "info")
                        self.insert_text(f"       Location: {path_b_disp}\n", "info")

        # 3. Check for Removed Files
        missing_files = set(db_a.keys()) - matched_files_a
        if missing_files:
            self.insert_text(f"\n{'='*60}\n", "info")
            self.insert_text("[REMOVED FILES] (Exist in A, missing in B):\n", "removed")
            self.insert_text(f"{'='*60}\n", "info")
            for f_name in sorted(list(missing_files)):
                # Show path of the removed file
                path_a = db_a[f_name]["paths"][0]
                rel_path_a = os.path.relpath(path_a, root_a)
                self.insert_text(f"  - {f_name} (was at {rel_path_a})\n", "removed")

        # Summary
        self.insert_text("\n\n" + "="*60 + "\n", "info")
        self.insert_text("SCAN COMPLETE\n", "header")
        self.insert_text(f"Total physical files scanned in New: {count_b}\n", "info")
        self.insert_text(f"Unique filenames in New: {len(db_b)}\n", "info")
        self.insert_text(f"New files detected: {stats['new_files']}\n", "new_file")
        self.insert_text(f"Modified files: {stats['changed_files']}\n", "file_path")
        self.insert_text(f"Removed files: {len(missing_files)}\n", "removed")
        self.insert_text(f"Total new keys to translate: {stats['new_keys']}\n", "new_key")

    def insert_text(self, text, tag=None):
        self.result_area.insert(tk.END, text, tag)

# --- MAIN APP ---

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Gothic Modpack Translator Tool v7.3")
        self.geometry("900x750")

        notebook = ttk.Notebook(self)
        notebook.pack(fill='both', expand=True, padx=5, pady=5)

        tab1 = SingleFileTab(notebook)
        tab2 = FolderScanTab(notebook)

        notebook.add(tab1, text=" Single File Compare ")
        notebook.add(tab2, text=" Folder Scanner ")

        style = ttk.Style()
        style.theme_use('clam') 

if __name__ == "__main__":
    app = App()
    app.mainloop()