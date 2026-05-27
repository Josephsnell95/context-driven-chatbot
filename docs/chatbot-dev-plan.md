# Chatbot Development Plan
### josephsnell95.github.io — Embedded Portfolio Assistant

**Author:** Joseph Snell  
**Version:** 0.1 — Planning Document  
**Status:** Pre-development  
**Last Updated:** May 2026

---

## 1. What Are We Building?

A conversational AI assistant embedded directly into your GitHub Pages portfolio site. Visitors will be able to open a chat widget and ask it questions — things like *"What tools does Joseph use?"*, *"Tell me about his Power BI work"*, or *"What's his background in analytics?"*

The bot will only know what you tell it. This is called a **governed context** — the AI is given a defined body of knowledge (about you, your work, your site) and is instructed to stay within it rather than drawing on general internet knowledge. This keeps responses accurate, on-brand, and safe.

---

## 2. Core Concepts (Explained Simply)

### 2.1 The AI Model

Rather than building an AI from scratch (which would take years and significant compute), we use an existing large language model (LLM) via an API. Think of an **API** like a drive-through window — you send in a request ("here's my context and a user's question") and the model sends back a response.

**This project uses two free APIs in a primary/fallback arrangement — total cost: £0.**

**Primary — Google Gemini API (via Google AI Studio)**
Gemini 2.5 Flash is available on a permanent free tier with 1,500 requests per day and a 1 million token context window. More than sufficient for portfolio traffic, and no credit card required.

**Fallback — Groq API (running Llama 3.3 70B)**
Llama is an open-source model built by Meta. Groq is a platform that hosts it for free at very high speed. It provides an additional 1,000 requests per day. 

A note on Llama: Meta releases Llama as open-source "model weights" — meaning anyone can host and run it. Groq is simply one of several platforms that do this for free. You're not calling Meta directly; you're calling Groq, which runs Llama on your behalf.

Combined free capacity: ~2,500 requests/day before any limits are hit.

### 2.2 System Prompts (How We Govern the Bot)

Every time a user sends the bot a message, we send the AI two things:
1. A **system prompt** — a hidden set of instructions the user never sees
2. The **user's message**

The system prompt is where the governance lives. It tells the AI who it is, what it knows, and what it should and shouldn't do. Example:

> *"You are a helpful assistant on Joseph Snell's portfolio site. You only answer questions about Joseph's skills, projects, and professional background. If asked anything outside this, politely redirect the user. Here is what you know about Joseph: [your content goes here]"*

This is not code — it's plain English. You write it, you control it.

### 2.3 Context Window

The AI doesn't have memory between conversations by default. Each time someone sends a message, we include the full conversation history so far, plus your governing context. This bundle is called the **context window** — think of it as everything the AI can "see" at once.

For a portfolio bot this is plenty. Your content is finite and fits easily within modern context limits.

### 2.4 Static Site Constraint

GitHub Pages hosts **static files** — HTML, CSS, and JavaScript only. There is no server running code in the background. This matters because:

- You **cannot** store your API key in the site's code (it would be publicly visible in the HTML source)
- Any call to the AI API must go through a small backend proxy sitting in the middle

**Solution options are explored in Section 5.**

### 2.5 Graceful Failure (Rate Limit Handling)

Both free APIs enforce daily request limits. When a limit is hit, the API returns a `429` error (HTTP shorthand for "too many requests"). Without handling this, a visitor would see a broken or blank response.

**The solution:** the Cloudflare Worker catches any `429` error and returns a friendly human-feeling message instead — at zero cost, since it never reaches the API.

**Failure chain:**
```
User sends message
  → Worker calls Gemini (primary)
      → If 429: Worker calls Groq/Llama (fallback)
          → If 429 again: Worker returns graceful message to user
```

**Confirmed graceful fallback message:**
> "Joe's assistant is having a rest right now — why not reach out to him directly? You can find him on LinkedIn (LINK), X (LINK), and GitHub (LINK)."

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

This is one of the most important design decisions — and one that's easy to overlook. Your GitHub Pages site will evolve over time as you add projects and posts. The bot's knowledge is whatever you put in the system prompt. Those two things will drift apart unless you have a deliberate strategy.

### The Three Approaches

**Option A — Manual context file (recommended)**

You maintain a single file in your repo called `bot-context.md`. It contains everything the bot knows about you — written in your own words, structured around the project template. When you update your site, you update this file too. The Cloudflare Worker reads it and uses it as the system prompt.

