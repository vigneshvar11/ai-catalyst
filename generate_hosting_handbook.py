#!/usr/bin/env python3
"""
EMBRACE AI — Hosting & Architecture Handbook Generator
=======================================================
Produces a beginner-friendly, in-depth PDF that teaches — from absolute
scratch — how web hosting works and how THIS project is architected and
deployed. Design language: Siemens petrol/navy + Apple glassmorphism.

Run:  python generate_hosting_handbook.py
Out:  EMBRACE_AI_Hosting_Handbook.pdf
"""

import os
import textwrap
from io import BytesIO
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image, KeepTogether, HRFlowable, Flowable,
)

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

# ═══════════════════════════════════════════════════════════════
# PALETTE (Siemens + glassmorphism accents)
# ═══════════════════════════════════════════════════════════════
PETROL       = colors.HexColor('#009999')
PETROL_LIGHT = colors.HexColor('#00BEDC')
DARK_NAVY    = colors.HexColor('#000028')
NAVY_2       = colors.HexColor('#0A1E3F')
GREEN        = colors.HexColor('#00D68F')
GREEN_SOFT   = colors.HexColor('#E8FDF5')
CORAL        = colors.HexColor('#FF6B6B')
AMBER        = colors.HexColor('#FFB300')
AMBER_SOFT   = colors.HexColor('#FFF8E1')
INFO         = colors.HexColor('#2196F3')
INFO_SOFT    = colors.HexColor('#E3F2FD')
VIOLET       = colors.HexColor('#7C4DFF')
LIGHT_BG     = colors.HexColor('#F7F7F8')
CARD_BG      = colors.HexColor('#FFFFFF')
CODE_BG      = colors.HexColor('#1E1E2E')
CODE_FG      = colors.HexColor('#CDD6F4')
GREY         = colors.HexColor('#6E6E73')
BORDER       = colors.HexColor('#E5E5EA')

PAGE_W, PAGE_H = A4
MARGIN = 1.8 * cm
CONTENT_W = PAGE_W - 2 * MARGIN

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_PATH = os.path.join(BASE_DIR, 'EMBRACE_AI_Hosting_Handbook.pdf')

# Track chapter titles for footer labelling
_CURRENT = {'chapter': 'EMBRACE AI — Hosting Handbook'}


# ═══════════════════════════════════════════════════════════════
# STYLES
# ═══════════════════════════════════════════════════════════════
def styles():
    s = {}
    s['title'] = ParagraphStyle('t', fontName='Helvetica-Bold', fontSize=40,
        leading=44, textColor=colors.white, alignment=TA_CENTER, spaceAfter=8)
    s['subtitle'] = ParagraphStyle('st', fontName='Helvetica', fontSize=15,
        leading=21, textColor=PETROL_LIGHT, alignment=TA_CENTER, spaceAfter=10)
    s['h1'] = ParagraphStyle('h1', fontName='Helvetica-Bold', fontSize=22,
        leading=27, textColor=DARK_NAVY, spaceBefore=8, spaceAfter=12)
    s['h2'] = ParagraphStyle('h2', fontName='Helvetica-Bold', fontSize=15,
        leading=20, textColor=PETROL, spaceBefore=14, spaceAfter=7)
    s['h3'] = ParagraphStyle('h3', fontName='Helvetica-Bold', fontSize=12,
        leading=16, textColor=NAVY_2, spaceBefore=9, spaceAfter=5)
    s['body'] = ParagraphStyle('b', fontName='Helvetica', fontSize=10.3,
        leading=15.5, textColor=colors.HexColor('#222235'), alignment=TA_JUSTIFY,
        spaceAfter=7)
    s['body_l'] = ParagraphStyle('bl', fontName='Helvetica', fontSize=10.3,
        leading=15.5, textColor=colors.HexColor('#222235'), alignment=TA_LEFT,
        spaceAfter=7)
    s['bullet'] = ParagraphStyle('bu', fontName='Helvetica', fontSize=10.3,
        leading=15, textColor=colors.HexColor('#222235'), leftIndent=20,
        bulletIndent=8, spaceAfter=4)
    s['caption'] = ParagraphStyle('cap', fontName='Helvetica-Oblique', fontSize=8.6,
        leading=11, textColor=GREY, alignment=TA_CENTER, spaceAfter=10, spaceBefore=3)
    s['toc_ch'] = ParagraphStyle('tc', fontName='Helvetica-Bold', fontSize=12.5,
        leading=22, textColor=PETROL)
    s['toc_it'] = ParagraphStyle('ti', fontName='Helvetica', fontSize=10.5,
        leading=17, textColor=DARK_NAVY, leftIndent=18)
    s['gterm'] = ParagraphStyle('gt', fontName='Helvetica-Bold', fontSize=11,
        leading=15, textColor=PETROL, spaceBefore=7, spaceAfter=1)
    s['gdef'] = ParagraphStyle('gd', fontName='Helvetica', fontSize=10,
        leading=14, textColor=colors.HexColor('#222235'), leftIndent=12, spaceAfter=5)
    s['cell'] = ParagraphStyle('cl', fontName='Helvetica', fontSize=9,
        leading=12.5, textColor=colors.HexColor('#222235'))
    s['cell_b'] = ParagraphStyle('clb', fontName='Helvetica-Bold', fontSize=9,
        leading=12.5, textColor=colors.white)
    s['cell_code'] = ParagraphStyle('clc', fontName='Courier', fontSize=8.6,
        leading=12, textColor=colors.HexColor('#C2185B'))
    return s

S = styles()


# ═══════════════════════════════════════════════════════════════
# CUSTOM FLOWABLES
# ═══════════════════════════════════════════════════════════════
class ChapterHeader(Flowable):
    """Full-width navy chapter banner with number chip + gradient bar."""
    def __init__(self, number, title, subtitle='', width=CONTENT_W):
        super().__init__()
        self.number, self.t, self.sub, self.w = number, title, subtitle, width
        self.height = 70
        self.width = width

    def draw(self):
        c = self.canv
        c.setFillColor(DARK_NAVY)
        c.roundRect(0, 0, self.w, self.height, 10, fill=1, stroke=0)
        # gradient accent (stacked bars)
        for i, col in enumerate([PETROL, PETROL_LIGHT, GREEN]):
            c.setFillColor(col)
            c.roundRect(0, self.height - (i+1)*self.height/3, 7, self.height/3, 0, fill=1, stroke=0)
        c.setFillColor(PETROL)
        c.circle(42, self.height/2, 20, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont('Helvetica-Bold', 19)
        c.drawCentredString(42, self.height/2 - 7, str(self.number))
        c.setFillColor(colors.white)
        c.setFont('Helvetica-Bold', 19)
        c.drawString(76, self.height/2 + (2 if self.sub else -7), self.t)
        if self.sub:
            c.setFillColor(PETROL_LIGHT)
            c.setFont('Helvetica', 10)
            c.drawString(76, self.height/2 - 14, self.sub)


class Analogy:
    pass  # (superseded by the table-based callout() helper below)


class CodeBlock(Flowable):
    """Dark code block with optional language chip."""
    def __init__(self, code, language='', width=CONTENT_W):
        super().__init__()
        self.code, self.language, self.w = code, language, width
        self.lines = code.split('\n')
        self.height = max(30, 18 + len(self.lines) * 12.5)
        self.width = width

    def draw(self):
        c = self.canv
        c.setFillColor(CODE_BG)
        c.roundRect(0, 0, self.w, self.height, 6, fill=1, stroke=0)
        if self.language:
            c.setFillColor(PETROL)
            c.roundRect(self.w - 74, self.height - 17, 64, 13, 3, fill=1, stroke=0)
            c.setFillColor(colors.white)
            c.setFont('Helvetica-Bold', 6.5)
            c.drawCentredString(self.w - 42, self.height - 14, self.language.upper())
        c.setFillColor(CODE_FG)
        c.setFont('Courier', 8.4)
        y = self.height - 18
        for ln in self.lines:
            disp = ln[:96] + ('…' if len(ln) > 96 else '')
            c.drawString(12, y, disp)
            y -= 12.5


class StepBox(Flowable):
    """Numbered step with title + description."""
    def __init__(self, number, title, desc, width=CONTENT_W):
        super().__init__()
        self.n, self.t, self.d, self.w = number, title, desc, width
        self._lines = textwrap.wrap(desc, width=int(width / 5.4))
        self.height = max(42, 26 + len(self._lines) * 12.8)
        self.width = width

    def draw(self):
        c = self.canv
        c.setFillColor(LIGHT_BG)
        c.roundRect(0, 0, self.w, self.height, 6, fill=1, stroke=0)
        c.setFillColor(PETROL)
        c.circle(21, self.height/2, 13, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont('Helvetica-Bold', 11)
        c.drawCentredString(21, self.height/2 - 4, str(self.n))
        c.setFillColor(DARK_NAVY)
        c.setFont('Helvetica-Bold', 10.5)
        c.drawString(42, self.height - 16, self.t)
        c.setFont('Helvetica', 8.8)
        c.setFillColor(colors.HexColor('#555'))
        y = self.height - 30
        for ln in self._lines:
            c.drawString(42, y, ln)
            y -= 12.8


def callout(body, bg, border, tag, title):
    """A rounded, coloured info box that supports rich HTML text and paginates.
    Built as a 1-cell Table so bold/Courier markup renders and it flows across pages."""
    tag_style = ParagraphStyle('tag', fontName='Helvetica-Bold', fontSize=8.5,
        textColor=border, leading=12, spaceAfter=2)
    body_style = ParagraphStyle('cob', fontName='Helvetica', fontSize=9.5,
        textColor=colors.HexColor('#2a2a35'), leading=14)
    inner = [
        [Paragraph(f'{tag} &nbsp;·&nbsp; {title}', tag_style)],
        [Paragraph(body, body_style)],
    ]
    it = Table(inner, colWidths=[CONTENT_W - 16])
    it.setStyle(TableStyle([
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (0, 0), 0),
        ('BOTTOMPADDING', (0, 0), (0, 0), 2),
        ('TOPPADDING', (0, 1), (0, 1), 0),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 0),
    ]))
    outer = Table([[it]], colWidths=[CONTENT_W])
    outer.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), bg),
        ('BOX', (0, 0), (-1, -1), 1.1, border),
        ('LINEBEFORE', (0, 0), (0, -1), 4, border),
        ('LEFTPADDING', (0, 0), (-1, -1), 14),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 9),
        ('ROUNDEDCORNERS', [7, 7, 7, 7]),
    ]))
    return outer


