"""
recommendation_service.py

Loads every saved ML artifact from the Hybrid E-Commerce Recommendation System
(Notebooks 01-07) exactly once, and exposes plain Python methods that the API
layer (main.py) calls per-request.

IMPORTANT: no training happens here. This module only reconstructs objects that
were already fit and saved to disk in earlier notebooks.
"""

import os
import pickle

import numpy as np
import pandas as pd
from scipy.sparse import load_npz
from sklearn.metrics.pairwise import cosine_similarity


class RecommendationService:
    """
    Loads artifacts once in __init__, then serves requests from memory.

    Loading touches disk (Drive or local) and deserializes multi-MB pickles and
    sparse matrices (the TF-IDF matrix, the ALS factors, the train matrix). Doing
    that on every request would add hundreds of milliseconds (or seconds, on Drive)
    of latency to every single API call, and would multiply memory usage under any
    concurrent traffic. Instantiate this class ONCE per process.
    """

    def __init__(self, base_dir: str = None):
        self.base_dir = base_dir or os.environ.get(
            "RECSYS_BASE_DIR", "/content/drive/MyDrive/hm_recsys"
        )
        self.processed_data_dir = os.path.join(self.base_dir, "processed_data")
        self.models_dir = os.path.join(self.base_dir, "models")
        self.artifacts_dir = os.path.join(self.base_dir, "artifacts")
        self.cb_artifacts_dir = os.path.join(self.base_dir, "cb_artifacts")

        self._load_artifacts()

    # ------------------------------------------------------------------ #
    # Loading (runs once, at startup)
    # ------------------------------------------------------------------ #
    def _load_artifacts(self):
        required_dirs = [self.processed_data_dir, self.models_dir, self.artifacts_dir]
        missing = [p for p in required_dirs if not os.path.exists(p)]
        if missing:
            raise FileNotFoundError(
                f"Required artifact directories not found: {missing}. "
                f"Run Notebooks 03-06 first, or set RECSYS_BASE_DIR correctly."
            )

        # --- Product metadata (for turning item_idx back into something readable) ---
        self.processed_articles = pd.read_csv(
            os.path.join(self.processed_data_dir, "processed_articles.csv")
        )
        self.article_lookup = self.processed_articles.set_index("article_id")

        # --- Content-based artifacts ---
        content_features = pd.read_csv(os.path.join(self.processed_data_dir, "content_features.csv"))
        self.cb_article_ids = content_features["article_id"].values
        self.cb_id_to_index = {aid: idx for idx, aid in enumerate(self.cb_article_ids)}

        vec_path = os.path.join(self.cb_artifacts_dir, "tfidf_vectorizer.pkl")
        mat_path = os.path.join(self.cb_artifacts_dir, "tfidf_matrix.npz")
        if os.path.exists(vec_path) and os.path.exists(mat_path):
            with open(vec_path, "rb") as f:
                self.tfidf_vectorizer = pickle.load(f)
            self.tfidf_matrix = load_npz(mat_path)
        else:
            # cb_artifacts/ was a LOCAL (non-Drive) path in Notebook 04/07, so it may not
            # exist in a fresh runtime. Rebuild with the exact same config as Notebook 04
            # rather than hard-failing -- this is a few seconds of work, not training.
            print("[RecommendationService] cb_artifacts not found locally — rebuilding TF-IDF...")
            from sklearn.feature_extraction.text import TfidfVectorizer
            FINAL_TFIDF_CONFIG = {"max_features": 10000, "min_df": 2, "max_df": 0.8, "ngram_range": (1, 2)}
            self.tfidf_vectorizer = TfidfVectorizer(**FINAL_TFIDF_CONFIG, stop_words="english")
            self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(
                content_features["combined_features"].fillna("")
            )

        # --- Encoders (string IDs <-> matrix indices) ---
        with open(os.path.join(self.processed_data_dir, "label_encoders.pkl"), "rb") as f:
            encoders = pickle.load(f)
        self.user_encoder = encoders["user_encoder"]
        self.item_encoder = encoders["item_encoder"]

        # --- Collaborative filtering (ALS) ---
        with open(os.path.join(self.models_dir, "als_model.pkl"), "rb") as f:
            als_bundle = pickle.load(f)
        self.als_model = als_bundle["model"]

        # --- Train matrix (needed to know what a user already purchased) ---
        self.train_matrix = load_npz(os.path.join(self.artifacts_dir, "train_matrix.npz"))

        # --- Popularity fallback (used for new/cold-start users) ---
        with open(os.path.join(self.artifacts_dir, "popularity_baseline.pkl"), "rb") as f:
            pop_bundle = pickle.load(f)
        self.popularity_ranking = pop_bundle["popularity_ranking"]

        # --- Hybrid config (alpha, activity threshold) from Notebook 06 ---
        with open(os.path.join(self.models_dir, "hybrid_model_config.pkl"), "rb") as f:
            hybrid_config = pickle.load(f)
        self.best_alpha = hybrid_config["best_alpha"]
        self.low_activity_threshold = hybrid_config["low_activity_threshold"]

        print("[RecommendationService] All artifacts loaded successfully.")

    # ------------------------------------------------------------------ #
    # Internal scoring helpers (same logic as Notebooks 05-07)
    # ------------------------------------------------------------------ #
    def _build_user_content_profile(self, user_idx):
        purchased_item_indices = self.train_matrix[user_idx].indices
        if len(purchased_item_indices) == 0:
            return None
        purchased_article_ids = self.item_encoder.inverse_transform(purchased_item_indices)
        cb_indices = [
            self.cb_id_to_index[aid] for aid in purchased_article_ids if aid in self.cb_id_to_index
        ]
        if not cb_indices:
            return None
        return np.asarray(self.tfidf_matrix[cb_indices].mean(axis=0))

    @staticmethod
    def _min_max_normalize(scores):
        if len(scores) == 0:
            return scores
        min_val, max_val = scores.min(), scores.max()
        if max_val - min_val < 1e-9:
            return np.zeros_like(scores)
        return (scores - min_val) / (max_val - min_val)

    def _get_adaptive_alpha(self, user_idx):
        n_purchases = self.train_matrix[user_idx].nnz
        if n_purchases == 0:
            return self.best_alpha
        elif n_purchases < self.low_activity_threshold:
            return 0.8
        else:
            return 0.2

    def _recommend_hybrid_core(self, user_idx, alpha, n=10, candidate_pool_size=50):
        already_purchased = set(self.train_matrix[user_idx].indices)

        als_ids, _ = self.als_model.recommend(
            user_idx, self.train_matrix[user_idx], N=candidate_pool_size, filter_already_liked_items=True
        )

        profile_vector = self._build_user_content_profile(user_idx)
        content_candidates = []
        if profile_vector is not None:
            scores = cosine_similarity(profile_vector, self.tfidf_matrix).flatten()
            top_cb_indices = scores.argsort()[::-1][:candidate_pool_size]
            for cb_idx in top_cb_indices:
                aid = self.cb_article_ids[cb_idx]
                if aid in self.item_encoder.classes_:
                    content_candidates.append(self.item_encoder.transform([aid])[0])

        candidate_items = list(dict.fromkeys(
            list(als_ids) + content_candidates + list(self.popularity_ranking[:20])
        ))
        candidate_items = [i for i in candidate_items if i not in already_purchased]
        if not candidate_items:
            return []

        candidate_article_ids = self.item_encoder.inverse_transform(candidate_items)
        valid_pairs = [
            (item_idx, self.cb_id_to_index[aid])
            for item_idx, aid in zip(candidate_items, candidate_article_ids)
            if aid in self.cb_id_to_index
        ]
        if not valid_pairs:
            return []

        valid_item_indices, valid_cb_indices = zip(*valid_pairs)
        valid_item_indices = np.array(valid_item_indices)
        valid_cb_indices = np.array(valid_cb_indices)

        user_vector = self.als_model.user_factors[user_idx]
        item_vectors = self.als_model.item_factors[valid_item_indices]
        collab_scores_raw = item_vectors @ user_vector

        if profile_vector is not None:
            content_scores_raw = cosine_similarity(
                profile_vector, self.tfidf_matrix[valid_cb_indices]
            ).flatten()
        else:
            content_scores_raw = np.zeros(len(valid_item_indices))

        content_scores_norm = self._min_max_normalize(content_scores_raw)
        collab_scores_norm = self._min_max_normalize(collab_scores_raw)
        hybrid_scores = alpha * content_scores_norm + (1 - alpha) * collab_scores_norm

        results = list(zip(valid_item_indices, hybrid_scores))
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:n]

    def _popularity_recommend(self, user_idx_or_none, n=10):
        already_purchased = (
            set(self.train_matrix[user_idx_or_none].indices)
            if user_idx_or_none is not None else set()
        )
        recs = []
        for item_idx in self.popularity_ranking:
            if item_idx in already_purchased:
                continue
            recs.append((item_idx, None))
            if len(recs) == n:
                break
        return recs

    def _format_recommendations(self, results):
        rows = []
        for item_idx, score in results:
            article_id = self.item_encoder.inverse_transform([item_idx])[0]
            if article_id not in self.article_lookup.index:
                continue
            meta = self.article_lookup.loc[article_id]
            rows.append({
                "article_id": str(article_id),
                "product_name": str(meta.get("prod_name", "")),
                "category": str(meta.get("product_group_name", "")),
                "score": round(float(score), 4) if score is not None else None,
            })
        return rows

    # ------------------------------------------------------------------ #
    # Public methods — these are what main.py calls
    # ------------------------------------------------------------------ #
    def is_known_user(self, customer_id: str) -> bool:
        return customer_id in self.user_encoder.classes_

    def get_recommendations(self, customer_id: str, top_k: int = 10):
        """
        Returns (recommendations, is_new_user).

        Unknown/new customer_ids are NOT an error — they automatically fall back to the
        popularity baseline. This is the cold-start handling required by the spec.
        """
        if self.is_known_user(customer_id):
            user_idx = self.user_encoder.transform([customer_id])[0]
            alpha = self._get_adaptive_alpha(user_idx)
            results = self._recommend_hybrid_core(user_idx, alpha=alpha, n=top_k)
            if not results:
                # Known user, but no valid hybrid candidates left (rare edge case) ->
                # popularity fallback rather than an empty/broken response.
                results = self._popularity_recommend(user_idx, n=top_k)
            return self._format_recommendations(results), False
        else:
            results = self._popularity_recommend(None, n=top_k)
            return self._format_recommendations(results), True

    def is_known_article(self, article_id) -> bool:
        return article_id in self.cb_id_to_index

    def get_similar_products(self, article_id, top_k: int = 10):
        """Content-based item-item similarity using the fitted TF-IDF matrix."""
        cb_idx = self.cb_id_to_index[article_id]
        item_vector = self.tfidf_matrix[cb_idx]
        scores = cosine_similarity(item_vector, self.tfidf_matrix).flatten()

        ranked_indices = scores.argsort()[::-1]
        rows = []
        for idx in ranked_indices:
            candidate_id = self.cb_article_ids[idx]
            if candidate_id == article_id:
                continue
            if candidate_id not in self.article_lookup.index:
                continue
            meta = self.article_lookup.loc[candidate_id]
            rows.append({
                "article_id": str(candidate_id),
                "product_name": str(meta.get("prod_name", "")),
                "category": str(meta.get("product_group_name", "")),
                "similarity_score": round(float(scores[idx]), 4),
            })
            if len(rows) == top_k:
                break
        return rows
