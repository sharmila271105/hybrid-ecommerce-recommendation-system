"""
Recommendation service for the Hybrid E-Commerce Recommendation System.

Loads pre-trained recommendation artifacts once at startup and provides
recommendation methods to the FastAPI layer.

No model training happens here.
"""

import os
import pickle

import numpy as np
import pandas as pd
from scipy.sparse import load_npz
from sklearn.metrics.pairwise import cosine_similarity
from huggingface_hub import hf_hub_download

HF_REPO_ID = "Sharmila271105/ecommerce-recommendation-artifacts"

class RecommendationService:

    def __init__(self, base_dir=None):

        # ---------------------------------------------------------
        # Project/artifact location
        # Priority:
        # 1. Explicit base_dir
        # 2. RECSYS_BASE_DIR environment variable
        # 3. Current project directory
        # ---------------------------------------------------------
        self.base_dir = (
            base_dir
            or os.environ.get("RECSYS_BASE_DIR")
            or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )

        self.processed_data_dir = os.path.join(
            self.base_dir, "processed_data"
        )

        self.models_dir = os.path.join(
            self.base_dir, "models"
        )

        self.artifacts_dir = os.path.join(
            self.base_dir, "artifacts"
        )

        self.cb_artifacts_dir = os.path.join(
            self.base_dir, "cb_artifacts"
        )

        self._load_artifacts()

    # =========================================================
    # LOAD ARTIFACTS
    # =========================================================

    def _load_artifacts(self):

        required_dirs = [
            self.processed_data_dir,
            self.models_dir,
            self.artifacts_dir,
        ]

        missing = [
            path for path in required_dirs
            if not os.path.exists(path)
        ]

        if missing:
            raise FileNotFoundError(
                f"Required artifact directories are missing: {missing}. "
                f"Set RECSYS_BASE_DIR to the folder containing "
                f"processed_data/, models/, and artifacts/."
            )

        # -----------------------------------------------------
        # Product metadata
        # -----------------------------------------------------

        self.processed_articles = pd.read_csv(
            os.path.join(
                self.processed_data_dir,
                "processed_articles.csv"
            )
        )

        self.article_lookup = self.processed_articles.set_index(
            "article_id"
        )

        # -----------------------------------------------------
        # Content-based artifacts
        # -----------------------------------------------------

        content_features = pd.read_csv(
            os.path.join(
                self.processed_data_dir,
                "content_features.csv"
            )
        )

        self.cb_article_ids = content_features[
            "article_id"
        ].values

        self.cb_id_to_index = {
            aid: idx
            for idx, aid in enumerate(self.cb_article_ids)
        }

        vectorizer_path = os.path.join(
            self.cb_artifacts_dir,
            "tfidf_vectorizer.pkl"
        )

        matrix_path = os.path.join(
            self.cb_artifacts_dir,
            "tfidf_matrix.npz"
        )

        if not os.path.exists(vectorizer_path):
            raise FileNotFoundError(
                f"Missing TF-IDF vectorizer: {vectorizer_path}"
            )

        if not os.path.exists(matrix_path):
            raise FileNotFoundError(
                f"Missing TF-IDF matrix: {matrix_path}"
            )

        with open(vectorizer_path, "rb") as f:
            self.tfidf_vectorizer = pickle.load(f)

        self.tfidf_matrix = load_npz(matrix_path)

        # -----------------------------------------------------
        # Encoders
        # -----------------------------------------------------

        encoder_path = os.path.join(
            self.processed_data_dir,
            "label_encoders.pkl"
        )

        with open(encoder_path, "rb") as f:
            encoders = pickle.load(f)

        self.user_encoder = encoders["user_encoder"]
        self.item_encoder = encoders["item_encoder"]

        # -----------------------------------------------------
        # ALS model
        # -----------------------------------------------------

        als_path = os.path.join(
            self.models_dir,
            "als_model.pkl"
        )

        with open(als_path, "rb") as f:
            als_bundle = pickle.load(f)

        self.als_model = als_bundle["model"]

        # -----------------------------------------------------
        # Training interaction matrix
        # -----------------------------------------------------

        train_matrix_path = os.path.join(
            self.artifacts_dir,
            "train_matrix.npz"
        )

        self.train_matrix = load_npz(
            train_matrix_path
        )

        # -----------------------------------------------------
        # Popularity baseline
        # -----------------------------------------------------

        popularity_path = os.path.join(
            self.artifacts_dir,
            "popularity_baseline.pkl"
        )

        with open(popularity_path, "rb") as f:
            popularity_bundle = pickle.load(f)

        self.popularity_ranking = popularity_bundle[
            "popularity_ranking"
        ]

        # -----------------------------------------------------
        # Hybrid configuration
        # -----------------------------------------------------

        hybrid_config_path = os.path.join(
            self.models_dir,
            "hybrid_model_config.pkl"
        )

        with open(hybrid_config_path, "rb") as f:
            hybrid_config = pickle.load(f)

        self.best_alpha = hybrid_config["best_alpha"]

        self.low_activity_threshold = hybrid_config[
            "low_activity_threshold"
        ]

        print(
            "[RecommendationService] "
            "All artifacts loaded successfully."
        )

    # =========================================================
    # CONTENT PROFILE
    # =========================================================

    def _build_user_content_profile(self, user_idx):

        purchased_item_indices = (
            self.train_matrix[user_idx].indices
        )

        if len(purchased_item_indices) == 0:
            return None

        purchased_article_ids = (
            self.item_encoder.inverse_transform(
                purchased_item_indices
            )
        )

        cb_indices = [
            self.cb_id_to_index[aid]
            for aid in purchased_article_ids
            if aid in self.cb_id_to_index
        ]

        if not cb_indices:
            return None

        return np.asarray(
            self.tfidf_matrix[cb_indices].mean(axis=0)
        )

    # =========================================================
    # SCORE NORMALIZATION
    # =========================================================

    @staticmethod
    def _min_max_normalize(scores):

        if len(scores) == 0:
            return scores

        min_val = scores.min()
        max_val = scores.max()

        if max_val - min_val < 1e-9:
            return np.zeros_like(scores)

        return (
            (scores - min_val)
            / (max_val - min_val)
        )

    # =========================================================
    # ADAPTIVE ALPHA
    # =========================================================

    def _get_adaptive_alpha(self, user_idx):

        n_purchases = self.train_matrix[user_idx].nnz

        if n_purchases == 0:
            return self.best_alpha

        elif n_purchases < self.low_activity_threshold:
            return 0.8

        else:
            return 0.2

    # =========================================================
    # HYBRID RECOMMENDATION
    # =========================================================

    def _recommend_hybrid_core(
        self,
        user_idx,
        alpha,
        n=10,
        candidate_pool_size=50
    ):

        already_purchased = set(
            self.train_matrix[user_idx].indices
        )

        # -----------------------------------------------------
        # ALS candidates
        # -----------------------------------------------------

        als_ids, _ = self.als_model.recommend(
            user_idx,
            self.train_matrix[user_idx],
            N=candidate_pool_size,
            filter_already_liked_items=True
        )

        # -----------------------------------------------------
        # Content-based candidates
        # -----------------------------------------------------

        profile_vector = (
            self._build_user_content_profile(user_idx)
        )

        content_candidates = []

        if profile_vector is not None:

            scores = cosine_similarity(
                profile_vector,
                self.tfidf_matrix
            ).flatten()

            top_cb_indices = (
                scores.argsort()[::-1]
                [:candidate_pool_size]
            )

            for cb_idx in top_cb_indices:

                article_id = self.cb_article_ids[cb_idx]

                if article_id in self.item_encoder.classes_:

                    item_idx = self.item_encoder.transform(
                        [article_id]
                    )[0]

                    content_candidates.append(item_idx)

        # -----------------------------------------------------
        # Combine candidates
        # -----------------------------------------------------

        candidate_items = list(
            dict.fromkeys(
                list(als_ids)
                + content_candidates
                + list(self.popularity_ranking[:20])
            )
        )

        candidate_items = [
            item
            for item in candidate_items
            if item not in already_purchased
        ]

        if not candidate_items:
            return []

        # -----------------------------------------------------
        # Map candidates to content indices
        # -----------------------------------------------------

        candidate_article_ids = (
            self.item_encoder.inverse_transform(
                candidate_items
            )
        )

        valid_pairs = [
            (item_idx, self.cb_id_to_index[article_id])
            for item_idx, article_id
            in zip(candidate_items, candidate_article_ids)
            if article_id in self.cb_id_to_index
        ]

        if not valid_pairs:
            return []

        valid_item_indices, valid_cb_indices = zip(
            *valid_pairs
        )

        valid_item_indices = np.array(
            valid_item_indices
        )

        valid_cb_indices = np.array(
            valid_cb_indices
        )

        # -----------------------------------------------------
        # Collaborative scores
        # -----------------------------------------------------

        user_vector = (
            self.als_model.user_factors[user_idx]
        )

        item_vectors = (
            self.als_model.item_factors[
                valid_item_indices
            ]
        )

        collab_scores_raw = (
            item_vectors @ user_vector
        )

        # -----------------------------------------------------
        # Content scores
        # -----------------------------------------------------

        if profile_vector is not None:

            content_scores_raw = cosine_similarity(
                profile_vector,
                self.tfidf_matrix[
                    valid_cb_indices
                ]
            ).flatten()

        else:

            content_scores_raw = np.zeros(
                len(valid_item_indices)
            )

        # -----------------------------------------------------
        # Normalize and combine
        # -----------------------------------------------------

        content_scores_norm = (
            self._min_max_normalize(
                content_scores_raw
            )
        )

        collab_scores_norm = (
            self._min_max_normalize(
                collab_scores_raw
            )
        )

        hybrid_scores = (
            alpha * content_scores_norm
            + (1 - alpha) * collab_scores_norm
        )

        results = list(
            zip(
                valid_item_indices,
                hybrid_scores
            )
        )

        results.sort(
            key=lambda x: x[1],
            reverse=True
        )

        return results[:n]

    # =========================================================
    # POPULARITY FALLBACK
    # =========================================================

    def _popularity_recommend(
        self,
        user_idx_or_none,
        n=10
    ):

        if user_idx_or_none is not None:

            already_purchased = set(
                self.train_matrix[
                    user_idx_or_none
                ].indices
            )

        else:

            already_purchased = set()

        recommendations = []

        for item_idx in self.popularity_ranking:

            if item_idx in already_purchased:
                continue

            recommendations.append(
                (item_idx, None)
            )

            if len(recommendations) == n:
                break

        return recommendations

    # =========================================================
    # FORMAT RESULTS
    # =========================================================

    def _format_recommendations(self, results):

        rows = []

        for item_idx, score in results:

            article_id = (
                self.item_encoder.inverse_transform(
                    [item_idx]
                )[0]
            )

            if article_id not in self.article_lookup.index:
                continue

            meta = self.article_lookup.loc[
                article_id
            ]

            rows.append({
                "article_id": str(article_id),
                "product_name": str(
                    meta.get("prod_name", "")
                ),
                "category": str(
                    meta.get("product_group_name", "")
                ),
                "score": (
                    round(float(score), 4)
                    if score is not None
                    else None
                )
            })

        return rows

    # =========================================================
    # PUBLIC METHODS
    # =========================================================

    def is_known_user(self, customer_id: str) -> bool:

        return customer_id in self.user_encoder.classes_

    def get_recommendations(
        self,
        customer_id: str,
        top_k: int = 10
    ):

        if self.is_known_user(customer_id):

            user_idx = self.user_encoder.transform(
                [customer_id]
            )[0]

            alpha = self._get_adaptive_alpha(
                user_idx
            )

            results = self._recommend_hybrid_core(
                user_idx,
                alpha=alpha,
                n=top_k
            )

            if not results:

                results = self._popularity_recommend(
                    user_idx,
                    n=top_k
                )

            return (
                self._format_recommendations(results),
                False
            )

        # New user → popularity fallback

        results = self._popularity_recommend(
            None,
            n=top_k
        )

        return (
            self._format_recommendations(results),
            True
        )

    def is_known_article(self, article_id) -> bool:

        return article_id in self.cb_id_to_index

    def get_similar_products(
        self,
        article_id,
        top_k: int = 10
    ):

        cb_idx = self.cb_id_to_index[
            article_id
        ]

        item_vector = self.tfidf_matrix[
            cb_idx
        ]

        scores = cosine_similarity(
            item_vector,
            self.tfidf_matrix
        ).flatten()

        ranked_indices = (
            scores.argsort()[::-1]
        )

        rows = []

        for idx in ranked_indices:

            candidate_id = (
                self.cb_article_ids[idx]
            )

            if candidate_id == article_id:
                continue

            if candidate_id not in self.article_lookup.index:
                continue

            meta = self.article_lookup.loc[
                candidate_id
            ]

            rows.append({
                "article_id": str(candidate_id),
                "product_name": str(
                    meta.get("prod_name", "")
                ),
                "category": str(
                    meta.get("product_group_name", "")
                ),
                "similarity_score": round(
                    float(scores[idx]),
                    4
                )
            })

            if len(rows) == top_k:
                break

        return rows
