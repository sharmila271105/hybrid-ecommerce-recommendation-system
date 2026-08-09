"""
main.py

FastAPI application entrypoint.

Responsibilities:
- Create the FastAPI app and its routes.
- Instantiate RecommendationService ONCE at process startup (not per-request).
- Validate input (top_k, path params) via FastAPI/Pydantic.
- Translate service-layer conditions (unknown user/article, bad input, missing
  artifacts) into proper HTTP status codes.

No ML logic lives in this file — see recommendation_service.py for that.

Run standalone with:
    uvicorn api.main:app --reload
"""

from typing import List, Optional

from fastapi import FastAPI, HTTPException, Path, Query
from pydantic import BaseModel

from api.recommendation_service import RecommendationService


# --------------------------------------------------------------------- #
# Load models ONCE at import time (i.e. once per process, at startup).
# If loading fails, the app still starts so /health can report the problem,
# but every other endpoint returns 503 instead of crashing.
# --------------------------------------------------------------------- #
try:
    recommendation_service = RecommendationService()
    SERVICE_READY = True
    SERVICE_ERROR = None
except Exception as exc:  # noqa: BLE001 - we want to surface ANY startup failure via /health
    recommendation_service = None
    SERVICE_READY = False
    SERVICE_ERROR = str(exc)


app = FastAPI(
    title="Hybrid E-Commerce Recommendation API",
    description=(
        "Serves content-based, collaborative, and hybrid recommendations from "
        "pre-trained artifacts. No training happens in this service."
    ),
    version="1.0.0",
)


# --------------------------------------------------------------------- #
# Section 7: Pydantic schemas — these also drive automatic request validation
# --------------------------------------------------------------------- #
class HealthResponse(BaseModel):
    status: str


class RecommendationItem(BaseModel):
    article_id: str
    product_name: str
    category: str
    score: Optional[float] = None


class RecommendationResponse(BaseModel):
    user_id: str
    is_new_user: bool
    recommendations: List[RecommendationItem]


class SimilarItem(BaseModel):
    article_id: str
    product_name: str
    similarity_score: float
    category: str


class SimilarResponse(BaseModel):
    article_id: str
    similar_products: List[SimilarItem]


def _ensure_service_ready():
    """Section 6: missing-artifact handling — surfaced as 503, not a crash."""
    if not SERVICE_READY:
        raise HTTPException(
            status_code=503,
            detail=f"Recommendation service unavailable — artifacts failed to load: {SERVICE_ERROR}",
        )


# --------------------------------------------------------------------- #
# Section 3: health endpoint
# --------------------------------------------------------------------- #
@app.get("/health", response_model=HealthResponse)
def health():
    """Lightweight liveness check — does not touch the ML artifacts."""
    return HealthResponse(status="healthy" if SERVICE_READY else "unhealthy")


# --------------------------------------------------------------------- #
# Section 4: personalized recommendations
# --------------------------------------------------------------------- #
@app.get("/recommend/{user_id}", response_model=RecommendationResponse)
def recommend(
    user_id: str = Path(
        ..., min_length=1, description="Customer ID (raw string, not the internal matrix index)"
    ),
    top_k: int = Query(10, ge=1, le=50, description="Number of recommendations to return (1-50)"),
):
    _ensure_service_ready()

    if not user_id.strip():
        raise HTTPException(status_code=400, detail="user_id must not be blank.")

    recs, is_new_user = recommendation_service.get_recommendations(user_id, top_k=top_k)

    if not recs:
        # Extremely rare (e.g. catalog metadata missing for every candidate) but still
        # a real failure mode worth a clear error rather than an empty 200.
        raise HTTPException(
            status_code=404,
            detail=f"No recommendations could be generated for user_id='{user_id}'.",
        )

    return RecommendationResponse(user_id=user_id, is_new_user=is_new_user, recommendations=recs)


# --------------------------------------------------------------------- #
# Section 5: content-based "similar products"
# --------------------------------------------------------------------- #
@app.get("/similar/{article_id}", response_model=SimilarResponse)
def similar(
    article_id: str = Path(..., min_length=1, description="Article ID from the product catalog"),
    top_k: int = Query(10, ge=1, le=50, description="Number of similar products to return (1-50)"),
):
    _ensure_service_ready()

    # Catalog article_ids are numeric (H&M convention) but always arrive as a string
    # from the URL path - normalize before the lookup, and reject non-numeric input.
    try:
        normalized_id = int(article_id)
    except ValueError:
        raise HTTPException(
            status_code=400, detail=f"article_id must be numeric, got '{article_id}'."
        )

    if not recommendation_service.is_known_article(normalized_id):
        raise HTTPException(
            status_code=404, detail=f"article_id {normalized_id} not found in catalog."
        )

    similar_products = recommendation_service.get_similar_products(normalized_id, top_k=top_k)
    return SimilarResponse(article_id=str(normalized_id), similar_products=similar_products)
