import os
import re
from pathlib import Path


TYPE_BY_DIR = {
    "syllabus": "theory",
    "notes": "theory",
    "question_papers": "question",
}
TYPE_KEYWORDS = ("method", "example", "theory", "question")
CHAPTER_PATTERN = re.compile(r"(?:ch|chapter)[_\s\-]?(\d+|[\w]+)", re.I)


def _infer_chapter(filepath: str) -> str:
    name = Path(filepath).stem.lower()
    m = CHAPTER_PATTERN.search(name)
    if m:
        return m.group(0).replace("_", " ").replace("-", " ").strip()
    return "unknown"


def _infer_subject(filepath: str, data_root: Path) -> str:
    try:
        rel = Path(filepath).resolve().relative_to(data_root)
        parts = rel.parts
        if len(parts) >= 3:
            return parts[1]  # e.g. notes/Mathematics/ch1.txt -> Mathematics
        if len(parts) == 2 and not parts[1].endswith(".txt"):
            return parts[1]
        return parts[0] if parts else Path(filepath).parent.name or "unknown"
    except (ValueError, IndexError):
        return Path(filepath).parent.name or "unknown"


def _infer_type_from_path(filepath: str, base_dir: str, data_root: Path) -> str:
    rel = Path(filepath).resolve()
    try:
        r = rel.relative_to(data_root)
        parts = r.parts
    except ValueError:
        parts = ()
    dir_type = TYPE_BY_DIR.get(base_dir, "theory")
    if base_dir == "question_papers":
        return "question"
    if base_dir == "syllabus":
        return "theory"
    stem = rel.stem.lower()
    for t in ("method", "example", "theory", "question"):
        if t in stem or (len(parts) >= 2 and parts[0].lower() == t):
            return t
    return dir_type


def load_documents(project_root: str | Path | None = None) -> list[dict]:
    if project_root is None:
        root = Path(__file__).resolve().parent.parent
    else:
        root = Path(project_root)
    data_root = root / "data"
    out = []
    for base in ("syllabus", "notes", "question_papers"):
        dir_path = data_root / base
        if not dir_path.is_dir():
            continue
        for f in dir_path.rglob("*.txt"):
            try:
                text = f.read_text(encoding="utf-8", errors="replace").strip()
            except Exception:
                continue
            if not text:
                continue
            rel_path = f.relative_to(root)
            source_file = str(rel_path).replace("\\", "/")
            subject = _infer_subject(str(f), data_root)
            chapter = _infer_chapter(str(f))
            doc_type = _infer_type_from_path(str(f), base, data_root)
            out.append({
                "source_file": source_file,
                "content": text,
                "subject": subject,
                "chapter": chapter,
                "type": doc_type,
            })
    return out
