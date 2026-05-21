#!/usr/bin/env python3
"""Generate executive ADR PDF (max 2 pages)."""

import urllib.request
from pathlib import Path

from fpdf import FPDF

FONT_URLS = {
    "DejaVuSans.ttf": "https://github.com/py-pdf/fpdf2/raw/master/test/fonts/DejaVuSans.ttf",
    "DejaVuSans-Bold.ttf": "https://github.com/py-pdf/fpdf2/raw/master/test/fonts/DejaVuSans-Bold.ttf",
    "DejaVuSans-Oblique.ttf": "https://github.com/py-pdf/fpdf2/raw/master/test/fonts/DejaVuSans-Oblique.ttf",
}


def ensure_fonts() -> Path:
    fonts_dir = Path(__file__).parent.parent / "fonts"
    fonts_dir.mkdir(exist_ok=True)
    for name, url in FONT_URLS.items():
        path = fonts_dir / name
        if not path.exists():
            urllib.request.urlretrieve(url, path)
    return fonts_dir


class ADRPDF(FPDF):
    def __init__(self) -> None:
        super().__init__()
        self.set_auto_page_break(auto=True, margin=12)
        fonts_dir = ensure_fonts()
        self.add_font("DejaVuSans", "", str(fonts_dir / "DejaVuSans.ttf"))
        self.add_font("DejaVuSans", "B", str(fonts_dir / "DejaVuSans-Bold.ttf"))
        self.add_font("DejaVuSans", "I", str(fonts_dir / "DejaVuSans-Oblique.ttf"))

    def header(self) -> None:
        self.set_font("DejaVuSans", "", 7)
        self.set_text_color(128, 128, 128)
        self.cell(0, 8, "Golden Path Platform — Architecture Decision Record (Executive)", align="L")
        self.cell(0, 8, f"Page {self.page_no()}/2", align="R")
        self.ln(6)
        self.set_draw_color(0, 102, 204)
        self.set_line_width(0.5)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(3)

    def footer(self) -> None:
        self.set_y(-12)
        self.set_font("DejaVuSans", "", 7)
        self.set_text_color(128, 128, 128)
        self.cell(0, 8, "Confidential — Gila Software Platform Engineering | v0.1.0 | 2024-05-20", align="C")


