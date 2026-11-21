"""Generate README proof images from live screenshots and measured project facts.

Run from the repository root with the already-installed matplotlib and Pillow.
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from matplotlib import font_manager
from PIL import Image, ImageDraw, ImageFont, ImageOps

ASSETS = Path(__file__).with_name("assets")
INK = "#12213f"
BLUE = "#2056d3"
TEAL = "#0e9384"
AMBER = "#ffb547"
SOFT = "#eef3ff"


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    props = font_manager.FontProperties(family="DejaVu Sans", weight="bold" if bold else "normal")
    return ImageFont.truetype(font_manager.findfont(props), size)


def architecture() -> None:
    fig, ax = plt.subplots(figsize=(13, 6.4), dpi=160)
    ax.set_xlim(0, 13)
    ax.set_ylim(0, 6.4)
    ax.axis("off")
    fig.patch.set_facecolor("#f7f9fd")
    ax.text(0.5, 5.85, "TalentOS Stage 1 — three skill pillars", fontsize=20, weight="bold", color=INK)
    ax.text(0.5, 5.42, "One local workspace, three engineering disciplines, no external API cost.", fontsize=11, color="#52627d")

    columns = [
        (0.5, BLUE, "FRONTEND", "Next.js 16 · TypeScript", [
            "Workspace onboarding", "HR-friendly screens", "Developer Mode JSON",
            "SVG loader + skeletons", "Role and permission chips",
        ]),
        (4.85, TEAL, "BACKEND", "FastAPI · SQLite", [
            "Tenant isolation + RBAC", "Tenant-safe endpoints", "Rate limits and security headers",
            "Indexed queries with WAL", "Idempotent local signup",
        ]),
        (9.2, AMBER, "AI", "Offline inference", [
            "Resume parsing", "Weighted rubric scoring", "Citation guardrails",
            "Interview copilot", "Hybrid talent search",
        ]),
    ]
    for x, color, title, subtitle, items in columns:
        box = FancyBboxPatch((x, 1.25), 3.3, 3.85, boxstyle="round,pad=0.18,rounding_size=0.18",
                             facecolor="white", edgecolor=color, linewidth=2)
        ax.add_patch(box)
        ax.add_patch(FancyBboxPatch((x + 0.18, 4.58), 2.94, 0.42,
                                    boxstyle="round,pad=0.08,rounding_size=0.12",
                                    facecolor=color, edgecolor="none"))
        ax.text(x + 1.65, 4.79, title, ha="center", va="center", color="white", fontsize=12, weight="bold")
        ax.text(x + 1.65, 4.28, subtitle, ha="center", va="center", color="#52627d", fontsize=10)
        for index, item in enumerate(items):
            ax.text(x + 0.32, 3.82 - index * 0.5, f"•  {item}", color=INK, fontsize=9.4, va="center")

    for x1, x2 in ((3.8, 4.85), (8.15, 9.2)):
        ax.add_patch(FancyArrowPatch((x1, 3.15), (x2, 3.15), arrowstyle="-|>", mutation_scale=18,
                                     color="#8ca0c4", linewidth=1.8))
    ax.text(6.5, 0.72, "Local-only data plane: SQLite at ./data/talentos.db  ·  resume files at ./data/storage",
            ha="center", fontsize=10.5, color="#52627d")
    fig.savefig(ASSETS / "10-architecture-matplotlib.png", bbox_inches="tight")
    plt.close(fig)


def proof_cards() -> None:
    fig, ax = plt.subplots(figsize=(12, 5.2), dpi=160)
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 5.2)
    ax.axis("off")
    fig.patch.set_facecolor("#f7f9fd")
    ax.text(0.5, 4.72, "Stage 1 proof, measured from this repository", fontsize=19, weight="bold", color=INK)
    ax.text(0.5, 4.3, "pytest, TypeScript, browser checks and live screenshots", fontsize=10.5, color="#52627d")

    cards = [
        (0.5, "98", "automated tests pass", BLUE),
        (3.4, "7", "phases completed", TEAL),
        (6.3, "9", "feature pages with guided JSON", "#7a5af8"),
        (9.2, "3", "skill pillars demonstrated", AMBER),
    ]
    for x, value, label, color in cards:
        ax.add_patch(FancyBboxPatch((x, 1.0), 2.35, 2.75, boxstyle="round,pad=0.16,rounding_size=0.18",
                                    facecolor="white", edgecolor="#d9e2f2", linewidth=1.2))
        ax.add_patch(FancyBboxPatch((x + 0.18, 3.18), 1.99, 0.16, boxstyle="round,pad=0.02",
                                    facecolor=color, edgecolor="none"))
        ax.text(x + 1.175, 2.4, value, ha="center", va="center", fontsize=34, weight="bold", color=color)
        ax.text(x + 1.175, 1.55, label, ha="center", va="center", fontsize=9.6, color="#52627d")
    ax.text(6.0, 0.48, "98 passed · TypeScript clean · 0 browser console errors", ha="center",
            fontsize=11, weight="bold", color=INK)
    fig.savefig(ASSETS / "11-stage1-proof-matplotlib.png", bbox_inches="tight")
    plt.close(fig)


def collage() -> None:
    canvas = Image.new("RGB", (1640, 1120), "#f7f9fd")
    draw = ImageDraw.Draw(canvas)
    title = _font(32, True)
    sub = _font(15)
    caption = _font(18, True)
    draw.text((40, 28), "What a recruiter sees on first open", font=title, fill=INK)
    draw.text((42, 70), "Live screenshots from the seeded org-1 demo workspace", font=sub, fill="#52627d")

    tiles = [
        ("01-onboarding-login.png", "1 · Open the workspace", (40, 115, 800, 610)),
        ("02-recruiter-overview.png", "2 · Today at a glance", (820, 115, 1600, 610)),
        ("03-guided-journey.png", "3 · Guided hiring journey", (40, 645, 800, 1080)),
        ("05-review-candidates.png", "4 · Evidence-led review", (820, 645, 1600, 1080)),
    ]
    for filename, label, box in tiles:
        source = Image.open(ASSETS / filename).convert("RGB")
        fitted = ImageOps.fit(source, (box[2] - box[0], box[3] - box[1] - 42), method=Image.Resampling.LANCZOS)
        canvas.paste(fitted, (box[0], box[1] + 42))
        draw.rounded_rectangle((box[0], box[1], box[2], box[1] + 38), radius=10, fill=BLUE)
        draw.text((box[0] + 14, box[1] + 7), label, font=caption, fill="white")
    canvas.save(ASSETS / "12-first-open-collage-pil.png")


def developer_strip() -> None:
    source = Image.open(ASSETS / "06-developer-mode-json.png").convert("RGB")
    canvas = Image.new("RGB", (1420, 780), "#f7f9fd")
    draw = ImageDraw.Draw(canvas)
    draw.text((28, 24), "Every feature ends with guided JSON", font=_font(28, True), fill=INK)
    draw.text((30, 64), "Developer Mode is collapsed for recruiters and expands for builders.", font=_font(15), fill="#52627d")
    fitted = ImageOps.fit(source, (1364, 636), method=Image.Resampling.LANCZOS)
    canvas.paste(fitted, (28, 108))
    draw.rounded_rectangle((40, 120, 430, 162), radius=10, fill=TEAL)
    draw.text((56, 128), "Guided process · JSON only", font=_font(18, True), fill="white")
    canvas.save(ASSETS / "13-developer-json-pil.png")


if __name__ == "__main__":
    ASSETS.mkdir(parents=True, exist_ok=True)
    architecture()
    proof_cards()
    collage()
    developer_strip()
    print("Generated 4 README visuals in", ASSETS)
