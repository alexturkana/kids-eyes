# Kids Eyes — Video Library Website

A clean, professional website for Dr. Martin C. Wilson's pediatric ophthalmology practice. Parents browse a searchable library of educational YouTube videos about children's eye conditions. Built to be simple, trustworthy, and mobile-friendly.

## Live URLs

- Website: https://kids-eyes-production.up.railway.app *(or whatever Railway assigns)*
- Target domain: https://www.kids-eyes.com *(locked by Wix — connect later)*

## Tech Stack

- **Backend:** Flask (Python) — `app.py`
- **Frontend:** Single-file vanilla HTML/CSS/JS — `templates/index.html` (home + video library)
- **Contact page:** `templates/contact.html` (practice info, map, office photos)
- **Video data:** YouTube Data API v3 (channel videos, metadata, statistics)
- **Video playback:** YouTube IFrame Player API (embedded player)
- **Hosting:** Railway (gunicorn, auto-deploys on push to main)
- **Repo:** GitHub — `alexturkana/kids-eyes` (branch: main)
- **Static assets:** `/static/` directory (logo, office photos, CSS if separated)

## Project Structure

```
app.py                  ← Flask application (all backend routes + YouTube API proxy)
Procfile                ← web: gunicorn app:app --bind 0.0.0.0:$PORT
requirements.txt        ← flask, gunicorn, requests, google-api-python-client
templates/
  index.html            ← Home page — video player + searchable video library
  contact.html          ← Contact page — practice info, map, office photos
static/
  kids-eyes-logo.png    ← Logo file
  office-front.jpg      ← Office photo — front angle
  office-side.jpg       ← Office photo — side angle
  favicon.ico           ← Favicon (cropped from logo)
```

## Local Development

- Python: `C:\BOB\python_scripts\Python\Python312\python.exe`
- App folder: `C:\kids_eyes_website\`
- Run: `"C:\BOB\python_scripts\Python\Python312\python.exe" "C:\kids_eyes_website\app.py"`
- Opens at: http://localhost:5000

## Deploy Workflow

```
cd C:\kids_eyes_website
git add .
git commit -m "description"
git push
# Railway auto-deploys on push to main
```

---

## CRITICAL ARCHITECTURE RULES

### 1. YouTube IFrame Player API Compliance

Per [YouTube Required Minimum Functionality](https://developers.google.com/youtube/terms/required-minimum-functionality):

- **Minimum player size:** 200×200px viewport. Recommended: at least 480×270 (16:9).
- **No overlays:** Never display overlays, frames, or visual elements in front of the embedded player or its controls.
- **No obscuring:** Never obscure any part of the player including controls.
- **No mouseover hijacking:** Never use mouseover/touch events on the player to trigger external actions.
- **No player modifications:** Only use changes explicitly described in the API docs.
- **Autoplay rules:** If autoplay is used, playback must initiate immediately when visible. We do NOT autoplay — user clicks play.
- **HTTP Referer:** Ensure Referrer-Policy is `strict-origin-when-cross-origin` (browser default). Do not suppress Referer.
- **No background play:** Never allow video to play when the window is closed/minimized.
- **No gating:** Never require users to take actions (subscribe, like, etc.) to watch a video.
- **Ads must play:** Never restrict YouTube ads from playing in the embedded player.

**Standard embed pattern:**
```html
<iframe
  width="560" height="315"
  src="https://www.youtube.com/embed/VIDEO_ID"
  title="YouTube video player"
  frameborder="0"
  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
  referrerpolicy="strict-origin-when-cross-origin"
  allowfullscreen>
</iframe>
```

**IFrame Player API pattern (for programmatic control):**
```html
<div id="player"></div>
<script>
  var tag = document.createElement('script');
  tag.src = "https://www.youtube.com/iframe_api";
  var firstScriptTag = document.getElementsByTagName('script')[0];
  firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);

  var player;
  function onYouTubeIframeAPIReady() {
    player = new YT.Player('player', {
      height: '315',
      width: '560',
      videoId: 'VIDEO_ID',
      playerVars: { 'playsinline': 1 },
      events: {
        'onReady': onPlayerReady,
        'onStateChange': onPlayerStateChange
      }
    });
  }
