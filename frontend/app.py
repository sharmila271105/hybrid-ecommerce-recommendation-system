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

RED = "#E50010"


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="H&M",
    page_icon="H&M",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# =========================================================
# CSS
# =========================================================

st.html(
    """
    <style>

    /* =====================================================
       GLOBAL
    ===================================================== */

    .stApp {
        background: #ffffff;
        color: #111111;
    }

    .block-container {
        max-width: 1440px;
        padding: 0 45px 60px 45px;
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


    /* =====================================================
       HEADER
    ===================================================== */

    .header {
        border-bottom: 1px solid #dddddd;
        padding: 25px 0 18px 0;
    }

    .logo {
        color: #E50010;
        font-family: Arial, Helvetica, sans-serif;
        font-size: 44px;
        font-weight: 900;
        letter-spacing: -4px;
        line-height: 1;
    }

    .nav {
        margin-top: 22px;
        display: flex;
        gap: 28px;
        font-family: Arial, Helvetica, sans-serif;
        font-size: 12px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: .5px;
    }

    .nav-item {
        color: #111111;
    }

    .nav-sale {
        color: #E50010;
    }


    /* =====================================================
       HERO
    ===================================================== */

    .hero {
        text-align: center;
        padding: 52px 0 42px 0;
    }

    .hero-small {
        color: #666666;
        font-size: 10px;
        font-weight: 600;
        letter-spacing: 2px;
        text-transform: uppercase;
        margin-bottom: 12px;
    }

    .hero-title {
        color: #111111;
        font-family: Georgia, "Times New Roman", serif;
        font-size: 42px;
        font-weight: 400;
        margin-bottom: 12px;
    }

    .hero-text {
        color: #666666;
        font-size: 14px;
        line-height: 1.7;
        max-width: 600px;
        margin: auto;
    }


    /* =====================================================
       NAVIGATION
    ===================================================== */

    .mode-title {
        color: #111111;
        font-family: Georgia, "Times New Roman", serif;
        font-size: 26px;
        margin-bottom: 7px;
    }

    .mode-description {
        color: #666666;
        font-size: 13px;
        margin-bottom: 20px;
    }


    /* =====================================================
       BUTTONS
    ===================================================== */

    .stButton > button {
        border-radius: 0 !important;
        min-height: 42px !important;
        background: #E50010 !important;
        color: white !important;
        border: 1px solid #E50010 !important;
        font-size: 11px !important;
        font-weight: 600 !important;
        letter-spacing: .6px !important;
    }

    .stButton > button:hover {
        background: #B8000C !important;
        border-color: #B8000C !important;
    }


    /* =====================================================
       INPUTS
    ===================================================== */

    label {
        color: #222222 !important;
        font-size: 11px !important;
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


    /* =====================================================
       MODE BAR
    ===================================================== */

    .mode-bar {
        border-top: 1px solid #111111;
        border-bottom: 1px solid #dddddd;
        padding: 0;
        margin-bottom: 35px;
    }


    /* =====================================================
       SECTION
    ===================================================== */

    .section {
        border-top: 1px solid #111111;
        margin-top: 50px;
        padding-top: 20px;
        margin-bottom: 22px;
    }

    .section-title {
        font-family: Georgia, "Times New Roman", serif;
        color: #111111;
        font-size: 27px;
    }

    .section-note {
        color: #777777;
        font-size: 11px;
        margin-top: 4px;
    }


    /* =====================================================
       MESSAGE
    ===================================================== */

    .message {
        background: #f7f7f5;
        border-left: 3px solid #E50010;
        padding: 15px 17px;
        margin-top: 20px;
        color: #333333;
        font-size: 12px;
        line-height: 1.6;
    }


    /* =====================================================
       PRODUCT CARD
    ===================================================== */

    .product-card {
        background: #ffffff;
        margin-bottom: 30px;
    }

    .product-image {
        width: 100%;
        height: 300px;
        background: #f2f2f0;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .product-placeholder {
        color: #b8b8b8;
        font-family: Georgia, "Times New Roman", serif;
        font-size: 34px;
    }

    .product-info {
        padding-top: 12px;
    }

    .product-name {
        color: #111111;
        font-size: 13px;
        line-height: 1.45;
        font-weight: 500;
    }

    .product-category {
        color: #777777;
        font-size: 11px;
        margin-top: 4px;
    }

    .product-id {
        color: #aaaaaa;
        font-size: 9px;
        margin-top: 6px;
    }

    .score {
        color: #555555;
        font-size: 9px;
        margin-top: 6px;
    }

    .popular {
        color: #E50010;
        font-size: 9px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: .7px;
        margin-top: 6px;
    }


    /* =====================================================
       FOOTER
    ===================================================== */

    .footer {
        border-top: 1px solid #dddddd;
        margin-top: 70px;
        padding-top: 25px;
        text-align: center;
        color: #888888;
        font-size: 10px;
        line-height: 1.7;
    }

    .footer-logo {
        color: #E50010;
        font-size: 15px;
        font-weight: 900;
        letter-spacing: -1px;
        margin-bottom: 5px;
    }

    </style>
    """
)


