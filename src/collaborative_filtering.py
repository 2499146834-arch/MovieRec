"""User-Based and Item-Based Collaborative Filtering with Z-score optimization.

Optimized with vectorized prediction for Item-Based CF and efficient
neighborhood search for User-Based CF.
"""

import time
import numpy as np
from scipy.sparse import csr_matrix
from sklearn.metrics.pairwise import cosine_similarity
from .config import DEFAULT_K_NEIGHBORS


def _pearson_similarity(matrix, axis=0):
    """Compute Pearson correlation along given axis (0=user-user, 1=item-item)."""
    if hasattr(matrix, "toarray"):
        mat = matrix.toarray()
    else:
        mat = np.asarray(matrix)
    if axis == 1:
        mat = mat.T

    centered = np.zeros_like(mat)
    for i in range(mat.shape[0]):
        row = mat[i]
        mask = row > 0
        if mask.sum() > 1:
            centered[i][mask] = row[mask] - row[mask].mean()

    sim = cosine_similarity(centered)
    sim = np.nan_to_num(sim, nan=0.0, posinf=0.0, neginf=0.0)
    return sim


def _cosine_similarity_safe(matrix, axis=0):
    """Compute cosine similarity handling zero vectors."""
    if axis == 1:
        matrix = matrix.T
    if hasattr(matrix, "toarray"):
        mat = matrix.toarray()
    else:
        mat = np.asarray(matrix)
    sim = cosine_similarity(mat)
    sim = np.nan_to_num(sim, nan=0.0, posinf=0.0, neginf=0.0)
    return sim


def _compute_similarity(matrix, measure, axis=0):
    if measure == "cosine":
        return _cosine_similarity_safe(matrix, axis=axis)
    elif measure == "pearson":
        return _pearson_similarity(matrix, axis=axis)
    else:
        raise ValueError(f"Unknown similarity measure: {measure}")


def _zscore_normalize(train_matrix):
    """Apply Z-score normalization per user: z_ui = (r_ui - mu_u) / sigma_u."""
    n_users = train_matrix.shape[0]
    normalized = train_matrix.toarray().copy()
    user_means = np.zeros(n_users)
    user_stds = np.zeros(n_users)

    for u in range(n_users):
        row = normalized[u]
        mask = row > 0
        if mask.sum() > 1:
            mean = row[mask].mean()
            std = row[mask].std(ddof=1)
            user_means[u] = mean
            user_stds[u] = std
            if std > 1e-8:
                normalized[u][mask] = (row[mask] - mean) / std
            else:
                normalized[u][mask] = 0.0
        elif mask.sum() == 1:
            user_means[u] = row[mask][0]

    return csr_matrix(normalized), user_means, user_stds


