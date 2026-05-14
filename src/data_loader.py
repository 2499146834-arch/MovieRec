"""Data loading, preprocessing, and train/test splitting."""

import os
import zipfile
import urllib.request
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
from sklearn.model_selection import train_test_split
import warnings
warnings.filterwarnings("ignore")

from .config import (
    ML1M_URL, ML1M_DIR, ML1M_ZIP, RANDOM_SEED,
    TEST_RATIO, MIN_USER_RATINGS, RATING_SCALE,
)


def download_movielens_1m():
    """Download MovieLens 1M dataset if not present."""
    if os.path.exists(ML1M_DIR):
        print(f"  Dataset already exists at {ML1M_DIR}")
        return
    os.makedirs(ML1M_DIR, exist_ok=True)
    print(f"  Downloading MovieLens 1M from {ML1M_URL} ...")
    urllib.request.urlretrieve(ML1M_URL, ML1M_ZIP)
    print("  Extracting ...")
    with zipfile.ZipFile(ML1M_ZIP, "r") as zf:
        zf.extractall(os.path.dirname(ML1M_DIR))
    os.remove(ML1M_ZIP)
    print("  Done.")


def load_ratings():
    """Load ratings from MovieLens 1M dataset.

    Returns:
        ratings_df: DataFrame with columns [userId, movieId, rating, timestamp]
    """
    ratings_path = os.path.join(ML1M_DIR, "ratings.dat")
    if not os.path.exists(ratings_path):
        download_movielens_1m()

    ratings = pd.read_csv(
        ratings_path,
        sep="::",
        engine="python",
        names=["userId", "movieId", "rating", "timestamp"],
    )
    return ratings


def load_movies():
    """Load movie metadata."""
    movies_path = os.path.join(ML1M_DIR, "movies.dat")
    if not os.path.exists(movies_path):
        download_movielens_1m()

    movies = pd.read_csv(
        movies_path,
        sep="::",
        engine="python",
        names=["movieId", "title", "genres"],
        encoding="latin-1",
    )
    return movies


def get_data_statistics(ratings_df):
    """Compute comprehensive data statistics.

    Returns:
        dict with keys: n_users, n_movies, n_ratings, sparsity_pct,
                        avg_ratings_per_user, avg_ratings_per_movie,
                        rating_mean, rating_std, rating_skew,
                        median_user_ratings, min_user_ratings, max_user_ratings
    """
    n_users = ratings_df["userId"].nunique()
    n_movies = ratings_df["movieId"].nunique()
    n_ratings = len(ratings_df)
    total_cells = n_users * n_movies
    sparsity_pct = 100 * (1 - n_ratings / total_cells)

    user_counts = ratings_df.groupby("userId").size()

    stats = {
        "n_users": n_users,
        "n_movies": n_movies,
        "n_ratings": n_ratings,
        "total_possible_pairs": total_cells,
        "sparsity_pct": sparsity_pct,
        "observed_pct": 100 - sparsity_pct,
        "avg_ratings_per_user": user_counts.mean(),
        "median_ratings_per_user": user_counts.median(),
        "min_ratings_per_user": user_counts.min(),
        "max_ratings_per_user": user_counts.max(),
        "rating_mean": ratings_df["rating"].mean(),
        "rating_std": ratings_df["rating"].std(),
        "rating_skew": ratings_df["rating"].skew(),
        "rating_distribution": ratings_df["rating"].value_counts().sort_index().to_dict(),
    }
    return stats


def build_user_item_matrix(ratings_df):
    """Build sparse user-item rating matrix.

    Returns:
        matrix: csr_matrix of shape (n_users, n_items)
        user_id_map: dict {original_user_id: matrix_index}
        item_id_map: dict {original_movie_id: matrix_index}
        reverse_user_map: dict {matrix_index: original_user_id}
        reverse_item_map: dict {matrix_index: original_movie_id}
    """
    users = sorted(ratings_df["userId"].unique())
    items = sorted(ratings_df["movieId"].unique())

    user_id_map = {uid: i for i, uid in enumerate(users)}
    item_id_map = {mid: i for i, mid in enumerate(items)}
    reverse_user_map = {i: uid for uid, i in user_id_map.items()}
    reverse_item_map = {i: mid for mid, i in item_id_map.items()}

    row_indices = ratings_df["userId"].map(user_id_map).values
    col_indices = ratings_df["movieId"].map(item_id_map).values
    values = ratings_df["rating"].values.astype(np.float64)

    matrix = csr_matrix(
        (values, (row_indices, col_indices)),
        shape=(len(users), len(items)),
    )
    return matrix, user_id_map, item_id_map, reverse_user_map, reverse_item_map


def split_train_test(ratings_df, by="user"):
    """Split ratings into train/test sets.

    'user' mode: for each user, hold out TEST_RATIO of latest ratings.
    'random' mode: global random 80/20 split.

    Returns:
        train_df, test_df
    """
    if by == "random":
        train_df, test_df = train_test_split(
            ratings_df, test_size=TEST_RATIO, random_state=RANDOM_SEED
        )
        return train_df, test_df

    # 'user' mode: chronological hold-out per user
    train_rows = []
    test_rows = []

    for uid, grp in ratings_df.groupby("userId"):
        grp = grp.sort_values("timestamp")
        # Only include users with sufficient ratings
        if len(grp) < MIN_USER_RATINGS:
            train_rows.append(grp)
            continue

        n_test = max(1, int(len(grp) * TEST_RATIO))
        test_rows.append(grp.iloc[-n_test:])
        train_rows.append(grp.iloc[:-n_test])

    train_df = pd.concat(train_rows, ignore_index=True)
    test_df = pd.concat(test_rows, ignore_index=True)
    return train_df, test_df


def print_data_summary(ratings_df, train_df, test_df):
    """Print a clean data summary for the report."""
    stats = get_data_statistics(ratings_df)

    print("=" * 60)
    print("DATASET SUMMARY")
    print("=" * 60)
    print(f"  Total users:              {stats['n_users']:,}")
    print(f"  Total movies:             {stats['n_movies']:,}")
    print(f"  Total ratings:            {stats['n_ratings']:,}")
    print(f"  Total possible pairs:     {stats['total_possible_pairs']:,}")
    print(f"  Matrix sparsity:          {stats['sparsity_pct']:.4f}%")
    print(f"  Observed interactions:    {stats['observed_pct']:.4f}%")
    print(f"  Avg ratings per user:     {stats['avg_ratings_per_user']:.1f}")
    print(f"  Median ratings per user:  {stats['median_ratings_per_user']:.0f}")
    print(f"  Min/Max per user:         {stats['min_ratings_per_user']} / {stats['max_ratings_per_user']}")
    print(f"  Rating mean:              {stats['rating_mean']:.3f}")
    print(f"  Rating std:               {stats['rating_std']:.3f}")
    print(f"  Rating skew:              {stats['rating_skew']:.3f}")
    print(f"  Train ratings:            {len(train_df):,}")
    print(f"  Test ratings:             {len(test_df):,}")
    print(f"  Test users:               {test_df['userId'].nunique():,}")
    print(f"  Avg test ratings / user:  {len(test_df) / test_df['userId'].nunique():.1f}")
    print("-" * 60)
    print("  Rating distribution (1-5):")
    for r in range(1, 6):
        count = stats["rating_distribution"].get(r, 0)
        pct = 100 * count / stats["n_ratings"]
        bar = "#" * int(pct)
        print(f"    {r}: {count:>8,} ({pct:5.1f}%) {bar}")
    print("=" * 60)
    print()

    return stats
