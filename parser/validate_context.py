"""
validate_context.py — CI validation gate for context files.
Runs on every PR to the chatbot repo. Exits with code 1 if any check fails,
blocking the PR from merging.
"""

import sys
from pathlib import Path

# ── Configuration ────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).parent.parent

SUPPLEMENTARY_CONTEXT = REPO_ROOT / "supplementary-context.txt"
PERSONA = REPO_ROOT / "persona.md"

MAX_CONTEXT_CHARS = 800_000  # safe margin for Cloudflare Worker script size

PLACEHOLDER_STRINGS = ["LINK", "[PLACEHOLDER]"]

FILES_TO_CHECK_PLACEHOLDERS = [
    REPO_ROOT / "persona.md",
    REPO_ROOT / "easter-eggs.md",
]

# ── Checks ───────────────────────────────────────────────────────────────────

def check_file_exists_and_nonempty(path: Path) -> bool:
    if not path.exists():
        return False
    if path.stat().st_size == 0:
        return False
    else:
        return True

def check_context_size(path: Path, max_chars: int) -> bool:
    if len(path.read_text(encoding="utf-8")) <= max_chars:
        return True
    else:
        return False

def check_no_placeholders(files: list, placeholders: list) -> bool:
    for file in files:
        content = file.read_text(encoding="utf-8")
        for placeholder in placeholders:
            if placeholder in content:
                print(f"FAIL: '{placeholder}' found in {file.name}")
                return False
    return True


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    passed = True

    # Check 1: supplementary-context.txt exists and is non-empty
    if not check_file_exists_and_nonempty(SUPPLEMENTARY_CONTEXT):
        print("FAIL: supplementary-context.txt is missing or empty")
        passed = False
    else:
        print("PASS: supplementary-context.txt exists and is non-empty")

    # Check 2: persona.md exists and is non-empty
    if not check_file_exists_and_nonempty(PERSONA):
        print("FAIL: persona.md is missing or empty")
        passed = False
    else:
        print("PASS: persona.md exists and is non-empty")

    # Check 3: supplementary-context.txt is under the character limit
    if passed and not check_context_size(SUPPLEMENTARY_CONTEXT, MAX_CONTEXT_CHARS):
        print(f"FAIL: supplementary-context.txt exceeds {MAX_CONTEXT_CHARS:,} characters")
        passed = False
    else:
        print("PASS: supplementary-context.txt is within character limit")

    # Check 4: no placeholder strings remain in context files
    if not check_no_placeholders(FILES_TO_CHECK_PLACEHOLDERS, PLACEHOLDER_STRINGS):
        passed = False
    else:
        print("PASS: no placeholder strings found")

    if not passed:
        sys.exit(1)

    print("\nAll checks passed.")
    sys.exit(0)

if __name__ == "__main__":
    main()