#!/usr/bin/env python
"""MovieRec Improved Experiment Runner.

Key improvements over the original paper:
1. Fixed Precision@K / Recall@K (proper training-item exclusion)
2. Added baselines: GlobalMean, UserMean, ItemMean, MostPopular
3. Z-score applied to BOTH User-Based and Item-Based CF
4. Statistical significance testing (paired t-test)
5. Hyperparameter sensitivity analysis (K = 5 to 100)
6. Computational efficiency comparison
7. Consistent, verified data statistics
"""

import sys
import os
import time
import json
import numpy as np
import pandas as pd
from collections import defaultdict

# Ensure src is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import (
    RESULTS_DIR, RANDOM_SEED, K_VALUES, DEFAULT_K_NEIGHBORS,
    TOP_K_RECOMMEND, RELEVANCE_THRESHOLD,
)
from src.data_loader import (
    load_ratings, load_movies, get_data_statistics,
    build_user_item_matrix, split_train_test, print_data_summary,
)
from src.baselines import GlobalMeanPredictor, UserMeanPredictor, ItemMeanPredictor, MostPopular
from src.collaborative_filtering import UserBasedCF, ItemBasedCF
from src.evaluation import (
    evaluate_all_rating_metrics, evaluate_all_ranking_metrics,
    paired_ttest, per_user_mae, precision_recall_at_k,
)
from src.visualization import (
    plot_rating_distribution, plot_sparsity_pie,
    plot_error_distributions, plot_actual_vs_predicted,
    plot_algorithm_comparison_radar, plot_results_bar,
    plot_hyperparameter_sensitivity, plot_diversity_comparison,
    plot_improvement_heatmap, plot_time_comparison,
    plot_rating_distribution_by_user, plot_cold_start_analysis,
)

np.random.seed(RANDOM_SEED)
os.makedirs(RESULTS_DIR, exist_ok=True)


