"""
HTML extractor — parses a single GitHub Pages HTML file
and returns clean text for use in the chatbot system prompt.
"""

from pathlib import Path
from bs4 import BeautifulSoup

# ── Configuration ────────────────────────────────────────────────────────────

# Tags to strip entirely before extracting text
STRIP_TAGS = ["script", "style", "link", "meta", "iframe", "noscript"]

# The content class that wraps meaning sections on this site
CONTENT_SECTION_CLASS = "content-section"

# ── Helpers ──────────────────────────────────────────────────────────────────

def clean_text(text: str) -> str:
    """Normalise whitespace and strip blank lines"""
    lines = [line.strip() for line in text.splitlines()]
    lines = [line for line in lines if line]
    return "\n".join(lines)

def parse_file(html_path: Path) -> str:
    """
    Parse a single HTML file and return extracted text.
    Targets content-section div strips nav, footer, scripts.
    """
    # utf-8-sig strips the Windows BOM that can corrupt the first character of a file
    with open(html_path, encoding="utf-8-sig", errors="replace") as f:
        soup = BeautifulSoup(f, "html.parser")
    
    # Strip boiler plate tags entirely
    for tag in soup(STRIP_TAGS):
        tag.decompose()

    # Strip nav and footer by id
    for element_id in ["nav", "footer"]:
        el = soup.find(id=element_id)
        if el:
            el.decompose()
    
    # Get page title
    title = soup.find("title")
    title_text = clean_text(title.get_text()) if title else html_path.stem

    sections = []

    # Target content-section divs specifically
    content_sections = soup.find_all("div", class_=CONTENT_SECTION_CLASS)

    if content_sections:
        for section in content_sections:
            # Get section label (the small label above the h2)
            label = section.find(class_="section-label")
            label_text = clean_text(label.get_text()) if label else ""

            # Get heading
            heading = section.find(["h1", "h2", "h3"])
            heading_text = clean_text(heading.get_text()) if heading else ""

            # Get all paragraph text
            paragraphs = section.find_all("p")
            para_text = "\n".join(
                clean_text(p.get_text())
                for p in paragraphs
                if clean_text(p.get_text())
                and "section-label" not in p.get("class", [])
            )

            # Get any named items (stack, metrics, roadmap etc)
            named_items = []
            for item in section.find_all(class_=[
                "stack-name", "metric-name", "roadmap-title"
            ]):
                named_items.append(clean_text(item.get_text()))

            # Build section block
            block = []
            if label_text:
                block.append(f"[{label_text}]")
            if heading_text:
                block.append(heading_text)
            if para_text:
                block.append(para_text)
            if named_items:
                block.append("Items: " + ", ".join(named_items))

            if block:
                sections.append("\n".join(block))
        
    else:
        # Fallback - no content-section divs found, extract body text
        body = soup.find("body")
        if body:
            sections.append(clean_text(body.get_text()))

    return f"=== {title_text} ===\n" + "\n\n".join(sections)
