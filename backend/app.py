# # # # app.py
# # # from dotenv import load_dotenv
# # # import os
# # # import threading
# # # import uuid
# # # from flask import Flask, request, jsonify, send_from_directory
# # # from flask_cors import CORS
# # # from yt_dlp import YoutubeDL
# # # from spotipy import Spotify
# # # from spotipy.oauth2 import SpotifyClientCredentials
# # # from mutagen.easyid3 import EasyID3

# # # load_dotenv()  # load variables from .env

# # # # Read Spotify keys from environment (do NOT hardcode in production)
# # # SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
# # # SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
# # # if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
# # #     raise RuntimeError('Set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET environment variables')

# # # sp = Spotify(auth_manager=SpotifyClientCredentials(
# # #     client_id=SPOTIFY_CLIENT_ID,
# # #     client_secret=SPOTIFY_CLIENT_SECRET
# # # ))

# # # # 🔥 CHANGED: use SAVE_PATH consistently for both download storage and listing
# # # SAVE_PATH = os.getenv('SAVE_PATH', os.path.join(os.getcwd(), 'downloads'))
# # # os.makedirs(SAVE_PATH, exist_ok=True)

# # # app = Flask(__name__)
# # # CORS(app)

# # # # In-memory job store. For production, use Redis or a database.
# # # JOBS = {}

# # # # 🔥 CHANGED: helper to search YouTube via yt-dlp instead of youtube-search-python
# # # def search_youtube(query: str) -> str:
# # #     ydl_opts = {
# # #         "quiet": True,
# # #         "skip_download": True,
# # #         "default_search": "ytsearch1",  # first result only
# # #     }
# # #     with YoutubeDL(ydl_opts) as ydl:
# # #         info = ydl.extract_info(query, download=False)
# # #         if "entries" in info and info["entries"]:
# # #             return info["entries"][0].get("webpage_url")
# # #         return info.get("webpage_url")


# # # def progress_hook(d, job_id, idx):
# # #     job = JOBS.get(job_id)
# # #     if not job:
# # #         return
# # #     entry = job['jobs'][idx]
# # #     status = d.get('status')
# # #     if status == 'downloading':
# # #         total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
# # #         downloaded = d.get('downloaded_bytes') or 0
# # #         try:
# # #             pct = int(downloaded / total * 100) if total else 0
# # #         except Exception:
# # #             pct = 0
# # #         entry['progress'] = pct
# # #         if d.get('eta'):
# # #             entry['message'] = f"ETA: {d.get('eta')}"
# # #     elif status == 'finished':
# # #         entry['progress'] = 85
# # #         entry['message'] = 'Postprocessing'


# # # def worker(job_id, songs):
# # #     job = JOBS[job_id]
# # #     try:
# # #         for idx, song in enumerate(songs):
# # #             entry = job['jobs'][idx]
# # #             entry['status'] = 'searching'
# # #             job['state'] = 'running'

# # #             # Spotify search
# # #             try:
# # #                 results = sp.search(q=song, type='track', limit=1)
# # #                 if results['tracks']['items']:
# # #                     track = results['tracks']['items'][0]
# # #                     title = track['name']
# # #                     artist = track['artists'][0]['name']
# # #                     album = track['album']['name']
# # #                     release_date = track['album']['release_date']
# # #                     entry['message'] = f'Found: {title} - {artist}'
# # #                 else:
# # #                     entry['status'] = 'not found'
# # #                     entry['message'] = 'Not found on Spotify'
# # #                     entry['progress'] = 100
# # #                     continue
# # #             except Exception as e:
# # #                 entry['status'] = 'error'
# # #                 entry['message'] = f'Spotify error: {e}'
# # #                 continue

# # #             # YouTube search & download
# # #             entry['status'] = 'downloading'
# # #             try:
# # #                 url = search_youtube(f"{title} {artist}")

# # #                 out_file = os.path.join(SAVE_PATH, f"{title} - {artist}.%(ext)s")
# # #                 ydl_opts = {
# # #                     'format': 'bestaudio/best',
# # #                     'outtmpl': out_file,
# # #                     'postprocessors': [{
# # #                         'key': 'FFmpegExtractAudio',
# # #                         'preferredcodec': 'mp3',
# # #                         'preferredquality': '192',
# # #                     }],
# # #                     'quiet': True,
# # #                     'progress_hooks': [
# # #                         lambda d, job_id=job_id, idx=idx: progress_hook(d, job_id, idx)
# # #                     ]
# # #                 }