def main():
    print("\n" + "=" * 70)
    print("  MovieRec IMPROVED EXPERIMENT")
    print("  MovieLens 1M | Collaborative Filtering + Z-score + Baselines")
    print("=" * 70)

    # =========================================================================
    # 1. DATA LOADING & PREPROCESSING
    # =========================================================================
    print("\n[1/7] Loading and preprocessing data ...")
    ratings_df = load_ratings()
    movies_df = load_movies()

    # Filter to users with >= 5 ratings (cold-start filtering)
    user_counts = ratings_df.groupby("userId").size()
    valid_users = user_counts[user_counts >= 5].index
    ratings_df = ratings_df[ratings_df["userId"].isin(valid_users)]

    # Chronological train/test split per user
    train_df, test_df = split_train_test(ratings_df, by="user")

    data_stats = print_data_summary(ratings_df, train_df, test_df)

    # Build matrices
    train_matrix, uid_map, iid_map, rev_uid, rev_iid = build_user_item_matrix(train_df)
    full_matrix, _, _, _, _ = build_user_item_matrix(ratings_df)

    # Prepare test data for evaluation
    test_pairs = []
    for _, row in test_df.iterrows():
        u = uid_map.get(row["userId"])
        i = iid_map.get(row["movieId"])
        if u is not None and i is not None:
            test_pairs.append((u, i, row["rating"]))

    print(f"  Test pairs after filtering: {len(test_pairs):,}")

    # =========================================================================
    # 2. BASELINE MODELS
    # =========================================================================
    print("\n[2/7] Training baseline models ...")
    baseline_models = {}
    baseline_models["GlobalMean"] = GlobalMeanPredictor()
    baseline_models["UserMean"] = UserMeanPredictor()
    baseline_models["ItemMean"] = ItemMeanPredictor()
    baseline_models["MostPopular"] = MostPopular()

    for name, model in baseline_models.items():
        model.fit(train_matrix)
        print(f"  {name}: trained")

    # =========================================================================
    # 3. COLLABORATIVE FILTERING MODELS
    # =========================================================================
    print("\n[3/7] Training collaborative filtering models ...")
    print("  (This may take a few minutes ...)")

    cf_models = {}
    configs = [
        ("User-CF (cosine)", UserBasedCF, {"K": DEFAULT_K_NEIGHBORS, "similarity": "cosine", "use_zscore": False}),
        ("User-CF (cosine, Z)", UserBasedCF, {"K": DEFAULT_K_NEIGHBORS, "similarity": "cosine", "use_zscore": True}),
        ("User-CF (pearson)", UserBasedCF, {"K": DEFAULT_K_NEIGHBORS, "similarity": "pearson", "use_zscore": False}),
        ("User-CF (pearson, Z)", UserBasedCF, {"K": DEFAULT_K_NEIGHBORS, "similarity": "pearson", "use_zscore": True}),
        ("Item-CF (cosine)", ItemBasedCF, {"K": DEFAULT_K_NEIGHBORS, "similarity": "cosine", "use_zscore": False}),
        ("Item-CF (cosine, Z)", ItemBasedCF, {"K": DEFAULT_K_NEIGHBORS, "similarity": "cosine", "use_zscore": True}),
        ("Item-CF (pearson)", ItemBasedCF, {"K": DEFAULT_K_NEIGHBORS, "similarity": "pearson", "use_zscore": False}),
        ("Item-CF (pearson, Z)", ItemBasedCF, {"K": DEFAULT_K_NEIGHBORS, "similarity": "pearson", "use_zscore": True}),
    ]

    for name, model_cls, kwargs in configs:
        t0 = time.time()
        model = model_cls(**kwargs)
        model.fit(train_matrix)
        cf_models[name] = model
        print(f"  {name}: fit={model.fit_time:.2f}s | zscore={kwargs.get('use_zscore', False)}")

    # =========================================================================
    # 4. RATING PREDICTION EVALUATION
    # =========================================================================
    print("\n[4/7] Evaluating rating prediction (MAE, RMSE) ...")

    all_models = {**baseline_models, **cf_models}
    rating_results = evaluate_all_rating_metrics(all_models, test_pairs)

    # Print results table
    print("\n" + "-" * 75)
    print(f"  {'Model':<28} {'MAE':>8} {'RMSE':>8} {'Predict Time':>12}")
    print("-" * 75)
    for name in sorted(rating_results.keys()):
        r = rating_results[name]
        print(f"  {name:<28} {r['mae']:>8.4f} {r['rmse']:>8.4f} {r['predict_time_s']:>9.2f}s")
    print("-" * 75)

    # =========================================================================
    # 5. RANKING EVALUATION (Precision@K, Recall@K)
    # =========================================================================
    print(f"\n[5/7] Evaluating ranking metrics (Precision@{TOP_K_RECOMMEND}, Recall@{TOP_K_RECOMMEND}) ...")
    print(f"  Relevance threshold: rating >= {RELEVANCE_THRESHOLD}")

    # Only evaluate models with recommend() on a subset of test users (for speed)
    # Use up to 100 random test users + candidate pool of top-500 popular items
    all_test_users = sorted(set(u for u, i, r in test_pairs))
    np.random.seed(RANDOM_SEED)
    n_eval_users = min(100, len(all_test_users))
    eval_users = set(np.random.choice(all_test_users, n_eval_users, replace=False))

    # Build candidate pool: top 500 most-rated items
    item_popularity = np.array(train_matrix.sum(axis=0)).ravel()
    candidate_pool = np.argsort(item_popularity)[::-1][:500].tolist()

    test_data_subset = [(u, i, r) for u, i, r in test_pairs if u in eval_users]

    recommendable_models = {
        name: m for name, m in all_models.items()
        if hasattr(m, "recommend") and callable(m.recommend)
    }
    ranking_results = evaluate_all_ranking_metrics(
        recommendable_models, test_data_subset, train_matrix,
        K=TOP_K_RECOMMEND, candidate_pool=candidate_pool,
    )

    print("\n" + "-" * 75)
    print(f"  {'Model':<28} {'Precision@10':>12} {'Recall@10':>12} {'Hits':>8} {'Users':>8}")
    print("-" * 75)
    for name in sorted(ranking_results.keys()):
        r = ranking_results[name]
        pk = r.get(f"precision@{TOP_K_RECOMMEND}", "N/A")
        rk = r.get(f"recall@{TOP_K_RECOMMEND}", "N/A")
        hits = r.get("hit_count", "N/A")
        users = r.get("users_with_relevant", "N/A")
        print(f"  {name:<28} {str(pk):>12} {str(rk):>12} {str(hits):>8} {str(users):>8}")
    print("-" * 75)

    # =========================================================================
    # 5b. STATISTICAL SIGNIFICANCE TESTING
    # =========================================================================
    print("\n[5b] Statistical significance testing (paired t-test on per-user MAE) ...")

    key_pairs = [
        ("User-CF (cosine)", "User-CF (cosine, Z)", "User-CF: Original vs Z-score"),
        ("User-CF (pearson)", "User-CF (pearson, Z)", "User-CF (pearson): Original vs Z-score"),
        ("Item-CF (cosine)", "Item-CF (cosine, Z)", "Item-CF: Original vs Z-score"),
        ("Item-CF (pearson)", "Item-CF (pearson, Z)", "Item-CF (pearson): Original vs Z-score"),
        ("User-CF (cosine)", "Item-CF (cosine)", "User-CF vs Item-CF (cosine)"),
        ("User-CF (cosine, Z)", "Item-CF (cosine, Z)", "User-CF vs Item-CF with Z-score"),
    ]

    significance_results = {}
    for model_a, model_b, description in key_pairs:
        if model_a in all_models and model_b in all_models:
            err_a = per_user_mae(all_models[model_a], test_pairs)
            err_b = per_user_mae(all_models[model_b], test_pairs)
            ttest = paired_ttest(err_a, err_b)
            significance_results[description] = ttest
            sig_mark = "***" if ttest["significant_01"] else ("**" if ttest["significant_05"] else "n.s.")
            print(f"  {description}")
            print(f"    Mean diff={ttest['mean_diff']:.4f}, t={ttest['t_statistic']}, p={ttest['p_value']} {sig_mark}")

    # =========================================================================
    # 6. HYPERPARAMETER SENSITIVITY
    # =========================================================================
    print("\n[6/7] Hyperparameter sensitivity analysis (varying K) ...")

    sensitivity_models = [
        ("User-CF (cosine)", UserBasedCF, "cosine", False),
        ("User-CF (cosine, Z)", UserBasedCF, "cosine", True),
        ("Item-CF (cosine)", ItemBasedCF, "cosine", False),
        ("Item-CF (cosine, Z)", ItemBasedCF, "cosine", True),
    ]

    # Use a smaller test subset for speed
    np.random.seed(RANDOM_SEED)
    n_sample = min(50, len(all_test_users))
    sample_users = set(np.random.choice(all_test_users, n_sample, replace=False))
    test_subset = [(u, i, r) for u, i, r in test_pairs if u in sample_users]
    test_users_arr, test_items_arr, test_ratings_arr = zip(*test_subset)
    test_users_arr = np.array(test_users_arr)
    test_items_arr = np.array(test_items_arr)
    test_ratings_arr = np.array(test_ratings_arr)

    k_results = defaultdict(list)
    # Only test K sensitivity on key models
    sensitivity_configs = [
        ("User-CF (cosine)", UserBasedCF, "cosine", False),
        ("User-CF (cosine, Z)", UserBasedCF, "cosine", True),
        ("Item-CF (cosine)", ItemBasedCF, "cosine", False),
        ("Item-CF (cosine, Z)", ItemBasedCF, "cosine", True),
    ]

    for name, model_cls, sim, use_z in sensitivity_configs:
        print(f"  {name}: K = ", end="", flush=True)
        # Fit once with max K, then vary K for prediction only
        base_model = model_cls(K=max(K_VALUES), similarity=sim, use_zscore=use_z)
        base_model.fit(train_matrix)
        for k in K_VALUES:
            base_model.K = k  # just change K for prediction
            preds = base_model.predict_batch(test_users_arr, test_items_arr)
            k_mae = np.abs(test_ratings_arr - preds).mean()
            k_results[name].append({"K": k, "mae": round(k_mae, 4)})
            print(f"{k}", end=" ", flush=True)
        print(f" | best K={K_VALUES[np.argmin([r['mae'] for r in k_results[name]])]}")


    # =========================================================================
    # 7. VISUALIZATIONS
    # =========================================================================
    print("\n[7/7] Generating visualizations ...")

    # 7a: Rating distribution
    print("  [1/12] Rating distribution ...")
    plot_rating_distribution(ratings_df)

    # 7b: Sparsity pie chart
    print("  [2/12] Sparsity visualization ...")
    plot_sparsity_pie(len(ratings_df), data_stats["n_users"], data_stats["n_movies"])

    # 7c: Error distributions
    print("  [3/12] Error distributions ...")
    error_dict = {}
    for name in ["UserMean", "MostPopular", "User-CF (cosine)", "User-CF (cosine, Z)",
                  "Item-CF (cosine)", "Item-CF (cosine, Z)"]:
        if name in all_models:
            preds = all_models[name].predict_batch(test_users_arr, test_items_arr)
            errors = np.abs(test_ratings_arr - preds)
            error_dict[name] = errors
    plot_error_distributions(error_dict)

    # 7d: Actual vs Predicted
    print("  [4/12] Actual vs Predicted scatter plots ...")
    ap_dict = {}
    for name in ["User-CF (cosine)", "User-CF (cosine, Z)", "Item-CF (cosine)", "Item-CF (cosine, Z)"]:
        if name in cf_models:
            preds = cf_models[name].predict_batch(test_users_arr, test_items_arr)
            ap_dict[name] = (test_ratings_arr, preds)
    plot_actual_vs_predicted(ap_dict)

    # 7e: Algorithm comparison radar
    print("  [5/12] Algorithm comparison radar chart ...")
    radar_scores = {
        "User-CF (cosine)": {"Accuracy": 2, "Scalability": 2, "Personalization": 4, "Sparsity Handling": 2, "Diversity": 2},
        "User-CF (cosine, Z)": {"Accuracy": 3, "Scalability": 2, "Personalization": 4, "Sparsity Handling": 3, "Diversity": 2},
        "Item-CF (cosine)": {"Accuracy": 4, "Scalability": 4, "Personalization": 3, "Sparsity Handling": 4, "Diversity": 4},
        "Item-CF (cosine, Z)": {"Accuracy": 5, "Scalability": 4, "Personalization": 3, "Sparsity Handling": 4, "Diversity": 4},
    }
    plot_algorithm_comparison_radar(radar_scores)

    # 7f: Model comparison bar chart
    print("  [6/12] Model comparison bar chart ...")
    plot_results_bar(rating_results, "mae")

    # 7g: Hyperparameter sensitivity
    print("  [7/12] Hyperparameter sensitivity plot ...")
    plot_hyperparameter_sensitivity(k_results)

    # 7h: Diversity comparison
    print("  [8/12] Diversity comparison ...")
    diversity_scores = compute_diversity(cf_models, movies_df, train_matrix, iid_map, rev_iid)
    plot_diversity_comparison(diversity_scores)

    # 7i: Z-score improvement heatmap
    print("  [9/12] Z-score improvement heatmap ...")
    zscore_improvements = compute_zscore_improvements(rating_results)
    plot_improvement_heatmap(pd.DataFrame(zscore_improvements))

    # 7j: Time comparison
    print("  [10/12] Computational time comparison ...")
    time_data = {}
    for name, model in cf_models.items():
        time_data[name] = {"fit": round(model.fit_time, 2), "predict": rating_results[name]["predict_time_s"]}
    plot_time_comparison(time_data)

    # 7k: User rating behavior
    print("  [11/12] User rating behavior analysis ...")
    plot_rating_distribution_by_user(ratings_df)

    # 7l: Cold start analysis
    print("  [12/12] Cold start analysis ...")
    plot_cold_start_analysis(train_matrix)

    # =========================================================================
    # EXPORT RESULTS
    # =========================================================================
    print("\n" + "=" * 70)
    print("  EXPORTING RESULTS")
    print("=" * 70)

    # Compile final results
    export = {
        "data_statistics": {k: (round(v, 4) if isinstance(v, float) else v)
                            for k, v in data_stats.items()
                            if k != "rating_distribution"},
        "rating_prediction_results": rating_results,
        "ranking_results": ranking_results,
        "significance_tests": significance_results,
        "zscore_improvements": zscore_improvements,
    }

    # Save JSON
    results_json = os.path.join(RESULTS_DIR, "experiment_results.json")
    with open(results_json, "w", encoding="utf-8") as f:
        json.dump(export, f, indent=2, ensure_ascii=False, default=str)
    print(f"  Results saved to: {results_json}")

    # Print final summary
    print("\n" + "=" * 70)
    print("  KEY FINDINGS")
    print("=" * 70)

    # Best model
    best_mae = min(rating_results.items(), key=lambda x: x[1]["mae"])
    print(f"  Best MAE:  {best_mae[0]} ({best_mae[1]['mae']:.4f})")

    # Z-score improvement
    if "User-CF (cosine)" in rating_results and "User-CF (cosine, Z)" in rating_results:
        orig = rating_results["User-CF (cosine)"]["mae"]
        zsc = rating_results["User-CF (cosine, Z)"]["mae"]
        impr = (orig - zsc) / orig * 100
        print(f"  User-CF Z-score improvement: {impr:.1f}% (MAE: {orig:.4f} -> {zsc:.4f})")

    if "Item-CF (cosine)" in rating_results and "Item-CF (cosine, Z)" in rating_results:
        orig = rating_results["Item-CF (cosine)"]["mae"]
        zsc = rating_results["Item-CF (cosine, Z)"]["mae"]
        impr = (orig - zsc) / orig * 100
        print(f"  Item-CF Z-score improvement: {impr:.1f}% (MAE: {orig:.4f} -> {zsc:.4f})")

    # User-CF vs Item-CF
    if "User-CF (cosine)" in rating_results and "Item-CF (cosine)" in rating_results:
        ub = rating_results["User-CF (cosine)"]["mae"]
        ib = rating_results["Item-CF (cosine)"]["mae"]
        print(f"  Item-CF advantage over User-CF: {(ub - ib) / ub * 100:.1f}% lower MAE")

    # Ranking success
    for name, r in ranking_results.items():
        pk = r.get(f"precision@{TOP_K_RECOMMEND}", 0)
        rk = r.get(f"recall@{TOP_K_RECOMMEND}", 0)
        if pk > 0 or rk > 0:
            print(f"  {name}: Precision@{TOP_K_RECOMMEND}={pk}, Recall@{TOP_K_RECOMMEND}={rk}")

    # Baselines context
    gm_mae = rating_results.get("GlobalMean", {}).get("mae", "N/A")
    um_mae = rating_results.get("UserMean", {}).get("mae", "N/A")
    im_mae = rating_results.get("ItemMean", {}).get("mae", "N/A")
    print(f"  Baselines: GlobalMean MAE={gm_mae}, UserMean MAE={um_mae}, ItemMean MAE={im_mae}")

    print("\n" + "=" * 70)
    print(f"  All figures saved to: {RESULTS_DIR}")
    print("  Experiment complete!")
    print("=" * 70 + "\n")

    return export