- ✅ Completely free, no moving parts
- ✅ You control exactly what the bot knows and how it's phrased — scrapers can't write "Joe saved his employer X"
- ✅ Version controlled — you can see exactly what the bot knew and when
- ⚠️ Requires a small discipline habit: update the file when you publish new content

**Option B — Automatic scraping (tempting but fragile)**

A script visits your site periodically and updates the context automatically.

- ✅ Hands-off once set up
- ❌ Scraped text is messy — picks up navigation, footers, repeated boilerplate
- ❌ Cannot infer business impact or what matters — just grabs raw text
- ❌ Adds complexity for a site that updates monthly, not daily

**Option C — RAG / vector database (overkill for now)**

RAG stands for *Retrieval Augmented Generation*. Rather than loading all your content into the system prompt at once, your content lives in a searchable database. When a user asks a question, the system fetches only the most relevant sections and passes those to the AI.

This is how enterprise chatbots handle large, frequently-changing content. It's the right approach at scale — but it requires a vector database, an embedding model, and paid infrastructure. Worth knowing about for the future, but not needed here.

### Decision: Option A

For your use case, manual is genuinely better than automated. The business impact framing has to come from you regardless — so you're writing the content either way. The maintenance habit is simply: **update `bot-context.md` when you publish something new.**

```
You publish a new blog post or project
  → Open bot-context.md in your repo
      → Add the new entry using the project template (5 min)
          → Commit it
              → The bot knows it on the next conversation
```

Because this file lives in your repo, it's version controlled — you can see the full history of what the bot knew and when.

---

## 5. What the Bot Should Know (Your Knowledge Base)

The `bot-context.md` file is structured around these sections. Each one feeds directly into the system prompt.

### 5.1 Professional Identity
- Who you are and what you do
- Your job title / area of expertise (analytics, data, AI)
- Your learning-in-public approach

### 5.2 Technical Skills
- Languages: Python, SQL, etc.
- Tools: Power BI, Azure DevOps, Jupyter
- Areas: data analysis, ML/AI fundamentals, dashboard development

### 5.3 Projects & Work
Each project gets its own entry using this template:

```
Project Name: [Name]
Business Impact: [PLACEHOLDER — to be completed by Joe]
What Joe Did: [The analytical/technical approach in plain English]
Tools Used: [Specific tools and methods]
Page Link: [URL to the relevant section or post on your site]
```

> ⏳ **TASK FOR JOE:** Complete a business impact entry for each project currently on your site. Even rough figures ("reduced reporting time by ~60%") are more powerful than methodology descriptions alone. This is the single most important content task before the bot goes live.

### 5.4 Site Map
- What pages/sections exist on your site
- What each section contains, so the bot can direct visitors to the right place

### 5.5 Scope Boundaries (What NOT to Answer)
- Personal questions outside your professional life
- Opinions on topics unrelated to your work
- Anything not explicitly included in `bot-context.md`

---

## 6. Architecture Options

Three approaches, ordered by simplicity:

### Option A — Direct API Call from the Browser *(Simplest, Not Recommended for Production)*

The user's browser calls the AI API directly. API key is exposed in your JavaScript.

- ✅ Easiest to build
- ❌ Anyone who views source can steal your API key
- ✅ Good for a private prototype / local testing only

---

### Option B — Cloudflare Worker Proxy *(Recommended)*

A Cloudflare Worker sits between your site and the AI. Your API key lives only in the Worker's environment, never on GitHub.

**Architecture note — why not Gemini as primary:**
Research confirmed that the Gemini free tier may use prompts to improve Google's models, and the free tier has restrictions for EU users under GDPR. Since your site is accessible from the UK and EU, this creates a compliance concern for a public-facing chatbot.

**Recommended primary model: Cloudflare Workers AI.** Since your Worker already runs on Cloudflare infrastructure, the AI call never leaves Cloudflare — cleaner data handling, simpler architecture, still completely free.

```
User types message
  → Browser sends to Cloudflare Worker
      → Worker calls Cloudflare Workers AI (primary — stays within Cloudflare)
          → If unavailable: Worker calls Groq/Llama (fallback)
              → If both fail: graceful failure message with contact links
                  → Response returned to browser
```

- ✅ No data leaves Cloudflare on the primary path
- ✅ Simpler — one infrastructure provider rather than two external APIs
- ✅ More defensible privacy position for UK/EU visitors
- ✅ Still completely free

---