# # #                 with YoutubeDL(ydl_opts) as ydl:
# # #                     ydl.download([url])

# # #                 mp3_file = os.path.join(SAVE_PATH, f"{title} - {artist}.mp3")
# # #                 if os.path.exists(mp3_file):
# # #                     try:
# # #                         audio = EasyID3(mp3_file)
# # #                     except Exception:
# # #                         # create tags if missing
# # #                         from mutagen.id3 import ID3, TIT2, TPE1, TALB, TDRC
# # #                         id3 = ID3()
# # #                         id3.add(TIT2(encoding=3, text=title))
# # #                         id3.add(TPE1(encoding=3, text=artist))
# # #                         id3.add(TALB(encoding=3, text=album))
# # #                         id3.add(TDRC(encoding=3, text=release_date))
# # #                         id3.save(mp3_file)
# # #                     else:
# # #                         audio['title'] = title
# # #                         audio['artist'] = artist
# # #                         audio['album'] = album
# # #                         audio['date'] = release_date
# # #                         audio.save()

# # #                     entry['status'] = 'done'
# # #                     entry['message'] = 'Saved with metadata'
# # #                     entry['progress'] = 100
# # #                 else:
# # #                     entry['status'] = 'error'
# # #                     entry['message'] = 'MP3 not found after download'
# # #             except Exception as e:
# # #                 entry['status'] = 'error'
# # #                 entry['message'] = f'YT download error: {e}'

# # #         job['state'] = 'done'
# # #     except Exception as e:
# # #         job['state'] = 'failed'
# # #         job['error'] = str(e)


# # # @app.route('/api/download', methods=['POST'])
# # # def api_download():
# # #     data = request.json or {}
# # #     songs = data.get('songs') or []
# # #     if not songs:
# # #         return jsonify({'error': 'no songs provided'}), 400

# # #     job_id = str(uuid.uuid4())
# # #     JOBS[job_id] = {
# # #         'state': 'queued',
# # #         'jobs': [{'name': s, 'status': 'queued', 'progress': 0, 'message': ''} for s in songs]
# # #     }

# # #     t = threading.Thread(target=worker, args=(job_id, songs), daemon=True)
# # #     t.start()

# # #     return jsonify({'job_id': job_id, 'initial': JOBS[job_id]['jobs']})


# # # @app.route('/api/status/<job_id>')
# # # def api_status(job_id):
# # #     job = JOBS.get(job_id)
# # #     if not job:
# # #         return jsonify({'error': 'job not found'}), 404
# # #     return jsonify({'state': job['state'], 'jobs': job['jobs']})


# # # # 🔥 CHANGED: single, canonical files endpoint that supports ?order=latest|oldest
# # # @app.route('/api/files')
# # # def api_files():
# # #     order = request.args.get('order', 'latest')  # 'latest' or 'oldest'
# # #     try:
# # #         files = [f for f in os.listdir(SAVE_PATH) if f.lower().endswith('.mp3')]
# # #         # sort by modification time
# # #         files.sort(key=lambda f: os.path.getmtime(os.path.join(SAVE_PATH, f)), reverse=(order == 'latest'))
# # #     except Exception:
# # #         files = []
# # #     # return object with files key (frontend expects this)
# # #     return jsonify({'files': files})


# # # @app.route('/api/file/<path:filename>')
# # # def api_file(filename):
# # #     return send_from_directory(SAVE_PATH, filename, as_attachment=True)


# # # if __name__ == '__main__':
# # #     # For development only. Use a proper WSGI server in production.
# # #     PORT = int(os.getenv('PORT',  7860))   # default 7860 for local server
# # #     # app.run(host='0.0.0.0', port=7860, debug=True)
# # #     app.run(host='0.0.0.0', port=PORT, debug=True)



















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

# # # -----------------------------
# # # Load environment variables
# # # -----------------------------
# # BASE_DIR = os.getcwd()
# # load_dotenv()  # load local .env if exists

# # # Detect environment
# # IS_LOCAL = os.path.exists(os.path.join(BASE_DIR, '.env'))

# # # -----------------------------
# # # Spotify setup
# # # -----------------------------
# # SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
# # SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')

