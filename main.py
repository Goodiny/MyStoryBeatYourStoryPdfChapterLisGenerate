#/usr/local/bin/python3.12

import fitz  # PyMuPDF


def has_indent(line_rect, threshold=20):
    x0 = line_rect[0]
    return x0 > threshold


def is_title_or_subtitle(size, flags, text):
    chapter_sizes = {14.0, 17.0}
    subchapter_size = 11.0
    subchapter_flags = {16, 20}

    # Проверяем, является ли текст заголовком или подзаголовком
    if ((size in chapter_sizes or (size == subchapter_size and flags in subchapter_flags)) and
            (text.strip().isupper() or size == 17.0 or text == " " or text.strip() in {":", "?", "!", ",", ".", "... (",
                                                                                       "!)"} or
             (len(text.strip()) > 0 and text.strip()[0].isnumeric()))):
        return True
    return False


def extract_chapters(pdf_path):
    doc = fitz.open(pdf_path)
    chapters = []

    current_title = ""
    current_level = None
    current_page = None
    old_origin = ()

    line_indent = False
    line_upper = False
    line_numeric = False

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        blocks = page.get_text("dict")["blocks"]

        for block in blocks:
            if "lines" in block:
                for line in block["lines"]:
                    first_span = line["spans"][0] if "spans" in line and len(line["spans"]) > 0 else None
                    if first_span:
                        if has_indent(first_span["bbox"], 90):
                            line_indent = True
                        else:
                            line_indent = False
                        if first_span["text"].strip().isupper():
                            line_upper = True
                        else:
                            line_upper = False
                        if first_span["text"][0].isnumeric():
                            line_numeric = True
                        else:
                            line_numeric = False

                    for span in line["spans"]:
                        text = span["text"]
                        size = span["size"]
                        flags = span["flags"]
                        origin = span["origin"]

                        if old_origin and int(origin[1]) != int(old_origin[1]):
                            same_line = False
                            old_origin = origin
                        else:
                            same_line = True

                        # if page_num + 1 == 7:
                        #     if is_title_or_subtitle(size, flags, text):
                        #         print(line)
                        #     print(is_title_or_subtitle(size, flags, text))
                        #     print(line_indent, line_upper, line_numeric)
                        #     print(text)

                        if (is_title_or_subtitle(size, flags, text) and (
                                (same_line and len(line["spans"]) == 1) or not line_indent) and
                                (line_upper or line_numeric or size == 17.0)):
                            if current_level is None:
                                current_level = 1 if size in {14, 17} else 2
                                current_page = page_num + 1

                            current_title += text.rstrip() + " "
                        else:
                            if current_title:
                                current_title = (current_title.replace(" :", ":").
                                                 replace(" ?", "?").
                                                 replace(" !", "!").
                                                 replace(" )", ")").
                                                 replace(" ,", ",").
                                                 replace(" .", ".").
                                                 replace("( ", "(").
                                                 replace("  ", " "))
                                chapters.append((current_level, current_title.strip(), current_page))
                                print((current_level, current_title.strip(), current_page))
                                current_title = ""
                                current_level = None
                                current_page = None
                        # if page_num + 1 in {4, 9, 7, 87}:
                        #     print(span)

    if current_title:
        chapters.append((current_level, current_title.strip(), current_page))
        print((current_level, current_title.strip(), current_page))

    return chapters


def create_toc_from_chapters(pdf_path, output_path):
    chapters = extract_chapters(pdf_path)

    toc_entries = []
    for level, title, page in chapters:
        toc_entries.append((1, title, page))

    create_toc(pdf_path, output_path, toc_entries)


def create_toc(pdf_path, output_path, toc_entries):
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
