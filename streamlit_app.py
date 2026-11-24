import hashlib
import os
import tempfile

import streamlit as st

from converter import convert

st.set_page_config(page_title="PDF to Markdown", page_icon="📄", layout="centered")

st.title("Turn a PDF into Markdown")
st.write(
    "Upload a PDF and get a clean .md file back, with headings, lists, tables and "
    "code blocks kept. Markdown uses far fewer tokens than a PDF when you paste it "
    "into an AI chat."
)


@st.cache_data(show_spinner=False, max_entries=20)
def run_conversion(pdf_bytes: bytes, digest: str) -> str:
    # `digest` makes the cache key explicit. The file is only written to a
    # temporary folder for the conversion and deleted right after.
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "input.pdf")
        with open(path, "wb") as f:
            f.write(pdf_bytes)
        return convert(path)


uploaded = st.file_uploader("Choose a PDF", type=["pdf"])

if uploaded is not None:
    data = uploaded.getvalue()

    if not data.startswith(b"%PDF-"):
        st.error("That file is not a valid PDF.")
        st.stop()

    try:
        with st.spinner(f"Converting {uploaded.name}…"):
            markdown = run_conversion(data, hashlib.sha256(data).hexdigest())
    except Exception:
        st.error(
            "Could not read this PDF. It may be corrupted, password-protected, "
            "or a scan (scans need OCR, which is not available on this server)."
        )
        st.stop()

    if not markdown.strip():
        st.error("No text found in this PDF.")
        st.stop()

    out_name = (os.path.splitext(uploaded.name)[0] or "document") + ".md"

    col1, col2 = st.columns(2)
    col1.metric("Characters", f"{len(markdown):,}")
    col2.metric("Approx. tokens", f"{round(len(markdown) / 3.6):,}")
    st.caption("Token count is a rough estimate (about 3.6 characters per token).")

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