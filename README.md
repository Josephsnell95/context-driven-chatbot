# context-driven-chatbot

A lightweight, context-driven chatbot built for GitHub Pages portfolios.
Runs entirely on free infrastructure — Cloudflare Workers AI as primary,
Groq/Llama as fallback, with graceful failure handling so the bot never
breaks and never incurs cost.

The bot only knows what you tell it. Context is built from your GitHub Pages
HTML and optionally your Jupyter notebooks, parsed into a clean text file and
baked into the Cloudflare Worker at deploy time. Persona, tone, easter eggs,
and hard behavioural rules are all defined in plain markdown files you control.

## Architecture

```
Browser → Cloudflare Worker → Cloudflare Workers AI (primary)
                            → Groq / Llama 3.3 70B (fallback)
                            → Graceful failure message (if both rate-limited)
```

**Parser** — Python scripts that extract meaningful content from your GitHub
Pages HTML (`html_extractor.py`) and optionally Jupyter notebooks
(`notebook_extractor.py`). Output is `supplementary-context.txt`.

**Worker** (`worker/index.js`) — Cloudflare Worker that receives messages
from the widget, prepends the system prompt (persona + easter eggs + parsed
context + rules), and calls the AI. Manages the primary/fallback/graceful
failure chain.

**Widget** (`widget/chatbot.html` + `widget/chatbot.js`) — self-contained
chat UI. Floating toggle button, consent notice, session-based message history.
Embeddable in any static site.

## Context files

| File | Purpose |
|------|---------|
| `persona.md` | Bot identity, tone, name responses |
| `easter-eggs.md` | Personal details triggered by specific questions |
| `supplementary-context.txt` | Parser output — your site and notebook content |
| `bot-context.md` | Manual knowledge stub — intentionally empty at MVP |

## Setup

### 1. Clone and install

```bash
git clone https://github.com/Josephsnell95/context-driven-chatbot
cd context-driven-chatbot
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r parser/requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
```

Edit `.env` with your local paths:

```
PAGES_REPO_PATH=/path/to/your/github-pages-repo
NOTEBOOK_REPO_PATH=/path/to/your/notebooks  # optional
```

### 3. Run the parser

```bash
python parser/parser.py
```

This writes `supplementary-context.txt`. Copy its contents into the
`SUPPLEMENTARY_CONTEXT` constant in `worker/index.js`.

### 4. Deploy the Worker

Install Wrangler and authenticate:

```bash
npm install -g wrangler
wrangler login
```

Add your Groq API key as a secret (get one free at console.groq.com):

```bash
cd worker
wrangler secret put GROQ_API_KEY
```

Deploy:

```bash
wrangler deploy
```

Note the Worker URL — you'll need it in the next step.

### 5. Embed the widget

Set `WORKER_URL` in `widget/chatbot.js` to your Worker URL, then copy
`chatbot.html` and `chatbot.js` into your GitHub Pages repo and load them
via your site's main script.

## Rate limits

Cloudflare Workers AI and Groq are both free tiers with daily limits. These
are a cost constraint, not a reliability constraint — the Worker handles
rate limit errors gracefully and returns a friendly redirect message rather
than a broken experience. No cost is ever incurred beyond the free tier.

## Privacy

The widget sets no cookies. Conversation history is stored in `sessionStorage`
only — it lives in the visitor's browser and is cleared when the tab closes.
No data is stored by this project. See the deployed privacy policy for
third-party provider details.

## Repo structure

```
context-driven-chatbot/
├── parser/
│   ├── parser.py
│   ├── html_extractor.py
│   ├── notebook_extractor.py
│   └── requirements.txt
├── worker/
│   ├── index.js
│   └── wrangler.toml
├── widget/
│   ├── chatbot.html
│   └── chatbot.js
├── .github/workflows/
├── docs/chatbot-dev-plan.md
├── persona.md
├── easter-eggs.md
├── bot-context.md
├── supplementary-context.txt
└── privacy-policy.md
```