# =========================================================
# HEADER
# =========================================================

st.html(
    """
    <div class="header">

        <div class="logo">H&M</div>

        <div class="nav">

            <div class="nav-item">Ladies</div>
            <div class="nav-item">Men</div>
            <div class="nav-item">Kids</div>
            <div class="nav-item">Home</div>
            <div class="nav-sale">Sale</div>

        </div>

    </div>
    """
)


# =========================================================
# HERO
# =========================================================

st.html(
    """
    <div class="hero">

        <div class="hero-small">
            H&M Recommendation
        </div>

        <div class="hero-title">
            Discover your next favourite
        </div>

        <div class="hero-text">
            Explore a personalised selection based on
            shopping behaviour and product similarity.
        </div>

    </div>
    """
)


# =========================================================
# MODE SELECTION
# =========================================================
#
# We deliberately use Streamlit buttons rather than tabs.
# This makes both modes reliably visible across deployments.
#

if "mode" not in st.session_state:
    st.session_state.mode = "for_you"


st.html(
    """
    <div class="mode-bar"></div>
    """
)


mode_col1, mode_col2 = st.columns(2)


with mode_col1:

    if st.button(
        "FOR YOU",
        use_container_width=True,
        key="for_you_button"
    ):
        st.session_state.mode = "for_you"


with mode_col2:

    if st.button(
        "SIMILAR PRODUCTS",
        use_container_width=True,
        key="similar_products_button"
    ):
        st.session_state.mode = "similar"


# =========================================================
# FOR YOU
# =========================================================

