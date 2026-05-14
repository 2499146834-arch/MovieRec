"""Pre-fetch TMDB movie posters for popular movies. Caches locally."""
import json, os, sys, time, urllib.request, urllib.parse, hashlib

# Fix Unicode output on Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

APP_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC = os.path.join(APP_DIR, "static")
POSTER_DIR = os.path.join(STATIC, "posters")
os.makedirs(POSTER_DIR, exist_ok=True)

API_KEY = "2dca580c2a14b55200e784d157207b4d"
TMDB_SEARCH = "https://api.themoviedb.org/3/search/movie"
TMDB_IMAGE = "https://image.tmdb.org/t/p/w342"  # Larger posters
TMDB_BACKDROP = "https://image.tmdb.org/t/p/w780"  # Backdrop for hero

with open(os.path.join(STATIC, "app_data.json"), "r", encoding="utf-8") as f:
    data = json.load(f)

movies = data["movies"]
popularity = {int(k): v for k, v in data["movie_popularity"].items()}

# Sort by popularity, fetch top N
movies_sorted = sorted(movies, key=lambda m: popularity.get(m["item_idx"], 0), reverse=True)
target = movies_sorted  # All movies

poster_map = {}
# Load existing cache
cache_file = os.path.join(STATIC, "poster_cache.json")
if os.path.exists(cache_file):
    with open(cache_file, "r") as f:
        poster_map = json.load(f)

new_count = 0
for i, m in enumerate(target):
    mid = str(m["movie_id"])
    if mid in poster_map and poster_map[mid]:
        continue

    # Search TMDB
    title = m["title"].rsplit("(", 1)[0].strip()
    year = str(m.get("year", ""))
    params = urllib.parse.urlencode({
        "api_key": API_KEY,
        "query": title,
        "year": year if year and year != "0" else "",
    })
    try:
        req = urllib.request.urlopen(f"{TMDB_SEARCH}?{params}", timeout=10)
        results = json.loads(req.read()).get("results", [])
        if results:
            poster_path = results[0].get("poster_path")
            if poster_path:
                img_url = f"{TMDB_IMAGE}{poster_path}"
                img_data = urllib.request.urlopen(img_url, timeout=10).read()
                with open(os.path.join(POSTER_DIR, f"{mid}.jpg"), "wb") as f:
                    f.write(img_data)
                poster_map[mid] = poster_path
                new_count += 1

                # Also download backdrop if available
                backdrop_path = results[0].get("backdrop_path")
                if backdrop_path:
                    try:
                        bg_url = f"{TMDB_BACKDROP}{backdrop_path}"
                        bg_data = urllib.request.urlopen(bg_url, timeout=10).read()
                        with open(os.path.join(POSTER_DIR, f"{mid}_bg.jpg"), "wb") as f:
                            f.write(bg_data)
                    except Exception:
                        pass

                print(f"  [{i+1}/{len(target)}] {title} ({year}) OK")
        time.sleep(0.15)
    except Exception as e:
        poster_map[mid] = ""
        print(f"  [{i+1}/{len(target)}] {title} FAIL: {e}")
        time.sleep(0.5)

# Save cache
with open(cache_file, "w") as f:
    json.dump(poster_map, f)
print(f"\nDone! New posters: {new_count}, Total cached: {sum(1 for v in poster_map.values() if v)}")
