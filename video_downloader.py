import tkinter as tk
from tkinter import filedialog, messagebox
import yt_dlp
import os
import threading
import webbrowser
import platform
import subprocess


class YTDLPLogger:
    def __init__(self, log_func):
        self.log_func = log_func

    def debug(self, msg):
        self.log_func(f"DEBUG: {msg}")

    def warning(self, msg):
        self.log_func(f"WARNING: {msg}")

    def error(self, msg):
        self.log_func(f"ERROR: {msg}")


class VideoDownloader:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Video Downloader")

        # Menu Bar
        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)

        # File Menu
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.file_menu.add_command(label="Close", command=self.root.destroy)
        self.menu_bar.add_cascade(label="File", menu=self.file_menu)

        # Help Menu
        self.help_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.help_menu.add_command(label="About", command=self.show_about)
        self.help_menu.add_command(label="Update", command=self.open_github_update)
        self.menu_bar.add_cascade(label="Help", menu=self.help_menu)

        # URL Entry
        self.url_label = tk.Label(self.root, text="Video URL:")
        self.url_label.pack()
        self.url_entry = tk.Entry(self.root, width=50)
        self.url_entry.pack()

        # Format Selection
        self.format_label = tk.Label(self.root, text="Format:")
        self.format_label.pack()
        self.format_var = tk.StringVar()
        self.format_var.set("mp4")
        self.format_option = tk.OptionMenu(self.root, self.format_var, "mp4", "webm")
        self.format_option.pack()

        # Quality Selection
        self.quality_label = tk.Label(self.root, text="Quality:")
        self.quality_label.pack()
        self.quality_var = tk.StringVar()
        self.quality_var.set("1080p")
        self.quality_option = tk.OptionMenu(self.root, self.quality_var, "1080p", "720p", "480p", "360p")
        self.quality_option.pack()

        # Output Directory Selection
        self.output_dir_label = tk.Label(self.root, text="Output Directory:")
        self.output_dir_label.pack()
        self.output_dir_entry = tk.Entry(self.root, width=50)
        self.output_dir_entry.pack()
        self.output_dir_button = tk.Button(self.root, text="Browse", command=self.browse_output_dir)
        self.output_dir_button.pack()

        # Filename Template
        self.filename_template_label = tk.Label(self.root, text="Filename Template:")
        self.filename_template_label.pack()
        self.filename_template_entry = tk.Entry(self.root, width=50)
        self.filename_template_entry.insert(0, "%(title)s.%(ext)s")
        self.filename_template_entry.pack()

        # Download Button
        self.download_button = tk.Button(self.root, text="Download", command=self.download_video)
        self.download_button.pack()

        # Log Frame
        self.log_frame = tk.Text(self.root, width=50, height=10)
        self.log_frame.pack()

        # Open File Location Button
        self.open_file_location_button = tk.Button(self.root, text="Open File Location", command=self.open_file_location)
        self.open_file_location_button.pack()

    def browse_output_dir(self):
        output_dir = filedialog.askdirectory()
        if output_dir:
            self.output_dir_entry.delete(0, tk.END)
            self.output_dir_entry.insert(0, output_dir)

    def download_video(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a video URL.")
            return

        format = self.format_var.get()
        # Quality selection not used in yt-dlp options yet.
        output_dir = self.output_dir_entry.get()
        filename_template = self.filename_template_entry.get()

        if not output_dir or not os.path.isdir(output_dir):
            messagebox.showerror("Error", "Please select a valid output directory.")
            return

        ydl_opts = {
            'format': f"bestvideo[ext={format}]+bestaudio[ext={format}]/best[ext={format}]",
            'outtmpl': os.path.join(output_dir, filename_template),
            'logger': YTDLPLogger(self.log),
            'progress_hooks': [self.progress_hook]
        }

        threading.Thread(target=self.download_video_thread, args=(url, ydl_opts), daemon=True).start()

    def download_video_thread(self, url, ydl_opts):
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            self.log("Download completed successfully!")
        except Exception as e:
            self.log(f"Error: {e}")

    def progress_hook(self, d):
        if d['status'] == 'downloading':
            downloaded = d.get('downloaded_bytes', 0)
            total = d.get('total_bytes', 0) or d.get('total_bytes_estimate', 0)
            if total > 0:
                percent = downloaded / total * 100
                self.log(f"Downloading... {percent:.1f}%")
            else:
                self.log("Downloading...")
        elif d['status'] == 'finished':
            self.log("Download finished, processing...")

    def log(self, message):
        self.root.after(0, lambda: self._append_log(message))

    def _append_log(self, message):
        self.log_frame.insert(tk.END, message + "\n")
        self.log_frame.see(tk.END)

    def open_file_location(self):
        output_dir = self.output_dir_entry.get()
        if not output_dir or not os.path.isdir(output_dir):
            messagebox.showerror("Error", "Invalid output directory.")
            return

        system = platform.system()
        try:
            if system == "Windows":
                os.startfile(output_dir)
            elif system == "Darwin":  # macOS
                subprocess.Popen(["open", output_dir])
            else:  # Linux and others
                subprocess.Popen(["xdg-open", output_dir])
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open directory: {e}")

    def show_about(self):
        about_window = tk.Toplevel(self.root)
        about_window.title("About")
        about_window.geometry("600x400")
        about_window.resizable(width=False, height=False)

        # Frame to hold text and scrollbar
        text_frame = tk.Frame(about_window)
        text_frame.pack(fill="both", expand=True, padx=10, pady=(10, 0))

        # Scrollbar
        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side="right", fill="y")

        # Text widget with scrollbar
        text = tk.Text(
            text_frame,
            wrap="word",
            font=("Arial", 10),
            yscrollcommand=scrollbar.set,
            state="normal",
            height=18,
            width=70
        )
        about_message = (
            "GUI Wrapper Creator: Mike Larios.\n\n"
            "YT-DLP is not created, updated, or maintained by Mike Larios in any way, nor does Mike Larios take any claims to the regards.\n\n"
            "DISCLAIMER:\n"
            "This software application is an independent tool designed to facilitate the downloading of publicly available educational video content "
            "for lawful, non-commercial, and informational use only. This application utilizes yt-dlp, an open-source command-line utility, in a modular "
            "and air-gapped capacity. The yt-dlp executable is not bundled, embedded, or modified by this application. Users must obtain yt-dlp separately "
            "in accordance with its licensing terms and ensure that its use complies with all local, national, and international laws. The developer of this "
            "application does not host, store, redistribute, or encourage the unauthorized downloading of copyrighted material. "
            "The responsibility for how this tool is used lies solely with the end user. By using this software, the user agrees to adhere to the applicable "
            "copyright laws and the Terms of Service of any media platform involved. The developer disclaims all liability for any misuse, infringement, or unlawful "
            "activity resulting from the use of this application.\n\nFor educational purposes only."
        )
        text.insert("1.0", about_message)
        text.configure(state="disabled")
        text.pack(side="left", fill="both", expand=True)

        scrollbar.config(command=text.yview)

        # Clickable URL Label always visible below text
        url_label = tk.Label(
            about_window,
            text="Visit thelarios.com",
            foreground="blue",
            cursor="hand2",
            font=("Arial", 12, "underline"),
            pady=10
        )
        url_label.pack()

        def open_url(event):
            webbrowser.open_new_tab("https://www.thelarios.com")

        url_label.bind("<Button-1>", open_url)

    def open_github_update(self):
        github_url = "https://github.com/someguru/video_downloader/releases/latest"
        webbrowser.open_new_tab(github_url)

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = VideoDownloader()
    app.run()