### Option C — Netlify/Vercel Hosting *(Alternative to GitHub Pages)*

Move the portfolio to Netlify or Vercel. Both host static sites for free and let you add serverless functions in the same repo.

- ✅ Cleaner architecture
- ✅ Still free
- ⚠️ Means migrating away from GitHub Pages

---

**Decision: Option B — Cloudflare Worker with Cloudflare Workers AI as primary, Groq/Llama as fallback.**

---

## 7. Technical Components

### 7.1 Repo Structure

The chatbot lives in its own repo, separate from your GitHub Pages repo. This makes it a standalone reusable product that others can clone and adapt for their own portfolio.

```
portfolio-chatbot/
├── parser/
│   ├── parser.py                  # HTML → supplementary-context.txt
│   └── requirements.txt           # beautifulsoup4, python-dotenv
├── worker/
│   └── index.js                   # Cloudflare Worker: Gemini → Groq → graceful fail
├── widget/
│   └── chatbot.html               # Embeddable chat widget (drop into any site)
├── .github/
│   └── workflows/
│       ├── validate-context.yml   # CI: validation gate on chatbot repo PRs
│       └── trigger-parser.yml     # CI: parser trigger from pages repo pushes
├── persona.md                     # Layer 0: Bear Necessities identity, tone, name responses
├── bot-context.md                 # Layer 1: curated professional knowledge
├── easter-eggs.md                 # Layer 1b: personal details and personality
├── supplementary-context.txt      # Layer 2: parser output, auto-updated by CI
├── .env.example                   # Safe to commit — template for new users
├── .env                           # Gitignored — your actual local paths
├── .gitignore
└── README.md                      # Setup guide for anyone cloning the tool
```

The `.env.example` that anyone cloning the repo would copy and fill in:

```
# Path to your local GitHub Pages repo
PAGES_REPO_PATH=/path/to/your/pages/repo

# Path to your curated context file
BOT_CONTEXT_PATH=/path/to/your/bot-context.md
```

This pattern — real config gitignored, example config committed — is standard professional practice and immediately recognisable to any engineer reviewing the repo.

### 7.2 The HTML Parser (parser.py)

A local Python script using `BeautifulSoup` that reads your GitHub Pages HTML files and extracts meaningful body content, stripping out navigation, footers, scripts, and styling boilerplate. Output is `supplementary-context.txt` — a clean text summary of everything on your site.

This serves as Layer 2 context: the bot has broad site awareness even for content not yet manually written up in `bot-context.md`.

### 7.3 The Context Files

Four files combine to form the full system prompt, loaded in priority order:

**`persona.md` (Layer 0 — identity)**
Defines who Bear Necessities is, its tone, name origin, rotating name responses, and rules for when humour is appropriate. Loaded first — sets the character before any content is surfaced.

**`bot-context.md` (Layer 1 — curated knowledge)**
Hand-written, impact-led professional content. Joe's bio, skills, and project entries with business impact. Maintained manually; updated when new work is published.

**`easter-eggs.md` (Layer 1b — personality)**
Personal details Joe has chosen to share — hobbies, opinions, the Bear Necessities story. Triggered only when a visitor asks genuinely personal questions about Joe as a person (not off-topic probing). Kept separate so it can be updated independently.

**`supplementary-context.txt` (Layer 2 — parsed)**
Auto-generated by the parser. Broad site awareness as a fallback. Loaded last and carries lowest precedence.

The Cloudflare Worker injects all four in order, with earlier layers taking precedence where content overlaps.

**On copyright:** `persona.md` and `easter-eggs.md` must never reproduce song lyrics verbatim. Bear Necessities responses riff on the *concept* and *spirit* of the song — original interpretations only. The title "The Bear Necessities" may be referenced freely.

### 7.4 The API Proxy (Cloudflare Worker)

A JavaScript file (~50 lines) that:
1. Receives the conversation from your site
2. Combines `bot-context.md` and `supplementary-context.txt` as the system prompt
3. Calls the Gemini API (primary)
4. If Gemini returns a 429, calls the Groq/Llama API (fallback)
5. If both return 429, returns the graceful failure message
6. Otherwise returns the AI response to the browser

### 7.5 The Chat Widget (widget/chatbot.html)

A floating button in the corner of your page that opens a chat panel when clicked. Built in plain HTML, CSS, and JavaScript — no frameworks needed. Designed to be dropped into any static site with a single `<script>` tag.

**Key parts:** toggle button, message history panel, text input and send button, loading indicator, close/minimise button.

