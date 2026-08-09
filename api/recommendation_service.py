"""
Lightweight inference service for the deployed H&M recommendation API.

The heavy ML model is used offline to generate recommendation_cache.pkl.
Render only performs fast lookup + product metadata formatting.

Artifacts loaded at runtime:
- recommendation_cache.pkl
- article_metadata.csv
- popularity_baseline.pkl
- tfidf_matrix_float32.npz
- cb_article_ids.npy
"""

import os
import pickle

import numpy as np
import pandas as pd

from scipy.sparse import load_npz
from sklearn.metrics.pairwise import cosine_similarity
from huggingface_hub import hf_hub_download


HF_REPO_ID = (
    "Sharmila271105/ecommerce-recommendation-artifacts"
)


class RecommendationService:

    def __init__(self, base_dir=None):

        self.base_dir = (
            base_dir
            or os.environ.get("RECSYS_BASE_DIR")
        )

        self._load_artifacts()

    # =====================================================
    # HUGGING FACE
    # =====================================================

    def _download(self, filename):

        print(
            f"[RecommendationService] "
            f"Downloading {filename}..."
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
            "Loading lightweight deployment artifacts..."
        )

        # -------------------------------------------------
        # RECOMMENDATION CACHE
        # -------------------------------------------------

        cache_path = self._download(
            "recommendation_cache.pkl"
        )

        with open(
            cache_path,
            "rb"
        ) as f:

            self.recommendation_cache = (
                pickle.load(f)
            )

        print(
            "Cached users:",
            len(
                self.recommendation_cache
            )
        )

        # -------------------------------------------------
        # ARTICLE METADATA
        # -------------------------------------------------

        metadata_path = self._download(
            "article_metadata.csv"
        )

        articles = pd.read_csv(
            metadata_path,
            dtype={
                "article_id": str,
                "prod_name": str,
                "product_group_name": str,
            },
        )

        articles["article_id"] = (
            articles["article_id"].astype(str)
        )

        self.article_lookup = (
            articles
            .drop_duplicates(
                "article_id"
            )
            .set_index(
                "article_id"
            )
        )

        print(
            "Articles:",
            len(
                self.article_lookup
            )
        )

        # -------------------------------------------------
        # POPULARITY
        # -------------------------------------------------

        popularity_path = self._download(
            "popularity_baseline.pkl"
        )

        with open(
            popularity_path,
            "rb"
        ) as f:

            popularity_bundle = (
                pickle.load(f)
            )

        self.popularity_ranking = (
            popularity_bundle[
                "popularity_ranking"
            ]
        )

        # -------------------------------------------------
        # TF-IDF
        # -------------------------------------------------

        tfidf_path = self._download(
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

        cb_ids_path = self._download(
            "cb_article_ids.npy"
        )

        self.cb_article_ids = np.load(
            cb_ids_path,
            allow_pickle=True,
        )

        self.cb_id_to_index = {
            str(article_id): idx
            for idx, article_id
            in enumerate(
                self.cb_article_ids
            )
        }

        print(
            "[RecommendationService] "
            "All lightweight artifacts loaded."
        )

    # =====================================================
    # POPULARITY FALLBACK
    # =====================================================

    def _popularity_recommend(
        self,
        n=10,
    ):

        results = []

        for item_idx in (
            self.popularity_ranking
        ):

            try:

                article_id = str(
                    int(item_idx)
                )

            except (
                ValueError,
                TypeError,
            ):

                article_id = str(
                    item_idx
                )

            if (
                article_id
                not in self.article_lookup.index
            ):
                continue

            results.append(
                (
                    article_id,
                    None,
                )
            )

            if len(results) >= n:
                break

        return results

    # =====================================================
    # FORMAT
    # =====================================================

    def _format_recommendations(
        self,
        results,
    ):

        rows = []

        for article_id, score in results:

            article_id = str(
                article_id
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
                    "article_id": article_id,

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
    # PUBLIC RECOMMENDATIONS
    # =====================================================

    def get_recommendations(
        self,
        customer_id: str,
        top_k: int = 10,
    ):

        customer_id = str(
            customer_id
        )

        # -------------------------------------------------
        # CACHED USER
        # -------------------------------------------------

        if (
            customer_id
            in self.recommendation_cache
        ):

            cached = (
                self.recommendation_cache[
                    customer_id
                ]
            )

            results = []

            for item in cached[:top_k]:

                results.append(
                    (
                        str(
                            item[
                                "article_id"
                            ]
                        ),
                        item.get(
                            "score"
                        ),
                    )
                )

            return (
                self._format_recommendations(
                    results
                ),
                False,
            )

        # -------------------------------------------------
        # UNKNOWN / NON-CACHED USER
        # -------------------------------------------------

        results = (
            self._popularity_recommend(
                n=top_k
            )
        )

        return (
            self._format_recommendations(
                results
            ),
            True,
        )

    # =====================================================
    # ARTICLE
    # =====================================================

    def is_known_article(
        self,
        article_id,
    ):

        article_id = str(
            article_id
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
        top_k=10,
    ):

        article_id = str(
            article_id
        )

        if not self.is_known_article(
            article_id
        ):
            return []

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

        # Calculate similarity against catalog.
        scores = cosine_similarity(
            item_vector,
            self.tfidf_matrix,
        ).ravel()

        # We need top_k + original item.
        k = min(
            top_k + 1,
            len(scores),
        )

        top_indices = np.argpartition(
            -scores,
            k - 1,
        )[:k]

        top_indices = (
            top_indices[
                np.argsort(
                    -scores[
                        top_indices
                    ]
                )
            ]
        )

        rows = []

        for idx in top_indices:

            candidate_id = str(
                self.cb_article_ids[
                    idx
                ]
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
                    "article_id": candidate_id,

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

            if len(rows) >= top_k:
                break

        return rows