# # if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
# #     if IS_LOCAL:
# #         raise RuntimeError(
# #             "Set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET in your local .env"
# #         )
# #     else:
# #         # In production, fail gracefully
# #         print("⚠️ Warning: Spotify credentials missing! Spotify search will fail.")
# #         SPOTIFY_CLIENT_ID = None
# #         SPOTIFY_CLIENT_SECRET = None

# # sp = None
# # if SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET:
# #     sp = Spotify(auth_manager=SpotifyClientCredentials(
# #         client_id=SPOTIFY_CLIENT_ID,
# #         client_secret=SPOTIFY_CLIENT_SECRET
# #     ))

# # # -----------------------------
# # # Download folder setup
# # # -----------------------------
# # LOCAL_DOWNLOADS = os.path.join(BASE_DIR, "downloads")
# # PROD_DOWNLOADS = os.path.join(BASE_DIR, "downloads_prod")

# # SAVE_PATH = LOCAL_DOWNLOADS if IS_LOCAL else PROD_DOWNLOADS
# # os.makedirs(SAVE_PATH, exist_ok=True)

# # # -----------------------------
# # # Flask app
# # # -----------------------------
# # app = Flask(__name__)
# # # CORS(app)
# # # allow both local and production frontend
# # # CORS(app, resources={r"/api/*": {"origins": [
# # #     "http://localhost:5173",  
# # #     "https://tune-flow-seven.vercel.app"
# # # ]}})

# # # allow Vercel frontend + localhost for dev
# # CORS(app, resources={
# #     r"/api/*": {
# #         "origins": [
# #             "http://localhost:5173",
# #             "https://tune-flow-seven.vercel.app"
# #         ]
# #     }
# # })


# # # In-memory job store
# # JOBS = {}

# # # -----------------------------
# # # Helpers
# # # -----------------------------
# # def search_youtube(query: str) -> str:
# #     ydl_opts = {
# #         "quiet": True,
# #         "skip_download": True,
# #         "default_search": "ytsearch1",
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
# #             title = artist = album = release_date = None
# #             if sp:
# #                 try:
# #                     results = sp.search(q=song, type='track', limit=1)
# #                     if results['tracks']['items']:
# #                         track = results['tracks']['items'][0]
# #                         title = track['name']
# #                         artist = track['artists'][0]['name']
# #                         album = track['album']['name']
# #                         release_date = track['album']['release_date']
# #                         entry['message'] = f'Found: {title} - {artist}'
# #                     else:
# #                         entry['status'] = 'not found'
# #                         entry['message'] = 'Not found on Spotify'
# #                         entry['progress'] = 100
# #                         continue
# #                 except Exception as e:
# #                     entry['status'] = 'error'
# #                     entry['message'] = f'Spotify error: {e}'
# #                     continue
# #             else:
# #                 # fallback: use search term as title
# #                 title = artist = song
# #                 entry['message'] = f'Using search term: {song}'

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
# #                         from mutagen.id3 import ID3, TIT2, TPE1, TALB, TDRC
# #                         id3 = ID3()
# #                         id3.add(TIT2(encoding=3, text=title))
# #                         id3.add(TPE1(encoding=3, text=artist))
# #                         id3.add(TALB(encoding=3, text=album or 'Unknown'))
# #                         id3.add(TDRC(encoding=3, text=release_date or ''))
# #                         id3.save(mp3_file)
# #                     else:
# #                         audio['title'] = title
# #                         audio['artist'] = artist
# #                         audio['album'] = album or 'Unknown'
# #                         audio['date'] = release_date or ''
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


# # # -----------------------------
# # # Routes
# # # -----------------------------

# # @app.route("/")
# # def index():
# #     return "Flask backend running on Cloud Run"


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


# # @app.route('/api/files')
# # def api_files():
# #     order = request.args.get('order', 'latest')
# #     try:
# #         files = [f for f in os.listdir(SAVE_PATH) if f.lower().endswith('.mp3')]
# #         files.sort(key=lambda f: os.path.getmtime(os.path.join(SAVE_PATH, f)), reverse=(order == 'latest'))
# #     except Exception:
# #         files = []
# #     return jsonify({'files': files})


# # @app.route('/api/file/<path:filename>')
# # def api_file(filename):
# #     return send_from_directory(SAVE_PATH, filename, as_attachment=True)


