"""
app.py

Streamlit frontend for the Hybrid E-Commerce Recommendation System.

Responsibilities:
- Render an e-commerce style UI (home page, personalized recommendations,
  similar products).
- Call the already-running FastAPI backend (Notebook 08) over HTTP for every
  recommendation — no model is loaded, trained, or touched in this file.
- Handle API errors (unavailable, timeout, invalid input, empty results)
  gracefully, without crashing the UI.

Run standalone with:
    streamlit run app/app.py

Requires the FastAPI backend to already be running (see Notebook 08):
    uvicorn api.main:app --reload
"""

import requests
import streamlit as st

# --------------------------------------------------------------------- #
# Section 8: Configuration — the ONLY place the API base URL is defined.
# Every API call in this file goes through the functions below, which all
# read API_URL from here. To point the app at a deployed backend later
# (Render/AWS/etc.), change this one line — nothing else in the file needs
# to change.
# --------------------------------------------------------------------- #
import os

API_URL = os.getenv(
    "API_URL",
    "http://127.0.0.1:8000"
)
REQUEST_TIMEOUT = 8  # seconds


# --------------------------------------------------------------------- #
# Section 7: API communication layer
#
# These functions are plain Python (no Streamlit calls inside them) so they
# can be imported and tested independently of the Streamlit runtime — see
# Notebook 09, Section 10 ("Final Testing").
#
# Every function returns a tuple: (data, error_message).
# - On success: (parsed_json, None)
# - On failure: (None, "human readable error message")
# The UI layer below only ever has to check "if error: show it".
# --------------------------------------------------------------------- #
def check_api_health():
    """GET /health — used to show a live backend status indicator."""
    try:
        resp = requests.get(f"{API_URL}/health", timeout=REQUEST_TIMEOUT)
        if resp.status_code == 200:
            return resp.json(), None
        return None, f"API returned status {resp.status_code} on /health."
    except requests.exceptions.ConnectionError:
        return None, "Cannot reach the API. Is FastAPI running (uvicorn api.main:app --reload)?"
    except requests.exceptions.Timeout:
        return None, "API health check timed out."
    except requests.exceptions.RequestException as exc:
        return None, f"Unexpected error contacting API: {exc}"


def get_recommendations(user_id: str, top_k: int = 10):
    """
    Calls GET /recommend/{user_id}.

    The backend never errors on an unknown user_id — it automatically falls
    back to popularity-based recommendations and sets is_new_user=True. So
    from this app's point of view, "invalid user" is not a distinct failure
    mode; it's a normal, successful response we display differently.
    """
    user_id = (user_id or "").strip()
    if not user_id:
        return None, "Please enter a user ID."

    try:
        resp = requests.get(
            f"{API_URL}/recommend/{user_id}",
            params={"top_k": top_k},
            timeout=REQUEST_TIMEOUT,
        )
    except requests.exceptions.ConnectionError:
        return None, "Cannot reach the API. Is FastAPI running (uvicorn api.main:app --reload)?"
    except requests.exceptions.Timeout:
        return None, "The API took too long to respond. Please try again."
    except requests.exceptions.RequestException as exc:
        return None, f"Unexpected error contacting API: {exc}"

    if resp.status_code == 200:
        data = resp.json()
        if not data.get("recommendations"):
            return data, "The API returned no recommendations for this user."
        return data, None

    if resp.status_code == 404:
        return None, resp.json().get("detail", "No recommendations could be generated.")
    if resp.status_code == 422:
        return None, "Invalid request (top_k must be between 1 and 50)."
    if resp.status_code == 503:
        return None, "The recommendation service is temporarily unavailable on the backend."
    return None, f"API returned an unexpected status ({resp.status_code})."


def get_similar_products(article_id: str, top_k: int = 10):
    """Calls GET /similar/{article_id}. Handles unknown/malformed article IDs."""
    article_id = (article_id or "").strip()
    if not article_id:
        return None, "Please enter an article ID."

    try:
        resp = requests.get(
            f"{API_URL}/similar/{article_id}",
            params={"top_k": top_k},
            timeout=REQUEST_TIMEOUT,
        )
    except requests.exceptions.ConnectionError:
        return None, "Cannot reach the API. Is FastAPI running (uvicorn api.main:app --reload)?"
    except requests.exceptions.Timeout:
        return None, "The API took too long to respond. Please try again."
    except requests.exceptions.RequestException as exc:
        return None, f"Unexpected error contacting API: {exc}"

    if resp.status_code == 200:
        data = resp.json()
        if not data.get("similar_products"):
            return data, "The API returned no similar products for this article."
        return data, None

    if resp.status_code == 400:
        return None, resp.json().get("detail", "article_id must be numeric.")
    if resp.status_code == 404:
        return None, resp.json().get("detail", f"article_id '{article_id}' was not found in the catalog.")
    if resp.status_code == 422:
        return None, "Invalid request (top_k must be between 1 and 50)."
    if resp.status_code == 503:
        return None, "The recommendation service is temporarily unavailable on the backend."
    return None, f"API returned an unexpected status ({resp.status_code})."


# --------------------------------------------------------------------- #
# Section 6: Explainability helper
#
# Only states what the model/API actually tells us. No per-item score
# breakdown (content vs. collaborative) is invented, because /recommend
# only returns a single combined hybrid score - not a breakdown.
# --------------------------------------------------------------------- #
def explanation_for(is_new_user: bool, score):
    if is_new_user:
        return "Popular right now \u2014 shown because we don't have purchase history for this user yet."
    if score is not None:
        return "Personalized pick from the hybrid model, based on this user's purchase history and similar products."
    return "Trending pick \u2014 shown as a fallback because a personalized score wasn't available for this item."


