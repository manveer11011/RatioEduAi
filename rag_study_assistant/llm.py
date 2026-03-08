import re
from pathlib import Path

import config

_ATTR_TOKEN_RE = re.compile(r"<\|[^|]*\|>")


def _clean_rag_reply(raw: str) -> str:
    if not raw or not raw.strip():
        return raw
    text = raw
    final_marker = "<|channel|>final<|message|>"
    if final_marker in text:
        text = text.split(final_marker, 1)[-1]
    else:
        for sep in ("assistantfinal", "assistant final ", "assistant  final "):
            if sep.lower() in text.lower():
                idx = text.lower().rfind(sep.lower())
                text = text[idx + len(sep) :]
                break
    text = _ATTR_TOKEN_RE.sub("", text)
    return text.strip() or raw.strip()


def get_model_path() -> str:
    return config.get_rag_gguf_path()


def load_llm(model_path: str | None = None):
    from llama_cpp import Llama
    path = model_path or get_model_path()
    if not Path(path).is_file():
        raise FileNotFoundError(f"GGUF model not found: {path}. Set RAG_GGUF_PATH or place model at {path}")
    return Llama(
        model_path=path,
        n_ctx=config.get_rag_n_ctx(),
        n_gpu_layers=config.get_n_gpu_layers(),
        verbose=False,
    )


def generate(llm, messages: list[dict], max_tokens: int | None = None) -> str:
    max_tokens = max_tokens if max_tokens is not None else config.get_max_tokens()
    try:
        response = llm.create_chat_completion(
            messages=messages,
            max_tokens=max_tokens,
            temperature=config.get_temperature(),
        )
    except Exception as e:
        return "[Error during inference. Please try again.]"
    choices = response.get("choices") or []
    if not choices:
        return ""
    msg = choices[0].get("message") or choices[0].get("delta") or {}
    raw = (msg.get("content") or "").strip()
    return _clean_rag_reply(raw)
