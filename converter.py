"""PDF -> clean Markdown.

Runs pymupdf4llm, then repairs the things it gets wrong on many real-world PDFs:
  * repeated page headers / footers
  * OCR "picture text" comments and stray HTML tags
  * code blocks (flattened to one line and wrapped in <mark>)
  * inline code (backticks)
  * tables split across a page break
"""
import os
import re
import tempfile

import pymupdf
import pymupdf4llm

# Set to True to keep the first page's header block (title/student table, etc.).
KEEP_FIRST_PAGE_HEADER = False

MONO_HINTS = ("consol", "courier", "mono", "menlo", "fira code", "source code")


# ---------------------------------------------------------------- extraction
def _call_to_markdown(path, **opts):
    """Call pymupdf4llm.to_markdown, dropping options this version rejects."""
    opts = dict(opts)
    while True:
        try:
            return pymupdf4llm.to_markdown(path, **opts)
        except TypeError as exc:
            bad = next((k for k in list(opts) if k in str(exc)), None)
            if bad is None:
                raise
            opts.pop(bad)


def _pages_text(path, use_ocr, force_ocr=False):
    result = _call_to_markdown(
        path, page_chunks=True, use_ocr=use_ocr, force_ocr=force_ocr,
        header=True, footer=True,
    )
    if isinstance(result, str):  # very old versions ignore page_chunks
        return [result]
    return [(chunk.get("text") if isinstance(chunk, dict) else str(chunk)) or "" for chunk in result]


# ------------------------------------------------- repeated header / footer
def _units(text):
    """Split into units: a whole table, or a single non-empty line."""
    units, table = [], []
    for line in text.split("\n"):
        if line.lstrip().startswith("|"):
            table.append(line)
            continue
        if table:
            units.append("\n".join(table))
            table = []
        if line.strip():
            units.append(line)
    if table:
        units.append("\n".join(table))
    return units


def _key(unit):
    flat = re.sub(r"\W+", " ", unit).strip().lower()
    return re.sub(r"\d+", "#", flat)