# --------------------------------------------------------------------- #
# UI: product card rendering
# --------------------------------------------------------------------- #
def render_recommendation_card(item: dict, is_new_user: bool):
    with st.container(border=True):
        st.markdown(f"**{item.get('product_name') or 'Unnamed product'}**")
        st.caption(f"Article ID: {item.get('article_id')}")
        st.write(f"Category: {item.get('category') or 'N/A'}")
        score = item.get("score")
        st.write(f"Score: {score:.4f}" if score is not None else "Score: N/A (popularity-based)")
        st.info(explanation_for(is_new_user, score), icon="\u2139\ufe0f")


def render_similar_card(item: dict):
    with st.container(border=True):
        st.markdown(f"**{item.get('product_name') or 'Unnamed product'}**")
        st.caption(f"Article ID: {item.get('article_id')}")
        st.write(f"Category: {item.get('category') or 'N/A'}")
        st.write(f"Similarity: {item.get('similarity_score'):.4f}")
        st.info(
            f"Similar to article {item.get('article_id')} based on shared product "
            "attributes (content-based similarity).",
            icon="\u2139\ufe0f",
        )


def render_card_grid(items, is_new_user=None, card_kind="recommendation"):
    cols_per_row = 2
    for row_start in range(0, len(items), cols_per_row):
        row_items = items[row_start: row_start + cols_per_row]
        cols = st.columns(cols_per_row)
        for col, item in zip(cols, row_items):
            with col:
                if card_kind == "recommendation":
                    render_recommendation_card(item, is_new_user)
                else:
                    render_similar_card(item)


# --------------------------------------------------------------------- #
# UI: page sections
# --------------------------------------------------------------------- #
def render_header():
    st.set_page_config(
        page_title="Hybrid E-Commerce Recommendations",
        page_icon="\U0001F6CD\ufe0f",
        layout="wide",
    )
    st.title("\U0001F6CD\ufe0f Hybrid E-Commerce Recommendation System")
    st.write(
        "A portfolio project demonstrating an end-to-end recommendation pipeline: "
        "content-based filtering, collaborative filtering (ALS), and a hybrid model "
        "that blends both \u2014 served through a FastAPI backend and this Streamlit "
        "frontend. Fashion product catalog courtesy of the H&M Personalized Fashion "
        "Recommendations dataset."
    )

    health, health_error = check_api_health()
    if health_error:
        st.error(f"Backend status: unreachable \u2014 {health_error}")
    elif health.get("status") == "healthy":
        st.success("Backend status: connected \u2192 " + API_URL)
    else:
        st.warning("Backend status: reachable, but reporting itself as unhealthy.")

    st.divider()


def render_recommendations_section():
    st.header("Personalized Recommendations")
    st.write(
        "Enter a customer ID to get personalized picks. Unknown IDs are treated as "
        "new users automatically \u2014 no error, just a popularity-based fallback."
    )

    col1, col2 = st.columns([3, 1])
    with col1:
        user_id = st.text_input(
            "Customer ID",
            key="user_id_input",
            placeholder="e.g. 00000dbacae5abe5e23885899a1fa44253a17956c6d1c3d25f88aa139fdfc657",
        )
    with col2:
        top_k = st.number_input("How many?", min_value=1, max_value=50, value=10, key="rec_top_k")

    if st.button("Get Recommendations", type="primary"):
        with st.spinner("Fetching recommendations..."):
            data, error = get_recommendations(user_id, top_k=top_k)
        st.session_state["rec_result"] = data
        st.session_state["rec_error"] = error

    data = st.session_state.get("rec_result")
    error = st.session_state.get("rec_error")

    if error and not (data and data.get("recommendations")):
        st.error(error)
    elif data:
        if data.get("is_new_user"):
            st.warning("New user detected. Showing popular products.")
        else:
            st.success(f"Showing personalized recommendations for user: {data.get('user_id')}")
        render_card_grid(data["recommendations"], is_new_user=data.get("is_new_user"), card_kind="recommendation")

    st.divider()


def render_similar_products_section():
    st.header("Find Similar Products")
    st.write("Enter an article ID from the catalog to find visually and descriptively similar products.")

    col1, col2 = st.columns([3, 1])
    with col1:
        article_id = st.text_input("Article ID", key="article_id_input", placeholder="e.g. 108775015")
    with col2:
        top_k = st.number_input("How many?", min_value=1, max_value=50, value=10, key="sim_top_k")

    if st.button("Find Similar Products"):
        with st.spinner("Searching for similar products..."):
            data, error = get_similar_products(article_id, top_k=top_k)
        st.session_state["sim_result"] = data
        st.session_state["sim_error"] = error

    data = st.session_state.get("sim_result")
    error = st.session_state.get("sim_error")

    if error and not (data and data.get("similar_products")):
        st.error(error)
    elif data:
        st.success(f"Products similar to article {data.get('article_id')}:")
        render_card_grid(data["similar_products"], card_kind="similar")


# --------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------- #
def main():
    render_header()
    render_recommendations_section()
    render_similar_products_section()


if __name__ == "__main__":
    main()
