import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import os
import importlib
import re

try:
    tkinterdnd2 = importlib.import_module('tkinterdnd2')
    TkinterDnD = tkinterdnd2.TkinterDnD
    DND_FILES = tkinterdnd2.DND_FILES
except ImportError:
    TkinterDnD = None
    DND_FILES = None

def analyze_language(text):
    """
    Checks value content after '=' for the scan tab.

    Fails the check if value contains:
    - ';;'
    - '[en]' or '[eng]'
    - standalone token 'en' or 'eng'

    Otherwise passes if any alphabetic letters are present.
    Returns: (is_english, reason)
    """
    if '=' not in text:
        return False, "No value found"

    value = text.split('=', 1)[1]
    value_stripped = value.strip()
    leading_value = value.lstrip().lower()

    if leading_value.startswith(';'):
        return False, "Starts with ';' after '='"
    
    if leading_value.startswith(';;'):
        return False, "Starts with ';;' after '='"

    if leading_value.startswith('[en]') or leading_value.startswith('[eng]'):
        return False, "Starts with [en] or [eng] marker"

    if re.match(r'^(?:en|eng)\b', leading_value):
        return False, "Starts with token 'en' or 'eng'"

    if re.search(r'[a-zA-Z]', value_stripped):
        return True, "Passes English check"

    if len(value_stripped) == 0:
        return False, "Empty value"

    return False, "No alphabetic letters found"

def get_keys(file_path):
    encodings = ['utf-16', 'utf-8-sig', 'utf-8', 'cp1250', 'cp1252']
    found_keys = {}

    if not os.path.exists(file_path):
        return None
    
    for enc in encodings:
        try:
            with open(file_path, 'rb') as f:
                content = f.read().decode(enc)
                for line_num, line in enumerate(content.splitlines(), 1):
                    stripped_line = line.strip()

                    # Skip empty lines, comments, and section headers
                    if not stripped_line or stripped_line.startswith('#') or stripped_line.startswith(';') or stripped_line.startswith('['):
                        continue
                        
                    if '=' in stripped_line:
                        key, value = stripped_line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        if key:
                            key_id = key.lower()
                            found_keys[key_id] = {
                                "text": stripped_line,
                                "value": value,
                                "line": line_num,
                                "display_key": key,
                            }
                return found_keys
        except:
            continue
    return {}

def count_lines(file_path):
    encodings = ['utf-16', 'utf-8-sig', 'utf-8', 'cp1250', 'cp1252']

    if not os.path.exists(file_path):
        return None

    for enc in encodings:
        try:
            with open(file_path, 'rb') as f:
                content = f.read().decode(enc)
                return len(content.splitlines())
        except:
            continue

    return None

def get_compare_lines(file_path):
    encodings = ['utf-16', 'utf-8-sig', 'utf-8', 'cp1250', 'cp1252']

    if not os.path.exists(file_path):
        return None

    for enc in encodings:
        try:
            with open(file_path, 'rb') as f:
                content = f.read().decode(enc)
                lines = []
                for line_num, line in enumerate(content.splitlines(), 1):
                    stripped_line = line.strip()
                    if not stripped_line or stripped_line.startswith('#') or stripped_line.startswith(';') or stripped_line.startswith('['):
                        continue

                    if '=' not in stripped_line:
                        continue

                    key_text, value_text = stripped_line.split('=', 1)
                    key_text = key_text.strip()
                    value_text = value_text.strip()
                    if not key_text:
                        continue

                    lines.append({
                        "line": line_num,
                        "text": stripped_line,
                        "key": key_text,
                        "key_norm": key_text.lower(),
                        "value": value_text,
                    })

                return lines
        except:
            continue

    return []

