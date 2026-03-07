import os
import re
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_GGUF_PATH = _PROJECT_ROOT / "model" / "Qwen3-4B-Instruct-2507-Q4_K_S.gguf"

N_CTX = 2048
TEMPERATURE = 0.2
N_GPU_LAYERS = 0

# Model may output <|channel|>analysis<|message|>...<|end|><|start|>assistant<|channel|>final<|message|>Answer
_ATTR_TOKEN_RE = re.compile(r"<\|[^|]*\|>")


def _clean_rag_reply(raw: str) -> str:
    """Extract only the final message; strip analysis and special tokens."""
    if not raw or not raw.strip():
        return raw
    text = raw
    # Prefer content after <|channel|>final<|message|>
    final_marker = "<|channel|>final<|message|>"
    if final_marker in text:
        text = text.split(final_marker, 1)[-1]
    else:
        # Fallback: drop content before last "assistant" + "final" section
        for sep in ("assistantfinal", "assistant final ", "assistant  final "):
            if sep.lower() in text.lower():
                idx = text.lower().rfind(sep.lower())
                text = text[idx + len(sep) :]
                break
    # Remove all <|...|> tokens
    text = _ATTR_TOKEN_RE.sub("", text)
    return text.strip() or raw.strip()


def get_model_path() -> str:
    return os.environ.get("RAG_GGUF_PATH", "").strip() or str(DEFAULT_GGUF_PATH)


def load_llm(model_path: str | None = None):
    from llama_cpp import Llama
    path = model_path or get_model_path()
    if not Path(path).is_file():
        raise FileNotFoundError(f"GGUF model not found: {path}. Set RAG_GGUF_PATH or place model at {path}")
    return Llama(
        model_path=path,
        n_ctx=N_CTX,
        n_gpu_layers=N_GPU_LAYERS,
        verbose=False,
    )


def generate(llm, messages: list[dict], max_tokens: int = 1024) -> str:
    try:
        response = llm.create_chat_completion(
            messages=messages,
            max_tokens=max_tokens,
            temperature=TEMPERATURE,
        )
    except Exception as e:
        return "[Error during inference. Please try again.]"
    choices = response.get("choices") or []
    if not choices:
        return ""
    msg = choices[0].get("message") or choices[0].get("delta") or {}
    raw = (msg.get("content") or "").strip()
    return _clean_rag_reply(raw)
