import os
import re
from functools import partial

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_GGUF_PATH = os.path.join(_PROJECT_ROOT, "model", "Qwen3-4B-Instruct-2507-Q4_K_S.gguf")
N_GPU_LAYERS = 0
_ATTR_TOKEN_RE = re.compile(r"<\|[^|]*\|>")


def get_gguf_path() -> str:
    return os.environ.get("GGUF_PATH", "").strip() or DEFAULT_GGUF_PATH


def clean_teacher_reply(reply: str) -> str:
    """Keep only the model's final response; hide thinking/analysis."""
    if not reply:
        return reply
    text = _ATTR_TOKEN_RE.sub("", reply)
    for sep in ("assistantfinal", "assistant final ", "assistant  final "):
        if sep.lower() in text.lower():
            idx = text.lower().rfind(sep.lower())
            text = text[idx + len(sep) :]
            break
    out = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        lower = line.lower()
        if "thinking" in lower:
            continue
        if lower.startswith("analysis") or "user says:" in lower or "user asks:" in lower:
            continue
        if len(line) < 70:
            if lower.startswith("they want ") or lower.startswith("we should ") or "within scope" in lower:
                continue
            if "let's do that" in lower or lower.startswith("we can respond"):
                continue
        out.append(line)
    text = "\n".join(out).strip()
    return re.sub(r"\n{3,}", "\n\n", text) or reply.strip()


def _build_messages(history: list[dict], new_user_message: str) -> list[dict]:
    from study_coding_teacher_agent.gguf_backend import TEACHER_SYSTEM_PROMPT
    messages = [{"role": "system", "content": TEACHER_SYSTEM_PROMPT}]
    for m in history:
        if m.get("role") in ("user", "assistant") and m.get("content"):
            messages.append({"role": m["role"], "content": m["content"]})
    messages.append({"role": "user", "content": new_user_message})
    return messages


def create_get_reply():
    from llama_cpp import Llama
    path = get_gguf_path()
    if not os.path.isfile(path):
        raise FileNotFoundError(f"GGUF model not found: {path}. Set GGUF_PATH or place model at {path}")
    llm = Llama(model_path=path, n_ctx=8192, n_gpu_layers=N_GPU_LAYERS, verbose=False)
    from study_coding_teacher_agent.gguf_backend import (
        get_teacher_response_gguf,
        get_teacher_response_gguf_messages,
    )

    def _get_reply(msg: str):
        return clean_teacher_reply(get_teacher_response_gguf(llm, msg))

    def _get_reply_with_history(history: list, msg: str):
        return clean_teacher_reply(
            get_teacher_response_gguf_messages(llm, _build_messages(history, msg))
        )

    return (_get_reply, _get_reply_with_history, "GGUF")