</script>
```

### 2. YouTube Data API v3 — Key Rules

- **API key** stored as Railway env var `YOUTUBE_API_KEY` — never hardcoded in frontend JS.
- **Channel handle:** `@martinwilson3510` — resolve to channel ID via API `channels.list?forHandle=martinwilson3510`.
- **Quota:** Default 10,000 units/day. `search.list` costs 100 units. `videos.list` costs 1 unit. `channels.list` costs 1 unit.
- **Strategy:** Use `playlistItems.list` on the channel's "uploads" playlist (cheap — 1 unit) instead of `search.list` (expensive — 100 units). Get the uploads playlist ID from `channels.list` response → `contentDetails.relatedPlaylists.uploads`.
- **Caching:** Cache video metadata in a JSON file or in-memory dict. Refresh on app startup and via a `/api/refresh` endpoint. Never call the YouTube API on every page load.
- **Fallback:** If API quota is exceeded or API key is missing, serve from a static `videos_cache.json` snapshot.

**Efficient data flow:**
1. `channels.list(forHandle=martinwilson3510)` → get channel ID + uploads playlist ID (1 unit)
2. `playlistItems.list(playlistId=UPLOADS_PLAYLIST_ID, maxResults=50)` → get all video IDs (1 unit per page)
3. `videos.list(id=VIDEO_IDS, part=snippet,contentDetails,statistics)` → get full metadata (1 unit per page of 50)
4. Cache everything. Serve from cache.

### 3. Single-File Frontend Approach

Keep each page as a single HTML file with inline CSS and JS — same pattern as the Memory Puzzle app. No React, Vue, jQuery, npm, or build tools. This keeps deployment simple and the codebase easy to hand off.

### 4. No Windows Paths in app.py

Railway runs Linux. Never use `C:\` paths or Windows-specific file references. Use `os.path` or relative paths only.

### 5. Port Configuration

Railway sets `$PORT` env var. app.py reads: `port = int(os.environ.get('PORT', 5000))`

### 6. Dependencies

Railway uses `requirements.txt` — keep it minimal:
```
flask
gunicorn
requests
google-api-python-client
```

### 7. Independent Value Requirement

Per YouTube developer policies, the site must provide **independent value** beyond just displaying YouTube videos. Our independent value:
- **Searchable video library** with filtering by title, description, and topic
- **Sortable metadata** (date, duration, views, likes)
- **Practice integration** — videos are contextual to a specific doctor's practice
- **Curated medical resource** — organized by pediatric eye condition, not a general video browser
- **Contact/practice information** — connects videos to actionable next steps (calling the office)

---

## Railway Environment Variables

| Variable | Value |
|---|---|
| YOUTUBE_API_KEY | AIzaSyBRJu_AhOD-NumzCvwpTYJGZ-MMmtUkQ_Q |
| PORT | *(set automatically by Railway)* |

## Google Cloud Project

- Project ID: `youtubeuploader-480119`
- API key name: `kids_eyes_website`
- Credentials console: https://console.cloud.google.com/apis/credentials?project=youtubeuploader-480119
- API key management: https://console.cloud.google.com/apis/credentials/key/de6d0f0e-bca9-4510-875d-75fe399cd17d?project=youtubeuploader-480119
- Enabled API: YouTube Data API v3

## YouTube Channel

- Handle: `@martinwilson3510`
- Channel URL: https://www.youtube.com/@martinwilson3510
- Channel ID: *(resolve via API on first run — cache it)*
- Description: KIDS EYES Video Discussions
- Topics: pediatric ophthalmology, childhood myopia, astigmatism, amblyopia, strabismus, school vision problems

---

## Practice Information

- **Doctor:** Dr. Martin C. Wilson, M.D.
- **Practice:** Pediatric Eye Physicians & Surgeons
- **Specialty:** Pediatric Ophthalmology
- **Address:** 155 W Lancaster Ave, Paoli, PA 19301
- **Phone:** (610) 993-8083
- **Affiliations:** Children's Hospital of Philadelphia (CHOP), Temple University School of Medicine (Class of 1990), 35+ years experience
- **Office Hours:**
  - Monday: 8 AM – 4 PM
  - Tuesday: 8 AM – 4 PM
  - Wednesday: 8 AM – 4 PM
  - Thursday: 8 AM – 4 PM
  - Friday – Sunday: Closed

---

## Key Features

### Home Page (Video Library)
- Hero video player — YouTube IFrame embed, large and prominent
- Random video selected on page load (from cached video list, not autoplay)
- Searchable video list — filters by title, description text
- Sort controls — by title (A-Z), date published, duration, view count, like count
- Video cards — thumbnail, title, duration badge, publish date, description excerpt
- Click any card → loads video into hero player + scrolls to top
- Video metadata display — title, full description, stats below player
- Responsive — works on phone, tablet, desktop

### Contact Page
- Practice name, doctor name, specialty
- Address with Google Maps embed
- Phone number (clickable tel: link on mobile)
- Office hours table
- Office photos (uploaded images)
- Kids Eyes logo

### Global
- Sticky header with logo + nav (Home | Contact)
- Footer with practice info + YouTube channel link
- Color palette from logo: pink (#F4BDD7), sky blue (#8DD3E0), dark charcoal for text
- Clean, warm typography — professional but approachable for parents
- Mobile-first responsive design
- Accessible: good contrast, readable sizes, alt text, keyboard nav

---

## Google Cloud Setup — COMPLETED ✅

- Project: `youtubeuploader-480119`
- YouTube Data API v3: enabled
- API key (`kids_eyes_website`): created and stored in Railway env vars
- **TODO:** Restrict API key to production domain(s) once Railway URL and kids-eyes.com are known

---

## Future Enhancements (Not MVP)

- Video category tags / filter chips (auto-grouped by topic keywords)
- Transcript search (via YouTube captions API or third-party service)
- "Recently Added" badges on new videos
- Share buttons per video
- SEO: unique URL paths per video (`/videos/what-is-astigmatism`)
- Schema.org structured data (MedicalBusiness, Physician, VideoObject)
- Privacy-friendly analytics (Plausible or Vercel Analytics)
- Dark mode toggle
- Cloudflare CDN for static assets (if needed for performance)
- Connect kids-eyes.com domain when Wix releases it

## Out of Scope

- Patient portal / login
- Appointment booking
- Blog / written articles
- E-commerce / payments
- Multi-language support
- Email newsletter
- Video uploads (all content comes from YouTube channel)

---

## Session Handoff

When the user says **"starting a new chat"** or **"new chat"**, save a fresh project snapshot to memory before responding:
1. Update project state — reflect any new routes, features, or line counts from this session
2. Note any coding patterns, bugs found, or architectural decisions made
3. Confirm to the user that memory is saved and they can safely start a new chat