def build_compare_report(path_a, path_b, run_translation_scan=False):
    lines_a = get_compare_lines(path_a)
    lines_b = get_compare_lines(path_b)
    line_count_a = count_lines(path_a)
    line_count_b = count_lines(path_b)

    if lines_a is None or lines_b is None:
        return None

    keys_a = {item["key_norm"] for item in lines_a}
    keys_b = {item["key_norm"] for item in lines_b}

    missing_in_translation = sorted(keys_b - keys_a)
    extra_in_translation = sorted(keys_a - keys_b)
    translation_lines = {item["key_norm"]: item for item in lines_a}
    source_lines = {item["key_norm"]: item for item in lines_b}

    report = {
        "path_a": path_a,
        "path_b": path_b,
        "line_count_a": line_count_a,
        "line_count_b": line_count_b,
        "lines_a": lines_a,
        "lines_b": lines_b,
        "missing_in_translation": missing_in_translation,
        "extra_in_translation": extra_in_translation,
        "translation_lines": translation_lines,
        "source_lines": source_lines,
        "translation_scan": None,
    }

    if run_translation_scan:
        trans_ok = []
        trans_fail = []
        for _, info in translation_lines.items():
            is_eng, reason = analyze_language(info['text'])
            if is_eng:
                trans_ok.append((info, reason))
            else:
                trans_fail.append((info, reason))

        report["translation_scan"] = {
            "ok": trans_ok,
            "fail": trans_fail,
        }

    return report

def collect_stringtable_files(folder_path):
    found = {}
    for root, _, files in os.walk(folder_path):
        for name in files:
            if name.lower() != "stringtable.ini":
                continue

            full_path = os.path.join(root, name)
            rel_path = os.path.relpath(full_path, folder_path).replace('\\', '/')
            rel_lower = rel_path.lower()
            mods_index = rel_lower.find('mods/')
            match_key = rel_lower[mods_index:] if mods_index >= 0 else rel_lower
            found.setdefault(match_key, []).append(full_path)

    for key in found:
        found[key].sort()
    return found


