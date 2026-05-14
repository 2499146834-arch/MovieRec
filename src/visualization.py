"""Visualization module for experiment results."""

import os
import numpy as np
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib.patches import FancyBboxPatch
import seaborn as sns

from .config import RESULTS_DIR, K_VALUES, TOP_K_RECOMMEND

# Style
plt.rcParams.update({
    "figure.dpi": 150,
    "savefig.dpi": 150,
    "savefig.bbox": "tight",
    "font.size": 11,
    "axes.titlesize": 13,
    "axes.labelsize": 12,
})
sns.set_palette("Set2")

os.makedirs(RESULTS_DIR, exist_ok=True)


def plot_rating_distribution(ratings_df, save=True):
    """Plot the distribution of ratings."""
    fig, ax = plt.subplots(figsize=(8, 5))
    counts = ratings_df["rating"].value_counts().sort_index()
    colors = sns.color_palette("Blues_r", len(counts))
    bars = ax.bar(counts.index, counts.values, color=colors, edgecolor="white", linewidth=0.8)

    for bar, count in zip(bars, counts.values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 500,
                f"{count:,}", ha="center", va="bottom", fontsize=9)

    ax.set_xlabel("Rating")
    ax.set_ylabel("Count")
    ax.set_title("Distribution of Movie Ratings (MovieLens 1M)")
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: f"{x:,.0f}"))

    if save:
        fig.savefig(os.path.join(RESULTS_DIR, "01_rating_distribution.png"))
    plt.close(fig)


def plot_sparsity_pie(n_ratings, n_users, n_items, save=True):
    """Pie chart showing matrix sparsity."""
    total = n_users * n_items
    sparsity = total - n_ratings

    fig, ax = plt.subplots(figsize=(7, 7))
    sizes = [n_ratings, sparsity]
    labels = [f"Observed\n({n_ratings:,} ratings)", f"Sparse\n({sparsity:,} cells)"]
    colors = ["#4CAF50", "#E0E0E0"]
    explode = (0.05, 0)

    wedges, texts, autotexts = ax.pie(
        sizes, explode=explode, labels=labels, colors=colors,
        autopct="%1.2f%%", startangle=140,
        textprops={"fontsize": 10}
    )
    for at in autotexts:
        at.set_fontweight("bold")
    ax.set_title(f"User-Item Interaction Matrix Sparsity\n"
                 f"({n_users:,} users x {n_items:,} items = {total:,} cells)")

    if save:
        fig.savefig(os.path.join(RESULTS_DIR, "02_sparsity_pie.png"))
    plt.close(fig)


def plot_error_distributions(errors_dict, save=True):
    """Histogram of prediction errors for each model."""
    n = len(errors_dict)
    fig, axes = plt.subplots(1, n, figsize=(5 * n, 4), sharey=True)
    if n == 1:
        axes = [axes]

    for ax, (name, errors) in zip(axes, errors_dict.items()):
        ax.hist(errors, bins=50, color="#4CAF50", edgecolor="white", alpha=0.8, density=True)
        ax.axvline(np.mean(errors), color="red", linestyle="--", linewidth=2,
                   label=f"Mean={np.mean(errors):.3f}")
        ax.axvline(np.median(errors), color="orange", linestyle="--", linewidth=2,
                   label=f"Median={np.median(errors):.3f}")
        ax.set_xlabel("Prediction Error (|Actual - Predicted|)")
        ax.set_title(f"Error Distribution: {name}")
        ax.legend(fontsize=8)

    fig.suptitle("Prediction Error Distribution Comparison", y=1.02)

    if save:
        fig.savefig(os.path.join(RESULTS_DIR, "03_error_distributions.png"))
    plt.close(fig)


def plot_actual_vs_predicted(actual_pred_dict, save=True):
    """Scatter plots of actual vs predicted ratings."""
    n = len(actual_pred_dict)
    fig, axes = plt.subplots(1, n, figsize=(5 * n, 4.5), sharey=True, sharex=True)
    if n == 1:
        axes = [axes]

    for ax, (name, (actual, predicted)) in zip(axes, actual_pred_dict.items()):
        ax.scatter(actual, predicted, alpha=0.03, s=1, color="#2196F3", rasterized=True)
        ax.plot([1, 5], [1, 5], "r--", linewidth=1.5, label="Perfect Prediction")
        ax.set_xlabel("Actual Rating")
        ax.set_ylabel("Predicted Rating")
        ax.set_title(name)
        ax.set_xlim(0.5, 5.5)
        ax.set_ylim(0.5, 5.5)
        ax.legend(fontsize=8)

    fig.suptitle("Actual vs Predicted Ratings", y=1.02)

    if save:
        fig.savefig(os.path.join(RESULTS_DIR, "04_actual_vs_predicted.png"), dpi=150)
    plt.close(fig)


