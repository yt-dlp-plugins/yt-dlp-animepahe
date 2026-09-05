This is a [yt-dlp](https://github.com/yt-dlp/yt-dlp "yt-dlp repooository") extractor plugin for [animepahe](https://animepahe.pw/ "animepahe"). it supports downloading single episodes, full playlists, and searching for content directly.

---

> [!IMPORTANT]
> **Requirements**: Animepahe requires Cloudflare bypass. 
> You **must** pass [`--impersonate`][impersonation] and supply valid cookies (e.g., [`--cookies-from-browser <browser>`][cookie]) for downloads to work.

---

## Installation
```bash
python -m pip install -U https://github.com/yt-dlp-plugins/yt-dlp-animepahe/archive/main.zip
```

## Usage

**1. Using url**:
```bash
# Default: all available languages
yt-dlp 'https://animepahe.pw/play/1c443926-8b78-358d-6cef-c9daf1fa3c8c/5df890ee9349d3254440096fa4a45bb754dfcb64868391d66740096a505afb33'

# Take only one language
yt-dlp --extractor-args 'animepahe:lang=ja' 'https://animepahe.pw/play/1c443926-8b78-358d-6cef-c9daf1fa3c8c/5df890ee9349d3254440096fa4a45bb754dfcb64868391d66740096a505afb33'

# Multiple languages, separate by commas
yt-dlp --extractor-args 'animepahe:lang=ja,en' 'https://animepahe.pw/play/1c443926-8b78-358d-6cef-c9daf1fa3c8c/5df890ee9349d3254440096fa4a45bb754dfcb64868391d66740096a505afb33'
```
> ⚠️ If the extractor displays `No video formats found!`, it means the language you selected is not available.


**2. Using search**:
```bash
yt-dlp 'animepahe:title'
```
---

## Troubleshooting

- HTTP Error [403](https://github.com/yt-dlp/yt-dlp/wiki/FAQ#im-getting-http-error-403-and-the-site-has-an-open-issue-on-the-tracker-thats-labeled-cloudflare-related-what-can-i-do) (Forbidden) on webpage download: Make sure to pass your browser cookies using [`--cookies-from-browser <browser_name>`][cookie] or [`--cookies <cookie_file>`][cookie].
- HTTP Error 403 (Forbidden) on video stream: Ensure [`--impersonate`][impersonation] is active to bypass Cloudflare TLS fingerprints.
- HTTP Error 429 (Too Many Requests): Animepahe rate-limited your IP. Add `--sleep-requests 5` to delay requests.

---

<div align="center">
  <img src="https://media.tenor.com/PdqGAzCcin8AAAAj/rtx-on-wuwa.gif" alt="iwak tempe"/>
</div>

[cookie]: https://github.com/yt-dlp/yt-dlp/wiki/FAQ#how-do-i-pass-cookies-to-yt-dlp
[impersonation]: https://github.com/yt-dlp/yt-dlp/blob/master/README.md#impersonation
