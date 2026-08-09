import os
import html
import requests
import streamlit as st


# =========================================================
# CONFIG
# =========================================================

API_URL = os.getenv(
    "API_URL",
    "https://hybrid-ecommerce-recommendation-system.onrender.com"
)

IMAGE_BASE_URL = (
    "https://qdrant-nextjs-demo-product-images"
    ".s3.us-east-1.amazonaws.com/images"
)


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
# HELPER FUNCTIONS
# =========================================================

def get_product_image_url(article_id):
    """
    Convert H&M article_id into the verified image URL format.

    Example:

        658030001
            -> 065/0658030001.jpg

        108775015
            -> 010/0108775015.jpg
    """

    article_id = str(article_id).strip()

    if not article_id.isdigit():
        return None

    article_id = article_id.zfill(10)

    folder = article_id[:3]

    return (
        f"{IMAGE_BASE_URL}/"
        f"{folder}/"
        f"{article_id}.jpg"
    )


def safe_text(value):
    """
    Safely escape text before putting it into HTML.
    """
    if value is None:
        return ""

    return html.escape(str(value))


def get_recommendations(user_id, top_k=10):
    """
    Call the recommendation API.
    """

    response = requests.get(
        f"{API_URL}/recommend/{user_id}",
        params={
            "top_k": top_k
        },
        timeout=60
    )

    return response


def get_similar_products(article_id, top_k=10):
    """
    Call the content-based similarity API.
    """

    response = requests.get(
        f"{API_URL}/similar/{article_id}",
        params={
            "top_k": top_k
        },
        timeout=60
    )

    return response


