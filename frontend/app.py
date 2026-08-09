import os
import requests
import streamlit as st


# =========================================================
# CONFIG
# =========================================================

API_URL = os.getenv(
    "API_URL",
    "https://hybrid-ecommerce-recommendation-system.onrender.com"
)


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="H&M Recommendation Engine",
    page_icon="🛍️",
    layout="wide",
)


# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown(
    """
    <style>

    .main-title {
        font-size: 42px;
        font-weight: 700;
        margin-bottom: 5px;
    }

    .subtitle {
        font-size: 18px;
        color: #666;
        margin-bottom: 30px;
    }

    .section-title {
        font-size: 28px;
        font-weight: 650;
        margin-top: 35px;
        margin-bottom: 15px;
    }

    .product-card {
        border: 1px solid #e5e5e5;
        border-radius: 12px;
        padding: 18px;
        height: 210px;
        background: white;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }

    .product-name {
        font-size: 17px;
        font-weight: 600;
        margin-bottom: 8px;
    }

    .product-category {
        font-size: 14px;
        color: #777;
        margin-bottom: 12px;
    }

    .score {
        font-size: 14px;
        font-weight: 600;
    }

    .info-box {
        padding: 15px;
        border-radius: 10px;
        background: #f7f7f7;
        margin-bottom: 20px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# HEADER
# =========================================================

st.markdown(
    '<div class="main-title">'
    'H&M Recommendation Engine'
    '</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="subtitle">'
    'Hybrid Collaborative + Content-Based Recommendation System'
    '</div>',
    unsafe_allow_html=True,
)


# =========================================================
# API HEALTH
# =========================================================

try:

    health_response = requests.get(
        f"{API_URL}/health",
        timeout=15,
    )

    if health_response.status_code == 200:

        health_data = (
            health_response.json()
        )

        if health_data.get("status") == "healthy":

            st.success(
                "🟢 Recommendation API is online"
            )

        else:

            st.warning(
                "🟡 Recommendation API is unhealthy"
            )

    else:

        st.warning(
            "🟡 API returned an unexpected response"
        )

except requests.RequestException:

    st.error(
        "🔴 Could not connect to recommendation API"
    )


# =========================================================
# PERSONALIZED RECOMMENDATIONS
# =========================================================

st.markdown(
    '<div class="section-title">'
    '👤 Personalized Recommendations'
    '</div>',
    unsafe_allow_html=True,
)

st.write(
    "Enter a customer ID to receive personalized recommendations."
)

user_id = st.text_input(
    "Customer ID",
    placeholder="Enter customer ID...",
)

top_k = st.slider(
    "Number of recommendations",
    min_value=4,
    max_value=10,
    value=10,
)


if st.button(
    "Get Recommendations",
    type="primary",
):

    if not user_id.strip():

        st.warning(
            "Please enter a customer ID."
        )

    else:

        with st.spinner(
            "Getting recommendations..."
        ):

            try:

                response = requests.get(
                    f"{API_URL}/recommend/{user_id.strip()}",
                    params={
                        "top_k": top_k
                    },
                    timeout=30,
                )

                if response.status_code == 200:

                    data = response.json()

                    recommendations = (
                        data.get(
                            "recommendations",
                            []
                        )
                    )

                    is_new_user = data.get(
                        "is_new_user",
                        False
                    )

                    # -------------------------------------
                    # NEW USER
                    # -------------------------------------

                    if is_new_user:

                        st.info(
                            "🆕 New user detected. "
                            "Showing popular products as a "
                            "cold-start recommendation."
                        )

                    else:

                        st.success(
                            "✨ Personalized recommendations "
                            "generated for this customer."
                        )

                    # -------------------------------------
                    # PRODUCTS
                    # -------------------------------------

                    if recommendations:

                        columns = st.columns(5)

                        for i, product in enumerate(
                            recommendations
                        ):

                            with columns[
                                i % 5
                            ]:

                                st.markdown(
                                    f"""
                                    <div class="product-card">

                                        <div class="product-name">
                                            {product["product_name"]}
                                        </div>

                                        <div class="product-category">
                                            {product["category"]}
                                        </div>

                                        <div>
                                            Article ID:
                                            {product["article_id"]}
                                        </div>

                                        <br>

                                        <div class="score">
                                            {
                                                "Popularity recommendation"
                                                if product["score"] is None
                                                else
                                                f"Score: {product['score']:.4f}"
                                            }
                                        </div>

                                    </div>
                                    """,
                                    unsafe_allow_html=True,
                                )

                    else:

                        st.warning(
                            "No recommendations found."
                        )

                elif response.status_code == 404:

                    st.warning(
                        "No recommendations were found "
                        "for this customer."
                    )

                elif response.status_code == 503:

                    st.error(
                        "Recommendation service is "
                        "currently unavailable."
                    )

                else:

                    st.error(
                        f"API error: "
                        f"{response.status_code}"
                    )

            except requests.RequestException as e:

                st.error(
                    f"Could not connect to API: {e}"
                )


# =========================================================
# SIMILAR PRODUCTS
# =========================================================

st.markdown(
    '<div class="section-title">'
    '🔍 Find Similar Products'
    '</div>',
    unsafe_allow_html=True,
)

st.write(
    "Enter an article ID to find visually/content-wise "
    "similar products based on product descriptions."
)

article_id = st.text_input(
    "Article ID",
    placeholder="Example: 108775015",
)

similar_k = st.slider(
    "Number of similar products",
    min_value=4,
    max_value=10,
    value=10,
    key="similar_k",
)


if st.button(
    "Find Similar Products",
):

    if not article_id.strip():

        st.warning(
            "Please enter an article ID."
        )

    else:

        with st.spinner(
            "Finding similar products..."
        ):

            try:

                response = requests.get(
                    f"{API_URL}/similar/{article_id.strip()}",
                    params={
                        "top_k": similar_k
                    },
                    timeout=30,
                )

                if response.status_code == 200:

                    data = response.json()

                    products = (
                        data.get(
                            "similar_products",
                            []
                        )
                    )

                    if products:

                        st.success(
                            f"Found {len(products)} similar products."
                        )

                        columns = st.columns(5)

                        for i, product in enumerate(
                            products
                        ):

                            with columns[
                                i % 5
                            ]:

                                st.markdown(
                                    f"""
                                    <div class="product-card">

                                        <div class="product-name">
                                            {product["product_name"]}
                                        </div>

                                        <div class="product-category">
                                            {product["category"]}
                                        </div>

                                        <div>
                                            Article ID:
                                            {product["article_id"]}
                                        </div>

                                        <br>

                                        <div class="score">
                                            Similarity:
                                            {product["similarity_score"]:.4f}
                                        </div>

                                    </div>
                                    """,
                                    unsafe_allow_html=True,
                                )

                    else:

                        st.warning(
                            "No similar products found."
                        )

                elif response.status_code == 400:

                    st.error(
                        "Article ID must be numeric."
                    )

                elif response.status_code == 404:

                    st.error(
                        "Article ID was not found "
                        "in the product catalog."
                    )

                else:

                    st.error(
                        f"API error: "
                        f"{response.status_code}"
                    )

            except requests.RequestException as e:

                st.error(
                    f"Could not connect to API: {e}"
                )


# =========================================================
# FOOTER
# =========================================================

st.markdown(
    """
    <br><br>
    <hr>

    <div style="text-align:center;color:#888;">
        Hybrid E-Commerce Recommendation System
        <br>
        Collaborative Filtering • Content-Based Filtering • Cold-Start Handling
    </div>
    """,
    unsafe_allow_html=True,
)
