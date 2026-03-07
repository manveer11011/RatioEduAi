"""Persistent chat history storage in chat_history folder. Used for model context/memory."""
import json
from pathlib import Path

import config


def _chat_history_dir() -> Path:
    return config.get_chat_history_dir()


def _ensure_dir() -> Path:
    d = _chat_history_dir()
    d.mkdir(parents=True, exist_ok=True)
    return d


def _chats_path() -> Path:
    return _ensure_dir() / "chats.json"


def _migrate_legacy_chats() -> None:
    """Migrate .ai_teacher_chats.json from project root to chat_history/chats.json."""
    root = config.PROJECT_ROOT
    legacy = root / ".ai_teacher_chats.json"
    dest = _chats_path()
    if legacy.is_file() and not dest.is_file():
        try:
            data = json.loads(legacy.read_text(encoding="utf-8"))
            chats = data if isinstance(data, list) else []
            if chats:
                _ensure_dir()
                dest.write_text(json.dumps(chats, ensure_ascii=False, indent=2), encoding="utf-8")
        except (json.JSONDecodeError, OSError):
            pass


def load_chats() -> list[dict]:
    """Load all chats from chat_history/chats.json."""
    _migrate_legacy_chats()
    path = _chats_path()
    if not path.is_file():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def save_chats(chats: list[dict]) -> None:
    """Save all chats to chat_history/chats.json."""
    path = _chats_path()
    path.write_text(json.dumps(chats, ensure_ascii=False, indent=2), encoding="utf-8")


def get_chat(chat_id: str) -> dict | None:
    """Get a single chat by id."""
    chats = load_chats()
    for c in chats:
        if c.get("id") == chat_id:
            return c
    return None


def save_chat(chat: dict) -> None:
    """Save or update a single chat."""
    chats = load_chats()
    chat_id = chat.get("id")
    for i, c in enumerate(chats):
        if c.get("id") == chat_id:
            chats[i] = chat
            save_chats(chats)
            return
    chats.append(chat)
    save_chats(chats)


def delete_chat(chat_id: str) -> bool:
    """Delete a chat by id. Returns True if deleted."""
    chats = load_chats()
    before = len(chats)
    chats = [c for c in chats if c.get("id") != chat_id]
    if len(chats) < before:
        save_chats(chats)
        return True
    return False
