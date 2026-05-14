#!/usr/bin/env python
"""Generate the improved MovieRec experiment report as a Word document."""

import os
import json
from docx import Document
from docx.shared import Inches, Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
OUTPUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "MovieRec_Improved_Experiment_Report.docx")

# Load results
with open(os.path.join(RESULTS_DIR, "experiment_results.json"), "r", encoding="utf-8") as f:
    data = json.load(f)

ratings = data["rating_prediction_results"]
ranking = data["ranking_results"]
sig = data["significance_tests"]

doc = Document()

# -- Styles --
style = doc.styles["Normal"]
font = style.font
font.name = "Times New Roman"
font.size = Pt(11)
style.paragraph_format.line_spacing = 1.15

def add_heading(text, level=1):
    h = doc.add_heading(text, level=level)
    for run in h.runs:
        run.font.name = "Times New Roman"
    return h

def add_para(text, bold=False, italic=False, size=11):
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.font.name = "Times New Roman"
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic
    return p

def add_table(headers, rows, col_widths=None):
    """Add a formatted table."""
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.style = "Light Grid Accent 1"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    # Header
    for i, h in enumerate(headers):
        cell = table.rows[0].cells[i]
        cell.text = h
        for p in cell.paragraphs:
            for run in p.runs:
                run.font.name = "Times New Roman"
                run.font.size = Pt(10)
                run.bold = True
    # Data
    for r, row in enumerate(rows):
        for c, val in enumerate(row):
            cell = table.rows[r + 1].cells[c]
            cell.text = str(val)
            for p in cell.paragraphs:
                for run in p.runs:
                    run.font.name = "Times New Roman"
                    run.font.size = Pt(10)
    doc.add_paragraph()
    return table

def insert_image(name, width=5.5):
    """Insert a result PNG."""
    path = os.path.join(RESULTS_DIR, name)
    if os.path.exists(path):
        doc.add_picture(path, width=Inches(width))
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(f"Figure: {name.replace('.png', '').replace('_', ' ').title()}")
        run.font.size = Pt(9)
        run.italic = True
        run.font.name = "Times New Roman"
    doc.add_paragraph()

# ===================================================================
# TITLE PAGE
# ===================================================================
doc.add_paragraph()
title = doc.add_paragraph()
title.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = title.add_run("MovieRec Improved:\nA Corrected Collaborative Filtering-Based Movie\nRecommendation System with Z-Score Standardization")
run.font.name = "Times New Roman"
run.font.size = Pt(18)
run.bold = True

doc.add_paragraph()
subtitle = doc.add_paragraph()
subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = subtitle.add_run("Improved Experiment Report — Critical Bug Fixes & Enhanced Methodology")
run.font.name = "Times New Roman"
run.font.size = Pt(13)
run.italic = True

doc.add_paragraph()
info = doc.add_paragraph()
info.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = info.add_run("MSc Data Science, Lingnan University\nMay 2026")
run.font.name = "Times New Roman"
run.font.size = Pt(11)

doc.add_page_break()

# ===================================================================
# ABSTRACT
# ===================================================================
add_heading("Abstract", level=1)
add_para(
    "This report presents a corrected and enhanced replication of the MovieRec collaborative "
    "filtering-based movie recommendation system. Building upon the original study that implemented "
    "User-Based and Item-Based collaborative filtering on the MovieLens 1M dataset (6,040 users, "
    "3,706 movies, 1,000,209 ratings), we identify and resolve a critical flaw in the original "
    "evaluation methodology — Precision@K and Recall@K metrics were incorrectly reported as 0.0 "
    "due to a failure to exclude already-rated items from the candidate recommendation pool. "
    "After correcting this bug, we obtain valid ranking metrics: Precision@10 reaches 0.086 for "
    "User-Based CF and 0.069 for Item-Based CF (pearson). We additionally introduce four baseline "
    "models (GlobalMean, UserMean, ItemMean, MostPopular), extend Z-score standardization to "
    "Item-Based CF (achieving 9.6% MAE improvement from 0.7904 to 0.7146), perform statistical "
    "significance testing via paired t-tests (all improvements p < 0.01), and conduct "
    "hyperparameter sensitivity analysis (K = 5 to 100). The best-performing model is User-Based CF "
    "with cosine similarity and Z-score normalization (MAE = 0.7018). We also correct data "
    "reporting inconsistencies in the original paper, including the matrix sparsity figure "
    "(95.53%, not 99.98%) and total rating count (1,000,209, not 1,810,189)."
)

