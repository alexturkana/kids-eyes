import os
import json
import time
import re
import logging
from flask import Flask, render_template, jsonify
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

YOUTUBE_API_KEY = os.environ.get('YOUTUBE_API_KEY', '')
CHANNEL_HANDLE = 'martinwilson3510'
CACHE_FILE = 'videos_cache.json'
CACHE_TTL = 3600  # 1 hour

_uploads_playlist_id = None  # cached after first lookup

_video_cache = []
_cache_timestamp = 0


def get_youtube_client():
    return build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)


def parse_duration_seconds(duration_str):
    match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration_str or '')
    if not match:
        return 0
    h = int(match.group(1) or 0)
    m = int(match.group(2) or 0)
    s = int(match.group(3) or 0)
    return h * 3600 + m * 60 + s


def format_duration(duration_str):
    total = parse_duration_seconds(duration_str)
    h = total // 3600
    m = (total % 3600) // 60
    s = total % 60
    if h:
        return f'{h}:{m:02d}:{s:02d}'
    return f'{m}:{s:02d}'


def best_thumbnail(thumbnails):
    for quality in ('standard', 'high', 'medium', 'default'):
        t = thumbnails.get(quality, {})
        if t.get('url'):
            return t['url']
    return ''


def get_uploads_playlist_id():
    """Resolve channel handle → uploads playlist ID (cached in memory)."""
    global _uploads_playlist_id
    if _uploads_playlist_id:
        return _uploads_playlist_id
    yt = get_youtube_client()
    resp = yt.channels().list(
        part='contentDetails',
        forHandle=CHANNEL_HANDLE
    ).execute()
    items = resp.get('items', [])
    if not items:
        raise ValueError(f'Channel @{CHANNEL_HANDLE} not found')
    _uploads_playlist_id = items[0]['contentDetails']['relatedPlaylists']['uploads']
    logging.info(f'Resolved uploads playlist: {_uploads_playlist_id}')
    return _uploads_playlist_id


def fetch_playlist_videos():
    if not YOUTUBE_API_KEY:
        logging.warning('No API key — serving from cache file')
        return load_cache_file()

    try:
        yt = get_youtube_client()
        playlist_id = get_uploads_playlist_id()
        video_ids = []
        page_token = None

        # Collect all video IDs from channel uploads
        while True:
            resp = yt.playlistItems().list(
                part='contentDetails',
                playlistId=playlist_id,
                maxResults=50,
                pageToken=page_token
            ).execute()
            for item in resp.get('items', []):
                vid = item['contentDetails'].get('videoId')
                if vid:
                    video_ids.append(vid)
            page_token = resp.get('nextPageToken')
            if not page_token:
                break

        if not video_ids:
            logging.warning('Playlist returned no videos')
            return load_cache_file()

        # Fetch full metadata in batches of 50
        videos = []
        for i in range(0, len(video_ids), 50):
            batch = video_ids[i:i + 50]
            vresp = yt.videos().list(
                part='snippet,contentDetails,statistics',
                id=','.join(batch)
            ).execute()
            for item in vresp.get('items', []):
                snippet = item.get('snippet', {})
                content = item.get('contentDetails', {})
                stats = item.get('statistics', {})
                duration_str = content.get('duration', 'PT0S')
                videos.append({
                    'id': item['id'],
                    'title': snippet.get('title', ''),
                    'description': snippet.get('description', ''),
                    'thumbnail': best_thumbnail(snippet.get('thumbnails', {})),
                    'publishedAt': snippet.get('publishedAt', ''),
                    'duration': format_duration(duration_str),
                    'durationSeconds': parse_duration_seconds(duration_str),
                    'viewCount': int(stats.get('viewCount', 0)),
                    'likeCount': int(stats.get('likeCount', 0)),
                })

        save_cache_file(videos)
        logging.info(f'Fetched {len(videos)} videos from playlist')
        return videos

    except HttpError as e:
        logging.error(f'YouTube API HTTP error: {e}')
        return load_cache_file()
    except Exception as e:
        logging.error(f'YouTube API error: {e}')
        return load_cache_file()


def save_cache_file(videos):
    try:
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump({'videos': videos, 'timestamp': time.time()}, f)
    except Exception as e:
        logging.error(f'Failed to write cache: {e}')


def load_cache_file():
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('videos', [])
    except Exception as e:
        logging.error(f'Failed to read cache: {e}')
    return []


def get_videos():
    global _video_cache, _cache_timestamp
    now = time.time()
    if _video_cache and (now - _cache_timestamp) < CACHE_TTL:
        return _video_cache
    videos = fetch_playlist_videos()
    if videos:
        _video_cache = videos
        _cache_timestamp = now
    elif not _video_cache:
        _video_cache = load_cache_file()
    return _video_cache


# Warm cache on startup
try:
    get_videos()
except Exception as e:
    logging.error(f'Startup cache warm failed: {e}')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/contact')
def contact():
    return render_template('contact.html')


@app.route('/api/videos')
def api_videos():
    return jsonify(get_videos())


@app.route('/api/refresh')
def api_refresh():
    global _video_cache, _cache_timestamp
    _cache_timestamp = 0  # Force re-fetch
    videos = fetch_playlist_videos()
    _video_cache = videos
    _cache_timestamp = time.time()
    return jsonify({'status': 'ok', 'count': len(videos)})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