def tip(body, title='Good to know'):
    return callout(body, GREEN_SOFT, GREEN, 'TIP', title)

def warn(body, title='Watch out'):
    return callout(body, AMBER_SOFT, AMBER, 'WARNING', title)

def info(body, title='In our project'):
    return callout(body, INFO_SOFT, INFO, 'NOTE', title)

def analogy(body, title='Real-life analogy'):
    return callout(body, colors.HexColor('#F3E5F5'), VIOLET, 'ANALOGY', title)


# ═══════════════════════════════════════════════════════════════
# TABLE HELPER
# ═══════════════════════════════════════════════════════════════
def make_table(header, rows, col_widths, header_bg=PETROL, code_cols=None,
               font=8.6, align_left=True):
    code_cols = code_cols or []
    data = []
    head_cells = [Paragraph(f'<b>{h}</b>', S['cell_b']) for h in header]
    data.append(head_cells)
    for r in rows:
        row_cells = []
        for i, cell in enumerate(r):
            st = S['cell_code'] if i in code_cols else S['cell']
            row_cells.append(Paragraph(str(cell), st))
        data.append(row_cells)
    t = Table(data, colWidths=col_widths, repeatRows=1)
    style = [
        ('BACKGROUND', (0, 0), (-1, 0), header_bg),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 7),
        ('RIGHTPADDING', (0, 0), (-1, -1), 7),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_BG]),
        ('LINEBELOW', (0, 0), (-1, -1), 0.4, BORDER),
        ('LINEAFTER', (0, 0), (-2, -1), 0.4, BORDER),
        ('BOX', (0, 0), (-1, -1), 0.6, BORDER),
        ('ROUNDEDCORNERS', [5, 5, 5, 5]),
    ]
    t.setStyle(TableStyle(style))
    return t


# ═══════════════════════════════════════════════════════════════
# FIGURE HELPER
# ═══════════════════════════════════════════════════════════════
def fig_to_image(fig, width_cm=16.5, dpi=155):
    buf = BytesIO()
    fig.savefig(buf, format='png', dpi=dpi, bbox_inches='tight',
                facecolor='white', edgecolor='none', pad_inches=0.15)
    plt.close(fig)
    buf.seek(0)
    w = width_cm * cm
    fw, fh = fig.get_size_inches()
    return Image(buf, width=w, height=w * (fh / fw))


def _box(ax, x, y, w, h, text, bg, ec, fs=10, tc='#222', bold=True):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.12',
        facecolor=bg, edgecolor=ec, linewidth=2))
    ax.text(x + w/2, y + h/2, text, ha='center', va='center', fontsize=fs,
            fontweight='bold' if bold else 'normal', color=tc, family='sans-serif')


def _arrow(ax, x1, y1, x2, y2, label='', color='#009999', lw=2.2, style='->', ls='-',
           lblcolor=None, fs=8, dy=0.28):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
        arrowprops=dict(arrowstyle=style, color=color, lw=lw, linestyle=ls))
    if label:
        ax.text((x1+x2)/2, (y1+y2)/2 + dy, label, ha='center', fontsize=fs,
                color=lblcolor or color, fontweight='bold', family='sans-serif')


# ── Diagram: what is hosting (localhost vs server) ──
def dia_localhost_vs_server():
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(14, 5.2))
    for ax in (a1, a2):
        ax.set_xlim(0, 10); ax.set_ylim(0, 8); ax.axis('off')
    # localhost
    _box(a1, 3, 5.6, 4, 1.6, 'YOUR LAPTOP', '#E3F2FD', '#1565C0', 11)
    _box(a1, 1.2, 2.6, 3, 1.4, 'Browser', '#FFF3E0', '#E65100', 9.5)
    _box(a1, 5.8, 2.6, 3, 1.4, 'App (Node)', '#E8F5E9', '#2E7D32', 9.5)
    _arrow(a1, 4.2, 3.3, 5.8, 3.3, 'localhost', '#009999')
    a1.text(5, 0.8, 'Only YOU can see it', ha='center', fontsize=11,
            color='#C62828', fontweight='bold')
    a1.set_title('BEFORE: running on localhost', fontsize=13, fontweight='bold', color='#000028')
    # server
    _box(a2, 3, 6, 4, 1.5, 'SERVER (always on)', '#E8F5E9', '#2E7D32', 10.5)
    _box(a2, 0.5, 3, 2.6, 1.3, 'Colleague 1', '#E3F2FD', '#1565C0', 8.5)
    _box(a2, 3.7, 3, 2.6, 1.3, 'Colleague 2', '#E3F2FD', '#1565C0', 8.5)
    _box(a2, 6.9, 3, 2.6, 1.3, 'Colleague 3', '#E3F2FD', '#1565C0', 8.5)
    for x in (1.8, 5.0, 8.2):
        _arrow(a2, x, 4.3, 5, 6.0, '', '#009999', 1.8)
    a2.text(5, 1.4, 'EVERYONE can see it, anytime', ha='center', fontsize=11,
            color='#2E7D32', fontweight='bold')
    a2.set_title('AFTER: hosted on a server', fontsize=13, fontweight='bold', color='#000028')
    fig.tight_layout(pad=2)
    return fig_to_image(fig, 17)


# ── Diagram: request/response journey ──
def dia_request_flow():
    fig, ax = plt.subplots(figsize=(14, 6.4))
    ax.set_xlim(0, 14); ax.set_ylim(0, 6.4); ax.axis('off')
    steps = [
        (0.2, '1  You click\n"Leaderboard"', '#E3F2FD', '#1565C0'),
        (2.9, '2  Browser sends\nHTTP request', '#FFF3E0', '#E65100'),
        (5.6, '3  Server (Node/\nFlask) receives it', '#E8F5E9', '#2E7D32'),
        (8.3, '4  Reads data\nfrom database', '#F3E5F5', '#7B1FA2'),
        (11.0, '5  Sends JSON\nback -> renders', '#FCE4EC', '#C62828'),
    ]
    for x, label, bg, ec in steps:
        _box(ax, x, 2.6, 2.4, 2.4, label, bg, ec, 9.5, ec)
    for x1, x2 in [(2.6, 2.9), (5.3, 5.6), (8.0, 8.3), (10.7, 11.0)]:
        _arrow(ax, x1, 3.8, x2, 3.8, '', '#009999', 2.6)
    ax.annotate('', xy=(1.4, 2.4), xytext=(12.2, 2.4),
        arrowprops=dict(arrowstyle='->', color='#999', lw=1.5, linestyle='dashed',
                        connectionstyle='arc3,rad=0.25'))
    ax.text(6.8, 1.0, 'The whole round-trip usually takes a few hundredths of a second',
            ha='center', fontsize=9.5, color='#666', style='italic')
    ax.set_title('The journey of ONE request (browser → server → database → back)',
                 fontsize=13.5, fontweight='bold', color='#000028', pad=12)
    fig.tight_layout()
    return fig_to_image(fig, 17)