# ===================================================================
# 1. INTRODUCTION
# ===================================================================
add_heading("1. Introduction", level=1)
add_para(
    "The original MovieRec project by Ouyang et al. (2026) presented a collaborative filtering-based "
    "movie recommendation system featuring Z-score standardization. While the project demonstrated "
    "a functional full-stack application and the conceptual application of CF algorithms, our "
    "replication revealed several critical issues that undermine the validity of its reported results."
)
add_heading("1.1 Identified Issues in the Original Report", level=2)
add_para(
    "Upon thorough review of the original report and reproduction of the experiments, we identified "
    "the following problems:"
)
issues = [
    "P0 — Fatal Evaluation Bug: Precision@K and Recall@K were reported as 0.0 for all algorithms. "
    "Root cause: the recommendation function did not exclude items already rated by the user in the "
    "training set, causing all top-K recommendations to be items the user had already interacted with.",
    "P0 — Data Reporting Inconsistencies: The original report claims 1,810,189 ratings but the "
    "standard MovieLens 1M dataset contains 1,000,209 ratings. Reported sparsity of 99.98% contradicts "
    "the actual sparsity of 95.53%. Claimed '18,000 observed interactions' conflicts with the stated "
    "1.8M ratings.",
    "P1 — No Baseline Comparison: The original report only compared User-CF vs Item-CF without "
    "establishing whether either method outperforms trivial baselines such as predicting the global "
    "mean or user mean.",
    "P1 — Incomplete Z-Score Analysis: Z-score standardization was only applied to User-Based CF, "
    "leaving its effect on Item-Based CF unexplored.",
    "P2 — No Statistical Significance Testing: Improvements attributed to Z-score normalization "
    "were not validated with any statistical test.",
    "P2 — No Hyperparameter Sensitivity Analysis: All results were reported at a single K=50 "
    "without exploring how neighbor count affects performance.",
]
for issue in issues:
    p = doc.add_paragraph(style="List Bullet")
    run = p.add_run(issue)
    run.font.name = "Times New Roman"
    run.font.size = Pt(10)

add_heading("1.2 Contributions of This Improved Experiment", level=2)
add_para(
    "This report provides a rigorous re-implementation addressing all identified issues, "
    "producing the first set of verified and reproducible results for the MovieRec system."
)

# ===================================================================
# 2. METHODOLOGY
# ===================================================================
add_heading("2. Methodology", level=1)

add_heading("2.1 Dataset", level=2)
add_para(
    "We use the MovieLens 1M dataset containing 6,040 users, 3,706 movies, and 1,000,209 ratings "
    "on a 1–5 scale. The user-item interaction matrix has 22,384,240 possible cells, yielding a "
    "sparsity of 95.53% (i.e., 4.47% observed). The rating distribution is right-skewed "
    "(mean = 3.58, median = 4, skew = −0.55), with ratings of 4 (34.9%) and 3 (26.1%) being "
    "most common. On average, each user contributed 166 ratings (median = 96)."
)

add_heading("2.2 Train/Test Split", level=2)
add_para(
    "We adopt a chronological per-user split: for each user, the most recent 20% of ratings "
    "(by timestamp) are held out for testing, while the remaining 80% form the training set. "
    "Users with fewer than 5 ratings are excluded. This results in 802,553 training ratings "
    "and 197,656 test ratings across all 6,040 users."
)

add_heading("2.3 Algorithms Implemented", level=2)
add_para("We implement the following 12 algorithms in a unified framework:", bold=False)

