"""Small GUI app: configure Logitech mouse buttons and generate a G HUB Lua script.

Run: python3 app.py
"""
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from generator import generate_lua, validate

ACTION_TYPES = ["remap", "text", "combo", "toggle"]


class MouseConfigApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Mouse Button Config -> G HUB Lua Generator")
        self.geometry("760x520")

        self.configs = []  # list of dicts
        self._build_ui()

    def _build_ui(self):
        # left: list of buttons
        left = ttk.Frame(self, padding=8)
        left.pack(side="left", fill="y")

        ttk.Label(left, text="Configured buttons").pack(anchor="w")
        self.listbox = tk.Listbox(left, width=28, height=20)
        self.listbox.pack(fill="y", expand=True, pady=4)
        self.listbox.bind("<<ListboxSelect>>", self._on_select)

        btns = ttk.Frame(left)
        btns.pack(fill="x", pady=4)
        ttk.Button(btns, text="+ Add", command=self._add_new).pack(side="left")
        ttk.Button(btns, text="Delete", command=self._delete_selected).pack(side="left")

        ttk.Button(left, text="Load config JSON", command=self._load_json).pack(fill="x", pady=(12, 2))
        ttk.Button(left, text="Save config JSON", command=self._save_json).pack(fill="x", pady=2)

        # right: editor form
        right = ttk.Frame(self, padding=8)
        right.pack(side="left", fill="both", expand=True)

        form = ttk.LabelFrame(right, text="Edit selected button", padding=8)
        form.pack(fill="x")

        row = ttk.Frame(form)
        row.pack(fill="x", pady=2)
        ttk.Label(row, text="Button number:", width=16).pack(side="left")
        self.button_var = tk.StringVar(value="4")
        ttk.Entry(row, textvariable=self.button_var, width=10).pack(side="left")

        row = ttk.Frame(form)
        row.pack(fill="x", pady=2)
        ttk.Label(row, text="Action type:", width=16).pack(side="left")
        self.type_var = tk.StringVar(value="remap")
        type_menu = ttk.Combobox(row, textvariable=self.type_var, values=ACTION_TYPES, state="readonly", width=12)
        type_menu.pack(side="left")
        type_menu.bind("<<ComboboxSelected>>", lambda e: self._refresh_fields())

        self.fields_frame = ttk.Frame(form)
        self.fields_frame.pack(fill="x", pady=6)
        self.field_vars = {}
        self._refresh_fields()

        ttk.Button(form, text="Save this button", command=self._save_current).pack(anchor="e", pady=(6, 0))

        # generated output
        out_frame = ttk.LabelFrame(right, text="Generated Lua script", padding=8)
        out_frame.pack(fill="both", expand=True, pady=(10, 0))

        self.output = tk.Text(out_frame, height=14, wrap="none")
        self.output.pack(fill="both", expand=True)

        out_btns = ttk.Frame(right)
        out_btns.pack(fill="x", pady=6)
        ttk.Button(out_btns, text="Generate Script", command=self._generate).pack(side="left")
        ttk.Button(out_btns, text="Save As .lua", command=self._save_lua).pack(side="left", padx=6)

    # ---- field builders per action type ----
    def _refresh_fields(self):
        for w in self.fields_frame.winfo_children():
            w.destroy()
        self.field_vars = {}
        t = self.type_var.get()

        if t == "remap":
            self._add_field("keys", "Keys (comma-separated, e.g. lctrl,c):", "lctrl,c")
        elif t == "text":
            self._add_field("text", "Text to type:", "")
        elif t == "combo":
            self._add_field("steps", "Steps (key or delay:ms, comma-separated, e.g. b,delay:150,1):", "")
        elif t == "toggle":
            self._add_field("key", "Key to repeat:", "f")
            self._add_field("interval_ms", "Interval ms:", "500")

    def _add_field(self, name, label, default):
        row = ttk.Frame(self.fields_frame)
        row.pack(fill="x", pady=2)
        ttk.Label(row, text=label, width=40).pack(side="left")
        var = tk.StringVar(value=default)
        ttk.Entry(row, textvariable=var, width=30).pack(side="left")
        self.field_vars[name] = var

    # ---- list management ----
    def _refresh_listbox(self):
        self.listbox.delete(0, tk.END)
        for cfg in self.configs:
            self.listbox.insert(tk.END, f'Button {cfg["button"]}: {cfg["type"]}')

    def _on_select(self, event):
        sel = self.listbox.curselection()
        if not sel:
            return
        cfg = self.configs[sel[0]]
        self.button_var.set(str(cfg["button"]))
        self.type_var.set(cfg["type"])
        self._refresh_fields()
        if cfg["type"] == "remap":
            self.field_vars["keys"].set(",".join(cfg["keys"]))
        elif cfg["type"] == "text":
            self.field_vars["text"].set(cfg["text"])
        elif cfg["type"] == "combo":
            parts = []
            for step in cfg["steps"]:
                if "key" in step:
                    parts.append(step["key"])
                else:
                    parts.append(f'delay:{step["delay_ms"]}')
            self.field_vars["steps"].set(",".join(parts))
        elif cfg["type"] == "toggle":
            self.field_vars["key"].set(cfg["key"])
            self.field_vars["interval_ms"].set(str(cfg["interval_ms"]))

    def _add_new(self):
        self.listbox.selection_clear(0, tk.END)
        self.button_var.set("4")
        self.type_var.set("remap")
        self._refresh_fields()

    def _delete_selected(self):
        sel = self.listbox.curselection()
        if not sel:
            return
        del self.configs[sel[0]]
        self._refresh_listbox()

    def _current_cfg_from_form(self):
        try:
            btn = int(self.button_var.get())
        except ValueError:
            raise ValueError("Button number must be an integer")
        t = self.type_var.get()
        cfg = {"button": btn, "type": t}

        if t == "remap":
            keys = [k.strip() for k in self.field_vars["keys"].get().split(",") if k.strip()]
            cfg["keys"] = keys
        elif t == "text":
            cfg["text"] = self.field_vars["text"].get()
        elif t == "combo":
            steps = []
            for part in self.field_vars["steps"].get().split(","):
                part = part.strip()
                if not part:
                    continue
                if part.startswith("delay:"):
                    steps.append({"delay_ms": int(part.split(":", 1)[1])})
                else:
                    steps.append({"key": part})
            cfg["steps"] = steps
        elif t == "toggle":
            cfg["key"] = self.field_vars["key"].get()
            cfg["interval_ms"] = int(self.field_vars["interval_ms"].get())

        validate(cfg)
        return cfg

    def _save_current(self):
        try:
            cfg = self._current_cfg_from_form()
        except ValueError as e:
            messagebox.showerror("Invalid input", str(e))
            return

        sel = self.listbox.curselection()
        existing_idx = None
        for i, c in enumerate(self.configs):
            if c["button"] == cfg["button"] and (not sel or i == sel[0]):
                existing_idx = i
                break

        if sel:
            self.configs[sel[0]] = cfg
        elif existing_idx is not None:
            self.configs[existing_idx] = cfg
        else:
            self.configs.append(cfg)

        self._refresh_listbox()

    # ---- generate / save ----
    def _generate(self):
        try:
            lua = generate_lua(self.configs)
        except ValueError as e:
            messagebox.showerror("Cannot generate", str(e))
            return
        self.output.delete("1.0", tk.END)
        self.output.insert(tk.END, lua)

    def _save_lua(self):
        if not self.output.get("1.0", tk.END).strip():
            self._generate()
        path = filedialog.asksaveasfilename(defaultextension=".lua", filetypes=[("Lua script", "*.lua")])
        if not path:
            return
        with open(path, "w") as f:
            f.write(self.output.get("1.0", tk.END))
        messagebox.showinfo("Saved", f"Script saved to {path}")

    def _save_json(self):
        path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json")])
        if not path:
            return
        with open(path, "w") as f:
            json.dump(self.configs, f, indent=2)
        messagebox.showinfo("Saved", f"Config saved to {path}")

    def _load_json(self):
        path = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if not path:
            return
        with open(path) as f:
            self.configs = json.load(f)
        self._refresh_listbox()


if __name__ == "__main__":
    app = MouseConfigApp()
    app.mainloop()
