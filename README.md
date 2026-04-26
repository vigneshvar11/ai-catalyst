<p align="center">
  <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/5/5f/Siemens-logo.svg/320px-Siemens-logo.svg.png" alt="Siemens" width="160">
</p>

<h1 align="center">EMBRACE AI</h1>
<p align="center"><strong>Engineering Systems — 12-Month AI Initiative Dashboard</strong></p>
<p align="center">
  <em>Siemens · Chennai · FT D AA IN SGI DET ENGSYS</em>
</p>

<p align="center">
  <a href="https://render.com/deploy?repo=https://github.com/vigneshvar11/embrace-ai">
    <img src="https://render.com/images/deploy-to-render-button.svg" alt="Deploy to Render">
  </a>
</p>

---

## What Is This?

EMBRACE AI is a gamified, 12-month learning initiative designed to upskill the 16-member Engineering Systems offshore team on Generative AI — starting from fun, curiosity-driven activities and progressing to real business use-case delivery.

This repository contains the **full-stack dashboard** that powers the initiative:

| Feature | Description |
|---------|-------------|
| **Dashboard** | Live countdown, current activity, seminar spotlight, top 3 leaderboard |
| **Leaderboard** | Cumulative monthly points table with all 16 members |
| **Calendar** | 12-month event timeline with phase indicators |
| **Team Directory** | Member cards with domains, roles, and profile photos |
| **Live Quiz** | Real-time MCQ game with room codes, tab-switch detection, anti-copy |
| **Seminar Survey** | Anonymous 1–5 star rating for presenters |
| **Admin Panel** | Manage members, assign points, create quizzes, launch surveys |

---

## Quick Start

### Prerequisites

- **Python 3.8+** installed ([python.org](https://www.python.org/downloads/))
- A modern browser (Chrome / Edge / Firefox)

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/YOUR_USERNAME/embrace-ai-dashboard.git
cd embrace-ai-dashboard

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start the server
python app.py
```

### Open the Dashboard

```
http://localhost:3000
```

### Admin Login

Click the **profile icon** (top right) and enter:
- **Username:** `admin`
- **Password:** `admin`

---

## Project Structure

```
EmbraceAI/
├── app.py                  # Python Flask server (backend)
├── requirements.txt        # Python dependencies
├── data/
│   └── db.json             # Database (all members, events, points, quizzes, surveys)
├── public/
│   ├── index.html          # Single-page application (frontend)
│   ├── css/
│   │   └── styles.css      # Siemens-themed styling
│   └── js/
│       └── app.js          # Frontend logic (navigation, rendering, quiz, survey)
├── uploads/
│   └── avatars/            # Member profile photos (uploaded via admin)
├── .gitignore
└── README.md
```

---

## How It Works

### Architecture

```
Browser (HTML/CSS/JS)  ◄──HTTP──►  Flask Server (app.py)  ◄──Read/Write──►  db.json
                       ◄─WebSocket─►  Flask-SocketIO          (JSON file)
```

- **Flask** serves the web pages and handles all API requests (add members, award points, etc.)
- **Flask-SocketIO** powers real-time features (live quiz, live survey, instant updates)
- **db.json** acts as a lightweight database — a single JSON file storing everything

### Public vs Admin

| | Public (No Login) | Admin (Login Required) |
|---|---|---|
| Dashboard | ✅ | ✅ |
| Leaderboard | ✅ | ✅ |
| Calendar | ✅ (view only) | ✅ (edit events) |
| Team | ✅ | ✅ |
| Quiz | ✅ (join & play) | ✅ (create & host) |
| Survey | ✅ (vote) | ✅ (launch & close) |
| Manage Members | ❌ | ✅ |
| Award Points | ❌ | ✅ |

---

## Hosting Options

### Option A: Office Network (Simplest)

```bash
python app.py
# Find your IP: ipconfig (Windows) or ifconfig (Mac/Linux)
# Share: http://YOUR_IP:3000
```

### Option B: Render (Free Cloud Hosting)

1. Push to GitHub
2. Go to [render.com](https://render.com) → New Web Service → Connect repo
3. Build Command: `pip install -r requirements.txt`
4. Start Command: `python app.py`
5. Share the generated URL with your team

### Option C: Railway / Fly.io

Similar to Render — connect GitHub, deploy, get a public URL.

---

## The 12-Month Syllabus

| Month | Title | Phase | Key Skill |
|-------|-------|-------|-----------|
| 1 | Who's Who: AI Edition | SPARK | Prompt engineering, image generation |
| 2 | AI Storyteller: EngSys Chronicles | SPARK | Multi-turn prompting, visual storytelling |
| 3 | Prompt Battle Arena | SPARK | Advanced prompt engineering |
| 4 | Copilot Power User | BUILD | M365 Copilot, productivity workflows |
| 5 | Code with AI | BUILD | AI-assisted coding, code review |
| 6 | Smart Documentation / RAG | BUILD | RAG, enterprise AI assistants |
| 7 | Automate the Boring Stuff | APPLY | AI automation, solution design |
| 8 | AI Agents Hackathon | APPLY | Agentic AI, multi-step workflows |
| 9 | Data Detective | APPLY | AI-powered data analysis |
| 10 | Use Case: Problem Definition | DELIVER | Business problem framing |
| 11 | Use Case: Build & Iterate | DELIVER | Prototyping, peer review |
| 12 | Grand Finale Showcase | DELIVER | End-to-end AI value demonstration |

---

## Points System

| Category | Points |
|----------|--------|
| Seminar Presenter (peer-rated 1–5) | Up to 5 |
| Quiz Winner (Top 3) | 3 / 2 / 1 |
| Activity Completion | 3 |
| Activity Award Categories | 5 each |
| First to Submit | 2 bonus |
| People's Choice (peer vote) | 3 |
| **Grand Finale — Best Use Case** | **15** |

Top 3 at year-end receive **Star Points** redeemable for gift cards / vouchers.

---

## Team

| Name | Domain |
|------|--------|
| Aravinthan Dhanabal | Manufacturing |
| Aswin Gangadharan | OT & Automation |
| Balaji M | PLM |
| Dharankumar N | PLM |
| Gopalakrishnan Rajendran | PLM |
| John Yabesh Johnson | Manufacturing |
| Minal Ramesh Nilange | Manufacturing |
| Pandiyarajan Nagarajan | Cross-Functional |
| Priyadharshani Varsha S | PLM |
| Rizwan Ali M | PLM |
| Saravanan Jayabalan | Cross-Functional |
| Sivakumar D | Cross-Functional |
| Soniya Dhayalan | OT & Automation |
| Tippu Sultan Shaik | PLM |
| Vidya Srivatsan | Cross-Functional |
| **Vigneshvar SA** | **PLM (Initiative Lead)** |

---

## Easter Eggs 🥚

- Type `embraceai` anywhere on the page
- Check the footer

---

<p align="center">
  <em>vibe coded with <strong>AI</strong> ✦</em>
</p>