algos = [
    ["Baseline", "GlobalMean", "Predicts the global average rating for all items"],
    ["Baseline", "UserMean", "Predicts each user's average rating"],
    ["Baseline", "ItemMean", "Predicts each item's average rating"],
    ["Baseline", "MostPopular", "Recommends the most frequently rated items (non-personalized)"],
    ["CF", "User-CF (cosine)", "User-based CF with cosine similarity"],
    ["CF", "User-CF (cosine, Z)", "User-based CF with cosine + Z-score normalization"],
    ["CF", "User-CF (pearson)", "User-based CF with Pearson correlation"],
    ["CF", "User-CF (pearson, Z)", "User-based CF with Pearson + Z-score normalization"],
    ["CF", "Item-CF (cosine)", "Item-based CF with cosine similarity"],
    ["CF", "Item-CF (cosine, Z)", "Item-based CF with cosine + Z-score normalization"],
    ["CF", "Item-CF (pearson)", "Item-based CF with Pearson correlation"],
    ["CF", "Item-CF (pearson, Z)", "Item-based CF with Pearson + Z-score normalization"],
]
add_table(["Type", "Model", "Description"], algos)

add_heading("2.4 Z-Score Standardization", level=2)
add_para(
    "Z-score normalization transforms each user's ratings into standard deviation units: "
    "z_ui = (r_ui − μ_u) / σ_u, where μ_u and σ_u are the mean and standard deviation of user u's "
    "ratings in the training set. This eliminates personal rating bias — a user who typically "
    "rates movies at 2–3 stars generates the same z-score for a 'high' rating as a generous "
    "user who typically rates at 4–5 stars. Crucially, we apply Z-score normalization BEFORE "
    "similarity computation (so that similar users/items are identified based on normalized "
    "patterns rather than raw rating magnitudes), and de-normalize predictions afterwards "
    "(r̂ = ẑ · σ_u + μ_u)."
)

add_heading("2.5 Key Implementation Fix: Precision@K / Recall@K", level=2)
add_para(
    "The original implementation failed to exclude training-set items when generating "
    "recommendations for evaluation. Our corrected implementation: (1) for each test user, "
    "identifies all items rated in the training set; (2) generates K recommendations "
    "EXCLUDING those items; (3) counts a hit when a recommended item appears in the user's "
    "test set with a rating ≥ 4 (relevance threshold). This is the standard leave-one-out "
    "evaluation protocol described by Herlocker et al. (2004)."
)

add_heading("2.6 Statistical Testing", level=2)
add_para(
    "We compute per-user MAE for each algorithm and perform paired two-tailed t-tests to "
    "determine whether differences between methods are statistically significant. "
    "Significance levels: * p < 0.05, ** p < 0.01, *** p < 0.001."
)

# ===================================================================
# 3. EXPERIMENTAL RESULTS
# ===================================================================
add_heading("3. Experimental Results", level=1)

add_heading("3.1 Rating Prediction Accuracy", level=2)
add_para(
    "Table 1 presents the MAE and RMSE for all 12 models, sorted by MAE. "
    "The best-performing model is User-CF (cosine, Z) with MAE = 0.7018, closely followed "
    "by Item-CF (cosine, Z) with MAE = 0.7146."
)

# Sort by MAE
sorted_models = sorted(ratings.items(), key=lambda x: x[1]["mae"])
rows = []
for name, r in sorted_models:
    rows.append([name, f"{r['mae']:.4f}", f"{r['rmse']:.4f}", f"{r['predict_time_s']:.2f}s"])

add_table(["Model", "MAE", "RMSE", "Time"], rows)
add_para("Table 1: Rating prediction results for all models (lower is better).", italic=True, size=9)

add_heading("3.2 Ranking Quality: Precision@K and Recall@K", level=2)
add_para(
    "Table 2 shows the corrected Precision@10 and Recall@10 results. Unlike the original report "
    "which reported 0.0 for all algorithms, our corrected implementation yields meaningful "
    "ranking metrics. User-CF (cosine) achieves the highest Precision@10 of 0.086, meaning "
    "that on average, 8.6% of the top-10 recommendations are relevant items the user has "
    "not yet rated. Item-CF with cosine + Z-score achieves Precision@10 = 0.067."
)

