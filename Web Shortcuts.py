import tkinter as tk
import keyboard
import webbrowser
import os
import pystray
from PIL import Image, ImageDraw
import threading

CONFIG_FILE = 'key_url_config.txt'

class KeyURLSetter:
    def __init__(self, master):
        self.master = master
        master.title("Key URL Setter")
        master.geometry("400x400")
        master.configure(bg="#f0f0f0")

        self.current_key = tk.StringVar()
        self.url = tk.StringVar()
        self.configurations = []

        input_frame = tk.Frame(master, bg="#f0f0f0")
        input_frame.pack(pady=10)

        self.label1 = tk.Label(input_frame, text="Key Combination:", bg="#f0f0f0", font=("Arial", 10))
        self.label1.grid(row=0, column=0, padx=5, pady=5)
        self.key_entry = tk.Entry(input_frame, textvariable=self.current_key, width=25)
        self.key_entry.grid(row=0, column=1, padx=5, pady=5)

        self.label2 = tk.Label(input_frame, text="URL:", bg="#f0f0f0", font=("Arial", 10))
        self.label2.grid(row=1, column=0, padx=5, pady=5)
        self.url_entry = tk.Entry(input_frame, textvariable=self.url, width=25)
        self.url_entry.grid(row=1, column=1, padx=5, pady=5)

        button_frame = tk.Frame(master, bg="#f0f0f0")
        button_frame.pack(pady=10)

        self.add_button = tk.Button(button_frame, text="Add", command=self.add_key, bg="#4CAF50", fg="white", font=("Arial", 10))
        self.add_button.grid(row=0, column=0, padx=5)

        self.edit_button = tk.Button(button_frame, text="Edit", command=self.open_edit_window, bg="#2196F3", fg="white", font=("Arial", 10))
        self.edit_button.grid(row=0, column=1, padx=5)

        self.delete_button = tk.Button(button_frame, text="Delete", command=self.delete_key, bg="#f44336", fg="white", font=("Arial", 10))
        self.delete_button.grid(row=0, column=2, padx=5)

        # Minimize button
        self.minimize_button = tk.Button(button_frame, text="Minimize", command=self.hide_window, bg="#FFC107", fg="black", font=("Arial", 10))
        self.minimize_button.grid(row=0, column=3, padx=5)

        self.config_listbox = tk.Listbox(master, selectmode=tk.SINGLE, height=10)
        self.config_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.config_listbox.bind("<Double-Button-1>", lambda event: self.open_edit_window())

        self.load_config()

        # Hide the window when closed with "X"
        self.master.protocol("WM_DELETE_WINDOW", self.hide_window)

        # Tray icon
        self.icon = self.create_image()
        self.tray_icon = pystray.Icon("KeyURLSetter", self.icon, "Key URL Setter", menu=pystray.Menu(
            pystray.MenuItem("Show", self.show_window),
            pystray.MenuItem("Exit", self.quit_app)
        ))

        # Start the icon in a separate thread to avoid blocking the interface
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def create_image(self):
        # Create an image for the icon
        image = Image.new('RGB', (64, 64), (255, 255, 255))
        dc = ImageDraw.Draw(image)
        dc.ellipse((16, 16, 48, 48), fill=(0, 128, 255))  # Example of a blue circle
        return image

    def add_key(self):
        key_combination = self.current_key.get()
        url = self.url.get()

        if key_combination and url:
            self.setup_hotkey(key_combination, url)
            self.configurations.append((key_combination, url))
            self.update_listbox()
            self.save_config()
            print(f"Hotkey '{key_combination}' set for URL '{url}'")

    def setup_hotkey(self, key_combination, url):
        self.remove_hotkey_by_key(key_combination)
        keyboard.add_hotkey(key_combination, lambda: self.open_url(url))

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as file:
                lines = file.readlines()
                for line in lines:
                    line = line.strip()
                    if line:
                        parts = line.split(';', 1)
                        if len(parts) == 2:
                            key_combination, url = parts
                            self.setup_hotkey(key_combination, url)
                            self.configurations.append((key_combination, url))
                self.update_listbox()

    def save_config(self):
        with open(CONFIG_FILE, 'w') as file:
            for k, u in self.configurations:
                file.write(f"{k};{u}\n")

    def update_listbox(self):
        self.config_listbox.delete(0, tk.END)
        for key_combination, url in self.configurations:
            self.config_listbox.insert(tk.END, f"{key_combination}: {url}")

    def open_url(self, url):
        print(f"Opening URL: {url}")
        webbrowser.open(url)

    def open_edit_window(self):
        selected_index = self.config_listbox.curselection()
        if not selected_index:
            print("Select an item to edit.")
            return

        edit_window = tk.Toplevel(self.master)
        edit_window.title("Edit Configuration")
        edit_window.configure(bg="#f0f0f0")
        edit_window.geometry("300x200")

        selected_item = self.config_listbox.get(selected_index)
        key_combination, url = selected_item.split(': ', 1)

        new_key_var = tk.StringVar(value=key_combination)
        new_url_var = tk.StringVar(value=url)

        tk.Label(edit_window, text="Key Combination:", bg="#f0f0f0").pack(pady=5)
        key_entry = tk.Entry(edit_window, textvariable=new_key_var, width=25)
        key_entry.pack(pady=5)

        tk.Label(edit_window, text="URL:", bg="#f0f0f0").pack(pady=5)
        url_entry = tk.Entry(edit_window, textvariable=new_url_var, width=25)
        url_entry.pack(pady=5)

        apply_button = tk.Button(edit_window, text="Apply Changes", command=lambda: self.apply_edit(new_key_var.get(), new_url_var.get(), key_combination, edit_window), bg="#2196F3", fg="white")
        apply_button.pack(pady=10)

    def apply_edit(self, new_key_combination, new_url, old_key_combination, edit_window):
        self.remove_hotkey_by_key(old_key_combination)
        index_to_update = next((i for i, (k, u) in enumerate(self.configurations) if k == old_key_combination), None)
        if index_to_update is not None:
            self.configurations[index_to_update] = (new_key_combination, new_url)
        self.setup_hotkey(new_key_combination, new_url)

        self.save_config()
        self.update_listbox()
        
        edit_window.destroy()
        print(f"Configuration updated: '{new_key_combination}' => '{new_url}'")

    def delete_key(self):
        selected_index = self.config_listbox.curselection()
        if not selected_index:
            print("Select an item to delete.")
            return

        selected_item = self.config_listbox.get(selected_index)
        key_combination = selected_item.split(': ', 1)[0]

        self.remove_hotkey_by_key(key_combination)
        self.configurations = [config for config in self.configurations if config[0] != key_combination]
        self.save_config()
        self.update_listbox()
        print(f"Configuration '{key_combination}' deleted.")

    def remove_hotkey_by_key(self, key_combination):
        try:
            keyboard.remove_hotkey(key_combination)
            print(f"Hotkey '{key_combination}' removed.")
        except Exception as e:
            print(f"Error removing hotkey: {e}")

    def hide_window(self):
        self.master.withdraw()  # Hide the window

    def show_window(self, icon, item):
        self.master.deiconify()  # Show the window

    def quit_app(self, icon, item):
        self.tray_icon.stop()  # Stop the tray icon
        self.master.quit()

if __name__ == "__main__":
    root = tk.Tk()
    app = KeyURLSetter(root)
    root.mainloop()