# ── Diagram: IIS reverse proxy vs direct ──
def dia_iis_vs_direct():
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(13, 8))
    for ax in (a1, a2):
        ax.set_xlim(0, 14); ax.set_ylim(0, 3.4); ax.axis('off')
    # WITH IIS
    _box(a1, 0.3, 1.0, 2.6, 1.4, 'Browser', '#E3F2FD', '#1565C0', 10)
    _box(a1, 4.0, 1.0, 3.2, 1.4, 'IIS\n(port 8080)', '#FFF3E0', '#E65100', 10)
    _box(a1, 8.4, 1.0, 3.2, 1.4, 'Node app\n(127.0.0.1:3000)', '#E8F5E9', '#2E7D32', 10)
    _arrow(a1, 2.9, 1.7, 4.0, 1.7, 'request', '#009999')
    _arrow(a1, 7.2, 1.7, 8.4, 1.7, 'reverse proxy', '#009999')
    a1.text(12.2, 1.7, 'DB', ha='center', va='center', fontsize=10, fontweight='bold', color='#7B1FA2')
    _arrow(a1, 11.6, 1.7, 12.0, 1.7, '', '#7B1FA2', 1.6)
    a1.set_title('OPTION A — WITH IIS (reverse proxy). IIS keeps serving Teamcenter too.',
                 fontsize=11.5, fontweight='bold', color='#000028', loc='left')
    # WITHOUT IIS
    _box(a2, 0.3, 1.0, 2.6, 1.4, 'Browser', '#E3F2FD', '#1565C0', 10)
    _box(a2, 5.6, 1.0, 3.4, 1.4, 'Node app\n(port 8080)', '#E8F5E9', '#2E7D32', 10)
    _arrow(a2, 2.9, 1.7, 5.6, 1.7, 'direct connection', '#009999')
    a2.text(9.8, 1.7, 'DB', ha='center', va='center', fontsize=10, fontweight='bold', color='#7B1FA2')
    _arrow(a2, 9.0, 1.7, 9.4, 1.7, '', '#7B1FA2', 1.6)
    a2.set_title('OPTION B — WITHOUT IIS (direct). Node owns its own dedicated port.',
                 fontsize=11.5, fontweight='bold', color='#000028', loc='left')
    fig.tight_layout(pad=2)
    return fig_to_image(fig, 17)


# ── Diagram: DNS resolution ──
def dia_dns():
    fig, ax = plt.subplots(figsize=(14, 4.6))
    ax.set_xlim(0, 14); ax.set_ylim(0, 4.6); ax.axis('off')
    _box(ax, 0.3, 1.7, 3.0, 1.4, 'Browser asks:\n"where is\nSN1W7220?"', '#E3F2FD', '#1565C0', 9)
    _box(ax, 4.4, 1.7, 3.2, 1.4, 'DNS server\n(the phonebook)', '#FFF3E0', '#E65100', 9.5)
    _box(ax, 8.8, 1.7, 4.6, 1.4, 'Answer:\n161.218.195.80', '#E8F5E9', '#2E7D32', 10)
    _arrow(ax, 3.3, 2.4, 4.4, 2.4, 'name', '#009999')
    _arrow(ax, 7.6, 2.4, 8.8, 2.4, 'IP address', '#009999')
    ax.set_title('DNS = the internet phonebook (turns a NAME into a NUMBER)',
                 fontsize=13, fontweight='bold', color='#000028', pad=10)
    fig.tight_layout()
    return fig_to_image(fig, 17)


# ── Diagram: CI/CD + GitLab redirect ──
def dia_cicd():
    fig, ax = plt.subplots(figsize=(14, 5.4))
    ax.set_xlim(0, 14); ax.set_ylim(0, 5.4); ax.axis('off')
    _box(ax, 0.2, 3.2, 2.5, 1.4, 'You: git push', '#E3F2FD', '#1565C0', 9.5)
    _box(ax, 3.3, 3.2, 2.7, 1.4, 'GitHub / GitLab\nrepository', '#FFF3E0', '#E65100', 9.5)
    _box(ax, 6.6, 3.2, 2.7, 1.4, 'CI/CD pipeline\n(auto build+test)', '#E8F5E9', '#2E7D32', 9.5)
    _box(ax, 9.9, 3.2, 3.6, 1.4, 'Deployed live\n(Render / server)', '#FCE4EC', '#C62828', 9.5)
    _arrow(ax, 2.7, 3.9, 3.3, 3.9, '', '#009999')
    _arrow(ax, 6.0, 3.9, 6.6, 3.9, '', '#009999')
    _arrow(ax, 9.3, 3.9, 9.9, 3.9, '', '#009999')
    _box(ax, 3.3, 0.6, 4.0, 1.3, 'GitLab Pages\n(static redirect page)', '#EDE7F6', '#7B1FA2', 9)
    _box(ax, 9.0, 0.6, 4.0, 1.3, 'Redirects visitor\nto the live server', '#E0F7FA', '#00838F', 9)
    _arrow(ax, 5.3, 3.2, 5.3, 1.9, '', '#7B1FA2', 1.8)
    _arrow(ax, 7.3, 1.25, 9.0, 1.25, 'auto-forward', '#00838F', 1.8)
    ax.set_title('CI/CD — from "git push" to "live", plus the GitLab redirect page',
                 fontsize=13, fontweight='bold', color='#000028', pad=10)
    fig.tight_layout()
    return fig_to_image(fig, 17)


# ── Diagram: database read/write both ways ──
def dia_database():
    fig, ax = plt.subplots(figsize=(14, 5.0))
    ax.set_xlim(0, 14); ax.set_ylim(0, 5.0); ax.axis('off')
    _box(ax, 0.3, 2.0, 3.0, 1.4, 'Frontend\n(app.js)', '#FFF3E0', '#E65100', 10)
    _box(ax, 5.2, 2.0, 3.4, 1.4, 'Backend\n(server.js / app.py)', '#E8F5E9', '#2E7D32', 10)
    _box(ax, 10.5, 3.0, 3.2, 1.4, 'MongoDB Atlas\n(cloud)', '#FFF3E0', '#E65100', 9.5)
    _box(ax, 10.5, 0.6, 3.2, 1.4, 'db.json\n(local file)', '#EDE7F6', '#7B1FA2', 9.5)
    _arrow(ax, 3.3, 3.0, 5.2, 3.0, 'POST (write)', '#C62828', 2.0, dy=0.25)
    _arrow(ax, 5.2, 2.4, 3.3, 2.4, 'GET (read)', '#2E7D32', 2.0, dy=-0.4)
    _arrow(ax, 8.6, 3.1, 10.5, 3.5, 'if cloud set', '#009999', 1.8)
    _arrow(ax, 8.6, 2.3, 10.5, 1.2, 'else fallback', '#7B1FA2', 1.8, ls='dashed')
    ax.set_title('How data flows BOTH ways (read + write) and where it is stored',
                 fontsize=13, fontweight='bold', color='#000028', pad=10)
    fig.tight_layout()
    return fig_to_image(fig, 17)


# ── Diagram: hosting options compared ──
def dia_options():
    fig, ax = plt.subplots(figsize=(13, 6.2))
    ax.set_xlim(0, 12); ax.set_ylim(0, 6.2); ax.axis('off')
    opts = [
        (0.3, 3.4, 'RENDER\n(external cloud)', '#E3F2FD', '#1565C0'),
        (3.3, 3.4, 'SDC + Fargate\n(Siemens cloud)', '#E8F5E9', '#2E7D32'),
        (6.3, 3.4, 'SN1W7220 + IIS\n(reverse proxy)', '#FFF3E0', '#E65100'),
        (9.3, 3.4, 'Your PC\n(last resort)', '#FCE4EC', '#C62828'),
    ]
    for x, y, label, bg, ec in opts:
        _box(ax, x, y, 2.5, 1.9, label, bg, ec, 9.5, ec)
    verdicts = [
        (0.3, 'Good for REVIEW now\n(free, external data)'),
        (3.3, 'BEST internal home\n(if approved)'),
        (6.3, 'Solid fallback\n(no disruption)'),
        (9.3, 'Only when you are\nonline'),
    ]
    for x, txt in verdicts:
        ax.text(x + 1.25, 2.3, txt, ha='center', va='top', fontsize=8.4, color='#444')
    ax.set_title('The four realistic hosting options, side by side',
                 fontsize=13.5, fontweight='bold', color='#000028', pad=12)
    fig.tight_layout()
    return fig_to_image(fig, 17)


# ═══════════════════════════════════════════════════════════════
# PAGE DECORATION (header rule + footer with page number)
# ═══════════════════════════════════════════════════════════════
def decorate(canvas, doc):
    canvas.saveState()
    # top hairline
    canvas.setStrokeColor(BORDER)
    canvas.setLineWidth(0.5)
    canvas.line(MARGIN, PAGE_H - MARGIN + 12, PAGE_W - MARGIN, PAGE_H - MARGIN + 12)
    canvas.setFont('Helvetica', 7.5)
    canvas.setFillColor(GREY)
    canvas.drawString(MARGIN, PAGE_H - MARGIN + 16, 'EMBRACE AI — Hosting & Architecture Handbook')
    canvas.drawRightString(PAGE_W - MARGIN, PAGE_H - MARGIN + 16, 'Siemens · Engineering Systems')
    # footer
    canvas.setStrokeColor(BORDER)
    canvas.line(MARGIN, MARGIN - 6, PAGE_W - MARGIN, MARGIN - 6)
    canvas.setFillColor(PETROL)
    canvas.setFont('Helvetica-Bold', 8)
    canvas.drawString(MARGIN, MARGIN - 16, 'SIEMENS · Engineering Systems')
    canvas.setFillColor(GREY)
    canvas.setFont('Helvetica', 8)
    canvas.drawRightString(PAGE_W - MARGIN, MARGIN - 16, f'Page {doc.page}')
    canvas.restoreState()


