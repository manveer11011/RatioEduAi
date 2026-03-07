import config
import numpy as np

from transformers import logging as tr_logging

tr_logging.set_verbosity_error()

_local_path = config.get_embedding_model_path()
_use_gguf = _local_path and str(_local_path).lower().endswith(".gguf")

if _use_gguf:
    from llama_cpp import Llama
    embedding_model = Llama(
        model_path=str(_local_path),
        embedding=True,
        n_ctx=512,
        n_gpu_layers=config.get_n_gpu_layers(),
        verbose=False,
    )
else:
    from sentence_transformers import SentenceTransformer
    if _local_path:
        embedding_model = SentenceTransformer(str(_local_path), local_files_only=True)
    else:
        embedding_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2", local_files_only=True)


def embed_text(text: str):
    if text is None:
        text = ""
    if _use_gguf:
        emb = embedding_model.embed(text, normalize=True)
        return np.array(emb, dtype=np.float32)
    return embedding_model.encode(text)
