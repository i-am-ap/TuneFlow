# # # app.py
# # from dotenv import load_dotenv
# # import os
# # import threading
# # import uuid
# # from flask import Flask, request, jsonify, send_from_directory
# # from flask_cors import CORS
# # from yt_dlp import YoutubeDL
# # from spotipy import Spotify
# # from spotipy.oauth2 import SpotifyClientCredentials
# # from mutagen.easyid3 import EasyID3

# # load_dotenv()  # load variables from .env

# # # Read Spotify keys from environment (do NOT hardcode in production)
# # SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
# # SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
# # if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
# #     raise RuntimeError('Set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET environment variables')

# # sp = Spotify(auth_manager=SpotifyClientCredentials(
# #     client_id=SPOTIFY_CLIENT_ID,
# #     client_secret=SPOTIFY_CLIENT_SECRET
# # ))

# # # 🔥 CHANGED: use SAVE_PATH consistently for both download storage and listing
# # SAVE_PATH = os.getenv('SAVE_PATH', os.path.join(os.getcwd(), 'downloads'))
# # os.makedirs(SAVE_PATH, exist_ok=True)

# # app = Flask(__name__)
# # CORS(app)

# # # In-memory job store. For production, use Redis or a database.
# # JOBS = {}

# # # 🔥 CHANGED: helper to search YouTube via yt-dlp instead of youtube-search-python
# # def search_youtube(query: str) -> str:
# #     ydl_opts = {
# #         "quiet": True,
# #         "skip_download": True,
# #         "default_search": "ytsearch1",  # first result only
# #     }
# #     with YoutubeDL(ydl_opts) as ydl:
# #         info = ydl.extract_info(query, download=False)
# #         if "entries" in info and info["entries"]:
# #             return info["entries"][0].get("webpage_url")
# #         return info.get("webpage_url")


# # def progress_hook(d, job_id, idx):
# #     job = JOBS.get(job_id)
# #     if not job:
# #         return
# #     entry = job['jobs'][idx]
# #     status = d.get('status')
# #     if status == 'downloading':
# #         total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
# #         downloaded = d.get('downloaded_bytes') or 0
# #         try:
# #             pct = int(downloaded / total * 100) if total else 0
# #         except Exception:
# #             pct = 0
# #         entry['progress'] = pct
# #         if d.get('eta'):
# #             entry['message'] = f"ETA: {d.get('eta')}"
# #     elif status == 'finished':
# #         entry['progress'] = 85
# #         entry['message'] = 'Postprocessing'


# # def worker(job_id, songs):
# #     job = JOBS[job_id]
# #     try:
# #         for idx, song in enumerate(songs):
# #             entry = job['jobs'][idx]
# #             entry['status'] = 'searching'
# #             job['state'] = 'running'

# #             # Spotify search
# #             try:
# #                 results = sp.search(q=song, type='track', limit=1)
# #                 if results['tracks']['items']:
# #                     track = results['tracks']['items'][0]
# #                     title = track['name']
# #                     artist = track['artists'][0]['name']
# #                     album = track['album']['name']
# #                     release_date = track['album']['release_date']
# #                     entry['message'] = f'Found: {title} - {artist}'
# #                 else:
# #                     entry['status'] = 'not found'
# #                     entry['message'] = 'Not found on Spotify'
# #                     entry['progress'] = 100
# #                     continue
# #             except Exception as e:
# #                 entry['status'] = 'error'
# #                 entry['message'] = f'Spotify error: {e}'
# #                 continue

# #             # YouTube search & download
# #             entry['status'] = 'downloading'
# #             try:
# #                 url = search_youtube(f"{title} {artist}")

# #                 out_file = os.path.join(SAVE_PATH, f"{title} - {artist}.%(ext)s")
# #                 ydl_opts = {
# #                     'format': 'bestaudio/best',
# #                     'outtmpl': out_file,
# #                     'postprocessors': [{
# #                         'key': 'FFmpegExtractAudio',
# #                         'preferredcodec': 'mp3',
# #                         'preferredquality': '192',
# #                     }],
# #                     'quiet': True,
# #                     'progress_hooks': [
# #                         lambda d, job_id=job_id, idx=idx: progress_hook(d, job_id, idx)
# #                     ]
# #                 }

# #                 with YoutubeDL(ydl_opts) as ydl:
# #                     ydl.download([url])

# #                 mp3_file = os.path.join(SAVE_PATH, f"{title} - {artist}.mp3")
# #                 if os.path.exists(mp3_file):
# #                     try:
# #                         audio = EasyID3(mp3_file)
# #                     except Exception:
# #                         # create tags if missing
# #                         from mutagen.id3 import ID3, TIT2, TPE1, TALB, TDRC
# #                         id3 = ID3()
# #                         id3.add(TIT2(encoding=3, text=title))
# #                         id3.add(TPE1(encoding=3, text=artist))
# #                         id3.add(TALB(encoding=3, text=album))
# #                         id3.add(TDRC(encoding=3, text=release_date))
# #                         id3.save(mp3_file)
# #                     else:
# #                         audio['title'] = title
# #                         audio['artist'] = artist
# #                         audio['album'] = album
# #                         audio['date'] = release_date
# #                         audio.save()