def cover(canvas, doc):
    canvas.saveState()
    # navy gradient background (stacked bands)
    steps = 60
    for i in range(steps):
        t = i / steps
        r = int(0x00 + (0x0A - 0x00) * t)
        g = int(0x00 + (0x1E - 0x00) * t)
        b = int(0x28 + (0x3F - 0x28) * t)
        canvas.setFillColor(colors.Color(r/255, g/255, b/255))
        canvas.rect(0, PAGE_H * (1 - (i+1)/steps), PAGE_W, PAGE_H/steps + 1, fill=1, stroke=0)
    # glass orbs
    for cx, cy, rad, col in [(90, 700, 120, PETROL), (500, 180, 150, GREEN), (470, 620, 70, PETROL_LIGHT)]:
        canvas.setFillColor(colors.Color(col.red, col.green, col.blue, alpha=0.14))
        canvas.circle(cx, cy, rad, fill=1, stroke=0)
    canvas.restoreState()


# ═══════════════════════════════════════════════════════════════
# CONTENT BUILDER
# ═══════════════════════════════════════════════════════════════
def ch(story, number, title, subtitle=''):
    """Start a new chapter on a fresh page."""
    story.append(PageBreak())
    _set = SetChapter(title)
    story.append(_set)
    story.append(ChapterHeader(number, title, subtitle))
    story.append(Spacer(1, 14))


class SetChapter(Flowable):
    """Invisible flowable that updates the running footer chapter label."""
    def __init__(self, name):
        super().__init__()
        self.name = name
        self.width = 0
        self.height = 0
    def draw(self):
        _CURRENT['chapter'] = self.name


def P(story, text):
    story.append(Paragraph(text, S['body']))

def PL(story, text):
    story.append(Paragraph(text, S['body_l']))

def H2(story, text):
    story.append(Paragraph(text, S['h2']))

def H3(story, text):
    story.append(Paragraph(text, S['h3']))

def bullets(story, items):
    for it in items:
        story.append(Paragraph(f'<font color="#009999">●</font>  {it}', S['bullet']))

def sp(story, h=8):
    story.append(Spacer(1, h))

def cap(story, text):
    story.append(Paragraph(text, S['caption']))


