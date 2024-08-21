#/usr/local/bin/python3.12
from __future__ import annotations

import fitz  # PyMuPDF


def has_indent(line_rect, threshold=20):
    return line_rect[0] > threshold


def remove_whitespace(s: str):
    return (s.replace(" :", ":").
            replace(" ?", "?").
            replace(" !", "!").
            replace(" )", ")").
            replace(" ,", ",").
            replace(" .", ".").
            replace("( ", "(").
            replace("  ", " "))


def check_line(line: dict) -> tuple[bool, bool, bool]:
    first_span = line["spans"][0] if "spans" in line and len(line["spans"]) > 0 else None

    line_indent = False
    line_upper = False
    line_numeric = False

    if first_span:
        if has_indent(first_span["bbox"], 90):
            line_indent = True
        if first_span["text"].strip().isupper():
            line_upper = True
        if first_span["text"][0].isnumeric():
            line_numeric = True

    return line_indent, line_upper, line_numeric


def is_title_or_subtitle(size: float,
                         flags: int,
                         text: str,
                         spans_count: int,
                         same_line: bool,
                         line_indent: bool,
                         line_upper: bool,
                         line_numeric: bool):
    chapter_sizes = {14.0, 17.0}
    subchapter_size = 11.0
    subchapter_flags = {16, 20}

    # Проверяем, является ли текст заголовком или подзаголовком
    if ((size in chapter_sizes or (size == subchapter_size and flags in subchapter_flags)) and
        (
            text.strip().isupper() or
            size == 17.0 or
            # text == " " or
            text.strip() in {":", "?", "!", ",", ".", "... (", "!)"} or
            (len(text.strip()) > 0 and text.strip()[0].isnumeric())
        ) and
        is_complex_line(same_line, spans_count, line_indent) and
        is_upper_numeric(line_upper, line_numeric, size)
    ):
        return True
    return False


def is_complex_line(same_line: bool, spans_count: int, line_indent: bool):
    return (same_line and spans_count == 1) or not line_indent


def is_upper_numeric(line_upper: bool, line_numeric: bool, size: float):
    return line_upper or line_numeric or size == 17.0


def extract_chapters(pdf_path: str):
    doc = fitz.open(pdf_path)
    chapters = []

    current_title: str = ""
    current_level = None
    current_page = None
    old_origin: tuple = ()

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        blocks = page.get_text("dict")["blocks"]

        for block in blocks:
            if "lines" in block:
                for line in block["lines"]:

                    for span in line["spans"]:
                        text = span["text"]
                        size = span["size"]
                        flags = span["flags"]
                        origin = span["origin"]
                        spans_count = len(line['spans'])

                        if old_origin and int(origin[1]) != int(old_origin[1]):
                            same_line = False
                            old_origin = origin
                        else:
                            same_line = True

                        if is_title_or_subtitle(size, flags, text, spans_count, same_line, *check_line(line)):
                            if current_level is None:
                                current_level = 1 if size in {14, 17} else 2
                                current_page = page_num + 1

                            current_title += text.rstrip() + " "
                        else:
                            if current_title:
                                current_title = remove_whitespace(current_title)
                                chapters.append((current_level, current_title.strip(), current_page))
                                current_title = ""
                                current_level = None
                                current_page = None

    if current_title:
        chapters.append((current_level, current_title.strip(), current_page))

    return chapters


def create_toc_from_chapters(pdf_path: str, output_path: str):
    chapters: list[tuple[int | None, str, int | None]] = extract_chapters(pdf_path)

    toc_entries: list[tuple[int, str, int | None]] = []
    for level, title, page in chapters:
        toc_entries.append((1, title, page))

    create_toc(pdf_path, output_path, toc_entries)


def create_toc(pdf_path: str, output_path, toc_entries):
    doc = fitz.open(pdf_path)
    toc = []

    for level, title, page in toc_entries:
        toc.append([level, title, page])

    doc.set_toc(toc)
    doc.save(output_path)
    print(f"PDF with TOC saved as: {output_path}")


if __name__ == "__main__":
    # Пример использования
    pdf_path = "My_Story_Can_Beat_Up_Your_Story перевод.pdf"
    output_path = "My_Story_Can_Beat_Up_Your_Story_перевод_with_toc.pdf"

    create_toc_from_chapters(pdf_path, output_path)
