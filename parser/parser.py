"""
context-driven-chatbot — Orchestrator for parsing modules
Extracts meaningful content from a GitHub Pages site and outputs
a clean supplementary context file for use in the chatbot system prompt.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

from html_extractor import parse_file
from notebook_extractor import extract_notebook

# ── Configuration ────────────────────────────────────────────────────────────

OUTPUT_FILE = Path(__file__).parent.parent / "supplementary-context.txt"

# ── Main ─────────────────────────────────────────────────────────────────────

def main():

    load_dotenv()

    PAGES_REPO_PATH = os.getenv("PAGES_REPO_PATH")

    if not PAGES_REPO_PATH:
        raise ValueError(
            "PAGES_REPO_PATH not set.\n"
            "Copy .env.example to .env and fill in your path"
        )
    
    pages_path = Path(PAGES_REPO_PATH)

    if not pages_path.exists():
        raise FileNotFoundError(
            f"Pages repo not found at: {pages_path}\n"
            "Check PAGES_REPO_PATH in your .env file"
        )

    # Find all HTML files, skip the footer partial
    html_files = [
        p for p in pages_path.rglob("*.html")
        if "footer.html" not in p.name
    ]

    print(f"Found {len(html_files)} HTML files to parse:")
    for f in html_files:
        print(f" {f.relative_to(pages_path)}")
    
    # Parse each file
    results = []
    for html_file in sorted(html_files):
        print(f"\nParsing: {html_file.name}...")
        extracted = parse_file(html_file)
        results.append(extracted)
        print(f" Done.")

    NOTEBOOKS_REPO_PATH = os.getenv("NOTEBOOK_REPO_PATH")

    if NOTEBOOKS_REPO_PATH:
        notebooks_path = Path(NOTEBOOKS_REPO_PATH)
        if not notebooks_path.exists():
            print(f"Warning: NOTEBOOK_REPO_PATH set but path not found: {notebooks_path} — skipping")
        else:
            notebook_files = list(notebooks_path.rglob("*.ipynb"))
            print(f"\nFound {len(notebook_files)} notebook files to parse:")
            for f in notebook_files:
                print(f"  {f.relative_to(notebooks_path)}")
            for notebook_file in sorted(notebook_files):
                print(f"\nParsing: {notebook_file.name}...")
                extracted = extract_notebook(notebook_file)
                results.append(extracted)
                print(f"  Done.")
    else:
        print("\nNOTEBOOK_REPO_PATH not set — skipping notebooks")

    # Write output
    output = "\n\n" + ("-"  * 60 + "\n\n").join(results)
    OUTPUT_FILE.write_text(output, encoding="utf-8")

    print(f"\n Supplementary context written to: {OUTPUT_FILE}")
    print(f"  {len(output)} characters extracted")

if __name__ == "__main__":
    main()