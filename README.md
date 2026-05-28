# Hackathon POC – Playwright MCP + Git Auto-Testing

A minimal Node.js/Express web app to demonstrate **automated test generation with Playwright MCP based on Git changes**.

---

## 🚀 Quick Start (< 5 minutes)

```bash
# 1. Install dependencies
cd hackathon-poc
npm install

# 2. Install Playwright browsers
npx playwright install chromium

# 3. Start the server
npm start
# → http://localhost:3000
```

---

## 🧪 Run Tests

```bash
# Run all Playwright tests (server starts automatically)
npm test

# Open interactive UI mode
npm run test:ui

# View HTML report
npm run test:report
```

---

## 📁 Project Structure

```
hackathon-poc/
├── package.json          # Dependencies & scripts
├── server.js             # Express server (port 3000)
├── playwright.config.js  # Playwright configuration
├── public/
│   ├── index.html        # Landing page
│   ├── style.css         # Styles
│   └── script.js         # Button interaction
├── tests/
│   └── landing.spec.js   # Playwright tests
└── README.md
```

---

## 🎯 Demo Flow (Git → Auto-Test)

| Step | Action |
|------|--------|
| 1 | `git init && git add . && git commit -m "initial: Intel Costa Rica"` |
| 2 | Change `#main-title` in `index.html` from **"Intel Costa Rica"** → **"Intel CR"** |
| 3 | Playwright MCP reads the git diff, detects the text change |
| 4 | Auto-generates/updates test assertions for `#main-title` |
| 5 | Runs tests and validates the new content |

---

## 🔑 Testable Element IDs

| ID | Element | Content |
|----|---------|---------|
| `#main-title` | `<h1>` | Page heading |
| `#event-text` | `<p>` | "Hackathon CR 2026" |
| `#btn-participar` | `<button>` | "Participar" |
| `#logo` | `<img>` | Intel logo |
| `#footer-text` | `<p>` | Footer copy |

---

## ⚙️ Git Setup

```bash
git init
echo "node_modules/" > .gitignore
echo "playwright-report/" >> .gitignore
echo "test-results/" >> .gitignore
git add .
git commit -m "feat: initial Intel Costa Rica landing page"
```
