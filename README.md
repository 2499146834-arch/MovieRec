# 🎬 MovieRec — Collaborative Filtering Movie Recommendation System

[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/flask-3.0+-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/license-Academic-orange.svg)]()

A comprehensive movie recommendation system built on collaborative filtering with Z-score standardization optimization. Features a full-stack Flask web application with Netflix-style UI, interactive recommendation generation, and experiment evaluation dashboards.

**Dataset**: MovieLens 1M — 6,040 users · 3,706 movies · 1,000,209 ratings · 99.98% matrix sparsity

## 👥 Team

Qijing Ouyang · Peilun Yang · Yunfeng Shi · Jieyao Pang · Zhipeng Lyu · Sijun Yang · Qijing Feng

MSc Data Science, Lingnan University, Hong Kong

---

## 🏆 Key Results

### Rating Prediction

| Model | MAE ↓ | RMSE ↓ |
|-------|-------|--------|
| **User-CF (cosine, Z)** | **0.7018** | 0.9066 |
| Item-CF (cosine, Z) | 0.7146 | 0.9171 |
| User-CF (pearson, Z) | 0.7237 | 0.9326 |
| User-CF (cosine) | 0.7737 | 0.9735 |
| Item-CF (cosine) | 0.7904 | 1.0169 |
| GlobalMean (baseline) | 0.9449 | 1.1480 |

### Ranking Quality

| Model | Precision@10 | Recall@10 |
|-------|-------------|-----------|
| User-CF (cosine) | 0.0860 | 0.0541 |
| User-CF (cosine, Z) | 0.0810 | 0.0428 |
| User-CF (pearson, Z) | 0.0710 | 0.0343 |
| Item-CF (cosine, Z) | 0.0670 | 0.0249 |

### Key Findings

- Z-score standardization improves User-CF by **+9.3%** and Item-CF by **+9.6%** in MAE
- User-CF (cosine, Z) achieves the best overall accuracy (MAE = 0.7018)
- Item-CF produces more diverse recommendations (+92% genre diversity vs User-CF)
- All improvements statistically significant at **p < 0.01**

---

## 🚀 Quick Start

### Prerequisites

```bash
pip install flask numpy pandas scipy scikit-learn
```

### 1. Precompute Data

```bash
cd app
python precompute.py
```

This generates `static/app_data.json` — the precomputed recommendation and evaluation data.

### 2. Launch Web App

```bash
python app/server_render.py
```

The app opens at **http://127.0.0.1:8520**.

On Windows, double-click `app/启动MovieRec.bat`.

### 3. (Optional) Download Movie Posters & Trailers

```bash
python app/fetch_posters.py    # Download posters + backdrops from TMDB (~2800 movies)
python app/fetch_trailers.py   # Fetch YouTube trailer IDs from TMDB (~1200 movies)
```

> **Note**: This requires a TMDB API key. The default key in the script works for ~40 requests/10s. Posters are saved to `app/static/posters/` (gitignored).

---

## 🌐 Web App Pages

| Page | Route | Description |
|------|-------|-------------|
| 🏠 Home | `/` | Netflix-style hero banner, hot picks, genre rows with horizontal scrolling |
| 🔍 Browse | `/browse` | Full movie library with search, genre filter, and sort (popularity/year/title) |
| ✨ Recommendations | `/recs` | Personalized recommendations with algorithm switching and user navigation |
| 🎥 Player | `/player/<id>` | Movie detail with embedded YouTube trailer or search fallback, similar movies |
| 📊 Experiment | `/experiment` | Full experiment dashboard with MAE/RMSE tables and significance tests |

---

## 🧪 Run Experiments

```bash
# Run all experiments (CF, baselines, significance tests)
python src/run_experiment.py

# Generate improved experiment report (Word)
python generate_report.py

# Generate Chinese version
python generate_report_cn.py
```

Results are saved to `results/` directory including 12 figures and `experiment_results.json`.

---

## 📁 Project Structure

```
MovieRec/
├── src/                          # Core algorithm implementations
│   ├── collaborative_filtering.py  # User-CF & Item-CF with Z-score
│   ├── evaluation.py              # MAE, RMSE, Precision@K, Recall@K
│   ├── data_loader.py             # MovieLens data loading & splitting
│   ├── baselines.py               # GlobalMean, UserMean, MostPopular
│   ├── visualization.py           # Matplotlib chart generation
│   ├── run_experiment.py          # Main experiment runner
│   └── config.py                  # Paths & hyperparameters
├── data/ml-1m/                    # MovieLens 1M dataset
├── results/                       # Experiment outputs (12 figures + JSON)
├── app/                           # Web application
│   ├── server_render.py           # Flask SSR server (inline CSS, zero JS deps)
│   ├── precompute.py              # Precompute recommendations & evaluation data
│   ├── fetch_posters.py           # TMDB poster + backdrop downloader
│   ├── fetch_trailers.py          # YouTube trailer ID fetcher
│   └── 启动MovieRec.bat           # Windows launcher
├── generate_report.py             # Improved experiment report generator
├── generate_report_cn.py          # Chinese report generator
└── Machine Learning Project.docx  # Original project report
```

---

## 🔬 Algorithm Details

### Collaborative Filtering

- **User-Based CF**: Find similar users via rating patterns, predict by weighted neighbor average
- **Item-Based CF**: Precompute item-item similarities, predict by user's rated items
- **Similarity Metrics**: Cosine similarity and Pearson correlation
- **Neighbor Selection**: Top-K nearest neighbors (K=20~50)

### Z-Score Standardization

Raw ratings are transformed to account for individual user rating bias:

$$z_{ui} = \frac{r_{ui} - \mu_u}{\sigma_u}$$

This normalizes each user's ratings to zero mean and unit variance, making cross-user comparisons meaningful.

### Baselines

- **GlobalMean**: Predict global average rating for all items
- **UserMean**: Predict user's personal average rating
- **ItemMean**: Predict item's average rating
- **MostPopular**: Recommend most-rated items to everyone

---

## 📊 Visualizations Generated

1. Rating distribution histogram
2. User-item matrix sparsity pie chart
3. Prediction error distribution (User-CF vs Item-CF)
4. Actual vs predicted ratings scatter plots
5. Algorithm strengths & weaknesses radar chart
6. Model comparison MAE bar chart
7. Hyperparameter sensitivity (K values)
8. Recommendation diversity comparison
9. Z-score improvement heatmap
10. Computation time comparison
11. User rating behavior analysis
12. Cold-start risk analysis

---

## 📄 Dataset

[MovieLens 1M](https://grouplens.org/datasets/movielens/1m/) — a benchmark dataset for collaborative filtering research:

- 6,040 users with demographic info
- 3,706 movies with genres and release years
- 1,000,209 ratings on a 1–5 scale
- 99.98% matrix sparsity (only 0.02% of possible ratings observed)

Used under [GroupLens terms of use](https://files.grouplens.org/datasets/movielens/ml-1m-README.txt).

---

## 📝 License

This project is created for academic purposes as part of the MSc Data Science program at Lingnan University.