# #                     entry['status'] = 'done'
# #                     entry['message'] = 'Saved with metadata'
# #                     entry['progress'] = 100
# #                 else:
# #                     entry['status'] = 'error'
# #                     entry['message'] = 'MP3 not found after download'
# #             except Exception as e:
# #                 entry['status'] = 'error'
# #                 entry['message'] = f'YT download error: {e}'

# #         job['state'] = 'done'
# #     except Exception as e:
# #         job['state'] = 'failed'
# #         job['error'] = str(e)


# # @app.route('/api/download', methods=['POST'])
# # def api_download():
# #     data = request.json or {}
# #     songs = data.get('songs') or []
# #     if not songs:
# #         return jsonify({'error': 'no songs provided'}), 400

# #     job_id = str(uuid.uuid4())
# #     JOBS[job_id] = {
# #         'state': 'queued',
# #         'jobs': [{'name': s, 'status': 'queued', 'progress': 0, 'message': ''} for s in songs]
# #     }

# #     t = threading.Thread(target=worker, args=(job_id, songs), daemon=True)
# #     t.start()

# #     return jsonify({'job_id': job_id, 'initial': JOBS[job_id]['jobs']})


# # @app.route('/api/status/<job_id>')
# # def api_status(job_id):
# #     job = JOBS.get(job_id)
# #     if not job:
# #         return jsonify({'error': 'job not found'}), 404
# #     return jsonify({'state': job['state'], 'jobs': job['jobs']})


# # # 🔥 CHANGED: single, canonical files endpoint that supports ?order=latest|oldest
# # @app.route('/api/files')
# # def api_files():
# #     order = request.args.get('order', 'latest')  # 'latest' or 'oldest'
# #     try:
# #         files = [f for f in os.listdir(SAVE_PATH) if f.lower().endswith('.mp3')]
# #         # sort by modification time
# #         files.sort(key=lambda f: os.path.getmtime(os.path.join(SAVE_PATH, f)), reverse=(order == 'latest'))
# #     except Exception:
# #         files = []
# #     # return object with files key (frontend expects this)
# #     return jsonify({'files': files})


# # @app.route('/api/file/<path:filename>')
# # def api_file(filename):
# #     return send_from_directory(SAVE_PATH, filename, as_attachment=True)


# # if __name__ == '__main__':
# #     # For development only. Use a proper WSGI server in production.
# #     PORT = int(os.getenv('PORT',  7860))   # default 7860 for local server
# #     # app.run(host='0.0.0.0', port=7860, debug=True)
# #     app.run(host='0.0.0.0', port=PORT, debug=True)



















# app.py
from dotenv import load_dotenv
import os
import threading
import uuid
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from yt_dlp import YoutubeDL
from spotipy import Spotify
from spotipy.oauth2 import SpotifyClientCredentials
from mutagen.easyid3 import EasyID3

# -----------------------------
# Load environment variables
# -----------------------------
BASE_DIR = os.getcwd()
load_dotenv()  # load local .env if exists

# Detect environment
IS_LOCAL = os.path.exists(os.path.join(BASE_DIR, '.env'))

# -----------------------------
# Spotify setup
# -----------------------------
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')

if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
    if IS_LOCAL:
        raise RuntimeError(
            "Set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET in your local .env"
        )
    else:
        # In production, fail gracefully
        print("⚠️ Warning: Spotify credentials missing! Spotify search will fail.")
        SPOTIFY_CLIENT_ID = None
        SPOTIFY_CLIENT_SECRET = None

sp = None
if SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET:
    sp = Spotify(auth_manager=SpotifyClientCredentials(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET
    ))

# -----------------------------
# Download folder setup
# -----------------------------
LOCAL_DOWNLOADS = os.path.join(BASE_DIR, "downloads")
PROD_DOWNLOADS = os.path.join(BASE_DIR, "downloads_prod")

SAVE_PATH = LOCAL_DOWNLOADS if IS_LOCAL else PROD_DOWNLOADS
os.makedirs(SAVE_PATH, exist_ok=True)

# -----------------------------
# Flask app
# -----------------------------
app = Flask(__name__)
# CORS(app)
# allow both local and production frontend
# CORS(app, resources={r"/api/*": {"origins": [
#     "http://localhost:5173",  
#     "https://tune-flow-git-main-i-am-aps-projects.vercel.app"
# ]}})

CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)


# In-memory job store
JOBS = {}

# -----------------------------
# Helpers
# -----------------------------
def search_youtube(query: str) -> str:
    ydl_opts = {
        "quiet": True,
        "skip_download": True,
        "default_search": "ytsearch1",
    }
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(query, download=False)
        if "entries" in info and info["entries"]:
            return info["entries"][0].get("webpage_url")
        return info.get("webpage_url")


