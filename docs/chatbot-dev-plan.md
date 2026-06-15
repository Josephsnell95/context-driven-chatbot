# Chatbot Development Plan
### josephsnell95.github.io — Embedded Portfolio Assistant

**Author:** Joseph Snell  
**Version:** 1.2  
**Status:** Live — all phases complete  
**Last Updated:** June 2026

---

## 1. What Are We Building?

A conversational AI assistant embedded directly into your GitHub Pages portfolio site. Visitors will be able to open a chat widget and ask it questions — things like *"What tools does Joseph use?"*, *"Tell me about his Power BI work"*, or *"What's his background in analytics?"*

The bot will only know what you tell it. This is called a **governed context** — the AI is given a defined body of knowledge (about you, your work, your site) and is instructed to stay within it rather than drawing on general internet knowledge. This keeps responses accurate, on-brand, and safe.

---

## 2. Core Concepts (Explained Simply)

### 2.1 The AI Model

Rather than building an AI from scratch (which would take years and significant compute), we use an existing large language model (LLM) via an API. Think of an **API** like a drive-through window — you send in a request ("here's my context and a user's question") and the model sends back a response.

**This project uses two free APIs in a primary/fallback arrangement — total cost: £0.**

**Primary — Cloudflare Workers AI (Llama 3.3 70B)**
Cloudflare Workers AI runs directly on Cloudflare's infrastructure — the same platform hosting the Worker proxy. This means the AI call never leaves Cloudflare on the primary path, which is a cleaner data handling position for UK/EU visitors. Free tier provides 10,000 neurons per day.

**Fallback — Groq API (running Llama 3.3 70B)**
Llama is an open-source model built by Meta. Groq is a platform that hosts it for free at very high speed. It provides an additional ~1,000 requests per day.

A note on rate limits: both providers enforce daily free limits. These are a **cost constraint, not a development constraint** — the graceful failure chain means the bot never breaks and never incurs cost, regardless of traffic. See Section 2.5.

### 2.2 System Prompts (How We Govern the Bot)

Every time a user sends the bot a message, we send the AI two things:
1. A **system prompt** — a hidden set of instructions the user never sees
2. The **user's message history** — the full conversation so far

The system prompt is where the governance lives. It tells the AI who it is, what it knows, and what it should and shouldn't do. The context files (`persona.md`, `easter-eggs.md`, `supplementary-context.txt`) are baked into the Worker at deploy time as string constants — there is no runtime file fetching.

### 2.3 Context Window

The AI doesn't have memory between conversations by default. Each time someone sends a message, we include the full conversation history so far, plus the governing context. This bundle is called the **context window** — think of it as everything the AI can "see" at once.

For a portfolio bot this is plenty. Your content is finite and fits easily within modern context limits.

### 2.4 Static Site Constraint

GitHub Pages hosts **static files** — HTML, CSS, and JavaScript only. There is no server running code in the background. This matters because:

- You **cannot** store your API key in the site's code (it would be publicly visible in the HTML source)
- Any call to the AI API must go through a small backend proxy sitting in the middle

The solution is a Cloudflare Worker — see Section 6.

### 2.5 Graceful Failure (Rate Limit Handling)

Both free APIs enforce daily request limits. When a limit is hit, the API returns a `429` error (HTTP shorthand for "too many requests"). Without handling this, a visitor would see a broken or blank response.

**The solution:** the Cloudflare Worker catches any `429` error and returns a friendly human-feeling message instead — at zero cost, since it never reaches the API.

**Failure chain:**
```
User sends message
  → Worker calls Cloudflare Workers AI (primary)
      → If rate limited (error codes 3036 or 3040): Worker calls Groq/Llama (fallback)
          → If 429 again: Worker returns graceful message to user
```

**Confirmed graceful fallback message:**
> "Joe's assistant is having a rest right now — why not reach out to him directly? You can find him on LinkedIn, X, and GitHub."

The visitor still has a path to contact Joe, the experience feels intentional rather than broken, and no cost is ever incurred beyond the free tier.

---

## 3. Must-Have Requirements

| # | Requirement | What It Means |
|---|-------------|---------------|
| 1 | Embedded in GitHub Pages | The chat widget lives on your existing site — no separate URL |
| 2 | Governed context | The bot only knows what you explicitly tell it |
| 3 | Stays on topic | Politely declines to answer questions outside your defined scope |
| 4 | Reflects your brand | Tone and presentation match your portfolio |
| 5 | Mobile friendly | Usable on phones (most recruiter traffic is mobile) |
| 6 | Zero personal cost | Free APIs only — no billing risk under any traffic level |
| 7 | Graceful failure | If free limits are hit, visitor gets a friendly redirect — never a broken experience |