# TAB 1: FILE COMPARATOR
class CompareTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        
        tk.Label(self, text="Compare Two Files", font=("Arial", 14, "bold")).pack(pady=10)
        tk.Label(self, text="File A is the translation file. Compare it against File B.", 
                 font=("Arial", 9), fg="gray").pack(pady=5)

        # --- File A Section ---
        tk.Label(self, text="File A (Reference):", font=("Arial", 10, "bold")).pack(anchor="w", padx=20)
        frame_a = tk.Frame(self)
        frame_a.pack(fill="x", padx=20, pady=5)
        self.entry_a = tk.Entry(frame_a, font=("Consolas", 9))
        self.entry_a.pack(side="left", fill="x", expand=True, padx=(0, 5))
        tk.Button(frame_a, text="Browse", command=lambda: self.browse(self.entry_a)).pack(side="right")
        
        # Enable Drag & Drop for Entry A when available
        if DND_FILES is not None:
            self.entry_a.drop_target_register(DND_FILES)
            self.entry_a.dnd_bind('<<Drop>>', lambda e: self.on_drop(e, self.entry_a))
            self.entry_a.dnd_bind('<<DragEnter>>', lambda e: self.on_drag_enter(e, self.entry_a))
            self.entry_a.dnd_bind('<<DragLeave>>', lambda e: self.on_drag_leave(e, self.entry_a))

        # Option to scan the translation (File A) for English content
        self.scan_translation_var = tk.BooleanVar(value=False)
        tk.Checkbutton(self, text="Run English-check on translation (File A)",
                       variable=self.scan_translation_var).pack(anchor="w", padx=20, pady=(0,5))

        # --- File B Section ---
        tk.Label(self, text="File B (New File):", font=("Arial", 10, "bold")).pack(anchor="w", padx=20, pady=(10, 0))
        frame_b = tk.Frame(self)
        frame_b.pack(fill="x", padx=20, pady=5)
        self.entry_b = tk.Entry(frame_b, font=("Consolas", 9))
        self.entry_b.pack(side="left", fill="x", expand=True, padx=(0, 5))
        tk.Button(frame_b, text="Browse", command=lambda: self.browse(self.entry_b)).pack(side="right")
        
        # Enable Drag & Drop for Entry B when available
        if DND_FILES is not None:
            self.entry_b.drop_target_register(DND_FILES)
            self.entry_b.dnd_bind('<<Drop>>', lambda e: self.on_drop(e, self.entry_b))
            self.entry_b.dnd_bind('<<DragEnter>>', lambda e: self.on_drag_enter(e, self.entry_b))
            self.entry_b.dnd_bind('<<DragLeave>>', lambda e: self.on_drag_leave(e, self.entry_b))

        # --- Compare Button ---
        self.compare_btn = tk.Button(self, text="COMPARE FILES", command=self.compare, 
                                     bg="#2e7d32", fg="white", font=("Arial", 11, "bold"), pady=10)
        self.compare_btn.pack(pady=20, fill="x", padx=100)

        # --- Results Area ---
        tk.Label(self, text="Scan results:", font=("Arial", 10)).pack(anchor="w", padx=20)
        self.result_area = scrolledtext.ScrolledText(
            self,
            width=80,
            height=15,
            font=("Consolas", 10),
            background="#f8fafc",
            foreground="#0f172a",
            insertbackground="#0f172a",
            borderwidth=1,
            relief="solid",
            wrap="none",
        )
        self.result_area.pack(pady=5, padx=20, fill="both", expand=True)

        self.result_area.tag_config("title", foreground="#0f172a", font=("Arial", 12, "bold"))
        self.result_area.tag_config("subtitle", foreground="#475569", font=("Arial", 9, "bold"))
        self.result_area.tag_config("section", foreground="white", background="#1d4ed8", font=("Consolas", 10, "bold"))
        self.result_area.tag_config("summary_label", foreground="#64748b", font=("Consolas", 10, "bold"))
        self.result_area.tag_config("summary_value", foreground="#0f172a", font=("Consolas", 10, "bold"))
        self.result_area.tag_config("legend_a", foreground="#b91c1c", background="#fee2e2", font=("Consolas", 9, "bold"))
        self.result_area.tag_config("legend_b", foreground="#166534", background="#dcfce7", font=("Consolas", 9, "bold"))
        self.result_area.tag_config("legend_note", foreground="#475569", font=("Consolas", 9))
        self.result_area.tag_config("block_replace", foreground="#7c2d12", background="#ffedd5", font=("Consolas", 10, "bold"))
        self.result_area.tag_config("block_insert", foreground="#14532d", background="#dcfce7", font=("Consolas", 10, "bold"))
        self.result_area.tag_config("block_delete", foreground="#7f1d1d", background="#fee2e2", font=("Consolas", 10, "bold"))
        self.result_area.tag_config("line_num_a", foreground="#b91c1c", font=("Consolas", 10, "bold"))
        self.result_area.tag_config("line_num_b", foreground="#166534", font=("Consolas", 10, "bold"))
        self.result_area.tag_config("line_text", foreground="#0f172a")
        self.result_area.tag_config("separator", foreground="#cbd5e1")
        self.result_area.tag_config("ok", foreground="#166534", background="#dcfce7", font=("Consolas", 9, "bold"))
        self.result_area.tag_config("warn", foreground="#7f1d1d", background="#fee2e2", font=("Consolas", 9, "bold"))

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

    def write_line(self, text="", *tags):
        self.result_area.insert(tk.END, text + "\n", tags)

    def compare(self):
        path_a = self.entry_a.get()
        path_b = self.entry_b.get()

        if not path_a or not path_b:
            messagebox.showwarning("Input Error", "Please select both files before comparing.")
            return

        report = build_compare_report(path_a, path_b, self.scan_translation_var.get())
        if report is None:
            messagebox.showwarning("Input Error", "One or both file paths do not exist.")
            return

        lines_a = report["lines_a"]
        lines_b = report["lines_b"]
        line_count_a = report["line_count_a"]
        line_count_b = report["line_count_b"]
        missing_in_translation = report["missing_in_translation"]
        extra_in_translation = report["extra_in_translation"]
        translation_lines = report["translation_lines"]
        source_lines = report["source_lines"]

        self.result_area.delete(1.0, tk.END)

        self.write_line("SUMMARY", "section")
        self.write_line(f"Lines in File A: {line_count_a if line_count_a is not None else 'unknown'}", "summary_label")
        self.write_line(f"Comparable keys in File A: {len(lines_a)}", "summary_value")
        self.write_line(f"Lines in File B: {line_count_b if line_count_b is not None else 'unknown'}", "summary_label")
        self.write_line(f"Comparable keys in File B: {len(lines_b)}", "summary_value")
        self.write_line(f"Keys missing from translation: {len(missing_in_translation)}", "summary_value")
        self.write_line(f"Keys extra in translation: {len(extra_in_translation)}", "summary_value")
        self.write_line("")
        self.write_line("LEGEND", "section")
        self.write_line("Missing = keys that exist in File B but not in File A", "legend_b")
        self.write_line("Extra = keys that exist in File A but not in File B", "legend_a")
        self.write_line("Headers, empty lines, comments, values, and key order are ignored.", "legend_note")
        self.write_line("")

        if not missing_in_translation and not extra_in_translation:
            self.write_line("No differences found after comparing only the text before '='.", "summary_value")
        else:
            self.write_line("MISSING KEYS", "section")
            if missing_in_translation:
                for index, key_norm in enumerate(missing_in_translation, 1):
                    source_item = source_lines[key_norm]
                    self.write_line(f"{index}. File B line {source_item['line']}: {source_item['key']}", "line_num_b")
            else:
                self.write_line("None", "summary_value")

            self.write_line("")
            self.write_line("EXTRA KEYS", "section")
            if extra_in_translation:
                for index, key_norm in enumerate(extra_in_translation, 1):
                    item = translation_lines[key_norm]
                    self.write_line(f"{index}. File A line {item['line']}: {item['key']}", "line_num_a")
            else:
                self.write_line("None", "summary_value")

        # If enabled, run the English-check on the translation (File A) and include results
        if report["translation_scan"] is not None:
            trans_ok = report["translation_scan"]["ok"]
            trans_fail = report["translation_scan"]["fail"]

            self.write_line("")
            self.write_line("TRANSLATION ENGLISH CHECK", "section")
            self.write_line(f"Total entries scanned: {len(translation_lines)}", "summary_label")
            self.write_line(f"Passes English check: {len(trans_ok)}", "ok")
            self.write_line(f"Fails English check: {len(trans_fail)}", "warn")
            self.write_line("")

            if trans_fail:
                for i, (info, reason) in enumerate(trans_fail, 1):
                    self.write_line(f"{i}. File A line {info['line']}: {info['key']}", "line_num_a")
                    self.write_line(f"[!] Fails English check: {reason}", "warn")
                    self.write_line(info['text'], "line_text")
                    self.write_line("-" * 70, "separator")
            else:
                self.write_line("No failing entries found.", "summary_value")

        self.result_area.yview_moveto(0)

