#!/usr/bin/env python3
"""
EMBRACE AI — IIS Hosting & Safety Guide (short companion PDF)
============================================================
Reuses the design toolkit from generate_hosting_handbook.py so it matches
the handbook's Siemens/glassmorphism theme exactly.

Run:  python generate_iis_safety_guide.py
Out:  EMBRACE_AI_IIS_Hosting_Guide.pdf
"""

import os
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, PageBreak,
    HRFlowable, NextPageTemplate,
)

# Reuse the shared design toolkit from the handbook generator
import generate_hosting_handbook as HB
from generate_hosting_handbook import (
    S, PETROL, PETROL_LIGHT, DARK_NAVY, GREEN, GREEN_SOFT, AMBER, AMBER_SOFT,
    INFO, INFO_SOFT, VIOLET, LIGHT_BG, BORDER, GREY, CONTENT_W, MARGIN,
    PAGE_W, PAGE_H, ChapterHeader, CodeBlock, StepBox, make_table,
    tip, warn, info, analogy, decorate, cover, SetChapter,
)

OUTPUT_PATH = os.path.join(HB.BASE_DIR, 'EMBRACE_AI_IIS_Hosting_Guide.pdf')


def P(story, t):  story.append(Paragraph(t, S['body']))
def H2(story, t): story.append(Paragraph(t, S['h2']))
def H3(story, t): story.append(Paragraph(t, S['h3']))
def sp(story, h=8): story.append(Spacer(1, h))
def cap(story, t): story.append(Paragraph(t, S['caption']))
def bullets(story, items):
    for it in items:
        story.append(Paragraph(f'<font color="#009999">●</font>  {it}', S['bullet']))
def ch(story, number, title, subtitle=''):
    story.append(PageBreak())
    story.append(SetChapter(title))
    story.append(ChapterHeader(number, title, subtitle))
    story.append(Spacer(1, 14))


