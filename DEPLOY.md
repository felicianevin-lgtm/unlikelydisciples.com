# unlikelydisciples.com — deploy runbook (GitHub Pages, free)

Site = static files in this folder. Host = GitHub Pages (free, no ads, custom
domain, HTTPS). Repo lives at github.com/<username>/unlikelydisciples.com.

## One-time setup (Felicia ~2 min + Claude does the rest)

1. **GitHub account** — sign in (or create one free) at github.com.
2. **Authorize the CLI** — Claude runs `gh auth login`; Felicia enters the
   one-time device code at github.com/login/device and approves. Claude never
   sees the password.
3. Claude then runs:
   - `gh repo create unlikelydisciples.com --public --source . --push`
   - `gh api` to enable Pages on main branch, root folder
   - CNAME file (already in repo) sets the custom domain; enforce HTTPS once
     the cert issues (~15 min).

## GoDaddy DNS (Felicia's GoDaddy → unlikelydisciples.com → DNS)

Delete any parked A/forwarding records, then add:

| Type  | Name | Value              |
|-------|------|--------------------|
| A     | @    | 185.199.108.153    |
| A     | @    | 185.199.109.153    |
| A     | @    | 185.199.110.153    |
| A     | @    | 185.199.111.153    |
| CNAME | www  | <username>.github.io |

Propagation: minutes to a few hours. Then in repo Settings → Pages tick
"Enforce HTTPS".

## Updating the site later

Edit files here → `git add -A && git commit -m "update" && git push`.
Live in ~1 minute. Streaming buttons for Spotify/Apple go in index.html at the
`<!-- Add when live -->` comment (also add the URLs to the JSON-LD `sameAs`
list — that's what tells Google this is THE Unlikely Disciples artist entity).

## SEO follow-ups once live

- Google Search Console: add property unlikelydisciples.com (verify via DNS
  TXT record at GoDaddy), submit sitemap.xml.
- Put https://unlikelydisciples.com in EVERY social bio (YT channel links,
  IG bio, TikTok bio, FB page website field) — reciprocal links are how the
  knowledge graph consolidates the entity vs. the other same-name band.
- When Spotify/Apple artist pages exist, add them to sameAs in index.html.
