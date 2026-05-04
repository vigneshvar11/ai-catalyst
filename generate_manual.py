#!/usr/bin/env python3
"""
AI CatalyESt — Complete Build Manual Generator
Generates a comprehensive, visually rich PDF explaining
how the dashboard was built from scratch.
"""

import os, json, math, textwrap
from io import BytesIO
from datetime import datetime

# ── PDF ──────────────────────────────────────────────────────
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch, mm, cm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image, KeepTogether, HRFlowable, ListFlowable, ListItem,
    Flowable,
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Circle, Polygon, Group
from reportlab.graphics import renderPDF

# ── Charts ───────────────────────────────────────────────────
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np

# ═══════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════
PAGE_W, PAGE_H = A4                     # 595.27 x 841.89 pt
MARGIN = 2 * cm
CONTENT_W = PAGE_W - 2 * MARGIN         # ~481 pt

# Siemens brand palette
PETROL       = colors.HexColor('#009999')
DARK_NAVY    = colors.HexColor('#000028')
LIGHT_PETROL = colors.HexColor('#00BEDC')
GREEN        = colors.HexColor('#00FFB9')
CORAL        = colors.HexColor('#FF6B6B')
LIGHT_BG     = colors.HexColor('#F7F7F8')
CODE_BG      = colors.HexColor('#1E1E2E')
CODE_FG      = colors.HexColor('#CDD6F4')
TIP_BG       = colors.HexColor('#E8FDF5')
TIP_BORDER   = colors.HexColor('#00D68F')
WARN_BG      = colors.HexColor('#FFF8E1')
WARN_BORDER  = colors.HexColor('#FFB300')
INFO_BG      = colors.HexColor('#E3F2FD')
INFO_BORDER  = colors.HexColor('#2196F3')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_PATH = os.path.join(BASE_DIR, 'AI_CatalyESt_Build_Manual.pdf')


# ═══════════════════════════════════════════════════════════════
# PARAGRAPH STYLES
# ═══════════════════════════════════════════════════════════════
def get_styles():
    """Return dict of ParagraphStyles."""
    s = {}
    s['title'] = ParagraphStyle('Title', fontName='Helvetica-Bold', fontSize=36,
        leading=42, textColor=DARK_NAVY, alignment=TA_CENTER, spaceAfter=6)
    s['subtitle'] = ParagraphStyle('Subtitle', fontName='Helvetica', fontSize=16,
        leading=22, textColor=PETROL, alignment=TA_CENTER, spaceAfter=20)
    s['h1'] = ParagraphStyle('H1', fontName='Helvetica-Bold', fontSize=24,
        leading=30, textColor=DARK_NAVY, spaceBefore=10, spaceAfter=14)
    s['h2'] = ParagraphStyle('H2', fontName='Helvetica-Bold', fontSize=17,
        leading=22, textColor=PETROL, spaceBefore=14, spaceAfter=8)
    s['h3'] = ParagraphStyle('H3', fontName='Helvetica-Bold', fontSize=13,
        leading=17, textColor=DARK_NAVY, spaceBefore=10, spaceAfter=6)
    s['body'] = ParagraphStyle('Body', fontName='Helvetica', fontSize=10.5,
        leading=15, textColor=DARK_NAVY, alignment=TA_JUSTIFY, spaceAfter=8)
    s['body_center'] = ParagraphStyle('BodyC', fontName='Helvetica', fontSize=10.5,
        leading=15, textColor=DARK_NAVY, alignment=TA_CENTER, spaceAfter=8)
    s['caption'] = ParagraphStyle('Caption', fontName='Helvetica-Oblique', fontSize=9,
        leading=12, textColor=colors.HexColor('#6E6E73'), alignment=TA_CENTER, spaceAfter=12)
    s['code_inline'] = ParagraphStyle('CodeInline', fontName='Courier', fontSize=9.5,
        leading=13, textColor=colors.HexColor('#D63384'), backColor=colors.HexColor('#F8F0F4'))
    s['toc_item'] = ParagraphStyle('TOC', fontName='Helvetica', fontSize=12,
        leading=22, textColor=DARK_NAVY, leftIndent=20, spaceAfter=2)
    s['toc_chapter'] = ParagraphStyle('TOCCh', fontName='Helvetica-Bold', fontSize=13,
        leading=24, textColor=PETROL, spaceAfter=2)
    s['bullet'] = ParagraphStyle('Bullet', fontName='Helvetica', fontSize=10.5,
        leading=15, textColor=DARK_NAVY, leftIndent=24, bulletIndent=10,
        spaceAfter=4, bulletFontSize=10)
    s['glossary_term'] = ParagraphStyle('GTerm', fontName='Helvetica-Bold', fontSize=11,
        leading=15, textColor=PETROL, spaceBefore=8, spaceAfter=2)
    s['glossary_def'] = ParagraphStyle('GDef', fontName='Helvetica', fontSize=10,
        leading=14, textColor=DARK_NAVY, leftIndent=12, spaceAfter=6)
    s['footer'] = ParagraphStyle('Footer', fontName='Helvetica', fontSize=8,
        leading=10, textColor=colors.HexColor('#999999'), alignment=TA_CENTER)
    s['step_num'] = ParagraphStyle('StepNum', fontName='Helvetica-Bold', fontSize=13,
        leading=16, textColor=colors.white, alignment=TA_CENTER)
    s['analogy'] = ParagraphStyle('Analogy', fontName='Helvetica-Oblique', fontSize=10.5,
        leading=15, textColor=colors.HexColor('#555555'), leftIndent=14, rightIndent=14,
        spaceBefore=4, spaceAfter=4)
    return s


# ═══════════════════════════════════════════════════════════════
# CUSTOM FLOWABLES
# ═══════════════════════════════════════════════════════════════
class ColoredBox(Flowable):
    """A rounded colored box with icon, title, and body text."""
    def __init__(self, title, body, bg, border, icon='💡', width=CONTENT_W):
        super().__init__()
        self.box_title = title
        self.box_body = body
        self.bg = bg
        self.border = border
        self.icon = icon
        self.box_width = width
        self._lines = self._wrap_text(body, int(width / 5.2))
        self.height = max(50, 36 + len(self._lines) * 14)
        self.width = width

    def _wrap_text(self, text, w):
        return textwrap.wrap(text, width=w)

    def draw(self):
        c = self.canv
        # Background
        c.setFillColor(self.bg)
        c.setStrokeColor(self.border)
        c.setLineWidth(1.5)
        c.roundRect(0, 0, self.box_width, self.height, 8, fill=1, stroke=1)
        # Left accent bar
        c.setFillColor(self.border)
        c.roundRect(0, 0, 5, self.height, 2, fill=1, stroke=0)
        # Icon + Title
        c.setFillColor(colors.HexColor('#333333'))
        c.setFont('Helvetica-Bold', 11)
        c.drawString(16, self.height - 20, f'{self.icon}  {self.box_title}')
        # Body
        c.setFont('Helvetica', 9.5)
        c.setFillColor(colors.HexColor('#444444'))
        y = self.height - 36
        for line in self._lines:
            c.drawString(20, y, line)
            y -= 14


class CodeBlock(Flowable):
    """A styled code block with dark background."""
    def __init__(self, code, language='', width=CONTENT_W):
        super().__init__()
        self.code = code
        self.language = language
        self.box_width = width
        self.lines = code.split('\n')
        self.height = max(36, 24 + len(self.lines) * 13)
        self.width = width

    def draw(self):
        c = self.canv
        # Background
        c.setFillColor(CODE_BG)
        c.roundRect(0, 0, self.box_width, self.height, 6, fill=1, stroke=0)
        # Language tag
        if self.language:
            c.setFillColor(PETROL)
            c.roundRect(self.box_width - 70, self.height - 18, 60, 14, 3, fill=1, stroke=0)
            c.setFillColor(colors.white)
            c.setFont('Helvetica-Bold', 7)
            c.drawCentredString(self.box_width - 40, self.height - 15, self.language.upper())
        # Code text
        c.setFillColor(CODE_FG)
        c.setFont('Courier', 8.5)
        y = self.height - 20
        for line in self.lines:
            # Truncate very long lines
            display_line = line[:90] + ('...' if len(line) > 90 else '')
            c.drawString(12, y, display_line)
            y -= 13


