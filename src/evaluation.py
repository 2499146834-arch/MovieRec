"""Evaluation metrics and statistical testing.

Key fix vs original paper: Precision@K and Recall@K properly exclude
training items from candidate recommendations and use a test-set-only
evaluation with relevance threshold.
"""

import time
import numpy as np
from scipy import stats as scipy_stats
from .config import RELEVANCE_THRESHOLD, TOP_K_RECOMMEND


def mae(y_true, y_pred):
    """Mean Absolute Error."""
    return np.abs(y_true - y_pred).mean()


def rmse(y_true, y_pred):
    """Root Mean Square Error."""
    return np.sqrt(np.mean((y_true - y_pred) ** 2))


def evaluate_rating_predictions(y_true, y_pred):
    """Compute MAE and RMSE."""
    return {"mae": mae(y_true, y_pred), "rmse": rmse(y_true, y_pred)}


def precision_recall_at_k(model, test_data, train_matrix, K=TOP_K_RECOMMEND, candidate_pool=None):
    """Compute Precision@K and Recall@K with proper train-item exclusion.

    For each test user:
    - Generate K recommended items NOT in their training set
    - Count hits where recommended item appears in the user's test set
      with rating >= RELEVANCE_THRESHOLD

    Args:
        model: Trained model with .recommend() method
        test_data: list of (user_idx, item_idx, rating) tuples
        train_matrix: csr_matrix of training ratings
        K: number of recommendations
        candidate_pool: optional list of item indices to restrict search

    Returns:
        dict with precision, recall, hit_count, total_relevant, total_users
    """
    # Build per-user test set
    user_test_items = {}  # user_idx -> [(item_idx, rating)]
    user_test_relevant = {}  # user_idx -> [item_idx] (relevant items only)

    for u, i, r in test_data:
        if u not in user_test_items:
            user_test_items[u] = []
            user_test_relevant[u] = []
        user_test_items[u].append((i, r))
        if r >= RELEVANCE_THRESHOLD:
            user_test_relevant[u].append(i)

    test_users = list(user_test_items.keys())

    precisions = []
    recalls = []
    hit_count = 0
    total_relevant = 0
    total_users = len(test_users)
    total_preds = 0

    for u in test_users:
        # Get training items to exclude
        train_row = train_matrix[u].toarray().ravel()
        train_items = set(np.where(train_row > 0)[0])

        # Generate recommendations
        try:
            recs = model.recommend(u, K=K, exclude_train_items=train_items, candidate_pool=candidate_pool)
        except Exception:
            precisions.append(0.0)
            recalls.append(0.0)
            continue

        if recs is None or len(recs) == 0:
            precisions.append(0.0)
            if n_relevant > 0:
                recalls.append(0.0)
            continue

        test_relevant_set = set(user_test_relevant.get(u, []))
        n_relevant = len(test_relevant_set)

        if n_relevant == 0:
            # User has no relevant items in test set; skip recall
            total_users -= 1
            if len(recs) > 0:
                precisions.append(0.0)
            continue

        hits = len(set(recs) & test_relevant_set)
        hit_count += hits
        total_relevant += n_relevant
        total_preds += len(recs)

        precisions.append(hits / len(recs) if len(recs) > 0 else 0.0)
        recalls.append(hits / n_relevant)

    avg_precision = np.mean(precisions) if precisions else 0.0
    avg_recall = np.mean(recalls) if recalls else 0.0

    return {
        f"precision@{K}": round(avg_precision, 4),
        f"recall@{K}": round(avg_recall, 4),
        "hit_count": hit_count,
        "total_relevant": total_relevant,
        "users_with_relevant": total_users,
        "total_recommendations": total_preds,
    }


def paired_ttest(results_a, results_b):
    """Paired t-test for statistical significance.

    Args:
        results_a: array of per-user metrics for method A
        results_b: array of per-user metrics for method B

    Returns:
        dict with t_statistic, p_value, significant (bool), mean_diff
    """
    # Ensure same length for paired comparison
    min_len = min(len(results_a), len(results_b))
    a = np.array(results_a[:min_len])
    b = np.array(results_b[:min_len])

    t_stat, p_value = scipy_stats.ttest_rel(a, b)
    return {
        "t_statistic": round(t_stat, 4),
        "p_value": round(float(p_value), 6),
        "significant_05": bool(p_value < 0.05),
        "significant_01": bool(p_value < 0.01),
        "mean_diff": round(float(np.mean(a) - np.mean(b)), 4),
    }


def evaluate_all_rating_metrics(models_dict, test_pairs):
    """Evaluate all models on rating prediction.

    Args:
        models_dict: {name: model} where model has .predict_batch()
        test_pairs: list of (user_idx, item_idx, true_rating)

    Returns:
        dict: {model_name: {mae: ..., rmse: ...}}
    """
    users, items, true_ratings = zip(*test_pairs)
    users = np.array(users)
    items = np.array(items)
    true_ratings = np.array(true_ratings)

    results = {}
    for name, model in models_dict.items():
        t0 = time.time()
        preds = model.predict_batch(users, items)
        elapsed = time.time() - t0
        results[name] = {
            "mae": round(mae(true_ratings, preds), 4),
            "rmse": round(rmse(true_ratings, preds), 4),
            "predict_time_s": round(elapsed, 2),
        }
    return results


def evaluate_all_ranking_metrics(
    models_dict, test_data, train_matrix, K=TOP_K_RECOMMEND, candidate_pool=None,
):
    """Evaluate ranking metrics (Precision@K, Recall@K) for all models.

    Only evaluates models that have a .recommend() method.
    """
    results = {}
    for name, model in models_dict.items():
        if hasattr(model, "recommend") and callable(model.recommend):
            t0 = time.time()
            metrics = precision_recall_at_k(model, test_data, train_matrix, K=K, candidate_pool=candidate_pool)
            metrics["time_s"] = round(time.time() - t0, 2)
            results[name] = metrics
    return results


def per_user_mae(model, test_data):
    """Compute per-user MAE for statistical testing."""
    user_errors = {}
    for u, i, r in test_data:
        pred = model.predict(u, i)
        err = abs(r - pred)
        if u not in user_errors:
            user_errors[u] = []
        user_errors[u].append(err)
    return np.array([np.mean(errs) for errs in user_errors.values()])
