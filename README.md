# 🎬 MovieRec — Collaborative Filtering Movie Recommendation System

[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/flask-3.0+-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/license-Academic-orange.svg)]()

A comprehensive movie recommendation system with collaborative filtering and Z-score standardization. Features a Flask SSR web app with Netflix-style UI, interactive recommendations, and experiment dashboards.

**Dataset**: MovieLens 1M — 6,040 users · 3,706 movies · 1,000,209 ratings (99.98% sparsity)

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
| Item-CF (cosine, Z) | 0.0670 | 0.0249 |

- Z-score standardization: **+9.3%** User-CF, **+9.6%** Item-CF (MAE)
- Item-CF produces **92% more diverse** recommendations than User-CF
- All improvements significant at **p < 0.01**

---

## 🚀 Quick Start

```bash
pip install flask numpy pandas scipy scikit-learn
python app/precompute.py          # Generate recommendation data
python app/server_render.py       # Start web server
```

Open **http://127.0.0.1:8520** · Windows: double-click `app/启动MovieRec.bat`

```bash
# Optional: Download movie posters & trailers (needs TMDB API key)
python app/fetch_posters.py
python app/fetch_trailers.py
```

---

## 🌐 Web App

| Page | Route | Description |
|------|-------|-------------|
| Home | `/` | Hero banner, hot picks, genre rows with horizontal scrolling |
| Browse | `/browse` | Search, filter by genre, sort, paginate |
| Recs | `/recs` | Personalized CF recommendations with algorithm switching |
| Player | `/player/<id>` | Movie detail + YouTube trailer embed or search fallback |
| Experiment | `/experiment` | Full evaluation dashboard with MAE/RMSE tables |

---

## 🧪 Experiments

```bash
python src/run_experiment.py           # Run all CF + baseline experiments
python scripts/generate_report.py      # Generate improved Word report (EN)
python scripts/generate_report_cn.py   # Generate Chinese version
```

---

## 📁 Project Structure

```
MovieRec/
├── src/                              # Core algorithms
│   ├── collaborative_filtering.py      # User-CF & Item-CF with Z-score normalization
│   ├── evaluation.py                  # MAE, RMSE, Precision@K, Recall@K
│   ├── data_loader.py                 # MovieLens 1M loading & train/test split
│   ├── baselines.py                   # GlobalMean, UserMean, ItemMean, MostPopular
│   ├── visualization.py               # 12 matplotlib charts
│   ├── run_experiment.py              # Main experiment pipeline
│   └── config.py                      # Paths & hyperparameters
├── data/ml-1m/                        # MovieLens 1M dataset
├── results/                           # Experiment outputs (12 figures + JSON)
├── reports/                           # Project reports
│   ├── Machine Learning Project.docx
│   ├── MovieRec_Improved_Experiment_Report.docx
│   └── MovieRec_改进实验报告_中文版.docx
├── scripts/                           # Utility scripts
│   ├── generate_report.py
│   └── generate_report_cn.py
├── app/                               # Web application
│   ├── server_render.py               # Flask SSR server (inline CSS, zero JS)
│   ├── precompute.py                  # Data preprocessing pipeline
│   ├── fetch_posters.py               # TMDB poster + backdrop downloader
│   ├── fetch_trailers.py              # YouTube trailer ID fetcher
│   └── 启动MovieRec.bat               # Windows one-click launcher
└── README.md
```

---

## 🔬 Algorithms

**Collaborative Filtering**: User-Based & Item-Based with cosine similarity and Pearson correlation, top-K neighbor selection (K=20~50).

**Z-Score Standardization**: $z_{ui} = \frac{r_{ui} - \mu_u}{\sigma_u}$ — normalizes each user's ratings to zero mean and unit variance, eliminating individual rating bias and improving MAE by 9–10%.

**Baselines**: GlobalMean, UserMean, ItemMean, MostPopular.

## 📊 Visualizations

12 matplotlib figures: rating distribution, sparsity analysis, error distributions, actual vs predicted scatter, algorithm radar comparison, hyperparameter sensitivity, diversity analysis, Z-score improvement heatmap, time comparison, rating behavior, and cold-start analysis.

## 📄 Dataset

[MovieLens 1M](https://grouplens.org/datasets/movielens/1m/) · Used under [GroupLens terms](https://files.grouplens.org/datasets/movielens/ml-1m-README.txt).
