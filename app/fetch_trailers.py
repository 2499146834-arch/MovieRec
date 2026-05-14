"""Fetch YouTube trailer IDs from TMDB for top movies."""
import json, os, sys, time, urllib.request, urllib.parse

# Fix Unicode output on Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

APP_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC = os.path.join(APP_DIR, "static")
API_KEY = "2dca580c2a14b55200e784d157207b4d"

with open(os.path.join(STATIC, "app_data.json"), "r", encoding="utf-8") as f:
    data = json.load(f)

movies = data["movies"]
popularity = {int(k): v for k, v in data["movie_popularity"].items()}
movies_sorted = sorted(movies, key=lambda m: popularity.get(m["item_idx"], 0), reverse=True)
target = movies_sorted[:1200]  # Top 1200

trailer_map = {}
cache_file = os.path.join(STATIC, "trailer_cache.json")
if os.path.exists(cache_file):
    with open(cache_file, "r") as f:
        trailer_map = json.load(f)

new_count = 0
for i, m in enumerate(target):
    mid = str(m["movie_id"])
    if mid in trailer_map:
        continue

    title = m["title"].rsplit("(", 1)[0].strip()
    year = str(m.get("year", ""))

    # Step 1: search TMDB for the movie
    search_params = urllib.parse.urlencode({
        "api_key": API_KEY, "query": title, "year": year if year and year != "0" else "",
    })
    try:
        req = urllib.request.urlopen(f"https://api.themoviedb.org/3/search/movie?{search_params}", timeout=10)
        results = json.loads(req.read()).get("results", [])
        if not results:
            trailer_map[mid] = ""
            continue

        tmdb_id = results[0]["id"]

        # Step 2: get videos for this movie
        vid_url = f"https://api.themoviedb.org/3/movie/{tmdb_id}/videos?api_key={API_KEY}"
        vid_req = urllib.request.urlopen(vid_url, timeout=10)
        videos = json.loads(vid_req.read()).get("results", [])

        # Find YouTube trailer
        trailer_key = ""
        for v in videos:
            if v["site"] == "YouTube" and v["type"] == "Trailer":
                trailer_key = v["key"]
                break
        # Fallback: any YouTube video
        if not trailer_key:
            for v in videos:
                if v["site"] == "YouTube":
                    trailer_key = v["key"]
                    break

        trailer_map[mid] = trailer_key
        if trailer_key:
            new_count += 1
            print(f"  [{i+1}/{len(target)}] {title} ({year}) -> youtube.com/watch?v={trailer_key}")
        else:
            print(f"  [{i+1}/{len(target)}] {title} ({year}) -> no trailer found")

        time.sleep(0.1)
    except Exception as e:
        trailer_map[mid] = ""
        print(f"  [{i+1}/{len(target)}] {title} FAIL: {e}")
        time.sleep(0.5)

with open(cache_file, "w") as f:
    json.dump(trailer_map, f)
print(f"\nDone! Trailers: {sum(1 for v in trailer_map.values() if v)}/{len(trailer_map)}")
