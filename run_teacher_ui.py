#!/usr/bin/env python3
"""Tkinter UI for the Study & Coding Teacher chatbot."""

import os
import re
import sys
import threading
import tkinter as tk
from tkinter import scrolledtext

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from study_coding_teacher_agent.backend_runner import clean_teacher_reply

_PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DEFAULT_GGUF_PATH = os.path.join(_PROJECT_ROOT, "model", "Qwen3-4B-Instruct-2507-Q4_K_S.gguf")
N_GPU_LAYERS = 0


def _get_gguf_path():
    return os.environ.get("GGUF_PATH", "") or DEFAULT_GGUF_PATH


def create_ui():
    path = _get_gguf_path()
    if not os.path.isfile(path):
        raise FileNotFoundError(f"GGUF model not found: {path}. Set GGUF_PATH or place model at {path}")
    from llama_cpp import Llama
    from study_coding_teacher_agent.gguf_backend import get_teacher_response_gguf
    llm = Llama(
        model_path=path,
        n_ctx=8192,
        n_gpu_layers=N_GPU_LAYERS,
        verbose=False,
    )

    def get_reply(text: str) -> str:
        return get_teacher_response_gguf(llm, text)

    bg_dark = "#0f1117"
    bg_card = "#161b22"
    bg_input = "#21262d"
    fg_light = "#e6edf3"
    fg_muted = "#8b949e"
    accent = "#58a6ff"
    accent_green = "#3fb950"
    accent_orange = "#d29922"
    border = "#30363d"

    root = tk.Tk()
    root.title("AI Teacher")
    root.geometry("900x620")
    root.configure(bg=bg_dark)

    header = tk.Frame(root, bg=bg_card, height=48)
    header.pack(fill=tk.X)
    header.pack_propagate(False)

    tk.Label(
        header,
        text="AI Teacher",
        fg=fg_light,
        bg=bg_card,
        font=("Segoe UI", 15, "bold"),
    ).pack(side=tk.LEFT, padx=20)

    main = tk.Frame(root, bg=bg_dark)
    main.pack(fill=tk.BOTH, expand=True)

    chat_container = tk.Frame(main, bg=bg_dark, padx=14, pady=10)
    chat_container.pack(fill=tk.BOTH, expand=True)

    chat = scrolledtext.ScrolledText(
        chat_container,
        bg=bg_dark,
        fg=fg_light,
        insertbackground=fg_light,
        relief=tk.FLAT,
        wrap=tk.WORD,
        font=("Segoe UI", 11),
        padx=12,
        pady=6,
    )
    chat.pack(fill=tk.BOTH, expand=True)
    chat.config(state=tk.DISABLED)

    chat.tag_configure("body", foreground=fg_light, lmargin1=12, lmargin2=12)
    chat.tag_configure("thinking", foreground=fg_muted, font=("Segoe UI", 10))
    chat.tag_configure("user", foreground=accent, font=("Segoe UI", 10, "bold"), spacing1=4, spacing3=2)
    chat.tag_configure("teacher", foreground=accent_green, font=("Segoe UI", 10, "bold"), spacing1=4, spacing3=2)
    chat.tag_configure("user_body", foreground=fg_light, lmargin1=12, lmargin2=12, spacing3=6)
    chat.tag_configure("teacher_body", foreground=fg_light, lmargin1=12, lmargin2=12, spacing3=6)
    chat.tag_configure("code", foreground=accent_orange, background="#0b0f14", font=("Consolas", 10), lmargin1=16, lmargin2=16, rmargin=16, spacing1=4, spacing3=4)
    chat.tag_configure("md_bold", foreground=fg_light, font=("Segoe UI", 11, "bold"))
    chat.tag_configure("md_code", foreground=accent_orange, font=("Consolas", 10))
    chat.tag_configure("md_block", foreground=accent_orange, background="#0b0f14", font=("Consolas", 10), lmargin1=16, lmargin2=16, rmargin=16, spacing1=4, spacing3=4)
    chat.tag_configure("md_heading", foreground=fg_light, font=("Segoe UI", 12, "bold"), spacing1=8, spacing3=2)
    chat.tag_configure("md_link", foreground=accent)
    chat.tag_configure("md_italic", foreground=fg_muted)
    chat.tag_configure("md_table", foreground=fg_light, font=("Segoe UI", 10), lmargin1=16, lmargin2=16, spacing1=2, spacing3=2)

    def _insert_inline_md(widget, line, base_tag="body"):
        pos = 0
        while pos < len(line):
            bold_m = re.search(r"\*\*(.+?)\*\*", line[pos:])
            code_m = re.search(r"`([^`]+)`", line[pos:])
            link_m = re.search(r"\[([^\]]+)\]\(([^)]+)\)", line[pos:])
            italic_m = re.search(r"(?<!\*)\*([^*]+)\*(?!\*)", line[pos:])
            b = (bold_m.start() + pos) if bold_m else len(line)
            c = (code_m.start() + pos) if code_m else len(line)
            l = (link_m.start() + pos) if link_m else len(line)
            it = (italic_m.start() + pos) if italic_m else len(line)
            if bold_m and b <= c and b <= l and b <= it:
                widget.insert(tk.END, line[pos:b], base_tag)
                widget.insert(tk.END, bold_m.group(1), "md_bold")
                pos = b + len(bold_m.group(0))
            elif code_m and c <= b and c <= l and c <= it:
                widget.insert(tk.END, line[pos:c], base_tag)
                widget.insert(tk.END, code_m.group(1), "md_code")
                pos = c + len(code_m.group(0))
            elif link_m and l <= b and l <= c and l <= it:
                widget.insert(tk.END, line[pos:l], base_tag)
                widget.insert(tk.END, link_m.group(1), "md_link")
                pos = l + len(link_m.group(0))
            elif italic_m and it <= b and it <= c and it <= l:
                widget.insert(tk.END, line[pos:it], base_tag)
                widget.insert(tk.END, italic_m.group(1), "md_italic")
                pos = it + len(italic_m.group(0))
            else:
                widget.insert(tk.END, line[pos:], base_tag)
                break

    def _insert_markdown(widget, text):
        parts = re.split(r"```", text)
        for i, part in enumerate(parts):
            if i % 2 == 1:
                block = part.strip()
                if re.match(r"^\w+\s*\n", block):
                    block = re.sub(r"^\w+\s*\n", "", block, count=1)
                widget.insert(tk.END, "\n" + block + "\n", "md_block")
                continue
            lines = part.split("\n")
            for line_idx, line in enumerate(lines):
                stripped = line.strip()
                if re.match(r"^\|[\s\-:|]+\|$", stripped):
                    continue
                if stripped.startswith("|") and "|" in stripped[1:]:
                    cells = [c.strip() for c in stripped.split("|")[1:-1]]
                    widget.insert(tk.END, "\n", "md_table")
                    for ci, cell in enumerate(cells):
                        _insert_inline_md(widget, cell, "md_table")
                        if ci < len(cells) - 1:
                            widget.insert(tk.END, "  │  ", "md_table")
                    widget.insert(tk.END, "\n", "md_table")
                    continue
                heading_m = re.match(r"^#+\s*(.+)$", stripped)
                if heading_m:
                    widget.insert(tk.END, "\n" + heading_m.group(1).strip() + "\n", "md_heading")
                    continue
                if not stripped:
                    widget.insert(tk.END, "\n", "body")
                    continue
                _insert_inline_md(widget, line, "body")
                if line_idx < len(lines) - 1:
                    widget.insert(tk.END, "\n", "body")

    def append_message(who, text, tag, render_md=False):
        chat.config(state=tk.NORMAL)
        chat.insert(tk.END, f"\n{who}\n", tag)
        body_tag = "teacher_body" if tag == "teacher" else "user_body"
        if render_md:
            _insert_markdown(chat, text)
            chat.insert(tk.END, "\n", body_tag)
        else:
            chat.insert(tk.END, text + "\n", body_tag)
        chat.config(state=tk.DISABLED)
        chat.see(tk.END)

    append_message("Teacher", "Ask me anything about coding or studying.", "teacher", render_md=False)

    input_wrap = tk.Frame(root, bg=border)
    input_wrap.pack(fill=tk.X)

    input_frame = tk.Frame(input_wrap, bg=bg_dark, padx=14, pady=12)
    input_frame.pack(fill=tk.X)

    entry = tk.Entry(
        input_frame,
        bg=bg_input,
        fg=fg_light,
        insertbackground=accent,
        relief=tk.FLAT,
        font=("Segoe UI", 11),
        highlightthickness=1,
        highlightbackground=border,
        highlightcolor=accent,
    )
    entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=8, padx=(0, 10))

    def send():
        text = entry.get().strip()
        if not text:
            return
        entry.delete(0, tk.END)
        append_message("You", text, "user")

        chat.config(state=tk.NORMAL)
        think_start = chat.index(tk.END)
        chat.insert(tk.END, "\nThinking...\n", "thinking")
        chat.config(state=tk.DISABLED)
        chat.see(tk.END)

        def run():
            try:
                reply = get_reply(text)
            except Exception as e:
                reply = str(e)
            root.after(0, lambda: finish(reply, think_start))

        def finish(reply, think_start):
            chat.config(state=tk.NORMAL)
            chat.delete(think_start, tk.END)
            chat.config(state=tk.DISABLED)
            append_message("Teacher", clean_teacher_reply(reply), "teacher", render_md=True)

        threading.Thread(target=run, daemon=True).start()

    tk.Button(
        input_frame,
        text="Send",
        bg=accent,
        fg=bg_dark,
        relief=tk.FLAT,
        font=("Segoe UI", 10, "bold"),
        command=send,
        cursor="hand2",
    ).pack(side=tk.RIGHT, ipadx=18, ipady=6)

    entry.bind("<Return>", lambda e: send())

    root.mainloop()


if __name__ == "__main__":
    create_ui()