---

## 4. Keeping the Bot in Sync With Your Site

### Decision: Parser-driven context only (MVP)

`bot-context.md` is an intentional stub for the MVP. The bot's knowledge base is derived entirely from `supplementary-context.txt` — the parsed output of the GitHub Pages site. This means the bot's credibility is tied directly to evidenced, published content rather than unverifiable assertions in a separate file. If a project isn't written up properly on the site, the bot won't surface it — which is the right forcing function.

`bot-context.md` remains in the repo as a placeholder for future use (e.g. a RAG implementation, or content that genuinely cannot live on the site). Do not populate it without updating this plan.

The maintenance habit is simple: **when you publish new content on your Pages site, push to main — the CI/CD pipeline handles the rest.**

---

## 5. What the Bot Knows (Context Architecture)

Four constants combine to form the full system prompt, baked into the Worker at deploy time:

**`PERSONA` (Layer 0 — identity)**
Defines who Bear Necessities is, its tone, name origin, rotating name responses, and rules for when humour is appropriate. Loaded first — sets the character before any content is surfaced.

**`EASTER_EGGS` (Layer 1 — personality)**
Personal details Joe has chosen to share — hobbies, opinions, the Bear Necessities story. Triggered only when a visitor asks genuinely personal questions about Joe as a person.

**`SUPPLEMENTARY_CONTEXT` (Layer 2 — parsed site content)**
Auto-generated by the parser from the GitHub Pages HTML and optionally Jupyter notebooks. This is the bot's primary knowledge source for professional content.

**`RULES` (Layer 3 — hard constraints)**
A concise block of absolute rules appended at the end of the system prompt. Positioned last so it receives the most attention from the model. Covers identity protection, jailbreak handling, and the confirmed AI disclosure line. Takes precedence over all other layers.

`bot-context.md` is present in the repo but intentionally empty at MVP stage. See Section 4 for rationale.

---

## 6. Architecture

**Decision: Cloudflare Worker with Cloudflare Workers AI as primary, Groq/Llama as fallback.**

A Cloudflare Worker sits between your site and the AI. Your API key lives only in the Worker's environment, never on GitHub.

```
User types message
  → Browser sends to Cloudflare Worker
      → Worker calls Cloudflare Workers AI (primary — stays within Cloudflare)
          → If rate limited: Worker calls Groq/Llama (fallback)
              → If both fail: graceful failure message with contact links
                  → Response returned to browser
```

- ✅ No data leaves Cloudflare on the primary path
- ✅ More defensible privacy position for UK/EU visitors
- ✅ Still completely free

---

## 7. Technical Components

### 7.1 Repo Structure

```
context-driven-chatbot/
├── parser/
│   ├── parser.py                  # Orchestrator — reads HTML and notebooks, writes supplementary-context.txt
│   ├── html_extractor.py          # HTML → clean text
│   ├── notebook_extractor.py      # .ipynb → clean text (optional)
│   ├── validate_context.py        # CI validation script — runs on every PR to main
│   └── requirements.txt           # beautifulsoup4, python-dotenv
├── worker/
│   ├── index.js                   # Cloudflare Worker: Workers AI → Groq → graceful fail
│   └── wrangler.toml              # Cloudflare project config — Worker name, entry point, AI binding
├── widget/
│   ├── chatbot.html               # Widget HTML and CSS — embeddable structure and styling
│   └── chatbot.js                 # Widget JavaScript — interaction, session state, Worker communication
├── .github/
│   └── workflows/
│       ├── validate-context.yml   # CI: validation gate on chatbot repo PRs
│       ├── deploy-worker.yml      # CI: redeploy Worker on merge to main
│       └── sync-widget.yml        # CI: copy widget files to Pages repo on widget changes
├── docs/
│   └── chatbot-dev-plan.md        # This file
├── persona.md                     # Layer 0: Bear Necessities identity and tone
├── bot-context.md                 # Intentional stub — see Section 4
├── easter-eggs.md                 # Layer 1: personal details and personality
├── supplementary-context.txt      # Layer 2: parser output, auto-updated by CI
├── privacy-policy.md              # Source of truth for privacy policy content
├── .env.example                   # Safe to commit — template for new users
├── .env                           # Gitignored — your actual local paths
├── .gitignore
└── README.md                      # Setup guide for anyone cloning the tool
```

