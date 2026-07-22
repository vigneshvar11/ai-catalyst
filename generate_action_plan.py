"""
Generate AI CatalyESt 6-Month Action Plan PDF
Brief reference document — not part of the web app.
"""

import os, json
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

# ── Paths ──────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(BASE_DIR, 'data', 'db.json')
OUT_PATH = os.path.join(BASE_DIR, 'AI_CatalyESt_Action_Plan.pdf')

# ── Colours (Siemens-themed) ──────────────────────────────────────────
PETROL     = colors.HexColor('#009999')
DARK_NAVY  = colors.HexColor('#000028')
LIGHT_BG   = colors.HexColor('#F5F7FA')
SPARK_CLR  = colors.HexColor('#FF6B6B')
BUILD_CLR  = colors.HexColor('#FFB300')
APPLY_CLR  = colors.HexColor('#7C4DFF')
DELIVER_CLR= colors.HexColor('#00BCD4')

PHASE_COLORS = {
    'SPARK': SPARK_CLR,
    'BUILD': BUILD_CLR,
    'APPLY': APPLY_CLR,
    'DELIVER': DELIVER_CLR,
}

MONTH_NAMES = [
    '', 'April 2026', 'May 2026', 'June 2026',
    'July 2026', 'August 2026', 'September 2026',
    'October 2026', 'November 2026', 'December 2026',
    'January 2027', 'February 2027', 'March 2027',
]

# ── Load data ─────────────────────────────────────────────────────────
with open(DB_PATH, 'r', encoding='utf-8') as f:
    db = json.load(f)

members = db.get('members', [])
events  = db.get('events', [])
config  = db.get('config', {})

# ── Styles ────────────────────────────────────────────────────────────
def build_styles():
    ss = getSampleStyleSheet()
    S = {}
    S['title'] = ParagraphStyle('Title', parent=ss['Title'],
        fontSize=26, leading=32, textColor=DARK_NAVY,
        fontName='Helvetica-Bold', alignment=TA_CENTER, spaceAfter=4)
    S['subtitle'] = ParagraphStyle('Subtitle', parent=ss['Normal'],
        fontSize=13, leading=18, textColor=PETROL,
        fontName='Helvetica', alignment=TA_CENTER, spaceAfter=20)
    S['h1'] = ParagraphStyle('H1', parent=ss['Heading1'],
        fontSize=18, leading=24, textColor=DARK_NAVY,
        fontName='Helvetica-Bold', spaceBefore=16, spaceAfter=8)
    S['h2'] = ParagraphStyle('H2', parent=ss['Heading2'],
        fontSize=14, leading=18, textColor=PETROL,
        fontName='Helvetica-Bold', spaceBefore=12, spaceAfter=6)
    S['body'] = ParagraphStyle('Body', parent=ss['Normal'],
        fontSize=10, leading=14, textColor=colors.HexColor('#333'),
        fontName='Helvetica', spaceAfter=6)
    S['bullet'] = ParagraphStyle('Bullet', parent=S['body'],
        leftIndent=16, bulletIndent=6, spaceBefore=2, spaceAfter=2)
    S['small'] = ParagraphStyle('Small', parent=ss['Normal'],
        fontSize=8, leading=11, textColor=colors.HexColor('#888'),
        fontName='Helvetica')
    S['footer'] = ParagraphStyle('Footer', parent=ss['Normal'],
        fontSize=8, textColor=colors.HexColor('#aaa'),
        fontName='Helvetica', alignment=TA_CENTER)
    return S


