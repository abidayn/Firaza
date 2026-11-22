"""Build the Project Brief (.docx) from submission/brief/project_brief_draft.md.

Needs python-docx (MIT):  pip install python-docx
Run from the repo root:   .venv/Scripts/python submission/brief/build_brief.py
Supports the Markdown subset used in the draft: #/##/### headings, paragraphs,
'-' bullets, '1.' numbered items, pipe tables, images ![caption](path), **bold**, `code`.
Lines starting with '>' are author notes and are skipped.
"""
import os
import re
import sys
from pathlib import Path

if os.getenv("PYLIB"):
    sys.path.insert(0, os.environ["PYLIB"])

from docx import Document  # noqa: E402
from docx.enum.table import WD_TABLE_ALIGNMENT  # noqa: E402
from docx.enum.text import WD_ALIGN_PARAGRAPH  # noqa: E402
from docx.oxml import OxmlElement  # noqa: E402
from docx.oxml.ns import qn  # noqa: E402
from docx.shared import Cm, Pt, RGBColor  # noqa: E402

HERE = Path(__file__).resolve().parent
SRC = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else HERE / "project_brief_draft.md"
OUT = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else HERE / "Project Brief - DB15-I036.docx"
FONT = "Inter"
PURPLE = RGBColor(0x3C, 0x34, 0x89)

doc = Document()
sec = doc.sections[0]
sec.page_width, sec.page_height = Cm(21), Cm(29.7)
for side in ("left_margin", "right_margin", "top_margin", "bottom_margin"):
    setattr(sec, side, Cm(2.54))

normal = doc.styles["Normal"]
normal.font.name, normal.font.size = FONT, Pt(11)
normal.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
normal.paragraph_format.line_spacing = 1.15
normal.paragraph_format.space_after = Pt(6)
for name, size in (("Title", 20), ("Heading 1", 15), ("Heading 2", 12.5), ("Heading 3", 11.5)):
    st = doc.styles[name]
    st.font.name, st.font.size, st.font.bold, st.font.color.rgb = FONT, Pt(size), True, PURPLE

INLINE = re.compile(r"(\*\*[^*]+\*\*|`[^`]+`)")


def add_runs(p, text, size=None):
    text = re.sub(r"(?<![*\w])\*([^*\n]+)\*(?![*\w])", r"\1", text)
    for part in INLINE.split(text):
        if not part:
            continue
        if part.startswith("**") and part.endswith("**"):
            r = p.add_run(part[2:-2]); r.bold = True
        elif part.startswith("`") and part.endswith("`"):
            r = p.add_run(part[1:-1]); r.font.name = "Consolas"
        else:
            r = p.add_run(part)
        if size:
            r.font.size = Pt(size)


def shade(cell, hex_color):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear"); shd.set(qn("w:color"), "auto"); shd.set(qn("w:fill"), hex_color)
    tcPr.append(shd)


def add_table(rows):
    cells = [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows]
    cells = [r for r in cells if not all(re.fullmatch(r":?-{2,}:?", c) for c in r)]
    t = doc.add_table(rows=len(cells), cols=len(cells[0]))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, row in enumerate(cells):
        for j, val in enumerate(row):
            cell = t.cell(i, j)
            cell.text = ""
            p = cell.paragraphs[0]
            p.paragraph_format.space_after = Pt(2)
            add_runs(p, val.replace("**", "") if i == 0 else val, size=9.5)
            if i == 0:
                for r in p.runs:
                    r.bold = True
                shade(cell, "EEEDFE")
    doc.add_paragraph()


lines = SRC.read_text(encoding="utf-8").splitlines()
i = 0
while i < len(lines):
    line = lines[i].rstrip()
    if not line or line.startswith(">"):
        i += 1
        continue
    if line.startswith("|"):
        block = []
        while i < len(lines) and lines[i].startswith("|"):
            block.append(lines[i]); i += 1
        add_table(block)
        continue
    m = re.match(r"!\[(.*?)\]\((.*?)\)", line)
    if m:
        img = (SRC.parent / m.group(2)).resolve()
        if img.exists():
            doc.add_picture(str(img), width=Cm(15.5))
            doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
            cap = doc.add_paragraph()
            add_runs(cap, m.group(1), size=9)
            cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        i += 1
        continue
    if line.startswith("# "):
        p = doc.add_paragraph(style="Title"); add_runs(p, line[2:])
    elif line.startswith("## "):
        p = doc.add_paragraph(style="Heading 1"); add_runs(p, line[3:])
    elif line.startswith("### "):
        p = doc.add_paragraph(style="Heading 2"); add_runs(p, line[4:])
    elif line.startswith("- "):
        p = doc.add_paragraph(style="List Bullet"); add_runs(p, line[2:])
    elif re.match(r"\d+\. ", line):
        num, rest = line.split(". ", 1)
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Cm(0.9)
        p.paragraph_format.first_line_indent = Cm(-0.6)
        p.paragraph_format.space_after = Pt(3)
        add_runs(p, f"{num}.  {rest}")
    else:
        p = doc.add_paragraph(); add_runs(p, line)
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    i += 1

footer = sec.footer.paragraphs[0]
footer.text = os.getenv("DOC_FOOTER", "Project Brief · DB15-I036 · Firaza Vendor Recommendation & Procurement Assistant")
footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
for r in footer.runs:
    r.font.size = Pt(8)

doc.save(OUT)
print("saved", OUT)
