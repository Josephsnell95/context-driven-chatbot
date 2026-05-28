"""
context-driven-chatbot — Orchestrator for parsing modules
Extracts meaningful content from a GitHub Pages site and outputs
a clean supplementary context file for use in the chatbot system prompt.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

from html_extractor import parse_file

# ── Configuration ────────────────────────────────────────────────────────────

OUTPUT_FILE = Path(__file__).parent.parent / "supplementary-context.txt"

# ── Main ─────────────────────────────────────────────────────────────────────

def main():

    load_dotenv()

    PAGES_REPO_PATH = os.getenv("PAGES_REPO_PATH")

    if not PAGES_REPO_PATH:
        raise ValueError(
            "PAGES_REPO_PATH not set."
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

    # Write output
    output = "\n\n" + ("-"  * 60 + "\n\n").join(results)
    OUTPUT_FILE.write_text(output, encoding="utf-8")

    print(f"\n Supplementary context written to: {OUTPUT_FILE}")
    print(f"  {len(output)} characters extracted")

if __name__ == "__main__":
    main()