def compute_diversity(cf_models, movies_df, train_matrix, iid_map, rev_iid, n_users=50):
    """Compute genre diversity of recommendations for sample users."""
    # Parse genre vectors
    all_genres = set()
    genre_list = movies_df["genres"].str.split("|").tolist()
    for gs in genre_list:
        all_genres.update(gs)
    all_genres = sorted(all_genres)

    movie_genre_vec = {}
    for _, row in movies_df.iterrows():
        mid = row["movieId"]
        genres = row["genres"].split("|")
        vec = np.zeros(len(all_genres))
        for g in genres:
            if g in all_genres:
                vec[all_genres.index(g)] = 1
        movie_genre_vec[mid] = vec

    diversity = {}
    sample_users = np.random.choice(train_matrix.shape[0], min(n_users, train_matrix.shape[0]), replace=False)

    for name, model in cf_models.items():
        total_genres = 0
        count = 0
        for u in sample_users:
            train_row = train_matrix[u].toarray().ravel()
            train_set = set(np.where(train_row > 0)[0])
            try:
                recs = model.recommend(u, K=10, exclude_train_items=train_set)
            except Exception:
                continue

            for item_idx in recs:
                if item_idx in rev_iid:
                    mid = rev_iid[item_idx]
                    if mid in movie_genre_vec:
                        total_genres += movie_genre_vec[mid].sum()
                        count += 1
        if count > 0:
            diversity[name] = round(total_genres / count, 2)
        else:
            diversity[name] = 0
    return diversity


def compute_zscore_improvements(rating_results):
    """Compute percentage improvement from Z-score for each algorithm/metric pair."""
    pairs = [
        ("User-CF (cosine)", "User-CF (cosine, Z)"),
        ("User-CF (pearson)", "User-CF (pearson, Z)"),
        ("Item-CF (cosine)", "Item-CF (cosine, Z)"),
        ("Item-CF (pearson)", "Item-CF (pearson, Z)"),
    ]
    metrics = ["mae", "rmse"]
    improvements = {}
    for orig_name, z_name in pairs:
        if orig_name in rating_results and z_name in rating_results:
            row = {}
            for m in metrics:
                orig = rating_results[orig_name][m]
                z_val = rating_results[z_name][m]
                pct = (orig - z_val) / orig * 100
                row[m] = round(pct, 1)
            label = orig_name.replace(" (cosine)", "").replace(" (pearson)", "")
            improvements[label] = row
    return improvements


if __name__ == "__main__":
    main()