def main() -> None:
    output_path = Path(__file__).parent.parent / "docs" / "output" / "ADR-Executive.pdf"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    pdf = ADRPDF()

    # ── PAGE 1 ───────────────────────────────────────────────────────────────
    pdf.add_page()
    pdf.set_font("DejaVuSans", "B", 16)
    pdf.set_text_color(0, 102, 204)
    pdf.cell(0, 10, "Architecture Decision Record", align="C")
    pdf.ln(6)
    pdf.set_font("DejaVuSans", "", 11)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 8, "Golden Path Platform — Shared Engineering Ecosystem", align="C")
    pdf.ln(10)

    # 1. Architecture Diagram
    pdf.set_font("DejaVuSans", "B", 12)
    pdf.set_text_color(33, 33, 33)
    pdf.cell(0, 8, "1. Architecture Diagram")
    pdf.ln(6)
    pdf.set_font("DejaVuSans", "", 9)
    pdf.set_text_color(40, 40, 40)
    pdf.multi_cell(0, 5, "The Golden Path Platform consists of two independent, distributable packages that create a shared ecosystem across 10+ engineering teams:")
    pdf.ln(2)

    pdf.set_font("DejaVuSans", "B", 9)
    pdf.cell(0, 5, "Component A — CLI (Python, uv)")
    pdf.ln(5)
    pdf.set_font("DejaVuSans", "", 9)
    pdf.multi_cell(0, 5, "Developer-facing interface for project scaffolding (goldenpath init), git governance (validate work-id), standards enforcement (standards), local environment bootstrap (local env), and DORA reporting (dora report). Distributed via uv tool install from Git.")
    pdf.ln(2)

    pdf.set_font("DejaVuSans", "B", 9)
    pdf.cell(0, 5, "Component B — Framework (TypeScript, pnpm)")
    pdf.ln(5)
    pdf.set_font("DejaVuSans", "", 9)
    pdf.multi_cell(0, 5, "Infrastructure and CI/CD framework providing: ServiceStack (polyglot CDK construct for Lambda + API Gateway + DynamoDB + SNS + X-Ray), generatePRPipeline() and generateIntegrationPipeline() (type-safe GitHub Actions generators), and DoraTelemetry (standardized metric emission). Distributed via pnpm from Git.")
    pdf.ln(2)

    pdf.set_font("DejaVuSans", "B", 9)
    pdf.cell(0, 5, "Integration & Wiring")
    pdf.ln(5)
    pdf.set_font("DejaVuSans", "", 9)
    pdf.multi_cell(0, 5, "Both tools consume goldenpath.yaml configuration and emit identical DORA event schemas (JSONL). This ensures Deployment Frequency, Lead Time, Change Failure Rate, and MTTR are comparable across Python, Go, TypeScript, and Clojure teams. The CLI manages local validation and git hooks; the Framework generates CI/CD pipelines that deploy AWS infrastructure and emit telemetry.")
    pdf.ln(4)

    # 2. Homologation
    pdf.set_font("DejaVuSans", "B", 12)
    pdf.set_text_color(33, 33, 33)
    pdf.cell(0, 8, "2. Homologation — Ensuring 10+ Teams Adopt the Platform")
    pdf.ln(6)
    pdf.set_font("DejaVuSans", "", 9)
    pdf.set_text_color(40, 40, 40)
    pdf.multi_cell(0, 5, "Adoption is driven by making compliance the path of least resistance:")
    pdf.ln(1)

    items = [
        "Convention over Configuration: goldenpath init scaffolds compliant projects automatically. Deviating requires manual effort.",
        "Git Hooks: Pre-push validation runs standards, Work ID validation, and test execution before code reaches remote.",
        "CI/CD Gate: PR pipelines fail if goldenpath standards --strict does not pass.",
        "Default Onboarding: New services must use goldenpath init; a template repository accelerates bootstrapping.",
        "Metrics Visibility: DORA dashboards expose team performance, making non-compliance visible to engineering leadership.",
        "Inner-Source Incentives: Contributing teams get steering committee representation and priority platform support.",
    ]
    for item in items:
        pdf.set_x(12)
        pdf.cell(4, 5, "-", align="L")
        pdf.multi_cell(0, 5, item)

    pdf.ln(2)
    pdf.set_font("DejaVuSans", "I", 8)
    pdf.multi_cell(0, 5, "Rollout: 2 pilot teams (4 weeks) → 4 expansion teams (8 weeks) → all 10+ teams (12 weeks). Success criteria: <5% standards failures and >80% hook installation.")

    # ── PAGE 2 ───────────────────────────────────────────────────────────────
    pdf.add_page()

    # 3. Scalability
    pdf.set_font("DejaVuSans", "B", 12)
    pdf.set_text_color(33, 33, 33)
    pdf.cell(0, 8, "3. Scalability — Avoiding the Platform Bottleneck")
    pdf.ln(6)
    pdf.set_font("DejaVuSans", "", 9)
    pdf.set_text_color(40, 40, 40)
    pdf.multi_cell(0, 5, "The platform team avoids becoming a bottleneck through three design principles:")
    pdf.ln(1)

    pdf.set_font("DejaVuSans", "B", 9)
    pdf.cell(0, 5, "Composition over Inheritance")
    pdf.ln(4)
    pdf.set_font("DejaVuSans", "", 9)
    pdf.multi_cell(0, 5, "Teams extend ServiceStack to add team-specific resources without modifying core framework code. The platform owns the contract; teams own the extensions.")
    pdf.ln(1)

    pdf.set_font("DejaVuSans", "B", 9)
    pdf.cell(0, 5, "Self-Service by Default")
    pdf.ln(4)
    pdf.set_font("DejaVuSans", "", 9)
    pdf.multi_cell(0, 5, "Custom Lambda environment variables, additional API routes, alarm thresholds, and test commands are configurable via stack properties and goldenpath.yaml — zero platform team touch required.")
    pdf.ln(1)

    pdf.set_font("DejaVuSans", "B", 9)
    pdf.cell(0, 5, "Decentralized Decision Making")
    pdf.ln(4)
    pdf.set_font("DejaVuSans", "", 9)
    pdf.multi_cell(0, 5, "Lightweight changes (<2 files, no API change) are self-merged by teams. Standard features require one Trusted Committer review. Only architectural changes (breaking, security model) escalate to the Platform Steering Committee.")
    pdf.ln(4)

    # 4. Shift-Left Strategy
    pdf.set_font("DejaVuSans", "B", 12)
    pdf.set_text_color(33, 33, 33)
    pdf.cell(0, 8, "4. Shift-Left Strategy — Reducing Defect Detection Time")
    pdf.ln(6)
    pdf.set_font("DejaVuSans", "", 9)
    pdf.set_text_color(40, 40, 40)
    pdf.multi_cell(0, 5, "Validation is pushed as early as possible in the development lifecycle:")
    pdf.ln(1)

    table_data = [
        ("Stage", "Target Time", "Defect Coverage"),
        ("IDE / Editor", "Real-time", "15%"),
        ("Pre-commit (commit-msg hook)", "< 1s", "10%"),
        ("Pre-push (goldenpath hooks)", "< 2 min", "30%"),
        ("PR Pipeline (GitHub Actions)", "< 5 min", "35%"),
        ("Integration Pipeline", "< 15 min", "9%"),
        ("Production (alarms + rollback)", "< 5 min MTTR", "1%"),
    ]

    col_widths = [70, 50, 50]
    for i, row in enumerate(table_data):
        pdf.set_font("DejaVuSans", "B" if i == 0 else "", 8)
        pdf.set_fill_color(230, 230, 230) if i == 0 else pdf.set_fill_color(255, 255, 255)
        for j, cell in enumerate(row):
            pdf.cell(col_widths[j], 5, cell, border=1, fill=True)
        pdf.ln(5)

    pdf.ln(3)
    pdf.set_font("DejaVuSans", "", 9)
    pdf.multi_cell(0, 5, "Amazon Q Developer provides AI-assisted PR analysis (security, performance, best practices) as an additional automated review layer before human review. LocalStack ensures local environment parity with production, eliminating 'works on my machine' defects detected only in staging.")
    pdf.ln(4)

    # Decision Log (compact)
    pdf.set_font("DejaVuSans", "B", 10)
    pdf.cell(0, 6, "Decision Log")
    pdf.ln(5)
    pdf.set_font("DejaVuSans", "", 8)
    decisions = [
        "ADR-001 Python for CLI — Team expertise, uv packaging",
        "ADR-002 TypeScript for Framework — CDK-native, type-safe workflows",
        "ADR-003 uv over pip — Modern, fast, reproducible",
        "ADR-004 pnpm over npm — Monorepo support, disk efficient",
        "ADR-005 LocalStack — AWS parity, zero cloud cost",
        "ADR-006 JSONL for DORA — Append-only, streamable",
        "ADR-007 OIDC for AWS auth — No long-lived secrets",
    ]
    for d in decisions:
        pdf.set_x(12)
        pdf.cell(3, 4, "•", align="L")
        pdf.cell(0, 4, d, ln=True)

    pdf.output(str(output_path))
    print(f"Generated Executive ADR PDF: {output_path}")


if __name__ == "__main__":
    main()