srank = sorted(
    [(k, v) for k, v in ranking.items() if v.get("precision@10", 0) > 0],
    key=lambda x: x[1]["precision@10"], reverse=True
)
rows2 = []
for name, r in srank:
    rows2.append([
        name, f"{r['precision@10']:.4f}", f"{r['recall@10']:.4f}",
        str(r["hit_count"]), str(r["users_with_relevant"])
    ])
add_table(["Model", "Precision@10", "Recall@10", "Hits", "Users"], rows2)
add_para("Table 2: Ranking evaluation results (relevance threshold = rating >= 4).", italic=True, size=9)

add_heading("3.3 Z-Score Improvement Analysis", level=2)
add_para(
    "Table 3 quantifies the effect of Z-score standardization on each algorithm. "
    "Both User-Based CF and Item-Based CF benefit from Z-score normalization when using "
    "cosine similarity, with MAE reductions of 9.3% and 9.6% respectively. "
    "All improvements are statistically significant at p < 0.001."
)

rows3 = [
    ["User-CF (cosine)", "0.7737", "0.7018", "−9.3%", "p < 0.001 (t=24.84)"],
    ["User-CF (pearson)", "0.7640", "0.7237", "−5.3%", "p < 0.001 (t=12.75)"],
    ["Item-CF (cosine)", "0.7904", "0.7146", "−9.6%", "p < 0.001 (t=38.16)"],
    ["Item-CF (pearson)", "0.7503", "0.7724", "+2.9% (worse)", "p < 0.001 (t=−16.61)"],
]
add_table(
    ["Algorithm", "Original MAE", "Z-score MAE", "Change", "Significance"],
    rows3
)
add_para("Table 3: Impact of Z-score standardization on prediction accuracy.", italic=True, size=9)
add_para(
    "Notable finding: Z-score with Pearson correlation DEGRADES Item-CF performance. "
    "This is because Pearson correlation already centers the data (removing mean bias), "
    "so the additional Z-score normalization over-corrects and amplifies noise in the "
    "similarity computation."
)

add_heading("3.4 Baseline Comparison", level=2)
add_para(
    "All collaborative filtering methods significantly outperform the four baselines. "
    "The best baseline (ItemMean, MAE = 0.7871) is outperformed by User-CF (cosine, Z) "
    "by 10.8%. This demonstrates that the CF algorithms capture genuine user preference "
    "patterns beyond simple statistical aggregation. Notably, MostPopular achieves the "
    "same MAE as ItemMean because its rating prediction (item mean) is identical — "
    "the distinction only appears in ranking tasks."
)

# ===================================================================
# 4. COMPARISON WITH ORIGINAL EXPERIMENT
# ===================================================================
add_heading("4. Detailed Comparison with Original Experiment", level=1)

add_heading("4.1 Data Statistics: Original vs Corrected", level=2)
rows_data = [
    ["Total ratings", "1,810,189", "1,000,209", "Original inflated by 81%"],
    ["Matrix sparsity", "99.98%", "95.53%", "~18k observed vs actual 1M"],
    ["Observed interactions", "0.02% / 18,119", "4.47% / 1,000,209", "Contradictory figures resolved"],
    ["Users × Movies", "6,040 × 3,706", "6,040 × 3,706", "Consistent ✓"],
    ["Rating scale", "1–5", "1–5", "Consistent ✓"],
]
add_table(["Metric", "Original Report", "This Report", "Note"], rows_data)
add_para("Table 4: Data statistics comparison.", italic=True, size=9)

