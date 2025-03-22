import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pygame import mixer
import os
import math
import random
import tempfile
from PIL import Image, ImageTk

# Constants
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(BASE_DIR, "proj_img")

class UltimateMediaPlayer:
    def __init__(self, root):
        self.root = root
        self.setup_main_window()
        self.initialize_mixer()
        self.load_images()
        self.setup_styles()
        self.create_ui()
        self.visualization_active = False
        self.current_time = 0
        self.paused = False
        self.current_song = ""

    def setup_main_window(self):
        self.root.title('Ultimate Music Player')
        self.root.geometry("1200x800")
        self.root.minsize(1000, 700)
        self.root.configure(bg="#0a0a0a")

    def setup_styles(self):
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Configure custom styles
        self.style.configure('TFrame', background='#0a0a0a')
        self.style.configure('TLabel', background='#0a0a0a', foreground='white')
        self.style.configure('Control.TButton', background='#1a1a1a', foreground='white', 
                           borderwidth=0, font=('Helvetica', 10))
        self.style.map('Control.TButton', background=[('active', '#2a2a2a')])
        self.style.configure('Playlist.TListbox', background='#1a1a1a', foreground='white',
                            selectbackground='#3a3a3a', font=('Helvetica', 12))
        self.style.configure('Modern.Horizontal.TScale', troughcolor='#1a1a1a', sliderthickness=10)

    def initialize_mixer(self):
        mixer.init()

    def load_images(self):
        self.images = {
            'play': self.load_image('play_button.png', (60, 60)),
            'pause': self.load_image('pause_button.png', (60, 60)),
            'stop': self.load_image('stop_button.png', (60, 60)),
            'logo': self.load_image('logo.png', (300, 300))
        }

    def load_image(self, filename, size=None):
        try:
            img_path = os.path.join(IMG_DIR, filename)
            img = Image.open(img_path)
            if size:
                img = img.resize(size, Image.Resampling.LANCZOS)
            return ImageTk.PhotoImage(img)
        except Exception as e:
            messagebox.showwarning("Missing Image", f"Image {filename} not found!")
            return None

    def create_ui(self):
        # Main container
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Centered Logo
        self.logo_label = ttk.Label(self.main_frame, image=self.images['logo'])
        self.logo_label.pack(pady=50)

        # Control Panel
        self.create_controls()
        
        # Playlist
        self.create_playlist()
        
        # Visualizer
        self.create_visualizer()
        
        # Status Bar
        self.create_status_bar()

    def create_controls(self):
        controls_frame = ttk.Frame(self.main_frame)
        controls_frame.pack(fill=tk.X, pady=20)

        # Playback buttons
        btn_frame = ttk.Frame(controls_frame)
        btn_frame.pack(side=tk.LEFT, padx=40)
        
        ttk.Button(btn_frame, image=self.images['play'], command=self.play_music, style='Control.TButton').pack(side=tk.LEFT, padx=15)
        ttk.Button(btn_frame, image=self.images['pause'], command=self.toggle_pause, style='Control.TButton').pack(side=tk.LEFT, padx=15)
        ttk.Button(btn_frame, image=self.images['stop'], command=self.stop_music, style='Control.TButton').pack(side=tk.LEFT, padx=15)

        # Add/Remove buttons
        list_controls = ttk.Frame(controls_frame)
        list_controls.pack(side=tk.LEFT, padx=40)
        ttk.Button(list_controls, text="Add Music", command=self.add_music, style='Control.TButton').pack(side=tk.LEFT, padx=10)
        ttk.Button(list_controls, text="Remove", command=self.remove_song, style='Control.TButton').pack(side=tk.LEFT, padx=10)

        # Volume control
        volume_frame = ttk.Frame(controls_frame)
        volume_frame.pack(side=tk.RIGHT, padx=40)
        ttk.Label(volume_frame, text="Volume:").pack(side=tk.LEFT)
        self.volume = ttk.Scale(volume_frame, from_=0, to=100, command=self.set_volume, style='Modern.Horizontal.TScale')
        self.volume.set(70)
        self.volume.pack(side=tk.LEFT, padx=10)

    def create_playlist(self):
        playlist_frame = ttk.Frame(self.main_frame)
        playlist_frame.pack(fill=tk.BOTH, expand=True, pady=20)

        self.playlist = tk.Listbox(playlist_frame, selectmode=tk.SINGLE, font=('Helvetica', 12), 
                                 bg='#1a1a1a', fg='white', selectbackground='#3a3a3a')
        scroll = ttk.Scrollbar(playlist_frame, command=self.playlist.yview)
        self.playlist.config(yscrollcommand=scroll.set)
        
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.playlist.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)

    def create_visualizer(self):
        self.vis_frame = ttk.Frame(self.main_frame)
        self.vis_canvas = tk.Canvas(self.vis_frame, bg='#0a0a0a', highlightthickness=0)
        self.vis_canvas.pack(fill=tk.BOTH, expand=True)
        self.vis_frame.pack(fill=tk.BOTH, expand=True)
        self.bars = []
        self.create_spectrum_visualizer()

    def create_spectrum_visualizer(self):
        width = 800
        height = 300
        center_x = width // 2
        center_y = height // 2
        radius = 120
        num_bars = 36
        
        for i in range(num_bars):
            angle = math.radians(i * (360 / num_bars))
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)
            bar = self.vis_canvas.create_line(
                x, y, 
                x + (radius * 0.3 * math.cos(angle)), 
                y + (radius * 0.3 * math.sin(angle)), 
                width=4, 
                fill=self.generate_gradient_color(i/num_bars)
            )
            self.bars.append(bar)

    def generate_gradient_color(self, position):
        r = int(255 * (1 - position))
        g = int(255 * position)
        b = 128
        return f'#{r:02x}{g:02x}{b:02x}'

    def update_visualization(self):
        if mixer.music.get_busy() and self.visualization_active:
            for i, bar in enumerate(self.bars):
                angle = math.radians(i * (360 / len(self.bars)))
                scale = 1 + 0.5 * math.sin(math.radians(i * 10 + self.current_time * 5))
                
                coords = self.vis_canvas.coords(bar)
                dx = (coords[2] - coords[0]) * scale
                dy = (coords[3] - coords[1]) * scale
                
                self.vis_canvas.coords(bar, 
                    coords[0], coords[1],
                    coords[0] + dx,
                    coords[1] + dy
                )
                self.vis_canvas.itemconfig(bar, fill=self.generate_gradient_color((i + self.current_time) % 1))
            
            self.current_time += 0.1
            self.root.after(50, self.update_visualization)

    def create_status_bar(self):
        status_frame = ttk.Frame(self.main_frame)
        status_frame.pack(fill=tk.X, pady=10)

        self.progress = ttk.Progressbar(status_frame, orient=tk.HORIZONTAL, 
                                      mode='determinate', length=800)
        self.progress.pack(fill=tk.X)
        self.time_label = ttk.Label(status_frame, text="00:00 / 00:00")
        self.time_label.pack()

    # Core functionality methods
    def add_music(self):
        paths = filedialog.askopenfilenames(
            filetypes=[
                ("Audio Files", "*.mp3 *.wav *.m4a *.opus *.mp4 *.aac *.flac"),
                ("All Files", "*.*")
            ]
        )
        if paths:
            for path in paths:
                self.playlist.insert(tk.END, path)

    def remove_song(self):
        selected = self.playlist.curselection()
        if selected:
            self.playlist.delete(selected[0])

    def play_music(self):
        selected = self.playlist.curselection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a song to play!")
            return
            
        self.current_song = self.playlist.get(selected[0])
        try:
            if self.current_song.lower().endswith(('.wav', '.mp3')):
                mixer.music.load(self.current_song)
            else:
                from pydub import AudioSegment
                audio = AudioSegment.from_file(self.current_song)
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
                    audio.export(tmp.name, format='wav')
                    mixer.music.load(tmp.name)
            
            mixer.music.play()
            self.logo_label.pack_forget()
            self.visualization_active = True
            self.update_visualization()
            self.update_progress()
        except Exception as e:
            messagebox.showerror("Error", f"Could not play file: {e}")

    def toggle_pause(self):
        if self.paused:
            mixer.music.unpause()
            self.paused = False
            self.visualization_active = True
            self.update_visualization()
        else:
            mixer.music.pause()
            self.paused = True
            self.visualization_active = False

    def stop_music(self):
        mixer.music.stop()
        self.progress['value'] = 0
        self.time_label.config(text="00:00 / 00:00")
        self.logo_label.pack(pady=50)
        self.visualization_active = False

    def set_volume(self, val):
        volume = float(val) / 100
        mixer.music.set_volume(volume)

    def update_progress(self):
        if mixer.music.get_busy():
            current_pos = mixer.music.get_pos() / 1000  # Get current position in seconds
            mins, secs = divmod(current_pos, 60)
            self.time_label.config(text=f"{int(mins):02}:{int(secs):02}")
            self.progress['value'] = current_pos
            self.root.after(1000, self.update_progress)

    def on_close(self):
        mixer.music.stop()
        mixer.quit()
        self.root.destroy()

if __name__ == "__main__":
    if not os.path.exists(IMG_DIR):
        os.makedirs(IMG_DIR, exist_ok=True)
        messagebox.showwarning("Missing Images", f"Place images in: {IMG_DIR}")
    
    root = tk.Tk()
    app = UltimateMediaPlayer(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()