def progress_hook(d, job_id, idx):
    job = JOBS.get(job_id)
    if not job:
        return
    entry = job['jobs'][idx]
    status = d.get('status')
    if status == 'downloading':
        total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
        downloaded = d.get('downloaded_bytes') or 0
        try:
            pct = int(downloaded / total * 100) if total else 0
        except Exception:
            pct = 0
        entry['progress'] = pct
        if d.get('eta'):
            entry['message'] = f"ETA: {d.get('eta')}"
    elif status == 'finished':
        entry['progress'] = 85
        entry['message'] = 'Postprocessing'


def worker(job_id, songs):
    job = JOBS[job_id]
    try:
        for idx, song in enumerate(songs):
            entry = job['jobs'][idx]
            entry['status'] = 'searching'
            job['state'] = 'running'

            # Spotify search
            title = artist = album = release_date = None
            if sp:
                try:
                    results = sp.search(q=song, type='track', limit=1)
                    if results['tracks']['items']:
                        track = results['tracks']['items'][0]
                        title = track['name']
                        artist = track['artists'][0]['name']
                        album = track['album']['name']
                        release_date = track['album']['release_date']
                        entry['message'] = f'Found: {title} - {artist}'
                    else:
                        entry['status'] = 'not found'
                        entry['message'] = 'Not found on Spotify'
                        entry['progress'] = 100
                        continue
                except Exception as e:
                    entry['status'] = 'error'
                    entry['message'] = f'Spotify error: {e}'
                    continue
            else:
                # fallback: use search term as title
                title = artist = song
                entry['message'] = f'Using search term: {song}'

            # YouTube search & download
            entry['status'] = 'downloading'
            try:
                url = search_youtube(f"{title} {artist}")
                out_file = os.path.join(SAVE_PATH, f"{title} - {artist}.%(ext)s")
                ydl_opts = {
                    'format': 'bestaudio/best',
                    'outtmpl': out_file,
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }],
                    'quiet': True,
                    'progress_hooks': [
                        lambda d, job_id=job_id, idx=idx: progress_hook(d, job_id, idx)
                    ]
                }

                with YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])

                mp3_file = os.path.join(SAVE_PATH, f"{title} - {artist}.mp3")
                if os.path.exists(mp3_file):
                    try:
                        audio = EasyID3(mp3_file)
                    except Exception:
                        from mutagen.id3 import ID3, TIT2, TPE1, TALB, TDRC
                        id3 = ID3()
                        id3.add(TIT2(encoding=3, text=title))
                        id3.add(TPE1(encoding=3, text=artist))
                        id3.add(TALB(encoding=3, text=album or 'Unknown'))
                        id3.add(TDRC(encoding=3, text=release_date or ''))
                        id3.save(mp3_file)
                    else:
                        audio['title'] = title
                        audio['artist'] = artist
                        audio['album'] = album or 'Unknown'
                        audio['date'] = release_date or ''
                        audio.save()

                    entry['status'] = 'done'
                    entry['message'] = 'Saved with metadata'
                    entry['progress'] = 100
                else:
                    entry['status'] = 'error'
                    entry['message'] = 'MP3 not found after download'
            except Exception as e:
                entry['status'] = 'error'
                entry['message'] = f'YT download error: {e}'

        job['state'] = 'done'
    except Exception as e:
        job['state'] = 'failed'
        job['error'] = str(e)


# -----------------------------
# Routes
# -----------------------------
@app.route('/api/download', methods=['POST'])
def api_download():
    data = request.json or {}
    songs = data.get('songs') or []
    if not songs:
        return jsonify({'error': 'no songs provided'}), 400

    job_id = str(uuid.uuid4())
    JOBS[job_id] = {
        'state': 'queued',
        'jobs': [{'name': s, 'status': 'queued', 'progress': 0, 'message': ''} for s in songs]
    }

    t = threading.Thread(target=worker, args=(job_id, songs), daemon=True)
    t.start()

    return jsonify({'job_id': job_id, 'initial': JOBS[job_id]['jobs']})


@app.route('/api/status/<job_id>')
def api_status(job_id):
    job = JOBS.get(job_id)
    if not job:
        return jsonify({'error': 'job not found'}), 404
    return jsonify({'state': job['state'], 'jobs': job['jobs']})


@app.route('/api/files')
def api_files():
    order = request.args.get('order', 'latest')
    try:
        files = [f for f in os.listdir(SAVE_PATH) if f.lower().endswith('.mp3')]
        files.sort(key=lambda f: os.path.getmtime(os.path.join(SAVE_PATH, f)), reverse=(order == 'latest'))
    except Exception:
        files = []
    return jsonify({'files': files})


@app.route('/api/file/<path:filename>')
def api_file(filename):
    return send_from_directory(SAVE_PATH, filename, as_attachment=True)


# -----------------------------
# Run app
# -----------------------------
if __name__ == '__main__':
    PORT = int(os.getenv('PORT', 7860))
    # app.run(host='0.0.0.0', port=PORT, debug=IS_LOCAL)
    app.run(host="0.0.0.0", port=PORT, debug=os.getenv("FLASK_DEBUG", "1") == "1")