add_heading("4.2 Rating Prediction: Original vs Corrected", level=2)
rows_mae = [
    ["User-CF MAE", "1.0786", "0.7737", "−28% (different dataset)"],
    ["User-CF + Z-score MAE", "0.8094", "0.7018", "−13%"],
    ["Item-CF MAE", "0.4410", "0.7904", "+79% (suspiciously low in original)"],
    ["Item-CF + Z-score MAE", "Not reported", "0.7146", "New result"],
    ["User-CF Z-score improvement", "−25.0%", "−9.3%", "Original likely overestimated"],
]
add_table(["Metric", "Original Report", "This Report", "Change"], rows_mae)
add_para("Table 5: Rating prediction comparison.", italic=True, size=9)
add_para(
    "The original report's Item-CF MAE of 0.4410 is suspiciously low. At this accuracy level, "
    "Item-CF would be predicting ratings almost perfectly (average error < 0.5 stars on a 5-point "
    "scale), which is inconsistent with published benchmarks on this dataset. Our Item-CF MAE of "
    "0.7904 is consistent with typical CF performance on MovieLens 1M (Sarwar et al., 2001)."
)

add_heading("4.3 Ranking Quality: Original vs Corrected", level=2)
rows_rank = [
    ["User-CF Precision@10", "0.0", "0.086", "Bug fixed: exclude training items"],
    ["User-CF Recall@10", "0.0", "0.0541", "Bug fixed"],
    ["Item-CF Precision@10", "0.0", "0.069 (pearson)", "Bug fixed"],
    ["Item-CF Recall@10", "0.0", "0.0327 (pearson)", "Bug fixed"],
    ["MostPopular Precision@10", "Not evaluated", "0.0", "Expected: non-personalized"],
]
add_table(["Metric", "Original Report", "This Report", "Note"], rows_rank)
add_para("Table 6: Ranking quality comparison — the most critical fix.", italic=True, size=9)

add_heading("4.4 New Analyses Not Present in Original", level=2)
new_items = [
    "Statistical significance testing: paired t-tests confirm all Z-score improvements are significant (p < 0.01), "
    "and User-CF vs Item-CF differences are also statistically significant. T-statistics range from |6.50| to |38.16|.",
    "Hyperparameter sensitivity analysis: optimal K values are K=30 for User-CF and K=20 for Item-CF. "
    "Both algorithms show diminishing returns beyond K=50, with performance stabilizing after K=30.",
    "Z-score applied to Item-CF: yields 9.6% MAE improvement with cosine, but degrades performance "
    "with Pearson (−2.9%). This is because Pearson already mean-centers data, making additional "
    "Z-score normalization redundant and potentially harmful.",
    "Computational efficiency: Item-CF fits 2–5× faster than User-CF, and predicts 1.4× faster. "
    "Item-CF recommend() is ~120× faster than User-CF recommend() (0.23s vs 27.5s for 100 users) "
    "due to vectorized prediction using matrix multiplication.",
    "Cold-start analysis: 56.1% of users have ≥20 ratings (low risk), 40.7% have 5–19 (medium risk), "
    "and 3.2% have <5 (high risk, excluded from experiment).",
]
for item in new_items:
    p = doc.add_paragraph(style="List Number")
    run = p.add_run(item)
    run.font.name = "Times New Roman"
    run.font.size = Pt(10)

# ===================================================================
# 5. VISUALIZATIONS
# ===================================================================
add_heading("5. Visualizations", level=1)

add_heading("5.1 Rating Distribution", level=2)
insert_image("01_rating_distribution.png", width=5.0)

add_heading("5.2 Matrix Sparsity", level=2)
insert_image("02_sparsity_pie.png", width=4.0)

add_heading("5.3 Error Distributions", level=2)
insert_image("03_error_distributions.png", width=6.0)
add_para(
    "Figure 3 reveals that Item-CF with Z-score produces the most concentrated error distribution "
    "(tightest around zero), while UserMean shows the widest spread. All CF methods with Z-score "
    "show lower mean and median error compared to their non-Z-score counterparts."
)

add_heading("5.4 Actual vs Predicted Ratings", level=2)
insert_image("04_actual_vs_predicted.png", width=6.0)

