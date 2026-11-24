# PDF & Image to Markdown Converter 📄 📸 ➡️ 📝

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://md-converter-shrithisside.streamlit.app/)

A fast, lightweight tool and Streamlit web application that converts PDF documents and image screenshots/photos into clean, structured, and token-efficient **Markdown** (`.md`). 

🌐 **Live Demo:** [md-converter-shrithisside.streamlit.app](https://md-converter-shrithisside.streamlit.app/) 

Designed especially for preparing documents for Large Language Models (LLMs) and AI chat prompts, it extracts content using PyMuPDF4LLM and RapidOCR, then applies targeted post-processing heuristics to fix common extraction glitches found in real-world PDFs and scans.

---

## ✨ Features

- **🚀 Token Efficiency for LLMs**: Markdown uses significantly fewer tokens than raw PDF or image uploads when prompting AI models, while preserving essential document semantics.
- **📸 Screenshot & Document Image OCR**: Built-in support for converting images (`.png`, `.jpg`, `.jpeg`, `.webp`, `.bmp`, `.tiff`) into Markdown using RapidOCR and layout-aware text detection.
- **💻 Smart Code Block Reconstruction**: Detects monospace fonts in the original PDF to reconstruct multiline code blocks and inline code backticks (`` `code` ``), complete with automatic language guessing (Bash, Python, JavaScript, JSON, SQL).
- **📑 Header & Footer Deduplication**: Automatically detects and drops repetitive running page headers and footers across multi-page documents.
- **📊 Table Continuation Stitching**: Automatically merges tables split across page breaks, deduplicating repeated header rows.
- **🧹 Noise & Artifact Removal**: Strips OCR artifacts, picture-text comments, stray HTML tags (`<mark>`, `<u>`), and fixes spacing around bold text and inline elements.
- **📈 Real-Time Metrics**: Displays total character counts and estimated token counts (~3.6 characters per token) to help gauge prompt sizes.
- **👁️ Dual View (Raw & Rendered)**: Inspect the raw Markdown with a one-click copy button, preview images, or preview the rendered HTML directly in the browser.
- **💾 Fast & Cached**: Uses SHA-256 hashing to cache conversion results for snappy UI interactions and quick `.md` downloads.
- **🔍 OCR Fallback**: Automatically retries using OCR for scanned PDFs when minimal text is detected.

---

## 💡 Why Convert? Token Savings Breakdown

Uploading a `.md` file instead of a 17-page PDF to a modern AI chatbot (ChatGPT, Claude, or Gemini) saves roughly **5,000 to 26,000 tokens**—a **55% to 87% reduction** in input tokens.

The exact savings depend on how the chatbot processes PDFs under the hood:

| AI Chatbot / Platform | How It Reads Your 17-Page PDF | PDF Input Cost | `.md` Input Cost | Tokens Saved |
| :--- | :--- | :--- | :--- | :--- |
| **Claude** (Web / API) | Extracts text + renders all 17 pages as images | ~28,000 – 31,000 | ~3,966 | **~24,000 – 27,000 (~87%)** |
| **ChatGPT** (GPT-4o / o3 / GPT-5) | Extracts text + renders pages as images for vision | ~15,000 – 22,000 | ~3,966 | **~11,000 – 18,000 (~75–82%)** |
| **Gemini** (Default / Med res) | Renders all 17 pages natively (~560 tokens/page) | ~9,520 | ~3,966 | **~5,554 (~58%)** |
| **Gemini** (Low res / Older 2.5) | Renders all 17 pages at low res (~258–280 tokens/page) | ~4,386 – 4,760 | ~3,966 | **~420 – 794 (~10–17%)** |
| **Text-only tools / Local LLMs** | Strips images and reads only the raw text layer | ~3,700 – 3,900 | ~3,966 | ~0 tokens |

---

## 📁 Project Structure

```text
md-converter/
├── .streamlit/
│   └── config.toml         # Streamlit settings (50 MB upload limit & custom dark theme)
├── converter.py            # Core conversion pipeline (PDF & Image OCR + post-processing)
├── streamlit_app.py        # Streamlit web application interface
├── requirements.txt        # Python dependencies
└── README.md               # Project documentation
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10 or higher
- *(Optional)* [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) if preferred as an alternate OCR engine for scanned PDFs.

### 1. Clone the Repository

```bash
git clone https://github.com/shrithisside/md-converter.git
cd md-converter
```

### 2. Set Up a Virtual Environment

```bash
# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate

# Windows (Command Prompt / PowerShell)
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 🖥️ Usage

### Live Demo

Try the application directly without installing anything locally:
👉 **[https://md-converter-shrithisside.streamlit.app/](https://md-converter-shrithisside.streamlit.app/)**

### Run Locally

Launch the Streamlit app locally:

```bash
streamlit run streamlit_app.py
```

The app will open automatically in your browser at `http://localhost:8501`.

1. Upload any `.pdf` document or image (`.png`, `.jpg`, `.jpeg`, `.webp`, `.bmp`, `.tiff`) up to 50 MB.
2. Review character count, estimated tokens, and conversion preview.
3. Switch between **Markdown** (raw code view with one-click copy) and **Preview** (rendered HTML view).
4. Click **Download .md** to save your clean output.

### Use as a Python Module

You can also use the conversion pipeline directly in your own Python scripts:

```python
from converter import convert, convert_image

# 1. Convert a PDF to clean Markdown
pdf_markdown = convert("path/to/document.pdf")

# 2. Convert an image or screenshot (OCR) to clean Markdown
image_markdown = convert_image("path/to/screenshot.png")

# Save to disk or pass directly to your LLM prompt
with open("output.md", "w", encoding="utf-8") as f:
    f.write(pdf_markdown)
```

---

## ⚙️ Configuration

- **Upload Size Limit**: Configured in `.streamlit/config.toml` (`maxUploadSize = 50`). Increase or decrease based on your deployment environment.
- **First Page Header Retention**: In `converter.py`, toggle `KEEP_FIRST_PAGE_HEADER = True` if your documents contain metadata (title blocks, author details) on the first page that might otherwise match repeated header criteria.

---

## 🧰 Built With

- [Streamlit](https://streamlit.io/) - Interactive web app framework
- [PyMuPDF](https://github.com/pymupdf/PyMuPDF) & [PyMuPDF4LLM](https://github.com/pymupdf/PyMuPDF4LLM) - PDF layout parsing and Markdown extraction
- [RapidOCR](https://github.com/RapidAI/RapidOCR) & [ONNX Runtime](https://onnxruntime.ai/) - Fast, high-accuracy OCR for images and scans
- [Pillow](https://python-pillow.org/) - Image handling and EXIF orientation normalization

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE) (or your preferred repository license).