# # # -----------------------------
# # # Run app
# # # -----------------------------
# # if __name__ == '__main__':
# #     PORT = int(os.getenv('PORT', 7860))
# #     # app.run(host='0.0.0.0', port=PORT, debug=IS_LOCAL)
# #     app.run(host="0.0.0.0", port=PORT, debug=os.getenv("FLASK_DEBUG", "1") == "1")











# # app.py — production-ready + dev friendly
# from dotenv import load_dotenv
# import os
# import threading
# import uuid
# import logging
# from flask import Flask, request, jsonify, send_from_directory
# from flask_cors import CORS
# import requests

# # ---------- logging ----------
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger("tuneflow-backend")

# # ---------- env / paths ----------
# BASE_DIR = os.getcwd()
# load_dotenv()  # load local .env if present
# IS_LOCAL = os.path.exists(os.path.join(BASE_DIR, ".env"))

# # allow overriding the production save path via env var
# SAVE_PATH_ENV = os.getenv("SAVE_PATH")
# LOCAL_DOWNLOADS = os.path.join(BASE_DIR, "downloads")
# PROD_DOWNLOADS = SAVE_PATH_ENV or os.path.join("/tmp", "downloads_prod")
# SAVE_PATH = LOCAL_DOWNLOADS if IS_LOCAL else PROD_DOWNLOADS
# os.makedirs(SAVE_PATH, exist_ok=True)

# # ---------- Spotify creds (optional in production) ----------
# SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
# SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
# _sp = None
# if SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET:
#     try:
#         # import here so startup failures are clearer
#         from spotipy import Spotify
#         from spotipy.oauth2 import SpotifyClientCredentials

#         _sp = Spotify(
#             auth_manager=SpotifyClientCredentials(
#                 client_id=SPOTIFY_CLIENT_ID, client_secret=SPOTIFY_CLIENT_SECRET
#             )
#         )
#         logger.info("Spotify client configured.")
#     except Exception as e:
#         logger.exception("Failed to initialize Spotify client: %s", e)
#         _sp = None
# else:
#     if IS_LOCAL:
#         # local dev: require creds (you can change this behavior if desired)
#         logger.error("Local run requires SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET in .env")
#         raise RuntimeError(
#             "Set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET in your local .env"
#         )
#     else:
#         logger.warning("Spotify credentials not found — fallback text-search used.")

# # ---------- Flask app + CORS ----------
# app = Flask(__name__)

# # FRONTEND origins: comma-separated list in env FRONTEND_ORIGINS (e.g. "http://localhost:5173,https://your-vercel-app.vercel.app")
# frontend_env = os.getenv("FRONTEND_ORIGINS", "")
# if frontend_env:
#     origins = [o.strip() for o in frontend_env.split(",") if o.strip()]
# else:
#     # safe default: allow local dev + allow any origin in PROD if explicitly set to "*"
#     origins = ["http://localhost:5173"]

# # allow wildcard if FRONTEND_ORIGINS = "*"
# if os.getenv("FRONTEND_ORIGINS") == "*":
#     CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)
# else:
#     CORS(app, resources={r"/api/*": {"origins": origins}}, supports_credentials=True)

# # ---------- in-memory store ----------
# JOBS = {}

# # ---------- helper functions ----------
# def ensure_cookies_file():
#     """
#     Downloads cookies.txt from COOKIES_URL env if not already present.
#     Returns path to cookies.txt or None if unavailable.
#     """
#     cookies_url = os.getenv("COOKIES_URL", "")
#     cookies_path = os.path.join(BASE_DIR, "cookies.txt")

#     if not cookies_url:
#         logger.warning("No COOKIES_URL set — running without cookies.")
#         return None

#     if not os.path.exists(cookies_path):
#         try:
#             logger.info("Downloading cookies file from %s", cookies_url)
#             r = requests.get(cookies_url, timeout=10)
#             r.raise_for_status()
#             with open(cookies_path, "wb") as f:
#                 f.write(r.content)
#             logger.info("Cookies file saved to %s", cookies_path)
#         except Exception as e:
#             logger.exception("Failed to download cookies: %s", e)
#             return None

#     return cookies_path



# def search_youtube(query: str) -> str:
#     """Return a YouTube webpage URL using yt-dlp's 'ytsearch1'"""
#     try:
#         # import inside function to avoid hard failure at import time if library missing
#         from yt_dlp import YoutubeDL
#     except Exception as e:
#         logger.exception("yt-dlp import failed: %s", e)
#         raise RuntimeError("yt-dlp not installed in environment")