def build_story():
    story = []

    # ── COVER ──
    story.append(Spacer(1, 175))
    story.append(Paragraph('Hosting on IIS', S['title']))
    story.append(Paragraph('&amp; Proving It Is Safe', S['title']))
    sp(story, 10)
    story.append(Paragraph('Which files you need, where they go, what each script does — and how to '
                           'confidently show you did not disturb Teamcenter', S['subtitle']))
    sp(story, 70)
    story.append(Paragraph('A companion to the EMBRACE AI Hosting &amp; Architecture Handbook',
                           ParagraphStyle('cvr', fontName='Helvetica', fontSize=11,
                                          textColor=colors.white, alignment=TA_CENTER, leading=17)))
    sp(story, 80)
    story.append(Paragraph('SIEMENS · Engineering Systems · AI CatalyESt',
                           ParagraphStyle('cf', fontName='Helvetica-Bold', fontSize=12,
                                          textColor=PETROL_LIGHT, alignment=TA_CENTER)))
    story.append(Paragraph(datetime.now().strftime('Edition · %B %Y'),
                           ParagraphStyle('cd', fontName='Helvetica', fontSize=9.5,
                                          textColor=colors.HexColor('#8892b0'), alignment=TA_CENTER)))

    # ═══ CHAPTER 1 — files & placement ═══
    ch(story, 1, 'The files you need', 'and exactly where each one goes')
    P(story, 'Hosting this app on IIS is <b>not</b> like hosting a plain static website, where IIS '
             'serves <font face="Courier">.html</font> files directly. Our app is a live <b>Node.js '
             'program</b>, so IIS never runs the app — it only <b>forwards</b> requests to Node. That '
             'means two separate locations matter on the server.')
    story.append(analogy('IIS here is like a hotel reception desk, and Node.js is the chef in the '
                         'kitchen. Reception (IIS) does not cook — it just takes your order to the '
                         'kitchen (Node) and brings the food back. Two different rooms, two different jobs.'))

    H2(story, 'A) The application files  →  C:\\apps\\embrace-ai')
    P(story, 'This is the whole Git repository — the actual app that Node runs. The important formats:')
    story.append(make_table(
        ['File / folder', 'Format', 'Why it is needed'],
        [
            ['server.js', '.js (JavaScript)', 'The Node.js backend that runs the app'],
            ['package.json', '.json', 'Lists the Node libraries to install'],
            ['node_modules/', 'folder', 'The installed libraries (from npm install)'],
            ['public/', 'folder (.html/.css/.js)', 'The frontend the browser sees'],
            ['data/db.json', '.json', 'The database file'],
            ['deploy/', 'folder (.bat/.ps1/.config)', 'Setup scripts + the IIS config'],
        ],
        [CONTENT_W*0.26, CONTENT_W*0.26, CONTENT_W*0.48], code_cols=[0]))
    sp(story, 6)
    P(story, 'You put these on the server by cloning the repo there:')
    story.append(CodeBlock('cd C:\\apps\\embrace-ai\n'
                           'git clone https://code.siemens.com/engsys/ai_catalyest.git .\n'
                           'npm install', 'batch'))

    H2(story, 'B) The IIS site folder  →  C:\\inetpub\\embrace-ai')
    P(story, 'IIS needs its <b>own</b> small folder containing <b>one</b> file: '
             '<font face="Courier">web.config</font>. This is the only file IIS itself reads.')
    story.append(make_table(
        ['File', 'Format', 'What it does'],
        [
            ['web.config', '.config (XML)', 'Tells IIS: enable WebSockets, and forward every request to http://localhost:3000'],
        ],
        [CONTENT_W*0.22, CONTENT_W*0.20, CONTENT_W*0.58], code_cols=[0]))
    sp(story, 6)
    story.append(info('Your repo already ships this file at '
                      '<font face="Courier">deploy/iis/web.config</font>. The '
                      '<font face="Courier">host-with-iis.bat</font> script copies it into '
                      '<font face="Courier">C:\\inetpub\\embrace-ai\\web.config</font> for you — you '
                      'do not place it by hand.'))

    # ═══ CHAPTER 2 — how the process works ═══
    ch(story, 2, 'How the IIS process works', 'the journey of one request')
    P(story, 'Once set up, here is what happens each time someone opens the app:')
    story.append(StepBox(1, 'Browser makes a request', 'A colleague opens http://SN1W7220:8080 in their browser.'))
    sp(story, 4)
    story.append(StepBox(2, 'IIS receives it', 'The request lands on the new "EmbraceAI" IIS site, listening on the dedicated port 8080.'))
    sp(story, 4)
    story.append(StepBox(3, 'web.config rewrites it', 'The rewrite rule says: forward this request to http://localhost:3000.'))
    sp(story, 4)
    story.append(StepBox(4, 'ARR forwards to Node', 'The Application Request Routing module actually passes the request to Node.'))
    sp(story, 4)
    story.append(StepBox(5, 'Node runs the app', 'server.js (on 127.0.0.1:3000) processes it and reads/writes db.json.'))
    sp(story, 4)
    story.append(StepBox(6, 'The answer returns', 'Node replies to IIS, and IIS sends it back to the browser.'))
    sp(story, 8)
    P(story, 'In short: <b>Node files live in C:\\apps\\embrace-ai and run as a background service; '
             'IIS files live in C:\\inetpub\\embrace-ai (just web.config), and IIS is a forwarding '
             'front door.</b> The script wires the two together.')
    H3(story, 'Prerequisites IIS needs (installed once)')
    bullets(story, [
        'IIS with the <b>WebSocket Protocol</b> feature',
        '<b>URL Rewrite</b> module',
        '<b>Application Request Routing (ARR)</b> module',
    ])
    story.append(tip('The <font face="Courier">host-with-iis.bat</font> script checks for URL Rewrite '
                     'and ARR and clearly warns you if either is missing, so you are never left guessing.'))

    # ═══ CHAPTER 3 — what each .bat does ═══
    ch(story, 3, 'What each script does', 'host-with-iis vs host-without-iis')
    H2(story, 'host-with-iis.bat  (behind IIS)')
    for n, (t, d) in enumerate([
        ('Checks admin + prerequisites', 'Confirms Administrator rights and that the app and NSSM exist.'),
        ('Enables IIS WebSocket feature', 'So live quizzes work through the proxy (safe, repeatable).'),
        ('Checks ARR + URL Rewrite', 'Warns you only — does not force anything.'),
        ('Turns on ARR proxy', 'Enables server-level reverse proxying.'),
        ('Sets Node to 127.0.0.1:3000', 'The app listens privately; only IIS can reach it.'),
        ('Creates a NEW IIS site', 'A separate "EmbraceAI" site on dedicated port 8080.'),
        ('Opens firewall + verifies', 'Allows the port and tests that the app answers.'),
    ], 1):
        story.append(StepBox(n, t, d)); sp(story, 3)
    sp(story, 6)
    H2(story, 'host-without-iis.bat  (direct Node)')
    for n, (t, d) in enumerate([
        ('Checks admin + prerequisites', 'Same safety checks.'),
        ('Confirms the port is free', 'Uses netstat to ensure port 8080 is not already busy.'),
        ('Sets Node to the public port', 'Node answers the browser directly on 8080.'),
        ('Ensures auto-restart', 'Service auto-starts on boot and restarts on failure.'),
        ('Starts service + firewall', 'Brings the app up and allows the port.'),
        ('Verifies', 'Tests that the API answers. IIS is not touched at all.'),
    ], 1):
        story.append(StepBox(n, t, d)); sp(story, 3)

    # ═══ CHAPTER 4 — proving you didn't break IIS ═══
    ch(story, 4, 'Proving you did not break IIS', 'five facts you can stand behind')
    P(story, 'If a teammate says <i>"IIS on 7220 doesn’t seem to work — did you do something?"</i>, '
             'here is what you can calmly and truthfully say. Each point is true <b>by design</b> of '
             'these scripts.')
    story.append(info('1. "I never stopped, disabled, or reset IIS." The two new scripts contain no '
                      'iisreset, no Stop-Service W3SVC, and no disabling of IIS services. They only '
                      'ADD things.', title='Fact 1 — no IIS shutdown'))
    sp(story, 5)
    story.append(info('2. "I never touched any existing site or the Default Web Site." The script only '
                      'runs appcmd add site for a brand-new "EmbraceAI" site. It never edits, stops, or '
                      'deletes Teamcenter’s site or any binding they use.', title='Fact 2 — existing sites untouched'))
    sp(story, 5)
    story.append(info('3. "I used a separate, dedicated port." Teamcenter uses port 80; EmbraceAI uses '
                      '8080 (and Node privately on 3000). Different ports cannot conflict — and the '
                      'direct script even checks the port is free first.', title='Fact 3 — no port conflict'))
    sp(story, 5)
    story.append(info('4. "Everything is reversible in seconds." Removing our footprint entirely has '
                      'zero effect on anything else (commands below).', title='Fact 4 — fully reversible'))
    sp(story, 5)
    story.append(info('5. "It is all in Git — fully auditable." Anyone can read '
                      'deploy/windows/host-with-iis.bat and confirm there is no destructive command.',
                      title='Fact 5 — auditable'))

    H2(story, 'The complete removal (reversal) commands')
    story.append(CodeBlock('appcmd delete site "EmbraceAI"\n'
                           'nssm stop EmbraceAI\n'
                           'netsh advfirewall firewall delete rule name="EmbraceAI HTTP 8080"',
                           'batch'))
    cap(story, 'Deletes only our site, stops only our service, removes only our firewall rule. Teamcenter is untouched.')

    H2(story, 'How to actually diagnose IIS health')
    P(story, 'Run these on the server — they prove IIS’s own services and their sites are healthy, '
             'independent of ours:')
    story.append(CodeBlock('Get-Service W3SVC, WAS | Select Name, Status     # should be Running\n'
                           'Get-Website | Select Name, State, Bindings        # their sites Started',
                           'powershell'))
    P(story, 'If W3SVC is Running and their sites are Started, IIS is fine — and any problem with '
             '<i>their</i> site is unrelated to a script that only added a separate site on a separate port.')

    # ═══ CHAPTER 5 — the one honest caveat ═══
    ch(story, 5, 'The one honest caveat', 'full transparency with your team')
    P(story, 'To be completely straight, there is exactly <b>one</b> IIS-level change in '
             '<font face="Courier">host-with-iis.bat</font> that is not scoped only to our site: '
             '<b>step 4 enables ARR’s server-level proxy flag</b> '
             '(<font face="Courier">system.webServer/proxy enabled=true</font>). This is a global IIS '
             'setting. It is normally harmless — it simply allows proxying — but it is server-wide, so '
             'mention it for full transparency:')
    story.append(warn('"The only server-wide change is enabling ARR proxying, a standard additive '
                      'setting. I made no changes to any existing site, port, or the IIS services '
                      'themselves."', title='Say this, for honesty'))
    sp(story, 6)
    P(story, 'If your team would prefer you make <b>zero</b> server-wide changes, use '
             '<font face="Courier">host-without-iis.bat</font> instead — it touches IIS <b>not at '
             'all</b> (Node simply runs on its own port). That is the easiest position to defend: '
             '<i>"I didn’t go near IIS."</i>')
    story.append(tip('Bottom line: with the direct script you can say you never touched IIS. With the '
                     'IIS script, the only global change is the standard ARR proxy toggle, and '
                     'everything else is a brand-new, separate, reversible site on its own port.'))

    sp(story, 12)
    story.append(HRFlowable(width='100%', thickness=2, color=PETROL, spaceAfter=10))
    story.append(Paragraph('You are covered: both scripts are additive, reversible, and auditable — '
                           'your existing IIS workloads keep running throughout.',
                           ParagraphStyle('end', fontName='Helvetica-Oblique', fontSize=11,
                                          textColor=PETROL, alignment=TA_CENTER, leading=16)))
    return story


def build():
    doc = BaseDocTemplate(
        OUTPUT_PATH, pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN + 6, bottomMargin=MARGIN + 6,
        title='EMBRACE AI — IIS Hosting & Safety Guide',
        author='Siemens Engineering Systems')
    frame = Frame(MARGIN, MARGIN + 4, CONTENT_W, PAGE_H - 2*MARGIN - 10, id='main')
    cover_frame = Frame(MARGIN, MARGIN, CONTENT_W, PAGE_H - 2*MARGIN, id='cover')
    doc.addPageTemplates([
        PageTemplate(id='cover', frames=[cover_frame], onPage=cover),
        PageTemplate(id='content', frames=[frame], onPage=decorate),
    ])
    story = build_story()
    for i, fl in enumerate(story):
        if isinstance(fl, PageBreak):
            story.insert(i, NextPageTemplate('content'))
            break
    doc.build(story)
    print(f'Guide generated: {OUTPUT_PATH}')


if __name__ == '__main__':
    build()