def build_pdf():
    S = build_styles()
    story = []

    # ── Title ──────────────────────────────────────────────────────
    story.append(Spacer(1, 30))
    story.append(Paragraph('AI CatalyESt', S['title']))
    story.append(Paragraph('6-Month Action Plan  •  May – October 2026', S['subtitle']))
    story.append(HRFlowable(width='80%', thickness=2, color=PETROL,
                            spaceAfter=12, spaceBefore=4))

    # Meta info
    story.append(Paragraph(
        f'<b>Team:</b> {config.get("teamName", "Engineering Systems")}  |  '
        f'<b>Company:</b> {config.get("company", "Siemens")}  |  '
        f'<b>Generated:</b> {datetime.now().strftime("%d %B %Y")}', S['small']))
    story.append(Spacer(1, 16))

    # ── Executive Summary ──────────────────────────────────────────
    story.append(Paragraph('Executive Summary', S['h1']))
    story.append(Paragraph(
        'AI CatalyESt (where <b>ES</b> = Engineering Systems) is a 12-month initiative '
        'at Siemens to upskill our team of <b>16 members</b> across <b>5 domains</b> '
        'in Artificial Intelligence — from awareness to real-world application. '
        'This document outlines the action plan for the next 6 months '
        '(May – October 2026), covering phases <b>SPARK</b>, <b>BUILD</b>, '
        'and <b>APPLY</b>.', S['body']))
    story.append(Spacer(1, 6))

    # Domains summary
    domains = {}
    for m in members:
        d = m.get('domain', 'Unknown')
        domains[d] = domains.get(d, 0) + 1
    domain_str = ', '.join(f'{d} ({c})' for d, c in sorted(domains.items()))
    story.append(Paragraph(
        f'<b>Domains represented:</b> {domain_str}', S['body']))
    story.append(Spacer(1, 12))

    # ── Phase Overview ─────────────────────────────────────────────
    story.append(Paragraph('Phase Overview', S['h1']))
    phase_data = [
        ['Phase', 'Months', 'Focus', 'Goal'],
        ['SPARK', 'Apr – May 2026', 'Awareness & Curiosity',
         'Introduce AI, build excitement, prompt basics'],
        ['BUILD', 'Jun – Jul 2026', 'Skill Development',
         'Hands-on prompt engineering, tool mastery'],
        ['APPLY', 'Aug – Sep 2026', 'Real Projects',
         'Apply AI to actual Siemens work, use cases'],
        ['DELIVER', 'Oct 2026 – Mar 2027', 'Showcase & Impact',
         'Present results, measure ROI, celebrate wins'],
    ]
    pt = Table(phase_data, colWidths=[65, 100, 130, 175])
    pt.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), DARK_NAVY),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E0E0E0')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_BG]),
        ('TEXTCOLOR', (0, 1), (0, 1), SPARK_CLR),
        ('TEXTCOLOR', (0, 2), (0, 2), BUILD_CLR),
        ('TEXTCOLOR', (0, 3), (0, 3), APPLY_CLR),
        ('TEXTCOLOR', (0, 4), (0, 4), DELIVER_CLR),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
    ]))
    story.append(pt)
    story.append(Spacer(1, 16))

    # ── Monthly Roadmap ────────────────────────────────────────────
    story.append(Paragraph('Monthly Roadmap', S['h1']))

    for ev in sorted(events, key=lambda e: e.get('month', 0)):
        month_num = ev.get('month', 0)
        phase = ev.get('phase', '')
        title = ev.get('title', 'TBD')
        desc = ev.get('description', '')
        date_str = ev.get('date', '')
        time_str = ev.get('time', '')
        duration = ev.get('duration', 60)
        activity = ev.get('activityType', '')
        status = ev.get('status', 'upcoming')
        presenter_id = ev.get('seminarPresenter')
        seminar = ev.get('seminarTopic', '')
        skills = ev.get('skills', '')
        comments = ev.get('comments', '')

        # Presenter name lookup
        presenter_name = ''
        if presenter_id:
            for m in members:
                if m.get('id') == presenter_id:
                    presenter_name = m.get('name', '')
                    break

        # Status badge
        status_label = '✅ Completed' if status == 'completed' else '🔜 Upcoming'
        phase_clr = PHASE_COLORS.get(phase, PETROL)

        month_label = MONTH_NAMES[month_num] if 0 < month_num < len(MONTH_NAMES) else f'Month {month_num}'

        # Month header
        story.append(Paragraph(
            f'<font color="{phase_clr.hexval()}">[{phase}]</font>  '
            f'Month {month_num} — {month_label}', S['h2']))

        # Event details table
        rows = [
            ['Event', title],
            ['Status', status_label],
            ['Date / Time', f'{date_str}  {time_str}' if date_str else 'TBD'],
            ['Duration', f'{duration} minutes'],
            ['Activity Type', activity if activity else '—'],
        ]
        if presenter_name:
            rows.append(['Presenter', presenter_name])
        if seminar:
            rows.append(['Seminar Topic', seminar])
        if skills:
            rows.append(['Skills Covered', skills])
        if desc:
            rows.append(['Description', desc])
        if comments:
            rows.append(['Notes', comments])

        t = Table(rows, colWidths=[100, 370])
        t.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TEXTCOLOR', (0, 0), (0, -1), PETROL),
            ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#333')),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#E5E5EA')),
            ('BACKGROUND', (0, 0), (0, -1), LIGHT_BG),
        ]))
        story.append(t)
        story.append(Spacer(1, 12))

    # ── Team Roster ────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph('Team Roster', S['h1']))
    story.append(Paragraph(
        f'{len(members)} members across {len(domains)} domains:', S['body']))

    roster_header = ['#', 'Name', 'Domain', 'Role']
    roster_rows = [roster_header]
    for i, m in enumerate(sorted(members, key=lambda x: x.get('name', '')), 1):
        roster_rows.append([
            str(i),
            m.get('name', ''),
            m.get('domain', ''),
            m.get('role', '') or '—',
        ])

    rt = Table(roster_rows, colWidths=[30, 180, 130, 130])
    rt.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PETROL),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
        ('TOPPADDING', (0, 0), (-1, -1), 7),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E0E0E0')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_BG]),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
    ]))
    story.append(rt)
    story.append(Spacer(1, 16))

    # ── Key Milestones ─────────────────────────────────────────────
    story.append(Paragraph('Key Milestones & Success Metrics', S['h1']))
    milestones = [
        'Month 1 (Apr): Kickoff complete — all 16 members onboarded ✅',
        'Month 2 (May): Knowledge Sharing Session — GenAI awareness established',
        'Month 3 (Jun): Prompt Battle Arena — hands-on prompt engineering skills',
        'Month 4 (Jul): BUILD phase activity — deeper tool mastery',
        'Month 5 (Aug): APPLY phase begins — real Siemens use cases',
        'Month 6 (Mar 2027): Grand Finale — showcase to leadership',
    ]
    for ms in milestones:
        story.append(Paragraph(f'• {ms}', S['bullet']))
    story.append(Spacer(1, 12))

    story.append(Paragraph('Success Metrics', S['h2']))
    metrics = [
        '100% participation rate across all 16 members',
        'Each member completes at least 1 AI use case by Month 5',
        'Leaderboard engagement — points tracked monthly',
        'Survey satisfaction score ≥ 4.0 / 5.0 per session',
        'At least 3 use cases presented to leadership at Grand Finale',
    ]
    for mt in metrics:
        story.append(Paragraph(f'• {mt}', S['bullet']))
    story.append(Spacer(1, 20))

    # ── Footer ─────────────────────────────────────────────────────
    story.append(HRFlowable(width='60%', thickness=1, color=colors.HexColor('#ccc'),
                            spaceAfter=6, spaceBefore=10))
    story.append(Paragraph(
        'AI CatalyESt  •  Engineering Systems  •  Siemens  •  '
        f'Generated {datetime.now().strftime("%d %b %Y")}  •  For internal reference only',
        S['footer']))

    # ── Build PDF ──────────────────────────────────────────────────
    doc = SimpleDocTemplate(
        OUT_PATH,
        pagesize=A4,
        topMargin=20*mm,
        bottomMargin=15*mm,
        leftMargin=18*mm,
        rightMargin=18*mm,
        title='AI CatalyESt — 6-Month Action Plan',
        author='Vigneshvar SA',
    )
    doc.build(story)
    print(f'\n✅ Action Plan PDF generated successfully!')
    print(f'   📄 {OUT_PATH}')
    size_kb = os.path.getsize(OUT_PATH) / 1024
    print(f'   📦 Size: {size_kb:.0f} KB')


if __name__ == '__main__':
    print('🚀 Generating AI CatalyESt 6-Month Action Plan...')
    build_pdf()
