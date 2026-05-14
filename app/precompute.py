"""Precompute recommendation data and movie metadata for the web app."""

import sys, os, json, pickle, random
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd
from collections import Counter

from src.data_loader import load_ratings, load_movies, build_user_item_matrix, split_train_test
from src.collaborative_filtering import ItemBasedCF, UserBasedCF
from src.config import DATA_DIR

APP_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(APP_DIR, "static")
os.makedirs(STATIC_DIR, exist_ok=True)

random.seed(42)
np.random.seed(42)


def build():
    print("Loading data...")
    ratings_df = load_ratings()
    movies_df = load_movies()

    # Filter users with >= 5 ratings
    user_counts = ratings_df.groupby("userId").size()
    valid_users = user_counts[user_counts >= 5].index
    ratings_df = ratings_df[ratings_df["userId"].isin(valid_users)]

    # Train/test split
    train_df, test_df = split_train_test(ratings_df, by="user")
    train_matrix, uid_map, iid_map, rev_uid, rev_iid = build_user_item_matrix(train_df)

    # Train best models
    print("Training models...")
    np.random.seed(42)

    model_ub = UserBasedCF(K=30, similarity="cosine", use_zscore=True)
    model_ub.fit(train_matrix)

    model_ib = ItemBasedCF(K=50, similarity="cosine", use_zscore=True)
    model_ib.fit(train_matrix)

    model_ub_raw = UserBasedCF(K=30, similarity="cosine", use_zscore=False)
    model_ub_raw.fit(train_matrix)

    model_ib_raw = ItemBasedCF(K=20, similarity="cosine", use_zscore=False)
    model_ib_raw.fit(train_matrix)

    # Generate recommendations for sample users
    print("Generating recommendations...")
    all_user_indices = list(range(train_matrix.shape[0]))
    sample_users = sorted(random.sample(all_user_indices, min(50, len(all_user_indices))))

    recommendations = []
    for user_idx in sample_users:
        uid = rev_uid[user_idx]
        train_row = train_matrix[user_idx].toarray().ravel()
        train_items = set(np.where(train_row > 0)[0])

        # User-CF Z-score
        recs_ub_z = model_ub.recommend(user_idx, K=10, exclude_train_items=train_items, candidate_pool=list(range(train_matrix.shape[1]))[:2000])

        # Item-CF Z-score
        recs_ib_z = model_ib.recommend(user_idx, K=10, exclude_train_items=train_items, candidate_pool=list(range(train_matrix.shape[1]))[:2000])

        # User-CF raw
        recs_ub = model_ub_raw.recommend(user_idx, K=10, exclude_train_items=train_items, candidate_pool=list(range(train_matrix.shape[1]))[:2000])

        # Item-CF raw
        recs_ib = model_ib_raw.recommend(user_idx, K=10, exclude_train_items=train_items, candidate_pool=list(range(train_matrix.shape[1]))[:2000])

        # Get prediction scores
        scores_ub_z = [float(model_ub.predict(user_idx, i)) for i in recs_ub_z]
        scores_ib_z = [float(model_ib.predict(user_idx, i)) for i in recs_ib_z]

        # User's top-rated movies (for profile)
        rated = [(i, train_matrix[user_idx, i]) for i in range(train_matrix.shape[1]) if train_matrix[user_idx, i] > 0]
        rated.sort(key=lambda x: x[1], reverse=True)
        top_rated = [int(i) for i, r in rated[:5]]

        recommendations.append({
            "user_idx": int(user_idx),
            "user_id": int(uid),
            "num_ratings": len(rated),
            "top_rated_items": top_rated,
            "recs_user_cf_z": [int(i) for i in recs_ub_z],
            "scores_user_cf_z": [round(s, 3) for s in scores_ub_z],
            "recs_item_cf_z": [int(i) for i in recs_ib_z],
            "scores_item_cf_z": [round(s, 3) for s in scores_ib_z],
            "recs_user_cf": [int(i) for i in recs_ub],
            "recs_item_cf": [int(i) for i in recs_ib],
        })

    # Build movie catalog
    print("Building movie catalog...")
    movies_catalog = []
    for _, row in movies_df.iterrows():
        mid = row["movieId"]
        if mid in iid_map:
            movies_catalog.append({
                "movie_id": int(mid),
                "item_idx": int(iid_map[mid]),
                "title": row["title"],
                "genres": row["genres"].split("|"),
                "year": int(row["title"].split("(")[-1].replace(")", "")) if "(" in row["title"] else 0,
            })

    # Movie popularity
    movie_popularity = {}
    for j in range(train_matrix.shape[1]):
        movie_popularity[j] = int(train_matrix[:, j].nnz)

    # Genre stats
    genre_counter = Counter()
    for m in movies_catalog:
        for g in m["genres"]:
            genre_counter[g] += 1

    # Compute per-genre avg rating
    genre_ratings = {g: [] for g in genre_counter}
    for _, row in ratings_df.iterrows():
        mid = row["movieId"]
        if mid in iid_map:
            gs = movies_df[movies_df["movieId"] == mid]["genres"].values
            if len(gs) > 0:
                for g in gs[0].split("|"):
                    if g in genre_ratings:
                        genre_ratings[g].append(row["rating"])
    genre_avg_rating = {g: round(np.mean(rs), 2) for g, rs in genre_ratings.items() if rs}

    # Save all data
    data = {
        "movies": movies_catalog,
        "recommendations": recommendations,
        "movie_popularity": {str(k): v for k, v in movie_popularity.items()},
        "genre_stats": {
            "counts": dict(genre_counter.most_common()),
            "avg_rating": genre_avg_rating,
        },
        "n_users": train_matrix.shape[0],
        "n_items": train_matrix.shape[1],
    }

    out_path = os.path.join(STATIC_DIR, "app_data.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    print(f"Data saved: {out_path} ({os.path.getsize(out_path) / 1024:.0f} KB)")
    print("Done!")


if __name__ == "__main__":
    build()