class ChapterHeader(Flowable):
    """Full-width colored chapter header."""
    def __init__(self, number, title, width=CONTENT_W):
        super().__init__()
        self.number = number
        self.chapter_title = title
        self.box_width = width
        self.height = 60
        self.width = width

    def draw(self):
        c = self.canv
        # Background gradient effect (two rects)
        c.setFillColor(DARK_NAVY)
        c.roundRect(0, 0, self.box_width, self.height, 8, fill=1, stroke=0)
        c.setFillColor(PETROL)
        c.roundRect(0, 0, 8, self.height, 4, fill=1, stroke=0)
        # Number circle
        c.setFillColor(PETROL)
        c.circle(40, self.height / 2, 18, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont('Helvetica-Bold', 16)
        c.drawCentredString(40, self.height / 2 - 6, str(self.number))
        # Title
        c.setFillColor(colors.white)
        c.setFont('Helvetica-Bold', 20)
        c.drawString(68, self.height / 2 - 7, self.chapter_title)


class StepBox(Flowable):
    """A numbered step indicator."""
    def __init__(self, number, title, desc, width=CONTENT_W):
        super().__init__()
        self.number = number
        self.step_title = title
        self.desc = desc
        self.box_width = width
        self._lines = textwrap.wrap(desc, width=int(width / 5.5))
        self.height = max(44, 28 + len(self._lines) * 13)
        self.width = width

    def draw(self):
        c = self.canv
        # Light background
        c.setFillColor(LIGHT_BG)
        c.roundRect(0, 0, self.box_width, self.height, 6, fill=1, stroke=0)
        # Number circle
        c.setFillColor(PETROL)
        c.circle(22, self.height / 2, 14, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont('Helvetica-Bold', 12)
        c.drawCentredString(22, self.height / 2 - 4, str(self.number))
        # Title
        c.setFillColor(DARK_NAVY)
        c.setFont('Helvetica-Bold', 11)
        c.drawString(44, self.height - 16, self.step_title)
        # Description
        c.setFont('Helvetica', 9)
        c.setFillColor(colors.HexColor('#555555'))
        y = self.height - 32
        for line in self._lines:
            c.drawString(44, y, line)
            y -= 13


# ═══════════════════════════════════════════════════════════════
# CHART GENERATORS (matplotlib → Image flowable)
# ═══════════════════════════════════════════════════════════════
def _fig_to_image(fig, width_cm=17, dpi=150):
    """Convert matplotlib figure → reportlab Image flowable."""
    buf = BytesIO()
    fig.savefig(buf, format='png', dpi=dpi, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close(fig)
    buf.seek(0)
    w = width_cm * cm
    # Calculate height from aspect ratio
    fig_w, fig_h = fig.get_size_inches()
    h = w * (fig_h / fig_w)
    return Image(buf, width=w, height=h)


def chart_architecture():
    """High-level architecture diagram."""
    fig, ax = plt.subplots(figsize=(14, 5.5))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 5.5)
    ax.axis('off')
    ax.set_facecolor('white')

    boxes = [
        (0.5, 1.5, 3, 2.5, 'BROWSER\n(User Interface)', '#E3F2FD', '#1565C0'),
        (5,   1.5, 3, 2.5, 'FLASK SERVER\n(Python Backend)', '#E8F5E9', '#2E7D32'),
        (9.5, 1.5, 3, 2.5, 'db.json\n(JSON Database)', '#FFF3E0', '#E65100'),
    ]
    for x, y, w, h, label, bg, ec in boxes:
        rect = FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.15',
            facecolor=bg, edgecolor=ec, linewidth=2.5)
        ax.add_patch(rect)
        ax.text(x + w/2, y + h/2, label, ha='center', va='center',
                fontsize=12, fontweight='bold', color='#333', family='sans-serif')

    # Arrows
    arrow_style = 'Simple,tail_width=3,head_width=12,head_length=8'
    for x1, x2, y_off, label, clr in [
        (3.5, 5.0, 3.3, 'HTTP REST API', '#1565C0'),
        (5.0, 3.5, 2.2, 'JSON Response', '#1565C0'),
        (8.0, 9.5, 3.3, 'Read File', '#2E7D32'),
        (9.5, 8.0, 2.2, 'JSON Data', '#2E7D32'),
    ]:
        ax.annotate('', xy=(x2, y_off), xytext=(x1, y_off),
            arrowprops=dict(arrowstyle='->', color=clr, lw=2))
        ax.text((x1+x2)/2, y_off + 0.3, label, ha='center', fontsize=8.5,
                color=clr, fontweight='bold', family='sans-serif')

    # WebSocket label
    ax.annotate('', xy=(5.0, 1.7), xytext=(3.5, 1.7),
        arrowprops=dict(arrowstyle='<->', color='#009999', lw=2, linestyle='dashed'))
    ax.text(4.25, 1.2, 'WebSocket\n(Real-time)', ha='center', fontsize=8,
            color='#009999', fontweight='bold', style='italic')

    ax.set_title('System Architecture — How the Parts Connect',
                 fontsize=15, fontweight='bold', color='#000028', pad=15)
    fig.tight_layout()
    return _fig_to_image(fig, 16)


def chart_tech_stack():
    """Technology stack pie chart."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    # Pie: Lines of code by language
    labels = ['Python\n(Backend)', 'JavaScript\n(Frontend)', 'HTML\n(Structure)', 'CSS\n(Styling)', 'JSON\n(Database)']
    sizes = [468, 1234, 271, 1207, 430]
    clrs = ['#009999', '#FFB300', '#FF6B6B', '#7C4DFF', '#00BCD4']
    explode = (0, 0.06, 0, 0, 0)
    wedges, texts, autotexts = ax1.pie(sizes, labels=labels, autopct='%1.0f%%',
        colors=clrs, explode=explode, startangle=140, textprops={'fontsize': 9},
        pctdistance=0.8, labeldistance=1.15)
    for t in autotexts:
        t.set_fontweight('bold')
        t.set_color('white')
        t.set_fontsize(8)
    ax1.set_title('Lines of Code by Language', fontsize=13, fontweight='bold', color='#000028')

    # Bar: Files by type
    file_types = ['Python', 'JavaScript', 'HTML', 'CSS', 'JSON', 'Config']
    counts = [3, 1, 1, 1, 2, 5]
    bar_colors = ['#009999', '#FFB300', '#FF6B6B', '#7C4DFF', '#00BCD4', '#78909C']
    bars = ax2.barh(file_types, counts, color=bar_colors, height=0.55, edgecolor='white', linewidth=1.5)
    ax2.set_xlabel('Number of Files', fontsize=10)
    ax2.set_title('Project Files by Type', fontsize=13, fontweight='bold', color='#000028')
    ax2.set_xlim(0, max(counts) + 1)
    for bar, count in zip(bars, counts):
        ax2.text(bar.get_width() + 0.15, bar.get_y() + bar.get_height()/2,
                 str(count), va='center', fontsize=10, fontweight='bold', color='#333')
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)

    fig.tight_layout(pad=3)
    return _fig_to_image(fig, 17)


def chart_project_structure():
    """Project folder structure as a tree diagram."""
    fig, ax = plt.subplots(figsize=(10, 9))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 18)
    ax.axis('off')

    tree = [
        (0, '[DIR]  AI-CatalyESt/', '#000028', True, 17),
        (1, '[PY]   app.py  --  Python Flask backend (468 lines)', '#009999', False, 16),
        (1, '[JS]   server.js  --  Node.js backend mirror (420 lines)', '#009999', False, 15),
        (1, '[CFG]  requirements.txt  --  Python dependencies', '#78909C', False, 14),
        (1, '[CFG]  package.json  --  Node.js dependencies', '#78909C', False, 13),
        (1, '[CFG]  Procfile  --  Deployment startup command', '#78909C', False, 12),
        (1, '[CFG]  render.yaml  --  Cloud config', '#78909C', False, 11),
        (1, '[DIR]  public/  --  Frontend files', '#1565C0', True, 10),
        (2, '[HTML] index.html  --  Main page (271 lines)', '#FF6B6B', False, 9),
        (2, '[DIR]  js/', '#FFB300', True, 8),
        (3, '[JS]   app.js  --  All frontend logic (1,234 lines)', '#FFB300', False, 7),
        (2, '[DIR]  css/', '#7C4DFF', True, 6),
        (3, '[CSS]  styles.css  --  All styling (1,207 lines)', '#7C4DFF', False, 5),
        (1, '[DIR]  data/  --  Database', '#00BCD4', True, 4),
        (2, '[JSON] db.json  --  JSON database (430 lines)', '#00BCD4', False, 3),
        (1, '[DIR]  uploads/avatars/  --  User photos', '#78909C', True, 2),
    ]
    for indent, label, color, is_bold, y in tree:
        x = 0.3 + indent * 0.8
        weight = 'bold' if is_bold else 'normal'
        size = 11 if indent == 0 else (10 if is_bold else 9.5)
        # Draw connector line
        if indent > 0:
            ax.plot([x - 0.3, x - 0.05], [y + 0.15, y + 0.15], color='#CCCCCC', lw=1)
        ax.text(x, y, label, fontsize=size, fontweight=weight, color=color,
                va='center', family='sans-serif')

    ax.set_title('Project Folder Structure', fontsize=14, fontweight='bold',
                 color='#000028', pad=12)
    fig.tight_layout()
    return _fig_to_image(fig, 14)


def chart_request_flow():
    """HTTP request-response flow diagram."""
    fig, ax = plt.subplots(figsize=(14, 6))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 6)
    ax.axis('off')

    steps = [
        (0.3,  3, '1\nUser clicks\na button', '#E3F2FD', '#1565C0'),
        (3.0,  3, '2\napp.js calls\nfetch(/api/...)', '#FFF3E0', '#E65100'),
        (5.7,  3, '3\nFlask receives\nthe request', '#E8F5E9', '#2E7D32'),
        (8.4,  3, '4\nReads/writes\ndb.json', '#F3E5F5', '#7B1FA2'),
        (11.1, 3, '5\nSends JSON\nback to browser', '#FCE4EC', '#C62828'),
    ]
    for x, y, label, bg, ec in steps:
        rect = FancyBboxPatch((x, y - 1.2), 2.2, 2.4, boxstyle='round,pad=0.12',
            facecolor=bg, edgecolor=ec, linewidth=2)
        ax.add_patch(rect)
        ax.text(x + 1.1, y, label, ha='center', va='center', fontsize=10,
                fontweight='bold', color=ec, family='sans-serif')

    for x1, x2 in [(2.5, 3.0), (5.2, 5.7), (7.9, 8.4), (10.6, 11.1)]:
        ax.annotate('', xy=(x2, 3), xytext=(x1, 3),
            arrowprops=dict(arrowstyle='->', color='#009999', lw=2.5))

    ax.text(7, 0.5, '6. app.js updates the page with the new data — no page reload needed!',
            ha='center', fontsize=11, fontweight='bold', color='#009999', style='italic')

    ax.set_title('How a Single Click Travels Through the System',
                 fontsize=14, fontweight='bold', color='#000028', pad=10)
    fig.tight_layout()
    return _fig_to_image(fig, 17)


def chart_websocket_flow():
    """WebSocket real-time quiz flow."""
    fig, ax = plt.subplots(figsize=(14, 7))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 8)
    ax.axis('off')

    # Timeline
    events_list = [
        (1, 7, 'Admin creates\nquiz', '#009999'),
        (3, 7, 'Players join\nwith code', '#1565C0'),
        (5, 7, 'Admin starts\nquiz', '#2E7D32'),
        (7, 7, 'Questions sent\nto all players', '#E65100'),
        (9, 7, 'Players answer\nin real-time', '#7B1FA2'),
        (11, 7, 'Scores calculated\n& leaderboard', '#C62828'),
        (13, 7, 'Quiz ends\npoints awarded', '#009999'),
    ]
    for x, y, label, clr in events_list:
        ax.plot(x, y, 'o', markersize=16, color=clr, zorder=5)
        ax.text(x, y - 0.9, label, ha='center', va='top', fontsize=8.5,
                fontweight='bold', color=clr, family='sans-serif')

    ax.plot([1, 13], [7, 7], '-', color='#CCCCCC', lw=3, zorder=1)

    # Anti-cheat note
    rect = FancyBboxPatch((2, 1.5), 10, 2.2, boxstyle='round,pad=0.15',
        facecolor='#FFF8E1', edgecolor='#FFB300', linewidth=2)
    ax.add_patch(rect)
    ax.text(7, 3, 'ANTI-CHEAT SYSTEM', ha='center', fontsize=12,
            fontweight='bold', color='#E65100')
    ax.text(7, 2.3, 'If a player switches browser tabs, the server detects it and deducts points.\n'
            'Final Score = Correct Answers − Tab Switches',
            ha='center', fontsize=9.5, color='#555', family='sans-serif')

    ax.set_title('Real-Time Quiz Lifecycle (WebSocket Events)',
                 fontsize=14, fontweight='bold', color='#000028', pad=10)
    fig.tight_layout()
    return _fig_to_image(fig, 17)


def chart_deployment_pipeline():
    """Deployment pipeline: Local → GitHub → Render → Live."""
    fig, ax = plt.subplots(figsize=(14, 4.5))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 4.5)
    ax.axis('off')

    stages = [
        (0.3,  1.5, 'YOUR COMPUTER\n(Write Code)', '#E3F2FD', '#1565C0'),
        (3.8,  1.5, 'GIT COMMIT\n(Save Version)', '#FFF3E0', '#E65100'),
        (7.3,  1.5, 'GITHUB\n(Cloud Storage)', '#F3E5F5', '#7B1FA2'),
        (10.8, 1.5, 'RENDER.COM\n(Live Server)', '#E8F5E9', '#2E7D32'),
    ]
    for x, y, label, bg, ec in stages:
        rect = FancyBboxPatch((x, y - 1), 2.8, 2.5, boxstyle='round,pad=0.15',
            facecolor=bg, edgecolor=ec, linewidth=2.5)
        ax.add_patch(rect)
        ax.text(x + 1.4, y + 0.25, label, ha='center', va='center', fontsize=10.5,
                fontweight='bold', color=ec, family='sans-serif')

    for x1, x2 in [(3.1, 3.8), (6.6, 7.3), (10.1, 10.8)]:
        ax.annotate('', xy=(x2, 2), xytext=(x1, 2),
            arrowprops=dict(arrowstyle='->', color='#009999', lw=2.5))

    texts = ['git add\ngit commit', 'git push', 'Auto-\nDeploy']
    positions = [(3.45, 3.0), (6.95, 3.0), (10.45, 3.0)]
    for (x, y), txt in zip(positions, texts):
        ax.text(x, y, txt, ha='center', fontsize=8, color='#009999',
                fontweight='bold', family='sans-serif')

    ax.set_title('From Your Computer to the Internet — Deployment Pipeline',
                 fontsize=14, fontweight='bold', color='#000028', pad=10)
    fig.tight_layout()
    return _fig_to_image(fig, 17)


def chart_feature_complexity():
    """Feature complexity / effort radar-ish bar chart."""
    fig, ax = plt.subplots(figsize=(12, 5))
    features = [
        'Dashboard\n& Stats', 'Leaderboard\nSystem', 'Calendar\nView',
        'Team\nManagement', 'Live Quiz\nEngine', 'Survey\nSystem',
        'Admin\nPanel', 'Auth &\nSecurity', 'Real-time\nWebSockets'
    ]
    complexity = [3, 4, 3, 3, 9, 5, 6, 4, 8]
    colors_list = ['#009999', '#00BCD4', '#FFB300', '#7C4DFF', '#FF6B6B',
                   '#4CAF50', '#E91E63', '#FF9800', '#2196F3']

    bars = ax.bar(range(len(features)), complexity, color=colors_list,
                  width=0.65, edgecolor='white', linewidth=2)
    ax.set_xticks(range(len(features)))
    ax.set_xticklabels(features, fontsize=9, fontweight='bold')
    ax.set_ylabel('Complexity (1-10)', fontsize=11)
    ax.set_ylim(0, 11)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(axis='y', alpha=0.3)
    for bar, val in zip(bars, complexity):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
                str(val), ha='center', fontsize=11, fontweight='bold', color='#333')
    ax.set_title('Feature Complexity Breakdown',
                 fontsize=14, fontweight='bold', color='#000028')
    fig.tight_layout()
    return _fig_to_image(fig, 17)


def chart_data_model():
    """Data model / relationships diagram."""
    fig, ax = plt.subplots(figsize=(14, 7))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 7.5)
    ax.axis('off')

    entities = [
        (0.5,  5, 3.5, 2, 'Members\n───────\nid, name, email\ndomain, avatar\njoinedDate', '#E3F2FD', '#1565C0'),
        (5.25, 5, 3.5, 2, 'Events\n───────\nid, month, title\nphase, date\nstatus', '#E8F5E9', '#2E7D32'),
        (10,   5, 3.5, 2, 'Points\n───────\nid, memberId\nmonth, points\ncategory', '#FFF3E0', '#E65100'),
        (0.5,  1, 3.5, 2, 'Quizzes\n───────\nid, title\nquestions[]\nparticipants', '#F3E5F5', '#7B1FA2'),
        (5.25, 1, 3.5, 2, 'Surveys\n───────\nid, question\noptions[]\nvotes[]', '#FCE4EC', '#C62828'),
        (10,   1, 3.5, 2, 'Teams\n───────\nid, name\nmembers[]\ncolor', '#E0F7FA', '#00838F'),
    ]
    for x, y, w, h, label, bg, ec in entities:
        rect = FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.1',
            facecolor=bg, edgecolor=ec, linewidth=2)
        ax.add_patch(rect)
        ax.text(x + w/2, y + h/2, label, ha='center', va='center', fontsize=9,
                fontweight='bold', color=ec, family='monospace')

    # Relationships
    ax.annotate('', xy=(5.25, 6), xytext=(4, 6),
        arrowprops=dict(arrowstyle='->', color='#999', lw=1.5, linestyle='dashed'))
    ax.annotate('', xy=(10, 6), xytext=(8.75, 6),
        arrowprops=dict(arrowstyle='->', color='#999', lw=1.5, linestyle='dashed'))
    ax.text(4.6, 6.3, 'presents at', fontsize=8, color='#999', style='italic')
    ax.text(9.3, 6.3, 'earns from', fontsize=8, color='#999', style='italic')

    ax.set_title('Database Collections & Relationships (db.json)',
                 fontsize=14, fontweight='bold', color='#000028', pad=10)
    fig.tight_layout()
    return _fig_to_image(fig, 17)


def chart_spa_navigation():
    """SPA tab navigation flow."""
    fig, ax = plt.subplots(figsize=(14, 4))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 4)
    ax.axis('off')

    tabs = ['Dashboard', 'Leaderboard', 'Calendar', 'Team', 'Quiz', 'Admin']
    clrs = ['#009999', '#00BCD4', '#FFB300', '#7C4DFF', '#FF6B6B', '#E91E63']
    for i, (tab, clr) in enumerate(zip(tabs, clrs)):
        x = 0.3 + i * 2.3
        rect = FancyBboxPatch((x, 2), 1.9, 1.2, boxstyle='round,pad=0.08',
            facecolor=clr, edgecolor='white', linewidth=2)
        ax.add_patch(rect)
        ax.text(x + 0.95, 2.6, tab, ha='center', va='center', fontsize=10,
                fontweight='bold', color='white', family='sans-serif')

    # Central box
    rect = FancyBboxPatch((3, 0.2), 8, 1.3, boxstyle='round,pad=0.1',
        facecolor='#F7F7F8', edgecolor='#CCCCCC', linewidth=1.5)
    ax.add_patch(rect)
    ax.text(7, 0.85, 'Content Area — Only this part changes, the page never reloads',
            ha='center', fontsize=10, color='#555', fontweight='bold')

    for i in range(6):
        x = 0.3 + i * 2.3 + 0.95
        ax.annotate('', xy=(min(max(x, 3.5), 10.5), 1.5), xytext=(x, 2),
            arrowprops=dict(arrowstyle='->', color='#AAAAAA', lw=1.5))

    ax.set_title('Single-Page App Navigation — No Page Reloads',
                 fontsize=13, fontweight='bold', color='#000028', pad=8)
    fig.tight_layout()
    return _fig_to_image(fig, 17)


def chart_phase_timeline():
    """12-month phase timeline."""
    fig, ax = plt.subplots(figsize=(14, 3.5))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 3.5)
    ax.axis('off')

    phases = [
        ('SPARK', 3, '#FF6B6B',  'Apr-Jun 2026',  'Months 1-3'),
        ('BUILD', 3, '#FFB300',  'Jul-Sep 2026',  'Months 4-6'),
        ('APPLY', 3, '#009999',  'Oct-Dec 2026',  'Months 7-9'),
        ('DELIVER', 3, '#7C4DFF', 'Jan-Mar 2027', 'Months 10-12'),
    ]
    x = 0.5
    for name, w, clr, period, months in phases:
        rect = FancyBboxPatch((x, 1), 3, 1.5, boxstyle='round,pad=0.08',
            facecolor=clr, edgecolor='white', linewidth=2, alpha=0.9)
        ax.add_patch(rect)
        ax.text(x + 1.5, 2, name, ha='center', va='center', fontsize=14,
                fontweight='bold', color='white')
        ax.text(x + 1.5, 1.3, f'{period}\n{months}', ha='center', va='center',
                fontsize=8, color='white', alpha=0.9)
        x += 3.3

    ax.set_title('12-Month AI CatalyESt Journey — Four Phases',
                 fontsize=13, fontweight='bold', color='#000028', pad=8)
    fig.tight_layout()
    return _fig_to_image(fig, 17)


# ═══════════════════════════════════════════════════════════════
# DOCUMENT BUILDERS
# ═══════════════════════════════════════════════════════════════

def build_cover(S):
    """Cover page."""
    story = []
    story.append(Spacer(1, 100))
    story.append(Paragraph('AI CatalyESt', S['title']))
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width='60%', thickness=3, color=PETROL,
                             spaceAfter=12, spaceBefore=0, dash=None))
    story.append(Paragraph('Complete Build Manual', ParagraphStyle('CoverSub',
        fontName='Helvetica', fontSize=22, leading=28, textColor=PETROL,
        alignment=TA_CENTER, spaceAfter=8)))
    story.append(Paragraph('From Zero to a Live Dashboard — Step by Step',
        ParagraphStyle('CoverTag', fontName='Helvetica-Oblique', fontSize=13,
        leading=18, textColor=colors.HexColor('#6E6E73'), alignment=TA_CENTER,
        spaceAfter=40)))

    # Info table
    info_data = [
        ['Organisation', 'Siemens Technology India — Engineering Systems'],
        ['Author', 'Vigneshvar SA'],
        ['Live URL', 'https://ai-catalyest.onrender.com'],
        ['Repository', 'github.com/vigneshvar11/ai-catalyst'],
        ['Generated', datetime.now().strftime('%B %d, %Y')],
    ]
    t = Table(info_data, colWidths=[120, 300])
    t.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), PETROL),
        ('TEXTCOLOR', (1, 0), (1, -1), DARK_NAVY),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('LINEBELOW', (0, 0), (-1, -2), 0.5, colors.HexColor('#E5E5EA')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(t)
    story.append(Spacer(1, 60))
    story.append(Paragraph(
        'This manual is designed so that anyone — even with zero coding experience — '
        'can understand how this dashboard was built and recreate it from scratch.',
        ParagraphStyle('CoverNote', fontName='Helvetica-Oblique', fontSize=10,
        leading=14, textColor=colors.HexColor('#999999'), alignment=TA_CENTER)))
    story.append(PageBreak())
    return story


def build_toc(S):
    """Table of Contents."""
    story = []
    story.append(Paragraph('Table of Contents', S['h1']))
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width='100%', thickness=2, color=PETROL, spaceAfter=16))

    chapters = [
        ('1', 'Understanding the Project'),
        ('2', 'What You Need Before Starting'),
        ('3', 'Building the Database'),
        ('4', 'Building the Backend Server'),
        ('5', 'Building the Frontend Interface'),
        ('6', 'Adding Real-Time Features'),
        ('7', 'Styling & Visual Design'),
        ('8', 'Testing Everything Locally'),
        ('9', 'Version Control with GitHub'),
        ('10', 'Deploying to the Cloud'),
        ('11', 'Project Analytics & Insights'),
        ('', 'Troubleshooting Guide'),
        ('', 'Glossary of Terms'),
    ]
    for num, title in chapters:
        prefix = f'Chapter {num}:  ' if num else ''
        style = S['toc_chapter'] if num else S['toc_item']
        dot_leader = '  ' + '·' * max(5, 55 - len(prefix + title))
        story.append(Paragraph(f'{prefix}{title}{dot_leader}', style))
    story.append(PageBreak())
    return story


def build_ch1(S):
    """Chapter 1: Understanding the Project."""
    story = []
    story.append(ChapterHeader(1, 'Understanding the Project'))
    story.append(Spacer(1, 16))

    story.append(Paragraph('<b>What is AI CatalyESt?</b>', S['h2']))
    story.append(Paragraph(
        'AI CatalyESt (where <b>ES</b> stands for <b>Engineering Systems</b>) is a 12-month '
        'initiative at Siemens that teaches team members about Artificial Intelligence through '
        'hands-on monthly activities. Think of it as a structured learning journey — from basic '
        'AI concepts to building real AI solutions.', S['body']))
    story.append(Paragraph(
        'To track this journey, we built a <b>live dashboard</b> — a website that shows the '
        'schedule, scores, leaderboards, and lets the admin run quizzes and surveys in real-time.', S['body']))

    story.append(ColoredBox('Real-World Analogy',
        'Think of the dashboard like a school\'s notice board — but digital and interactive. '
        'It shows who\'s winning, what\'s coming next, lets teachers (admins) create tests, '
        'and students can participate in live quizzes from their phones.',
        TIP_BG, TIP_BORDER, '🎯'))
    story.append(Spacer(1, 12))

    story.append(Paragraph('<b>What Does the Dashboard Do?</b>', S['h2']))
    features = [
        '<b>Dashboard</b> — Shows countdown to next event, activity stats, progress overview',
        '<b>Leaderboard</b> — Ranks all 16 members by total points earned across 12 months',
        '<b>Calendar</b> — Visual 12-month plan with all events, dates, and phases',
        '<b>Team View</b> — Shows all members with their domains and roles',
        '<b>Live Quiz Engine</b> — Real-time quizzes with anti-cheat detection',
        '<b>Survey System</b> — Anonymous rating polls after presentations',
        '<b>Admin Panel</b> — Full control to manage members, events, points, quizzes',
    ]
    for f in features:
        story.append(Paragraph(f'• {f}', S['bullet']))
    story.append(Spacer(1, 12))

    story.append(Paragraph('<b>How Is It Built? — The Big Picture</b>', S['h2']))
    story.append(Paragraph(
        'Every website has three parts, just like a restaurant:', S['body']))

    story.append(ColoredBox('The Restaurant Analogy',
        '1. THE MENU (Frontend) — What the customer sees: the beautiful webpage with buttons, '
        'colors, and animations. Made with HTML, CSS, and JavaScript.\n'
        '2. THE WAITER (Backend Server) — Takes orders from the customer and brings food from the '
        'kitchen. This is our Python Flask server — it receives requests and sends back data.\n'
        '3. THE KITCHEN (Database) — Where all the ingredients (data) are stored. '
        'Our kitchen is a simple JSON file called db.json.',
        INFO_BG, INFO_BORDER, '🍽️'))
    story.append(Spacer(1, 14))

    # Architecture diagram
    story.append(chart_architecture())
    story.append(Paragraph('Figure 1.1 — System architecture showing how the browser, server, and database communicate.', S['caption']))

    story.append(Spacer(1, 10))
    story.append(chart_phase_timeline())
    story.append(Paragraph('Figure 1.2 — The 12-month journey is divided into four progressive phases.', S['caption']))

    story.append(PageBreak())
    return story


def build_ch2(S):
    """Chapter 2: Prerequisites."""
    story = []
    story.append(ChapterHeader(2, 'What You Need Before Starting'))
    story.append(Spacer(1, 16))

    story.append(Paragraph(
        'Before writing any code, you need to install a few free tools on your computer. '
        'Think of these as the <b>equipment</b> you need before you can start cooking.', S['body']))

    prereqs = [
        ('Python 3.10+', 'The programming language our server is written in.',
         'Go to python.org/downloads and click the big yellow "Download" button. '
         'During installation, CHECK the box that says "Add Python to PATH". This is critical!'),
        ('Visual Studio Code', 'The text editor where you\'ll write code (like Microsoft Word, but for code).',
         'Go to code.visualstudio.com and download it. It\'s free. Install normally.'),
        ('Git', 'A version-control tool — think of it as an "undo history" for your entire project.',
         'Go to git-scm.com and download. Install with default settings — just keep clicking "Next".'),
        ('Node.js (Optional)', 'Only needed if you want to run the JavaScript backend instead of Python.',
         'Go to nodejs.org and download the LTS version. Install normally.'),
        ('A Modern Browser', 'Chrome, Edge, or Firefox to view your dashboard.',
         'You almost certainly already have one. Any modern browser works.'),
    ]
    for i, (name, what, how) in enumerate(prereqs, 1):
        story.append(StepBox(i, name, f'{what} HOW: {how}'))
        story.append(Spacer(1, 6))

    story.append(Spacer(1, 10))
    story.append(ColoredBox('Checkpoint ✓',
        'After installing everything, open a terminal (search "Terminal" or "Command Prompt" '
        'in your Start menu) and type these commands. If each shows a version number, you\'re ready!',
        TIP_BG, TIP_BORDER, '✅'))
    story.append(Spacer(1, 8))
    story.append(CodeBlock('python --version     →  Python 3.12.3\n'
                           'git --version        →  git version 2.45.0\n'
                           'code --version       →  1.90.0', 'terminal'))
    story.append(Spacer(1, 10))

    story.append(Paragraph('<b>Creating Your Project Folder</b>', S['h2']))
    story.append(Paragraph(
        'Create a new folder on your computer. This is where ALL your project files will live. '
        'You can name it anything, but we\'ll call it <b>AI-CatalyESt</b>.', S['body']))
    story.append(CodeBlock('mkdir AI-CatalyESt\ncd AI-CatalyESt', 'terminal'))
    story.append(Spacer(1, 8))

    story.append(Paragraph('<b>Setting Up a Virtual Environment</b>', S['h2']))
    story.append(ColoredBox('What is a Virtual Environment?',
        'Imagine you have a toolbox. A virtual environment is like having a SEPARATE toolbox '
        'for each project, so tools from one project don\'t interfere with another. '
        'It keeps your project\'s Python packages isolated and clean.',
        INFO_BG, INFO_BORDER, '📦'))
    story.append(Spacer(1, 8))
    story.append(CodeBlock('python -m venv .venv\n\n# Activate it:\n'
                           '# On Windows:\n.venv\\Scripts\\activate\n\n'
                           '# On Mac/Linux:\nsource .venv/bin/activate', 'terminal'))
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        'You\'ll know it\'s active when you see <b>(.venv)</b> at the beginning of your '
        'terminal prompt. Always activate this before working on the project!', S['body']))

    story.append(PageBreak())
    return story


def build_ch3(S):
    """Chapter 3: Building the Database."""
    story = []
    story.append(ChapterHeader(3, 'Building the Database'))
    story.append(Spacer(1, 16))

    story.append(Paragraph(
        'Most websites use complex database systems like PostgreSQL or MongoDB. '
        'We chose something much simpler: a <b>single JSON file</b>. This makes it easy '
        'to understand, edit, and debug — perfect for a team dashboard.', S['body']))

    story.append(ColoredBox('What is JSON?',
        'JSON (JavaScript Object Notation) is a way to store data as text. It looks like a '
        'list of labeled boxes. For example: {"name": "Vigneshvar", "role": "Lead"}. '
        'It\'s human-readable — you can open it in any text editor and understand it!',
        INFO_BG, INFO_BORDER, '📋'))
    story.append(Spacer(1, 12))

    story.append(Paragraph('<b>Database Structure</b>', S['h2']))
    story.append(Paragraph(
        'Our database file <b>data/db.json</b> has 6 main collections (think of them as '
        'different drawers in a filing cabinet):', S['body']))

    story.append(chart_data_model())
    story.append(Paragraph('Figure 3.1 — The six data collections and how they relate to each other.', S['caption']))

    story.append(Paragraph('<b>Step 1: Create the data folder and file</b>', S['h3']))
    story.append(CodeBlock('mkdir data\n# Create a new file: data/db.json', 'terminal'))
    story.append(Spacer(1, 8))

    story.append(Paragraph('<b>Step 2: Add the initial structure</b>', S['h3']))
    story.append(Paragraph('Copy this into your db.json file. This is the skeleton of your database:', S['body']))
    story.append(CodeBlock(
        '{\n'
        '  "config": {\n'
        '    "admin": { "username": "admin", "password": "admin" },\n'
        '    "appName": "AI CatalyESt",\n'
        '    "teamName": "Engineering Systems",\n'
        '    "company": "Siemens"\n'
        '  },\n'
        '  "members": [],\n'
        '  "events": [],\n'
        '  "points": [],\n'
        '  "quizzes": [],\n'
        '  "surveys": [],\n'
        '  "teams": []\n'
        '}', 'json'))
    story.append(Spacer(1, 8))

    story.append(Paragraph('<b>Step 3: Add members</b>', S['h3']))
    story.append(Paragraph(
        'Each member is a JSON object with these fields. The <b>id</b> is generated from the '
        'name by making it lowercase and replacing spaces with hyphens:', S['body']))
    story.append(CodeBlock(
        '{\n'
        '  "id": "vigneshvar-sa",\n'
        '  "name": "Vigneshvar SA",\n'
        '  "email": "vigneshvar.sa@siemens.com",\n'
        '  "role": "Initiative Lead",\n'
        '  "domain": "PLM",\n'
        '  "avatar": null,\n'
        '  "joinedDate": "2026-04-01"\n'
        '}', 'json'))
    story.append(Spacer(1, 8))

    story.append(ColoredBox('Key Concept: IDs',
        'Every item in the database needs a unique identifier (ID). For members, we create IDs '
        'from their names (e.g., "Vigneshvar SA" → "vigneshvar-sa"). For other items like events '
        'or quizzes, we use a prefix + random characters (e.g., "event-a1b2c3d4").',
        TIP_BG, TIP_BORDER, '🔑'))

    story.append(PageBreak())
    return story


def build_ch4(S):
    """Chapter 4: Building the Backend."""
    story = []
    story.append(ChapterHeader(4, 'Building the Backend Server'))
    story.append(Spacer(1, 16))

    story.append(ColoredBox('The Waiter Analogy — Continued',
        'Remember the restaurant? The backend server is the waiter. When you click a button '
        'on the website (place an order), the server receives it, goes to the database (kitchen), '
        'gets the data (food), and brings it back to your browser (table). '
        'Our waiter speaks Python and uses a framework called Flask.',
        INFO_BG, INFO_BORDER, '🍽️'))
    story.append(Spacer(1, 12))

    story.append(Paragraph('<b>Step 1: Install Flask</b>', S['h3']))
    story.append(Paragraph(
        'Flask is a Python library that turns your Python script into a web server. '
        'Install it along with the other packages we need:', S['body']))
    story.append(CodeBlock(
        'pip install flask flask-socketio gunicorn gevent gevent-websocket', 'terminal'))
    story.append(Spacer(1, 8))

    story.append(Paragraph(
        'Save these to a <b>requirements.txt</b> file so anyone can install them later:', S['body']))
    story.append(CodeBlock(
        'flask>=3.0.0\nflask-socketio>=5.3.0\ngunicorn>=21.2.0\n'
        'gevent>=24.2.1\ngevent-websocket>=0.10.1', 'txt'))
    story.append(Spacer(1, 10))

    story.append(Paragraph('<b>Step 2: Create app.py — The Heart of the Server</b>', S['h3']))

    story.append(Paragraph(
        'Create a file called <b>app.py</b> in your project root. This is the main server file. '
        'Let\'s build it piece by piece:', S['body']))
    story.append(Spacer(1, 6))

    story.append(Paragraph('<b>Part A: Imports and Setup</b>', S['h3']))
    story.append(CodeBlock(
        'import os, json, uuid\n'
        'from flask import Flask, request, jsonify, send_from_directory\n'
        'from flask_socketio import SocketIO, emit, join_room\n\n'
        'app = Flask(__name__, static_folder="public", static_url_path="")\n'
        'app.config["SECRET_KEY"] = "ai-catalyst-secret"\n'
        'socketio = SocketIO(app, cors_allowed_origins="*")\n\n'
        'DB_PATH = os.path.join(os.path.dirname(__file__), "data", "db.json")', 'python'))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        'This sets up Flask to serve your website files from the <b>public/</b> folder '
        'and enables WebSocket support for real-time features.', S['body']))

    story.append(Paragraph('<b>Part B: Database Helpers</b>', S['h3']))
    story.append(CodeBlock(
        'def read_db():\n'
        '    with open(DB_PATH, "r") as f:\n'
        '        return json.load(f)\n\n'
        'def write_db(data):\n'
        '    with open(DB_PATH, "w") as f:\n'
        '        json.dump(data, f, indent=2)', 'python'))
    story.append(Spacer(1, 6))
    story.append(ColoredBox('Why Two Functions?',
        'read_db() opens the JSON file and converts it into a Python dictionary (like a labeled box). '
        'write_db() takes a dictionary and saves it back to the file. Every API route uses these two '
        'functions to interact with the database. Simple!',
        TIP_BG, TIP_BORDER, '💡'))
    story.append(Spacer(1, 10))

    story.append(Paragraph('<b>Part C: API Routes (CRUD)</b>', S['h3']))
    story.append(Paragraph(
        'API routes are URLs that the frontend calls to get or change data. We follow a pattern '
        'called <b>CRUD</b> — the four basic operations on any data:', S['body']))

    crud_data = [
        ['Operation', 'HTTP Method', 'URL Pattern', 'What It Does'],
        ['Create', 'POST', '/api/members', 'Add a new member'],
        ['Read', 'GET', '/api/members', 'List all members'],
        ['Update', 'PUT', '/api/members/:id', 'Change a member\'s info'],
        ['Delete', 'DELETE', '/api/members/:id', 'Remove a member'],
    ]
    t = Table(crud_data, colWidths=[70, 80, 130, 170])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PETROL),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E5EA')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_BG]),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ]))
    story.append(t)
    story.append(Spacer(1, 8))

    story.append(Paragraph(
        'This same CRUD pattern repeats for <b>every resource</b>: events, points, quizzes, '
        'surveys, and teams. Once you understand it for members, you understand it for all!', S['body']))
    story.append(Spacer(1, 6))

    story.append(CodeBlock(
        '@app.route("/api/members", methods=["GET"])\n'
        'def get_members():\n'
        '    db = read_db()\n'
        '    return jsonify(db["members"])\n\n'
        '@app.route("/api/members", methods=["POST"])\n'
        'def create_member():\n'
        '    db = read_db()\n'
        '    data = request.json\n'
        '    name = data.get("name", "")\n'
        '    member_id = name.lower().replace(" ", "-")\n'
        '    new_member = {"id": member_id, **data}\n'
        '    db["members"].append(new_member)\n'
        '    write_db(db)\n'
        '    return jsonify(new_member), 201', 'python'))
    story.append(Spacer(1, 8))

    story.append(chart_request_flow())
    story.append(Paragraph('Figure 4.1 — The journey of a single click through the system.', S['caption']))

    story.append(Paragraph('<b>Part D: Starting the Server</b>', S['h3']))
    story.append(CodeBlock(
        'if __name__ == "__main__":\n'
        '    port = int(os.environ.get("PORT", 3000))\n'
        '    socketio.run(app, host="0.0.0.0", port=port, debug=True)', 'python'))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        'When you run <b>python app.py</b>, this starts the server on port 3000. '
        'Open your browser and go to <b>http://localhost:3000</b> to see your site!', S['body']))

    story.append(PageBreak())
    return story


def build_ch5(S):
    """Chapter 5: Building the Frontend."""
    story = []
    story.append(ChapterHeader(5, 'Building the Frontend Interface'))
    story.append(Spacer(1, 16))

    story.append(ColoredBox('The Building Analogy',
        'Think of the frontend like building a house:\n'
        '• HTML = The structure (walls, rooms, doors) — defines WHAT is on the page\n'
        '• CSS = The paint and decoration — defines how it LOOKS\n'
        '• JavaScript = The electricity and plumbing — defines how it WORKS',
        INFO_BG, INFO_BORDER, '🏠'))
    story.append(Spacer(1, 12))

    story.append(Paragraph('<b>Step 1: Create the folder structure</b>', S['h3']))
    story.append(CodeBlock(
        'mkdir public\nmkdir public/js\nmkdir public/css\n'
        'mkdir uploads\nmkdir uploads/avatars', 'terminal'))
    story.append(Spacer(1, 8))

    story.append(chart_project_structure())
    story.append(Paragraph('Figure 5.1 — Complete project folder structure with file purposes and line counts.', S['caption']))

    story.append(Paragraph('<b>Step 2: Create index.html — The One and Only Page</b>', S['h3']))
    story.append(Paragraph(
        'Our entire dashboard uses a technique called <b>Single-Page Application (SPA)</b>. '
        'Instead of having separate pages for dashboard, leaderboard, calendar, etc., we have '
        'ONE HTML file with ALL sections. JavaScript shows/hides them like tabs.', S['body']))
    story.append(Spacer(1, 6))

    story.append(chart_spa_navigation())
    story.append(Paragraph('Figure 5.2 — SPA navigation: clicking tabs shows different content without reloading the page.', S['caption']))

    story.append(CodeBlock(
        '<!DOCTYPE html>\n'
        '<html lang="en">\n'
        '<head>\n'
        '  <meta charset="UTF-8">\n'
        '  <meta name="viewport"\n'
        '        content="width=device-width, initial-scale=1.0">\n'
        '  <title>AI CatalyESt Dashboard</title>\n'
        '  <link rel="stylesheet" href="/css/styles.css">\n'
        '</head>\n'
        '<body>\n'
        '  <!-- Navigation Bar -->\n'
        '  <nav id="main-nav">...</nav>\n\n'
        '  <!-- Each tab is a <section> -->\n'
        '  <section id="tab-dashboard">...</section>\n'
        '  <section id="tab-leaderboard">...</section>\n'
        '  <section id="tab-calendar">...</section>\n'
        '  ...\n\n'
        '  <!-- Scripts loaded LAST (after page renders) -->\n'
        '  <script src="/js/app.js"></script>\n'
        '</body>\n'
        '</html>', 'html'))
    story.append(Spacer(1, 8))

    story.append(ColoredBox('Why Load Scripts at the Bottom?',
        'When the browser reads your HTML from top to bottom, if it hits a <script> tag, it pauses '
        'to download and run that script. By putting scripts at the BOTTOM, the user sees the page '
        'structure immediately while scripts load in the background. This prevents the "blank screen" problem.',
        TIP_BG, TIP_BORDER, '⚡'))
    story.append(Spacer(1, 12))

    story.append(Paragraph('<b>Step 3: Create app.js — The Brain of the Frontend</b>', S['h3']))
    story.append(Paragraph(
        'This is the largest file in the project (1,234 lines). It controls everything the user '
        'interacts with. Here\'s the key pattern:', S['body']))

    story.append(CodeBlock(
        '// 1. GLOBAL STATE — stores all data in memory\n'
        'const state = {\n'
        '  members: [],\n'
        '  events: [],\n'
        '  points: [],\n'
        '  leaderboard: [],\n'
        '  currentTab: "dashboard",\n'
        '};\n\n'
        '// 2. API HELPER — talks to the server\n'
        'async function api(url, options = {}) {\n'
        '  const res = await fetch(url, { ...options });\n'
        '  return await res.json();\n'
        '}\n\n'
        '// 3. LOAD DATA — fetches everything when page opens\n'
        'async function loadAllData() {\n'
        '  state.members = await api("/api/members");\n'
        '  state.events = await api("/api/events");\n'
        '  // ... etc\n'
        '}\n\n'
        '// 4. RENDER FUNCTIONS — build HTML for each tab\n'
        'function renderDashboard() {\n'
        '  document.getElementById("tab-dashboard").innerHTML = `\n'
        '    <h1>Welcome to AI CatalyESt</h1>\n'
        '    <p>${state.members.length} members</p>\n'
        '  `;\n'
        '}', 'javascript'))
    story.append(Spacer(1, 8))

    story.append(Paragraph(
        'Every tab has its own <b>render function</b>: renderDashboard(), renderLeaderboard(), '
        'renderCalendar(), renderTeam(), etc. When you click a tab, JavaScript calls the '
        'corresponding render function, which generates HTML from the data in <b>state</b>.', S['body']))

    story.append(PageBreak())
    return story


def build_ch6(S):
    """Chapter 6: Real-Time Features."""
    story = []
    story.append(ChapterHeader(6, 'Adding Real-Time Features'))
    story.append(Spacer(1, 16))

    story.append(ColoredBox('Phone Call vs. Letters',
        'Normal web requests (HTTP) are like sending letters — you send one, wait for a reply, done. '
        'WebSockets are like a phone call — once connected, both sides can talk freely in real-time. '
        'This is how our quiz system works: the server can PUSH questions to all players simultaneously.',
        INFO_BG, INFO_BORDER, '📞'))
    story.append(Spacer(1, 12))

    story.append(Paragraph('<b>Socket.IO — WebSockets Made Easy</b>', S['h2']))
    story.append(Paragraph(
        'We use a library called <b>Socket.IO</b> that handles WebSocket connections for us. '
        'It works on both the server (Python) and client (JavaScript) sides.', S['body']))

    story.append(Paragraph('<b>Server Side (Python):</b>', S['h3']))
    story.append(CodeBlock(
        '@socketio.on("quiz:join")\n'
        'def handle_join(data):\n'
        '    """When a player joins a quiz room"""\n'
        '    room = data["quizId"]\n'
        '    join_room(room)\n'
        '    emit("quiz:playerJoined",\n'
        '         {"player": data["name"]},\n'
        '         room=room)', 'python'))
    story.append(Spacer(1, 8))

    story.append(Paragraph('<b>Client Side (JavaScript):</b>', S['h3']))
    story.append(CodeBlock(
        '// Connect to the server\n'
        'const socket = io();\n\n'
        '// Listen for questions\n'
        'socket.on("quiz:question", (data) => {\n'
        '  showQuestion(data.question);\n'
        '});\n\n'
        '// Send an answer\n'
        'socket.emit("quiz:answer", {\n'
        '  quizId: "quiz-abc123",\n'
        '  answer: 2  // option index\n'
        '});', 'javascript'))
    story.append(Spacer(1, 12))

    story.append(chart_websocket_flow())
    story.append(Paragraph('Figure 6.1 — Complete quiz lifecycle from creation to scoring, including anti-cheat detection.', S['caption']))

    story.append(Spacer(1, 8))
    story.append(ColoredBox('Anti-Cheat System',
        'The quiz has a clever anti-cheat mechanism. If a player switches to another browser tab '
        '(presumably to Google the answer), the browser fires a "visibilitychange" event. '
        'Our JavaScript catches this and tells the server. The server tracks tab switches per player '
        'and deducts points: Final Score = Correct Answers − Tab Switches.',
        WARN_BG, WARN_BORDER, '🛡️'))

    story.append(PageBreak())
    return story


def build_ch7(S):
    """Chapter 7: Styling."""
    story = []
    story.append(ChapterHeader(7, 'Styling & Visual Design'))
    story.append(Spacer(1, 16))

    story.append(Paragraph(
        'The styling file (styles.css, 1,207 lines) gives the dashboard its Siemens-branded, '
        'Apple-like minimalist look. Let\'s understand the key design decisions.', S['body']))

    story.append(Paragraph('<b>CSS Custom Properties (Variables)</b>', S['h2']))
    story.append(Paragraph(
        'Instead of typing the same color code everywhere, we define variables once and use them '
        'throughout. If we want to change the brand color, we change it in ONE place.', S['body']))
    story.append(CodeBlock(
        ':root {\n'
        '  --primary:    #009999;   /* Siemens Petrol */\n'
        '  --dark:       #000028;   /* Deep Navy */\n'
        '  --green:      #00FFB9;   /* Bright Accent */\n'
        '  --bg:         #F7F7F8;   /* Light Background */\n'
        '  --font:       "Inter", sans-serif;\n'
        '  --radius:     16px;      /* Rounded corners */\n'
        '  --shadow:     0 2px 20px rgba(0,0,0,0.06);\n'
        '}', 'css'))
    story.append(Spacer(1, 8))

    # Color palette visual
    palette_data = [
        ['  ', '  ', '  ', '  ', '  '],
        ['#009999', '#000028', '#00FFB9', '#00BEDC', '#F7F7F8'],
        ['Petrol', 'Dark Navy', 'Green', 'Light Blue', 'Background'],
        ['Primary', 'Text', 'Accent', 'Secondary', 'Surface'],
    ]
    t = Table(palette_data, colWidths=[90] * 5, rowHeights=[30, 20, 20, 20])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 0), PETROL),
        ('BACKGROUND', (1, 0), (1, 0), DARK_NAVY),
        ('BACKGROUND', (2, 0), (2, 0), GREEN),
        ('BACKGROUND', (3, 0), (3, 0), LIGHT_PETROL),
        ('BACKGROUND', (4, 0), (4, 0), LIGHT_BG),
        ('FONTNAME', (0, 1), (-1, 1), 'Courier'),
        ('FONTSIZE', (0, 1), (-1, -1), 8.5),
        ('FONTNAME', (0, 2), (-1, -1), 'Helvetica'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E5EA')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(t)
    story.append(Paragraph('Figure 7.1 — The Siemens-inspired color palette used throughout the dashboard.', S['caption']))

    story.append(Paragraph('<b>Design Principles Applied</b>', S['h2']))
    principles = [
        '<b>Generous Whitespace</b> — Elements have ample padding (20-32px) and margins so nothing feels cramped.',
        '<b>Rounded Corners</b> — All cards use 16px border-radius for a soft, modern feel.',
        '<b>Subtle Shadows</b> — Light box-shadows give depth without heaviness.',
        '<b>Consistent Typography</b> — Inter font with a clear hierarchy: 28px for titles, 13px for body text.',
        '<b>Responsive Design</b> — CSS media queries adjust layout for phones, tablets, and desktops.',
        '<b>Smooth Animations</b> — Hover effects, tab transitions, and card entries all use CSS transitions.',
    ]
    for p in principles:
        story.append(Paragraph(f'• {p}', S['bullet']))

    story.append(PageBreak())
    return story


def build_ch8(S):
    """Chapter 8: Testing."""
    story = []
    story.append(ChapterHeader(8, 'Testing Everything Locally'))
    story.append(Spacer(1, 16))

    story.append(Paragraph('<b>Running the Server</b>', S['h2']))
    story.append(CodeBlock(
        '# Make sure your virtual environment is active!\n'
        '# You should see (.venv) in your prompt.\n\n'
        'python app.py\n\n'
        '# You should see:\n'
        '# * Running on http://0.0.0.0:3000\n'
        '# * Debugger is active!', 'terminal'))
    story.append(Spacer(1, 8))

    story.append(StepBox(1, 'Open your browser',
        'Navigate to http://localhost:3000 — you should see the dashboard with the AI CatalyESt header.'))
    story.append(Spacer(1, 6))
    story.append(StepBox(2, 'Test the Dashboard tab',
        'The countdown timer should show time remaining until the next event. The activity cards should display.'))
    story.append(Spacer(1, 6))
    story.append(StepBox(3, 'Test Admin Login',
        'Click the login icon in the navigation bar. Enter username: admin, password: admin. '
        'After login, you should see additional admin buttons appear.'))
    story.append(Spacer(1, 6))
    story.append(StepBox(4, 'Test Adding a Member',
        'Go to Admin > Members. Click "Add Member". Fill in the form and submit. '
        'Check the Team tab to verify the new member appears.'))
    story.append(Spacer(1, 6))
    story.append(StepBox(5, 'Test a Live Quiz',
        'Go to Admin > Quizzes. Create a quiz with 2-3 questions. Start it. '
        'Open a second browser window to join as a player.'))
    story.append(Spacer(1, 10))

    story.append(ColoredBox('Checkpoint ✓',
        'If all 5 tests above work correctly, your application is ready for deployment! '
        'If something doesn\'t work, check the terminal for error messages — Python will tell you '
        'exactly what line caused the problem.',
        TIP_BG, TIP_BORDER, '✅'))

    story.append(Spacer(1, 12))
    story.append(Paragraph('<b>Common Issues During Testing</b>', S['h2']))
    issues = [
        ['Issue', 'Cause', 'Fix'],
        ['Page is blank', 'Server not running', 'Run python app.py in terminal'],
        ['Port already in use', 'Another app on port 3000', 'Kill it or change PORT=3001'],
        ['"Module not found"', 'Missing dependency', 'Run pip install -r requirements.txt'],
        ['Data not loading', 'db.json has invalid JSON', 'Validate at jsonlint.com'],
        ['Admin buttons missing', 'Not logged in', 'Login with admin/admin'],
    ]
    t = Table(issues, colWidths=[120, 140, 200])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PETROL),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E5EA')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_BG]),
    ]))
    story.append(t)

    story.append(PageBreak())
    return story


def build_ch9(S):
    """Chapter 9: GitHub."""
    story = []
    story.append(ChapterHeader(9, 'Version Control with GitHub'))
    story.append(Spacer(1, 16))

    story.append(ColoredBox('The Video Game Analogy',
        'Git is like a save system in a video game. Every time you "commit", you create a save point. '
        'If you mess something up, you can go back to any previous save. '
        'GitHub is like cloud storage for your saves — it keeps them safe online and lets others access them.',
        INFO_BG, INFO_BORDER, '🎮'))
    story.append(Spacer(1, 12))

    story.append(Paragraph('<b>Step 1: Create a GitHub Account</b>', S['h3']))
    story.append(Paragraph(
        'Go to <b>github.com</b> and sign up for a free account. Choose a username '
        'you\'ll remember — it becomes part of your repository URL.', S['body']))

    story.append(Paragraph('<b>Step 2: Install GitHub CLI</b>', S['h3']))
    story.append(CodeBlock(
        '# Windows (using winget):\n'
        'winget install GitHub.cli\n\n'
        '# Then login:\n'
        'gh auth login\n'
        '# Follow the prompts — choose "GitHub.com" and "HTTPS"', 'terminal'))
    story.append(Spacer(1, 8))

    story.append(Paragraph('<b>Step 3: Initialize Git in Your Project</b>', S['h3']))
    story.append(CodeBlock(
        '# Inside your project folder:\n'
        'git init\n\n'
        '# Create a .gitignore file to exclude unnecessary files:\n'
        '# (files like .venv/, node_modules/, __pycache__/)', 'terminal'))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        'The <b>.gitignore</b> file tells Git which files NOT to track. '
        'You don\'t want to upload your virtual environment (it\'s huge) or temporary files.', S['body']))
    story.append(CodeBlock(
        '# .gitignore contents:\n'
        '.venv/\nnode_modules/\n__pycache__/\n*.pyc\nuploads/avatars/*\n'
        '!uploads/avatars/.gitkeep', 'text'))
    story.append(Spacer(1, 8))

    story.append(Paragraph('<b>Step 4: Create Repository and Push</b>', S['h3']))
    story.append(CodeBlock(
        '# Create a new repository on GitHub:\n'
        'gh repo create ai-catalyst --public --source=.\n\n'
        '# Add all files, create a save point, and upload:\n'
        'git add -A\n'
        'git commit -m "Initial commit: AI CatalyESt dashboard"\n'
        'git push origin master', 'terminal'))
    story.append(Spacer(1, 10))

    story.append(chart_deployment_pipeline())
    story.append(Paragraph('Figure 9.1 — The complete deployment pipeline from your computer to the live internet.', S['caption']))

    story.append(ColoredBox('Golden Rule of Git',
        'Commit early, commit often! Every time you complete a small piece of work (add a feature, '
        'fix a bug), create a commit. Your commit message should describe WHAT changed, like: '
        '"Add leaderboard sorting" or "Fix quiz timer countdown".',
        TIP_BG, TIP_BORDER, '✨'))

    story.append(PageBreak())
    return story


def build_ch10(S):
    """Chapter 10: Deployment."""
    story = []
    story.append(ChapterHeader(10, 'Deploying to the Cloud'))
    story.append(Spacer(1, 16))

    story.append(Paragraph(
        'Right now your dashboard only works on your computer (localhost). To make it accessible '
        'to anyone on the internet, we need to put it on a <b>cloud server</b>. We\'ll use '
        '<b>Render.com</b> — a free hosting platform.', S['body']))

    story.append(ColoredBox('What is "Deploying"?',
        'Deploying means copying your code to a computer on the internet (a server) that runs 24/7, '
        'so anyone with the URL can access your website. It\'s like moving your restaurant from your '
        'kitchen to a real storefront that customers can visit anytime.',
        INFO_BG, INFO_BORDER, '🌍'))
    story.append(Spacer(1, 12))

    story.append(Paragraph('<b>Step 1: Create Configuration Files</b>', S['h3']))
    story.append(Paragraph(
        'Render needs to know how to start your server. Create these files:', S['body']))

    story.append(Paragraph('<b>Procfile</b> — tells Render the startup command:', S['h3']))
    story.append(CodeBlock(
        'web: gunicorn -k geventwebsocket.gunicorn.workers'
        '.GeventWebSocketWorker -w 1 --bind 0.0.0.0:$PORT app:app', 'text'))
    story.append(Spacer(1, 6))

    story.append(Paragraph('<b>runtime.txt</b> — tells Render which Python version:', S['h3']))
    story.append(CodeBlock('python-3.12.3', 'text'))
    story.append(Spacer(1, 6))

    story.append(Paragraph('<b>render.yaml</b> — full service configuration:', S['h3']))
    story.append(CodeBlock(
        'services:\n'
        '  - type: web\n'
        '    name: ai-catalyest\n'
        '    runtime: python\n'
        '    buildCommand: pip install -r requirements.txt\n'
        '    startCommand: gunicorn -k geventwebsocket...\n'
        '    envVars:\n'
        '      - key: PYTHON_VERSION\n'
        '        value: 3.12.3', 'yaml'))
    story.append(Spacer(1, 10))

    story.append(Paragraph('<b>Step 2: Sign Up on Render.com</b>', S['h3']))
    steps = [
        ('Go to render.com', 'Click "Get Started for Free" and sign up with your GitHub account.'),
        ('Create New Web Service', 'Click "New +" → "Web Service". Connect your GitHub repository.'),
        ('Configure Settings', 'Name: ai-catalyest. Runtime: Python 3. Build: pip install -r requirements.txt.'),
        ('Deploy!', 'Click "Create Web Service". Render will build and deploy your app in about 3 minutes.'),
    ]
    for i, (title, desc) in enumerate(steps, 1):
        story.append(StepBox(i, title, desc))
        story.append(Spacer(1, 6))

    story.append(Spacer(1, 8))
    story.append(Paragraph('<b>Step 3: Auto-Deploy from GitHub</b>', S['h3']))
    story.append(Paragraph(
        'The best part: Render watches your GitHub repository. Every time you push code to GitHub, '
        'Render automatically deploys the update. Just push and wait 2-3 minutes!', S['body']))
    story.append(CodeBlock(
        '# Make a change, then:\n'
        'git add -A\n'
        'git commit -m "Update dashboard styling"\n'
        'git push origin master\n\n'
        '# Render auto-deploys in ~2-3 minutes!', 'terminal'))
    story.append(Spacer(1, 10))

    story.append(ColoredBox('Free Tier Limitation',
        'Render\'s free plan puts your server to "sleep" after 15 minutes of no visitors. '
        'The first visit after sleep takes ~30 seconds to "wake up". This is normal! '
        'Our code handles this with a loading overlay and auto-retry logic.',
        WARN_BG, WARN_BORDER, '⚠️'))

    story.append(PageBreak())
    return story


def build_ch11(S):
    """Chapter 11: Analytics & Insights."""
    story = []
    story.append(ChapterHeader(11, 'Project Analytics & Insights'))
    story.append(Spacer(1, 16))

    story.append(Paragraph(
        'Let\'s step back and look at the complete project from a data perspective. '
        'These charts reveal the scope, complexity, and composition of what we built.', S['body']))
    story.append(Spacer(1, 8))

    # Key metrics boxes
    metrics = [
        ['Total Lines of Code', 'Project Files', 'API Endpoints', 'Team Members'],
        ['3,610', '13+', '18', '16'],
        ['Across 5 languages', 'Python, JS, HTML, CSS, JSON', '6 resources × 3 CRUD ops', 'In 5 domains'],
    ]
    t = Table(metrics, colWidths=[115] * 4, rowHeights=[24, 36, 24])
    t.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('TEXTCOLOR', (0, 0), (-1, 0), PETROL),
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 1), (-1, 1), 22),
        ('TEXTCOLOR', (0, 1), (-1, 1), DARK_NAVY),
        ('FONTNAME', (0, 2), (-1, 2), 'Helvetica'),
        ('FONTSIZE', (0, 2), (-1, 2), 8),
        ('TEXTCOLOR', (0, 2), (-1, 2), colors.HexColor('#999')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOX', (0, 0), (0, -1), 1, colors.HexColor('#E5E5EA')),
        ('BOX', (1, 0), (1, -1), 1, colors.HexColor('#E5E5EA')),
        ('BOX', (2, 0), (2, -1), 1, colors.HexColor('#E5E5EA')),
        ('BOX', (3, 0), (3, -1), 1, colors.HexColor('#E5E5EA')),
        ('BACKGROUND', (0, 0), (-1, -1), LIGHT_BG),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(t)
    story.append(Spacer(1, 16))

    story.append(chart_tech_stack())
    story.append(Paragraph('Figure 11.1 — Code distribution by language and file count breakdown.', S['caption']))

    story.append(chart_feature_complexity())
    story.append(Paragraph('Figure 11.2 — Relative complexity of each feature. The live quiz engine and WebSocket system are the most complex.', S['caption']))

    # Technology choices table
    story.append(Paragraph('<b>Technology Choices & Why</b>', S['h2']))
    tech_data = [
        ['Technology', 'Role', 'Why We Chose It'],
        ['Python + Flask', 'Backend server', 'Easy to learn, minimal boilerplate, great for APIs'],
        ['Socket.IO', 'Real-time comms', 'Handles WebSockets with automatic reconnection'],
        ['Vanilla JS', 'Frontend logic', 'No framework complexity — simple and fast'],
        ['JSON file', 'Database', 'No setup needed — just a text file anyone can read'],
        ['CSS Variables', 'Theming', 'One-place brand color changes, maintainable design'],
        ['Render.com', 'Hosting', 'Free tier, auto-deploy from GitHub, supports Python'],
        ['GitHub', 'Version control', 'Free, industry standard, enables auto-deploy'],
    ]
    t = Table(tech_data, colWidths=[100, 115, 250])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PETROL),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E5EA')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_BG]),
        ('TEXTCOLOR', (0, 1), (0, -1), PETROL),
    ]))
    story.append(t)

    story.append(PageBreak())
    return story


def build_troubleshooting(S):
    """Troubleshooting guide."""
    story = []
    story.append(ChapterHeader('?', 'Troubleshooting Guide'))
    story.append(Spacer(1, 16))

    issues = [
        ('The page shows "Not Found" on a white screen',
         'The server is not running, or it\'s a cold start on Render\'s free tier.',
         'Wait 30 seconds and refresh. The loading overlay should appear and auto-retry. '
         'If running locally, make sure python app.py is running in your terminal.'),
        ('The page loads with huge/disproportionate text',
         'External fonts (Google Fonts) or CSS haven\'t loaded yet.',
         'This is handled by the loading overlay we added. It shows a spinner until everything loads. '
         'The inline critical CSS ensures the overlay itself always renders correctly.'),
        ('Data is not loading (empty dashboard)',
         'API calls are failing — either the server isn\'t ready or db.json is corrupted.',
         'Check the browser console (F12 → Console tab) for error messages. '
         'Validate your db.json at jsonlint.com. Our api() function retries 3 times automatically.'),
        ('"ModuleNotFoundError: No module named flask"',
         'Python packages are not installed or virtual environment is not active.',
         'Run: pip install -r requirements.txt. Make sure (.venv) appears in your terminal prompt.'),
        ('Changes not appearing on the live site',
         'You forgot to push to GitHub, or Render hasn\'t finished deploying.',
         'Run: git add -A && git commit -m "update" && git push. Then wait 2-3 minutes for Render.'),
        ('Quiz participants can\'t join',
         'WebSocket connection failed — possibly a firewall or CORS issue.',
         'Make sure you\'re using the correct URL. On Render, use https:// not http://.'),
        ('Admin buttons are not visible',
         'You\'re not logged in as admin.',
         'Click the lock icon → enter admin/admin → admin buttons will appear in the nav bar.'),
    ]
    for problem, cause, fix in issues:
        story.append(Paragraph(f'<b>Problem:</b> {problem}', S['h3']))
        story.append(ColoredBox('Cause', cause, WARN_BG, WARN_BORDER, '🔍'))
        story.append(Spacer(1, 4))
        story.append(ColoredBox('Solution', fix, TIP_BG, TIP_BORDER, '✅'))
        story.append(Spacer(1, 12))

    story.append(PageBreak())
    return story


def build_glossary(S):
    """Glossary of terms for non-coders."""
    story = []
    story.append(ChapterHeader('G', 'Glossary of Terms'))
    story.append(Spacer(1, 16))

    story.append(Paragraph(
        'These are the technical terms used in this manual, explained in plain English.', S['body']))
    story.append(Spacer(1, 8))

    terms = [
        ('API (Application Programming Interface)',
         'A set of rules that lets two programs talk to each other. Our frontend uses APIs to ask the '
         'backend for data, like asking a librarian for a specific book.'),
        ('Backend',
         'The "behind-the-scenes" part of a website — the server and database that users never see directly. '
         'Like the kitchen in a restaurant: essential but hidden.'),
        ('Browser',
         'The application you use to visit websites — Chrome, Firefox, Edge, Safari. It reads HTML/CSS/JS '
         'and turns them into the visual page you see.'),
        ('Commit',
         'A "save point" in Git. Each commit captures the state of all your files at that moment, '
         'with a message describing what changed.'),
        ('CRUD',
         'Create, Read, Update, Delete — the four basic operations you can do on any data. '
         'Every resource in our API supports these four operations.'),
        ('CSS (Cascading Style Sheets)',
         'The language that controls how a webpage LOOKS — colors, fonts, spacing, animations. '
         'It\'s the paint and wallpaper of your house.'),
        ('Database',
         'Where data is stored permanently. Ours is a simple JSON text file (db.json). '
         'Professional apps use databases like PostgreSQL or MongoDB.'),
        ('Deployment',
         'The process of putting your website on a server so anyone on the internet can access it.'),
        ('Flask',
         'A Python framework (pre-built code library) that makes it easy to create web servers. '
         'It handles HTTP requests, URL routing, and more.'),
        ('Frontend',
         'The part of a website that users see and interact with — the HTML page, styles, and JavaScript. '
         'Like a restaurant\'s dining area with menus and tables.'),
        ('Git',
         'A version control system that tracks changes to your files over time. Think of it as an '
         '"unlimited undo" button for your entire project.'),
        ('GitHub',
         'A website that hosts Git repositories online. Like Google Drive but specifically for code. '
         'Free to use, and millions of developers use it.'),
        ('HTML (HyperText Markup Language)',
         'The language that defines the STRUCTURE of a webpage — headings, paragraphs, buttons, images. '
         'It\'s the skeleton/frame of your house.'),
        ('HTTP (HyperText Transfer Protocol)',
         'The "language" browsers and servers use to communicate. When you type a URL, your browser '
         'sends an HTTP request. The server sends back an HTTP response.'),
        ('JavaScript',
         'The programming language of the web. It makes pages interactive — handles clicks, '
         'animates elements, and communicates with servers. The electricity of your house.'),
        ('JSON (JavaScript Object Notation)',
         'A text format for storing data as labeled pairs: {"name": "Vigneshvar", "age": 22}. '
         'Easy for both humans and computers to read.'),
        ('Render.com',
         'A cloud platform that hosts websites. It connects to your GitHub repository and '
         'automatically deploys your code to the internet.'),
        ('REST (Representational State Transfer)',
         'A design pattern for APIs where each URL represents a resource and HTTP methods '
         '(GET, POST, PUT, DELETE) represent actions on it.'),
        ('SPA (Single-Page Application)',
         'A web app that loads ONE HTML page and dynamically updates content using JavaScript, '
         'instead of loading new pages. Feel faster and smoother.'),
        ('Socket.IO / WebSocket',
         'Technology for real-time, two-way communication between browser and server. '
         'Like a phone call instead of exchanging letters.'),
        ('Terminal / Command Line',
         'A text-based interface where you type commands to control your computer. Every developer '
         'uses it to run programs, install packages, and manage files.'),
        ('Virtual Environment',
         'An isolated Python workspace. Like a separate toolbox for each project so their '
         'dependencies don\'t interfere with each other. Created with python -m venv .venv.'),
    ]
    for term, definition in terms:
        story.append(Paragraph(f'<b>{term}</b>', S['glossary_term']))
        story.append(Paragraph(definition, S['glossary_def']))

    story.append(PageBreak())
    return story


def build_final_page(S):
    """Final page with credits."""
    story = []
    story.append(Spacer(1, 100))
    story.append(HRFlowable(width='60%', thickness=2, color=PETROL, spaceAfter=20))
    story.append(Paragraph('You\'ve Reached the End!', S['h1']))
    story.append(Spacer(1, 12))
    story.append(Paragraph(
        'Congratulations on reading through the entire manual. You now have the knowledge '
        'to build and deploy a full-stack web dashboard from scratch — no AI assistance needed.',
        ParagraphStyle('Final', fontName='Helvetica', fontSize=12, leading=18,
        textColor=DARK_NAVY, alignment=TA_CENTER, spaceAfter=20)))
    story.append(Paragraph(
        '<b>Live Dashboard:</b> https://ai-catalyest.onrender.com',
        ParagraphStyle('FinalLink', fontName='Helvetica', fontSize=11, leading=16,
        textColor=PETROL, alignment=TA_CENTER, spaceAfter=6)))
    story.append(Paragraph(
        '<b>Source Code:</b> github.com/vigneshvar11/ai-catalyst',
        ParagraphStyle('FinalLink2', fontName='Helvetica', fontSize=11, leading=16,
        textColor=PETROL, alignment=TA_CENTER, spaceAfter=30)))
    story.append(HRFlowable(width='40%', thickness=1, color=colors.HexColor('#E5E5EA'), spaceAfter=20))
    story.append(Paragraph(
        'Built with ❤️ by Vigneshvar SA | Siemens Technology India | Engineering Systems',
        ParagraphStyle('Credits', fontName='Helvetica', fontSize=9, leading=13,
        textColor=colors.HexColor('#999'), alignment=TA_CENTER, spaceAfter=4)))
    story.append(Paragraph(
        f'Manual generated on {datetime.now().strftime("%B %d, %Y")}',
        ParagraphStyle('Date', fontName='Helvetica', fontSize=8, leading=11,
        textColor=colors.HexColor('#BBBBBB'), alignment=TA_CENTER)))
    return story


# ═══════════════════════════════════════════════════════════════
# PAGE TEMPLATES (Header/Footer)
# ═══════════════════════════════════════════════════════════════
def header_footer(canvas, doc):
    """Draw header line and footer with page number on each page."""
    canvas.saveState()
    # Header line
    canvas.setStrokeColor(PETROL)
    canvas.setLineWidth(1.5)
    canvas.line(MARGIN, PAGE_H - MARGIN + 10, PAGE_W - MARGIN, PAGE_H - MARGIN + 10)
    canvas.setFont('Helvetica', 7)
    canvas.setFillColor(colors.HexColor('#AAAAAA'))
    canvas.drawString(MARGIN, PAGE_H - MARGIN + 14, 'AI CatalyESt — Complete Build Manual')
    canvas.drawRightString(PAGE_W - MARGIN, PAGE_H - MARGIN + 14, 'Siemens Engineering Systems')

    # Footer
    canvas.setFont('Helvetica', 8)
    canvas.setFillColor(colors.HexColor('#BBBBBB'))
    canvas.drawCentredString(PAGE_W / 2, MARGIN - 15, f'— {doc.page} —')
    canvas.restoreState()


def cover_template(canvas, doc):
    """Minimal template for cover page (no header/footer)."""
    canvas.saveState()
    # Top accent bar
    canvas.setFillColor(PETROL)
    canvas.rect(0, PAGE_H - 8, PAGE_W, 8, fill=1, stroke=0)
    # Bottom accent
    canvas.setFillColor(DARK_NAVY)
    canvas.rect(0, 0, PAGE_W, 4, fill=1, stroke=0)
    canvas.restoreState()


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════
def generate_manual():
    """Generate the complete PDF manual."""
    print('🚀 Generating AI CatalyESt Build Manual...')
    print(f'   Output: {OUTPUT_PATH}')

    S = get_styles()

    # Build document
    doc = SimpleDocTemplate(
        OUTPUT_PATH,
        pagesize=A4,
        topMargin=MARGIN + 10,
        bottomMargin=MARGIN,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        title='AI CatalyESt — Complete Build Manual',
        author='Vigneshvar SA — Siemens Engineering Systems',
    )

    # Assemble story
    story = []
    print('   [1/13] Cover page...')
    story += build_cover(S)
    print('   [2/13] Table of Contents...')
    story += build_toc(S)
    print('   [3/13] Chapter 1: Understanding the Project...')
    story += build_ch1(S)
    print('   [4/13] Chapter 2: Prerequisites...')
    story += build_ch2(S)
    print('   [5/13] Chapter 3: Database...')
    story += build_ch3(S)
    print('   [6/13] Chapter 4: Backend Server...')
    story += build_ch4(S)
    print('   [7/13] Chapter 5: Frontend Interface...')
    story += build_ch5(S)
    print('   [8/13] Chapter 6: Real-Time Features...')
    story += build_ch6(S)
    print('   [9/13] Chapter 7: Styling...')
    story += build_ch7(S)
    print('   [10/13] Chapter 8: Testing...')
    story += build_ch8(S)
    print('   [11/13] Chapter 9: GitHub...')
    story += build_ch9(S)
    print('   [12/13] Chapter 10: Deployment...')
    story += build_ch10(S)
    print('   [13/13] Chapter 11: Analytics...')
    story += build_ch11(S)
    print('   [+] Troubleshooting Guide...')
    story += build_troubleshooting(S)
    print('   [+] Glossary...')
    story += build_glossary(S)
    print('   [+] Final page...')
    story += build_final_page(S)

    # Build PDF with page templates
    from reportlab.platypus import PageTemplate, Frame
    from reportlab.platypus.doctemplate import BaseDocTemplate

    print('   📄 Rendering PDF...')
    doc.build(story, onFirstPage=cover_template, onLaterPages=header_footer)

    size_mb = os.path.getsize(OUTPUT_PATH) / (1024 * 1024)
    print(f'\n✅ Manual generated successfully!')
    print(f'   📄 {OUTPUT_PATH}')
    print(f'   📦 Size: {size_mb:.1f} MB')


if __name__ == '__main__':
    generate_manual()
