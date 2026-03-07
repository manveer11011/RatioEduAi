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
- Python 3.8+ with `pip install -r requirements.txt`
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

**Note:** The packaged app still requires the Python backend to be present. For a fully standalone build, distribute the entire project folder and run the Electron exe from there. Users need Python + dependencies installed.