Note: `trigger-parser.yml` lives in the Pages repo (`.github/workflows/`), not the chatbot repo.

### 7.2 The HTML Parser (parser/parser.py + parser/html_extractor.py)

`parser.py` is a thin orchestrator. It reads GitHub Pages HTML files via `html_extractor.py`, and optionally Jupyter notebooks via `notebook_extractor.py` if `NOTEBOOK_REPO_PATH` is set in `.env`. Output is written to `supplementary-context.txt`. If `NOTEBOOK_REPO_PATH` is not set, notebooks are silently skipped.

**Status: Complete ✅**

### 7.3 The API Proxy (worker/index.js)

A Cloudflare Worker that:
1. Receives the conversation history from the widget as a JSON array
2. Constructs the system prompt from four baked-in constants: `PERSONA`, `EASTER_EGGS`, `SUPPLEMENTARY_CONTEXT`, and `RULES`
3. Calls Cloudflare Workers AI (primary)
4. If rate limited (error codes 3036 or 3040), calls Groq/Llama (fallback)
5. If both fail, returns the graceful failure message
6. Otherwise returns the AI response to the browser as JSON

**Deployment:** Managed via Wrangler CLI. `wrangler.toml` in `worker/` declares the Worker name, entry point, and Workers AI binding. The Groq API key is stored as a Wrangler secret — never committed to the repo.

**Live URL:** `https://bear-necessities-worker.josephsnell.workers.dev`

**Status: Complete and deployed ✅**

### 7.4 The Chat Widget (widget/chatbot.html + widget/chatbot.js)

The widget is split into two files:

**`chatbot.html`** — contains the HTML structure and scoped CSS. Includes the toggle button, chat panel, consent notice, message history container, loading indicator, and input row. The `<style>` block is self-contained so it does not conflict with the portfolio site's stylesheet when injected.

**`chatbot.js`** — contains all JavaScript. Handles panel open/close, consent acknowledgement, message rendering, Worker communication, error handling, and session state persistence. Scrolls to the latest message on render and on session restore.

**Embed approach:** both files live in `assets/html/` and `assets/js/` respectively in the GitHub Pages repo. `main.js` fetches `chatbot.html` via `insertAdjacentHTML` and then appends `chatbot.js` as a dynamically created script tag. This ensures the script executes after the HTML is in the DOM, and means the widget is injected on every page without duplicating code.

**Session state:** panel open/closed state, consent acknowledgement, and full message history are all persisted to `sessionStorage`. This means the widget survives page navigations within a tab — the panel stays open, the conversation history is restored, and the user does not see the consent notice again. Everything clears when the tab is closed.

**Error handling:** the fetch to the Worker is wrapped in try/catch/finally. If the request fails for any reason, a friendly error message is rendered in the chat and the input is re-enabled via the `finally` block.

**Status: Complete and embedded ✅**

### 7.5 Conversation State

Conversation history is persisted to `sessionStorage` as a JSON array. Each new message is appended to the array and saved immediately. On page load, the saved array is restored and all messages are re-rendered into the history panel. When the tab closes, `sessionStorage` is cleared — no database needed, no persistent storage.

---

## 8. Development Phases

### Phase 1 — Parser ✅
- [x] Build `parser.py` with `.env` configuration for repo path
- [x] Refactor: split HTML extraction into `html_extractor.py`
- [x] Create `.env.example` as a safe-to-commit template
- [x] Validate parser output against live Pages HTML

### Phase 2 — Worker ✅
- [x] Create Cloudflare account
- [x] Build `worker/index.js` — Workers AI → Groq → graceful failure
- [x] CORS handling for cross-origin requests from GitHub Pages
- [x] Add `wrangler.toml` with Workers AI binding declaration
- [x] Add Groq API key as Wrangler secret
- [x] Deploy Worker to Cloudflare
- [x] Test end-to-end with a real API call — response confirmed

### Phase 3 — Widget ✅
- [x] Build `widget/chatbot.html` — floating chat UI with consent notice
- [x] Implement consent notice (session memory, no cookies)
- [x] Style to match portfolio site
- [x] Refactor: split JavaScript into `widget/chatbot.js`
- [x] Add session state persistence (panel state, message history)
- [x] Add error handling (try/catch/finally around Worker fetch)
- [x] Mobile tested — works on iPhone; minor desktop resize edge case noted, not material