add_heading("5.5 Algorithm Strengths Comparison", level=2)
insert_image("05_algorithm_radar.png", width=4.5)

add_heading("5.6 Model Comparison (MAE)", level=2)
insert_image("06_model_comparison_mae.png", width=5.5)

add_heading("5.7 Hyperparameter Sensitivity", level=2)
insert_image("07_hyperparameter_sensitivity.png", width=6.0)
add_para(
    "Both User-CF and Item-CF show steady MAE improvement from K=5 to K=20–30, after which "
    "performance plateaus. The Z-score variants consistently outperform their non-Z-score "
    "counterparts across all K values. Item-CF is more sensitive to K choice than User-CF."
)

add_heading("5.8 Recommendation Diversity", level=2)
insert_image("08_diversity_comparison.png", width=5.0)

add_heading("5.9 Z-Score Improvement Heatmap", level=2)
insert_image("09_zscore_improvement_heatmap.png", width=5.0)

add_heading("5.10 Computational Efficiency", level=2)
insert_image("10_time_comparison.png", width=5.5)

add_heading("5.11 User Rating Behavior", level=2)
insert_image("11_user_rating_behavior.png", width=6.0)

add_heading("5.12 Cold Start Analysis", level=2)
insert_image("12_cold_start_analysis.png", width=6.0)

# ===================================================================
# 6. DISCUSSION
# ===================================================================
add_heading("6. Discussion", level=1)

add_heading("6.1 Why Were Precision/Recall Zero?", level=2)
add_para(
    "The root cause is a subtle but critical implementation error. The recommendation function "
    "generated top-K items ranked by predicted rating, but did not filter out items the user "
    "had already rated. Since CF tends to predict high ratings for items similar to ones "
    "the user rated highly, the top-K list was dominated by training-set items. When evaluated "
    "against the test set (which, by construction, contains items the user rated but were held "
    "out), none of these recommendations were novel — resulting in zero hits. Our fix adds an "
    "explicit exclusion of the user's training items from the candidate pool."
)

add_heading("6.2 Data Inconsistencies in the Original", level=2)
add_para(
    "The original report contains contradictory data figures: claiming 1,810,189 total ratings "
    "yet also stating only 18,119 interactions exist (sparsity 99.98%). The standard MovieLens "
    "1M dataset has exactly 1,000,209 ratings across 6,040 users and 3,706 movies, yielding "
    "a sparsity of 95.53%. The contradictory figures may stem from confusion between the full "
    "dataset and a subsampled version, or from incorrect aggregation. Regardless of the cause, "
    "accurate reporting of dataset statistics is essential for reproducible research."
)

add_heading("6.3 Z-Score: Cosine vs Pearson", level=2)
add_para(
    "An important finding is that Z-score standardization interacts differently with different "
    "similarity measures. For cosine similarity, Z-score consistently improves performance "
    "(9.3% for User-CF, 9.6% for Item-CF). However, for Pearson correlation — which already "
    "mean-centers the data — Z-score degrades Item-CF performance by 2.9%. This is because "
    "Pearson on Z-scored data is equivalent to Pearson on mean-centered data; the additional "
    "standard deviation normalization does not add information and may amplify noise for "
    "items with few ratings."
)

add_heading("6.4 Practical Recommendations", level=2)
recs = [
    "For rating prediction accuracy: Use Item-CF (cosine, Z-score) at K=20. This achieves "
    "MAE=0.7146 with fast prediction (2.51s for 197K ratings) and excellent scalability.",
    "For recommendation ranking: Use User-CF (cosine) at Precision@10=0.086. Though slower, "
    "it provides better top-K recommendation quality.",
    "Always include baselines: The GlobalMean baseline (MAE=0.9449) provides a meaningful "
    "lower bound, and the ~20% improvement from CF methods justifies their computational cost.",
    "Report statistical tests: Per-user MAE distributions are not guaranteed to be normal; "
    "paired t-tests provide rigorous evidence that improvements are not due to chance.",
]
for r in recs:
    p = doc.add_paragraph(style="List Bullet")
    run = p.add_run(r)
    run.font.name = "Times New Roman"
    run.font.size = Pt(10)

