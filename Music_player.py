import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pygame
from pygame import mixer
import os
import math
import random
import tempfile
from PIL import Image, ImageTk
import time # ### ADDED: For checking song end
import json # ### ADDED: For saving/loading playlists
from mutagen.easyid3 import EasyID3 # ### ADDED: For MP3 metadata
from mutagen.mp4 import MP4 # ### ADDED: For M4A/MP4 metadata
from mutagen.flac import FLAC # ### ADDED: For FLAC metadata
from mutagen.oggopus import OggOpus # ### ADDED: For Opus metadata
from mutagen import File as MutagenFile # ### ADDED: Generic metadata loader
from pydub import AudioSegment # ### ADDED: Import here
from pydub.exceptions import CouldntDecodeError # ### ADDED: Specific pydub error

# Constants
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(BASE_DIR, "proj_img")
# ### ADDED: Define supported file types tuple for reuse
SUPPORTED_FILETYPES = (
    ("Audio Files", "*.mp3 *.wav *.m4a *.opus *.mp4 *.aac *.flac *.ogg"),
    ("MP3 Files", "*.mp3"),
    ("WAV Files", "*.wav"),
    ("M4A Files", "*.m4a"),
    ("MP4 Audio", "*.mp4"),
    ("FLAC Files", "*.flac"),
    ("Opus Files", "*.opus"),
    ("OGG Files", "*.ogg"),
    ("AAC Files", "*.aac"),
    ("All Files", "*.*")
)
# ### ADDED: Playlist file type
PLAYLIST_FILETYPE = (("Playlist Files", "*.ump"), ("All Files", "*.*"))

# ### ADDED: Repeat states
REPEAT_OFF = 0
REPEAT_ONE = 1
REPEAT_ALL = 2

# ### ADDED: Theme Definitions ###
THEMES = {
    "Dark": {
        "bg": "#0a0a0a",
        "fg": "white",
        "frame_bg": "#0a0a0a",
        "control_bg": "#1a1a1a",
        "control_active_bg": "#2a2a2a",
        "listbox_bg": "#1a1a1a",
        "listbox_fg": "white",
        "listbox_select_bg": "#0078D7", # Example selection color
        "listbox_select_fg": "white",
        "scale_trough": "#1a1a1a",
        "progress_trough": "#1a1a1a",
        "progress_bar": "#3a3a3a",
        "toggle_selected_bg": "#4a4a4a",
        "toggle_selected_fg": "#00ff00",
    },
    "Light": {
        "bg": "#f0f0f0",
        "fg": "black",
        "frame_bg": "#f0f0f0",
        "control_bg": "#e1e1e1",
        "control_active_bg": "#cccccc",
        "listbox_bg": "#ffffff",
        "listbox_fg": "black",
        "listbox_select_bg": "#0078D7",
        "listbox_select_fg": "white",
        "scale_trough": "#d3d3d3",
        "progress_trough": "#d3d3d3",
        "progress_bar": "#a0a0a0",
        "toggle_selected_bg": "#b0b0b0",
        "toggle_selected_fg": "#006400", # Dark green
    },
    "Blue": {
        "bg": "#01081a",
        "fg": "#c0c0ff",
        "frame_bg": "#01081a",
        "control_bg": "#0b1a40",
        "control_active_bg": "#1a2c5a",
        "listbox_bg": "#051029",
        "listbox_fg": "#c0c0ff",
        "listbox_select_bg": "#2a52be", # Royal Blue like
        "listbox_select_fg": "white",
        "scale_trough": "#0b1a40",
        "progress_trough": "#0b1a40",
        "progress_bar": "#1a2c5a",
        "toggle_selected_bg": "#1a2c5a",
        "toggle_selected_fg": "#90ee90", # Light Green
    }
    # Add more themes here if desired
}
DEFAULT_THEME = "Dark" # Or your preferred default
CONFIG_FILE = "player_config.json" # File to save settings
# ### END THEME Definitions ###

