#!/usr/bin/env python3
"""Start RAG backend server on port 8000 for Electron app."""

import os
import sys

os.environ.setdefault("PORT", "8000")

ROOT = __import__("pathlib").Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

if __name__ == "__main__":
    import uvicorn
    import config
    from run_teacher_web import app
    uvicorn.run(app, host=config.get_host(), port=config.get_port())