#     opts = {"quiet": True, "skip_download": True, "default_search": "ytsearch1"}
#     with YoutubeDL(opts) as ydl:
#         info = ydl.extract_info(query, download=False)
#         if isinstance(info, dict) and "entries" in info and info["entries"]:
#             return info["entries"][0].get("webpage_url")
#         return info.get("webpage_url")


# def progress_hook(d, job_id, idx):
#     job = JOBS.get(job_id)
#     if not job:
#         return
#     entry = job["jobs"][idx]
#     status = d.get("status")
#     if status == "downloading":
#         total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
#         downloaded = d.get("downloaded_bytes") or 0
#         try:
#             pct = int(downloaded / total * 100) if total else 0
#         except Exception:
#             pct = 0
#         entry["progress"] = pct
#         if d.get("eta"):
#             entry["message"] = f"ETA: {d.get('eta')}"
#     elif status == "finished":
#         entry["progress"] = 85
#         entry["message"] = "Postprocessing"


# def worker(job_id, songs):
#     """Worker thread that searches + downloads and writes MP3s into SAVE_PATH"""
#     logger.info("Worker started for job %s (%d songs)", job_id, len(songs))
#     job = JOBS[job_id]
#     try:
#         for idx, song in enumerate(songs):
#             entry = job["jobs"][idx]
#             entry["status"] = "searching"
#             job["state"] = "running"

#             title = artist = album = release_date = None

#             # ------------------------------ Cookies for Youtube search ------------------------------
#             # If you have issues with YouTube blocking requests, consider using cookies.
#             cookies_file = ensure_cookies_file()
#             #--------------------------------------------------------------------

#             if _sp:
#                 try:
#                     results = _sp.search(q=song, type="track", limit=1)
#                     if results["tracks"]["items"]:
#                         track = results["tracks"]["items"][0]
#                         title = track["name"]
#                         artist = track["artists"][0]["name"]
#                         album = track["album"]["name"]
#                         release_date = track["album"]["release_date"]
#                         entry["message"] = f"Found: {title} - {artist}"
#                     else:
#                         entry["status"] = "not found"
#                         entry["message"] = "Not found on Spotify"
#                         entry["progress"] = 100
#                         continue
#                 except Exception as e:
#                     logger.exception("Spotify search failed for %s: %s", song, e)
#                     entry["status"] = "error"
#                     entry["message"] = f"Spotify error: {e}"
#                     continue
#             else:
#                 # fallback: use the input line as title+artist to search YouTube
#                 title = artist = song
#                 entry["message"] = f"Using search term: {song}"

#             entry["status"] = "downloading"
#             try:
#                 url = search_youtube(f"{title} {artist}")
#                 out_file = os.path.join(SAVE_PATH, f"{title} - {artist}.%(ext)s")
#                 ydl_opts = {
#                     "format": "bestaudio/best",
#                     "outtmpl": out_file,
#                     "cookiefile": cookies_file if cookies_file else None,  # <-- Cookies
#                     "postprocessors": [
#                         {
#                             "key": "FFmpegExtractAudio",
#                             "preferredcodec": "mp3",
#                             "preferredquality": "192",
#                         }
#                     ],
#                     "quiet": True,
#                     "progress_hooks": [
#                         lambda d, job_id=job_id, idx=idx: progress_hook(d, job_id, idx)
#                     ],
#                 }

#                 # download
#                 from yt_dlp import YoutubeDL  # local import
#                 logger.info("Using cookies file: %s", cookies_file if os.path.exists(cookies_file) else "None")        # to ensure cookies is being used
#                 with YoutubeDL(ydl_opts) as ydl:
#                     ydl.download([url])

#                 mp3_file = os.path.join(SAVE_PATH, f"{title} - {artist}.mp3")
#                 if os.path.exists(mp3_file):
#                     try:
#                         from mutagen.easyid3 import EasyID3

#                         audio = EasyID3(mp3_file)
#                         audio["title"] = title
#                         audio["artist"] = artist
#                         audio["album"] = album or "Unknown"
#                         audio["date"] = release_date or ""
#                         audio.save()
#                     except Exception:
#                         # fallback to writing minimal ID3 tags (import inside)
#                         try:
#                             from mutagen.id3 import ID3, TIT2, TPE1, TALB, TDRC