class UltimateMediaPlayer:
    def __init__(self, root):
        self.root = root
        self.setup_main_window()
        self.initialize_mixer()
        self.load_images()
        # ### ADDED: Theme state ###
        self.current_theme = DEFAULT_THEME
        self.load_config() # Load theme preference before setting up UI
        self.setup_styles()

        # ### MODIFICATION: Initialize state variables earlier and add new ones
        self.playlist_paths = [] # Store full paths
        self.current_index = -1
        self.paused = False
        self.playing = False # Track if music is actively playing (not just loaded)
        self.current_song_path = ""
        self.song_length_seconds = 0
        # ### MODIFICATION: Change how temp file is tracked
        # self.temp_wav_file = None # Old way
        self.temp_wav_file_path = None # Store path of temp file for cleanup
        self.shuffle_on = False
        self.repeat_mode = REPEAT_OFF # 0: off, 1: repeat one, 2: repeat all
        self.shuffled_indices = []
        self.after_id_progress = None # Store ID for progress update loop
        self.after_id_visualizer = None # Store ID for visualizer update loop
        self.visualization_active = False # Start inactive

        self.create_ui() # Create UI after variables are initialized
        self.check_ffmpeg() # ### ADDED: Check for ffmpeg early

    def setup_main_window(self):
        self.root.title('Ultimate Music Player')
        # ### MODIFICATION: Slightly larger default size
        self.root.geometry("1200x850")
        self.root.minsize(1000, 700)
        self.root.configure(bg="#0a0a0a")

    def setup_styles(self):
        """Initializes the ttk Style object."""
        self.style = ttk.Style()
        # Apply the currently loaded theme
        self.apply_theme(self.current_theme)

    # ### ADDED: Apply Theme Method ###
    def apply_theme(self, theme_name):
        """Applies the specified theme to UI elements."""
        if theme_name not in THEMES:
            print(f"Warning: Theme '{theme_name}' not found. Using default '{DEFAULT_THEME}'.")
            theme_name = DEFAULT_THEME

        self.current_theme = theme_name
        theme = THEMES[theme_name]
        print(f"Applying theme: {theme_name}")

        # Use 'clam' or another base theme that allows configuration
        self.style.theme_use('clam')

        # --- Configure Styles based on the theme dictionary ---
        self.style.configure('TFrame', background=theme['frame_bg'])
        self.style.configure('TLabel', background=theme['frame_bg'], foreground=theme['fg'], font=('Helvetica', 10))

        self.style.configure('Control.TButton', background=theme['control_bg'], foreground=theme['fg'],
                               borderwidth=0, font=('Helvetica', 10), padding=5)
        self.style.map('Control.TButton', background=[('active', theme['control_active_bg'])])

        self.style.configure('Toggle.TButton', background=theme['control_bg'], foreground=theme['fg'],
                               borderwidth=0, font=('Helvetica', 10, 'bold'), padding=5)
        self.style.map('Toggle.TButton',
                       background=[('active', theme['control_active_bg']), ('selected', theme['toggle_selected_bg'])],
                       foreground=[('selected', theme['toggle_selected_fg'])])

        # Note: Listbox is a tk widget, not ttk, but we style its frame/scrollbar via ttk.
        # We need to configure the Listbox itself directly later.
        self.style.configure('Playlist.TListbox', # This might be less effective for tk.Listbox
                               background=theme['listbox_bg'], foreground=theme['listbox_fg'],
                               selectbackground=theme['listbox_select_bg'], font=('Helvetica', 12),
                               highlightthickness=0, borderwidth=0)

        self.style.configure('Modern.Horizontal.TScale', troughcolor=theme['scale_trough'],
                               sliderthickness=10, background=theme['frame_bg']) # Background often needed

        self.style.configure('Modern.Horizontal.TProgressbar', troughcolor=theme['progress_trough'],
                               background=theme['progress_bar'], thickness=10)

        # --- Apply theme to non-ttk widgets directly ---
        # Required because styles might not cover everything, or for tk widgets
        self.root.configure(bg=theme['bg'])

        # Update existing widgets if they have already been created
        # Use hasattr checks because this might be called before create_ui during init
        if hasattr(self, 'main_frame'):
             # Update frames (might inherit from root, but direct set is safer)
             for frame in [self.main_frame,
                           getattr(self, 'top_frame', None), # Check if these exist yet
                           getattr(self, 'controls_outer_frame', None),
                           getattr(self, 'controls_frame', None),
                           getattr(self, 'volume_frame', None),
                           getattr(self, 'playlist_frame', None),
                           getattr(self, 'list_controls', None),
                           getattr(self, 'listbox_frame', None),
                           getattr(self, 'vis_frame', None),
                           getattr(self, 'status_frame', None)]:
                  if frame:
                      try: # Use try-except for safety
                          frame.configure(style='TFrame') # Re-apply style
                      except tk.TclError: pass # Widget might not exist fully yet

        if hasattr(self, 'playlist_box'): # This is a tk.Listbox
            self.playlist_box.configure(
                bg=theme['listbox_bg'],
                fg=theme['listbox_fg'],
                selectbackground=theme['listbox_select_bg'],
                selectforeground=theme['listbox_select_fg']
            )
        if hasattr(self, 'vis_canvas'): # This is a tk.Canvas
            self.vis_canvas.configure(bg=theme['bg'])

        # Re-apply styles to specific labels if needed (often inherit correctly)
        if hasattr(self, 'song_title_label'):
             self.song_title_label.configure(style='TLabel')
             self.song_artist_label.configure(style='TLabel')
             self.time_label.configure(style='TLabel')
             # Find the volume label and re-apply style if needed
             if hasattr(self, 'volume_frame'):
                  for child in self.volume_frame.winfo_children():
                      if isinstance(child, ttk.Label):
                          child.configure(style='TLabel')


        # Re-apply styles to specific buttons if they might lose styling
        if hasattr(self, 'play_pause_button'):
            self.play_pause_button.configure(style='Control.TButton')
            # ... find and re-apply style to other Control.TButton and Toggle.TButton instances ...
            # This can be tedious; often configuring the style itself is enough,
            # but direct config ensures changes apply if widgets were created before the style change.
            # Example for shuffle button:
            if hasattr(self, 'shuffle_button'):
                 self.shuffle_button.configure(style='Control.TButton') # Use base style, state will map color
                 # Re-apply selected state if needed
                 if self.shuffle_on:
                     self.shuffle_button.state(['selected'])
                 else:
                     self.shuffle_button.state(['!selected'])
            if hasattr(self, 'repeat_button'):
                 self.repeat_button.configure(style='Control.TButton')
                 # Re-apply selected state if needed
                 if self.repeat_mode != REPEAT_OFF:
                     self.repeat_button.state(['selected'])
                 else:
                     self.repeat_button.state(['!selected'])

        print(f"Theme '{theme_name}' applied.")

     ### ADDED: Change Theme Callback ###
    def change_theme(self, theme_name):
        """Callback function to change the theme."""
        self.apply_theme(theme_name)
        # You might want to save the config immediately after changing
        # self.save_config() # Optional: save instantly

    def initialize_mixer(self):
        try:
            mixer.init()
            mixer.music.set_volume(0.7) # Set initial volume
        except Exception as e:
            messagebox.showerror("Mixer Error", f"Failed to initialize audio mixer: {e}\nMake sure you have audio drivers installed.")
            self.root.destroy()

    # ### ADDED: Check if ffmpeg seems accessible to pydub
    def check_ffmpeg(self):
        try:
            # Try converting a tiny silent segment. This often triggers the check.
            silence = AudioSegment.silent(duration=10)
            silence.export(os.devnull, format="mp3") # Export to null device
            print("FFmpeg check passed (or not needed for basic formats).")
        except CouldntDecodeError:
             print("FFmpeg check failed.") # Should not happen here ideally
        except Exception as e: # Catch broader exceptions, often related to finding ffmpeg/libav
             if "ffmpeg" in str(e).lower() or "libav" in str(e).lower():
                 messagebox.showwarning("FFmpeg Missing?",
                                        "Could not find FFmpeg or Libav.\n"
                                        "Support for formats like M4A, MP4, FLAC, Opus, AAC might be limited.\n"
                                        "Please install FFmpeg and ensure it's in your system's PATH.")
             else:
                 print(f"Potential issue during FFmpeg check: {e}") # Log other errors

    def load_images(self):
        # ### MODIFICATION: Add new icons
        self.images = {
            'play': self.load_image('play_button.png', (50, 50)),
            'pause': self.load_image('pause_button.png', (50, 50)),
            'stop': self.load_image('stop_button.png', (50, 50)),
            'next': self.load_image('next_button.png', (40, 40)),   # ADD these images
            'prev': self.load_image('prev_button.png', (40, 40)),   # ADD these images
            'shuffle_off': self.load_image('shuffle_off.png', (30, 30)), # ADD these images
            'shuffle_on': self.load_image('shuffle_on.png', (30, 30)),   # ADD these images
            'repeat_off': self.load_image('repeat_off.png', (30, 30)), # ADD these images
            'repeat_one': self.load_image('repeat_one.png', (30, 30)), # ADD these images
            'repeat_all': self.load_image('repeat_all.png', (30, 30)), # ADD these images
            'logo': self.load_image('logo.png', (250, 250)) # Slightly smaller logo
        }

    def load_image(self, filename, size=None):
        try:
            img_path = os.path.join(IMG_DIR, filename)
            if not os.path.exists(img_path):
                print(f"Warning: Image file not found at {img_path}")
                # Return a placeholder transparent image of the correct size
                if size:
                    img = Image.new('RGBA', size, (0, 0, 0, 0))
                    return ImageTk.PhotoImage(img)
                else:
                    return None # Or handle differently if size is not guaranteed

            img = Image.open(img_path).convert("RGBA") # Ensure RGBA for transparency
            if size:
                img = img.resize(size, Image.Resampling.LANCZOS)
            return ImageTk.PhotoImage(img)
        except Exception as e:
            messagebox.showwarning("Image Load Error", f"Error loading image {filename}: {e}")
            # Return a placeholder if any error occurs
            if size:
                try:
                    img = Image.new('RGBA', size, (0, 0, 0, 0))
                    return ImageTk.PhotoImage(img)
                except: return None # Final fallback
            return None

     # ### ADDED: Load configuration ###
    def load_config(self):
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                    self.current_theme = config.get('theme', DEFAULT_THEME)
                    # Load other settings here in the future if needed
                    print(f"Loaded config. Theme set to: {self.current_theme}")
            else:
                # Use default theme if config file doesn't exist
                self.current_theme = DEFAULT_THEME
                print("Config file not found. Using default theme.")
        except (json.JSONDecodeError, IOError, Exception) as e:
            print(f"Error loading config file '{CONFIG_FILE}': {e}. Using default theme.")
            self.current_theme = DEFAULT_THEME


    # ### ADDED: Save configuration ###
    def save_config(self):
        config = {
            'theme': self.current_theme
            # Save other settings here
        }
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(config, f, indent=4)
            print(f"Configuration saved to '{CONFIG_FILE}'.")
        except IOError as e:
            print(f"Error saving config file '{CONFIG_FILE}': {e}")


    def create_ui(self):
        # ### ADDED: Create Menu Bar FIRST ###
        # Create menu before main frame to avoid potential layout issues on some systems
        self.create_menu()

        # --- Main container Frame - Create it ONCE ---
        self.main_frame = ttk.Frame(self.root, style='TFrame')
        # Add this single main_frame to the root window using pack
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # --- Configure grid layout FOR CHILDREN INSIDE self.main_frame ---
        # Define how rows/columns inside main_frame should resize
        self.main_frame.grid_rowconfigure(0, weight=0) # Top frame (logo/meta) - No extra vertical space
        self.main_frame.grid_rowconfigure(1, weight=1) # Playlist row expands vertically
        self.main_frame.grid_rowconfigure(2, weight=1) # Visualizer row expands vertically
        self.main_frame.grid_rowconfigure(3, weight=0) # Controls row - No extra vertical space
        self.main_frame.grid_rowconfigure(4, weight=0) # Status bar row - No extra vertical space
        self.main_frame.grid_columnconfigure(0, weight=1) # Main column expands horizontally

        # --- Create Widgets and grid them into self.main_frame ---

        # Top section (Logo and Metadata) - Placed in row 0 of main_frame
        top_frame = ttk.Frame(self.main_frame, style='TFrame')
        top_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        top_frame.grid_columnconfigure(1, weight=1) # Metadata column inside top_frame expands

        self.logo_label = ttk.Label(top_frame, image=self.images.get('logo'), style='TLabel')
        self.logo_label.grid(row=0, column=0, rowspan=2, padx=(0, 20))

        self.song_title_label = ttk.Label(top_frame, text="No Song Playing", font=('Helvetica', 14, 'bold'), anchor='w', style='TLabel')
        self.song_title_label.grid(row=0, column=1, sticky="ew")
        self.song_artist_label = ttk.Label(top_frame, text="", font=('Helvetica', 11), anchor='w', style='TLabel')
        self.song_artist_label.grid(row=1, column=1, sticky="ew")

        # Playlist (Takes up vertical space) - Placed in row 1 of main_frame
        # (create_playlist method itself handles gridding its internal elements)
        self.create_playlist()

        # Visualizer (Takes up vertical space) - Placed in row 2 of main_frame
        # (create_visualizer method handles gridding its internal elements)
        self.create_visualizer()

        # Control Panel - Placed in row 3 of main_frame
        # (create_controls method handles gridding its internal elements)
        self.create_controls()

        # Status Bar - Placed in row 4 of main_frame
        # (create_status_bar method handles gridding its internal elements)
        self.create_status_bar()

        # Initially hide visualizer, show logo
        # Ensure vis_frame exists before trying to remove it
        if hasattr(self, 'vis_frame'):
             self.vis_frame.grid_remove()
        # Logo is already gridded within top_frame, so it should show correctly.


    def create_controls(self):
        # ### MODIFICATION: Use grid layout for controls too
        controls_outer_frame = ttk.Frame(self.main_frame, style='TFrame')
        controls_outer_frame.grid(row=3, column=0, sticky="ew", pady=10) # Placed below playlist and vis

        # Center the main controls using column configuration
        controls_outer_frame.grid_columnconfigure(0, weight=1)
        controls_outer_frame.grid_columnconfigure(1, weight=0) # Playback buttons
        controls_outer_frame.grid_columnconfigure(2, weight=0) # Volume
        controls_outer_frame.grid_columnconfigure(3, weight=1)

        controls_frame = ttk.Frame(controls_outer_frame, style='TFrame')
        controls_frame.grid(row=0, column=1) # Place in the center column

        # Playback buttons (Prev, Play/Pause, Stop, Next)
        self.play_pause_button = ttk.Button(controls_frame, image=self.images.get('play'), command=self.toggle_play_pause, style='Control.TButton')
        self.play_pause_button.pack(side=tk.LEFT, padx=5)
        ttk.Button(controls_frame, image=self.images.get('prev'), command=self.play_previous, style='Control.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(controls_frame, image=self.images.get('stop'), command=self.stop_music, style='Control.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(controls_frame, image=self.images.get('next'), command=self.play_next, style='Control.TButton').pack(side=tk.LEFT, padx=5)

        # Shuffle and Repeat Buttons
        self.shuffle_button = ttk.Button(controls_frame, image=self.images.get('shuffle_off'), command=self.toggle_shuffle, style='Control.TButton')
        self.shuffle_button.pack(side=tk.LEFT, padx=(15, 5))
        self.repeat_button = ttk.Button(controls_frame, image=self.images.get('repeat_off'), command=self.toggle_repeat, style='Control.TButton')
        self.repeat_button.pack(side=tk.LEFT, padx=5)

        # Volume control (aligned to the right of playback controls)
        volume_frame = ttk.Frame(controls_outer_frame, style='TFrame')
        volume_frame.grid(row=0, column=2, padx=(20, 0))
        ttk.Label(volume_frame, text="Volume:", style='TLabel').pack(side=tk.LEFT)
        self.volume_scale = ttk.Scale(volume_frame, from_=0, to=100, orient=tk.HORIZONTAL, command=self.set_volume, style='Modern.Horizontal.TScale', length=120)
        self.volume_scale.set(70) # Initial volume
        self.volume_scale.pack(side=tk.LEFT, padx=5)


    def create_playlist(self):
        # ### MODIFICATION: Playlist frame now uses grid
        playlist_frame = ttk.Frame(self.main_frame, style='TFrame')
        playlist_frame.grid(row=1, column=0, sticky="nsew", pady=5)
        playlist_frame.grid_rowconfigure(1, weight=1) # Listbox row expands
        playlist_frame.grid_columnconfigure(0, weight=1) # Listbox col expands

        # Playlist controls (Add, Remove, Save, Load, Clear)
        list_controls = ttk.Frame(playlist_frame, style='TFrame')
        list_controls.grid(row=0, column=0, sticky="ew", pady=(0, 5))

        ttk.Button(list_controls, text="Add Files", command=self.add_music, style='Control.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(list_controls, text="Add Folder", command=self.add_folder, style='Control.TButton').pack(side=tk.LEFT, padx=5) # ### ADDED
        ttk.Button(list_controls, text="Remove Sel.", command=self.remove_selected_song, style='Control.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(list_controls, text="Clear All", command=self.clear_playlist, style='Control.TButton').pack(side=tk.LEFT, padx=5) # ### ADDED
        ttk.Button(list_controls, text="Save List", command=self.save_playlist, style='Control.TButton').pack(side=tk.LEFT, padx=(15, 5)) # ### ADDED
        ttk.Button(list_controls, text="Load List", command=self.load_playlist, style='Control.TButton').pack(side=tk.LEFT, padx=5) # ### ADDED

        # Listbox itself
        listbox_frame = ttk.Frame(playlist_frame, style='TFrame') # Frame to hold listbox and scrollbar
        listbox_frame.grid(row=1, column=0, sticky="nsew")
        listbox_frame.grid_rowconfigure(0, weight=1)
        listbox_frame.grid_columnconfigure(0, weight=1)

        self.playlist_box = tk.Listbox(listbox_frame, selectmode=tk.SINGLE,
                                      font=('Helvetica', 11), # Slightly smaller font
                                      bg='#1a1a1a', fg='white', selectbackground='#0078D7', # More distinct selection
                                      selectforeground='white', borderwidth=0, highlightthickness=0,
                                      activestyle='none') # Avoid dotted outline
        # ### ADDED: Double click to play
        self.playlist_box.bind('<Double-Button-1>', self.play_on_double_click)

        scroll = ttk.Scrollbar(listbox_frame, orient=tk.VERTICAL, command=self.playlist_box.yview)
        self.playlist_box.config(yscrollcommand=scroll.set)

        scroll.grid(row=0, column=1, sticky='ns')
        self.playlist_box.grid(row=0, column=0, sticky='nsew')

    def create_visualizer(self):
        # ### MODIFICATION: Visualizer uses grid, starts hidden
        self.vis_frame = ttk.Frame(self.main_frame, style='TFrame')
        self.vis_frame.grid(row=2, column=0, sticky="nsew", pady=5) # Placed below playlist
        self.vis_frame.grid_rowconfigure(0, weight=1)
        self.vis_frame.grid_columnconfigure(0, weight=1)

        self.vis_canvas = tk.Canvas(self.vis_frame, bg='#0a0a0a', highlightthickness=0, width=600, height=150) # Fixed initial size suggestion
        self.vis_canvas.grid(row=0, column=0, sticky="nsew")

        self.bars = []
        self.create_spectrum_visualizer() # Keep the aesthetic visualizer for now

    def create_spectrum_visualizer(self):
        # Keep the aesthetic circular visualizer as a placeholder
        # A true spectrum visualizer requires audio analysis (complex)
        self.vis_canvas.update_idletasks() # Ensure canvas size is known
        width = self.vis_canvas.winfo_width()
        height = self.vis_canvas.winfo_height()
        if width < 10 or height < 10: # Fallback size
            width, height = 600, 150

        center_x = width // 2
        center_y = height // 2
        max_radius = min(center_x, center_y) * 0.8
        min_radius = max_radius * 0.4
        num_bars = 60 # More bars for finer look
        bar_width = 4

        self.vis_canvas.delete("all") # Clear previous bars if recreating
        self.bars = []

        for i in range(num_bars):
            angle = math.radians(i * (360 / num_bars) - 90) # Start from top
            x0 = center_x + min_radius * math.cos(angle)
            y0 = center_y + min_radius * math.sin(angle)
            x1 = center_x + max_radius * math.cos(angle)
            y1 = center_y + max_radius * math.sin(angle)

            # Initial bar (short)
            bar = self.vis_canvas.create_line(
                x0, y0,
                x0 + (max_radius * 0.1 * math.cos(angle)), # Start short
                y0 + (max_radius * 0.1 * math.sin(angle)),
                width=bar_width,
                fill=self.generate_gradient_color(i / num_bars)
            )
            self.bars.append(bar)

        # ### ADDED: Store constants for update_visualization
        self.vis_center_x = center_x
        self.vis_center_y = center_y
        self.vis_min_radius = min_radius
        self.vis_max_radius = max_radius
        self.vis_num_bars = num_bars

     # ### ADDED: Create Menu Method ###
    def create_menu(self):
        """Creates the main menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar) # Assign menu to the root window

        # --- Options Menu ---
        options_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Options", menu=options_menu)

        # --- Themes Submenu ---
        theme_menu = tk.Menu(options_menu, tearoff=0)
        options_menu.add_cascade(label="Theme", menu=theme_menu)

        # Variable to hold the selected theme name for radio buttons
        self.theme_var = tk.StringVar(value=self.current_theme)

        # Add radio buttons for each theme
        for theme_name in THEMES:
            theme_menu.add_radiobutton(
                label=theme_name,
                variable=self.theme_var,
                value=theme_name,
                command=lambda name=theme_name: self.change_theme(name) # Pass name correctly
            )

    def generate_gradient_color(self, position):
        # Cycle through hue for more colors
        hue = position * 360
        # Simple HSL to RGB approximation (adjust saturation/lightness as needed)
        import colorsys
        r, g, b = colorsys.hls_to_rgb(hue / 360.0, 0.6, 0.7) # Hue, Lightness, Saturation
        return f'#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}'


    def update_visualization(self):
        # ### MODIFICATION: Check playing state and use stored constants
        if self.playing and not self.paused and self.visualization_active and self.bars:
            current_time_ms = mixer.music.get_pos() # Milliseconds

            for i, bar in enumerate(self.bars):
                angle = math.radians(i * (360 / self.vis_num_bars) - 90) # Start from top

                # More dynamic scaling based on time and position
                # This is still *not* frequency analysis, just pseudo-random movement
                dynamic_scale = 0.1 + 0.9 * abs(math.sin(math.pi * (current_time_ms / 3000.0 + i / self.vis_num_bars)))
                # Add some random jitter
                dynamic_scale *= (1 + random.uniform(-0.1, 0.1))
                dynamic_scale = max(0.05, min(1.0, dynamic_scale)) # Clamp scale

                x0 = self.vis_center_x + self.vis_min_radius * math.cos(angle)
                y0 = self.vis_center_y + self.vis_min_radius * math.sin(angle)
                x1 = self.vis_center_x + (self.vis_min_radius + (self.vis_max_radius - self.vis_min_radius) * dynamic_scale) * math.cos(angle)
                y1 = self.vis_center_y + (self.vis_min_radius + (self.vis_max_radius - self.vis_min_radius) * dynamic_scale) * math.sin(angle)

                try:
                    self.vis_canvas.coords(bar, x0, y0, x1, y1)
                    # Update color slowly based on time
                    color_pos = (i / self.vis_num_bars + current_time_ms / 20000.0) % 1.0
                    self.vis_canvas.itemconfig(bar, fill=self.generate_gradient_color(color_pos))
                except tk.TclError: # Handle cases where canvas might be destroyed during update
                    break

            # Schedule next update
            self.after_id_visualizer = self.root.after(50, self.update_visualization) # 50ms update interval
        else:
             # If stopped or paused, reset visualizer to base state (optional)
             self.reset_visualization()


    # ### ADDED: Reset visualizer bars to minimum length
    def reset_visualization(self):
        if not self.bars: return
        for i, bar in enumerate(self.bars):
             angle = math.radians(i * (360 / self.vis_num_bars) - 90)
             x0 = self.vis_center_x + self.vis_min_radius * math.cos(angle)
             y0 = self.vis_center_y + self.vis_min_radius * math.sin(angle)
             # Set to minimum length (or zero length)
             x1 = x0 + (self.vis_max_radius * 0.05 * math.cos(angle)) # Minimal length
             y1 = y0 + (self.vis_max_radius * 0.05 * math.sin(angle))
             try:
                 self.vis_canvas.coords(bar, x0, y0, x1, y1)
                 self.vis_canvas.itemconfig(bar, fill=self.generate_gradient_color(i / self.vis_num_bars)) # Reset color too
             except tk.TclError:
                 break


    def create_status_bar(self):
        # ### MODIFICATION: Use grid, add seek functionality
        status_frame = ttk.Frame(self.main_frame, style='TFrame')
        status_frame.grid(row=4, column=0, sticky="ew", pady=(10, 0)) # Bottom row
        status_frame.grid_columnconfigure(1, weight=1) # Progress bar expands

        self.time_label = ttk.Label(status_frame, text="00:00 / 00:00", style='TLabel', font=('Helvetica', 10))
        self.time_label.grid(row=0, column=0, padx=(0, 10))

        self.progress_bar = ttk.Progressbar(status_frame, orient=tk.HORIZONTAL,
                                            mode='determinate', length=400, style='Modern.Horizontal.TProgressbar')
        self.progress_bar.grid(row=0, column=1, sticky="ew")
        # ### ADDED: Bind mouse click to progress bar for seeking
        self.progress_bar.bind("<Button-1>", self.seek_music)

        self.total_time_label = ttk.Label(status_frame, text="", style='TLabel', font=('Helvetica', 10)) # Separate label for total time
        self.total_time_label.grid(row=0, column=2, padx=(10, 0))


    # --- Core Functionality Methods ---

    # ### ADDED: Add music from a folder
    def add_folder(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            added_count = 0
            for filename in os.listdir(folder_path):
                file_path = os.path.join(folder_path, filename)
                if os.path.isfile(file_path):
                    # Check if the file extension is in our supported list
                    _, ext = os.path.splitext(filename)
                    if any(ext.lower() in type_pattern for type_desc, type_pattern in SUPPORTED_FILETYPES if type_pattern != '*.*'):
                        if file_path not in self.playlist_paths:
                            self.playlist_paths.append(file_path)
                            self.playlist_box.insert(tk.END, os.path.basename(file_path))
                            added_count += 1
            if added_count > 0:
                 messagebox.showinfo("Folder Added", f"Added {added_count} supported audio files.")
            else:
                 messagebox.showinfo("Folder Scan", "No new supported audio files found in the selected folder.")
            self._apply_shuffle() # Re-shuffle if needed


    def add_music(self):
        paths = filedialog.askopenfilenames(filetypes=SUPPORTED_FILETYPES)
        added_count = 0
        if paths:
            for path in paths:
                if path not in self.playlist_paths:
                    self.playlist_paths.append(path)
                    self.playlist_box.insert(tk.END, os.path.basename(path)) # Display only filename
                    added_count += 1
            if added_count > 0:
                 self._apply_shuffle() # Re-shuffle if needed


    # ### MODIFICATION: Renamed and clarified remove function
    def remove_selected_song(self):
        selected_indices = self.playlist_box.curselection()
        if not selected_indices:
            messagebox.showwarning("Remove Error", "Please select a song from the playlist to remove.")
            return

        selected_index = selected_indices[0]

        # Stop music if the removed song is the one playing
        if selected_index == self.current_index and self.playing:
            self.stop_music() # Stop playback cleanly

        # Remove from listbox and internal path list
        self.playlist_box.delete(selected_index)
        removed_path = self.playlist_paths.pop(selected_index)
        print(f"Removed: {removed_path}")

        # Adjust current_index if necessary
        if self.current_index >= selected_index:
             # If the removed item was before or at the current index, decrement current index
             # But handle the case where it was the *currently playing* song (already stopped)
             if self.current_index > selected_index:
                 self.current_index -= 1
             elif self.current_index == selected_index:
                 # It *was* the current song, now it's gone. Set index invalid.
                 self.current_index = -1

        # Update shuffle list if shuffle is on
        self._apply_shuffle() # Regenerate shuffled indices


    # ### ADDED: Clear entire playlist
    def clear_playlist(self):
        if messagebox.askyesno("Confirm Clear", "Are you sure you want to clear the entire playlist?"):
            self.stop_music()
            self.playlist_box.delete(0, tk.END)
            self.playlist_paths.clear()
            self.current_index = -1
            self.shuffled_indices = []
            self.song_title_label.config(text="No Song Playing")
            self.song_artist_label.config(text="")
            self._update_time_display(0, 0) # Reset time display


    # ### ADDED: Save playlist to a file
    def save_playlist(self):
        if not self.playlist_paths:
            messagebox.showwarning("Save Error", "Playlist is empty. Add songs before saving.")
            return

        filepath = filedialog.asksaveasfilename(
            defaultextension=".ump",
            filetypes=PLAYLIST_FILETYPE,
            title="Save Playlist As"
        )
        if filepath:
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(self.playlist_paths, f)
                messagebox.showinfo("Playlist Saved", f"Playlist saved successfully to\n{filepath}")
            except Exception as e:
                messagebox.showerror("Save Error", f"Failed to save playlist: {e}")


    # ### ADDED: Load playlist from a file
    def load_playlist(self):
        if self.playlist_paths:
             if not messagebox.askyesno("Confirm Load", "Loading a new playlist will clear the current one. Continue?"):
                 return

        filepath = filedialog.askopenfilename(
            filetypes=PLAYLIST_FILETYPE,
            title="Load Playlist"
        )
        if filepath:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    loaded_paths = json.load(f)

                if not isinstance(loaded_paths, list):
                     raise ValueError("Invalid playlist file format.")

                self.clear_playlist() # Clear existing playlist first

                added_count = 0
                missing_files = []
                for path in loaded_paths:
                    if os.path.exists(path): # Check if file still exists
                        self.playlist_paths.append(path)
                        self.playlist_box.insert(tk.END, os.path.basename(path))
                        added_count += 1
                    else:
                        missing_files.append(os.path.basename(path))

                self._apply_shuffle() # Apply shuffle if needed

                if missing_files:
                    messagebox.showwarning("Load Warning",
                                           f"Loaded {added_count} songs.\nCould not find the following files (removed from list):\n" + "\n".join(missing_files))
                elif added_count > 0:
                     messagebox.showinfo("Playlist Loaded", f"Playlist loaded successfully.")
                else:
                     messagebox.showinfo("Playlist Loaded", "Loaded playlist file, but no valid songs were found.")


            except json.JSONDecodeError:
                 messagebox.showerror("Load Error", "Failed to load playlist: Invalid file format.")
            except Exception as e:
                messagebox.showerror("Load Error", f"Failed to load playlist: {e}")


    # ### ADDED: Get metadata using Mutagen
    def get_metadata(self, filepath):
        title = os.path.basename(filepath) # Default to filename
        artist = "Unknown Artist"
        album = "Unknown Album"
        duration = 0

        try:
            audio = MutagenFile(filepath, easy=True)
            if audio:
                 # EasyID3/EasyMP4 like access
                 if 'title' in audio: title = audio['title'][0]
                 if 'artist' in audio: artist = audio['artist'][0]
                 if 'album' in audio: album = audio['album'][0]
                 # Get duration from info attribute (more reliable across formats)
                 if hasattr(audio, 'info') and hasattr(audio.info, 'length'):
                     duration = int(audio.info.length)

        except Exception as e:
            print(f"Could not read metadata for {filepath}: {e}")
            # Fallback: try pydub for duration if mutagen failed
            try:
                 audio_seg = AudioSegment.from_file(filepath)
                 duration = len(audio_seg) // 1000 # pydub duration is in ms
            except Exception as e_pd:
                 print(f"Could not get duration using pydub either for {filepath}: {e_pd}")

        return {"title": title, "artist": artist, "album": album, "duration": duration}


    # ### ADDED: Unified method to start playing a track at a given index
    # ### ADDED: Unified method to start playing a track at a given index
    def _play_track_at_index(self, index):
        if 0 <= index < len(self.playlist_paths):
            self.current_index = index
            self.current_song_path = self.playlist_paths[self.current_index]

            # Highlight in playlist
            self.playlist_box.selection_clear(0, tk.END)
            self.playlist_box.selection_set(self.current_index)
            self.playlist_box.activate(self.current_index)
            self.playlist_box.see(self.current_index) # Ensure visible

            # ### MODIFICATION: Cleanup using the stored path now
            self._cleanup_temp_file()

            metadata = self.get_metadata(self.current_song_path)
            self.song_length_seconds = metadata['duration']
            self.song_title_label.config(text=metadata['title'])
            self.song_artist_label.config(text=metadata['artist'])

            # Update total time display and progress bar range
            self.progress_bar['maximum'] = self.song_length_seconds if self.song_length_seconds > 0 else 1 # Avoid division by zero
            self._update_time_display(0, self.song_length_seconds)

            try:
                # Check if conversion is needed
                file_ext = os.path.splitext(self.current_song_path)[1].lower()
                load_path = self.current_song_path # Assume direct load initially

                # Explicitly list formats needing conversion for pygame.mixer
                if file_ext not in ['.wav', '.mp3', '.ogg']:
                    print(f"Format {file_ext} requires conversion, attempting with pydub...")
                    temp_file = None # Define temp_file here to ensure it's in scope for finally
                    try:
                        audio = AudioSegment.from_file(self.current_song_path)
                        # ### MODIFICATION: Handle temp file creation/closing carefully
                        temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
                        temp_file_path = temp_file.name # Get the name *before* closing
                        print(f"Attempting to convert to temporary file: {temp_file_path}")
                        audio.export(temp_file, format='wav') # Export *to the file object*
                        temp_file.close() # <--- **** Explicitly close the file ****
                        # Now the file should be fully written and closed, ready for Pygame
                        load_path = temp_file_path
                        self.temp_wav_file_path = temp_file_path # Store path for later cleanup
                        print(f"Conversion successful. Using temp file: {load_path}")

                    except CouldntDecodeError as cde:
                         messagebox.showerror("Playback Error", f"Could not decode file: {os.path.basename(self.current_song_path)}\n\nIs FFmpeg installed and in PATH?\nError: {cde}")
                         self._reset_playback_state()
                         # ### MODIFICATION: Clean up temp file even if conversion fails
                         if temp_file:
                             temp_file.close() # Ensure closed
                             if os.path.exists(temp_file.name):
                                 os.remove(temp_file.name)
                         return
                    except Exception as e_conv:
                        messagebox.showerror("Playback Error", f"Conversion failed for {os.path.basename(self.current_song_path)}: {e_conv}")
                        self._reset_playback_state()
                        # ### MODIFICATION: Clean up temp file even if conversion fails
                        if temp_file:
                             temp_file.close() # Ensure closed
                             if os.path.exists(temp_file.name):
                                 os.remove(temp_file.name)
                        return
                    # No finally block needed here anymore as cleanup happens on error or in _cleanup_temp_file

                # Load and Play
                print(f"Loading into mixer: {load_path}") # Debug print
                mixer.music.load(load_path) # Load using the potentially temporary path
                print("Mixer load successful.") # Debug print
                mixer.music.play()
                print("Mixer play successful.") # Debug print
                self.playing = True
                self.paused = False
                self.play_pause_button.config(image=self.images.get('pause')) # Show pause icon

                # Switch view: hide logo, show visualizer
                self.logo_label.grid_remove()
                self.vis_frame.grid() # Show visualizer frame
                self.visualization_active = True # Enable flag
                self.reset_visualization() # Ensure clean start for vis
                self.update_visualization() # Start visualizer updates
                self.update_progress() # Start progress updates

            # ### MODIFICATION: Correct exception type here
            except pygame.error as e_mix:
                 messagebox.showerror("Playback Error", f"Mixer could not play file: {os.path.basename(self.current_song_path)}\nPath attempted: {load_path}\nError: {e_mix}")
                 self._reset_playback_state()
                 self._cleanup_temp_file() # Clean up if conversion happened but load failed
            except Exception as e:
                 messagebox.showerror("Playback Error", f"An unexpected error occurred while trying to play:\n{os.path.basename(self.current_song_path)}\nError: {e}")
                 self._reset_playback_state()
                 self._cleanup_temp_file() # Clean up on general errors too

        else:
            print("Invalid index or empty playlist.")
            self.stop_music() # Stop if trying to play invalid index


    # ### MODIFICATION: Play music handles selection or plays current/first
    def play_music(self):
        if not self.playlist_paths:
            messagebox.showwarning("Empty Playlist", "Please add songs to the playlist first.")
            return

        selected_indices = self.playlist_box.curselection()

        if selected_indices:
            # Play the selected song
            target_index = selected_indices[0]
        elif self.current_index != -1 and not self.playing:
            # Resume the 'current' song if one was selected but stopped
            target_index = self.current_index
        else:
            # Play the first song if nothing is selected or current
             target_index = self.shuffled_indices[0] if self.shuffle_on else 0

        if 0 <= target_index < len(self.playlist_paths):
            # If it's the same song and it's paused, just unpause
            if target_index == self.current_index and self.paused:
                self.toggle_play_pause()
            else:
                # Otherwise, stop current and play the new/selected one
                self.stop_music(internal_call=True) # Stop without resetting UI elements yet
                self._play_track_at_index(target_index)
        else:
             messagebox.showerror("Error", "Cannot determine which song to play.")


    # ### ADDED: Play song on double click
    def play_on_double_click(self, event):
        widget = event.widget
        selected_indices = widget.curselection()
        if selected_indices:
            target_index = selected_indices[0]
            self.stop_music(internal_call=True) # Stop current playback
            self._play_track_at_index(target_index)


    # ### MODIFICATION: Combined play/pause toggle
    def toggle_play_pause(self):
        if not self.playing and not self.paused:
            # If nothing is loaded/playing, treat as play command
            self.play_music()
        elif self.playing and not self.paused:
            # Pause
            mixer.music.pause()
            self.paused = True
            self.playing = False # Mark as not actively playing for updates
            self.play_pause_button.config(image=self.images.get('play')) # Show play icon
            # Stop visualizer updates but don't reset it visually
            if self.after_id_visualizer:
                self.root.after_cancel(self.after_id_visualizer)
            self.visualization_active = False # Also set flag

        elif self.paused:
            # Unpause
            mixer.music.unpause()
            self.paused = False
            self.playing = True # Mark as actively playing again
            self.play_pause_button.config(image=self.images.get('pause')) # Show pause icon
            self.visualization_active = True # Re-enable flag
            self.update_visualization() # Resume visualizer
            self.update_progress() # Resume progress updates (important if paused for a while)


    # ### MODIFICATION: Stop music cleans up states
    def stop_music(self, internal_call=False):
        # internal_call prevents UI reset when stopping just before playing next
        mixer.music.stop()
        self.playing = False
        self.paused = False
        self._cleanup_temp_file() # Clean up any temp file

        # Cancel scheduled updates
        if self.after_id_progress:
            self.root.after_cancel(self.after_id_progress)
            self.after_id_progress = None
        if self.after_id_visualizer:
            self.root.after_cancel(self.after_id_visualizer)
            self.after_id_visualizer = None
        self.visualization_active = False

        if not internal_call:
            self._reset_playback_state()
            self.play_pause_button.config(image=self.images.get('play'))
            # Switch view: hide visualizer, show logo
            self.vis_frame.grid_remove()
            self.logo_label.grid() # Show logo again
            # Deselect in listbox
            self.playlist_box.selection_clear(0, tk.END)
            self.current_index = -1 # Indicate no song is actively selected/playing


    # ### ADDED: Central place to reset playback related UI/state
    def _reset_playback_state(self):
        self.progress_bar['value'] = 0
        self.song_length_seconds = 0
        self._update_time_display(0, 0)
        self.song_title_label.config(text="No Song Playing")
        self.song_artist_label.config(text="")
        self.reset_visualization() # Reset visualizer appearance


    # ### ADDED: Helper to clean up temporary WAV file
    # ### ADDED: Helper to clean up temporary WAV file
    def _cleanup_temp_file(self):
        # ### MODIFICATION: Use the stored path
        if self.temp_wav_file_path:
            try:
                # No need to close here, should have been closed in _play_track_at_index
                if os.path.exists(self.temp_wav_file_path):
                    os.remove(self.temp_wav_file_path) # Delete the file using its path
                    print(f"Cleaned up temp file: {self.temp_wav_file_path}")
                else:
                    print(f"Temp file path stored, but file not found for cleanup: {self.temp_wav_file_path}")
                self.temp_wav_file_path = None # Reset the path variable
            except PermissionError as pe:
                 print(f"Permission error cleaning up temp file {self.temp_wav_file_path}: {pe}. Might still be in use?")
                 # Keep the path stored, maybe try again later? Or just log it.
            except Exception as e:
                print(f"Error cleaning up temp file {self.temp_wav_file_path}: {e}")
                # Reset the path variable even if deletion fails to avoid repeated errors
                self.temp_wav_file_path = None


    def set_volume(self, val):
        try:
            volume = float(val) / 100
            mixer.music.set_volume(volume)
        except Exception as e:
            print(f"Error setting volume: {e}")


    # ### MODIFICATION: Update progress handles song end and looping
    def update_progress(self):
        # Cancel previous loop first
        if self.after_id_progress:
            self.root.after_cancel(self.after_id_progress)
            self.after_id_progress = None

        # Check if still supposed to be playing
        if self.playing and not self.paused:
            current_pos_ms = mixer.music.get_pos() # Returns time since playback START in ms, or -1 if not playing

            if current_pos_ms == -1 and self.playing:
                 # Mixer stopped unexpectedly or finished the song naturally
                 print("Mixer indicates playback ended.")
                 self._handle_song_end() # Let the handler decide what's next
                 return # Stop this update loop

            current_pos_sec = current_pos_ms / 1000.0

            # Ensure progress doesn't exceed max visually (can happen briefly)
            if self.song_length_seconds > 0:
                 display_pos = min(current_pos_sec, self.song_length_seconds)
                 self.progress_bar['value'] = display_pos
                 self._update_time_display(display_pos, self.song_length_seconds)
            else:
                 # If we don't know the length, just show current time
                 self._update_time_display(current_pos_sec, 0)
                 self.progress_bar['value'] = 0 # Or indeterminate?

            # Schedule the next update
            self.after_id_progress = self.root.after(500, self.update_progress) # Update ~twice per second

        elif not self.playing and not self.paused:
             # If stop_music was called, state is correct, do nothing.
             pass
        elif self.paused:
             # If paused, do nothing, don't reschedule. toggle_play_pause will restart it.
             pass


    # ### ADDED: Handle logic when a song finishes playing
    def _handle_song_end(self):
        print(f"Song ended. Repeat Mode: {self.repeat_mode}, Shuffle: {self.shuffle_on}")
        self.playing = False # Mark as not playing

        if self.repeat_mode == REPEAT_ONE:
            print("Repeating single song.")
            # Replay the current track
            self.stop_music(internal_call=True) # Stop cleanly first
            self._play_track_at_index(self.current_index)
        elif self.repeat_mode == REPEAT_ALL:
            print("Repeating all. Playing next.")
            self.play_next(force_next=True) # force_next ensures it wraps around if needed
        elif self.shuffle_on:
             # If shuffle is on but repeat is off, play next shuffled track
             print("Shuffle on, playing next shuffled.")
             self.play_next()
        else:
            # Repeat off, shuffle off: play next sequential track if available
            if self.current_index < len(self.playlist_paths) - 1:
                 print("Playing next sequential song.")
                 self.play_next()
            else:
                 # End of playlist, no repeat/shuffle
                 print("End of playlist reached.")
                 self.stop_music() # Full stop and UI reset


    # ### ADDED: Seek functionality
    def seek_music(self, event):
        # Only allow seeking if a song is loaded (playing or paused)
        if (self.playing or self.paused) and self.current_index != -1:
             # Ensure we have a valid song length to calculate seek position
             if self.song_length_seconds > 0:
                 try:
                     # Calculate position based on click location relative to progress bar width
                     clicked_x = event.x
                     bar_width = self.progress_bar.winfo_width()
                     # Avoid division by zero if bar width isn't available yet
                     if bar_width <= 0:
                         return

                     seek_fraction = clicked_x / bar_width
                     seek_seconds = self.song_length_seconds * seek_fraction

                     # Clamp seek position to valid range (0 to slightly before the end)
                     # Seeking exactly to the end can sometimes cause issues
                     seek_seconds = max(0.0, min(seek_seconds, self.song_length_seconds - 0.1))

                     # --- Seeking Logic ---
                     # Option 2 (Reload and play from start) is generally preferred for reliability
                     # across different audio formats and Pygame backends compared to set_pos.

                     # Determine the correct file path to load (original or temporary WAV)
                     load_path = self.temp_wav_file_path if self.temp_wav_file_path else self.current_song_path

                     # Stop current playback before reloading (important for play(start=...) to work correctly)
                     # mixer.music.stop() # Stop might clear the queue, use pause/rewind maybe? Let's try without stop first.
                                          # Pygame docs suggest play(start=...) implicitly handles this.

                     # Play the loaded music starting from the calculated seek time
                     print(f"Seeking: Attempting to play '{load_path}' from {seek_seconds:.2f}s")
                     mixer.music.play(start=seek_seconds)

                     # If the music was paused, seeking should unpause it and make it play
                     if self.paused:
                         # We need to update the state correctly
                         self.paused = False
                         self.playing = True
                         self.play_pause_button.config(image=self.images.get('pause'))
                         # Ensure visualization and progress updates resume
                         self.visualization_active = True
                         self.update_visualization() # Start visualizer if needed
                         # Progress update will be started below

                     # --- UI Updates ---
                     # Manually update the progress bar immediately for visual feedback
                     self.progress_bar['value'] = seek_seconds
                     # Update the time display immediately
                     self._update_time_display(seek_seconds, self.song_length_seconds)
                     print(f"Seek successful to {seek_seconds:.2f}s")

                     # Restart the progress update loop forcefully if it wasn't running
                     # (e.g., if unpausing via seek or if it stopped for some reason)
                     # Cancel any existing loop first to avoid duplicates
                     if self.after_id_progress:
                         self.root.after_cancel(self.after_id_progress)
                         self.after_id_progress = None
                     # Start a new update loop if we are now playing
                     if self.playing:
                         self.update_progress()

                 # --- Error Handling ---
                 # Catch Pygame-specific errors during play operation
                 except pygame.error as e:
                     messagebox.showerror("Seek Error", f"Pygame error during seek:\n{e}")
                     # Optionally, try to reset state or stop music here if seek fails badly
                     # self.stop_music()
                 # Catch any other unexpected errors during calculation or UI updates
                 except Exception as e:
                     messagebox.showerror("Seek Error", f"An unexpected error occurred during seek:\n{e}")
             else:
                 print("Cannot seek: Song length unknown.")
        else:
             print("Cannot seek: No song loaded or playing.")

    # ### ADDED: Toggle shuffle mode
    def toggle_shuffle(self):
        self.shuffle_on = not self.shuffle_on
        if self.shuffle_on:
            self.shuffle_button.config(image=self.images.get('shuffle_on'))
            # ### MODIFICATION: Use ttk 'selected' state for visual feedback
            self.shuffle_button.state(['selected'])
            self._apply_shuffle()
            print("Shuffle ON")
        else:
            self.shuffle_button.config(image=self.images.get('shuffle_off'))
            # ### MODIFICATION: Clear ttk 'selected' state
            self.shuffle_button.state(['!selected'])
            self.shuffled_indices = [] # Clear shuffled list
            print("Shuffle OFF")


    # ### ADDED: Apply shuffle logic (generates shuffled index list)
    def _apply_shuffle(self):
        if self.shuffle_on and self.playlist_paths:
            count = len(self.playlist_paths)
            self.shuffled_indices = list(range(count))
            random.shuffle(self.shuffled_indices)

            # Ensure the currently playing song (if any) is placed first in the shuffle order
            # to avoid immediately repeating it or skipping it weirdly.
            if self.current_index != -1 and self.current_index in self.shuffled_indices:
                current_shuffled_pos = self.shuffled_indices.index(self.current_index)
                # Swap current index to the position *after* the hypothetical 'current' play head
                # Or just keep it where it is, simpler logic:
                # Let's just remove it and re-insert at start for simplicity now
                self.shuffled_indices.pop(current_shuffled_pos)
                self.shuffled_indices.insert(0, self.current_index)
            print(f"Shuffled indices: {self.shuffled_indices}")


    # ### ADDED: Toggle repeat mode
    def toggle_repeat(self):
        self.repeat_mode = (self.repeat_mode + 1) % 3 # Cycle through 0, 1, 2
        if self.repeat_mode == REPEAT_OFF:
            self.repeat_button.config(image=self.images.get('repeat_off'))
            self.repeat_button.state(['!selected'])
            print("Repeat OFF")
        elif self.repeat_mode == REPEAT_ONE:
            self.repeat_button.config(image=self.images.get('repeat_one'))
            self.repeat_button.state(['selected']) # Use selected state
            print("Repeat ONE")
        elif self.repeat_mode == REPEAT_ALL:
            self.repeat_button.config(image=self.images.get('repeat_all'))
            self.repeat_button.state(['selected']) # Use selected state
            print("Repeat ALL")


    # ### ADDED: Play the next song based on shuffle/repeat state
    def play_next(self, force_next=False): # force_next used by repeat_all
        if not self.playlist_paths: return

        if self.repeat_mode == REPEAT_ONE and not force_next:
             # If repeat one is on, just replay the current song
             print("Repeat One active, replaying current track.")
             self.stop_music(internal_call=True)
             self._play_track_at_index(self.current_index)
             return

        count = len(self.playlist_paths)
        if count == 0: return

        next_index = -1

        if self.shuffle_on:
            if not self.shuffled_indices: self._apply_shuffle() # Ensure shuffled list exists

            # Find the *next* item in the shuffled list
            try:
                # Find where the *current* song is in the shuffle order
                current_shuffle_pos = self.shuffled_indices.index(self.current_index)
                next_shuffle_pos = (current_shuffle_pos + 1) % count
                next_index = self.shuffled_indices[next_shuffle_pos]
            except ValueError:
                # Current song wasn't in shuffle list (e.g., just added), play first shuffled
                if self.shuffled_indices:
                    next_index = self.shuffled_indices[0]
                else: return # No songs
            except IndexError:
                 return # Should not happen with modulo, but safety first

            # If shuffle and repeat_all are on, regenerate shuffle list when it loops
            if self.repeat_mode == REPEAT_ALL and next_shuffle_pos == 0 and current_shuffle_pos == count -1:
                print("Shuffle loop complete, reshuffling.")
                self._apply_shuffle()
                # Play the *new* first shuffled song
                next_index = self.shuffled_indices[0] if self.shuffled_indices else -1

        else: # Sequential playback
            next_index = (self.current_index + 1) % count
            # Handle end of list without repeat_all
            if next_index == 0 and self.current_index == count - 1 and self.repeat_mode != REPEAT_ALL:
                 print("Reached end of playlist sequentially, stopping.")
                 self.stop_music()
                 return # Do not loop back

        # Play the determined next track
        if next_index != -1:
             self.stop_music(internal_call=True)
             self._play_track_at_index(next_index)


    # ### ADDED: Play the previous song based on shuffle/repeat state
    def play_previous(self):
        if not self.playlist_paths: return

        count = len(self.playlist_paths)
        if count == 0: return

        prev_index = -1

        # Simple behavior: Go back 5 seconds if played > 5s, else go to previous track
        current_pos_ms = mixer.music.get_pos()
        if current_pos_ms > 5000: # If more than 5 seconds into the song
            print("Restarting current song.")
            self.stop_music(internal_call=True)
            self._play_track_at_index(self.current_index) # Just restart current
            return

        # Otherwise, go to the actual previous track
        if self.shuffle_on:
             if not self.shuffled_indices: self._apply_shuffle()
             try:
                 current_shuffle_pos = self.shuffled_indices.index(self.current_index)
                 prev_shuffle_pos = (current_shuffle_pos - 1 + count) % count # Wrap around correctly
                 prev_index = self.shuffled_indices[prev_shuffle_pos]
             except (ValueError, IndexError):
                 if self.shuffled_indices:
                     prev_index = self.shuffled_indices[-1] # Go to last shuffled if error
                 else: return
        else: # Sequential
            prev_index = (self.current_index - 1 + count) % count

        # Play the determined previous track
        if prev_index != -1:
             self.stop_music(internal_call=True)
             self._play_track_at_index(prev_index)


    # ### MODIFICATION: Utility to format time display
    def _format_time(self, seconds):
        if seconds < 0: seconds = 0
        minutes, seconds = divmod(int(seconds), 60)
        hours, minutes = divmod(minutes, 60)
        if hours > 0:
            return f"{hours}:{minutes:02}:{seconds:02}"
        else:
            return f"{minutes:02}:{seconds:02}"

    # ### ADDED: Update time label centrally
    def _update_time_display(self, current_seconds, total_seconds):
         current_time_str = self._format_time(current_seconds)
         total_time_str = self._format_time(total_seconds) if total_seconds > 0 else "--:--"
         self.time_label.config(text=f"{current_time_str} / {total_time_str}")
         # self.total_time_label maybe not needed if combined like this


    def on_close(self):
        print("Closing application...")
        self.save_config() # ### ADDED: Save config on close ###
        self.stop_music()
        self._cleanup_temp_file()
        try:
            mixer.quit()
        except Exception as e:
            print(f"Error during mixer quit: {e}")
        self.root.destroy()


# --- Main Execution ---
if __name__ == "__main__":
    # Create image directory if it doesn't exist
    if not os.path.exists(IMG_DIR):
        try:
            os.makedirs(IMG_DIR)
            messagebox.showinfo("Image Directory Created",
                              f"Image directory created at:\n{IMG_DIR}\n\nPlease place required button images (play, pause, stop, next, prev, shuffle_on/off, repeat_on/off/all) and a logo.png inside.")
        except OSError as e:
            messagebox.showerror("Error", f"Could not create image directory: {IMG_DIR}\n{e}")

    root = tk.Tk()
    # Catch potential TclError if system theme resources aren't found
    try:
        app = UltimateMediaPlayer(root)
        root.protocol("WM_DELETE_WINDOW", app.on_close)
        root.mainloop()
    except tk.TclError as e:
         messagebox.showerror("Theme Error", f"Failed to apply theme styles. Check your Tk/Tcl installation.\nError: {e}")
    except Exception as e:
         messagebox.showerror("Fatal Error", f"An unexpected error occurred on startup: {e}")