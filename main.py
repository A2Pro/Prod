import tkinter as tk
from tkinter import ttk, filedialog
import pygame
import os
import random
from mutagen.mp3 import MP3
import yt_dlp
import threading
import urllib.parse
from PIL import Image
import requests
from io import BytesIO
import time

class ModernMusicPlayer:
    def __init__(self, root):
        self.root = root
        self.root.title("Modern Music Player")
        self.root.configure(bg="#1E1E1E")
        
        # Enable touch events
        self.root.bind('<Button-1>', self.handle_click)
        self.root.bind('<ButtonRelease-1>', self.handle_release)
        self.root.bind('<B1-Motion>', self.handle_drag)
        
        pygame.mixer.init()
        
        self.current_song = None
        self.playlist = []
        self.is_playing = False
        self.timer_value = 0
        self.volume = 0.5
        self.song_position = 0
        self.songs_dir = os.path.join(os.getcwd(), "songs")
        self.last_timer_update = time.time()
        self.dragging = False
        
        self.current_song_var = tk.StringVar(value="No song playing")
        self.timer_var = tk.StringVar(value="00:00:00")
        self.current_time_var = tk.StringVar(value="0:00")
        self.total_time_var = tk.StringVar(value="0:00")
        self.url_var = tk.StringVar()
        self.progress_var = tk.DoubleVar(value=0)
        
        if not os.path.exists(self.songs_dir):
            os.makedirs(self.songs_dir)
            
        self.load_local_songs()
        
        self.setup_styles()
        self.create_gui()
        self.update_loop()

    def handle_click(self, event):
        """Handle both mouse clicks and touch events"""
        widget = event.widget
        if isinstance(widget, ttk.Scale):
            self.dragging = True
            # Calculate value based on click position
            self.update_scale_value(widget, event)

    def handle_release(self, event):
        """Handle release of mouse button or touch"""
        self.dragging = False
        widget = event.widget
        if isinstance(widget, ttk.Scale):
            self.update_scale_value(widget, event)

    def handle_drag(self, event):
        """Handle drag events for both mouse and touch"""
        if self.dragging:
            widget = event.widget
            if isinstance(widget, ttk.Scale):
                self.update_scale_value(widget, event)

    def update_scale_value(self, widget, event):
        """Update scale value based on click/touch position"""
        if widget == self.progress_bar:
            width = widget.winfo_width()
            if width > 0:  # Ensure widget has been drawn
                click_position = max(0, min(event.x, width))
                value = (click_position / width) * 100
                self.progress_var.set(value)
                self.seek_position(value)
        elif widget == self.volume_scale:
            width = widget.winfo_width()
            if width > 0:
                click_position = max(0, min(event.x, width))
                value = (click_position / width) * 100
                self.volume_scale.set(value)
                self.set_volume(value)

    def setup_styles(self):
        style = ttk.Style()
        
        # Define colors
        TEXT_COLOR = "#87CEEB"  
        BG_COLOR = "#1E1E1E"   
        ACCENT_COLOR = "#1DB954" 
        
        style.configure("TFrame", background=BG_COLOR)
        style.configure("TLabel", background=BG_COLOR, foreground=TEXT_COLOR)
        style.configure("TButton", 
                       padding=10,
                       background="#2D2D2D",
                       foreground=TEXT_COLOR,
                       font=('Helvetica', 10))
        style.configure("TEntry",
                       fieldbackground="#2D2D2D",
                       foreground=TEXT_COLOR,
                       insertcolor=TEXT_COLOR)
        style.configure("Horizontal.TScale",
                       background=BG_COLOR,
                       troughcolor="#4A4A4A",
                       lightcolor=ACCENT_COLOR,
                       darkcolor=ACCENT_COLOR)

        style.configure("Modern.TFrame", background=BG_COLOR)
        style.configure("Modern.TButton",
                       padding=10,
                       background="#2D2D2D",
                       foreground=TEXT_COLOR,
                       font=('Helvetica', 10))
        style.configure("Control.TButton",
                       padding=15,
                       background="#2D2D2D",
                       foreground=TEXT_COLOR,
                       font=('Helvetica', 14))
        style.configure("Modern.TLabel",
                       background=BG_COLOR,
                       foreground=TEXT_COLOR,
                       font=('Helvetica', 10))
        style.configure("Timer.TLabel",
                       background=BG_COLOR,
                       foreground=TEXT_COLOR,
                       font=('Helvetica', 24, 'bold'))
        
        self.root.option_add('*TEntry*foreground', TEXT_COLOR)
        self.root.option_add('*TEntry*background', '#2D2D2D')
        self.root.option_add('*TEntry*selectBackground', ACCENT_COLOR)
        self.root.option_add('*TEntry*selectForeground', TEXT_COLOR)

    def load_local_songs(self):
        if os.path.exists(self.songs_dir):
            self.playlist = [
                os.path.join(self.songs_dir, f) 
                for f in os.listdir(self.songs_dir) 
                if f.endswith('.mp3')
            ]
            if self.playlist:
                self.current_song = 0
                self.update_song_display()

    def update_song_display(self):
        if self.playlist and self.current_song is not None:
            song_name = os.path.basename(self.playlist[self.current_song])[:-4]
            self.current_song_var.set(f"Now playing: {song_name}")
        else:
            self.current_song_var.set("No song playing")

    def create_gui(self):
        self.main_frame = ttk.Frame(self.root, style="Modern.TFrame")
        self.main_frame.pack(expand=True, fill='both', padx=20, pady=20)

        url_frame = ttk.Frame(self.main_frame, style="Modern.TFrame")
        url_frame.pack(fill='x', pady=(0, 20))
        
        url_entry = ttk.Entry(url_frame, 
                            textvariable=self.url_var,
                            font=('Helvetica', 10),
                            style='TEntry')
        url_entry.pack(side='left', expand=True, fill='x', padx=(0, 10))
        
        browse_button = ttk.Button(url_frame, text="Browse",
                                 command=self.browse_files,
                                 style="Modern.TButton")
        browse_button.pack(side='right', padx=(0, 10))
        
        load_button = ttk.Button(url_frame, text="Load URL",
                               command=self.load_youtube_playlist,
                               style="Modern.TButton")
        load_button.pack(side='right')

        timer_frame = ttk.Frame(self.main_frame, style="Modern.TFrame")
        timer_frame.pack(fill='x', pady=20)
        
        ttk.Label(timer_frame, textvariable=self.timer_var,
                 style="Timer.TLabel").pack(side='top')

        timer_controls = ttk.Frame(timer_frame, style="Modern.TFrame")
        timer_controls.pack(side='top', pady=10)
        
        ttk.Button(timer_controls, text="◄", command=self.decrease_timer,
                  style="Control.TButton").pack(side='left', padx=5)
        ttk.Button(timer_controls, text="►", command=self.increase_timer,
                  style="Control.TButton").pack(side='left', padx=5)

        progress_frame = ttk.Frame(self.main_frame, style="Modern.TFrame")
        progress_frame.pack(fill='x', pady=20)
        
        ttk.Label(progress_frame, textvariable=self.current_time_var, 
                 style="Modern.TLabel").pack(side='left', padx=5)
        
        self.progress_bar = ttk.Scale(progress_frame, from_=0, to=100,
                                    orient='horizontal', variable=self.progress_var,
                                    style="Horizontal.TScale")
        self.progress_bar.pack(side='left', fill='x', expand=True)
        
        # Bind touch events specifically to the progress bar
        self.progress_bar.bind('<Button-1>', self.handle_click)
        self.progress_bar.bind('<ButtonRelease-1>', self.handle_release)
        self.progress_bar.bind('<B1-Motion>', self.handle_drag)
        
        ttk.Label(progress_frame, textvariable=self.total_time_var, 
                 style="Modern.TLabel").pack(side='left', padx=5)

        controls_frame = ttk.Frame(self.main_frame, style="Modern.TFrame")
        controls_frame.pack(fill='x', pady=20)
        
        ttk.Button(controls_frame, text="⏮", command=self.previous_song,
                  style="Control.TButton").pack(side='left', expand=True)
        self.play_button = ttk.Button(controls_frame, text="▶",
                                    command=self.toggle_play,
                                    style="Control.TButton")
        self.play_button.pack(side='left', expand=True)
        ttk.Button(controls_frame, text="⏭", command=self.next_song,
                  style="Control.TButton").pack(side='left', expand=True)
        ttk.Button(controls_frame, text="🔀", command=self.shuffle_playlist,
                  style="Control.TButton").pack(side='left', expand=True)

        volume_frame = ttk.Frame(self.main_frame, style="Modern.TFrame")
        volume_frame.pack(fill='x', pady=20)
        
        ttk.Label(volume_frame, text="🔊", style="Modern.TLabel").pack(side='left')
        self.volume_scale = ttk.Scale(volume_frame, from_=0, to=100,
                                    orient='horizontal',
                                    style="Horizontal.TScale")
        self.volume_scale.set(50)
        self.volume_scale.pack(side='left', expand=True, fill='x', padx=10)
        
        # Bind touch events to the volume scale
        self.volume_scale.bind('<Button-1>', self.handle_click)
        self.volume_scale.bind('<ButtonRelease-1>', self.handle_release)
        self.volume_scale.bind('<B1-Motion>', self.handle_drag)

        ttk.Label(self.main_frame, textvariable=self.current_song_var,
                 style="Modern.TLabel", wraplength=400).pack(pady=10)

    def browse_files(self):
        files = filedialog.askopenfilenames(
            title="Select MP3 Files",
            filetypes=[("MP3 files", "*.mp3")]
        )
        if files:
            for file in files:
                filename = os.path.basename(file)
                destination = os.path.join(self.songs_dir, filename)
                with open(file, 'rb') as src, open(destination, 'wb') as dst:
                    dst.write(src.read())
            
            self.load_local_songs()

    def load_youtube_playlist(self):
        url = self.url_var.get()
        if not url:
            return
            
        def download_thread():
            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'outtmpl': os.path.join(self.songs_dir, '%(title)s.%(ext)s'),
            }
            
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.extract_info(url, download=True)
                    self.root.after(0, self.load_local_songs)
            
            except Exception as e:
                print(f"Error downloading playlist: {e}")

        threading.Thread(target=download_thread, daemon=True).start()

    def toggle_play(self):
        if not self.playlist:
            return
            
        if self.is_playing:
            self.song_position = pygame.mixer.music.get_pos()
            pygame.mixer.music.pause()
            self.play_button.configure(text="▶")
        else:
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.unpause()
            else:
                self.play_current_song()
            self.play_button.configure(text="⏸")
        
        self.is_playing = not self.is_playing

    def play_current_song(self):
        if not self.playlist:
            return
            
        try:
            song_path = self.playlist[self.current_song]
            pygame.mixer.music.load(song_path)
            pygame.mixer.music.play(start=self.song_position / 1000.0 if self.song_position > 0 else 0)
            self.update_song_display()
            self.is_playing = True
            self.play_button.configure(text="⏸")
        except Exception as e:
            print(f"Error playing song: {e}")

    def next_song(self):
        if not self.playlist:
            return
            
        self.song_position = 0
        self.current_song = (self.current_song + 1) % len(self.playlist)
        self.play_current_song()

    def previous_song(self):
        if not self.playlist:
            return
            
        self.song_position = 0
        self.current_song = (self.current_song - 1) % len(self.playlist)
        self.play_current_song()

    def shuffle_playlist(self):
        if not self.playlist:
            return
            
        current = self.playlist[self.current_song]
        random.shuffle(self.playlist)
        self.current_song = self.playlist.index(current)

    def set_volume(self, value):
        self.volume = float(value) / 100
        pygame.mixer.music.set_volume(self.volume)
    def increase_timer(self):
        self.timer_value += 60
        self.update_timer_display()

    def decrease_timer(self):
        self.timer_value = max(0, self.timer_value - 60)
        self.update_timer_display()

    def update_timer_display(self):
        hours = self.timer_value // 3600
        minutes = (self.timer_value % 3600) // 60
        seconds = self.timer_value % 60
        self.timer_var.set(f"{hours:02d}:{minutes:02d}:{seconds:02d}")

    def seek_position(self, value):
        """Seek to position in song when progress bar is dragged"""
        if self.playlist and self.current_song is not None:
            try:
                value = float(value)
                audio = MP3(self.playlist[self.current_song])
                total_length = audio.info.length
                position = (value / 100) * total_length
                
                pygame.mixer.music.play(start=position)
                if not self.is_playing:
                    pygame.mixer.music.pause()
            except:
                pass

    def update_loop(self):
        if self.timer_value > 0 and time.time() - self.last_timer_update >= 1:
            self.timer_value -= 1
            self.update_timer_display()
            self.last_timer_update = time.time()
            
            if self.timer_value == 0:
                pygame.mixer.music.stop()
                self.is_playing = False
                self.play_button.configure(text="▶")
                self.song_position = 0

        # Update progress bar (10 times per second)
        if self.is_playing and pygame.mixer.music.get_busy():
            current_pos = pygame.mixer.music.get_pos() / 1000 
            total_length = 0
            
            if self.playlist and self.current_song is not None:
                try:
                    audio = MP3(self.playlist[self.current_song])
                    total_length = audio.info.length
                    progress = (current_pos / total_length) * 100
                    self.progress_var.set(progress)
                    
                    self.current_time_var.set(f"{int(current_pos // 60)}:{int(current_pos % 60):02d}")
                    self.total_time_var.set(f"{int(total_length // 60)}:{int(total_length % 60):02d}")
                except:
                    pass
        
        if self.is_playing and not pygame.mixer.music.get_busy():
            self.song_position = 0
            self.next_song()
        
        self.root.after(100, self.update_loop)  

def main():
    root = tk.Tk()
    root.configure(bg="#1E1E1E")
    app = ModernMusicPlayer(root)
    root.minsize(400, 600)
    root.mainloop()

if __name__ == "__main__":
    main()