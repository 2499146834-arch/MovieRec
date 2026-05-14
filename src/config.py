"""Configuration and constants for MovieRec improved experiment."""

import os

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
RESULTS_DIR = os.path.join(BASE_DIR, "results")

# MovieLens 1M dataset
ML1M_URL = "https://files.grouplens.org/datasets/movielens/ml-1m.zip"
ML1M_DIR = os.path.join(DATA_DIR, "ml-1m")
ML1M_ZIP = os.path.join(DATA_DIR, "ml-1m.zip")

# Experiment settings
RANDOM_SEED = 42
RATING_SCALE = (1, 5)
RELEVANCE_THRESHOLD = 4.0  # rating >= 4 means relevant for Precision/Recall

# Train/test split
TEST_RATIO = 0.2  # 20% test per user
MIN_USER_RATINGS = 5  # users must have at least this many ratings

# CF hyperparameters
DEFAULT_K_NEIGHBORS = 50
K_VALUES = [5, 10, 20, 30, 50, 80, 100]  # for sensitivity analysis

# Recommendation
TOP_K_RECOMMEND = 10

# Similarity measures
SIMILARITY_MEASURES = ["cosine", "pearson"]
