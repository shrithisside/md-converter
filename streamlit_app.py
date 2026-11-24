import hashlib
import os
import tempfile

import streamlit as st

from converter import convert, convert_image

IMAGE_TYPES = ["png", "jpg", "jpeg", "webp", "bmp", "tif", "tiff"]

st.set_page_config(page_title="PDF & Image to Markdown", page_icon="📄", layout="centered")

st.title("Turn a PDF or image into Markdown")
st.write(
    "Upload a PDF, or a screenshot / photo of a document, and get a clean .md file "
    "back, with headings, lists and tables kept. Markdown uses far fewer tokens than "
    "a PDF or image when you paste it into an AI chat."
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


uploaded = st.file_uploader("Choose a PDF or image", type=["pdf"] + IMAGE_TYPES)

if uploaded is not None:
    data = uploaded.getvalue()
    is_pdf = data.startswith(b"%PDF-")

    if not is_pdf and uploaded.name.lower().endswith(".pdf"):
        st.error("That file is not a valid PDF.")
        st.stop()

    if not is_pdf:
        with st.expander("Image preview", expanded=False):
            st.image(data, use_container_width=True)

    try:
        message = (
            f"Converting {uploaded.name}…"
            if is_pdf
            else f"Reading text from {uploaded.name} (OCR can take up to a minute)…"
        )
        with st.spinner(message):
            markdown = run_conversion(data, hashlib.sha256(data).hexdigest(), is_pdf)
    except Exception:
        st.error(
            "Could not read this file. A PDF may be corrupted or password-protected, "
            "and an image may be in an unsupported format."
        )
        st.stop()

    if not markdown.strip():
        st.error(
            "No text found. For images, try a sharper, higher-resolution picture "
            "with the text clearly visible."
        )
        st.stop()

    out_name = (os.path.splitext(uploaded.name)[0] or "document") + ".md"

    col1, col2 = st.columns(2)
    col1.metric("Characters", f"{len(markdown):,}")
    col2.metric("Approx. tokens", f"{round(len(markdown) / 3.6):,}")
    st.caption("Token count is a rough estimate (about 3.6 characters per token).")

    if not is_pdf:
        st.info("OCR output can contain small recognition errors. Skim it before relying on it.")

    st.download_button(
        "Download .md",
        data=markdown,
        file_name=out_name,
        mime="text/markdown",
        type="primary",
    )

    raw_tab, preview_tab = st.tabs(["Markdown", "Preview"])
    with raw_tab:
        st.code(markdown, language="markdown")  # has a built-in copy button
    with preview_tab:
        st.markdown(markdown, unsafe_allow_html=True)