def _drop_repeated(pages):
    if len(pages) < 3:
        return pages
    per_page = [_units(p) for p in pages]
    seen = {}
    for units in per_page:
        for k in {_key(u) for u in units}:
            seen[k] = seen.get(k, 0) + 1
    threshold = max(3, -(-len(pages) // 2))  # at least half the pages
    repeated = {k for k, n in seen.items() if n >= threshold and len(k) >= 6}
    out = []
    for i, units in enumerate(per_page):
        keep_all = KEEP_FIRST_PAGE_HEADER and i == 0
        out.append("\n\n".join(u for u in units if keep_all or _key(u) not in repeated))
    return out


# ------------------------------------------------------------- noise cleanup
def _clean_noise(md):
    def picture(match):
        body = match.group(1).replace("<br>", "\n").strip()
        first = body.split("\n")[0].strip()
        # Keep diagrams that are really text flows (a -> b -> c); drop logos.
        return f"\n\n{first}\n\n" if "→" in first else "\n\n"

    md = re.sub(
        r"<!-- Start of picture text -->(.*?)<!-- End of picture text -->",
        picture, md, flags=re.S,
    )
    md = re.sub(r"</?u>", "", md)
    md = re.sub(r"~~[^~\n]{0,12}~~", "", md)  # OCR junk like ~~(EEE~~
    # Headings: drop the **bold** wrapper pymupdf4llm adds.
    md = re.sub(
        r"^(#{1,6}\s+)(.*)$",
        lambda m: m.group(1) + m.group(2).replace("**", "").strip(),
        md, flags=re.M,
    )
    return md


# ------------------------------------------------- code / inline-code (PDF)
def _is_mono(font):
    f = font.lower()
    return any(h in f for h in MONO_HINTS)


def _code_from_pdf(path):
    """Return (code_blocks, inline_code_strings) based on monospace fonts."""
    blocks, inline = [], set()
    with pymupdf.open(path) as doc:
        for page in doc:
            for b in page.get_text("dict")["blocks"]:
                lines = b.get("lines", [])
                if not lines:
                    continue
                mono_chars = total_chars = 0
                for line in lines:
                    for s in line["spans"]:
                        n = len(s["text"].replace(" ", "").replace("\u00a0", ""))
                        total_chars += n
                        if _is_mono(s["font"]):
                            mono_chars += n
                if total_chars == 0 or mono_chars == 0:
                    continue
                if mono_chars / total_chars >= 0.9:
                    text_lines = ["".join(s["text"] for s in l["spans"]).rstrip() for l in lines]
                    while text_lines and not text_lines[-1].strip():
                        text_lines.pop()
                    while text_lines and not text_lines[0].strip():
                        text_lines.pop(0)
                    if text_lines:
                        blocks.append(text_lines)
                else:
                    for line in lines:
                        for s in line["spans"]:
                            t = s["text"].strip()
                            if _is_mono(s["font"]) and t:
                                inline.add(t)
    return blocks, inline


def _norm(s):
    return re.sub(r"[^A-Za-z0-9]", "", s)


def _guess_lang(lines):
    first = next((l.strip() for l in lines if l.strip()), "")
    joined = "\n".join(lines)
    if re.match(r"(?i)select\s", first):
        return "sql"
    if first.startswith("{") or first.startswith("["):
        return "json"
    if re.search(r"\b(const|let|var|function)\b|=>|server\.", joined):
        return "javascript"
    if re.search(r"^(aws|curl|git|docker|sudo|pip|npm)\b", joined, re.M) or first.startswith("#"):
        return "bash"
    return ""


MARK_LINE = re.compile(r"^\s*(?:[-*]\s+)?<mark>(.*)</mark>\s*$")


def _rebuild_code_blocks(md, code_blocks):
    lines = md.split("\n")
    pos = 0
    for block in code_blocks:
        target = _norm("".join(block))
        if len(target) < 3:
            continue
        i = pos
        replaced = False
        while i < len(lines):
            m = MARK_LINE.match(lines[i])
            if not m or not _norm(m.group(1)) or not target.startswith(_norm(m.group(1))):
                i += 1
                continue
            acc, j, used = "", i, []
            while j < len(lines):
                if not lines[j].strip():
                    j += 1
                    continue
                mj = MARK_LINE.match(lines[j])
                if not mj:
                    break
                acc += _norm(mj.group(1))
                used.append(j)
                j += 1
                if acc == target or not target.startswith(acc):
                    break
            if acc == target:
                fence = ["```" + _guess_lang(block), *block, "```"]
                lines[used[0]:used[-1] + 1] = fence
                pos = used[0] + len(fence)
                replaced = True
                break
            i += 1
        if not replaced:
            continue
    # Anything still wrapped in <mark> is code we could not rebuild: unwrap it.
    text = "\n".join(lines)
    return re.sub(r"</?mark>", "", text)


def _looks_like_code(s):
    if len(s) < 3 or not re.search(r"[A-Za-z]", s) and not re.search(r"[/_.\-*<>(){}=:]", s):
        return False
    if re.fullmatch(r"\d+", s):
        return False
    return bool(re.search(r"[/_.\-*<>(){}=:@]", s)) or bool(re.search(r"[a-z][A-Z]", s))


def _add_inline_code(md, inline):
    candidates = sorted((s for s in inline if _looks_like_code(s)), key=len, reverse=True)
    if not candidates:
        return md
    alt = "|".join(re.escape(c) for c in candidates)
    prose = re.compile("(?<![\\w`])(" + alt + ")(?![\\w`])")
    # Inside table cells pymupdf4llm often glues code to neighbouring words
    # ("dedicated/healthendpoint"), so match anywhere and add the spaces back.
    cell = re.compile("(" + alt + ")")

    def spaced(m):
        line, a, b = m.string, m.start(), m.end()
        pre = " " if a > 0 and line[a - 1].isalnum() else ""
        post = " " if b < len(line) and line[b].isalnum() else ""
        return f"{pre}`{m.group(1)}`{post}"

    out, in_fence = [], False
    for line in md.split("\n"):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            out.append(line)
        elif in_fence or line.lstrip().startswith("#"):
            out.append(line)
        else:
            parts = re.split(r"(`[^`]*`)", line)  # leave existing backticks alone
            is_table = line.lstrip().startswith("|")
            rx = cell if is_table else prose
            rebuilt = []
            for p in parts:
                if p.startswith("`"):
                    rebuilt.append(p)
                elif is_table:
                    rebuilt.append(rx.sub(lambda m, p=p: _spaced(m, p), p))
                else:
                    rebuilt.append(rx.sub(r"`\1`", p))
            out.append("".join(rebuilt))
    return "\n".join(out)


def _spaced(m, text):
    a, b = m.start(), m.end()
    pre = " " if a > 0 and text[a - 1].isalnum() else ""
    post = " " if b < len(text) and (text[b].isalnum() or text[b] == "(") else ""
    return f"{pre}`{m.group(1)}`{post}"


def _fix_bold_spacing(md):
    """'word**bold**word' -> 'word **bold** word'; '**bold** .' -> '**bold**.'"""
    def bold(m):
        line, a, b = m.string, m.start(), m.end()
        pre = " " if a > 0 and line[a - 1].isalnum() else ""
        post = " " if b < len(line) and line[b].isalnum() else ""
        return f"{pre}**{m.group(1).strip()}**{post}"

    out, in_fence = [], False
    for line in md.split("\n"):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            out.append(line)
        elif in_fence:
            out.append(line)
        else:
            line = re.sub(r"\*\*([^*\n]+?)\*\*", bold, line)
            line = re.sub(r"(\*\*) +([,.;:!?])", r"\1\2", line)
            out.append(line)
    return "\n".join(out)


def _tighten_lists(md):
    return re.sub(r"(^(?:[-*] |\d+\. ).*)\n\n(?=(?:[-*] |\d+\. ))", r"\1\n", md, flags=re.M)


# ----------------------------------------------------------------- tables
def _merge_split_tables(md):
    """Merge a table continued after a page break (same header row repeated)."""
    lines = md.split("\n")
    out, i = [], 0
    last_table_header = None
    while i < len(lines):
        line = lines[i]
        is_row = line.lstrip().startswith("|")
        if is_row:
            # start of a table: header + separator
            if (
                i + 1 < len(lines)
                and re.match(r"^\s*\|[\s:\-|]+\|\s*$", lines[i + 1])
            ):
                header = line.strip()
                if header == last_table_header and out:
                    # drop trailing blank lines, skip header + separator
                    while out and not out[-1].strip():
                        out.pop()
                    i += 2
                    continue
                last_table_header = header
        elif line.strip():
            last_table_header = None
        out.append(line)
        i += 1
    return "\n".join(out)


# ------------------------------------------------------------------- main
def convert(path):
    pages = _pages_text(path, use_ocr=False)
    if len(re.sub(r"\s", "", "".join(pages))) < 100:
        # Probably a scanned PDF: retry with OCR (needs Tesseract installed).
        pages = _pages_text(path, use_ocr=True)

    md = "\n\n".join(_drop_repeated(pages))
    md = _clean_noise(md)

    code_blocks, inline = _code_from_pdf(path)
    md = _rebuild_code_blocks(md, code_blocks)
    md = _add_inline_code(md, inline)
    md = _merge_split_tables(md)
    md = _fix_bold_spacing(md)
    md = _tighten_lists(md)

    md = re.sub(r"[ \t]+\n", "\n", md)          # trailing spaces
    md = re.sub(r"\n{3,}", "\n\n", md)          # collapse blank lines
    return md.strip() + "\n"


def convert_image(path):
    """Image (png/jpg/webp/bmp/tiff...) -> Markdown using OCR.

    The image is wrapped in a one-page PDF so the same pymupdf4llm pipeline
    (layout detection + OCR) is used. Needs `rapidocr` (pip only) or Tesseract.
    """
    from PIL import Image, ImageOps  # Pillow ships with streamlit / rapidocr

    with tempfile.TemporaryDirectory() as tmp:
        # Normalise any format (webp, bmp, tiff, gif, phone photos...) to PNG.
        png_path = os.path.join(tmp, "image.png")
        with Image.open(path) as im:
            im = ImageOps.exif_transpose(im).convert("RGB")
            im.thumbnail((3000, 3000))  # cap very large photos to save memory
            im.save(png_path, "PNG")

        with pymupdf.open(png_path) as img:
            pdf_bytes = img.convert_to_pdf()
        pdf_path = os.path.join(tmp, "image.pdf")
        with open(pdf_path, "wb") as f:
            f.write(pdf_bytes)
        pages = _pages_text(pdf_path, use_ocr=True, force_ocr=True)

    md = "\n\n".join(pages)
    md = _clean_noise(md)
    md = _merge_split_tables(md)
    md = _fix_bold_spacing(md)
    md = _tighten_lists(md)
    md = re.sub(r"[ \t]+\n", "\n", md)
    md = re.sub(r"\n{3,}", "\n\n", md)
    return md.strip() + "\n"