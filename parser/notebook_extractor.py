"""
Notebook extractor — parses Jupyter notebook files (.ipynb)
and returns clean text for use in the chatbot system prompt.
"""

import json
from pathlib import Path

# ── Helpers ──────────────────────────────────────────────────────────────────

def extract_markdown_cell(cell: dict) -> str:
    """Returns full markdown cell as plaintext"""
    return "\n".join(cell["source"])

def extract_code_cell(cell: dict) -> str:
    """Returns only import, from and comments from code cells"""
    kept = []
    for line in cell["source"]:
        if line.startswith(("import", "from")):
            kept.append(line)
        elif "#" in line:
            kept.append(line.partition("#")[2])
    return "\n".join(kept)


# ── Configuration ────────────────────────────────────────────────────────────

# Dictionary to map cell types
CELL_EXTRACTORS = {
    "markdown": extract_markdown_cell,
    "code": extract_code_cell,
}


def extract_notebook(notebook_path: Path) -> str:
    """
    Parse a single .ipynb file and return extracted text.
    Targets cell types markdown and code.
    """
    with open(notebook_path, encoding="utf-8", errors="replace") as f:
        notebook = json.load(f)
    sections = []
    for cell in notebook["cells"]:
        if cell["cell_type"] in CELL_EXTRACTORS:
            sections.append(CELL_EXTRACTORS[cell["cell_type"]](cell))
    return f"=== {notebook_path.stem} ===\n" + "\n\n".join(sections)