#                             id3 = ID3()
#                             id3.add(TIT2(encoding=3, text=title))
#                             id3.add(TPE1(encoding=3, text=artist))
#                             id3.add(TALB(encoding=3, text=album or "Unknown"))
#                             id3.add(TDRC(encoding=3, text=release_date or ""))
#                             id3.save(mp3_file)
#                         except Exception:
#                             logger.exception("Failed to write ID3 tags for %s", mp3_file)

#                     entry["status"] = "done"
#                     entry["message"] = "Saved with metadata"
#                     entry["progress"] = 100
#                 else:
#                     entry["status"] = "error"
#                     entry["message"] = "MP3 not found after download"
#             except Exception as e:
#                 logger.exception("Download error for %s: %s", song, e)
#                 entry["status"] = "error"
#                 entry["message"] = f"YT download error: {e}"

#         job["state"] = "done"
#     except Exception as e:
#         logger.exception("Worker crashed for job %s: %s", job_id, e)
#         job["state"] = "failed"
#         job["error"] = str(e)

# # ---------- routes ----------
# @app.route("/", methods=["GET"])
# def health():
#     return jsonify({"status": "ok", "message": "TuneFlow backend running"})

# @app.route("/api/download", methods=["POST"])
# def api_download():
#     data = request.json or {}
#     songs = data.get("songs") or []
#     if not songs:
#         return jsonify({"error": "no songs provided"}), 400

#     job_id = str(uuid.uuid4())
#     JOBS[job_id] = {
#         "state": "queued",
#         "jobs": [{"name": s, "status": "queued", "progress": 0, "message": ""} for s in songs],
#     }

#     t = threading.Thread(target=worker, args=(job_id, songs), daemon=True)
#     t.start()

#     return jsonify({"job_id": job_id, "initial": JOBS[job_id]["jobs"]})

# @app.route("/api/status/<job_id>")
# def api_status(job_id):
#     job = JOBS.get(job_id)
#     if not job:
#         return jsonify({"error": "job not found"}), 404
#     return jsonify({"state": job["state"], "jobs": job["jobs"]})

# @app.route("/api/files")
# def api_files():
#     order = request.args.get("order", "latest")
#     try:
#         files = [f for f in os.listdir(SAVE_PATH) if f.lower().endswith(".mp3")]
#         files.sort(key=lambda f: os.path.getmtime(os.path.join(SAVE_PATH, f)), reverse=(order=="latest"))
#     except Exception as e:
#         logger.exception("Failed to list files: %s", e)
#         files = []
#     return jsonify({"files": files})

# @app.route("/api/file/<path:filename>")
# def api_file(filename):
#     return send_from_directory(SAVE_PATH, filename, as_attachment=True)

# # ---------- run ----------
# if __name__ == "__main__":
#     port = int(os.environ.get("PORT", 7860))
#     debug = IS_LOCAL or os.getenv("FLASK_DEBUG", "0") == "1"
#     logger.info("Starting dev server on port %d (IS_LOCAL=%s, SAVE_PATH=%s)", port, IS_LOCAL, SAVE_PATH)
#     app.run(host="0.0.0.0", port=port, debug=debug)






# app.py — production-ready + dev friendly
from dotenv import load_dotenv
import os
import threading
import uuid
import logging
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import requests

# ---------- logging ----------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("tuneflow-backend")

# ---------- env / paths ----------
BASE_DIR = os.getcwd()
load_dotenv()  # load local .env if present
IS_LOCAL = os.path.exists(os.path.join(BASE_DIR, ".env"))

# allow overriding the production save path via env var
SAVE_PATH_ENV = os.getenv("SAVE_PATH")
LOCAL_DOWNLOADS = os.path.join(BASE_DIR, "downloads")
PROD_DOWNLOADS = SAVE_PATH_ENV or os.path.join("/tmp", "downloads_prod")
SAVE_PATH = LOCAL_DOWNLOADS if IS_LOCAL else PROD_DOWNLOADS
os.makedirs(SAVE_PATH, exist_ok=True)

# ---------- Spotify creds (optional in production) ----------
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
_sp = None
if SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET:
    try:
        from spotipy import Spotify
        from spotipy.oauth2 import SpotifyClientCredentials

        _sp = Spotify(
            auth_manager=SpotifyClientCredentials(
                client_id=SPOTIFY_CLIENT_ID, client_secret=SPOTIFY_CLIENT_SECRET
            )
        )
        logger.info("Spotify client configured.")
    except Exception as e:
        logger.exception("Failed to initialize Spotify client: %s", e)
        _sp = None