def plot_algorithm_comparison_radar(scores_dict, save=True):
    """Radar chart comparing algorithms on multiple dimensions."""
    categories = list(next(iter(scores_dict.values())).keys())
    N = len(categories)
    angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))

    for name, scores in scores_dict.items():
        values = [scores[c] for c in categories]
        values += values[:1]
        ax.fill(angles, values, alpha=0.15)
        ax.plot(angles, values, linewidth=2, label=name, marker="o", markersize=6)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, fontsize=10)
    ax.set_ylim(0, 5)
    ax.set_yticks([1, 2, 3, 4, 5])
    ax.set_yticklabels(["1", "2", "3", "4", "5"], fontsize=8)
    ax.set_title("Algorithm Strengths & Weaknesses Comparison", pad=20)
    ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1))

    if save:
        fig.savefig(os.path.join(RESULTS_DIR, "05_algorithm_radar.png"))
    plt.close(fig)


def plot_results_bar(results_dict, metric="mae", save=True):
    """Horizontal bar chart comparing all models on one metric."""
    names = list(results_dict.keys())
    values = [results_dict[n][metric] for n in names]

    # Sort by value
    sorted_idx = np.argsort(values)
    names = [names[i] for i in sorted_idx]
    values = [values[i] for i in sorted_idx]

    fig, ax = plt.subplots(figsize=(10, len(names) * 0.6 + 1))
    colors = sns.color_palette("viridis", len(names))

    bars = ax.barh(names, values, color=colors, edgecolor="white", linewidth=0.8)
    for bar, val in zip(bars, values):
        ax.text(bar.get_width() + 0.01, bar.get_y() + bar.get_height() / 2,
                f"{val:.4f}", va="center", fontsize=10, fontweight="bold")

    ax.set_xlabel(metric.upper())
    ax.set_title(f"Model Comparison: {metric.upper()} (lower is better)")
    ax.invert_yaxis()

    if save:
        fig.savefig(os.path.join(RESULTS_DIR, f"06_model_comparison_{metric}.png"))
    plt.close(fig)


def plot_hyperparameter_sensitivity(k_results, save=True):
    """Plot MAE vs K (number of neighbors) for each algorithm variant."""
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    # Split by algorithm type
    ub_results = {k: v for k, v in k_results.items() if "User" in k}
    ib_results = {k: v for k, v in k_results.items() if "Item" in k}

    for ax, (title, data) in zip(axes, [("User-Based CF", ub_results), ("Item-Based CF", ib_results)]):
        for name, results in data.items():
            ks = [r["K"] for r in results]
            maes = [r["mae"] for r in results]
            ax.plot(ks, maes, marker="o", linewidth=2, markersize=6, label=name)

        ax.set_xlabel("K (Number of Neighbors)")
        ax.set_ylabel("MAE")
        ax.set_title(f"{title}: Hyperparameter Sensitivity")
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.3)

    fig.suptitle("Impact of K on Prediction Accuracy", y=1.02)

    if save:
        fig.savefig(os.path.join(RESULTS_DIR, "07_hyperparameter_sensitivity.png"))
    plt.close(fig)


def plot_diversity_comparison(diversity_data, save=True):
    """Bar chart comparing recommendation diversity across models."""
    names = list(diversity_data.keys())
    values = list(diversity_data.values())

    fig, ax = plt.subplots(figsize=(len(names) * 1.2, 5))
    colors = sns.color_palette("Set2", len(names))
    bars = ax.bar(names, values, color=colors, edgecolor="white", linewidth=1)

    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.1,
                f"{val:.2f}", ha="center", fontweight="bold")

    ax.set_ylabel("Avg Unique Genres per User")
    ax.set_title("Recommendation Diversity Comparison")
    ax.set_ylim(0, max(values) * 1.15)

    if save:
        fig.savefig(os.path.join(RESULTS_DIR, "08_diversity_comparison.png"))
    plt.close(fig)


def plot_improvement_heatmap(improvement_matrix, save=True):
    """Heatmap showing improvement from Z-score across algorithms and metrics."""
    fig, ax = plt.subplots(figsize=(8, 6))
    sns.heatmap(
        improvement_matrix,
        annot=True,
        fmt=".1f",
        cmap="RdYlGn",
        center=0,
        ax=ax,
        cbar_kws={"label": "Improvement (%)"},
        linewidths=1,
    )
    ax.set_title("Z-Score Standardization: % Improvement by Algorithm and Metric")
    ax.set_ylabel("")

    if save:
        fig.savefig(os.path.join(RESULTS_DIR, "09_zscore_improvement_heatmap.png"))
    plt.close(fig)


def plot_diversity_analysis_detailed(diversity_data, save=True):
    """Detailed diversity analysis plot."""
    if not isinstance(diversity_data, dict):
        return

    fig, ax = plt.subplots(figsize=(10, 6))
    names = list(diversity_data.keys())
    values = [diversity_data[n] for n in names]
    colors = sns.color_palette("Set2", len(names))
    bars = ax.bar(names, values, color=colors)

    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.05,
                f"{val:.1f}", ha="center", fontweight="bold")
    ax.set_ylabel("Average Genres per Recommendation")
    ax.set_title("Recommendation Diversity (Genre-Based Analysis)")
    ax.set_ylim(0, max(values) * 1.15)

    if save:
        fig.savefig(os.path.join(RESULTS_DIR, "08_diversity_comparison.png"))
    plt.close(fig)


