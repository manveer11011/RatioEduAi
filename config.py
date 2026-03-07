"""Load .env and expose settings. Import early so env vars are available."""
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# When running as PyInstaller exe, use exe directory; else use script directory
if getattr(sys, "frozen", False):
    _PROJECT_ROOT = Path(sys.executable).resolve().parent
else:
    _PROJECT_ROOT = Path(__file__).resolve().parent
load_dotenv(_PROJECT_ROOT / ".env")
os.environ.setdefault("HF_HUB_OFFLINE", "1")

PROJECT_ROOT = _PROJECT_ROOT


def _env(key: str, default: str = "") -> str:
    return (os.environ.get(key) or default).strip()


def _env_int(key: str, default: int) -> int:
    try:
        return int(os.environ.get(key, default))
    except (TypeError, ValueError):
        return default


def _env_float(key: str, default: float) -> float:
    try:
        return float(os.environ.get(key, default))
    except (TypeError, ValueError):
        return default


def _default_gguf_path() -> Path:
    filename = _env("DEFAULT_GGUF_FILENAME", "Llama-3.2-1B-Instruct-Q8_0.gguf")
    # When frozen, model is bundled in PyInstaller temp dir
    base = Path(sys._MEIPASS) / "model" if getattr(sys, "frozen", False) else PROJECT_ROOT / "model"
    path = base / filename
    if path.exists():
        return path
    # Fallback: use first .gguf found in model/
    if base.exists():
        for p in base.glob("*.gguf"):
            return p
    return path  # Let caller handle missing


def get_gguf_path() -> str:
    p = _env("GGUF_PATH")
    if p:
        return p
    return str(_default_gguf_path())


def get_rag_gguf_path() -> str:
    p = _env("RAG_GGUF_PATH")
    if p:
        return p
    return str(_default_gguf_path())


def get_embedding_model_path() -> Path | None:
    p = _env("EMBEDDING_MODEL_PATH")
    if not p:
        return None
    path = Path(p)
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    path = path.resolve()
    return path if (path.is_dir() or path.is_file()) else None


def get_index_dir(project_root: Path | None = None) -> Path:
    p = _env("INDEX_DIR")
    if p:
        path = Path(p)
        if not path.is_absolute():
            path = (project_root or PROJECT_ROOT) / path
        return path.resolve()
    root = project_root or PROJECT_ROOT
    return root / "index"


def get_chat_history_dir(project_root: Path | None = None) -> Path:
    """Directory for persistent chat history (used as model context/memory)."""
    p = _env("CHAT_HISTORY_DIR")
    if p:
        path = Path(p)
        if not path.is_absolute():
            path = (project_root or PROJECT_ROOT) / path
        return path.resolve()
    root = project_root or PROJECT_ROOT
    return root / "chat_history"


def get_n_gpu_layers() -> int:
    return _env_int("N_GPU_LAYERS", 0)


def get_rag_n_ctx() -> int:
    return _env_int("RAG_N_CTX", 2048)


def get_teacher_n_ctx() -> int:
    return _env_int("TEACHER_N_CTX", 8192)


def get_temperature() -> float:
    return _env_float("TEMPERATURE", 0.2)


def get_max_tokens() -> int:
    return _env_int("MAX_TOKENS", 4096)


def get_port() -> int:
    return _env_int("PORT", 8765)


def get_host() -> str:
    return _env("HOST") or "127.0.0.1"


def get_max_message_length() -> int:
    return _env_int("MAX_MESSAGE_LENGTH", 32_000)


def get_rate_limit_requests() -> int:
    return _env_int("RATE_LIMIT_REQUESTS", 60)


def get_rate_limit_window_sec() -> int:
    return _env_int("RATE_LIMIT_WINDOW_SEC", 60)
