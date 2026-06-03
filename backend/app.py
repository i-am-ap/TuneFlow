import os
import uuid
import threading
import logging
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

# ----------------- Logging -----------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("tuneflow-backend")

# ----------------- Environment -----------------
load_dotenv()  # Load local .env if present
ENV = os.getenv("ENV", "local")  # "local" or "production"

BASE_DIR = os.getcwd()
LOCAL_DOWNLOADS = os.path.join(BASE_DIR, "downloads")
PROD_DOWNLOADS = os.path.join("/tmp", "downloads_prod")
SAVE_PATH = LOCAL_DOWNLOADS if ENV == "local" else PROD_DOWNLOADS
os.makedirs(SAVE_PATH, exist_ok=True)

# ----------------- Cookies -----------------
COOKIES_CONTENT = None
if ENV == "production":
    COOKIES_CONTENT = os.getenv("YOUTUBE_COOKIES")
    if not COOKIES_CONTENT:
        logger.warning("⚠️ YOUTUBE_COOKIES not set in ENV!")
    else:
        logger.info("✅ Loaded YouTube cookies from ENV")
else:
    logger.info("⚠️ Running in local mode: cookies not used")

# ----------------- Flask App + CORS -----------------
app = Flask(__name__)
frontend_env = os.getenv("FRONTEND_ORIGINS", "")
origins = [o.strip() for o in frontend_env.split(",") if o.strip()] or ["http://localhost:5173"]

# if os.getenv("FRONTEND_ORIGINS") == "*":
#     CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)
# else:
#     CORS(app, resources={r"/api/*": {"origins": origins}}, supports_credentials=True)

CORS(app)

# ----------------- In-Memory Job Store -----------------
JOBS = {}

# ----------------- YouTube Search -----------------
def search_youtube(query: str):
    """Return first YouTube URL using yt-dlp"""
    from yt_dlp import YoutubeDL

    opts = {"quiet": True, "skip_download": True, "default_search": "ytsearch1"}
    if ENV == "production" and COOKIES_CONTENT:
        cookie_path = "/tmp/cookies.txt"
        with open(cookie_path, "w", encoding="utf-8") as f:
            f.write(COOKIES_CONTENT)
        opts["cookiefile"] = cookie_path

    with YoutubeDL(opts) as ydl:
        info = ydl.extract_info(query, download=False)
        if "entries" in info and info["entries"]:
            return info["entries"][0].get("webpage_url")
        return info.get("webpage_url")

# ----------------- Progress Hook -----------------
def progress_hook(d, job_id, idx):
    job = JOBS.get(job_id)
    if not job:
        return
    entry = job["jobs"][idx]
    status = d.get("status")
    if status == "downloading":
        total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
        downloaded = d.get("downloaded_bytes") or 0
        entry["progress"] = int(downloaded / total * 100) if total else 0
        if d.get("eta"):
            entry["message"] = f"ETA: {d.get('eta')}"
    elif status == "finished":
        entry["progress"] = 85
        entry["message"] = "Postprocessing"

# ----------------- Worker -----------------
def worker(job_id, songs):
    logger.info("Worker started for job %s (%d songs)", job_id, len(songs))
    job = JOBS[job_id]
    from yt_dlp import YoutubeDL

    try:
        for idx, song in enumerate(songs):
            entry = job["jobs"][idx]
            entry["status"] = "searching"
            job["state"] = "running"

            title = artist = song
            entry["message"] = f"Searching: {song}"

            entry["status"] = "downloading"
            try:
                url = search_youtube(f"{title} {artist}")
                out_file = os.path.join(SAVE_PATH, f"{title}.%(ext)s")
                ydl_opts = {
                    "format": "bestaudio/best",
                    "outtmpl": out_file,
                    "postprocessors": [
                        {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}
                    ],
                    "quiet": True,
                    "ignoreerrors": True,
                    "noplaylist": True,
                    "progress_hooks": [lambda d, job_id=job_id, idx=idx: progress_hook(d, job_id, idx)],
                }

                if ENV == "production" and COOKIES_CONTENT:
                    cookie_path = "/tmp/cookies.txt"
                    ydl_opts["cookiefile"] = cookie_path

                try:
                    with YoutubeDL(ydl_opts) as ydl:
                        ydl.download([url])
                except Exception:
                    # 🔄 fallback if bestaudio/best not available
                    fallback_opts = ydl_opts.copy()
                    fallback_opts["format"] = "m4a/bestaudio/best"
                    with YoutubeDL(fallback_opts) as ydl:
                        ydl.download([url])

                mp3_file = os.path.join(SAVE_PATH, f"{title}.mp3")
                if os.path.exists(mp3_file):
                    entry["status"] = "done"
                    entry["message"] = "Saved successfully"
                    entry["progress"] = 100
                else:
                    entry["status"] = "error"
                    entry["message"] = "MP3 not found after download"

            except Exception as e:
                entry["status"] = "error"
                entry["message"] = f"YT download error: {e}"
                logger.exception("Download error for %s: %s", song, e)

        job["state"] = "done"
    except Exception as e:
        job["state"] = "failed"
        job["error"] = str(e)
        logger.exception("Worker crashed for job %s: %s", job_id, e)

# ----------------- Routes -----------------
@app.route("/", methods=["GET"])
def health():
    return jsonify({"status": "ok", "message": f"TuneFlow running in {ENV} mode"})

@app.route("/api/download", methods=["GET","POST"])
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
    try:
        files = [f for f in os.listdir(SAVE_PATH) if f.lower().endswith(".mp3")]
        files.sort(key=lambda f: os.path.getmtime(os.path.join(SAVE_PATH, f)), reverse=True)
    except Exception as e:
        logger.exception("Failed to list files: %s", e)
        files = []
    return jsonify({"files": files})

@app.route("/api/file/<path:filename>")
def api_file(filename):
    return send_from_directory(SAVE_PATH, filename, as_attachment=True)

# ----------------- Run -----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    debug = ENV == "local" or os.getenv("FLASK_DEBUG", "0") == "1"
    logger.info("Starting server on port %d (ENV=%s, SAVE_PATH=%s)", port, ENV, SAVE_PATH)
    app.run(host="0.0.0.0", port=port, debug=debug)
