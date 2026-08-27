# W3-16 — Deployment runbook

## Streamlit Community Cloud

1. Push this repository to GitHub without `.env` or API keys.
2. In Streamlit Community Cloud choose **Create app**.
3. Select the repository/branch and set main file to `app.py`.
4. Use Python 3.11 and allow installation from `requirements.txt`.
5. The app reads committed processed artifacts; add provider secrets only if a
   future deployment refreshes data at runtime.
6. Deploy, open the public URL in an incognito browser, and execute the smoke
   checklist below.

## React deployment alternative

```powershell
cd frontend
npm ci
npm run build
```

Publish `frontend/dist` to Vercel, Cloudflare Pages, Netlify, or GitHub Pages.
The SPA must serve `public/data/dashboard.json` at `/data/dashboard.json`.

## Smoke checklist

- Research page loads and reports the visible market date.
- Combined filters apply only after Apply Filters.
- Missing values do not pass active criteria.
- Ticker deep dive and SPY comparison render.
- Method table of contents and signal explanation open.
- Market Quest resets and advances from Day 1 to Day 2.
- Camera denial produces a recoverable message.
- Mobile viewport has no inaccessible core control.

## Status

Local deployment configuration is complete. A public URL requires the owner's
GitHub/Streamlit or static-host account and therefore remains external evidence;
no URL is fabricated in this document.