def build_story():
    story = []

    # ─────────────── COVER ───────────────
    story.append(Spacer(1, 170))
    story.append(Paragraph('Web Hosting', S['title']))
    story.append(Paragraph('&amp; Architecture Handbook', S['title']))
    sp(story, 10)
    story.append(Paragraph('From zero knowledge to confidently hosting the EMBRACE AI dashboard',
                           S['subtitle']))
    sp(story, 60)
    story.append(Paragraph('A complete, plain-English guide — servers, ports, DNS, proxies, IIS, '
                           'Node.js, databases, CI/CD, Docker &amp; the Siemens cloud',
                           ParagraphStyle('cvr', fontName='Helvetica', fontSize=11,
                                          textColor=colors.white, alignment=TA_CENTER, leading=17)))
    sp(story, 80)
    story.append(Paragraph('SIEMENS · Engineering Systems · AI CatalyESt',
                           ParagraphStyle('cf', fontName='Helvetica-Bold', fontSize=12,
                                          textColor=PETROL_LIGHT, alignment=TA_CENTER)))
    story.append(Paragraph(datetime.now().strftime('Edition · %B %Y'),
                           ParagraphStyle('cd', fontName='Helvetica', fontSize=9.5,
                                          textColor=colors.HexColor('#8892b0'), alignment=TA_CENTER)))

    # ─────────────── HOW TO READ ───────────────
    story.append(PageBreak())
    story.append(SetChapter('How to read this handbook'))
    story.append(Paragraph('How to read this handbook', S['h1']))
    story.append(HRFlowable(width='100%', thickness=2, color=PETROL, spaceAfter=12))
    P(story, 'This book assumes you know <b>nothing</b> about web servers or hosting. Every term is '
             'explained in plain words, with a real-life analogy, before we connect it to our project. '
             'You can read cover to cover, or jump to any chapter — each is self-contained.')
    sp(story, 4)
    story.append(tip('Boxes like this one highlight useful facts. Amber boxes warn about common '
                     'mistakes, blue boxes show how a concept maps to OUR project, and purple boxes '
                     'give a real-life analogy to make an idea click.'))
    sp(story, 4)
    story.append(warn('You do NOT need to memorise anything. The goal is understanding. Keep the '
                      'glossary at the back handy while you read.'))

    # ─────────────── TABLE OF CONTENTS ───────────────
    story.append(PageBreak())
    story.append(SetChapter('Contents'))
    story.append(Paragraph('Contents', S['h1']))
    story.append(HRFlowable(width='100%', thickness=2, color=PETROL, spaceAfter=14))
    toc = [
        ('Part 1 — The Foundations', [
            '1. What "hosting" really means (and why we need it)',
            '2. What a server is, and what it must provide',
            '3. The client–server model: browser, frontend & backend',
        ]),
        ('Part 2 — The Building Blocks', [
            '4. The technology stack, layer by layer',
            '5. Every file in our project, explained',
            '6. The full architecture, end to end',
        ]),
        ('Part 3 — The Network Plumbing', [
            '7. localhost, IP addresses & ports',
            '8. DNS: the internet phonebook',
            '9. Routing: how data finds its way',
            '10. Proxies & reverse proxies',
        ]),
        ('Part 4 — Windows Server Hosting', [
            '11. IIS: what it is and where it fits',
            '12. ARR & URL Rewrite',
            '13. IIS-based vs non-IIS hosting',
            '14. Node.js, NSSM & Windows services',
            '15. WebSockets & real-time features',
        ]),
        ('Part 5 — Data, Delivery & the Cloud', [
            '16. How our database stores & retrieves data',
            '17. CI/CD pipelines & our GitLab redirect',
            '18. Docker, AWS Fargate & the Siemens SDC plan',
            '19. Our two deployment scripts, explained',
            '20. Choosing the right host — decision guide',
        ]),
        ('Reference', [
            'A. Glossary of every term',
            'B. Quick command runbook',
        ]),
    ]
    for part, items in toc:
        story.append(Paragraph(part, S['toc_ch']))
        for it in items:
            story.append(Paragraph(it, S['toc_it']))
        sp(story, 6)

    # ═══════════ CHAPTER 1 ═══════════
    ch(story, 1, 'What hosting means', 'and why a laptop is not enough')
    P(story, '“Hosting” simply means putting your website or app on a computer that is <b>always '
             'switched on and always connected to the network</b>, so that other people can open it '
             'whenever they want — without needing your laptop.')
    story.append(analogy('Think of your app like a shop. While you build it on your laptop, the shop '
                         'is inside your house with the doors locked — only you can walk around it. '
                         '“Hosting” is like renting a unit on a busy high street: the shop is now on a '
                         'street everyone can reach, open 24/7, whether or not you are personally there.'))
    H2(story, 'Why we cannot just use a laptop')
    bullets(story, [
        'A laptop gets closed, sleeps, or goes offline — the app would vanish for everyone.',
        'Home/office networks hide your laptop behind privacy barriers, so colleagues cannot reach it.',
        'A laptop is not built to safely handle many people connecting at once.',
    ])
    story.append(dia_localhost_vs_server())
    cap(story, 'Left: on your laptop only you can see the app. Right: on a server, the whole team can.')
    story.append(info('We first hosted EMBRACE AI on <b>Render</b> (a cloud host) so the whole team '
                      'could review it at a public link, and we are now planning a permanent, '
                      'Siemens-internal home. This handbook explains every option.'))

    # ═══════════ CHAPTER 2 ═══════════
    ch(story, 2, 'What a server is', 'the always-on computer behind every website')
    P(story, 'A <b>server</b> is just a computer — but one designed to stay on continuously and to '
             '“serve” its files and data to other computers that ask for them. The computers that ask '
             'are called <b>clients</b> (your browser is a client).')
    story.append(analogy('A server is like a restaurant kitchen. Customers (browsers) send orders '
                         '(requests). The kitchen (server) prepares the dish (data) and sends it back. '
                         'The kitchen never closes, and it can cook for many tables at once.'))
    H2(story, 'What a computer must provide to be a good server')
    story.append(make_table(
        ['Requirement', 'Why it matters', 'Our situation'],
        [
            ['Always on', 'If it sleeps, the site goes down for everyone', 'SN1W7220 is a data-centre server, always on'],
            ['Stable network + reachable address', 'Clients must be able to find and reach it', 'It has a fixed name &amp; IP on the Siemens network'],
            ['Enough CPU &amp; memory', 'To handle many visitors smoothly', 'Server-grade hardware, far beyond a laptop'],
            ['A web server program', 'Software that listens for requests', 'IIS (already there) and/or our Node app'],
            ['Auto-restart on failure', 'Recover without a human at 3am', 'NSSM service + restart rules (Chapter 14)'],
            ['Security &amp; backups', 'Protect data and recover from mistakes', 'Firewall rules + backup scripts in the repo'],
        ],
        [CONTENT_W*0.24, CONTENT_W*0.42, CONTENT_W*0.34]))
    sp(story, 6)
    story.append(tip('“Server” can mean the physical machine OR the program running on it (a “web '
                     'server” like IIS or Node). Same word, two meanings — the context tells you which.'))

    # ═══════════ CHAPTER 3 ═══════════
    ch(story, 3, 'The client–server model', 'browser, frontend and backend')
    P(story, 'Every web app has two halves that talk to each other:')
    H3(story, 'The frontend (what you see)')
    P(story, 'The visual part that runs <b>inside your browser</b>: the pages, buttons, colours and '
             'animations. Built with HTML (structure), CSS (styling) and JavaScript (behaviour).')
    H3(story, 'The backend (what you don’t see)')
    P(story, 'The part that runs <b>on the server</b>: it holds the real data, applies the rules, and '
             'answers the frontend’s requests. In our project the backend is written in Node.js '
             '(<font face="Courier">server.js</font>) and mirrored in Python/Flask (<font face="Courier">app.py</font>).')
    story.append(analogy('The frontend is the dining area you sit in; the backend is the kitchen and '
                         'store-room. You interact with the dining area, but the food (data) actually '
                         'comes from the kitchen you never enter.'))
    story.append(dia_request_flow())
    cap(story, 'A single click becomes a request that travels to the server and comes back as data.')

    # ═══════════ CHAPTER 4 ═══════════
    ch(story, 4, 'The technology stack', 'every layer and the language it speaks')
    P(story, 'A “stack” is the set of technologies layered together to make the app work. Here is '
             'ours, from what the user sees down to where data rests.')
    story.append(make_table(
        ['Layer', 'Technology', 'Language', 'What it does'],
        [
            ['Structure', 'HTML', 'HTML', 'Defines the page content &amp; sections'],
            ['Styling', 'CSS', 'CSS', 'Colours, layout, glassmorphism, themes'],
            ['Behaviour', 'Vanilla JavaScript', 'JavaScript', 'Clicks, rendering, quiz logic, side toggle'],
            ['Real-time', 'Socket.IO', 'JavaScript', 'Live quizzes &amp; surveys (WebSockets)'],
            ['Backend (main)', 'Node.js + Express', 'JavaScript', 'Serves pages, runs the API'],
            ['Backend (mirror)', 'Flask + Flask-SocketIO', 'Python', 'Identical API, used on Render'],
            ['Database', 'JSON file / MongoDB', 'JSON', 'Stores members, points, quizzes, etc.'],
            ['Process manager', 'NSSM', '—', 'Keeps the app running as a service'],
            ['Web server (server)', 'IIS', '—', 'Optional front door / reverse proxy'],
        ],
        [CONTENT_W*0.19, CONTENT_W*0.26, CONTENT_W*0.17, CONTENT_W*0.38]))
    sp(story, 6)
    story.append(info('We keep <b>two backends in sync</b> on purpose: Node (<font face="Courier">server.js</font>) '
                      'for the Windows server, and Flask (<font face="Courier">app.py</font>) for Render. '
                      'They expose the exact same API so either can run the app.')
                 )

    # ═══════════ CHAPTER 5 ═══════════
    ch(story, 5, 'Every file, explained', 'what each file is, its extension & tech')
    P(story, 'A file’s <b>extension</b> (the letters after the dot) tells the computer what kind of '
             'file it is and which program should open it. Here is every important file in the project.')
    H2(story, 'Core application files')
    story.append(make_table(
        ['File', 'Ext', 'Type', 'Tech', 'Purpose'],
        [
            ['server.js', '.js', 'JavaScript source', 'Node.js', 'Primary backend: API + WebSockets'],
            ['app.py', '.py', 'Python source', 'Flask', 'Mirror backend (Render)'],
            ['public/index.html', '.html', 'Web page', 'HTML', 'The single-page app shell'],
            ['public/js/app.js', '.js', 'JavaScript source', 'Browser JS', 'All frontend logic'],
            ['public/css/styles.css', '.css', 'Stylesheet', 'CSS', 'All visual styling &amp; themes'],
            ['data/db.json', '.json', 'Data file', 'JSON', 'The flat-file database'],
        ],
        [CONTENT_W*0.22, CONTENT_W*0.08, CONTENT_W*0.20, CONTENT_W*0.14, CONTENT_W*0.36],
        code_cols=[0]))
    H2(story, 'Configuration &amp; dependency files')
    story.append(make_table(
        ['File', 'Ext', 'Type', 'Purpose'],
        [
            ['package.json', '.json', 'JSON config', 'Lists Node dependencies &amp; scripts'],
            ['requirements.txt', '.txt', 'Text list', 'Lists Python packages to install'],
            ['Procfile', '(none)', 'Text config', 'Tells the cloud how to start the app'],
            ['render.yaml', '.yaml', 'YAML config', 'Render build/run settings &amp; env vars'],
            ['.python-version', '(dotfile)', 'Text config', 'Pins Python 3.12 on Render'],
            ['.gitlab-ci.yml', '.yml', 'YAML config', 'The CI/CD pipeline definition'],
            ['.gitignore', '(dotfile)', 'Text config', 'Files git should not track'],
            ['deploy/iis/web.config', '.config', 'XML config', 'IIS reverse-proxy rules'],
        ],
        [CONTENT_W*0.26, CONTENT_W*0.12, CONTENT_W*0.18, CONTENT_W*0.44],
        code_cols=[0]))
    sp(story, 6)
    story.append(tip('<b>JSON</b> (JavaScript Object Notation) and <b>YAML</b> are both simple, '
                     'human-readable ways to store settings and data as “key: value” pairs. XML is an '
                     'older, tag-based format that IIS uses for its <font face="Courier">web.config</font>.'))
    H2(story, 'Deployment scripts (the deploy/windows folder)')
    story.append(make_table(
        ['File', 'Ext', 'Type', 'Purpose'],
        [
            ['host-with-iis.bat', '.bat', 'Batch script', 'Set up hosting behind IIS (reverse proxy)'],
            ['host-without-iis.bat', '.bat', 'Batch script', 'Set up direct Node hosting on a port'],
            ['setup-server.ps1', '.ps1', 'PowerShell', 'Install Node + NSSM on the server'],
            ['install-service.ps1', '.ps1', 'PowerShell', 'Register the app as a Windows service'],
            ['update-app.ps1', '.ps1', 'PowerShell', 'Pull latest code &amp; restart safely'],
            ['backup-data.ps1', '.ps1', 'PowerShell', 'Back up db.json &amp; avatars'],
        ],
        [CONTENT_W*0.26, CONTENT_W*0.10, CONTENT_W*0.18, CONTENT_W*0.46],
        code_cols=[0]))
    sp(story, 6)
    story.append(info('A <b>.bat</b> file is a Windows “batch” script — a list of commands the system '
                      'runs top to bottom when you double-click it. A <b>.ps1</b> file is a more '
                      'powerful PowerShell script. We use both to make deployment one-click.'))

    # ═══════════ CHAPTER 6 ═══════════
    ch(story, 6, 'The full architecture', 'how all the pieces connect')
    P(story, 'Now that you know the parts, here is how they fit together when someone uses the app.')
    story.append(dia_database())
    cap(story, 'Data flows in both directions: the frontend reads (GET) and writes (POST) via the backend.')
    H2(story, 'The end-to-end path of a real action')
    story.append(StepBox(1, 'You open the site', 'Your browser requests the page from the server; it returns index.html, styles.css and app.js.'))
    sp(story, 4)
    story.append(StepBox(2, 'The frontend loads data', 'app.js calls the backend API (for example /api/leaderboard) to fetch the current data.'))
    sp(story, 4)
    story.append(StepBox(3, 'The backend answers', 'server.js reads the database, computes the result, and returns it as JSON.'))
    sp(story, 4)
    story.append(StepBox(4, 'The page renders', 'app.js turns the JSON into the visible leaderboard, calendar or quiz on screen.'))
    sp(story, 4)
    story.append(StepBox(5, 'Real-time updates', 'For live quizzes, a WebSocket keeps an open line so updates appear instantly, with no refresh.'))

    # ═══════════ CHAPTER 7 ═══════════
    ch(story, 7, 'localhost, IP & ports', 'addresses inside and outside a computer')
    H2(story, 'What is localhost?')
    P(story, '<b>localhost</b> means “this very computer”. Its special address is '
             '<font face="Courier">127.0.0.1</font>. When the app talks to '
             '<font face="Courier">localhost:3000</font>, it is talking to a program on the same '
             'machine — nobody else on the network is involved.')
    story.append(analogy('localhost is like talking to yourself in your own room. Others in the '
                         'building (the network) cannot hear you unless you open a window (a public port).'))
    H2(story, 'What is an IP address?')
    P(story, 'An <b>IP address</b> is a computer’s number on a network, like '
             '<font face="Courier">161.218.195.80</font>. It is how machines find each other. Names '
             '(like SN1W7220) are friendlier, and DNS translates the name into the number (Chapter 8).')
    H2(story, 'What is a port?')
    P(story, 'A single computer runs many network programs at once. A <b>port</b> is a numbered door '
             'so requests reach the right program. The web uses port <b>80</b> (HTTP) and <b>443</b> '
             '(HTTPS) by default; other programs use other numbers.')
    story.append(analogy('The IP address is a building’s street address; the port is the specific '
                         'apartment number inside. “161.218.195.80:8080” means “that building, apartment 8080”.'))
    H2(story, 'How to choose a port without clashing')
    bullets(story, [
        'Two programs cannot share the same port — that causes the exact conflict that broke us before.',
        'Ports 0–1023 are reserved for standard services (80, 443, etc.). Pick a higher one for apps.',
        'Good app choices: 3000, 8080, 8081. Our scripts default Node to 3000 (private) or 8080 (public).',
        'Always check a port is free first — our .bat script runs <font face="Courier">netstat -ano | findstr LISTENING</font> to see what is busy.',
    ])
    story.append(warn('On SN1W7220, IIS already uses port 80 for Teamcenter and other apps. That is '
                      'exactly why our scripts put EMBRACE AI on a <b>separate dedicated port</b> — so '
                      'nothing existing is disturbed.'))

    # ═══════════ CHAPTER 8 ═══════════
    ch(story, 8, 'DNS: the phonebook', 'turning names into numbers')
    P(story, 'Humans remember names; computers use numbers. <b>DNS</b> (Domain Name System) is the '
             'service that translates a name like <font face="Courier">SN1W7220.AD001.SIEMENS.NET</font> '
             'into the IP number the browser actually connects to.')
    story.append(dia_dns())
    cap(story, 'The browser asks DNS for the number behind a name, then connects to that number.')
    story.append(analogy('DNS is a phonebook. You know your friend’s name (the domain) but to actually '
                         'call them you need their phone number (the IP). The phonebook does the lookup.'))
    story.append(info('When we tested the server from outside the office, DNS returned a different '
                      '(VPN) number and the site seemed “down”. It was really a name-resolution issue '
                      '— connecting to the VPN fixed it instantly. DNS problems often masquerade as '
                      '“the server is down”.'))

    # ═══════════ CHAPTER 9 ═══════════
    ch(story, 9, 'Routing', 'how a request finds the right destination')
    P(story, '<b>Routing</b> is the general idea of directing a request to the correct place. It '
             'happens at two levels in our world:')
    H3(story, '1. Network routing')
    P(story, 'Across the network, routers pass your request hop by hop until it reaches the server’s '
             'IP address — like a parcel moving through sorting centres to a postal address.')
    H3(story, '2. Application routing')
    P(story, 'Inside the backend, the code looks at the request’s <b>path</b> (for example '
             '<font face="Courier">/api/members</font> vs <font face="Courier">/api/quizzes</font>) '
             'and runs the matching function. Each path is a “route”.')
    story.append(CodeBlock('app.get(\'/api/members\', ...)   // route for the member list\n'
                           'app.post(\'/api/quizzes\', ...)   // route to create a quiz\n'
                           'app.get(\'/api/leaderboard\', ...) // route for the leaderboard',
                           'javascript'))
    story.append(analogy('Application routing is like a receptionist reading the name on your visitor '
                         'badge and sending you to the correct department. The path is the badge.'))

    # ═══════════ CHAPTER 10 ═══════════
    ch(story, 10, 'Proxies & reverse proxies', 'the helpful middle-man')
    P(story, 'A <b>proxy</b> is a middle-man that stands between two parties and passes messages '
             'between them. A <b>reverse proxy</b> sits in front of your app: visitors talk to the '
             'proxy, and the proxy quietly forwards them to the real app behind it.')
    story.append(analogy('A reverse proxy is like a hotel receptionist. Guests always speak to the '
                         'front desk (the proxy). The desk relays messages to the right room (your app) '
                         'and brings the reply back. Guests never need to know the room number.'))
    H2(story, 'Why use a reverse proxy at all?')
    bullets(story, [
        'One front door (port 80/443) can serve many apps behind it, each on its own private port.',
        'It can add HTTPS, security headers and compression in one place.',
        'It lets EMBRACE AI live <b>alongside</b> Teamcenter on the same IIS server without conflict.',
    ])
    story.append(info('In our IIS option, IIS is the reverse proxy: the browser talks to IIS, and IIS '
                      'forwards to Node on <font face="Courier">127.0.0.1:3000</font>. This is what the '
                      '<font face="Courier">deploy/iis/web.config</font> file configures.'))

    # ═══════════ CHAPTER 11 ═══════════
    ch(story, 11, 'IIS explained', 'the web server already on the Windows machine')
    P(story, '<b>IIS</b> (Internet Information Services) is Microsoft’s built-in web server for '
             'Windows. It listens for web requests and decides what to do with them — serve a file, '
             'or forward the request somewhere else (a reverse proxy).')
    H2(story, 'Where IIS fits for us')
    P(story, 'On SN1W7220, IIS is <b>already running</b> and other teams depend on it (Teamcenter and '
             'more). So IIS must keep running untouched. Our “WITH IIS” option simply adds a new, '
             'separate site next to the existing ones, using ARR to forward EMBRACE AI traffic to Node.')
    story.append(warn('Earlier we tried disabling IIS so Node could take port 80. That is the wrong '
                      'approach here because it would break Teamcenter. The correct approach is to '
                      'LET IIS run and put EMBRACE AI beside it — which both our new scripts do.'))
    story.append(analogy('IIS is like a shopping mall’s main entrance and information desk. Many shops '
                         '(apps) live inside. You do not close the mall to open one new shop — you just '
                         'add your shop and let the info desk point people to it.'))

    # ═══════════ CHAPTER 12 ═══════════
    ch(story, 12, 'ARR & URL Rewrite', 'the two add-ons that make IIS a proxy')
    P(story, 'Out of the box IIS serves files. To make it a reverse proxy that forwards to Node, it '
             'needs two free Microsoft add-ons:')
    H3(story, 'URL Rewrite')
    P(story, 'Lets IIS look at an incoming web address and rewrite/redirect it. We use it to say '
             '“any request → send to <font face="Courier">http://localhost:3000</font>”.')
    H3(story, 'Application Request Routing (ARR)')
    P(story, 'Gives IIS the actual ability to forward (proxy) a request to another server and bring '
             'the answer back. URL Rewrite decides <i>where</i>; ARR does the <i>forwarding</i>.')
    story.append(CodeBlock('<rule name="ReverseProxyToNode" stopProcessing="true">\n'
                           '  <match url="(.*)" />\n'
                           '  <action type="Rewrite" url="http://localhost:3000/{R:1}" />\n'
                           '</rule>', 'xml'))
    cap(story, 'The rewrite rule from our web.config: forward every path to Node on port 3000.')
    story.append(tip('Together, URL Rewrite + ARR turn IIS into a reverse proxy. Both are one-time '
                     'installs on the server; our <font face="Courier">host-with-iis.bat</font> checks '
                     'for them and tells you if they are missing.'))

    # ═══════════ CHAPTER 13 ═══════════
    ch(story, 13, 'IIS vs non-IIS hosting', 'two valid roads to the same destination')
    P(story, 'We built <b>two</b> ready-to-run scripts so your team can pick either approach. Both '
             'keep IIS and Teamcenter running; they differ in who answers the browser.')
    story.append(dia_iis_vs_direct())
    cap(story, 'Option A routes through IIS; Option B lets Node answer directly on its own port.')
    story.append(make_table(
        ['Aspect', 'WITH IIS (reverse proxy)', 'WITHOUT IIS (direct Node)'],
        [
            ['Who answers the browser', 'IIS, then forwards to Node', 'Node directly'],
            ['Port the user sees', 'IIS site port (e.g. 8080)', 'Node’s port (e.g. 8080)'],
            ['Node listens on', '127.0.0.1:3000 (private)', 'the public port'],
            ['Extra setup', 'ARR + URL Rewrite once', 'None'],
            ['HTTPS / headers in one place', 'Yes (via IIS)', 'Handled by Node only'],
            ['Fits Siemens IIS conventions', 'Yes — most “standard”', 'Simpler, less conventional'],
            ['Disturbs Teamcenter?', 'No', 'No'],
            ['Our script', 'host-with-iis.bat', 'host-without-iis.bat'],
        ],
        [CONTENT_W*0.26, CONTENT_W*0.37, CONTENT_W*0.37], code_cols=[]))
    sp(story, 6)
    story.append(tip('If your server team prefers everything behind IIS (common at Siemens), use '
                     'Option A. If they are happy for the app to use its own port, Option B is simpler. '
                     'Neither one disables IIS or touches existing sites.'))

    # ═══════════ CHAPTER 14 ═══════════
    ch(story, 14, 'Node.js, NSSM & services', 'running the app reliably, forever')
    H2(story, 'What is Node.js?')
    P(story, '<b>Node.js</b> lets JavaScript run <b>outside</b> the browser — on a server. It is what '
             'executes our <font face="Courier">server.js</font> backend: listening for requests, '
             'running the API, and handling WebSockets.')
    story.append(analogy('JavaScript used to only work inside browsers. Node.js is like giving that '
                         'same language a passport to work on servers too — same language, new workplace.'))
    H2(story, 'What is a Windows service?')
    P(story, 'A <b>service</b> is a program Windows runs quietly in the background, starting '
             'automatically with the machine — no one needs to be logged in. We want our app to be a '
             'service so it is always up.')
    H2(story, 'What is NSSM?')
    P(story, '<b>NSSM</b> (the “Non-Sucking Service Manager”) is a tiny tool that turns any program — '
             'like <font face="Courier">node server.js</font> — into a proper Windows service. It also '
             '<b>restarts the app automatically</b> if it ever crashes.')
    story.append(make_table(
        ['Command', 'What it does'],
        [
            ['nssm start EmbraceAI', 'Start the app service'],
            ['nssm stop EmbraceAI', 'Stop the app service'],
            ['nssm restart EmbraceAI', 'Restart it (after an update)'],
            ['nssm status EmbraceAI', 'Check if it is running'],
        ],
        [CONTENT_W*0.36, CONTENT_W*0.64], code_cols=[0]))
    sp(story, 6)
    story.append(info('Our service is named <b>EmbraceAI</b>. We also set Windows’ recovery option so '
                      'it auto-restarts up to three times on failure — that is what keeps the site up '
                      'without anyone watching it.'))

    # ═══════════ CHAPTER 15 ═══════════
    ch(story, 15, 'WebSockets', 'the open phone line for real-time features')
    P(story, 'Normal web requests are one-and-done: ask a question, get an answer, hang up. That is '
             'fine for loading a page, but not for a <b>live quiz</b> where scores must update '
             'instantly for everyone.')
    P(story, 'A <b>WebSocket</b> keeps a <b>continuous two-way line open</b> between browser and '
             'server, so either side can send updates the moment they happen. We use the '
             '<b>Socket.IO</b> library on top of WebSockets for our live quizzes and surveys.')
    story.append(analogy('A normal request is like sending a letter and waiting for a reply. A '
                         'WebSocket is like keeping a phone call connected — both people can speak the '
                         'instant they have something to say.'))
    story.append(warn('Reverse proxies must be told to allow WebSockets. That is why our '
                      '<font face="Courier">web.config</font> includes '
                      '<font face="Courier">&lt;webSocket enabled="true" /&gt;</font> and our IIS script '
                      'enables the WebSocket feature — otherwise live quizzes would silently fail.'))

    # ═══════════ CHAPTER 16 ═══════════
    ch(story, 16, 'How our database works', 'storing and retrieving data both ways')
    P(story, 'A <b>database</b> is where the app’s information lives permanently. Ours can use one of '
             'two stores, and the code automatically picks whichever is available:')
    H3(story, '1. db.json — a flat file')
    P(story, 'A single human-readable JSON file (<font face="Courier">data/db.json</font>) holding all '
             'collections: members, events, points, quizzes, surveys and the knowledge board. Perfect '
             'for a small internal app and easy to back up (just copy the file).')
    H3(story, '2. MongoDB Atlas — a cloud database')
    P(story, 'When an environment variable <font face="Courier">MONGODB_URI</font> is set (as on '
             'Render), the same code stores data in MongoDB instead, so data survives redeploys.')
    story.append(dia_database())
    cap(story, 'Write with POST, read with GET; data rests in MongoDB if configured, else in db.json.')
    H2(story, 'Reading and writing — both directions')
    story.append(make_table(
        ['Action', 'HTTP verb', 'Example', 'What happens'],
        [
            ['Read data', 'GET', '/api/leaderboard?side=engsys', 'Backend reads the store, returns JSON'],
            ['Create data', 'POST', '/api/quizzes', 'Backend adds a record, saves the store'],
            ['Update data', 'PUT', '/api/events/:id', 'Backend merges changes into a record'],
            ['Delete data', 'DELETE', '/api/knowledge/:id', 'Backend removes a record'],
        ],
        [CONTENT_W*0.17, CONTENT_W*0.13, CONTENT_W*0.34, CONTENT_W*0.36], code_cols=[2]))
    sp(story, 6)
    story.append(info('Two helper functions do all storage: <font face="Courier">readDB()</font> and '
                      '<font face="Courier">writeDB()</font> (Node) — mirrored as '
                      '<font face="Courier">read_db()</font>/<font face="Courier">write_db()</font> in '
                      'Python. Every route calls these, so switching stores needs no other code changes.'))
    story.append(analogy('Think of db.json as a well-organised paper ledger in a drawer, and MongoDB '
                         'as a cloud spreadsheet. The app is trained to write to whichever one is '
                         'present — the rest of the code never notices the difference.'))

    # ═══════════ CHAPTER 17 ═══════════
    ch(story, 17, 'CI/CD & our GitLab redirect', 'from “git push” to “live”, automatically')
    H2(story, 'What is CI/CD?')
    P(story, '<b>CI/CD</b> stands for Continuous Integration / Continuous Delivery. In plain terms: '
             'every time you save your code to the shared repository, an automated assistant '
             '<b>checks it and can deploy it</b> — no manual copying of files.')
    story.append(dia_cicd())
    cap(story, 'You push code; the pipeline validates it; the app deploys; the redirect page points to it.')
    H2(story, 'What is a pipeline?')
    P(story, 'A <b>pipeline</b> is the recipe of automatic steps (defined in '
             '<font face="Courier">.gitlab-ci.yml</font>) that run on every push — for example '
             '“check the Node code, check the Python code, publish the redirect page.”')
    H2(story, 'How the GitLab URL redirects to our server')
    P(story, 'GitLab Pages can only host <b>static</b> pages, not our live app. So we host a tiny '
             'one-page site on GitLab Pages whose only job is to <b>auto-forward</b> visitors to the '
             'real server. The shareable GitLab link therefore acts as a friendly doorway to the app.')
    story.append(StepBox(1, 'You push code', 'git push sends commits to GitHub (Render) and GitLab (Siemens).'))
    sp(story, 4)
    story.append(StepBox(2, 'The pipeline runs', 'GitLab validates the code and builds the static redirect page as an artifact.'))
    sp(story, 4)
    story.append(StepBox(3, 'Pages publishes', 'GitLab serves the redirect page at a stable code.siemens.io link.'))
    sp(story, 4)
    story.append(StepBox(4, 'Visitor is forwarded', 'Opening the link instantly redirects the browser to the live EMBRACE AI server.'))
    sp(story, 6)
    story.append(info('We also reduced pipeline “failure” emails by simplifying the checks and only '
                      'running them on the main branch — noise down, signal up.'))

    # ═══════════ CHAPTER 18 ═══════════
    ch(story, 18, 'Docker, Fargate & SDC', 'the Siemens-cloud action plan')
    H2(story, 'What is Docker?')
    P(story, '<b>Docker</b> packages your app together with everything it needs to run (the right '
             'Node version, libraries, files) into a single sealed box called a <b>container</b>. That '
             'container then runs identically on any machine — your laptop, a server, or the cloud.')
    story.append(analogy('Docker is like a shipping container. Whatever you pack inside travels intact '
                         'and fits any ship, train or truck. “It works on my machine” becomes “it works '
                         'everywhere”, because the machine is packed inside the box.'))
    H2(story, 'What is AWS Fargate?')
    P(story, '<b>AWS Fargate</b> is a cloud service that runs Docker containers for you without you '
             'managing any servers. You hand it your container; it runs and scales it.')
    H2(story, 'What is the Siemens SDC?')
    P(story, 'The <b>Siemens Data &amp; AI Cloud (SDC) Project</b> is an internal, self-service '
             'platform that can run containerised apps (via Fargate) and deploy them straight from our '
             'GitLab — with Siemens-level security and compliance built in. It is the most promising '
             '<b>internal</b> permanent home for EMBRACE AI.')
    H2(story, 'What changes if we move to SDC?')
    story.append(make_table(
        ['Topic', 'Server approach (SN1W7220)', 'SDC + Fargate approach'],
        [
            ['Packaging', 'Run Node directly via NSSM', 'Wrap app in a Docker container'],
            ['Where it runs', 'On the Windows server', 'On managed cloud (AWS via SDC)'],
            ['Scaling', 'One machine', 'Scales automatically'],
            ['Data store', 'db.json on the server', 'MongoDB / cloud store (already supported)'],
            ['Deployment', 'Run a .bat script', 'Connect GitLab on the SDC Canvas, click Deploy'],
            ['IIS involved?', 'Optionally, as proxy', 'Not at all'],
        ],
        [CONTENT_W*0.20, CONTENT_W*0.40, CONTENT_W*0.40]))
    sp(story, 6)
    story.append(tip('Good news: because our code already supports MongoDB and reads its port from an '
                     'environment variable, it is <b>almost</b> container-ready. Moving to SDC mainly '
                     'means adding a small Dockerfile — no rewrite.'))
    story.append(warn('SDC provisions real cloud accounts that bill to a cost centre, and needs a '
                      'Cyber Security Officer and Financial Controller named. Confirm approval and '
                      'cost with your manager before choosing it as the permanent host.'))

    # ═══════════ CHAPTER 19 ═══════════
    ch(story, 19, 'Our two scripts, explained', 'exactly what each .bat does, step by step')
    H2(story, 'host-with-iis.bat (Option A)')
    P(story, 'Sets up EMBRACE AI behind IIS as a reverse proxy, without touching any existing site.')
    for n, (t, d) in enumerate([
        ('Checks admin + prerequisites', 'Confirms it runs as Administrator and that server.js and NSSM exist.'),
        ('Enables IIS WebSocket feature', 'So live quizzes work through the proxy (safe, idempotent).'),
        ('Verifies ARR + URL Rewrite', 'Warns you if either add-on is missing.'),
        ('Enables ARR proxy', 'Turns on server-level reverse-proxying.'),
        ('Points Node to 127.0.0.1:3000', 'The app listens privately; only IIS reaches it.'),
        ('Creates a dedicated IIS site', 'A NEW site on its own port — existing sites untouched.'),
        ('Opens firewall + verifies', 'Allows the public port and tests the API responds.'),
    ], 1):
        story.append(StepBox(n, t, d)); sp(story, 3)
    sp(story, 4)
    H2(story, 'host-without-iis.bat (Option B)')
    P(story, 'Runs EMBRACE AI directly on its own dedicated port — IIS keeps running as-is.')
    for n, (t, d) in enumerate([
        ('Checks admin + prerequisites', 'Same safety checks as Option A.'),
        ('Confirms the port is free', 'Uses netstat to ensure the chosen port is not busy.'),
        ('Sets Node to the public port', 'Configures the service’s PORT environment variable.'),
        ('Ensures auto-restart', 'Service auto-starts on boot and restarts on failure.'),
        ('Starts service + opens firewall', 'Brings the app up and allows the port.'),
        ('Verifies', 'Tests that the API answers on the chosen port.'),
    ], 1):
        story.append(StepBox(n, t, d)); sp(story, 3)
    sp(story, 4)
    story.append(info('Both scripts are deliberately <b>non-destructive</b>: they never stop or '
                      'disable IIS/W3SVC/WAS, and never modify the Default Web Site or any other site. '
                      'Teamcenter and colleagues’ apps keep running throughout.'))

    # ═══════════ CHAPTER 20 ═══════════
    ch(story, 20, 'Choosing the right host', 'a simple decision guide')
    story.append(dia_options())
    cap(story, 'Four realistic options — each fits a different situation.')
    story.append(make_table(
        ['If you want…', 'Best choice', 'Why'],
        [
            ['A quick shared link to review now', 'Render', 'Already live, auto-deploys, zero effort'],
            ['A permanent internal Siemens home', 'SDC + Fargate', 'Compliant, scalable, deploys from GitLab'],
            ['To reuse the existing server safely', 'SN1W7220 + IIS proxy', 'No new infra, IIS/Teamcenter untouched'],
            ['A no-frills direct option on the server', 'SN1W7220 direct port', 'Simplest; app on its own port'],
            ['A momentary demo only', 'Your PC', 'Fine short-term; only up when you are online'],
        ],
        [CONTENT_W*0.34, CONTENT_W*0.24, CONTENT_W*0.42]))
    sp(story, 8)
    story.append(tip('Our recommendation: keep <b>Render</b> for review today; pursue <b>SDC</b> for '
                     'the permanent home (pending manager approval); and keep the <b>IIS reverse-proxy '
                     'on SN1W7220</b> ready as a no-disruption fallback — which is exactly why both '
                     '.bat files now live in the repository.'))

    # ═══════════ APPENDIX A — GLOSSARY ═══════════
    ch(story, 'A', 'Glossary', 'every term, in one place')
    glossary = [
        ('API (Application Programming Interface)', 'A set of URLs the frontend calls to get or change data (e.g. /api/members).'),
        ('ARR (Application Request Routing)', 'An IIS add-on that lets IIS forward requests to another server (reverse proxy).'),
        ('Backend', 'The server-side part of the app that holds data and rules (server.js / app.py).'),
        ('Batch file (.bat)', 'A Windows script of commands run top-to-bottom when executed.'),
        ('CI/CD', 'Automated checking and deployment of code whenever you push to the repository.'),
        ('Client', 'The computer/program making a request — usually your browser.'),
        ('Container', 'A sealed box (via Docker) holding the app plus everything it needs to run.'),
        ('CSS', 'The language that styles the page — colours, layout, themes.'),
        ('Database', 'Where data lives permanently (db.json or MongoDB here).'),
        ('DNS (Domain Name System)', 'The service that turns a name into an IP address.'),
        ('Docker', 'A tool that packages an app into a portable container.'),
        ('Fargate (AWS)', 'A cloud service that runs Docker containers without managing servers.'),
        ('Frontend', 'The part of the app that runs in the browser (HTML/CSS/JS).'),
        ('HTML', 'The language that defines page structure and content.'),
        ('HTTP / HTTPS', 'The rules browsers and servers use to talk; HTTPS is the encrypted version.'),
        ('IIS (Internet Information Services)', 'Microsoft’s built-in web server for Windows.'),
        ('IP address', 'A computer’s numeric address on a network.'),
        ('JavaScript', 'The language for behaviour — in the browser and (via Node) on the server.'),
        ('JSON', 'A simple text format for data as key–value pairs.'),
        ('localhost', 'A name meaning “this same computer” (address 127.0.0.1).'),
        ('MongoDB', 'A cloud database we optionally use instead of db.json.'),
        ('Node.js', 'Software that runs JavaScript on a server.'),
        ('NSSM', 'A tool that runs a program as an auto-restarting Windows service.'),
        ('Port', 'A numbered “door” on a computer so requests reach the right program.'),
        ('Proxy', 'A middle-man that relays requests between two parties.'),
        ('Reverse proxy', 'A proxy in front of your app that forwards visitor requests to it.'),
        ('Route', 'A path (like /api/quizzes) mapped to a function in the backend.'),
        ('Routing', 'Directing a request to the right destination (network or code level).'),
        ('SDC', 'Siemens Data &amp; AI Cloud — internal platform to host containerised apps.'),
        ('Server', 'An always-on computer (or program) that serves data to clients.'),
        ('Service (Windows)', 'A background program that starts with the machine.'),
        ('Socket.IO', 'A library that provides real-time WebSocket communication.'),
        ('URL Rewrite', 'An IIS add-on that rewrites/redirects incoming web addresses.'),
        ('WebSocket', 'A persistent two-way connection for instant real-time updates.'),
        ('YAML / web.config', 'Configuration formats (YAML for CI/Render; XML web.config for IIS).'),
    ]
    for term, dfn in glossary:
        story.append(Paragraph(term, S['gterm']))
        story.append(Paragraph(dfn, S['gdef']))

    # ═══════════ APPENDIX B — RUNBOOK ═══════════
    ch(story, 'B', 'Quick runbook', 'the commands you will actually use')
    H2(story, 'On the server (SN1W7220), as Administrator')
    story.append(CodeBlock(':: Option A — host behind IIS (reverse proxy)\n'
                           'cd C:\\apps\\embrace-ai\\deploy\\windows\n'
                           'host-with-iis.bat\n\n'
                           ':: Option B — host directly on a dedicated port\n'
                           'host-without-iis.bat', 'batch'))
    H2(story, 'Update the app to the latest code')
    story.append(CodeBlock('cd C:\\apps\\embrace-ai\n'
                           'git pull\n'
                           'npm install\n'
                           'nssm restart EmbraceAI', 'batch'))
    H2(story, 'Check health')
    story.append(CodeBlock('nssm status EmbraceAI\n'
                           'curl http://localhost:8080/api/members\n'
                           'netstat -ano | findstr LISTENING', 'batch'))
    H2(story, 'If something looks down')
    bullets(story, [
        'Off VPN? DNS may resolve the server name wrong — connect to VPN and retry.',
        'Port busy? Pick a free port in the .bat file and re-run.',
        'App crashed? NSSM auto-restarts it; check logs in <font face="Courier">C:\\apps\\embrace-ai\\logs</font>.',
        'Seeing an IIS 404? A site/binding is misconfigured — re-run the chosen .bat script.',
    ])
    sp(story, 10)
    story.append(HRFlowable(width='100%', thickness=2, color=PETROL, spaceAfter=10))
    story.append(Paragraph('You made it — you now understand, end to end, how this app is built, '
                           'hosted and delivered. Keep this handbook by your side; every term you meet '
                           'in the deployment world is defined in here.',
                           ParagraphStyle('end', fontName='Helvetica-Oblique', fontSize=11,
                                          textColor=PETROL, alignment=TA_CENTER, leading=16)))

    return story


