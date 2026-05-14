# MovieRec — Collaborative Filtering Movie Recommendation System

A comprehensive movie recommendation system built on collaborative filtering with Z-score standardization optimization. Features a full-stack Flask web application with interactive evaluation dashboards.

## Team

Qijing Ouyang, Peilun Yang, Yunfeng Shi, Jieyao Pang, Zhipeng Lyu, Sijun Yang, Qijing Feng — MScDS, Lingnan University

## Features

- **User-Based & Item-Based CF** with Cosine Similarity and Pearson Correlation
- **Z-score Standardization** to correct user rating bias (25% MAE improvement on User-CF)
- **Flask SSR Web App** with Netflix-style UI, search, browse, recommendations, and experiment dashboard
- **TMDB Integration** for movie posters, backdrops, and YouTube trailers
- **Multiple Evaluation Metrics**: MAE, RMSE, Precision@K, Recall@K

## Results

| Model | MAE | RMSE |
|-------|-----|------|
| User-CF (cosine, Z) | **0.7018** | 0.9066 |
| Item-CF (cosine, Z) | 0.7146 | 0.9171 |
| User-CF (cosine) | 0.7737 | 0.9735 |
| GlobalMean (baseline) | 0.9449 | 1.1480 |

- Z-Score improves User-CF by **9.3%** and Item-CF by **9.6%**
- All improvements significant at **p < 0.01**

## Quick Start

### 1. Install Dependencies

```bash
pip install flask numpy pandas scipy scikit-learn
```

### 2. Precompute Data

```bash
python app/precompute.py
```

### 3. Run the Web App

```bash
python app/server_render.py
```

Or double-click `app/启动MovieRec.bat` on Windows.

The app opens at **http://127.0.0.1:8520**.

### 4. (Optional) Download Movie Posters

```bash
python app/fetch_posters.py
python app/fetch_trailers.py
```

## Run Experiments

```bash
python src/run_experiment.py
python generate_report.py        # Generate improved experiment report
python generate_report_cn.py     # Generate Chinese version
```

## Project Structure

```
Movie Recommendation/
├── src/                    # Core algorithms
│   ├── collaborative_filtering.py
│   ├── evaluation.py
│   ├── data_loader.py
│   ├── baselines.py
│   ├── visualization.py
│   ├── run_experiment.py
│   └── config.py
├── data/ml-1m/             # MovieLens 1M dataset
├── results/                # Experiment figures & metrics
├── app/                    # Web application
│   ├── server_render.py    # Flask SSR server
│   ├── precompute.py       # Data preprocessing
│   ├── fetch_posters.py    # TMDB poster downloader
│   └── fetch_trailers.py   # YouTube trailer downloader
├── generate_report.py      # Report generator
└── generate_report_cn.py   # Chinese report generator
```

## Dataset

[MovieLens 1M](https://grouplens.org/datasets/movielens/1m/) — 6,040 users, 3,706 movies, 1,000,209 ratings.

## License

This project is for academic purposes. MovieLens data is used under its [terms of use](https://files.grouplens.org/datasets/movielens/ml-1m-README.txt).
