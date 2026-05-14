"""Baseline recommendation models for comparison."""

import numpy as np
from scipy.sparse import csr_matrix
from collections import Counter


class GlobalMeanPredictor:
    """Predict global average rating for all items."""

    def __init__(self):
        self.global_mean = None

    def fit(self, train_matrix):
        """Compute global mean from non-zero entries."""
        self.global_mean = train_matrix.data.mean()

    def predict(self, user_idx, item_idx):
        return self.global_mean

    def predict_batch(self, user_ids, item_ids):
        return np.full(len(user_ids), self.global_mean)

    # GlobalMean has no recommend() - not meaningful without item info


class UserMeanPredictor:
    """Predict user's average rating for all items."""

    def __init__(self):
        self.user_means = None
        self.global_mean = None

    def fit(self, train_matrix):
        n_users = train_matrix.shape[0]
        self.global_mean = train_matrix.data.mean()
        self.user_means = np.zeros(n_users)
        for u in range(n_users):
            row = train_matrix[u].data
            self.user_means[u] = row.mean() if len(row) > 0 else self.global_mean

    def predict(self, user_idx, item_idx):
        return self.user_means[user_idx]

    def predict_batch(self, user_ids, item_ids):
        return self.user_means[user_ids]


class ItemMeanPredictor:
    """Predict item's average rating."""

    def __init__(self):
        self.item_means = None
        self.global_mean = None

    def fit(self, train_matrix):
        n_items = train_matrix.shape[1]
        self.global_mean = train_matrix.data.mean()
        self.item_means = np.zeros(n_items)
        train_csc = train_matrix.tocsc()
        for j in range(n_items):
            col = train_csc[:, j].data
            self.item_means[j] = col.mean() if len(col) > 0 else self.global_mean

    def predict(self, user_idx, item_idx):
        return self.item_means[item_idx]

    def predict_batch(self, user_ids, item_ids):
        return self.item_means[item_ids]


class MostPopular:
    """Recommend most popular items (by rating count), non-personalized."""

    def __init__(self):
        self.item_popularity = None  # sorted list of item indices by popularity
        self.item_mean_ratings = None

    def fit(self, train_matrix):
        n_items = train_matrix.shape[1]
        popularity = []
        item_mean_ratings = np.zeros(n_items)
        train_csc = train_matrix.tocsc()
        global_mean = train_matrix.data.mean()

        for j in range(n_items):
            col = train_csc[:, j].data
            pop = len(col)
            popularity.append(pop)
            item_mean_ratings[j] = col.mean() if pop > 0 else global_mean

        popularity = np.array(popularity)
        self.item_popularity = np.argsort(popularity)[::-1]  # descending
        self.item_mean_ratings = item_mean_ratings

    def recommend(self, user_idx, K=10, exclude_train_items=None):
        """Recommend top-K most popular items, excluding items user has already rated."""
        if exclude_train_items is not None:
            rated_set = set(exclude_train_items)
            candidates = [i for i in self.item_popularity if i not in rated_set]
        else:
            candidates = self.item_popularity

        return candidates[:K]

    def predict(self, user_idx, item_idx):
        return self.item_mean_ratings[item_idx]

    def predict_batch(self, user_ids, item_ids):
        return self.item_mean_ratings[item_ids]