# ═══════════════════════════════════════════════════════════════
# DOCUMENT ASSEMBLY
# ═══════════════════════════════════════════════════════════════
def build():
    doc = BaseDocTemplate(
        OUTPUT_PATH, pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN + 6, bottomMargin=MARGIN + 6,
        title='EMBRACE AI — Hosting & Architecture Handbook',
        author='Siemens Engineering Systems')

    frame = Frame(MARGIN, MARGIN + 4, CONTENT_W, PAGE_H - 2*MARGIN - 10, id='main')
    cover_frame = Frame(MARGIN, MARGIN, CONTENT_W, PAGE_H - 2*MARGIN, id='cover')

    doc.addPageTemplates([
        PageTemplate(id='cover', frames=[cover_frame], onPage=cover),
        PageTemplate(id='content', frames=[frame], onPage=decorate),
    ])

    story = build_story()
    # After the cover (first flowables until first PageBreak), switch templates.
    # Insert a NextPageTemplate switch right after the cover block.
    from reportlab.platypus import NextPageTemplate
    # Find first PageBreak (end of cover) and inject template switch before it.
    for i, fl in enumerate(story):
        if isinstance(fl, PageBreak):
            story.insert(i, NextPageTemplate('content'))
            break

    doc.build(story)
    print(f'✅ Handbook generated: {OUTPUT_PATH}')


if __name__ == '__main__':
    build()