else:
    if IS_LOCAL:
        logger.error("Local run requires SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET in .env")
        raise RuntimeError(
            "Set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET in your local .env"
        )
    else:
        logger.warning("Spotify credentials not found — fallback text-search used.")

# ---------- Flask app + CORS ----------
app = Flask(__name__)

frontend_env = os.getenv("FRONTEND_ORIGINS", "")
if frontend_env:
    origins = [o.strip() for o in frontend_env.split(",") if o.strip()]
else:
    origins = ["http://localhost:5173"]

if os.getenv("FRONTEND_ORIGINS") == "*":
    CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)
else:
    CORS(app, resources={r"/api/*": {"origins": origins}}, supports_credentials=True)

# ---------- in-memory store ----------
JOBS = {}

# ---------- helper functions ----------
def ensure_cookies_file():
    """
    Return path to cookies.txt for yt-dlp.
    Priority:
    1. Local cookies.txt (for dev)
    2. Download from COOKIES_URL (for Railway/prod)
    """
    cookies_url = os.getenv("COOKIES_URL", "")
    cookies_path = os.path.join(BASE_DIR, "cookies.txt")

    # Local dev fallback
    if os.path.exists(cookies_path):
        logger.info("Using local cookies.txt at %s", cookies_path)
        return cookies_path

    # Production: download from URL
    if cookies_url:
        try:
            logger.info("Downloading cookies file from %s", cookies_url)
            r = requests.get(cookies_url, timeout=10)
            r.raise_for_status()
            with open(cookies_path, "wb") as f:
                f.write(r.content)
            logger.info("Cookies file saved to %s", cookies_path)
            return cookies_path
        except Exception as e:
            logger.exception("Failed to download cookies: %s", e)
            return None

    logger.warning("No cookies.txt found and no COOKIES_URL set.")
    return None


def search_youtube(query: str) -> str:
    try:
        from yt_dlp import YoutubeDL
    except Exception as e:
        logger.exception("yt-dlp import failed: %s", e)
        raise RuntimeError("yt-dlp not installed in environment")

    opts = {"quiet": True, "skip_download": True, "default_search": "ytsearch1"}
    with YoutubeDL(opts) as ydl:
        info = ydl.extract_info(query, download=False)
        if isinstance(info, dict) and "entries" in info and info["entries"]:
            return info["entries"][0].get("webpage_url")
        return info.get("webpage_url")


def progress_hook(d, job_id, idx):
    job = JOBS.get(job_id)
    if not job:
        return
    entry = job["jobs"][idx]
    status = d.get("status")
    if status == "downloading":
        total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
        downloaded = d.get("downloaded_bytes") or 0
        try:
            pct = int(downloaded / total * 100) if total else 0
        except Exception:
            pct = 0
        entry["progress"] = pct
        if d.get("eta"):
            entry["message"] = f"ETA: {d.get('eta')}"
    elif status == "finished":
        entry["progress"] = 85
        entry["message"] = "Postprocessing"