# TAB 2: LANGUAGE SCANNER
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
        
        # Enable Drag & Drop for Entry when available
        if DND_FILES is not None:
            self.entry_file.drop_target_register(DND_FILES)
            self.entry_file.dnd_bind('<<Drop>>', lambda e: self.on_drop(e))
            self.entry_file.dnd_bind('<<DragEnter>>', lambda e: self.on_drag_enter(e))
            self.entry_file.dnd_bind('<<DragLeave>>', lambda e: self.on_drag_leave(e))

        # --- Scan Button ---
        self.scan_btn = tk.Button(self, text="SCAN FILE", command=self.scan, 
                                  bg="#2e7d32", fg="white", font=("Arial", 11, "bold"), pady=10)
        self.scan_btn.pack(pady=20, fill="x", padx=100)

        # --- Results Area ---
        tk.Label(self, text="Scan Results:", font=("Arial", 10)).pack(anchor="w", padx=20)
        self.result_area = scrolledtext.ScrolledText(
            self,
            width=80,
            height=15,
            font=("Consolas", 10),
            background="#f8fafc",
            foreground="#0f172a",
            insertbackground="#0f172a",
            borderwidth=1,
            relief="solid",
            wrap="none",
        )
        self.result_area.pack(pady=5, padx=20, fill="both", expand=True)

        self.result_area.tag_config("title", foreground="#0f172a", font=("Arial", 12, "bold"))
        self.result_area.tag_config("subtitle", foreground="#475569", font=("Arial", 9, "bold"))
        self.result_area.tag_config("section", foreground="white", background="#1d4ed8", font=("Consolas", 10, "bold"))
        self.result_area.tag_config("summary_label", foreground="#64748b", font=("Consolas", 10, "bold"))
        self.result_area.tag_config("summary_value", foreground="#0f172a", font=("Consolas", 10, "bold"))
        self.result_area.tag_config("entry_header", foreground="#0f172a", font=("Consolas", 10, "bold"))
        self.result_area.tag_config("ok", foreground="#166534", background="#dcfce7", font=("Consolas", 9, "bold"))
        self.result_area.tag_config("warn", foreground="#7f1d1d", background="#fee2e2", font=("Consolas", 9, "bold"))
        self.result_area.tag_config("meta", foreground="#475569", font=("Consolas", 9))
        self.result_area.tag_config("line_text", foreground="#0f172a")
        self.result_area.tag_config("separator", foreground="#cbd5e1")

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

    def write_line(self, text="", *tags):
        self.result_area.insert(tk.END, text + "\n", tags)

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

        self.write_line("SUMMARY", "section")
        self.write_line(f"File: {path}", "summary_label")
        self.write_line(f"Total entries: {total_count}", "summary_value")
        self.write_line(f"Passes English check: {has_english_count}", "ok")
        self.write_line(f"Fails English check: {no_english_count}", "warn")
        self.write_line("")

        # --- Display Results (always only failed entries) ---
        keys_to_show = no_english_keys
        
        if not keys_to_show:
            self.write_line("No entries match the current filter.", "summary_value")
        else:
            self.write_line("ENTRIES", "section")
            for i, (k, info, reason) in enumerate(keys_to_show, 1):
                is_eng = k in [x[0] for x in english_keys]

                self.write_line(f"Entry #{i}: {k}", "entry_header")
                self.write_line(f"Line {info['line']}", "meta")

                if is_eng:
                    self.write_line("[OK] Passes English check", "ok")
                else:
                    self.write_line("[!] Fails English check", "warn")

                self.write_line(f"Reason: {reason}", "meta")
                self.write_line(info['text'], "line_text")
                self.write_line("-" * 70, "separator")
            
            self.result_area.yview_moveto(0)

