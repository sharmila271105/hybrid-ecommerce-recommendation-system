"""
main.py

FastAPI application entrypoint.

Responsibilities:
- Create the FastAPI app and its routes.
- Instantiate RecommendationService once at process startup.
- Validate input through FastAPI/Pydantic.
- Translate service errors into HTTP status codes.

No ML logic lives here.
"""

from typing import List, Optional

from fastapi import FastAPI, HTTPException, Path, Query
from pydantic import BaseModel

from api.recommendation_service import RecommendationService


# =========================================================
# SERVICE INITIALIZATION
# =========================================================

try:
    recommendation_service = RecommendationService()
    SERVICE_READY = True
    SERVICE_ERROR = None

except Exception as exc:
    recommendation_service = None
    SERVICE_READY = False
    SERVICE_ERROR = str(exc)


# =========================================================
# FASTAPI APPLICATION
# =========================================================

app = FastAPI(
    title="Hybrid E-Commerce Recommendation API",
    description=(
        "Serves content-based, collaborative, and hybrid "
        "recommendations from pre-trained artifacts. "
        "No training happens in this service."
    ),
    version="1.0.0",
)


# =========================================================
# PYDANTIC SCHEMAS
# =========================================================

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


# =========================================================
# SERVICE CHECK
# =========================================================

def _ensure_service_ready():
    if not SERVICE_READY:
        raise HTTPException(
            status_code=503,
            detail=(
                "Recommendation service unavailable — "
                f"artifacts failed to load: {SERVICE_ERROR}"
            ),
        )


# =========================================================
# HEALTH
# =========================================================

@app.get(
    "/health",
    response_model=HealthResponse,
)
def health():

    return HealthResponse(
        status=(
            "healthy"
            if SERVICE_READY
            else "unhealthy"
        )
    )


# =========================================================
# RECOMMENDATIONS
# =========================================================

@app.get(
    "/recommend/{user_id}",
    response_model=RecommendationResponse,
)
def recommend(
    user_id: str = Path(
        ...,
        min_length=1,
        description=(
            "Customer ID "
            "(raw string, not internal matrix index)"
        ),
    ),
    top_k: int = Query(
        10,
        ge=1,
        le=50,
        description=(
            "Number of recommendations "
            "to return (1-50)"
        ),
    ),
):

    _ensure_service_ready()

    if not user_id.strip():
        raise HTTPException(
            status_code=400,
            detail="user_id must not be blank.",
        )

    recs, is_new_user = (
        recommendation_service.get_recommendations(
            user_id,
            top_k=top_k,
        )
    )

    if not recs:
        raise HTTPException(
            status_code=404,
            detail=(
                "No recommendations could be "
                f"generated for user_id='{user_id}'."
            ),
        )

    return RecommendationResponse(
        user_id=user_id,
        is_new_user=is_new_user,
        recommendations=recs,
    )


# =========================================================
# SIMILAR PRODUCTS
# =========================================================

@app.get(
    "/similar/{article_id}",
    response_model=SimilarResponse,
)
def similar(
    article_id: str = Path(
        ...,
        min_length=1,
        description=(
            "Article ID from the product catalog"
        ),
    ),
    top_k: int = Query(
        10,
        ge=1,
        le=50,
        description=(
            "Number of similar products "
            "to return (1-50)"
        ),
    ),
):

    _ensure_service_ready()

    # H&M article IDs are numeric
    try:
        normalized_id = int(article_id)

    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=(
                f"article_id must be numeric, "
                f"got '{article_id}'."
            ),
        )

    if not recommendation_service.is_known_article(
        normalized_id
    ):
        raise HTTPException(
            status_code=404,
            detail=(
                f"article_id {normalized_id} "
                "not found in catalog."
            ),
        )

    similar_products = (
        recommendation_service.get_similar_products(
            normalized_id,
            top_k=top_k,
        )
    )

    return SimilarResponse(
        article_id=str(normalized_id),
        similar_products=similar_products,
    )
