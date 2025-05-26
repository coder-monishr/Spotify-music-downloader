import os
import threading
import tkinter as tk
from tkinter import ttk, messagebox
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import yt_dlp


SPOTIPY_CLIENT_ID = '3c87f4b17bee480b99b899446e96ceea'
SPOTIPY_CLIENT_SECRET = 'b22afe6f6fe349428b457615f669cb8c'
SPOTIPY_REDIRECT_URI = 'http://127.0.0.1:8888/callback'
SCOPE = 'playlist-read-private'
DOWNLOAD_DIR = 'downloads'


def login_to_spotify():
    return spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id=SPOTIPY_CLIENT_ID,
        client_secret=SPOTIPY_CLIENT_SECRET,
        redirect_uri=SPOTIPY_REDIRECT_URI,
        scope=SCOPE
    ))


def get_user_playlists(sp):
    playlists = sp.current_user_playlists()
    return [(pl['name'], pl['id']) for pl in playlists['items']]


def get_tracks(sp, playlist_id):
    results = sp.playlist_tracks(playlist_id)
    tracks = results['items']
    songs = []
    for item in tracks:
        track = item['track']
        name = track['name']
        artist = track['artists'][0]['name']
        songs.append(f"{name} - {artist}")
    return songs


def download_song(query, log_func):
    if not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR)

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'{DOWNLOAD_DIR}/%(title)s.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            ydl.download([f"ytsearch1:{query}"])
            log_func(f"✅ Downloaded: {query}")
        except Exception as e:
            log_func(f"❌ Failed: {query} — {e}")


class SpotifyDownloaderApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("🎧 Spotify Playlist Downloader")
        self.geometry("620x460")
        self.resizable(False, False)

        self.sp = None
        self.playlists = []
        self.filtered_playlists = []

        self.create_widgets()

    def create_widgets(self):
        tk.Label(self, text="Spotify Playlist Downloader", font=("Helvetica", 16, "bold")).pack(pady=10)

        self.login_button = tk.Button(self, text="Login to Spotify", command=self.spotify_login)
        self.login_button.pack()

        self.search_label = tk.Label(self, text="Search Playlists:")
        self.search_entry = tk.Entry(self, width=50)
        self.search_entry.bind("<KeyRelease>", self.filter_playlists)

        self.playlist_label = tk.Label(self, text="Select Playlist:")
        self.playlist_dropdown = ttk.Combobox(self, state="readonly")
        self.download_button = tk.Button(self, text="Download Playlist", command=self.download_selected_playlist, state="disabled")

        self.search_label.pack(pady=3)
        self.search_entry.pack(pady=3)
        self.playlist_label.pack(pady=3)
        self.playlist_dropdown.pack(pady=5)
        self.download_button.pack(pady=10)

        self.log_output = tk.Text(self, height=12, width=72)
        self.log_output.pack(pady=10)
        self.log_output.configure(state='disabled')

    def spotify_login(self):
        self.log("🔐 Logging into Spotify...")
        try:
            self.sp = login_to_spotify()
            self.playlists = get_user_playlists(self.sp)
            self.filtered_playlists = self.playlists
            self.update_dropdown()
            self.download_button.config(state="normal")
            self.log("✅ Login successful. You can now search and select a playlist.")
        except Exception as e:
            self.log(f"❌ Login failed: {e}")
            messagebox.showerror("Login Error", str(e))

    def filter_playlists(self, event=None):
        keyword = self.search_entry.get().lower()
        self.filtered_playlists = [pl for pl in self.playlists if keyword in pl[0].lower()]
        self.update_dropdown()

    def update_dropdown(self):
        self.playlist_dropdown['values'] = [name for name, _ in self.filtered_playlists]
        if self.filtered_playlists:
            self.playlist_dropdown.current(0)

    def download_selected_playlist(self):
        idx = self.playlist_dropdown.current()
        if idx == -1 or not self.filtered_playlists:
            messagebox.showwarning("No Playlist", "Please select a playlist first.")
            return

        playlist_name, playlist_id = self.filtered_playlists[idx]
        self.log(f"\n🎵 Fetching playlist: {playlist_name}")
        threading.Thread(target=self.download_playlist_thread, args=(playlist_id, playlist_name), daemon=True).start()

    def download_playlist_thread(self, playlist_id, playlist_name):
        try:
            songs = get_tracks(self.sp, playlist_id)
            self.log(f"📥 Found {len(songs)} tracks. Starting download...\n")
            for song in songs:
                self.log(f"🔍 Searching: {song}")
                download_song(song, self.log)
            self.log(f"\n✅ Playlist '{playlist_name}' downloaded successfully to '{DOWNLOAD_DIR}'")
        except Exception as e:
            self.log(f"❌ Error: {e}")
            messagebox.showerror("Download Error", str(e))

    def log(self, message):
        self.log_output.configure(state='normal')
        self.log_output.insert(tk.END, message + "\n")
        self.log_output.see(tk.END)
        self.log_output.configure(state='disabled')


if __name__ == "__main__":
    app = SpotifyDownloaderApp()
    app.mainloop()
