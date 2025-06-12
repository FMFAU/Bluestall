import customtkinter as ctk
import winreg
import subprocess
import os
import shutil
from tkinter import messagebox
import threading
import time
import glob
import win32com.client
import psutil
from PIL import Image, ImageTk

class UninstallerApp:
    def __init__(self):
        self.app = ctk.CTk()
        self.app.title("Bluestall - Advanced Uninstaller Pro")
        self.app.geometry("1200x700")

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.logo_path = os.path.join("Assets", "bluestall_logo.png")
        self.logo_img = None
        if os.path.exists(self.logo_path):
            try:
                pil_logo = Image.open(self.logo_path).resize((96, 96))  
                self.logo_img = ctk.CTkImage(light_image=pil_logo, dark_image=pil_logo, size=(96, 96))
            except:
                self.logo_img = None

        self.loading_frame = ctk.CTkFrame(self.app)
        self.loading_frame.pack(fill="both", expand=True)

        if self.logo_img:
            self.loading_logo_label = ctk.CTkLabel(self.loading_frame, image=self.logo_img, text="")
            self.loading_logo_label.pack(pady=40)

        self.loading_label = ctk.CTkLabel(
            self.loading_frame,
            text="Starting up...",
            font=("Arial", 24, "bold")  
        )
        self.loading_label.pack(pady=20)

        self.loading_progress_bar = ctk.CTkProgressBar(self.loading_frame, width=400, height=20)  
        self.loading_progress_bar.pack(pady=20)
        self.loading_progress_bar.set(0)

        self.tips = [
            "Tip: You can batch uninstall multiple apps at once!",
            "Tip: Use the search bar to quickly find an app.",
            "Tip: Scan for leftovers after uninstall for a cleaner system.",
            "Tip: Switch between dark and light mode in Settings.",
            "Tip: Check the Uninstalled Files tab for saved space info."
        ]
        self.tip_label = ctk.CTkLabel(
            self.loading_frame,
            text=self.tips[0],
            font=("Arial", 16, "italic")
        )
        self.tip_label.pack(pady=10)
        self.current_tip = 0
        self.rotate_tips()

        threading.Thread(target=self.load_installed_apps, daemon=True).start()

    def rotate_tips(self):
        self.current_tip = (self.current_tip + 1) % len(self.tips)
        self.tip_label.configure(text=self.tips[self.current_tip])
        self.app.after(2500, self.rotate_tips)

    def load_uninstalled_apps_data(self):
        """Load uninstalled apps data from a JSON file"""
        import json
        try:
            with open("uninstalled_apps.json", "r") as f:
                self.uninstalled_apps = json.load(f)
        except FileNotFoundError:
            self.uninstalled_apps = []

    def setup_uninstall_tab(self):

        self.search_frame = ctk.CTkFrame(self.tab1)
        self.search_frame.pack(fill="x", padx=10, pady=10)

        self.search_var = ctk.StringVar()
        self.search_entry = ctk.CTkEntry(
            self.search_frame,
            placeholder_text="🔍 Search applications...",
            width=400,
            height=35,
            font=("Arial", 14),
            textvariable=self.search_var
        )
        self.search_entry.pack(side="left", padx=10)
        self.search_var.trace("w", self.filter_apps)

        self.refresh_button = ctk.CTkButton(
            self.search_frame,
            text="🔄 Refresh",
            command=self.load_installed_apps,
            width=100,
            height=35
        )
        self.refresh_button.pack(side="right", padx=10)

        self.apps_frame = ctk.CTkScrollableFrame(self.tab1)
        self.apps_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.status_frame = ctk.CTkFrame(self.tab1)
        self.status_frame.pack(fill="x", padx=10, pady=5)

        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="Ready",
            font=("Arial", 12)
        )
        self.status_label.pack(side="left", padx=10)

        self.progress_bar = ctk.CTkProgressBar(self.status_frame)
        self.progress_bar.pack(fill="x", padx=10, pady=5)
        self.progress_bar.set(0)

    def setup_batch_uninstall_tab(self):

        self.batch_frame = ctk.CTkFrame(self.tab2)
        self.batch_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.batch_label = ctk.CTkLabel(
            self.batch_frame,
            text="Select multiple applications to uninstall:",
            font=("Arial", 16, "bold")
        )
        self.batch_label.pack(pady=10)

        self.batch_apps_frame = ctk.CTkScrollableFrame(self.batch_frame)
        self.batch_apps_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.batch_checkboxes = {}

        self.batch_uninstall_button = ctk.CTkButton(
            self.batch_frame,
            text="Uninstall Selected",
            command=self.batch_uninstall,
            width=200,
            height=40
        )
        self.batch_uninstall_button.pack(pady=10)

    def setup_settings_tab(self):

        self.settings_frame = ctk.CTkFrame(self.tab3)
        self.settings_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.settings_label = ctk.CTkLabel(
            self.settings_frame,
            text="Settings",
            font=("Arial", 16, "bold")
        )
        self.settings_label.pack(pady=10)

        self.auto_scan_var = ctk.BooleanVar(value=False)
        self.auto_scan_checkbox = ctk.CTkCheckBox(
            self.settings_frame,
            text="Auto-scan for leftovers after uninstall",
            variable=self.auto_scan_var
        )
        self.auto_scan_checkbox.pack(pady=5)

        self.theme_label = ctk.CTkLabel(
            self.settings_frame,
            text="Select Theme:",
            font=("Arial", 12)
        )
        self.theme_label.pack(pady=5)

        self.theme_var = ctk.StringVar(value="dark")
        self.theme_dark_radio = ctk.CTkRadioButton(
            self.settings_frame,
            text="Dark",
            variable=self.theme_var,
            value="dark",
            command=self.change_theme
        )
        self.theme_dark_radio.pack(pady=2)

        self.theme_light_radio = ctk.CTkRadioButton(
            self.settings_frame,
            text="Light",
            variable=self.theme_var,
            value="light",
            command=self.change_theme
        )
        self.theme_light_radio.pack(pady=2)

        self.confirm_uninstall_var = ctk.BooleanVar(value=True)
        self.confirm_uninstall_checkbox = ctk.CTkCheckBox(
            self.settings_frame,
            text="Confirm before uninstalling an app",
            variable=self.confirm_uninstall_var
        )
        self.confirm_uninstall_checkbox.pack(pady=5)

        self.language_label = ctk.CTkLabel(
            self.settings_frame,
            text="Language:",
            font=("Arial", 12)
        )
        self.language_label.pack(pady=5)

        self.language_var = ctk.StringVar(value="English")
        self.language_option = ctk.CTkOptionMenu(
            self.settings_frame,
            variable=self.language_var,
            values=["English", "Spanish", "French", "German"]
        )
        self.language_option.pack(pady=2)

    def change_theme(self):
        """Change the application theme"""
        ctk.set_appearance_mode(self.theme_var.get())

    def batch_uninstall(self):
        selected_apps = [app for app in self.apps if self.batch_checkboxes[app["name"]].get()]
        if not selected_apps:
            messagebox.showinfo("Batch Uninstall", "No applications selected.")
            return
        if messagebox.askyesno("Batch Uninstall", f"Are you sure you want to uninstall {len(selected_apps)} applications?"):
            for app in selected_apps:
                self.uninstall_app(app)

    def setup_uninstalled_files_tab(self):

        self.uninstalled_frame = ctk.CTkFrame(self.tab4)
        self.uninstalled_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.uninstalled_label = ctk.CTkLabel(
            self.uninstalled_frame,
            text="Uninstalled Applications",
            font=("Arial", 16, "bold")
        )
        self.uninstalled_label.pack(pady=10)

        self.uninstalled_apps_frame = ctk.CTkScrollableFrame(self.uninstalled_frame)
        self.uninstalled_apps_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.update_uninstalled_apps_list()

    def update_uninstalled_apps_list(self):

        for widget in self.uninstalled_apps_frame.winfo_children():
            widget.destroy()

        for app in self.uninstalled_apps:
            app_frame = ctk.CTkFrame(self.uninstalled_apps_frame)
            app_frame.pack(fill="x", padx=5, pady=2)

            info_frame = ctk.CTkFrame(app_frame)
            info_frame.pack(side="left", fill="x", expand=True, padx=10, pady=5)

            name_label = ctk.CTkLabel(
                info_frame,
                text=app["name"],
                font=("Arial", 14, "bold")
            )
            name_label.pack(anchor="w")

            storage_label = ctk.CTkLabel(
                info_frame,
                text=f"Storage Saved: {app['storage_saved']}",
                font=("Arial", 12),
                text_color="gray"
            )
            storage_label.pack(anchor="w")

    def build_main_ui(self):

        self.loading_frame.pack_forget()

        self.main_frame = ctk.CTkFrame(self.app)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        self.header_frame = ctk.CTkFrame(self.main_frame)
        self.header_frame.pack(fill="x", padx=10, pady=10)
        if self.logo_img:
            self.logo_label = ctk.CTkLabel(self.header_frame, image=self.logo_img, text="")
            self.logo_label.pack(side="left", padx=(10, 10))
        self.title_label = ctk.CTkLabel(
            self.header_frame,
            text="Bluestall",
            font=("Arial", 24, "bold")
        )
        self.title_label.pack(side="left", padx=10)
        self.tabview = ctk.CTkTabview(self.main_frame)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)
        self.tab1 = self.tabview.add("Uninstall")
        self.tab2 = self.tabview.add("Batch Uninstall")
        self.tab3 = self.tabview.add("Settings")
        self.tab4 = self.tabview.add("Uninstalled Files")
        self.app_buttons = []
        self.uninstalled_apps = []
        self.load_uninstalled_apps_data()
        self.setup_uninstall_tab()
        self.setup_batch_uninstall_tab()
        self.setup_settings_tab()
        self.setup_uninstalled_files_tab()
        self.update_apps_list()
        self.update_batch_apps_list()

    def load_installed_apps(self):
        """Load all installed applications from Windows registry"""
        self.loading_label.configure(text="Starting up...")
        self.loading_progress_bar.set(0.1)
        time.sleep(0.5)

        self.loading_label.configure(text="Launching core...")
        self.loading_progress_bar.set(0.2)
        time.sleep(0.5)

        self.loading_label.configure(text="Loading applications...")
        self.loading_progress_bar.set(0.3)
        self.apps = []

        registry_paths = [
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
            r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"
        ]

        for path in registry_paths:
            try:
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path) as key:
                    for i in range(winreg.QueryInfoKey(key)[0]):
                        try:
                            subkey_name = winreg.EnumKey(key, i)
                            with winreg.OpenKey(key, subkey_name) as subkey:
                                try:
                                    name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                                    uninstall_string = winreg.QueryValueEx(subkey, "UninstallString")[0]
                                    install_location = winreg.QueryValueEx(subkey, "InstallLocation")[0]
                                    publisher = winreg.QueryValueEx(subkey, "Publisher")[0] if "Publisher" in [winreg.EnumValue(subkey, j)[0] for j in range(winreg.QueryInfoKey(subkey)[1])] else "Unknown"
                                    version = winreg.QueryValueEx(subkey, "DisplayVersion")[0] if "DisplayVersion" in [winreg.EnumValue(subkey, j)[0] for j in range(winreg.QueryInfoKey(subkey)[1])] else "Unknown"

                                    self.apps.append({
                                        "name": name,
                                        "uninstall_string": uninstall_string,
                                        "install_location": install_location,
                                        "publisher": publisher,
                                        "version": version
                                    })
                                except:
                                    continue
                        except:
                            continue
            except:
                continue

        self.loading_label.configure(text=f"Found {len(self.apps)} applications")
        self.loading_progress_bar.set(1.0)
        time.sleep(0.5)

        self.app.after(0, self.build_main_ui)

    def update_batch_apps_list(self):

        for widget in self.batch_apps_frame.winfo_children():
            widget.destroy()
        self.batch_checkboxes.clear()

        for app in self.apps:
            app_frame = ctk.CTkFrame(self.batch_apps_frame)
            app_frame.pack(fill="x", padx=5, pady=2)

            info_frame = ctk.CTkFrame(app_frame)
            info_frame.pack(side="left", fill="x", expand=True, padx=10, pady=5)

            app_icon = self.get_app_icon(app)
            if app_icon:
                icon_label = ctk.CTkLabel(info_frame, image=app_icon, text="")
                icon_label.pack(side="left", padx=(0, 10))

            name_label = ctk.CTkLabel(
                info_frame,
                text=app["name"],
                font=("Arial", 14, "bold")
            )
            name_label.pack(anchor="w")

            details_label = ctk.CTkLabel(
                info_frame,
                text=f"Publisher: {app['publisher']} | Version: {app['version']}",
                font=("Arial", 12),
                text_color="gray"
            )
            details_label.pack(anchor="w")

            var = ctk.BooleanVar()
            checkbox = ctk.CTkCheckBox(app_frame, text="", variable=var)
            checkbox.pack(side="right", padx=10)
            self.batch_checkboxes[app["name"]] = var

    def get_app_icon(self, app):
        """Try to get the app icon from the install location or use a placeholder."""

        exe_path = None
        if app.get("install_location") and os.path.exists(app["install_location"]):
            for file in os.listdir(app["install_location"]):
                if file.lower().endswith(".exe"):
                    exe_path = os.path.join(app["install_location"], file)
                    break

        icon_path = os.path.join("Assets", "app_placeholder.png")
        if exe_path and os.path.exists(exe_path):

            pass
        if os.path.exists(icon_path):
            try:
                pil_icon = Image.open(icon_path).resize((32, 32))
                return ctk.CTkImage(light_image=pil_icon, dark_image=pil_icon, size=(32, 32))
            except:
                return None
        return None

    def update_apps_list(self):
        """Update the applications list in the UI"""

        for widget in self.apps_frame.winfo_children():
            widget.destroy()

        for app in self.apps:
            app_frame = ctk.CTkFrame(self.apps_frame)
            app_frame.pack(fill="x", padx=5, pady=2)

            info_frame = ctk.CTkFrame(app_frame)
            info_frame.pack(side="left", fill="x", expand=True, padx=10, pady=5)

            name_label = ctk.CTkLabel(
                info_frame,
                text=app["name"],
                font=("Arial", 14, "bold")
            )
            name_label.pack(anchor="w")

            storage_used = self.calculate_storage_used(app)
            storage_label = ctk.CTkLabel(
                info_frame,
                text=f"Storage Used: {storage_used / (1024 * 1024):.2f} MB" if storage_used > 0 else "Storage Used: ?",
                font=("Arial", 12),
                text_color="gray"
            )
            storage_label.pack(anchor="w")

            uninstall_button = ctk.CTkButton(
                app_frame,
                text="Uninstall",
                command=lambda a=app: self.uninstall_app(a)
            )
            uninstall_button.pack(side="right", padx=10, pady=5)

    def filter_apps(self, *args):
        """Filter applications based on search text"""
        search_text = self.search_var.get().lower()
        filtered_apps = [app for app in self.apps if search_text in app["name"].lower()]

        for button in self.app_buttons:
            button.destroy()
        self.app_buttons.clear()

        for app in filtered_apps:
            app_frame = ctk.CTkFrame(self.apps_frame)
            app_frame.pack(fill="x", padx=5, pady=2)

            info_frame = ctk.CTkFrame(app_frame)
            info_frame.pack(side="left", fill="x", expand=True, padx=10, pady=5)

            app_icon = self.get_app_icon(app)
            if app_icon:
                icon_label = ctk.CTkLabel(info_frame, image=app_icon, text="")
                icon_label.pack(side="left", padx=(0, 10))

            name_label = ctk.CTkLabel(
                info_frame,
                text=app["name"],
                font=("Arial", 14, "bold")
            )
            name_label.pack(anchor="w")

            details_label = ctk.CTkLabel(
                info_frame,
                text=f"Publisher: {app['publisher']} | Version: {app['version']}",
                font=("Arial", 12),
                text_color="gray"
            )
            details_label.pack(anchor="w")

            buttons_frame = ctk.CTkFrame(app_frame)
            buttons_frame.pack(side="right", padx=10, pady=5)

            scan_button = ctk.CTkButton(
                buttons_frame,
                text="🔍 Scan",
                command=lambda a=app: self.scan_leftovers(a),
                width=100
            )
            scan_button.pack(side="left", padx=5)

            uninstall_button = ctk.CTkButton(
                buttons_frame,
                text="🗑️ Uninstall",
                command=lambda a=app: self.uninstall_app(a),
                width=100,
                fg_color="#FF5555",
                hover_color="#FF3333"
            )
            uninstall_button.pack(side="left", padx=5)

            self.app_buttons.append(app_frame)

    def scan_leftovers(self, app):
        """Scan for leftover files and registry entries"""
        self.status_label.configure(text=f"Scanning for leftovers of {app['name']}...")
        self.progress_bar.set(0.2)

        threading.Thread(target=self._perform_deep_scan, args=(app,), daemon=True).start()

    def _perform_deep_scan(self, app):
        """Perform a deep scan for leftover files and registry entries"""
        leftovers = []

        program_files_paths = [
            os.environ.get('ProgramFiles', 'C:\\Program Files'),
            os.environ.get('ProgramFiles(x86)', 'C:\\Program Files (x86)'),
            os.environ.get('LOCALAPPDATA', 'C:\\Users\\%USERNAME%\\AppData\\Local'),
            os.environ.get('APPDATA', 'C:\\Users\\%USERNAME%\\AppData\\Roaming')
        ]

        app_name_clean = app["name"].lower().replace(" ", "")
        for path in program_files_paths:
            if os.path.exists(path):
                for root, dirs, files in os.walk(path):
                    for item in dirs + files:
                        if app_name_clean in item.lower():
                            leftovers.append(os.path.join(root, item))

        registry_paths = [
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
            r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"
        ]

        for path in registry_paths:
            try:
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path) as key:
                    for i in range(winreg.QueryInfoKey(key)[0]):
                        try:
                            subkey_name = winreg.EnumKey(key, i)
                            with winreg.OpenKey(key, subkey_name) as subkey:
                                try:
                                    name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                                    if app_name_clean in name.lower():
                                        leftovers.append(f"Registry: {path}\\{subkey_name}")
                                except:
                                    continue
                        except:
                            continue
            except:
                continue

        self.progress_bar.set(1.0)
        self.status_label.configure(text=f"Found {len(leftovers)} leftover items for {app['name']}")

        if leftovers:
            messagebox.showinfo("Leftovers Found", f"Found {len(leftovers)} leftover items for {app['name']}:\n" + "\n".join(leftovers))
        else:
            messagebox.showinfo("No Leftovers", f"No leftover items found for {app['name']}.")

        time.sleep(2)
        self.progress_bar.set(0)

    def calculate_storage_used(self, app):
        """Calculate the storage used by an app."""
        storage_used = 0
        if app.get("install_location") and os.path.exists(app["install_location"]):
            for root, dirs, files in os.walk(app["install_location"]):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        storage_used += os.path.getsize(file_path)
                    except:
                        pass
        return storage_used

    def uninstall_app(self, app):
        """Uninstall the selected application"""
        if messagebox.askyesno("Confirm Uninstall", f"Are you sure you want to uninstall {app['name']}?"):
            self.status_label.configure(text=f"Uninstalling {app['name']}...")
            self.progress_bar.set(0.2)

            storage_used = self.calculate_storage_used(app)

            threading.Thread(target=self._perform_uninstall, args=(app, storage_used), daemon=True).start()

    def _perform_uninstall(self, app, storage_used):
        """Perform the actual uninstallation process"""
        try:

            subprocess.run(app["uninstall_string"], shell=True)
            self.progress_bar.set(0.5)

            self._cleanup_leftovers(app)

            self.progress_bar.set(1.0)
            self.status_label.configure(text=f"Successfully uninstalled {app['name']}")

            self.uninstalled_apps.append({
                "name": app["name"],
                "storage_saved": f"{storage_used / (1024 * 1024):.2f} MB"
            })
            self.update_uninstalled_apps_list()

            self.save_uninstalled_apps_data()

            self.apps.remove(app)
            self.update_apps_list()
            self.update_batch_apps_list()

            scan = messagebox.askyesno(
                "Scan for Leftovers",
                f"Do you wish to scan for leftovers after uninstalling {app['name']}?"
            )
            if scan:
                self.scan_leftovers(app)

            time.sleep(2)
            self.progress_bar.set(0)

        except Exception as e:
            self.status_label.configure(text=f"Error uninstalling {app['name']}: {str(e)}")
            self.progress_bar.set(0)

    def _cleanup_leftovers(self, app):
        """Clean up leftover files and registry entries"""
        try:

            if os.path.exists(app["install_location"]):
                shutil.rmtree(app["install_location"], ignore_errors=True)

            program_files_paths = [
                os.environ.get('ProgramFiles', 'C:\\Program Files'),
                os.environ.get('ProgramFiles(x86)', 'C:\\Program Files (x86)'),
                os.environ.get('LOCALAPPDATA', 'C:\\Users\\%USERNAME%\\AppData\\Local'),
                os.environ.get('APPDATA', 'C:\\Users\\%USERNAME%\\AppData\\Roaming')
            ]

            app_name_clean = app["name"].lower().replace(" ", "")
            for path in program_files_paths:
                if os.path.exists(path):
                    for root, dirs, files in os.walk(path):
                        for item in dirs + files:
                            if app_name_clean in item.lower():
                                try:
                                    item_path = os.path.join(root, item)
                                    if os.path.isfile(item_path):
                                        os.remove(item_path)
                                    elif os.path.isdir(item_path):
                                        shutil.rmtree(item_path, ignore_errors=True)
                                except:
                                    continue

        except Exception as e:
            print(f"Error cleaning up leftovers: {str(e)}")

    def save_uninstalled_apps_data(self):
        """Save uninstalled apps data to a JSON file"""
        import json
        with open("uninstalled_apps.json", "w") as f:
            json.dump(self.uninstalled_apps, f, indent=4)

    def run(self):
        """Start the application"""
        self.app.mainloop()

if __name__ == "__main__":
    app = UninstallerApp()
    app.run()