# =========================================================
# CUSTOM CSS
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
        letter-spacing: 0.5px;
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
       MODE NAVIGATION
       ===================================================== */

    .mode-bar {
        border-top: 1px solid #111111;
        border-bottom: 1px solid #dddddd;
        margin-bottom: 35px;
    }

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
        color: #ffffff !important;
        border: 1px solid #E50010 !important;
        font-size: 11px !important;
        font-weight: 600 !important;
        letter-spacing: 0.6px !important;
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
        height: 330px;
        background: #f2f2f0;
        overflow: hidden;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .product-real-image {
        width: 100%;
        height: 100%;
        object-fit: cover;
        display: block;
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
        letter-spacing: 0.7px;
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
# MODE STATE
# =========================================================

if "mode" not in st.session_state:
    st.session_state.mode = "for_you"


# =========================================================
# MODE NAVIGATION
# =========================================================

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


    input_col, button_col = st.columns(
        [4, 1]
    )


    with button_col:

        recommend_clicked = st.button(
            "VIEW SELECTION",
            use_container_width=True,
            type="primary",
            key="recommend_button"
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

                    response = get_recommendations(
                        user_id.strip(),
                        top_k=10
                    )


                    # =================================================
                    # SUCCESS
                    # =================================================

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


                        # -------------------------------------------------
                        # MESSAGE
                        # -------------------------------------------------

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


                        # -------------------------------------------------
                        # SECTION TITLE
                        # -------------------------------------------------

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


                        # -------------------------------------------------
                        # PRODUCTS
                        # -------------------------------------------------

                        if recommendations:

                            product_columns = st.columns(5)


                            for i, product in enumerate(
                                recommendations
                            ):

                                with product_columns[i % 5]:

                                    name = safe_text(
                                        product.get(
                                            "product_name",
                                            "Product"
                                        )
                                    )

                                    category = safe_text(
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
                                    ).strip()


                                    score = product.get(
                                        "score"
                                    )


                                    # -----------------------------------------
                                    # IMAGE
                                    # -----------------------------------------

                                    image_url = (
                                        get_product_image_url(
                                            article_id
                                        )
                                    )


                                    if image_url:

                                        image_html = f"""
                                        <img
                                            src="{image_url}"
                                            class="product-real-image"
                                            loading="lazy"
                                            alt="{name}"
                                        >
                                        """

                                    else:

                                        image_html = """
                                        <div class="
                                        product-placeholder">
                                            H&M
                                        </div>
                                        """


                                    # -----------------------------------------
                                    # SCORE
                                    # -----------------------------------------

                                    if score is None:

                                        ranking_html = """
                                        <div class="popular">
                                            Popular selection
                                        </div>
                                        """

                                    else:

                                        try:

                                            score_value = float(
                                                score
                                            )

                                            ranking_html = f"""
                                            <div class="score">
                                                Recommendation score
                                                {score_value:.4f}
                                            </div>
                                            """

                                        except (
                                            TypeError,
                                            ValueError
                                        ):

                                            ranking_html = ""


                                    # -----------------------------------------
                                    # CARD
                                    # -----------------------------------------

                                    st.html(
                                        f"""
                                        <div class="product-card">

                                            <div class="
                                            product-image">

                                                {image_html}

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
                                                    {article_id}

                                                </div>

                                                {ranking_html}

                                            </div>

                                        </div>
                                        """
                                    )


                        else:

                            st.info(
                                "No recommendations found."
                            )


                    # =================================================
                    # NOT FOUND
                    # =================================================

                    elif response.status_code == 404:

                        st.warning(
                            "No recommendations could be "
                            "generated for this customer."
                        )


                    # =================================================
                    # SERVICE UNAVAILABLE
                    # =================================================

                    elif response.status_code == 503:

                        st.error(
                            "Recommendation service is "
                            "currently unavailable."
                        )


                    # =================================================
                    # OTHER
                    # =================================================

                    else:

                        st.error(
                            f"API request failed: "
                            f"{response.status_code}"
                        )


                except requests.RequestException:

                    st.error(
                        "Could not connect to the "
                        "recommendation service."
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


    article_id_input = st.text_input(
        "Article number",
        placeholder="Example: 108775015",
        key="similar_article_id"
    )


    input_col, button_col = st.columns(
        [4, 1]
    )


    with button_col:

        find_clicked = st.button(
            "FIND SIMILAR",
            use_container_width=True,
            type="primary",
            key="similar_button"
        )


    if find_clicked:

        if not article_id_input.strip():

            st.warning(
                "Please enter an article number."
            )

        else:

            if not article_id_input.strip().isdigit():

                st.error(
                    "Article number must be numeric."
                )

            else:

                with st.spinner(
                    "Finding similar styles..."
                ):

                    try:

                        response = get_similar_products(
                            article_id_input.strip(),
                            top_k=10
                        )


                        # =================================================
                        # SUCCESS
                        # =================================================

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


                            # -------------------------------------------------
                            # PRODUCTS
                            # -------------------------------------------------

                            if products:

                                product_columns = st.columns(5)


                                for i, product in enumerate(
                                    products
                                ):

                                    with product_columns[i % 5]:

                                        name = safe_text(
                                            product.get(
                                                "product_name",
                                                "Product"
                                            )
                                        )

                                        category = safe_text(
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
                                        ).strip()


                                        similarity = product.get(
                                            "similarity_score",
                                            0
                                        )


                                        # -------------------------------------
                                        # IMAGE
                                        # -------------------------------------

                                        image_url = (
                                            get_product_image_url(
                                                candidate_id
                                            )
                                        )


                                        if image_url:

                                            image_html = f"""
                                            <img
                                                src="{image_url}"
                                                class="product-real-image"
                                                loading="lazy"
                                                alt="{name}"
                                            >
                                            """

                                        else:

                                            image_html = """
                                            <div class="
                                            product-placeholder">
                                                H&M
                                            </div>
                                            """


                                        # -------------------------------------
                                        # SIMILARITY
                                        # -------------------------------------

                                        try:

                                            similarity_value = float(
                                                similarity
                                            )

                                            score_html = f"""
                                            <div class="score">
                                                Similarity
                                                {similarity_value:.4f}
                                            </div>
                                            """

                                        except (
                                            TypeError,
                                            ValueError
                                        ):

                                            score_html = ""


                                        # -------------------------------------
                                        # CARD
                                        # -------------------------------------

                                        st.html(
                                            f"""
                                            <div class="product-card">

                                                <div class="
                                                product-image">

                                                    {image_html}

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

                                                    {score_html}

                                                </div>

                                            </div>
                                            """
                                        )


                            else:

                                st.info(
                                    "No similar products found."
                                )


                        # =================================================
                        # BAD ARTICLE ID
                        # =================================================

                        elif response.status_code == 400:

                            st.error(
                                "Article number must be numeric."
                            )


                        # =================================================
                        # ARTICLE NOT FOUND
                        # =================================================

                        elif response.status_code == 404:

                            st.error(
                                f"Article "
                                f"{article_id_input.strip()} "
                                "was not found in the catalogue."
                            )


                        # =================================================
                        # SERVICE UNAVAILABLE
                        # =================================================

                        elif response.status_code == 503:

                            st.error(
                                "Recommendation service is "
                                "currently unavailable."
                            )


                        # =================================================
                        # OTHER
                        # =================================================

                        else:

                            st.error(
                                f"API request failed: "
                                f"{response.status_code}"
                            )


                    except requests.RequestException:

                        st.error(
                            "Could not connect to the "
                            "recommendation service."
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
