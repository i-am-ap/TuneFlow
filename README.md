## Smart Downloader (Frontend + Backend)

## Quick start (development)

### Frontend
1. `cd frontend` (if you put frontend files in `frontend/`, otherwise root)
2. `npm install`
3. `npm run dev` (Vite will run on 5173)

### Backend
1. Create a Python venv: `python -m venv venv && source venv/bin/activate` (Windows: `venv\\Scripts\\activate`)
2. `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and set `SPOTIFY_CLIENT_ID` and `SPOTIFY_CLIENT_SECRET`.
4. `python app.py` (server runs on port 7860)

API is proxied from Vite dev server so frontend requests to `/api/*` go to `http://localhost:7860/api/*`.

## Notes
- Do **not** push Spotify credentials to public repos. Use environment variables or secrets.
- For production: use a task queue (Celery/RQ) and persistent job store (Redis/Postgres). Add rate limiting and quotas.
- This project is for learning / personal use — be mindful of YouTube/Spotify terms of service.
