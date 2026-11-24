import hashlib
import os
import tempfile

import streamlit as st

from converter import convert, convert_image

IMAGE_TYPES = ["png", "jpg", "jpeg", "webp", "bmp", "tif", "tiff"]

st.set_page_config(
    page_title="PDF & Image to Markdown | LLM-Optimized",
    page_icon="📄",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# Custom CSS for modern styling
st.markdown(
    """
    <style>
    /* Global Container */
    .block-container {
        max-width: 860px;
        padding-top: 2rem;
        padding-bottom: 4rem;
    }

    /* Hero Section */
    .hero-badge-container {
        display: flex;
        justify-content: center;
        gap: 8px;
        flex-wrap: wrap;
        margin-bottom: 1rem;
    }

    .hero-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 5px 14px;
        border-radius: 9999px;
        font-size: 0.8rem;
        font-weight: 600;
        letter-spacing: 0.03em;
        text-transform: uppercase;
        background: rgba(99, 102, 241, 0.12);
        color: #818CF8;
        border: 1px solid rgba(99, 102, 241, 0.28);
    }

    .hero-badge.secondary {
        background: rgba(16, 185, 129, 0.12);
        color: #34D399;
        border-color: rgba(16, 185, 129, 0.28);
    }

    .hero-title {
        font-size: 2.6rem;
        font-weight: 800;
        line-height: 1.2;
        letter-spacing: -0.02em;
        margin-bottom: 0.75rem;
        background: linear-gradient(135deg, #FFFFFF 20%, #CBD5E1 60%, #818CF8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .hero-subtitle {
        font-size: 1.05rem;
        color: #94A3B8;
        line-height: 1.6;
        margin-bottom: 1.75rem;
    }

    /* Privacy Banner */
    .privacy-pill {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 10px 14px;
        border-radius: 10px;
        background: rgba(15, 23, 42, 0.6);
        border: 1px solid rgba(148, 163, 184, 0.15);
        color: #94A3B8;
        font-size: 0.84rem;
        margin-top: 0.5rem;
        margin-bottom: 2rem;
    }

    /* Feature Grid */
    .feature-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(230px, 1fr));
        gap: 16px;
        margin: 2rem 0;
    }

    .feature-card {
        padding: 20px;
        border-radius: 14px;
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.07);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }

    .feature-card:hover {
        transform: translateY(-2px);
        border-color: rgba(99, 102, 241, 0.4);
    }

    .feature-icon {
        font-size: 1.6rem;
        margin-bottom: 10px;
    }

    .feature-card h4 {
        margin: 0 0 6px 0;
        font-size: 1.05rem;
        font-weight: 700;
        color: #F1F5F9;
    }

    .feature-card p {
        margin: 0;
        font-size: 0.88rem;
        color: #94A3B8;
        line-height: 1.5;
    }

    /* Workflow Steps */
    .steps-container {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 12px;
        background: rgba(30, 41, 59, 0.4);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 12px;
        padding: 16px 20px;
        margin: 1.5rem 0 2.5rem 0;
    }

    .step-item {
        display: flex;
        align-items: center;
        gap: 10px;
        font-size: 0.9rem;
        color: #E2E8F0;
    }

    .step-num {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 24px;
        height: 24px;
        border-radius: 50%;
        background: #4F46E5;
        color: #FFFFFF;
        font-size: 0.75rem;
        font-weight: 700;
    }

    .step-arrow {
        color: #64748B;
        font-size: 1.1rem;
    }

    /* Result Info Banner */
    .result-banner {
        padding: 16px 20px;
        border-radius: 12px;
        background: rgba(16, 185, 129, 0.08);
        border: 1px solid rgba(16, 185, 129, 0.25);
        color: #A7F3D0;
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 1.25rem;
    }

    /* Metric Box */
    [data-testid="stMetricValue"] {
        font-size: 1.7rem !important;
        font-weight: 700 !important;
        color: #F8FAFC !important;
    }

    /* Footer */
    .app-footer {
        text-align: center;
        margin-top: 4rem;
        padding-top: 1.5rem;
        border-top: 1px solid rgba(255, 255, 255, 0.07);
        font-size: 0.85rem;
        color: #64748B;
    }
    .app-footer a {
        color: #818CF8;
        text-decoration: none;
    }
    .app-footer a:hover {
        text-decoration: underline;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner=False, max_entries=20)
def run_conversion(file_bytes: bytes, digest: str, is_pdf: bool) -> str:
    # `digest` makes the cache key explicit. The file is only written to a
    # temporary folder for the conversion and deleted right after.
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "input")
        with open(path, "wb") as f:
            f.write(file_bytes)
        return convert(path) if is_pdf else convert_image(path)


# ---------------------------------------------------------------- HERO HEADER
st.markdown(
    """
    <div style="text-align: center; margin-bottom: 1.5rem;">
        <div class="hero-badge-container">
            <span class="hero-badge">⚡ Token-Optimized for AI</span>
            <span class="hero-badge secondary">📸 PDF &amp; Image OCR</span>
        </div>
        <h1 class="hero-title">Turn PDFs &amp; Images into Clean Markdown</h1>
        <p class="hero-subtitle">
            Upload any PDF, screenshot, or document photo. Get structured, publication-grade <strong>.md</strong> with intact headings,
            tables, lists, and syntax-highlighted code blocks. Cut input token consumption by up to <strong>87%</strong> in ChatGPT, Claude, and Gemini.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------- FILE UPLOADER
uploaded = st.file_uploader(
    "Choose a PDF or image file (PNG, JPG, WEBP, TIFF up to 50 MB)",
    type=["pdf"] + IMAGE_TYPES,
    help="Upload any PDF or document photo/screenshot.",
)

st.markdown(
    """
    <div class="privacy-pill">
        <span>🔒</span>
        <span><strong>100% In-Memory &amp; Private:</strong> Files are processed ephemerally and deleted immediately after conversion. Never stored, never logged.</span>
    </div>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------- RESULTS OR LANDING PAGE
if uploaded is not None:
    data = uploaded.getvalue()
    is_pdf = data.startswith(b"%PDF-")

    if not is_pdf and uploaded.name.lower().endswith(".pdf"):
        st.error("⚠️ That file is not a valid PDF. Please upload a standard `.pdf` file.")
        st.stop()

    if not is_pdf:
        with st.expander("🖼️ View uploaded image", expanded=False):
            st.image(data, use_container_width=True)

    try:
        spinner_msg = (
            f"Converting **{uploaded.name}** to clean Markdown…"
            if is_pdf
            else f"Reading text from **{uploaded.name}** via OCR (may take a moment)…"
        )
        with st.spinner(spinner_msg):
            markdown = run_conversion(data, hashlib.sha256(data).hexdigest(), is_pdf)
    except Exception:
        st.error(
            "⚠️ Could not read this file. A PDF may be corrupted or password-protected, "
            "and an image may be in an unsupported format."
        )
        st.stop()

    if not markdown.strip():
        st.warning(
            "⚠️ No text found in this file. For images, try a sharper, higher-resolution picture "
            "with the text clearly visible."
        )
        st.stop()

    out_name = (os.path.splitext(uploaded.name)[0] or "document") + ".md"
    char_count = len(markdown)
    token_est = round(char_count / 3.6)

    # Success Banner
    st.markdown(
        f"""
        <div class="result-banner">
            <div>
                <strong>✅ Ready to download:</strong> {uploaded.name} ({(len(data)/1024):,.1f} KB)
            </div>
            <div style="font-size: 0.85rem; opacity: 0.9;">
                {"PDF Structure Restored" if is_pdf else "OCR Extraction Complete"}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Metrics Row
    m_col1, m_col2, m_col3 = st.columns(3)
    m_col1.metric("Characters", f"{char_count:,}")
    m_col2.metric("Estimated Tokens", f"{token_est:,}", help="Approx. 3.6 characters per token")
    m_col3.metric("Token Reduction", "~55% – 87%", help="Compared to vision-based ingestion")

    if not is_pdf:
        st.caption("ℹ️ OCR output can contain small recognition errors. Skim through before copying.")

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

    # Download Button
    st.download_button(
        label=f"📥 Download {out_name}",
        data=markdown,
        file_name=out_name,
        mime="text/markdown",
        type="primary",
        use_container_width=True,
    )

    st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)

    # Tabs for Inspection
    raw_tab, preview_tab = st.tabs(["📄 Markdown Code", "👁️ Formatted Preview"])
    with raw_tab:
        st.code(markdown, language="markdown")
    with preview_tab:
        st.markdown(markdown, unsafe_allow_html=True)

else:
    # ------------------------------------------------ LANDING PAGE CONTENT (EMPTY STATE)
    # 3-Step Flow
    st.markdown(
        """
        <div class="steps-container">
            <div class="step-item">
                <span class="step-num">1</span>
                <div><strong>Upload File</strong><br><small style="color:#94A3B8;">PDF or image screenshot</small></div>
            </div>
            <span class="step-arrow">→</span>
            <div class="step-item">
                <span class="step-num">2</span>
                <div><strong>Auto-Repair &amp; OCR</strong><br><small style="color:#94A3B8;">Code, tables &amp; text cleaned</small></div>
            </div>
            <span class="step-arrow">→</span>
            <div class="step-item">
                <span class="step-num">3</span>
                <div><strong>Prompt AI</strong><br><small style="color:#94A3B8;">One-click copy or download</small></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Feature Highlights Grid
    st.markdown(
        """
        <div class="feature-grid">
            <div class="feature-card">
                <div class="feature-icon">⚡</div>
                <h4>Massive Token Savings</h4>
                <p>Standard PDF/image uploads force chatbots to render pages as costly vision tokens. Clean Markdown cuts token usage by 55% to 87%.</p>
            </div>
            <div class="feature-card">
                <div class="feature-icon">📸</div>
                <h4>Screenshots &amp; Photos (OCR)</h4>
                <p>Upload document photos or screen captures in PNG, JPG, or WEBP. RapidOCR automatically extracts readable text and tables.</p>
            </div>
            <div class="feature-card">
                <div class="feature-icon">💻</div>
                <h4>Monospace &amp; Code Recovery</h4>
                <p>Detects font styles to reconstruct indented multiline code blocks, infer programming languages (SQL, Python, JS, Bash), and format backticks.</p>
            </div>
            <div class="feature-card">
                <div class="feature-icon">🧹</div>
                <h4>Page Break &amp; Header Cleanup</h4>
                <p>Identifies and strips repeating headers and footers across multi-page documents while automatically stitching split tables together.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Token Savings Comparison Table Section
    with st.expander("💡 **Why Convert? See Token Savings on a 17-Page PDF**", expanded=True):
        st.markdown(
            """
            Uploading a clean **.md** file instead of a 17-page PDF to modern AI chatbots (ChatGPT, Claude, or Gemini)
            saves **5,000 to 26,000 tokens**—a **55% to 87% reduction** in input costs and latency:

            | AI Chatbot / Platform | How It Reads Your 17-Page PDF | PDF Input Cost | `.md` Input Cost | Tokens Saved |
            | :--- | :--- | :--- | :--- | :--- |
            | **Claude** (Web / API) | Extracts text + renders all 17 pages as images | ~28,000 – 31,000 | ~3,966 | **~24,000 – 27,000 (~87%)** |
            | **ChatGPT** (GPT-4o / o3 / GPT-5) | Extracts text + renders pages as images for vision | ~15,000 – 22,000 | ~3,966 | **~11,000 – 18,000 (~75–82%)** |
            | **Gemini** (Default / Med res) | Renders all 17 pages natively (~560 tokens/page) | ~9,520 | ~3,966 | **~5,554 (~58%)** |
            | **Gemini** (Low res / Older 2.5) | Renders all 17 pages at low res (~258–280 tokens/page) | ~4,386 – 4,760 | ~3,966 | **~420 – 794 (~10–17%)** |
            | **Text-only tools / Local LLMs** | Strips images and reads only the raw text layer | ~3,700 – 3,900 | ~3,966 | ~0 tokens |
            """
        )

# ---------------------------------------------------------------- FOOTER
st.markdown(
    """
    <div class="app-footer">
        Powered by <a href="https://github.com/pymupdf/PyMuPDF" target="_blank">PyMuPDF4LLM</a> &amp; 
        <a href="https://streamlit.io/" target="_blank">Streamlit</a> • 
        <a href="https://github.com/shrithisside/md-converter" target="_blank">View GitHub Repository</a>
    </div>
    """,
    unsafe_allow_html=True,
)


else:
    # ------------------------------------------------ LANDING PAGE CONTENT (EMPTY STATE)
    # 3-Step Flow
    st.markdown(
        """
        <div class="steps-container">
            <div class="step-item">
                <span class="step-num">1</span>
                <div><strong>Upload File</strong><br><small style="color:#94A3B8;">PDF or image screenshot</small></div>
            </div>
            <span class="step-arrow">→</span>
            <div class="step-item">
                <span class="step-num">2</span>
                <div><strong>Auto-Repair &amp; OCR</strong><br><small style="color:#94A3B8;">Code, tables &amp; text cleaned</small></div>
            </div>
            <span class="step-arrow">→</span>
            <div class="step-item">
                <span class="step-num">3</span>
                <div><strong>Prompt AI</strong><br><small style="color:#94A3B8;">One-click copy or download</small></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Feature Highlights Grid
    st.markdown(
        """
        <div class="feature-grid">
            <div class="feature-card">
                <div class="feature-icon">⚡</div>
                <h4>Massive Token Savings</h4>
                <p>Standard PDF/image uploads force chatbots to render pages as costly vision tokens. Clean Markdown cuts token usage by 55% to 87%.</p>
            </div>
            <div class="feature-card">
                <div class="feature-icon">📸</div>
                <h4>Screenshots &amp; Photos (OCR)</h4>
                <p>Upload document photos or screen captures in PNG, JPG, or WEBP. RapidOCR automatically extracts readable text and tables.</p>
            </div>
            <div class="feature-card">
                <div class="feature-icon">💻</div>
                <h4>Monospace &amp; Code Recovery</h4>
                <p>Detects font styles to reconstruct indented multiline code blocks, infer programming languages (SQL, Python, JS, Bash), and format backticks.</p>
            </div>
            <div class="feature-card">
                <div class="feature-icon">🧹</div>
                <h4>Page Break &amp; Header Cleanup</h4>
                <p>Identifies and strips repeating headers and footers across multi-page documents while automatically stitching split tables together.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Token Savings Comparison Table Section
    with st.expander("💡 **Why Convert? See Token Savings on a 17-Page PDF**", expanded=True):
        st.markdown(
            """
            Uploading a clean **.md** file instead of a 17-page PDF to modern AI chatbots (ChatGPT, Claude, or Gemini)
            saves **5,000 to 26,000 tokens**—a **55% to 87% reduction** in input costs and latency:

            | AI Chatbot / Platform | How It Reads Your 17-Page PDF | PDF Input Cost | `.md` Input Cost | Tokens Saved |
            | :--- | :--- | :--- | :--- | :--- |
            | **Claude** (Web / API) | Extracts text + renders all 17 pages as images | ~28,000 – 31,000 | ~3,966 | **~24,000 – 27,000 (~87%)** |
            | **ChatGPT** (GPT-4o / o3 / GPT-5) | Extracts text + renders pages as images for vision | ~15,000 – 22,000 | ~3,966 | **~11,000 – 18,000 (~75–82%)** |
            | **Gemini** (Default / Med res) | Renders all 17 pages natively (~560 tokens/page) | ~9,520 | ~3,966 | **~5,554 (~58%)** |
            | **Gemini** (Low res / Older 2.5) | Renders all 17 pages at low res (~258–280 tokens/page) | ~4,386 – 4,760 | ~3,966 | **~420 – 794 (~10–17%)** |
            | **Text-only tools / Local LLMs** | Strips images and reads only the raw text layer | ~3,700 – 3,900 | ~3,966 | ~0 tokens |
            """
        )

# ---------------------------------------------------------------- FOOTER
st.markdown(
    """
    <div class="app-footer">
        Powered by <a href="https://github.com/pymupdf/PyMuPDF" target="_blank">PyMuPDF4LLM</a> &amp; 
        <a href="https://streamlit.io/" target="_blank">Streamlit</a> • 
        <a href="https://github.com/shrithisside/md-converter" target="_blank">View GitHub Repository</a>
    </div>
    """,
    unsafe_allow_html=True,
)