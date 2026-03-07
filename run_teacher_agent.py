#!/usr/bin/env python3
"""
Run the Study & Coding Teacher agent (CLI).

  pip install llama-cpp-python
  python run_teacher_agent.py

Custom GGUF path: set GGUF_PATH=C:/path/to/model.gguf
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

_PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DEFAULT_GGUF_PATH = os.path.join(_PROJECT_ROOT, "model", "Qwen3-4B-Instruct-2507-Q4_K_S.gguf")
N_GPU_LAYERS = 0


def _get_gguf_path():
    return os.environ.get("GGUF_PATH", "").strip() or DEFAULT_GGUF_PATH


def main():
    gguf_path = _get_gguf_path()
    if not os.path.isfile(gguf_path):
        sys.exit(f"GGUF model not found: {gguf_path}. Set GGUF_PATH or place model at {gguf_path}")
    try:
        from llama_cpp import Llama
        llm = Llama(
            model_path=gguf_path,
            n_ctx=8192,
            n_gpu_layers=N_GPU_LAYERS,
            verbose=False,
        )
    except ImportError:
        sys.exit("pip install llama-cpp-python")
    except Exception as e:
        sys.exit(f"Failed to load GGUF: {e}")
    from study_coding_teacher_agent.gguf_backend import get_teacher_response_gguf
    get_reply = lambda msg: get_teacher_response_gguf(llm, msg, use_short_prompt=False, use_guard=False)

    print("Ask me anything. Type 'quit' or 'exit' to stop.\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            break
        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q"):
            print("Bye!")
            break
        reply = get_reply(user_input)
        print("Teacher:", reply)
        print()


if __name__ == "__main__":
    main()