class UserBasedCF:
    """User-Based Collaborative Filtering with optional Z-score normalization."""

    def __init__(self, K=DEFAULT_K_NEIGHBORS, similarity="cosine", use_zscore=False):
        self.K = K
        self.similarity = similarity
        self.use_zscore = use_zscore
        self.train_matrix = None
        self.user_similarity = None
        self.user_means = None
        self.user_stds = None
        self.n_users = 0
        self.n_items = 0
        self.global_mean = 0.0
        self.fit_time = 0.0
        # Cache column user indices for faster predict
        self._col_users = None  # list of arrays: for each item, which users rated it

    def fit(self, train_matrix):
        t0 = time.time()
        self.train_matrix = train_matrix.copy()
        self.n_users, self.n_items = train_matrix.shape
        self.global_mean = train_matrix.data.mean()

        if self.use_zscore:
            norm_matrix, self.user_means, self.user_stds = _zscore_normalize(train_matrix)
            self.user_similarity = _compute_similarity(norm_matrix, self.similarity, axis=0)
        else:
            self.user_means = np.full(self.n_users, self.global_mean)
            self.user_stds = np.ones(self.n_users)
            self.user_similarity = _compute_similarity(train_matrix, self.similarity, axis=0)

        # Precompute column indices for faster predict
        csc = train_matrix.tocsc()
        self._col_users = []
        for j in range(self.n_items):
            users = csc[:, j].indices
            self._col_users.append(users)

        self.fit_time = time.time() - t0

    def predict(self, user_idx, item_idx):
        """Predict rating for a single user-item pair."""
        rated_indices = self._col_users[item_idx]

        if len(rated_indices) == 0:
            return self.user_means[user_idx]

        ratings = self.train_matrix[rated_indices, item_idx].toarray().ravel()
        sims = self.user_similarity[user_idx][rated_indices]

        # Apply Z-score: convert to z-space BEFORE filtering
        if self.use_zscore:
            rater_means = self.user_means[rated_indices]
            rater_stds = self.user_stds[rated_indices]
            valid = rater_stds > 1e-8
            z_ratings = np.zeros_like(ratings)
            z_ratings[valid] = (ratings[valid] - rater_means[valid]) / rater_stds[valid]
            work_ratings = z_ratings
        else:
            work_ratings = ratings

        # Top K most similar users who rated this item
        if len(sims) > self.K:
            top_k = np.argpartition(sims, -self.K)[-self.K:]
            sims = sims[top_k]
            work_ratings = work_ratings[top_k]

        pos_mask = sims > 0
        if pos_mask.sum() == 0:
            return self.user_means[user_idx]

        sims = sims[pos_mask]
        work_ratings = work_ratings[pos_mask]

        pred = np.dot(sims, work_ratings) / sims.sum()

        # De-normalize from z-space
        if self.use_zscore:
            if self.user_stds[user_idx] > 1e-8:
                pred = pred * self.user_stds[user_idx] + self.user_means[user_idx]
            else:
                pred = self.user_means[user_idx]

        return np.clip(pred, 1, 5)

    def predict_batch(self, user_ids, item_ids):
        """Predict ratings for multiple user-item pairs (optimized, Z-score aware)."""
        preds = np.zeros(len(user_ids))
        # Group by item for efficiency
        pairs_by_item = {}
        for idx, (u, i) in enumerate(zip(user_ids, item_ids)):
            pairs_by_item.setdefault(i, []).append((idx, u))

        for item, pairs in pairs_by_item.items():
            rated_indices = self._col_users[item]
            if len(rated_indices) == 0:
                for idx, u in pairs:
                    preds[idx] = self.user_means[u]
                continue

            raw_ratings = self.train_matrix[rated_indices, item].toarray().ravel()

            # Pre-compute z-scored ratings for this item (same for all users)
            if self.use_zscore:
                rater_means = self.user_means[rated_indices]
                rater_stds = self.user_stds[rated_indices]
                valid = rater_stds > 1e-8
                work_ratings = np.zeros_like(raw_ratings)
                work_ratings[valid] = (raw_ratings[valid] - rater_means[valid]) / rater_stds[valid]
            else:
                work_ratings = raw_ratings

            for idx, u in pairs:
                sims = self.user_similarity[u][rated_indices]

                if len(sims) > self.K:
                    top_k = np.argpartition(sims, -self.K)[-self.K:]
                    s = sims[top_k]
                    r = work_ratings[top_k]
                else:
                    s = sims
                    r = work_ratings

                pos = s > 0
                if pos.sum() == 0:
                    preds[idx] = self.user_means[u]
                else:
                    pred = np.dot(s[pos], r[pos]) / s[pos].sum()
                    if self.use_zscore:
                        if self.user_stds[u] > 1e-8:
                            pred = pred * self.user_stds[u] + self.user_means[u]
                        else:
                            pred = self.user_means[u]
                    preds[idx] = np.clip(pred, 1, 5)

        return preds

    def recommend(self, user_idx, K=10, exclude_train_items=None, candidate_pool=None):
        """Generate top-K recommendations excluding already-rated items."""
        if exclude_train_items is None:
            train_row = self.train_matrix[user_idx].toarray().ravel()
            exclude_train_items = set(np.where(train_row > 0)[0])
        else:
            exclude_train_items = set(exclude_train_items)

        if candidate_pool is None:
            candidate_pool = range(self.n_items)

        # Batch-predict all candidates
        candidate_list = [i for i in candidate_pool if i not in exclude_train_items]
        if not candidate_list:
            return []

        preds = self.predict_batch(
            np.full(len(candidate_list), user_idx),
            np.array(candidate_list),
        )

        top_k = np.argsort(preds)[::-1][:K]
        return [candidate_list[i] for i in top_k]