### Phase 4 — Embed & Test ✅
- [x] Embed widget in GitHub Pages via `main.js` injection pattern
- [x] Widget persists across page navigations
- [x] Deploy privacy policy page (`privacy_policy.html` at Pages repo root)
- [x] Add footer link to privacy policy
- [x] Test against all 12 success criteria
- [x] Fix jailbreak vulnerability — added `RULES` block to end of system prompt

### Phase 4b — Pre-CI/CD Cleanup ✅
- [x] Full repo audit — all files reviewed file by file
- [x] `html_extractor.py` — removed dead `SKIP_CLASSES` constant; added UTF-8 BOM comment
- [x] `notebook_extractor.py` — added `.strip()` to kept lines; filter empty sections before appending
- [x] `parser.py` — removed unused `yaml` import; wired in `notebook_extractor`; fixed error string; added optional notebook parsing block
- [x] `chatbot.js` — added scroll-to-bottom on render and session restore; consistent semicolons
- [x] `chatbot.html` — corrected privacy policy URL to `privacy_policy.html`
- [x] `worker/index.js` — added optional chaining on Groq response parse
- [x] `.env.example` — removed `BOT_CONTEXT_PATH` and `GROQ_API_KEY`; fixed `NOTEBOOK_REPO_PATH` comment
- [x] `README.md` — written from scratch; covers architecture, setup, rate limits, privacy, repo structure
- [x] `.gitignore` — added `__pycache__/`

### Phase 5 — CI/CD Pipeline ✅
- [x] Build `parser/validate_context.py` — validation script with four checks
- [x] Add `.github/workflows/validate-context.yml` — runs on every PR to main, blocks merge on failure
- [x] Replace `LINK` placeholders in `persona.md` and `easter-eggs.md` with real contact URLs
- [x] Add `.github/workflows/trigger-parser.yml` to Pages repo — fires on push to main
- [x] Cross-repo PR confirmed working — parser runs, diffs output, opens PR on chatbot repo if changed
- [x] End-to-end pipeline tested — Pages push → parser → automated PR → validation gate → merge
- [x] Remove legacy `parser-config.example.yml` and `parser-config.yml` files

### Phase 6 — Content & Polish ✅
- [x] Add Bear Necessities project page (`projects/bear_necessities.html`) to Pages site
- [x] Add Bear Necessities to projects index and homepage featured grid
- [x] Mobile tested — widget works on iPhone; desktop resize edge case noted, not material
- [x] Worker redeploy automation — `deploy-worker.yml` fires on merge to main, runs `wrangler deploy`
- [x] Widget sync Action — `sync-widget.yml` copies `chatbot.html` and `chatbot.js` to Pages repo on widget changes
- [x] Screenshots added to Bear Necessities project page
- [x] Privacy policy link in consent notice corrected to `privacy_policy.html`

---

## 9. CI/CD Pipeline Design

CI/CD stands for *Continuous Integration / Continuous Deployment*. GitHub provides this for free via **GitHub Actions** on public repos.

### 9.1 Parser Trigger (pages repo → chatbot repo)

**Trigger:** push or merge to `main` on the Pages repo  
**File:** `.github/workflows/trigger-parser.yml` (lives in the Pages repo)  
**What it does:** checks out both repos, runs `parser.py` with `PAGES_REPO_PATH` set to the runner workspace, diffs output against current `supplementary-context.txt`, opens a PR on the chatbot repo if changed  
**Uses:** `CHATBOT_REPO_PAT` secret stored in the Pages repo — fine-grained PAT scoped to contents and pull requests on the chatbot repo  
**Result:** automated PR appears on chatbot repo; validation gate runs automatically on that PR

### 9.2 Validation Gate (chatbot repo PR)

**Trigger:** any pull request opened against the chatbot repo  
**File:** `.github/workflows/validate-context.yml`  
**Script:** `parser/validate_context.py`  
**Checks:**
- `supplementary-context.txt` exists and is non-empty
- `supplementary-context.txt` is under 800,000 characters
- `persona.md` exists and is non-empty
- No `LINK` or `[PLACEHOLDER]` strings remain in `persona.md` or `easter-eggs.md`

**Result:** PR blocked from merging if any check fails — green tick if all pass

### 9.3 Worker Redeploy (chatbot repo → Cloudflare)

**Trigger:** merge to `main` on the chatbot repo  
**File:** `.github/workflows/deploy-worker.yml`  
**What it does:** checks out the repo, installs Node and Wrangler, runs `wrangler deploy` from `worker/`  
**Uses:** `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ACCOUNT_ID` secrets stored in the chatbot repo  
**Result:** Worker is redeployed automatically on every merge to main — context updates go live without a manual step