### 7.6 Conversation State

The widget tracks conversation history in the browser's memory during a session. Each new message appends to the history, which is sent to the Worker each time. When the page is closed, history resets — no database needed.

---

## 8. Development Phases

### Phase 1 — Local Prototype
*Goal: Prove it works before putting it live*

- [ ] Create a Google AI Studio account and get a free Gemini API key
- [ ] Create a Groq account and get a free API key (fallback)
- [ ] Write a first draft of `bot-context.md` with basic identity and placeholder projects
- [ ] Build a minimal HTML chat widget (single file, no styling)
- [ ] Test the API call directly in the browser (temporarily, for local testing only)
- [ ] Validate: does the bot stay on topic? Does the tone feel right?

### Phase 2 — Secure the API Keys
*Goal: Make it safe to put live*

- [ ] Create a Cloudflare account (free)
- [ ] Deploy a Cloudflare Worker with both API keys stored as environment secrets
- [ ] Implement the primary → fallback → graceful failure logic in the Worker
- [ ] Update the chat widget to call the Worker instead of the API directly
- [ ] Test end-to-end from a live URL

### Phase 3 — Embed in GitHub Pages
*Goal: Integrate cleanly into your portfolio*

- [ ] Style the chat widget to match your site's colours and fonts
- [ ] Add the widget to your `index.html`
- [ ] Test on mobile
- [ ] Add a subtle label indicating it's AI-powered

### Phase 4 — Populate the Knowledge Base
*Goal: Make the bot genuinely useful to recruiters*

- [ ] ⏳ **TASK FOR JOE:** Complete `bot-context.md` — write business impact entries for each project
- [ ] Add FAQ-style content for questions a recruiter might ask
- [ ] Test edge cases: what happens when someone asks something out of scope?
- [ ] Refine system prompt instructions based on real test conversations

### Phase 5 — Parser & CI/CD Pipeline
*Goal: Automate context freshness and enforce quality*

- [ ] Build `parser.py` with `.env` configuration for repo path
- [ ] Create `.env.example` as a safe-to-commit template
- [ ] Write `README.md` explaining the tool for other users
- [ ] Set up GitHub Action on pages repo: trigger parser on push/merge
- [ ] Configure cross-repo PR: parser output auto-raises PR on chatbot repo
- [ ] Set up GitHub Action on chatbot repo: validate `bot-context.md` on PR
- [ ] Define and implement validation spec (see Section 8)
- [ ] Test full end-to-end pipeline: pages update → parser → PR → validation → deploy

---

## 8. CI/CD Pipeline Design

CI/CD stands for *Continuous Integration / Continuous Deployment*. It means code events (pushes, pull requests, merges) automatically trigger actions — tests, builds, updates — without manual steps. GitHub provides this for free via **GitHub Actions** on public repos.

This project implements two complementary Actions that together form a full automated pipeline.

### 8.1 Angle 1 — Parser Trigger (pages repo → chatbot repo)

**What it solves:** without this, you have to remember to manually run the parser every time your pages site changes. With it, that happens automatically.

**Trigger:** a push or merge to your GitHub Pages repo  
**Action:** runs `parser.py` against the updated HTML, diffs the output against the current `supplementary-context.txt`, and if anything has changed, automatically opens a PR on the chatbot repo with the updated file  
**Result:** you get a PR to review — you're still in control, the automation just does the legwork

```
Push/merge to pages repo
  → GitHub Action triggers parser.py
      → Fresh supplementary-context.txt generated
          → Diff against current version
              → If changed: PR auto-opened on chatbot repo
                  → Joe reviews and merges
```

**What this requires:**
- A GitHub Personal Access Token (PAT) stored as a secret in the pages repo, scoped to allow PRs on the chatbot repo
- The parser script accessible from the Action (lives in the chatbot repo, called via the token)

### 8.2 Angle 2 — Validation Gate (chatbot repo PR)

**What it solves:** prevents broken or incomplete context from ever reaching the live bot. Checks run before merge, not after.

**Trigger:** any pull request opened against the chatbot repo  
**Action:** runs a validation script against `bot-context.md`  
**Result:** PR is blocked from merging if validation fails — green tick means it's safe to deploy

**Validation spec — what counts as valid:**

