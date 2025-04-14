# 🎵 Ultimate Music Player

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

![Application Screenshot](portray/application.jpg)

A feature-rich desktop music player built with Python, Tkinter, and Pygame, featuring multiple format support, playlist management, theme selection, and an aesthetic visualizer.

## ✨ Features

-   **GUI:** Modern interface built with Tkinter and ttk, using a responsive grid layout.
-   **Audio Playback:** Powered by `pygame.mixer`.
-   **Multi-Format Support:**
    -   Plays MP3, WAV, OGG directly (via Pygame).
    -   Supports M4A, FLAC, Opus, AAC, MP4 audio, and more by converting to temporary WAV files using `pydub` (requires **FFmpeg**).
    -   Includes a check for FFmpeg availability on startup.
-   **Playback Controls:**
    -   Play / Pause / Stop
    -   Next / Previous Track
    -   Seekable Progress Bar
    -   Volume Control Slider
-   **Playlist Management:**
    -   Add individual audio files.
    -   Add all supported audio files from a folder.
    -   Remove selected song.
    -   Clear entire playlist.
    -   Save current playlist to a `.ump` (JSON) file.
    -   Load playlist from a `.ump` file (checks for file existence).
-   **Playback Modes:**
    -   Shuffle mode toggle.
    -   Repeat modes: Off, Repeat Single Song, Repeat All.
-   **Metadata Display:** Shows Title, Artist, and Duration (using `mutagen` with `pydub` fallback for duration).
-   **Visualizer:** Includes a basic aesthetic circular visualizer (movement based on time, not audio frequency).
-   **Theming:**
    -   Selectable UI themes (e.g., Dark, Light, Blue) via the "Options" menu.
    -   Remembers the last selected theme between sessions (saved in `player_config.json`).
-   **Robustness:** Includes error handling for missing files, decoding issues, and missing dependencies. Cleans up temporary files automatically.

## ⚙️ Dependencies

**Python Libraries:**

* `pygame`: For audio playback.
* `Pillow` (PIL Fork): For handling images (button icons, logo).
* `pydub`: For converting non-native audio formats (relies on FFmpeg).
* `mutagen`: For reading audio metadata (tags).

**External Software:**

* **FFmpeg:** **Required** for playing formats like M4A, MP4, FLAC, AAC, Opus, etc.
    * You must install FFmpeg separately on your system.
    * Ensure the FFmpeg executable is added to your system's **PATH** environment variable so `pydub` can find it.
    * Downloads: [FFmpeg Official Site](https://ffmpeg.org/download.html) or pre-built binaries (e.g., from [gyan.dev](https://www.gyan.dev/ffmpeg/builds/) for Windows).

## 🚀 Installation

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/yourusername/UltimateMusicPlayer.git](https://github.com/yourusername/UltimateMusicPlayer.git)
    cd UltimateMusicPlayer
    ```
    *(Replace `yourusername` with your actual GitHub username)*

2.  **Install FFmpeg:** Download and install FFmpeg for your operating system and make sure it's added to your system's PATH.

3.  **Create a virtual environment (Recommended):**
    ```bash
    python -m venv venv
    # Activate the environment (Windows)
    .\venv\Scripts\activate
    # Activate the environment (macOS/Linux)
    source venv/bin/activate
    ```

4.  **Install Python libraries:**
    * Create a `requirements.txt` file with the following content:
        ```txt
        pygame
        Pillow
        pydub
        mutagen
        ```
    * Install the requirements:
        ```bash
        pip install -r requirements.txt
        ```

5.  **Add Images:** Create a folder named `proj_img` in the project directory and place the necessary `.png` files inside (e.g., `play_button.png`, `pause_button.png`, `logo.png`, etc. - see `load_images` function in the code for required names).

## 💻 Usage

Make sure your virtual environment is activated. Then run the player:

```bash
python Music_player.py