### 9.4 Widget Sync (chatbot repo → Pages repo)

**Trigger:** push to `main` on the chatbot repo affecting `widget/**`  
**File:** `.github/workflows/sync-widget.yml`  
**What it does:** checks out both repos, copies `widget/chatbot.html` to `assets/html/` and `widget/chatbot.js` to `assets/js/` in the Pages repo, commits and pushes directly to Pages main  
**Uses:** `CHATBOT_REPO_PAT` secret stored in the chatbot repo — fine-grained PAT scoped to contents on the Pages repo  
**Result:** widget updates propagate to the live site automatically on merge

---

## 10. Persona & Behaviour Decisions

### Voice
Third person at all times — the bot is an assistant *about* Joseph, not a simulation of Joseph.

### Fallback Behaviour
When the bot cannot answer, it redirects warmly to Joe's contact channels rather than going silent or guessing.

### Response Style
Lead with business impact, then method, then link. The achievement first, the technique second.

---

## 11. Estimated Costs

| Item | Cost |
|------|------|
| Cloudflare Workers AI (primary) | Free — 10,000 neurons/day |
| Groq API / Llama (fallback) | Free — ~1,000 req/day |
| Cloudflare Workers (proxy) | Free up to 100,000 requests/day |
| GitHub Pages hosting | Free |
| **Total** | **£0** |

---

## 12. Privacy & Consent

A privacy policy is required. Bear Necessities has a genuinely light data footprint:
- No database, no logging, no cookies
- Conversation lives only in the visitor's browser's `sessionStorage` — cleared when the tab closes
- No personal data collected or stored by Joe

**Files:**
- `privacy-policy.md` — source of truth in the chatbot repo; keep in sync with deployed page
- `privacy_policy.html` — deployed at `josephsnell95.github.io/privacy_policy.html` ✅
- Consent notice built into `widget/chatbot.html` — session memory only, input disabled until acknowledged ✅
- Footer link to privacy policy on all pages via shared `footer.html` ✅

---

## 13. Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Bot gives inaccurate information | Governed context; only parsed site content surfaces |
| API key exposed | Cloudflare Worker proxy; keys never committed to GitHub |
| Free tier limits hit | Primary → fallback → graceful failure — zero cost regardless |
| Bot goes off-topic | System prompt constraints; tested against edge cases before go-live |
| Jailbreak / persona reassignment | `RULES` block appended to end of system prompt; confirmed effective in testing |
| Free tier terms change | Architecture is portable — swapping provider means ~5 lines in the Worker |
| GDPR non-compliance | Cloudflare Workers AI keeps data within one provider; privacy policy and consent notice in place |
| Context stale after Pages update | CI/CD pipeline opens automated PR on chatbot repo; Worker redeploy Action fires on merge |
| Widget out of sync with chatbot repo | Widget sync Action copies files to Pages repo automatically on widget changes |

---

## 14. Success Criteria

All 12 criteria confirmed passing ✅

1. *"What does Joe do professionally?"* ✅
2. *"What tools and technologies does he use?"* ✅
3. *"Tell me about one of his projects."* ✅
4. *"Where can I see his work?"* ✅
5. *"How can I contact him?"* ✅
6. *"Are you AI?"* → "Bear by name, AI by nature..." ✅
7. *"What's your name?"* → rotating Bear Necessities response ✅
8. Off-topic question → polite redirect to contact ✅
9. Jailbreak attempt → cheerfully firm refusal ✅
10. Rate limit hit → friendly fallback with contact links ✅ *(confirmed during Worker build)*
11. Personal question → warm easter egg response ✅
12. First message → consent notice shown, input disabled until acknowledged ✅

---

## 15. Future Considerations

**RAG architecture** — replace the baked-in context string with a vector database. Semantic retrieval at query time rather than loading everything into the prompt. The right approach as the site grows, but requires paid infrastructure and an embedding model. Not needed at current content volume.

**Source-aware responses** — Bear surfaces links to the relevant page on the site alongside answers, so visitors can navigate directly to the write-up rather than just reading a summary.

**Widget sync PR vs direct push** — currently the widget sync Action commits directly to Pages main. If the widget becomes more complex, switching to a PR-based approach (matching the parser trigger pattern) gives an extra review step before changes go live.

---

*This document is a living reference. Update it as decisions are made and phases are completed.*