if st.session_state.mode == "for_you":

    st.html(
        """
        <div style="margin-top:35px;">

            <div class="mode-title">
                Your recommendations
            </div>

            <div class="mode-description">
                Enter a customer ID to view a personalised selection.
            </div>

        </div>
        """
    )


    user_id = st.text_input(
        "Customer ID",
        placeholder="Enter customer ID",
        key="recommend_user_id"
    )


    button_col1, button_col2 = st.columns(
        [4, 1]
    )


    with button_col2:

        recommend = st.button(
            "VIEW SELECTION",
            use_container_width=True,
            type="primary",
            key="recommend_button"
        )


    if recommend:

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
                            "top_k": 10
                        },
                        timeout=60
                    )


                    if response.status_code == 200:

                        data = response.json()

                        recommendations = data.get(
                            "recommendations",
                            []
                        )

                        is_new_user = data.get(
                            "is_new_user",
                            False
                        )


                        if is_new_user:

                            st.html(
                                """
                                <div class="message">

                                    <b>Welcome.</b>
                                    <br>

                                    We don't have enough shopping
                                    history for this customer yet.
                                    This selection is based on
                                    popular products.

                                </div>
                                """
                            )

                        else:

                            st.html(
                                """
                                <div class="message">

                                    <b>Selected for you.</b>
                                    <br>

                                    This selection is based on
                                    previous shopping behaviour
                                    and product characteristics.

                                </div>
                                """
                            )


                        st.html(
                            """
                            <div class="section">

                                <div class="section-title">
                                    Recommended for you
                                </div>

                                <div class="section-note">
                                    Curated selection
                                </div>

                            </div>
                            """
                        )


                        if recommendations:

                            product_columns = st.columns(5)


                            for i, product in enumerate(
                                recommendations
                            ):

                                with product_columns[i % 5]:

                                    name = str(
                                        product.get(
                                            "product_name",
                                            "Product"
                                        )
                                    )

                                    category = str(
                                        product.get(
                                            "category",
                                            ""
                                        )
                                    )

                                    article_id = str(
                                        product.get(
                                            "article_id",
                                            ""
                                        )
                                    )

                                    score = product.get(
                                        "score"
                                    )


                                    if score is None:

                                        ranking = """
                                        <div class="popular">
                                            Popular selection
                                        </div>
                                        """

                                    else:

                                        ranking = f"""
                                        <div class="score">
                                            Recommendation score
                                            {float(score):.4f}
                                        </div>
                                        """


                                    st.html(
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
                                            product-info">

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
                                                    Article {article_id}
                                                </div>

                                                {ranking}

                                            </div>

                                        </div>
                                        """
                                    )


                        else:

                            st.info(
                                "No recommendations found."
                            )


                    elif response.status_code == 404:

                        st.warning(
                            "No recommendations could be "
                            "generated for this customer."
                        )


                    elif response.status_code == 503:

                        st.error(
                            "Recommendation service is "
                            "currently unavailable."
                        )


                    else:

                        st.error(
                            f"API request failed: "
                            f"{response.status_code}"
                        )


                except requests.RequestException as error:

                    st.error(
                        "Could not connect to the "
                        "recommendation service."
                    )

                    st.caption(
                        str(error)
                    )


# =========================================================
# SIMILAR PRODUCTS
# =========================================================

else:

    st.html(
        """
        <div style="margin-top:35px;">

            <div class="mode-title">
                Find similar products
            </div>

            <div class="mode-description">
                Enter an article number to discover
                similar styles.
            </div>

        </div>
        """
    )


    article_id = st.text_input(
        "Article number",
        placeholder="Example: 108775015",
        key="similar_article_id"
    )


    button_col1, button_col2 = st.columns(
        [4, 1]
    )


    with button_col2:

        find_similar = st.button(
            "FIND SIMILAR",
            use_container_width=True,
            type="primary",
            key="similar_button"
        )


    if find_similar:

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
                            "top_k": 10
                        },
                        timeout=60
                    )


                    if response.status_code == 200:

                        data = response.json()

                        products = data.get(
                            "similar_products",
                            []
                        )


                        st.html(
                            """
                            <div class="message">

                                <b>Similar styles.</b>
                                <br>

                                Products are ranked using
                                content similarity between
                                product descriptions.

                            </div>
                            """
                        )


                        st.html(
                            """
                            <div class="section">

                                <div class="section-title">
                                    You may also like
                                </div>

                                <div class="section-note">
                                    Similar styles
                                </div>

                            </div>
                            """
                        )


                        if products:

                            product_columns = st.columns(5)


                            for i, product in enumerate(
                                products
                            ):

                                with product_columns[i % 5]:

                                    name = str(
                                        product.get(
                                            "product_name",
                                            "Product"
                                        )
                                    )

                                    category = str(
                                        product.get(
                                            "category",
                                            ""
                                        )
                                    )

                                    candidate_id = str(
                                        product.get(
                                            "article_id",
                                            ""
                                        )
                                    )

                                    similarity = float(
                                        product.get(
                                            "similarity_score",
                                            0
                                        )
                                    )


                                    st.html(
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
                                            product-info">

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
                                                    Article
                                                    {candidate_id}
                                                </div>

                                                <div class="
                                                score">
                                                    Similarity
                                                    {similarity:.4f}
                                                </div>

                                            </div>

                                        </div>
                                        """
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
                            f"Article {article_id} was not "
                            "found in the catalogue."
                        )


                    elif response.status_code == 503:

                        st.error(
                            "Recommendation service is "
                            "currently unavailable."
                        )


                    else:

                        st.error(
                            f"API request failed: "
                            f"{response.status_code}"
                        )


                except requests.RequestException as error:

                    st.error(
                        "Could not connect to the "
                        "recommendation service."
                    )

                    st.caption(
                        str(error)
                    )


# =========================================================
# FOOTER
# =========================================================

st.html(
    """
    <div class="footer">

        <div class="footer-logo">
            H&M
        </div>

        Personalised fashion discovery

    </div>
    """
)