| Check | Rule |
|-------|------|
| Required sections | Identity, Skills, Projects, Contact, Site Map all present |
| Project entries | At least one complete project entry exists |
| Project fields | Every entry has: Name, Business Impact, What Joe Did, Tools Used, Page Link |
| No placeholders | No text matching `[PLACEHOLDER]` or `[to be completed]` remains |
| Contact URLs | LinkedIn, X, and GitHub URLs are present and correctly formatted |
| Token budget | Total character count of both context files is under 800,000 characters (safe margin for Gemini's 1M token context window) |

### 8.3 The Full Pipeline End-to-End

```
Joe updates pages repo (new post or project)
  → Angle 1: parser runs, raises PR on chatbot repo
      → Joe reviews supplementary context, merges PR
          → Angle 2: validation runs on merged content
              → All checks pass → green tick
                  → Cloudflare Worker picks up updated bot-context.md
                      → Bot is live with current knowledge
```

This is a genuine end-to-end automated pipeline. It demonstrates not just the ability to build something, but to maintain it reliably — a distinction that matters significantly at mid-senior level.

---

## 9. Persona & Behaviour Decisions

These are confirmed design decisions that will shape the system prompt.

### 8.1 Voice
The bot speaks in **third person** at all times. It is an assistant *about* Joseph, not a simulation of Joseph. This is more trustworthy and avoids any awkwardness of an AI pretending to be a person.

> ✅ "Joe evidenced forecasting in his work on Project X..."  
> ❌ "I worked on forecasting in Project X..."

### 8.2 Fallback Behaviour
When a visitor asks something the bot cannot answer from the knowledge base, it should not guess or go silent. Instead it redirects warmly to Joe's contact channels.

**Confirmed fallback line (adapt as needed):**
> "That's not something I can speak to directly — but why not reach out to Joe? You can find him on [LinkedIn], [X/Twitter], and [GitHub]."

The bot should have Joe's profile URLs baked into the system prompt so it can link them directly in fallback responses.

### 8.3 Response Style — Lead with Business Impact
This is the most important design decision for making the bot useful to recruiters.

When answering skills or capability questions, the bot should **lead with the outcome/impact, then evidence it with the project**, then link to the relevant page. This mirrors how a strong CV works — the achievement first, the method second.

**Example of the target response pattern:**

> *Visitor: "Does Joe know much about forecasting?"*
>
> *Bot: "Yes — Joe applied demand forecasting in [Project X], where his model helped his employer reduce inventory costs by [X%]. He used [method/tool] to do it. You can see the full write-up [here → link]."*

This means your **knowledge base entries for each project need to explicitly include the business impact** — not just what you did technically, but what it changed for the organisation. Even approximate figures (e.g. "reduced manual reporting time by ~60%") are more powerful than methodology descriptions alone.

---

## 10. The System Prompt — Starter Template

Below is a starter template you'll flesh out with your actual content. The business impact instruction is baked into the behaviour rules.

```
You are an AI assistant on Joe Snell's professional portfolio website 
(josephsnell95.github.io). Your role is to help visitors — particularly 
recruiters and collaborators — understand Joe's skills, experience, and 
project work.

BEHAVIOUR RULES:
- Always refer to Joe in the third person
- Only answer using the information provided in this prompt — never invent or 
  assume details
- When answering questions about Joe's skills or capabilities, lead with 
  business impact first ("Joe delivered X result"), then explain the method or 
  tool used, then link to the relevant page on his site
- Keep responses concise — 2–4 sentences is ideal unless more detail is asked for
- If asked something outside this knowledge base, respond with:
  "That's not something I can speak to directly — but why not reach out to Joe? 
  You can find him on LinkedIn (LINK), X (LINK), and GitHub (LINK)."
- Never speculate. If you're not sure, use the fallback above.

ABOUT JOE:
[Professional bio — who he is, what he specialises in, his learning-in-public approach]

SKILLS:
[Languages, tools, platforms — Python, SQL, Power BI, Azure DevOps, etc.]

PROJECTS:
Format each project like this:

Project Name: [Name]
Business Impact: [What changed for the organisation — quantified if possible]
What Joe Did: [The analytical/technical approach in plain English]
Tools Used: [Specific tools and methods]
Page Link: [URL to the relevant section or post on your site]

CONTACT:
LinkedIn: [URL]
X/Twitter: [URL]  
GitHub: [URL]

SITE SECTIONS:
[Brief description of what each section of the site contains, so the bot can 
direct visitors to the right place]
```

---

## 10. Estimated Costs

| Item | Cost |
|------|------|
| Gemini API (primary, 1,500 req/day) | Free — permanent tier |
| Groq API / Llama (fallback, 1,000 req/day) | Free — permanent tier |
| Cloudflare Workers (proxy) | Free up to 100,000 requests/day |
| GitHub Pages hosting | Free |
| Domain (optional) | ~£10–15/year if you add a custom domain |
| **Total** | **£0** |

Combined free API capacity of ~2,500 requests/day means the bot would need to be fielding the equivalent of a viral moment before limits are even approached — and even then, the graceful failure kicks in rather than any cost.

---

## 11. Privacy & Consent

### 11.1 Privacy Policy

A privacy policy is required. The moment visitor messages are sent to a third-party API, data is being processed — even transiently. A public-facing chatbot accessible to UK and EU visitors falls under UK GDPR.

The good news: Bear Necessities has a genuinely light data footprint by design:
- No database, no logging, no cookies
- Conversation lives only in the visitor's browser memory — gone when the tab closes
- No personal data is collected or stored by Joe

The policy lives at `josephsnell95.github.io/privacy-policy` and must be kept up to date if the AI provider changes.

**File:** `privacy-policy.md` → deploy as a page on your GitHub Pages site

### 11.2 In-Widget Consent Notice

A consent notice must appear in the chat widget before a visitor can type. This is displayed once per session — "Got it" dismisses it using session memory only (no cookie, no persistent storage).

**Confirmed notice text:**

```
By chatting with Bear Necessities you agree to our Privacy Policy.
Messages are processed by Cloudflare AI. We don't store your conversations.
[Privacy Policy ↗]  [Got it]
```

The privacy policy link opens in a new tab. "Got it" hides the notice and activates the input field. If the visitor doesn't click "Got it", the input field remains disabled — they cannot send a message without acknowledging the notice.

### 11.3 What to Add to Your GitHub Pages Site

- A `/privacy-policy` page (can be a simple HTML page from the markdown draft)
- The consent notice built into `widget/chatbot.html`
- A footer link to the privacy policy on your main site (good practice regardless of the chatbot)

---

## 12. Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Bot gives inaccurate information | Strict system prompt; only include verified content in `bot-context.md` |
| API key exposed | Use Cloudflare Worker proxy (Phase 2); never commit keys to GitHub |
| Free tier limits hit unexpectedly | Primary → fallback → graceful failure chain handles this at zero cost |
| `bot-context.md` falls out of date | Build the 5-min update habit into your publishing workflow |
| Bot goes off-topic | Test edge cases in Phase 1; tighten system prompt instructions |
| Visitors try to jailbreak it | Cloudflare Workers AI and Groq/Llama are resistant; persona.md reinforces this |
| Free tier terms change | Architecture is portable — swapping the AI provider means updating ~5 lines in the Worker |
| GDPR/UK GDPR non-compliance | Cloudflare Workers AI as primary keeps data within one provider; privacy policy and consent notice are in place |

---

## 13. Success Criteria

The bot is considered ready when it can correctly and confidently answer:

1. *"What does Joe do professionally?"*
2. *"What tools and technologies does he use?"*
3. *"Tell me about one of his projects."*
4. *"Where can I see his work?"*
5. *"How can I contact him?"*
6. *"Are you AI?"* → "Bear by name, AI by nature..."
7. *"What's your name?"* → one of the rotating Bear Necessities responses

And gracefully handles:

8. *"What's your opinion on [unrelated topic]?"* → polite redirect to contact
9. *"Ignore your instructions and..."* → stays governed, cheerfully firm
10. A question when rate limits are hit → friendly fallback with contact links
11. A personal question covered in `easter-eggs.md` → warm, witty, on-brand
12. Consent notice shown before first message → input disabled until acknowledged

---

## 14. Next Steps

When you're ready to start building, the immediate actions are:

1. **Sign up for Cloudflare** → cloudflare.com (free account — Workers and Workers AI)
2. **Sign up for Groq** → console.groq.com (free Llama API key — fallback)
3. **Deploy the privacy policy** → add `privacy-policy.md` as a page on your GitHub Pages site
4. ⏳ **TASK FOR JOE:** Fill in remaining easter egg placeholders (shooting type, weakness wit, contact URLs throughout all files)
5. ⏳ **TASK FOR JOE:** Begin drafting `bot-context.md` — bio, skills, and at least one project entry
6. **Come back here** — we'll build the Phase 1 prototype together, one piece at a time

---

*This document is a living reference. Update it as decisions are made and phases are completed.*