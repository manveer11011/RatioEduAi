# RatioEdu – Electron Desktop + RAG Backend

## Run the app (one command)

From project root:

```bash
cd electron_app
npm install
npm run dev
```

Or: `npm run dev` from project root.

**What happens:**
1. If RAG index is missing → auto-runs `python -m rag_study_assistant.main --build`
2. Starts FastAPI backend on port 8000
3. Waits for backend ready
4. Opens the chat window

**Requirements:**
- Python 3.8+ with `pip install -r requirements.txt -r requirements-build.txt`
- GGUF model in `model/`
- `.txt` notes in `data/syllabus`, `data/notes`, or `data/question_papers`
- Node.js (for Electron)

## Final build (distributable)

To package the Electron app for distribution:

```bash
cd electron_app
npm install
npm install --save-dev electron-builder
npx electron-builder --win
```

**Important for production build:**
1. Ensure `data/` and `model/` folders exist (create empty if needed).
2. The build bundles the Python backend and requirement files into the app.
3. When users run the installer, it **automatically installs** `requirements.txt` and `requirements-build.txt` during setup (via pip). Python must be installed on the system.
4. When you run the exe, it **starts the backend automatically** and **stops it when you close the app**. No separate backend process needed.
