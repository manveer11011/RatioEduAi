const { app, BrowserWindow } = require("electron");
const path = require("path");
const { spawn } = require("child_process");
const fs = require("fs");
const http = require("http");

const PORT = 8000;
const API_URL = `http://127.0.0.1:${PORT}`;
const PROJECT_ROOT = path.join(__dirname, "..");

let backendProcess = null;

function indexExists() {
  return fs.existsSync(path.join(PROJECT_ROOT, "index", "faiss.index"));
}

function embeddingModelReady() {
  const envPath = path.join(PROJECT_ROOT, ".env");
  if (!fs.existsSync(envPath)) return true;
  const content = fs.readFileSync(envPath, "utf8");
  const match = content.match(/^EMBEDDING_MODEL_PATH=(.+)$/m);
  if (!match) return true;
  const raw = match[1].trim();
  if (!raw || raw.startsWith("#")) return true;
  const p = raw.replace(/^["']|["']$/g, "");
  const full = path.isAbsolute(p) ? p : path.join(PROJECT_ROOT, p);
  return fs.existsSync(full);
}

function runRagBuild() {
  return new Promise((resolve) => {
    const py = process.platform === "win32" ? "python" : "python3";
    const build = spawn(py, ["-m", "rag_study_assistant.main", "--build"], {
      cwd: PROJECT_ROOT,
      stdio: "pipe",
      env: { ...process.env, PYTHONUNBUFFERED: "1" },
    });
    let stderr = "";
    build.stderr?.on("data", (d) => { stderr += d.toString(); });
    build.on("close", (code) => {
      if (code === 0) resolve(true);
      else resolve(false);
    });
    build.on("error", () => resolve(false));
  });
}

function startBackend() {
  const py = process.platform === "win32" ? "python" : "python3";
  const script = path.join(PROJECT_ROOT, "start_backend.py");
  if (!fs.existsSync(script)) {
    console.error("start_backend.py not found");
    return null;
  }
  backendProcess = spawn(py, [script], {
    cwd: PROJECT_ROOT,
    env: { ...process.env, PORT: String(PORT) },
    stdio: "pipe",
  });
  backendProcess.stderr?.on("data", (d) => process.stderr.write(d));
  backendProcess.on("error", (err) => console.error("Backend spawn error:", err));
  return backendProcess;
}

function waitForServer(maxAttempts = 120) {
  return new Promise((resolve) => {
    let attempts = 0;
    const check = () => {
      http.get(`${API_URL}/api/status`, (res) => {
        if (res.statusCode === 200) return resolve(true);
        if (++attempts < maxAttempts) setTimeout(check, 1000);
        else resolve(false);
      }).on("error", () => {
        if (++attempts < maxAttempts) setTimeout(check, 1000);
        else resolve(false);
      });
    };
    setTimeout(check, 2000);
  });
}

function createWindow() {
  const win = new BrowserWindow({
    width: 1100,
    height: 800,
    backgroundColor: "#0f172a",
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false
    }
  });

  win.loadFile(path.join(__dirname, "index.html"));
}

function createSplashWindow() {
  const splash = new BrowserWindow({
    width: 420,
    height: 280,
    frame: false,
    transparent: false,
    backgroundColor: "#0d0d0d",
  });
  const html = '<!DOCTYPE html><html><head><meta charset="UTF-8"></head><body style="margin:0;background:#0d0d0d;color:#ececec;font-family:Segoe UI,sans-serif;display:flex;flex-direction:column;align-items:center;justify-content:center;height:100vh;min-height:280px;"><div style="font-size:3rem;color:#10a37f;margin-bottom:8px;">&#9671;</div><h1 style="margin:0;font-size:1.75rem;font-weight:600;letter-spacing:-0.02em;">RatioEdu</h1><p style="margin:16px 0 0;font-size:0.875rem;color:#8e8e93;">Loading...</p></body></html>';
  splash.loadURL("data:text/html;charset=utf-8," + encodeURIComponent(html));
  return splash;
}

app.whenReady().then(async () => {
  const splash = createSplashWindow();

  try {
    if (!embeddingModelReady()) {
      splash.close();
      const { dialog } = require("electron");
      dialog.showErrorBox(
        "Embedding Model Missing",
        "EMBEDDING_MODEL_PATH is set in .env but the file does not exist.\n\nAdd the embedding model file (e.g. model/embedding/all-MiniLM-L6-v2-Q8_0.gguf) or remove EMBEDDING_MODEL_PATH to use the default."
      );
      app.quit();
      return;
    }
    if (!indexExists()) {
      const built = await runRagBuild();
      if (!built) {
        splash.close();
        const { dialog } = require("electron");
        dialog.showErrorBox(
          "Setup Required",
          "Add .txt files under data/syllabus, data/notes, or data/question_papers, then restart the app.\n\nRun: python -m rag_study_assistant.main --build"
        );
        app.quit();
        return;
      }
    }

    startBackend();
    const ready = await waitForServer();
    splash.close();
    if (!ready) {
      const { dialog } = require("electron");
      dialog.showErrorBox(
        "Backend Failed",
        "Could not start the Python backend. Ensure Python and dependencies are installed:\npip install -r requirements.txt"
      );
      app.quit();
      return;
    }

    createWindow();
  } catch (err) {
    splash.close();
    const { dialog } = require("electron");
    dialog.showErrorBox("Error", String(err.message || err));
    app.quit();
  }
});

app.on("before-quit", () => {
  if (backendProcess) {
    backendProcess.kill();
  }
});
