#!/usr/bin/env python3
"""Generate ADR PDF from markdown source."""

import re
from pathlib import Path

from fpdf import FPDF


class ADRPDF(FPDF):
    def __init__(self) -> None:
        super().__init__()
        self.set_auto_page_break(auto=True, margin=15)
        fonts_dir = Path(__file__).parent.parent / "fonts"
        self.add_font("DejaVuSans", "", str(fonts_dir / "DejaVuSans.ttf"))
        self.add_font("DejaVuSans", "B", str(fonts_dir / "DejaVuSans-Bold.ttf"))
        self.add_font("DejaVuSans", "I", str(fonts_dir / "DejaVuSans-Oblique.ttf"))
        self.add_font("DejaVuSans", "BI", str(fonts_dir / "DejaVuSans-BoldOblique.ttf"))

    def header(self) -> None:
        if self.page_no() > 1:
            self.set_font("DejaVuSans", "", 8)
            self.set_text_color(128, 128, 128)
            self.cell(0, 10, "Golden Path Platform - Architecture Decision Record", align="L")
            self.cell(0, 10, f"Page {self.page_no()}", align="R")
            self.ln(10)
            self.set_draw_color(200, 200, 200)
            self.line(10, self.get_y(), 200, self.get_y())
            self.ln(5)

    def footer(self) -> None:
        self.set_y(-15)
        self.set_font("DejaVuSans", "", 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, "Confidential - Gila Software Platform Engineering", align="C")

    def cover_page(self, title: str, subtitle: str, meta: dict[str, str]) -> None:
        self.add_page()
        self.set_font("DejaVuSans", "B", 24)
        self.set_text_color(0, 102, 204)
        self.cell(0, 20, "GILA SOFTWARE", align="C")
        self.ln(12)
        self.set_font("DejaVuSans", "", 12)
        self.set_text_color(100, 100, 100)
        self.cell(0, 10, "Enterprise Platform Engineering", align="C")
        self.ln(30)
        self.set_draw_color(0, 102, 204)
        self.set_line_width(1.5)
        self.line(40, self.get_y(), 170, self.get_y())
        self.ln(8)
        self.set_font("DejaVuSans", "B", 20)
        self.set_text_color(33, 33, 33)
        self.multi_cell(0, 12, title, align="C")
        self.ln(4)
        self.set_font("DejaVuSans", "", 14)
        self.set_text_color(80, 80, 80)
        self.multi_cell(0, 10, subtitle, align="C")
        self.ln(15)
        self.set_draw_color(0, 102, 204)
        self.set_line_width(1.5)
        self.line(40, self.get_y(), 170, self.get_y())
        self.ln(15)
        self.set_font("DejaVuSans", "", 11)
        self.set_text_color(60, 60, 60)
        for key, value in meta.items():
            self.set_font("DejaVuSans", "B", 11)
            self.cell(50, 8, f"{key}:", align="R")
            self.set_font("DejaVuSans", "", 11)
            self.cell(0, 8, value, align="L")
            self.ln(8)
        self.ln(20)
        self.set_font("DejaVuSans", "I", 10)
        self.set_text_color(120, 120, 120)
        self.multi_cell(
            0, 8,
            "This document contains architectural decisions for the Golden Path Developer Experience Platform. "
            "It addresses homologation, scalability, and shift-left strategies for 10+ engineering teams.",
            align="C",
        )

    def render_text(self, text: str) -> None:
        """Render plain text with basic formatting."""
        lines = text.split("\n")
        for line in lines:
            line = line.rstrip()
            if not line:
                self.ln(4)
                continue
            self.set_x(10)
            if line.startswith("## "):
                self.set_font("DejaVuSans", "B", 14)
                self.set_text_color(0, 102, 204)
                self.cell(0, 10, line[3:].strip())
                self.ln(10)
                continue
            if line.startswith("### "):
                self.set_font("DejaVuSans", "B", 12)
                self.set_text_color(50, 50, 50)
                self.cell(0, 8, line[4:].strip())
                self.ln(8)
                continue
            if line.strip().startswith("- "):
                text_content = line.strip()[2:]
                self.set_font("DejaVuSans", "", 10)
                self.set_text_color(40, 40, 40)
                self.cell(5, 6, "", align="L")
                self.cell(5, 6, "-", align="L")
                self.multi_cell(0, 6, self._clean(text_content))
                continue
            match = re.match(r"^\s*(\d+)\.\s+(.*)$", line)
            if match:
                num, text_content = match.groups()
                self.set_font("DejaVuSans", "", 10)
                self.set_text_color(40, 40, 40)
                self.cell(5, 6, "", align="L")
                self.cell(8, 6, f"{num}.", align="L")
                self.multi_cell(0, 6, self._clean(text_content))
                continue
            self.set_font("DejaVuSans", "", 10)
            self.set_text_color(40, 40, 40)
            self.multi_cell(0, 6, self._clean(line))

    def _clean(self, text: str) -> str:
        text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
        text = re.sub(r"__(.+?)__", r"\1", text)
        text = re.sub(r"`(.+?)`", r"\1", text)
        text = re.sub(r"\[(.+?)\]\(.+?\)", r"\1", text)
        return text.strip()


def extract_text_content(md_text: str) -> str:
    """Extract text content, skipping ASCII art code blocks."""
    lines = md_text.split("\n")
    result = []
    in_code = False
    for line in lines:
        if line.startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            # Skip ASCII art lines (lines with many box-drawing or repeated chars)
            if len(line) > 100 or set(line).issubset(set(" |-+/\\<>[]{}()*=_.:@#~`\"'")):
                continue
            result.append(line)
            continue
        result.append(line)
    return "\n".join(result)


def main() -> None:
    adr_path = Path(__file__).parent.parent / "docs" / "ADR.md"
    output_path = Path(__file__).parent.parent / "docs" / "output" / "ADR.pdf"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    md_text = adr_path.read_text(encoding="utf-8")
    text_content = extract_text_content(md_text)

    pdf = ADRPDF()
    pdf.cover_page(
        title="Architecture Decision Record",
        subtitle="Golden Path Platform - Shared Engineering Ecosystem",
        meta={
            "Version": "0.1.0",
            "Date": "2024-05-20",
            "Author": "Platform Engineering",
            "Status": "Approved",
            "Classification": "Internal",
        },
    )
    pdf.add_page()
    pdf.render_text(text_content)
    pdf.output(str(output_path))
    print(f"Generated ADR PDF: {output_path}")


if __name__ == "__main__":
    main()
