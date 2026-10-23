# Running Harvey for Finely Tossed

[Harvey](https://github.com/ethanplusai/harvey) (MIT) is an open-source cold-email agent. It finds restaurants, reads their sites, drafts emails with Claude, and waits for you to approve each one before anything is sent. It runs on your own computer, using your Claude Pro or Max subscription through the Claude CLI.

This folder holds everything specific to Finely Tossed:

| File | What it is |
|---|---|
| `harvey.local.yaml` | Harvey's settings: persona, product, target chefs and cities, sending limits. Approval is on. |
| `skills/product_knowledge.md` | What Harvey knows about Finely Tossed, including the hard email rules (no prices, no "website/SEO" wording, personal hook, preview CTA). |
| `contacted.csv` (not in git) | The 20 restaurants already emailed on 20 Oct 2026. This repo is public, so the list is kept out of git: download it from the project files and save it in this folder. |
| `seed_contacted.py` | Marks those 20 as "contacted" in Harvey's database so it skips them. |

Harvey 0.2.1 (commit `f851026`) installed cleanly with Python 3.13, and its test suite passed (1,237 passed, 25 skipped). Loading this config and running `harvey status` works, with the postal-address warning described below.

## What you need first

- Python 3.11 or newer (`python3 --version`)
- The Claude CLI, logged in to your Pro or Max plan: `npm install -g @anthropic-ai/claude-code`, then `claude login`. Check with `claude -p "say hi"`.
- Git

## Install (about 10 minutes)

```bash
# 1. Get Harvey and this repo side by side
git clone https://github.com/ethanplusai/harvey.git
git clone https://github.com/udddipandatta-web/Lead.git
cd harvey

# 2. Install it in its own virtual environment
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e .

# 3. Copy in the Finely Tossed config and product knowledge
cp ../Lead/harvey-setup/harvey.local.yaml .
cp ../Lead/harvey-setup/skills/product_knowledge.md skills/

# 4. Create your secrets file (never commit it)
cp .env.example .env
```

## Fill in `.env`

Only these matter for now:

| Key | Needed? | Where to get it |
|---|---|---|
| `GMAIL_CLIENT_ID`, `GMAIL_CLIENT_SECRET` | Yes | [Google Cloud Console](https://console.cloud.google.com/): create a project, enable the **Gmail API**, set up the OAuth consent screen (External, add udddipandatta@gmail.com as a test user), then Credentials → Create OAuth client ID → **Desktop app**. Paste both values. |
| `REOON_API_KEY` | Strongly recommended | [reoon.com/email-verifier](https://reoon.com/email-verifier) → sign up → API. Verifies addresses before sending so you don't bounce. Free tier is enough. |
| `ZEROBOUNCE_API_KEY` | Optional | [zerobounce.net](https://zerobounce.net) → API. 100 free checks a month; better at Google/Microsoft catch-all domains. |
| `SERPER_API_KEY` or `DATAFORSEO_*` | Optional | Paid discovery sources. The free default (OpenStreetMap) is fine to start. |

Then connect Gmail once:

```bash
harvey gmail auth        # opens a browser; sign in as udddipandatta@gmail.com
```

## Set your postal address (required)

Open `harvey.local.yaml` and fill in `compliance.postal_address` with a street address, PO box or virtual mailbox where you receive post. US law (CAN-SPAM) requires it in every cold email, and Harvey adds it under each one with the opt-out line. Until it is set, `harvey run`, `harvey status` and the Outbox show a warning.

## Exclude the 20 restaurants already emailed

Save `contacted.csv` from the project files into `../Lead/harvey-setup/` first, then:

```bash
python ../Lead/harvey-setup/seed_contacted.py
harvey status            # should show Prospects: {'contacted': 20}
```

Harvey has no separate exclusion list, so this records each restaurant's email domain as a known company with its contact already "contacted". Discovery skips known domains, and the sender never sends a first email to a contacted address. Two of the 20 use a hotel group's email domain, so Harvey will also skip other restaurants on those two domains. Follow-ups to these 20 stay with the existing Gmail threads, not Harvey.

When you contact more chefs outside Harvey, add them to `contacted.csv` and run the script again. It is safe to re-run.

## Choose what Harvey looks for

```bash
harvey signals                 # review the catalog
harvey signals --confirm free  # turn on the free signals
harvey discover --estimate     # see what discovery would find and cost
harvey discover                # find restaurants in the configured cities
```

Discovery finds restaurants by city; it can't tell which ones hold a Michelin star. Use the dashboard's Companies tab or cohort builder to keep the list to fine dining, and reject anything that isn't a fit in the Outbox.

## Run it

Two terminals, both with `source .venv/bin/activate` inside the `harvey` folder:

```bash
harvey dashboard     # prints a private link to http://127.0.0.1:5555 — open it
harvey run           # the loop: every 15 minutes it finds, profiles, drafts
```

Every email lands in the dashboard's **Outbox** for you to approve (`A`), edit (`E`) or reject (`R`). Nothing is sent without your approval, because `require_approval: true` is set. To stop all sending at once: `harvey sending pause`.

## Deliverability: read before sending at volume

- **Sending from personal Gmail is a stopgap.** The config caps it at 15 a day. Cold email from a personal address is easy for Gmail to flag, and a flag hurts your own inbox too.
- **Move to a dedicated domain.** The plan is `uddipan@finelytossed.com`. Buy the domain, create a Google Workspace mailbox on it, and add Google's SPF, DKIM and DMARC records (if you also keep Resend, its SPF include and DKIM record from the Resend setup notes can sit alongside them). Change `persona.email` and redo `harvey gmail auth` with that account.
- **Warm it up for 2–4 weeks** with a warmup service before real volume. Set `channels.email.warmup.start_date` to the day warmup starts; Harvey then holds cold email for 14 days and ramps from 5 a day.
- **Check readiness** any time with `harvey warmup finelytossed.com` (SPF, DKIM, DMARC, domain age, blocklists).
- **Watch bounces.** The config pauses sending if bounces pass 3%.

## Differences from the manual outreach brief

- Harvey's writer aims for short emails (first email under 75 words), shorter than the 100–150 words used in the manual batches. To keep 100–150, edit rule 10 in Harvey's `prompts/writer.md`.
- Harvey adds the postal address and an opt-out line ("Not the right fit? Reply "no thanks" and I won't email again.") under each cold email.

## Moving to Resend later

Harvey has no Resend integration. It supports Gmail, Microsoft 365, and any SMTP + IMAP mailbox. Resend offers SMTP for sending but doesn't host an inbox for Harvey to read replies from, so a Google Workspace mailbox on finelytossed.com is the simplest fit.
