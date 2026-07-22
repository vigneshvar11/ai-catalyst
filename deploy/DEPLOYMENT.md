# EMBRACE AI — Migration & Deployment Guide

## Overview

This guide migrates the EMBRACE AI dashboard from Render (third-party) to:
- **Source code**: code.siemens.com (Siemens GitLab)
- **Hosting**: `SN1W7220.AD001.SIEMENS.NET` (Windows Server + IIS)

Architecture on the server:
```
Browser → IIS (port 80) → reverse proxy → Node.js (port 3000) → data/db.json
                         → WebSocket proxy → Socket.IO
```

---

## Part 1: Push Code to code.siemens.com

### Step 1: Create a Group on code.siemens.com

1. Open **https://code.siemens.com** and sign in with your Siemens credentials
2. Click **"New group"** (or use an existing group)
   - Group name: e.g., `engsys` or your team's namespace
   - Visibility: **Internal** (accessible to all Siemens employees) or **Private**
3. Inside the group, click **"New project"**
   - Project name: `embrace-ai`
   - Visibility: match the group setting
   - **Do not** initialize with README (you already have one)
4. Copy the HTTPS clone URL, e.g.:  
   `https://code.siemens.com/engsys/embrace-ai.git`

### Step 2: Push Your Code

Run these commands from your local project folder:

```powershell
cd "c:\Users\z00557hk\Downloads\NorthStar'25\EmbraceAI"

# Add code.siemens.com as a new remote (keep "origin" pointing to GitHub/Render)
git remote add siemens https://code.siemens.com/YOUR_GROUP/embrace-ai.git

# Push all branches and tags
git push siemens main --tags
git push siemens --all

# Verify on https://code.siemens.com/YOUR_GROUP/embrace-ai
```

### Step 3: (Later) Switch Default Remote

Once the server deployment is verified, make code.siemens.com the default:
```powershell
git remote rename origin github-old
git remote rename siemens origin
```

---

## Part 2: Deploy on Windows Server

### Step 1: Connect to the Server

1. Open **Remote Desktop Connection** (mstsc)
2. Computer: `SN1W7220.AD001.SIEMENS.NET`
3. Login: `uawet39j` (or `w99sjt30` if locked)

### Step 2: Run the Server Setup Script

Open **PowerShell as Administrator** on the server and run:

```powershell
# First, clone the repo from code.siemens.com
cd C:\
mkdir apps
cd apps
git clone https://code.siemens.com/YOUR_GROUP/embrace-ai.git
cd embrace-ai

# Run the setup script (installs IIS features, Node.js, NSSM, URL Rewrite, ARR)
powershell -ExecutionPolicy Bypass -File .\deploy\windows\setup-server.ps1
```

This installs:
- IIS with WebSocket support
- Node.js 20 LTS
- IIS URL Rewrite module
- Application Request Routing (ARR)
- NSSM (service manager)

### Step 3: Install Dependencies & Create the Service

```powershell
cd C:\apps\embrace-ai
npm install

# Register Node.js as a Windows Service
powershell -ExecutionPolicy Bypass -File .\deploy\windows\install-service.ps1
```

This creates a service called **EmbraceAI** that:
- Runs `node server.js` automatically on boot
- Restarts on crashes (5-second delay)
- Logs to `C:\apps\embrace-ai\logs\`

### Step 4: Create the IIS Site

```powershell
powershell -ExecutionPolicy Bypass -File .\deploy\windows\create-iis-site.ps1
```

This creates an IIS website that reverse-proxies to Node.js, including WebSocket support.

### Step 5: Verify

1. On the server, open: **http://localhost**
2. From your workstation, open: **http://SN1W7220.AD001.SIEMENS.NET**
3. Test each feature:
   - [ ] Dashboard loads with countdown, activity card, top 3
   - [ ] Leaderboard displays all 16 members
   - [ ] Calendar shows 12-month plan
   - [ ] Team directory loads with domain filter
   - [ ] Admin login works (admin/admin)
   - [ ] Admin: add/edit/delete members
   - [ ] Admin: assign points
   - [ ] Admin: create & run a quiz (real-time WebSocket)
   - [ ] Admin: launch a survey (real-time WebSocket)
   - [ ] Avatar upload works
   - [ ] Multiple browser tabs can join the same quiz

---

## Part 3: Updating the App

After pushing changes to code.siemens.com:

**Option A — Manual (RDP to server)**
```powershell
powershell -ExecutionPolicy Bypass -File C:\apps\embrace-ai\deploy\windows\update-app.ps1
```

**Option B — Automatic (requires GitLab Runner)**
See `.gitlab-ci.yml` — uncomment the deploy stage after installing a GitLab Runner on the server.

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| App not loading via IIS | `nssm status EmbraceAI` — if not Running, check `C:\apps\embrace-ai\logs\` |
| WebSocket not connecting | Verify IIS WebSocket feature: `Get-WindowsFeature Web-WebSockets` |
| 502 Bad Gateway | Node.js service crashed — `nssm restart EmbraceAI` |
| Port 80 conflict | Stop "Default Web Site" in IIS Manager |
| ARR not proxying | Open IIS Manager → Server → Application Request Routing → enable proxy |
| `db.json` permissions | Ensure the service account has read/write on `C:\apps\embrace-ai\data\` |

### Useful Commands

```powershell
nssm status EmbraceAI       # Check if running
nssm restart EmbraceAI      # Restart after code changes
nssm stop EmbraceAI         # Stop the service
Get-Content C:\apps\embrace-ai\logs\embrace-ai-stderr.log -Tail 50  # Recent errors
iisreset                    # Restart IIS (rarely needed)
```

---

## After Verification: Decommission Render

Once http://SN1W7220.AD001.SIEMENS.NET is fully functional:

1. Update any shared bookmarks/links to point to the new URL
2. Notify the team of the new address
3. Optionally add a redirect on Render to the new URL
4. Delete the Render service
5. (Optional) Remove the GitHub remote if no longer needed