class ItemBasedCF:
    """Item-Based Collaborative Filtering with optional Z-score normalization.

    Uses vectorized prediction for single-user recommendation.
    """

    def __init__(self, K=DEFAULT_K_NEIGHBORS, similarity="cosine", use_zscore=False):
        self.K = K
        self.similarity = similarity
        self.use_zscore = use_zscore
        self.train_matrix = None
        self.item_similarity = None
        self.user_means = None
        self.user_stds = None
        self.n_users = 0
        self.n_items = 0
        self.global_mean = 0.0
        self.fit_time = 0.0

    def fit(self, train_matrix):
        t0 = time.time()
        self.train_matrix = train_matrix.copy()
        self.n_users, self.n_items = train_matrix.shape
        self.global_mean = train_matrix.data.mean()

        if self.use_zscore:
            norm_matrix, self.user_means, self.user_stds = _zscore_normalize(train_matrix)
            self.item_similarity = _compute_similarity(norm_matrix, self.similarity, axis=1)
        else:
            self.user_means = np.full(self.n_users, self.global_mean)
            self.user_stds = np.ones(self.n_users)
            self.item_similarity = _compute_similarity(train_matrix, self.similarity, axis=1)

        # Clip negative similarities for cleaner weighted average
        self.item_similarity = np.maximum(self.item_similarity, 0)
        self.fit_time = time.time() - t0

    def predict(self, user_idx, item_idx):
        """Predict rating using item-item similarity."""
        row = self.train_matrix[user_idx]
        rated_indices = row.indices
        if len(rated_indices) == 0:
            return self.user_means[user_idx]

        ratings = row.data
        sims = self.item_similarity[item_idx][rated_indices]

        if len(sims) > self.K:
            top_k = np.argpartition(sims, -self.K)[-self.K:]
            sims = sims[top_k]
            ratings = ratings[top_k]

        pos = sims > 0
        if pos.sum() == 0:
            return ratings.mean()

        pred = np.dot(sims[pos], ratings[pos]) / sims[pos].sum()
        return np.clip(pred, 1, 5)

    def predict_batch(self, user_ids, item_ids):
        """Predict ratings for multiple user-item pairs.

        Groups by user for efficiency since item_similarity lookups are per-item but
        user's rated items are reused within the same user.
        """
        preds = np.zeros(len(user_ids))
        pairs_by_user = {}
        for idx, (u, i) in enumerate(zip(user_ids, item_ids)):
            pairs_by_user.setdefault(u, []).append((idx, i))

        for u, pairs in pairs_by_user.items():
            row = self.train_matrix[u]
            rated_indices = row.indices
            if len(rated_indices) == 0:
                for idx, _ in pairs:
                    preds[idx] = self.user_means[u]
                continue
            ratings = row.data

            for idx, item in pairs:
                sims = self.item_similarity[item][rated_indices]
                if len(sims) > self.K:
                    top_k = np.argpartition(sims, -self.K)[-self.K:]
                    s, r = sims[top_k], ratings[top_k]
                else:
                    s, r = sims, ratings

                pos = s > 0
                if pos.sum() == 0:
                    preds[idx] = ratings.mean()
                else:
                    preds[idx] = np.clip(np.dot(s[pos], r[pos]) / s[pos].sum(), 1, 5)

        return preds

    def predict_all_for_user(self, user_idx):
        """Vectorized prediction of ALL items for a single user.

        pred(u,i) = (sum_j sim(i,j) * r(u,j)) / (sum_j sim(i,j)) for all i
        This is a single sparse-dense matrix-vector product!
        """
        row = self.train_matrix[user_idx]
        if row.nnz == 0:
            return np.full(self.n_items, self.user_means[user_idx])

        # Weighted sum: (1 x n_items) = (1 x n_rated) @ (n_rated x n_items)
        rated_idx = row.indices
        ratings = row.data.astype(np.float64)
        weighted_sum = ratings @ self.item_similarity[rated_idx, :]

        # Normalization: sum of similarities for each target item
        sim_abs = self.item_similarity[rated_idx, :]
        norm = sim_abs.sum(axis=0)
        norm[norm == 0] = 1.0

        return np.clip(weighted_sum / norm, 1, 5)

    def recommend(self, user_idx, K=10, exclude_train_items=None, candidate_pool=None):
        """Generate top-K recommendations using vectorized prediction."""
        if exclude_train_items is None:
            train_row = self.train_matrix[user_idx].toarray().ravel()
            exclude_train_items = set(np.where(train_row > 0)[0])
        else:
            exclude_train_items = set(exclude_train_items)

        # Vectorized: compute predictions for ALL items at once
        all_preds = self.predict_all_for_user(user_idx)

        if candidate_pool is not None:
            # Score only candidates
            candidates = [i for i in candidate_pool if i not in exclude_train_items]
            if not candidates:
                return []
            scores = [(i, all_preds[i]) for i in candidates]
        else:
            # Score all unrated items
            scores = [(i, all_preds[i]) for i in range(self.n_items)
                      if i not in exclude_train_items]

        scores.sort(key=lambda x: x[1], reverse=True)
        return [item for item, _ in scores[:K]]