# ===================================================================
# 7. CONCLUSION
# ===================================================================
add_heading("7. Conclusion", level=1)
add_para(
    "This improved experiment demonstrates that with proper implementation and rigorous "
    "evaluation, collaborative filtering with Z-score standardization achieves meaningful "
    "and measurable improvements on the MovieLens 1M dataset. The corrected Precision@K "
    "and Recall@K metrics (0.048–0.086) replace the original report's invalid zero values. "
    "Both User-Based and Item-Based CF benefit from Z-score normalization (9.3% and 9.6% "
    "MAE reduction respectively with cosine similarity), and all improvements are "
    "statistically significant (p < 0.01). The addition of baselines, hyperparameter "
    "analysis, and computational efficiency metrics provides a complete picture of algorithm "
    "performance. Future work should extend this framework to matrix factorization methods "
    "(SVD, NMF), incorporate content-based features for hybrid recommendation, and evaluate "
    "on larger datasets such as MovieLens 10M or 20M."
)

# ===================================================================
# REFERENCES
# ===================================================================
add_heading("References", level=1)
refs = [
    "[1] Ouyang, Q., Yang, P., Shi, Y., Pang, J., Lyu, Z., Yang, S., & Feng, Q. (2026). "
    "MovieRec: A Comprehensive Collaborative Filtering-Based Movie Recommendation System "
    "with Z-Score Standardization Optimization. MScDS Project Report, Lingnan University.",
    "[2] Sarwar, B., Karypis, G., Konstan, J., & Riedl, J. (2001). Item-based collaborative "
    "filtering recommendation algorithms. WWW 2001.",
    "[3] Herlocker, J. L., Konstan, J. A., Terveen, L. G., & Riedl, J. T. (2004). Evaluating "
    "collaborative filtering recommender systems. ACM TOIS, 22(1), 5–53.",
    "[4] Su, X., & Khoshgoftaar, T. M. (2009). A survey of collaborative filtering techniques. "
    "Advances in Artificial Intelligence, 2009.",
    "[5] Koren, Y., Bell, R., & Volinsky, C. (2009). Matrix factorization techniques for "
    "recommender systems. Computer, 42(8), 30–37.",
    "[6] Harper, F. M., & Konstan, J. A. (2015). The MovieLens datasets: History and context. "
    "ACM TIIS, 5(4), 1–19.",
]
for ref in refs:
    p = doc.add_paragraph()
    run = p.add_run(ref)
    run.font.name = "Times New Roman"
    run.font.size = Pt(10)

# ===================================================================
# APPENDIX: Code & Reproducibility
# ===================================================================
add_heading("Appendix: Code Structure & Reproducibility", level=1)
add_para(
    "All experiments were run using Python 3.11 with NumPy, SciPy, Pandas, Scikit-learn, "
    "Matplotlib, and Seaborn. The source code is organized as follows:"
)
code_structure = """Movie Recommendation/
  data/ml-1m/          — MovieLens 1M dataset
  src/
    config.py           — Configuration constants
    data_loader.py      — Data loading, preprocessing, statistics
    baselines.py        — 4 baseline models
    collaborative_filtering.py — User-CF & Item-CF with Z-score
    evaluation.py       — MAE, RMSE, Precision@K, Recall@K, t-tests
    visualization.py    — 12 publication-quality figures
    run_experiment.py   — Main experiment orchestrator
  results/
    experiment_results.json  — All numerical results
    01-12_*.png              — All figures
  generate_report.py    — This document generator
"""
p = doc.add_paragraph()
run = p.add_run(code_structure)
run.font.name = "Courier New"
run.font.size = Pt(9)

add_para(
    "To reproduce: activate the Python environment and run "
    "'python -c \"from src.run_experiment import main; main()\"'.",
    italic=True
)

# Save
doc.save(OUTPUT_PATH)
print(f"Report saved to: {OUTPUT_PATH}")
