"""
Memory-efficient recommendation service for the Hybrid E-Commerce
Recommendation System.

This deployment version does NOT load:
- als_model.pkl
- label_encoders.pkl
- train_matrix.npz
- processed_articles.csv
- content_features.csv
- tfidf_vectorizer.pkl

Instead it uses compact inference artifacts generated in Colab.
"""

import os
import pickle

import numpy as np
import pandas as pd

from scipy.sparse import load_npz
from sklearn.metrics.pairwise import cosine_similarity

from huggingface_hub import hf_hub_download


# =========================================================
# HUGGING FACE CONFIGURATION
# =========================================================

HF_REPO_ID = (
    "Sharmila271105/ecommerce-recommendation-artifacts"
)


class RecommendationService:

    # =====================================================
    # INITIALIZATION
    # =====================================================

    def __init__(self, base_dir=None):

        self.base_dir = (
            base_dir
            or os.environ.get("RECSYS_BASE_DIR")
            or os.path.dirname(
                os.path.dirname(
                    os.path.abspath(__file__)
                )
            )
        )

        self._load_artifacts()

    # =====================================================
    # HUGGING FACE DOWNLOAD
    # =====================================================

    def _get_artifact(self, filename):

        print(
            f"[RecommendationService] "
            f"Loading {filename} from Hugging Face..."
        )

        return hf_hub_download(
            repo_id=HF_REPO_ID,
            filename=filename,
            repo_type="model",
        )

    # =====================================================
    # LOAD ARTIFACTS
    # =====================================================

    def _load_artifacts(self):

        print(
            "[RecommendationService] "
            "Loading optimized inference artifacts..."
        )

        # -------------------------------------------------
        # USER IDS
        # -------------------------------------------------

        user_ids_path = self._get_artifact(
            "user_ids.npy"
        )

        self.user_ids = np.load(
            user_ids_path,
            allow_pickle=True,
        )

        self.user_id_to_index = {
            str(user_id): idx
            for idx, user_id
            in enumerate(self.user_ids)
        }

        print(
            "Users:",
            len(self.user_ids)
        )

        # -------------------------------------------------
        # ITEM IDS
        # -------------------------------------------------

        item_ids_path = self._get_artifact(
            "item_ids.npy"
        )

        self.item_ids = np.load(
            item_ids_path,
            allow_pickle=True,
        )

        self.item_id_to_index = {
            self._normalize_article_id(article_id): idx
            for idx, article_id
            in enumerate(self.item_ids)
        }

        print(
            "Items:",
            len(self.item_ids)
        )

        # -------------------------------------------------
        # ALS USER FACTORS
        # -------------------------------------------------

        user_factors_path = self._get_artifact(
            "user_factors.npy"
        )

        # MEMORY MAPPED
        self.user_factors = np.load(
            user_factors_path,
            mmap_mode="r",
        )

        # -------------------------------------------------
        # ALS ITEM FACTORS
        # -------------------------------------------------

        item_factors_path = self._get_artifact(
            "item_factors.npy"
        )

        # MEMORY MAPPED
        self.item_factors = np.load(
            item_factors_path,
            mmap_mode="r",
        )

        print(
            "User factors:",
            self.user_factors.shape
        )

        print(
            "Item factors:",
            self.item_factors.shape
        )

        # -------------------------------------------------
        # USER PURCHASE HISTORY
        # -------------------------------------------------

        indptr_path = self._get_artifact(
            "train_indptr_uint32.npy"
        )

        indices_path = self._get_artifact(
            "train_indices_uint32.npy"
        )

        self.train_indptr = np.load(
            indptr_path,
            mmap_mode="r",
        )

        self.train_indices = np.load(
            indices_path,
            mmap_mode="r",
        )

        print(
            "Purchase history:",
            len(self.train_indptr) - 1,
            "users"
        )

        # -------------------------------------------------
        # TF-IDF MATRIX
        # -------------------------------------------------

        tfidf_path = self._get_artifact(
            "tfidf_matrix_float32.npz"
        )

        self.tfidf_matrix = load_npz(
            tfidf_path
        )

        print(
            "TF-IDF:",
            self.tfidf_matrix.shape,
            self.tfidf_matrix.dtype,
        )

        # -------------------------------------------------
        # CONTENT ARTICLE IDS
        # -------------------------------------------------

        cb_ids_path = self._get_artifact(
            "cb_article_ids.npy"
        )

        self.cb_article_ids = np.load(
            cb_ids_path,
            allow_pickle=True,
        )

        self.cb_id_to_index = {
            self._normalize_article_id(article_id): idx
            for idx, article_id
            in enumerate(self.cb_article_ids)
        }

        # -------------------------------------------------
        # PRODUCT METADATA
        # -------------------------------------------------

        metadata_path = self._get_artifact(
            "article_metadata.csv"
        )

        self.article_lookup = pd.read_csv(
            metadata_path,
            dtype={
                "article_id": str,
                "prod_name": str,
                "product_group_name": str,
            },
        )

        self.article_lookup["article_id"] = (
            self.article_lookup[
                "article_id"
            ].map(
                self._normalize_article_id
            )
        )

        self.article_lookup = (
            self.article_lookup
            .drop_duplicates(
                "article_id"
            )
            .set_index("article_id")
        )

        # -------------------------------------------------
        # POPULARITY
        # -------------------------------------------------

        popularity_path = self._get_artifact(
            "popularity_baseline.pkl"
        )

        with open(
            popularity_path,
            "rb",
        ) as f:

            popularity_bundle = pickle.load(f)

        self.popularity_ranking = list(
            popularity_bundle[
                "popularity_ranking"
            ]
        )

        # -------------------------------------------------
        # HYBRID CONFIG
        # -------------------------------------------------

        hybrid_path = self._get_artifact(
            "hybrid_model_config.pkl"
        )

        with open(
            hybrid_path,
            "rb",
        ) as f:

            hybrid_config = pickle.load(f)

        self.best_alpha = float(
            hybrid_config[
                "best_alpha"
            ]
        )

        self.low_activity_threshold = int(
            hybrid_config[
                "low_activity_threshold"
            ]
        )

        print(
            "[RecommendationService] "
            "All optimized artifacts loaded successfully."
        )

    # =====================================================
    # ID NORMALIZATION
    # =====================================================

    @staticmethod
    def _normalize_article_id(article_id):

        try:
            return int(article_id)
        except (ValueError, TypeError):
            return str(article_id)

    # =====================================================
    # USER PURCHASED ITEMS
    # =====================================================

    def _get_purchased_items(
        self,
        user_idx,
    ):

        start = int(
            self.train_indptr[user_idx]
        )

        end = int(
            self.train_indptr[user_idx + 1]
        )

        return self.train_indices[
            start:end
        ]

    # =====================================================
    # ADAPTIVE ALPHA
    # =====================================================

    def _get_adaptive_alpha(
        self,
        user_idx,
    ):

        start = int(
            self.train_indptr[user_idx]
        )

        end = int(
            self.train_indptr[user_idx + 1]
        )

        n_purchases = end - start

        if n_purchases == 0:

            return self.best_alpha

        if (
            n_purchases
            < self.low_activity_threshold
        ):

            return 0.8

        return 0.2

    # =====================================================
    # USER CONTENT PROFILE
    # =====================================================

    def _build_user_content_profile(
        self,
        user_idx,
    ):

        purchased_items = (
            self._get_purchased_items(
                user_idx
            )
        )

        if len(purchased_items) == 0:
            return None

        profile_rows = []

        for item_idx in purchased_items:

            if item_idx >= len(
                self.item_ids
            ):
                continue

            article_id = (
                self._normalize_article_id(
                    self.item_ids[
                        int(item_idx)
                    ]
                )
            )

            cb_idx = (
                self.cb_id_to_index.get(
                    article_id
                )
            )

            if cb_idx is not None:
                profile_rows.append(
                    cb_idx
                )

        if not profile_rows:
            return None

        # Mean of sparse TF-IDF vectors.
        profile = (
            self.tfidf_matrix[
                profile_rows
            ].mean(axis=0)
        )

        return np.asarray(
            profile,
            dtype=np.float32,
        )

    # =====================================================
    # MIN-MAX NORMALIZATION
    # =====================================================

    @staticmethod
    def _min_max_normalize(scores):

        scores = np.asarray(
            scores,
            dtype=np.float32,
        )

        if len(scores) == 0:
            return scores

        min_val = scores.min()
        max_val = scores.max()

        if (
            max_val - min_val
            < 1e-9
        ):

            return np.zeros_like(
                scores
            )

        return (
            scores - min_val
        ) / (
            max_val - min_val
        )

    # =====================================================
    # ALS CANDIDATES
    # =====================================================

    def _get_als_candidates(
        self,
        user_idx,
        already_purchased,
        candidate_pool_size=50,
    ):

        user_vector = np.asarray(
            self.user_factors[
                user_idx
            ],
            dtype=np.float32,
        )

        n_items = self.item_factors.shape[0]

        # Process items in chunks so we NEVER
        # create a 100k+ score array unnecessarily.
        chunk_size = 8192

        candidate_pairs = []

        for start in range(
            0,
            n_items,
            chunk_size,
        ):

            end = min(
                start + chunk_size,
                n_items,
            )

            item_vectors = np.asarray(
                self.item_factors[
                    start:end
                ],
                dtype=np.float32,
            )

            scores = (
                item_vectors
                @ user_vector
            )

            # Remove already purchased products.
            local_indices = np.arange(
                start,
                end,
                dtype=np.int64,
            )

            if already_purchased:

                purchased_mask = np.isin(
                    local_indices,
                    list(
                        already_purchased
                    ),
                )

                scores[
                    purchased_mask
                ] = -np.inf

            k = min(
                candidate_pool_size,
                len(scores),
            )

            if k == 0:
                continue

            top_local = np.argpartition(
                -scores,
                k - 1,
            )[:k]

            for local_idx in top_local:

                score = float(
                    scores[local_idx]
                )

                if np.isfinite(score):

                    candidate_pairs.append(
                        (
                            int(
                                start
                                + local_idx
                            ),
                            score,
                        )
                    )

        if not candidate_pairs:
            return []

        candidate_pairs.sort(
            key=lambda x: x[1],
            reverse=True,
        )

        return [
            item_idx
            for item_idx, _
            in candidate_pairs[
                :candidate_pool_size
            ]
        ]

    # =====================================================
    # CONTENT CANDIDATES
    # =====================================================

    def _get_content_candidates(
        self,
        profile_vector,
        candidate_pool_size=50,
    ):

        if profile_vector is None:
            return []

        scores = cosine_similarity(
            profile_vector,
            self.tfidf_matrix,
        ).ravel()

        k = min(
            candidate_pool_size,
            len(scores),
        )

        if k == 0:
            return []

        # Avoid full argsort.
        top_indices = np.argpartition(
            -scores,
            k - 1,
        )[:k]

        top_indices = top_indices[
            np.argsort(
                -scores[top_indices]
            )
        ]

        candidates = []

        for cb_idx in top_indices:

            article_id = (
                self._normalize_article_id(
                    self.cb_article_ids[
                        cb_idx
                    ]
                )
            )

            item_idx = (
                self.item_id_to_index.get(
                    article_id
                )
            )

            if item_idx is not None:
                candidates.append(
                    int(item_idx)
                )

        return candidates

    # =====================================================
    # HYBRID RECOMMENDATION
    # =====================================================

    def _recommend_hybrid_core(
        self,
        user_idx,
        alpha,
        n=10,
        candidate_pool_size=50,
    ):

        purchased = (
            self._get_purchased_items(
                user_idx
            )
        )

        already_purchased = set(
            int(x)
            for x in purchased
        )

        # -------------------------------------------------
        # ALS candidates
        # -------------------------------------------------

        als_candidates = (
            self._get_als_candidates(
                user_idx,
                already_purchased,
                candidate_pool_size,
            )
        )

        # -------------------------------------------------
        # Content profile
        # -------------------------------------------------

        profile_vector = (
            self._build_user_content_profile(
                user_idx
            )
        )

        # -------------------------------------------------
        # Content candidates
        # -------------------------------------------------

        content_candidates = (
            self._get_content_candidates(
                profile_vector,
                candidate_pool_size,
            )
        )

        # -------------------------------------------------
        # Popularity candidates
        # -------------------------------------------------

        popularity_candidates = []

        for item_idx in (
            self.popularity_ranking[:20]
        ):

            item_idx = int(
                item_idx
            )

            if (
                item_idx
                not in already_purchased
            ):

                popularity_candidates.append(
                    item_idx
                )

        # -------------------------------------------------
        # Combine candidates
        # -------------------------------------------------

        candidate_items = list(
            dict.fromkeys(
                als_candidates
                + content_candidates
                + popularity_candidates
            )
        )

        candidate_items = [
            int(item_idx)
            for item_idx in candidate_items
            if int(item_idx)
            not in already_purchased
        ]

        if not candidate_items:
            return []

        # -------------------------------------------------
        # Collaborative scores
        # -------------------------------------------------

        user_vector = np.asarray(
            self.user_factors[
                user_idx
            ],
            dtype=np.float32,
        )

        item_indices = np.asarray(
            candidate_items,
            dtype=np.int64,
        )

        item_vectors = np.asarray(
            self.item_factors[
                item_indices
            ],
            dtype=np.float32,
        )

        collab_scores = (
            item_vectors
            @ user_vector
        )

        # -------------------------------------------------
        # Content scores
        # -------------------------------------------------

        if profile_vector is not None:

            cb_indices = []

            valid_positions = []

            for pos, item_idx in enumerate(
                candidate_items
            ):

                article_id = (
                    self._normalize_article_id(
                        self.item_ids[
                            item_idx
                        ]
                    )
                )

                cb_idx = (
                    self.cb_id_to_index.get(
                        article_id
                    )
                )

                if cb_idx is not None:

                    cb_indices.append(
                        cb_idx
                    )

                    valid_positions.append(
                        pos
                    )

            content_scores = np.zeros(
                len(candidate_items),
                dtype=np.float32,
            )

            if cb_indices:

                selected_matrix = (
                    self.tfidf_matrix[
                        cb_indices
                    ]
                )

                selected_scores = (
                    cosine_similarity(
                        profile_vector,
                        selected_matrix,
                    ).ravel()
                )

                for pos, score in zip(
                    valid_positions,
                    selected_scores,
                ):

                    content_scores[
                        pos
                    ] = score

        else:

            content_scores = np.zeros(
                len(candidate_items),
                dtype=np.float32,
            )

        # -------------------------------------------------
        # Normalize
        # -------------------------------------------------

        collab_norm = (
            self._min_max_normalize(
                collab_scores
            )
        )

        content_norm = (
            self._min_max_normalize(
                content_scores
            )
        )

        # -------------------------------------------------
        # Hybrid score
        # -------------------------------------------------

        hybrid_scores = (
            alpha
            * content_norm
            + (
                1.0 - alpha
            )
            * collab_norm
        )

        # -------------------------------------------------
        # Rank
        # -------------------------------------------------

        order = np.argsort(
            -hybrid_scores
        )

        results = []

        for idx in order[:n]:

            results.append(
                (
                    int(
                        candidate_items[idx]
                    ),
                    float(
                        hybrid_scores[idx]
                    ),
                )
            )

        return results

    # =====================================================
    # POPULARITY FALLBACK
    # =====================================================

    def _popularity_recommend(
        self,
        user_idx_or_none,
        n=10,
    ):

        if user_idx_or_none is not None:

            already_purchased = set(
                int(x)
                for x in
                self._get_purchased_items(
                    user_idx_or_none
                )
            )

        else:

            already_purchased = set()

        recommendations = []

        for item_idx in (
            self.popularity_ranking
        ):

            item_idx = int(
                item_idx
            )

            if (
                item_idx
                in already_purchased
            ):
                continue

            recommendations.append(
                (
                    item_idx,
                    None,
                )
            )

            if len(
                recommendations
            ) == n:

                break

        return recommendations

    # =====================================================
    # FORMAT RESULTS
    # =====================================================

    def _format_recommendations(
        self,
        results,
    ):

        rows = []

        for item_idx, score in results:

            if (
                item_idx < 0
                or item_idx
                >= len(self.item_ids)
            ):
                continue

            article_id = (
                self._normalize_article_id(
                    self.item_ids[
                        item_idx
                    ]
                )
            )

            if (
                article_id
                not in self.article_lookup.index
            ):
                continue

            meta = (
                self.article_lookup.loc[
                    article_id
                ]
            )

            rows.append(
                {
                    "article_id": str(
                        article_id
                    ),
                    "product_name": str(
                        meta.get(
                            "prod_name",
                            "",
                        )
                    ),
                    "category": str(
                        meta.get(
                            "product_group_name",
                            "",
                        )
                    ),
                    "score": (
                        round(
                            float(score),
                            4,
                        )
                        if score is not None
                        else None
                    ),
                }
            )

        return rows

    # =====================================================
    # PUBLIC METHODS
    # =====================================================

    def is_known_user(
        self,
        customer_id: str,
    ) -> bool:

        return (
            str(customer_id)
            in self.user_id_to_index
        )

    def get_recommendations(
        self,
        customer_id: str,
        top_k: int = 10,
    ):

        customer_id = str(
            customer_id
        )

        if self.is_known_user(
            customer_id
        ):

            user_idx = (
                self.user_id_to_index[
                    customer_id
                ]
            )

            alpha = (
                self._get_adaptive_alpha(
                    user_idx
                )
            )

            results = (
                self._recommend_hybrid_core(
                    user_idx,
                    alpha=alpha,
                    n=top_k,
                )
            )

            if not results:

                results = (
                    self._popularity_recommend(
                        user_idx,
                        n=top_k,
                    )
                )

            return (
                self._format_recommendations(
                    results
                ),
                False,
            )

        # -------------------------------------------------
        # New user → popularity fallback
        # -------------------------------------------------

        results = (
            self._popularity_recommend(
                None,
                n=top_k,
            )
        )

        return (
            self._format_recommendations(
                results
            ),
            True,
        )

    # =====================================================
    # ARTICLE LOOKUP
    # =====================================================

    def is_known_article(
        self,
        article_id,
    ) -> bool:

        article_id = (
            self._normalize_article_id(
                article_id
            )
        )

        return (
            article_id
            in self.cb_id_to_index
        )

    # =====================================================
    # SIMILAR PRODUCTS
    # =====================================================

    def get_similar_products(
        self,
        article_id,
        top_k: int = 10,
    ):

        article_id = (
            self._normalize_article_id(
                article_id
            )
        )

        cb_idx = (
            self.cb_id_to_index[
                article_id
            ]
        )

        item_vector = (
            self.tfidf_matrix[
                cb_idx
            ]
        )

        scores = cosine_similarity(
            item_vector,
            self.tfidf_matrix,
        ).ravel()

        k = min(
            top_k + 1,
            len(scores),
        )

        candidate_indices = (
            np.argpartition(
                -scores,
                k - 1,
            )[:k]
        )

        candidate_indices = (
            candidate_indices[
                np.argsort(
                    -scores[
                        candidate_indices
                    ]
                )
            ]
        )

        rows = []

        for idx in candidate_indices:

            candidate_id = (
                self._normalize_article_id(
                    self.cb_article_ids[
                        idx
                    ]
                )
            )

            if (
                candidate_id
                == article_id
            ):
                continue

            if (
                candidate_id
                not in self.article_lookup.index
            ):
                continue

            meta = (
                self.article_lookup.loc[
                    candidate_id
                ]
            )

            rows.append(
                {
                    "article_id": str(
                        candidate_id
                    ),
                    "product_name": str(
                        meta.get(
                            "prod_name",
                            "",
                        )
                    ),
                    "category": str(
                        meta.get(
                            "product_group_name",
                            "",
                        )
                    ),
                    "similarity_score": round(
                        float(
                            scores[idx]
                        ),
                        4,
                    ),
                }
            )

            if len(rows) == top_k:
                break

        return rows
