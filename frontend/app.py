import os
import requests
import streamlit as st


# =========================================================
# CONFIG
# =========================================================

API_URL = os.getenv(
    "API_URL",
    "https://hybrid-ecommerce-recommendation-system.onrender.com",
)

HM_RED = "#E50010"


# =========================================================
# PAGE
# =========================================================

st.set_page_config(
    page_title="H&M — Recommendation",
    page_icon="H&M",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# =========================================================
# CSS
# =========================================================

st.markdown(
    """
    <style>

    /* ================================================== */
    /* GLOBAL */
    /* ================================================== */

    .stApp {
        background: #ffffff;
        color: #111111;
    }

    .block-container {
        max-width: 1500px;
        padding: 0 42px 60px 42px;
    }

    #MainMenu {
        visibility: hidden;
    }

    footer {
        visibility: hidden;
    }

    header {
        background: #ffffff !important;
    }

    /* Remove default Streamlit top spacing */
    [data-testid="stHeader"] {
        background: transparent;
    }


    /* ================================================== */
    /* HEADER */
    /* ================================================== */

    .hm-header {
        width: 100%;
        padding: 28px 0 18px 0;
        border-bottom: 1px solid #dedede;
        margin-bottom: 0;
    }

    .hm-logo {
        color: #E50010;
        font-family: Arial, Helvetica, sans-serif;
        font-size: 48px;
        font-weight: 900;
        letter-spacing: -5px;
        line-height: 1;
        display: inline-block;
    }

    .hm-navigation {
        display: flex;
        gap: 30px;
        margin-top: 23px;
        font-family: Arial, Helvetica, sans-serif;
        font-size: 13px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .hm-navigation span {
        color: #111111;
    }

    .hm-navigation .sale {
        color: #E50010;
    }


    /* ================================================== */
    /* HERO */
    /* ================================================== */

    .hero {
        padding: 65px 0 55px 0;
        text-align: center;
    }

    .hero-kicker {
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 1.8px;
        text-transform: uppercase;
        color: #666666;
        margin-bottom: 15px;
    }

    .hero-title {
        font-family: Georgia, "Times New Roman", serif;
        font-size: 46px;
        font-weight: 400;
        letter-spacing: -1px;
        color: #111111;
        margin-bottom: 12px;
    }

    .hero-description {
        max-width: 620px;
        margin: auto;
        color: #666666;
        font-size: 15px;
        line-height: 1.7;
    }


    /* ================================================== */
    /* SEARCH AREA */
    /* ================================================== */

    .search-heading {
        font-family: Georgia, "Times New Roman", serif;
        font-size: 28px;
        font-weight: 400;
        color: #111111;
        margin-bottom: 8px;
    }

    .search-description {
        color: #666666;
        font-size: 14px;
        margin-bottom: 18px;
    }


    /* ================================================== */
    /* STREAMLIT INPUTS */
    /* ================================================== */

    label {
        color: #222222 !important;
        font-size: 12px !important;
        font-weight: 600 !important;
    }

    div[data-baseweb="input"] {
        border-radius: 0 !important;
        border: 1px solid #999999 !important;
        background: #ffffff !important;
    }

    div[data-baseweb="input"]:focus-within {
        border-color: #111111 !important;
        box-shadow: none !important;
    }

    div[data-baseweb="input"] input {
        color: #111111 !important;
        background: #ffffff !important;
    }

    /* ================================================== */
    /* BUTTONS */
    /* ================================================== */

    .stButton > button {
        border-radius: 0 !important;
        background: #E50010 !important;
        color: #ffffff !important;
        border: 1px solid #E50010 !important;
        font-size: 12px !important;
        font-weight: 600 !important;
        letter-spacing: 0.4px !important;
        min-height: 42px !important;
    }

    .stButton > button:hover {
        background: #b9000c !important;
        border-color: #b9000c !important;
    }


    /* ================================================== */
    /* PRODUCT SECTION */
    /* ================================================== */

    .section-rule {
        border-top: 1px solid #111111;
        margin: 60px 0 25px 0;
    }

    .section-header {
        display: flex;
        justify-content: space-between;
        align-items: baseline;
        margin-bottom: 22px;
    }

    .section-title {
        font-family: Georgia, "Times New Roman", serif;
        font-size: 29px;
        font-weight: 400;
        color: #111111;
    }

    .section-note {
        color: #777777;
        font-size: 12px;
    }


    /* ================================================== */
    /* PRODUCT CARDS */
    /* ================================================== */

    .product-card {
        background: #ffffff;
        margin-bottom: 28px;
    }

    .product-image {
        height: 310px;
        background: #f3f3f1;
        display: flex;
        justify-content: center;
        align-items: center;
        position: relative;
        overflow: hidden;
    }

    .product-placeholder {
        color: #b2b2b2;
        font-family: Georgia, "Times New Roman", serif;
        font-size: 42px;
        font-weight: 400;
    }

    .product-details {
        padding-top: 13px;
    }

    .product-name {
        color: #111111;
        font-size: 14px;
        font-weight: 500;
        line-height: 1.4;
        margin-bottom: 4px;
    }

    .product-category {
        color: #777777;
        font-size: 12px;
        line-height: 1.4;
        margin-bottom: 7px;
    }

    .product-price {
        color: #111111;
        font-size: 13px;
        margin-bottom: 7px;
    }

    .product-id {
        color: #999999;
        font-size: 10px;
        letter-spacing: 0.2px;
    }

    .recommendation-score {
        color: #555555;
        font-size: 10px;
        margin-top: 8px;
    }

    .popular-label {
        color: #E50010;
        font-size: 10px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        margin-top: 8px;
    }


    /* ================================================== */
    /* USER MESSAGE */
    /* ================================================== */

    .personalized-message {
        background: #f7f7f5;
        border-left: 3px solid #E50010;
        padding: 16px 18px;
        margin: 18px 0 28px 0;
        color: #333333;
        font-size: 13px;
        line-height: 1.6;
    }

    .new-user-message {
        background: #f7f7f5;
        border-left: 3px solid #E50010;
        padding: 16px 18px;
        margin: 18px 0 28px 0;
        color: #333333;
        font-size: 13px;
        line-height: 1.6;
    }


    /* ================================================== */
    /* TABS */
    /* ================================================== */

    button[data-baseweb="tab"] {
        color: #555555 !important;
        font-size: 13px !important;
        font-weight: 500 !important;
    }

    button[data-baseweb="tab"][aria-selected="true"] {
        color: #111111 !important;
    }

    div[data-baseweb="tab-highlight"] {
        background: #E50010 !important;
    }


    /* ================================================== */
    /* SLIDER */
    /* ================================================== */

    div[data-baseweb="slider"] {
        margin-top: 5px;
    }


    /* ================================================== */
    /* API STATUS */
    /* ================================================== */

    .api-status {
        text-align: right;
        color: #777777;
        font-size: 10px;
        letter-spacing: 0.5px;
        text-transform: uppercase;
        margin-top: 12px;
    }

    .api-status span {
        color: #E50010;
        font-weight: 700;
    }


    /* ================================================== */
    /* FOOTER */
    /* ================================================== */

    .footer {
        border-top: 1px solid #dedede;
        margin-top: 70px;
        padding: 25px 0;
        text-align: center;
        color: #777777;
        font-size: 11px;
        line-height: 1.8;
    }

    .footer-brand {
        color: #E50010;
        font-weight: 800;
        font-size: 16px;
        letter-spacing: -1px;
        margin-bottom: 5px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# HEADER
# =========================================================

st.markdown(
    """
    <div class="hm-header">

        <div class="hm-logo">
            H&M
        </div>

        <div class="hm-navigation">
            <span>Ladies</span>
            <span>Men</span>
            <span>Kids</span>
            <span>Home</span>
            <span class="sale">Sale</span>
        </div>

    </div>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# API STATUS
# =========================================================

try:

    health = requests.get(
        f"{API_URL}/health",
        timeout=15,
    )

    if (
        health.status_code == 200
        and health.json().get("status") == "healthy"
    ):

        st.markdown(
            """
            <div class="api-status">
                <span>●</span> online
            </div>
            """,
            unsafe_allow_html=True,
        )

    else:

        st.markdown(
            """
            <div class="api-status">
                API unavailable
            </div>
            """,
            unsafe_allow_html=True,
        )

except requests.RequestException:

    st.markdown(
        """
        <div class="api-status">
            API unavailable
        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# HERO
# =========================================================

st.markdown(
    """
    <div class="hero">

        <div class="hero-kicker">
            Your selection
        </div>

        <div class="hero-title">
            Discover your next favourite
        </div>

        <div class="hero-description">
            A personalised selection of styles based on
            shopping behaviour and product similarity.
        </div>

    </div>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# TABS
# =========================================================

tab_for_you, tab_similar = st.tabs(
    [
        "For you",
        "Similar products",
    ]
)


# =========================================================
# FOR YOU
# =========================================================

with tab_for_you:

    st.markdown(
        """
        <div class="search-heading">
            Your recommendations
        </div>

        <div class="search-description">
            Enter a customer ID to view a personalised selection.
        </div>
        """,
        unsafe_allow_html=True,
    )

    user_id = st.text_input(
        "Customer ID",
        placeholder="Enter customer ID",
        label_visibility="visible",
        key="user_id",
    )

    col_input, col_button = st.columns(
        [4, 1]
    )

    with col_button:

        st.write("")

        recommend_clicked = st.button(
            "VIEW SELECTION",
            use_container_width=True,
            type="primary",
        )

    top_k = st.slider(
        "Products",
        min_value=5,
        max_value=10,
        value=10,
        key="top_k",
    )

    if recommend_clicked:

        if not user_id.strip():

            st.warning(
                "Please enter a customer ID."
            )

        else:

            with st.spinner(
                "Loading selection..."
            ):

                try:

                    response = requests.get(
                        f"{API_URL}/recommend/"
                        f"{user_id.strip()}",
                        params={
                            "top_k": top_k
                        },
                        timeout=60,
                    )

                    if response.status_code == 200:

                        data = response.json()

                        recommendations = data.get(
                            "recommendations",
                            [],
                        )

                        is_new_user = data.get(
                            "is_new_user",
                            False,
                        )

                        if is_new_user:

                            st.markdown(
                                """
                                <div class="new-user-message">
                                    <b>Welcome.</b>
                                    <br>
                                    We don't have enough shopping
                                    history for this customer yet.
                                    This selection is based on
                                    popular styles.
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )

                        else:

                            st.markdown(
                                """
                                <div class="personalized-message">
                                    <b>Selected for you.</b>
                                    <br>
                                    Recommendations are based on
                                    your previous shopping behaviour
                                    and product characteristics.
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )

                        st.markdown(
                            """
                            <div class="section-rule"></div>

                            <div class="section-header">

                                <div class="section-title">
                                    Recommended for you
                                </div>

                                <div class="section-note">
                                    Curated selection
                                </div>

                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                        if recommendations:

                            columns = st.columns(5)

                            for i, product in enumerate(
                                recommendations
                            ):

                                with columns[
                                    i % 5
                                ]:

                                    name = str(
                                        product.get(
                                            "product_name",
                                            "Product",
                                        )
                                    )

                                    category = str(
                                        product.get(
                                            "category",
                                            "",
                                        )
                                    )

                                    article_id = str(
                                        product.get(
                                            "article_id",
                                            "",
                                        )
                                    )

                                    score = product.get(
                                        "score"
                                    )

                                    if score is None:

                                        score_html = (
                                            '<div class="popular-label">'
                                            'Popular selection'
                                            '</div>'
                                        )

                                    else:

                                        score_html = (
                                            '<div class='
                                            '"recommendation-score">'
                                            f'Ranking score '
                                            f'{float(score):.4f}'
                                            '</div>'
                                        )

                                    st.markdown(
                                        f"""
                                        <div class="product-card">

                                            <div class="
                                            product-image">

                                                <div class="
                                                product-placeholder">
                                                    H&M
                                                </div>

                                            </div>

                                            <div class="
                                            product-details">

                                                <div class="
                                                product-name">
                                                    {name}
                                                </div>

                                                <div class="
                                                product-category">
                                                    {category}
                                                </div>

                                                <div class="
                                                product-id">
                                                    {article_id}
                                                </div>

                                                {score_html}

                                            </div>

                                        </div>
                                        """,
                                        unsafe_allow_html=True,
                                    )

                        else:

                            st.info(
                                "No products were returned."
                            )

                    elif response.status_code == 503:

                        st.error(
                            "The recommendation service "
                            "is temporarily unavailable."
                        )

                    else:

                        st.error(
                            f"Request failed "
                            f"({response.status_code})."
                        )

                except requests.RequestException:

                    st.error(
                        "Unable to connect to the "
                        "recommendation service."
                    )


# =========================================================
# SIMILAR PRODUCTS
# =========================================================

with tab_similar:

    st.markdown(
        """
        <div class="search-heading">
            Find similar products
        </div>

        <div class="search-description">
            Enter an article number to explore styles
            with similar product characteristics.
        </div>
        """,
        unsafe_allow_html=True,
    )

    article_id = st.text_input(
        "Article number",
        placeholder="Example: 108775015",
        key="article_id",
    )

    similar_k = st.slider(
        "Products",
        min_value=5,
        max_value=10,
        value=10,
        key="similar_k",
    )

    col_empty, col_button = st.columns(
        [4, 1]
    )

    with col_button:

        find_clicked = st.button(
            "FIND SIMILAR",
            use_container_width=True,
            type="primary",
        )

    if find_clicked:

        if not article_id.strip():

            st.warning(
                "Please enter an article number."
            )

        else:

            with st.spinner(
                "Finding similar styles..."
            ):

                try:

                    response = requests.get(
                        f"{API_URL}/similar/"
                        f"{article_id.strip()}",
                        params={
                            "top_k": similar_k
                        },
                        timeout=60,
                    )

                    if response.status_code == 200:

                        data = response.json()

                        products = data.get(
                            "similar_products",
                            [],
                        )

                        st.markdown(
                            """
                            <div class="personalized-message">
                                <b>Similar styles.</b>
                                <br>
                                Products are ranked by
                                similarity between their
                                product descriptions.
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                        st.markdown(
                            """
                            <div class="section-rule"></div>

                            <div class="section-header">

                                <div class="section-title">
                                    You may also like
                                </div>

                                <div class="section-note">
                                    Similar styles
                                </div>

                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                        if products:

                            columns = st.columns(5)

                            for i, product in enumerate(
                                products
                            ):

                                with columns[
                                    i % 5
                                ]:

                                    name = str(
                                        product.get(
                                            "product_name",
                                            "Product",
                                        )
                                    )

                                    category = str(
                                        product.get(
                                            "category",
                                            "",
                                        )
                                    )

                                    candidate_id = str(
                                        product.get(
                                            "article_id",
                                            "",
                                        )
                                    )

                                    similarity = float(
                                        product.get(
                                            "similarity_score",
                                            0,
                                        )
                                    )

                                    st.markdown(
                                        f"""
                                        <div class="product-card">

                                            <div class="
                                            product-image">

                                                <div class="
                                                product-placeholder">
                                                    H&M
                                                </div>

                                            </div>

                                            <div class="
                                            product-details">

                                                <div class="
                                                product-name">
                                                    {name}
                                                </div>

                                                <div class="
                                                product-category">
                                                    {category}
                                                </div>

                                                <div class="
                                                product-id">
                                                    {candidate_id}
                                                </div>

                                                <div class="
                                                recommendation-score">
                                                    Similarity
                                                    {similarity:.4f}
                                                </div>

                                            </div>

                                        </div>
                                        """,
                                        unsafe_allow_html=True,
                                    )

                        else:

                            st.info(
                                "No similar products found."
                            )

                    elif response.status_code == 400:

                        st.error(
                            "Article number must be numeric."
                        )

                    elif response.status_code == 404:

                        st.error(
                            "This article number was not "
                            "found in the catalogue."
                        )

                    else:

                        st.error(
                            f"Request failed "
                            f"({response.status_code})."
                        )

                except requests.RequestException:

                    st.error(
                        "Unable to connect to the "
                        "recommendation service."
                    )


# =========================================================
# FOOTER
# =========================================================

st.markdown(
    """
    <div class="footer">

        <div class="footer-brand">
            H&M
        </div>

        Recommendation experience powered by
        collaborative filtering and content-based similarity.

        <br>

        For demonstration purposes.

    </div>
    """,
    unsafe_allow_html=True,
)