def worker(job_id, songs):
    logger.info("Worker started for job %s (%d songs)", job_id, len(songs))
    job = JOBS[job_id]
    try:
        for idx, song in enumerate(songs):
            entry = job["jobs"][idx]
            entry["status"] = "searching"
            job["state"] = "running"

            title = artist = album = release_date = None

            # --- Cookies for Youtube ---
            cookies_file = ensure_cookies_file()

            if _sp:
                try:
                    results = _sp.search(q=song, type="track", limit=1)
                    if results["tracks"]["items"]:
                        track = results["tracks"]["items"][0]
                        title = track["name"]
                        artist = track["artists"][0]["name"]
                        album = track["album"]["name"]
                        release_date = track["album"]["release_date"]
                        entry["message"] = f"Found: {title} - {artist}"
                    else:
                        entry["status"] = "not found"
                        entry["message"] = "Not found on Spotify"
                        entry["progress"] = 100
                        continue
                except Exception as e:
                    logger.exception("Spotify search failed for %s: %s", song, e)
                    entry["status"] = "error"
                    entry["message"] = f"Spotify error: {e}"
                    continue
            else:
                title = artist = song
                entry["message"] = f"Using search term: {song}"

            entry["status"] = "downloading"
            try:
                url = search_youtube(f"{title} {artist}")
                out_file = os.path.join(SAVE_PATH, f"{title} - {artist}.%(ext)s")
                ydl_opts = {
                    "format": "bestaudio/best",
                    "outtmpl": out_file,
                    "cookiefile": cookies_file if cookies_file else None,
                    "postprocessors": [
                        {
                            "key": "FFmpegExtractAudio",
                            "preferredcodec": "mp3",
                            "preferredquality": "192",
                        }
                    ],
                    "quiet": True,
                    "progress_hooks": [
                        lambda d, job_id=job_id, idx=idx: progress_hook(d, job_id, idx)
                    ],
                }

                from yt_dlp import YoutubeDL
                if cookies_file:
                    logger.info("Using cookies file: %s", cookies_file)
                else:
                    logger.info("No cookies file will be used")

                with YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])

                mp3_file = os.path.join(SAVE_PATH, f"{title} - {artist}.mp3")
                if os.path.exists(mp3_file):
                    try:
                        from mutagen.easyid3 import EasyID3

                        audio = EasyID3(mp3_file)
                        audio["title"] = title
                        audio["artist"] = artist
                        audio["album"] = album or "Unknown"
                        audio["date"] = release_date or ""
                        audio.save()
                    except Exception:
                        try:
                            from mutagen.id3 import ID3, TIT2, TPE1, TALB, TDRC

                            id3 = ID3()
                            id3.add(TIT2(encoding=3, text=title))
                            id3.add(TPE1(encoding=3, text=artist))
                            id3.add(TALB(encoding=3, text=album or "Unknown"))
                            id3.add(TDRC(encoding=3, text=release_date or ""))
                            id3.save(mp3_file)
                        except Exception:
                            logger.exception("Failed to write ID3 tags for %s", mp3_file)

                    entry["status"] = "done"
                    entry["message"] = "Saved with metadata"
                    entry["progress"] = 100
                else:
                    entry["status"] = "error"
                    entry["message"] = "MP3 not found after download"
            except Exception as e:
                logger.exception("Download error for %s: %s", song, e)
                entry["status"] = "error"
                entry["message"] = f"YT download error: {e}"

        job["state"] = "done"
    except Exception as e:
        logger.exception("Worker crashed for job %s: %s", job_id, e)
        job["state"] = "failed"
        job["error"] = str(e)

# ---------- routes ----------
@app.route("/", methods=["GET"])
def health():
    return jsonify({"status": "ok", "message": "TuneFlow backend running"})

@app.route("/api/download", methods=["POST"])
def api_download():
    data = request.json or {}
    songs = data.get("songs") or []
    if not songs:
        return jsonify({"error": "no songs provided"}), 400

    job_id = str(uuid.uuid4())
    JOBS[job_id] = {
        "state": "queued",
        "jobs": [{"name": s, "status": "queued", "progress": 0, "message": ""} for s in songs],
    }

    t = threading.Thread(target=worker, args=(job_id, songs), daemon=True)
    t.start()

    return jsonify({"job_id": job_id, "initial": JOBS[job_id]["jobs"]})

@app.route("/api/status/<job_id>")
def api_status(job_id):
    job = JOBS.get(job_id)
    if not job:
        return jsonify({"error": "job not found"}), 404
    return jsonify({"state": job["state"], "jobs": job["jobs"]})

@app.route("/api/files")
def api_files():
    order = request.args.get("order", "latest")
    try:
        files = [f for f in os.listdir(SAVE_PATH) if f.lower().endswith(".mp3")]
        files.sort(key=lambda f: os.path.getmtime(os.path.join(SAVE_PATH, f)), reverse=(order=="latest"))
    except Exception as e:
        logger.exception("Failed to list files: %s", e)
        files = []
    return jsonify({"files": files})

@app.route("/api/file/<path:filename>")
def api_file(filename):
    return send_from_directory(SAVE_PATH, filename, as_attachment=True)

# ---------- run ----------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    debug = IS_LOCAL or os.getenv("FLASK_DEBUG", "0") == "1"
    logger.info("Starting dev server on port %d (IS_LOCAL=%s, SAVE_PATH=%s)", port, IS_LOCAL, SAVE_PATH)
    app.run(host="0.0.0.0", port=port, debug=debug)