def plot_time_comparison(time_data, save=True):
    """Bar chart comparing fitting and prediction time across models."""
    names = list(time_data.keys())
    fit_times = [time_data[n]["fit"] for n in names]
    pred_times = [time_data[n]["predict"] for n in names]

    fig, ax = plt.subplots(figsize=(10, 5))
    x = np.arange(len(names))
    width = 0.35

    bars1 = ax.bar(x - width / 2, fit_times, width, label="Fit Time", color="#4CAF50")
    bars2 = ax.bar(x + width / 2, pred_times, width, label="Predict Time", color="#2196F3")

    for bar in bars1:
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.05,
                f"{bar.get_height():.2f}s", ha="center", fontsize=8)
    for bar in bars2:
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.05,
                f"{bar.get_height():.2f}s", ha="center", fontsize=8)

    ax.set_xticks(x)
    ax.set_xticklabels(names, rotation=15, ha="right", fontsize=9)
    ax.set_ylabel("Time (seconds)")
    ax.set_title("Computational Efficiency Comparison")
    ax.legend()

    if save:
        fig.savefig(os.path.join(RESULTS_DIR, "10_time_comparison.png"))
    plt.close(fig)


def plot_rating_distribution_by_user(ratings_df, save=True):
    """Boxplot of per-user rating statistics."""
    user_stats = ratings_df.groupby("userId")["rating"].agg(["mean", "std", "count"]).dropna()

    fig, axes = plt.subplots(1, 3, figsize=(14, 4.5))

    axes[0].hist(user_stats["mean"], bins=40, color="#4CAF50", edgecolor="white")
    axes[0].axvline(user_stats["mean"].mean(), color="red", linestyle="--",
                    label=f"Mean={user_stats['mean'].mean():.2f}")
    axes[0].set_xlabel("User Mean Rating")
    axes[0].set_ylabel("Count")
    axes[0].set_title("User Mean Rating Distribution")
    axes[0].legend()

    axes[1].hist(user_stats["std"].clip(0, 2), bins=40, color="#2196F3", edgecolor="white")
    axes[1].axvline(user_stats["std"].median(), color="red", linestyle="--",
                    label=f"Median={user_stats['std'].median():.2f}")
    axes[1].set_xlabel("User Rating Std Dev")
    axes[1].set_title("User Rating Variability")
    axes[1].legend()

    axes[2].hist(np.log10(user_stats["count"]), bins=40, color="#FF9800", edgecolor="white")
    axes[2].axvline(np.log10(user_stats["count"]).median(), color="red", linestyle="--",
                    label=f"Median={user_stats['count'].median():.0f}")
    axes[2].set_xlabel("log10(Number of Ratings)")
    axes[2].set_title("User Activity Distribution")
    axes[2].legend()

    fig.suptitle("User Rating Behavior Analysis")
    plt.tight_layout()

    if save:
        fig.savefig(os.path.join(RESULTS_DIR, "11_user_rating_behavior.png"))
    plt.close(fig)


def plot_cold_start_analysis(train_matrix, save=True):
    """Analyze cold-start risk distribution."""
    n_users = train_matrix.shape[0]
    user_counts = np.array([train_matrix[u].nnz for u in range(n_users)])

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    # Histogram
    axes[0].hist(user_counts, bins=80, color="#4CAF50", edgecolor="white", alpha=0.8)
    axes[0].axvline(np.median(user_counts), color="red", linestyle="--",
                    label=f"Median={np.median(user_counts):.0f}")
    axes[0].axvline(20, color="orange", linestyle=":", label="Low threshold (20)")
    axes[0].axvline(5, color="darkred", linestyle=":", label="Cold-start threshold (5)")
    axes[0].set_xlabel("Number of Ratings per User")
    axes[0].set_ylabel("User Count")
    axes[0].set_title("User Interaction Count Distribution")
    axes[0].legend()

    # Cold start risk pie
    low_risk = (user_counts >= 20).sum()
    med_risk = ((user_counts >= 5) & (user_counts < 20)).sum()
    high_risk = (user_counts < 5).sum()

    sizes = [low_risk, med_risk, high_risk]
    labels = [f"Low Risk (>=20)\n{low_risk} users",
              f"Medium Risk (5-19)\n{med_risk} users",
              f"High Risk (<5)\n{high_risk} users"]
    colors = ["#4CAF50", "#FF9800", "#F44336"]

    axes[1].pie(sizes, labels=labels, colors=colors, autopct="%1.1f%%",
                startangle=90, textprops={"fontsize": 9})
    axes[1].set_title("Cold Start Risk Distribution")

    plt.tight_layout()

    if save:
        fig.savefig(os.path.join(RESULTS_DIR, "12_cold_start_analysis.png"))
    plt.close(fig)


def print_all_figures():
    """Return dict mapping figure names to file paths."""
    figs = {}
    for f in sorted(os.listdir(RESULTS_DIR)):
        if f.endswith(".png"):
            figs[f] = os.path.join(RESULTS_DIR, f)
    return figs