# TAB 3: FOLDER COMPARATOR
class FolderCompareTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)

        tk.Label(self, text="Compare Folder A vs Folder B", font=("Arial", 14, "bold")).pack(pady=10)
        tk.Label(
            self,
            text="Folder A is translation. Matches are made for stringtable.ini files by normalized path (from Mods/ onward).",
            font=("Arial", 9),
            fg="gray"
        ).pack(pady=5)

        tk.Label(self, text="Folder A (Translation):", font=("Arial", 10, "bold")).pack(anchor="w", padx=20)
        frame_a = tk.Frame(self)
        frame_a.pack(fill="x", padx=20, pady=5)
        self.entry_folder_a = tk.Entry(frame_a, font=("Consolas", 9))
        self.entry_folder_a.pack(side="left", fill="x", expand=True, padx=(0, 5))
        tk.Button(frame_a, text="Browse", command=lambda: self.browse_folder(self.entry_folder_a)).pack(side="right")

        if DND_FILES is not None:
            self.entry_folder_a.drop_target_register(DND_FILES)
            self.entry_folder_a.dnd_bind('<<Drop>>', lambda e: self.on_drop_folder(e, self.entry_folder_a))
            self.entry_folder_a.dnd_bind('<<DragEnter>>', lambda e: self.on_drag_enter_folder(e, self.entry_folder_a))
            self.entry_folder_a.dnd_bind('<<DragLeave>>', lambda e: self.on_drag_leave_folder(e, self.entry_folder_a))

        tk.Label(self, text="Folder B (Modpack):", font=("Arial", 10, "bold")).pack(anchor="w", padx=20, pady=(10, 0))
        frame_b = tk.Frame(self)
        frame_b.pack(fill="x", padx=20, pady=5)
        self.entry_folder_b = tk.Entry(frame_b, font=("Consolas", 9))
        self.entry_folder_b.pack(side="left", fill="x", expand=True, padx=(0, 5))
        tk.Button(frame_b, text="Browse", command=lambda: self.browse_folder(self.entry_folder_b)).pack(side="right")

        if DND_FILES is not None:
            self.entry_folder_b.drop_target_register(DND_FILES)
            self.entry_folder_b.dnd_bind('<<Drop>>', lambda e: self.on_drop_folder(e, self.entry_folder_b))
            self.entry_folder_b.dnd_bind('<<DragEnter>>', lambda e: self.on_drag_enter_folder(e, self.entry_folder_b))
            self.entry_folder_b.dnd_bind('<<DragLeave>>', lambda e: self.on_drag_leave_folder(e, self.entry_folder_b))

        self.compare_btn = tk.Button(
            self,
            text="COMPARE FOLDERS",
            command=self.compare_folders,
            bg="#2e7d32",
            fg="white",
            font=("Arial", 11, "bold"),
            pady=10
        )
        self.compare_btn.pack(pady=20, fill="x", padx=100)

        tk.Label(self, text="Folder compare results:", font=("Arial", 10)).pack(anchor="w", padx=20)
        self.result_area = scrolledtext.ScrolledText(
            self,
            width=80,
            height=15,
            font=("Consolas", 10),
            background="#f8fafc",
            foreground="#0f172a",
            insertbackground="#0f172a",
            borderwidth=1,
            relief="solid",
            wrap="none",
        )
        self.result_area.pack(pady=5, padx=20, fill="both", expand=True)

        self.result_area.tag_config("section", foreground="white", background="#1d4ed8", font=("Consolas", 10, "bold"))
        self.result_area.tag_config("summary_label", foreground="#64748b", font=("Consolas", 10, "bold"))
        self.result_area.tag_config("summary_value", foreground="#0f172a", font=("Consolas", 10, "bold"))
        self.result_area.tag_config("line_num_a", foreground="#b91c1c", font=("Consolas", 10, "bold"))
        self.result_area.tag_config("line_num_b", foreground="#166534", font=("Consolas", 10, "bold"))
        self.result_area.tag_config("warn", foreground="#7f1d1d", background="#fee2e2", font=("Consolas", 9, "bold"))
        self.result_area.tag_config("ok", foreground="#166534", background="#dcfce7", font=("Consolas", 9, "bold"))
        self.result_area.tag_config("line_text", foreground="#0f172a")
        self.result_area.tag_config("separator", foreground="#cbd5e1")

    def browse_folder(self, entry_widget):
        folder = filedialog.askdirectory()
        if folder:
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, folder)

    def on_drop_folder(self, event, entry_widget):
        path = event.data

        # TkDnD can wrap paths that contain spaces with braces.
        if path.startswith('{') and path.endswith('}'):
            path = path[1:-1]

        path = path.strip()
        if os.path.isfile(path):
            path = os.path.dirname(path)

        entry_widget.delete(0, tk.END)
        entry_widget.insert(0, path)
        entry_widget.config(bg="white")

    def on_drag_enter_folder(self, event, entry_widget):
        entry_widget.config(bg="#e3f2fd")

    def on_drag_leave_folder(self, event, entry_widget):
        entry_widget.config(bg="white")

    def write_line(self, text="", *tags):
        self.result_area.insert(tk.END, text + "\n", tags)

    def compare_folders(self):
        folder_a = self.entry_folder_a.get().strip()
        folder_b = self.entry_folder_b.get().strip()

        if not folder_a or not folder_b:
            messagebox.showwarning("Input Error", "Please select both folders before comparing.")
            return

        if not os.path.isdir(folder_a) or not os.path.isdir(folder_b):
            messagebox.showwarning("Input Error", "One or both folder paths do not exist.")
            return

        files_a = collect_stringtable_files(folder_a)
        files_b = collect_stringtable_files(folder_b)

        pair_items = []
        unmatched_a = []
        unmatched_b = []

        common_keys = sorted(set(files_a.keys()) & set(files_b.keys()))
        for key in common_keys:
            a_list = files_a[key]
            b_list = files_b[key]
            pair_count = min(len(a_list), len(b_list))

            for i in range(pair_count):
                pair_items.append((key, a_list[i], b_list[i]))

            if len(a_list) > pair_count:
                unmatched_a.extend((key, p) for p in a_list[pair_count:])
            if len(b_list) > pair_count:
                unmatched_b.extend((key, p) for p in b_list[pair_count:])

        only_a = sorted(set(files_a.keys()) - set(files_b.keys()))
        for key in only_a:
            unmatched_a.extend((key, p) for p in files_a[key])

        only_b = sorted(set(files_b.keys()) - set(files_a.keys()))
        for key in only_b:
            unmatched_b.extend((key, p) for p in files_b[key])

        self.result_area.delete(1.0, tk.END)
        self.write_line("SUMMARY", "section")
        self.write_line(f"Folder A stringtable.ini files: {sum(len(v) for v in files_a.values())}", "summary_label")
        self.write_line(f"Folder B stringtable.ini files: {sum(len(v) for v in files_b.values())}", "summary_label")
        self.write_line(f"Matched pairs: {len(pair_items)}", "summary_value")
        self.write_line(f"Unmatched in Folder A: {len(unmatched_a)}", "summary_value")
        self.write_line(f"Unmatched in Folder B: {len(unmatched_b)}", "summary_value")
        self.write_line("")

        if unmatched_a or unmatched_b:
            self.write_line("UNMATCHED FILES", "section")
            if unmatched_a:
                self.write_line("In Folder A only:", "line_num_a")
                for key, full_path in unmatched_a:
                    self.write_line(f"- {key} -> {full_path}", "line_text")
            if unmatched_b:
                self.write_line("In Folder B only:", "line_num_b")
                for key, full_path in unmatched_b:
                    self.write_line(f"- {key} -> {full_path}", "line_text")
            self.write_line("")

        if not pair_items:
            self.write_line("No matching stringtable.ini files were found.", "summary_value")
            self.result_area.yview_moveto(0)
            return

        self.write_line("PAIR RESULTS", "section")
        for pair_index, (key, path_a, path_b) in enumerate(pair_items, 1):
            report = build_compare_report(path_a, path_b, run_translation_scan=True)
            if report is None:
                self.write_line(f"{pair_index}. {key}", "warn")
                self.write_line("Could not read one or both files.", "warn")
                self.write_line("-" * 70, "separator")
                continue

            missing_count = len(report["missing_in_translation"])
            extra_count = len(report["extra_in_translation"])
            scan_info = report["translation_scan"] or {"ok": [], "fail": []}

            self.write_line(f"{pair_index}. {key}", "summary_value")
            self.write_line(f"File A: {path_a}", "line_num_a")
            self.write_line(f"File B: {path_b}", "line_num_b")
            self.write_line(
                f"Missing keys: {missing_count} | Extra keys: {extra_count} | Translation English fails: {len(scan_info['fail'])}",
                "summary_label"
            )

            if scan_info["fail"]:
                for i, (info, reason) in enumerate(scan_info["fail"], 1):
                    self.write_line(f"  [A fail {i}] line {info['line']}: {info['key']} -> {reason}", "warn")

            self.write_line("-" * 70, "separator")

        self.result_area.yview_moveto(0)

# MAIN APP WITH TABS

class ComparisonApp:
    def __init__(self, root):
        self.root = root
        self.root.title("inidiff")
        self.root.geometry("800x650")

        tk.Label(root, text="inidiff", font=("Arial", 14, "bold")).pack(pady=10)

        # --- Create Notebook (Tabs) ---
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # --- Tab 1: Compare ---
        self.compare_tab = CompareTab(self.notebook)
        self.notebook.add(self.compare_tab, text="Compare Files")

        # --- Tab 2: Scan ---
        self.scan_tab = ScanTab(self.notebook)
        self.notebook.add(self.scan_tab, text="Check for English")

        # --- Tab 3: Folder Compare ---
        self.folder_compare_tab = FolderCompareTab(self.notebook)
        self.notebook.add(self.folder_compare_tab, text="Folder Compare")

        # Style the tabs
        style = ttk.Style()
        style.configure('TNotebook.Tab', font=('Arial', 10, 'bold'), padding=[20, 5])

if __name__ == "__main__":
    # Initialize with TkinterDnD.Tk() when available, otherwise fall back to tk.Tk().
    root = TkinterDnD.Tk() if TkinterDnD is not None else tk.Tk()
    app = ComparisonApp(root)
    root.mainloop()