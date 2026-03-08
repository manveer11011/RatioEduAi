# RatioEdu – Electron Desktop App

ChatGPT-style desktop UI that connects to the Python RAG backend.

## Prerequisites

1. **Start the Python backend** (RAG FastAPI server):

   ```bash
   # From project root
   PORT=8000 python run_teacher_web.py
   ```

   Or set `PORT=8000` in `.env`. The backend must be running before using the app.

## Run the Electron app

```bash
cd electron_app
npm install
npm run dev
```

Or from project root:

```bash
cd electron_app && npm install && npm run dev
```

## API

The app sends messages to `http://127.0.0.1:8000/api/chat` (POST, JSON body: `{message: "..."}`) and expects `{reply: "..."}`.
