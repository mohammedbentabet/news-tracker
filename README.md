# Signal Desk — Multi-source News Monitor

A self-updating news dashboard covering Finance, Economics, Politics, Sports, OSINT/Investigative, and Society across ~40 outlets (EN/FR/AR). Runs entirely free on GitHub — no server, no hosting bill.

## What's in this folder
- `index.html` — the website itself (open this in a browser to preview locally)
- `data/sources.json` — the list of outlets and their RSS URLs (edit this to add/remove sources)
- `data/news.json` — the live data file, rewritten every ~15 minutes by the GitHub Action
- `scripts/fetch_news.py` — the script that pulls all the feeds
- `.github/workflows/update-news.yml` — the scheduler that runs the script automatically
- `requirements.txt` — Python dependency (just `feedparser`)

## One-time setup (10 minutes)

1. **Upload these files to your repo.**
   On your new repo's page, click **"Add file" → "Upload files"**, then drag in everything from this folder — keep the folder structure intact (the `.github/workflows/` and `data/` and `scripts/` folders need to stay where they are). Commit the upload.

2. **Turn on GitHub Pages.**
   Go to your repo → **Settings → Pages**. Under "Build and deployment", set **Source: Deploy from a branch**, branch **main**, folder **/ (root)**. Save. GitHub will give you a live URL like `https://yourusername.github.io/your-repo-name/` — that's your website.

3. **Turn on and run the Action once manually.**
   Go to the **Actions** tab. If prompted, click "I understand my workflows, enable them." Click into **"Update News Data"** on the left, then click **"Run workflow"** (top right) to trigger the first fetch immediately rather than waiting 15 minutes.

4. **Check it worked.**
   After ~1 minute, refresh the Actions tab — the run should show a green checkmark. Then visit your Pages URL. The ticker and cards should populate, and the "Source Health" panel at the bottom of the page shows which of the ~40 feeds succeeded (green dot) or failed (red dot) on the last run.

From then on, it updates itself every 15 minutes automatically, with no further action from you.

## A few things to know

- **Some feed URLs may need a tweak.** A handful of the ~40 sources (regional/French/Arabic outlets in particular) were selected based on known-good RSS conventions but not individually pre-tested against a live fetch — GitHub's servers can reach sites my sandbox can't test against directly. If the Source Health panel shows a red dot for any source, send me its name and I'll give you a corrected URL or a working alternative in one line.
- **"Headline only" sources** (Financial Times, Reuters) are marked with a red badge — these outlets don't offer full-article RSS, so you get title + link only, not the article body. Click through to read on the source site.
- **Updates are "roughly" every 15 minutes.** GitHub can delay scheduled runs by 10-30 minutes during high load — this is a GitHub platform limit, not something we can tune away on the free tier.
- **Adding or removing a source:** edit `data/sources.json` directly on GitHub (click the file → pencil icon → edit → commit). No need to touch any other file.
