#!/usr/bin/env python3
"""center_pdf.py

Horizontally **and** vertically center visible content of each page while
avoiding accidental clipping. Works by examining all graphical objects
(text, lines, rects, curves, images).

Usage:
    uv run center_pdf.py

Dependencies:
    pip install pdfplumber PyPDF2
"""

import sys
from pathlib import Path
from typing import Iterable, Tuple, Union

import pdfplumber
from PyPDF2 import PdfReader, PdfWriter, Transformation


def _iter_objects(page) -> Iterable[dict]:
    """Yield every drawable object on *page* that has bbox keys x0, x1, y0, y1."""
    for attr in ("chars", "lines", "rects", "curves", "images"):
        # getattr의 세 번째 인자로 빈 리스트를 제공하여 해당 속성이 없을 때 오류 방지
        for obj in getattr(page, attr, []):
            if obj is not None and all(k in obj for k in ("x0", "x1", "y0", "y1")):
                yield obj


def _page_bbox(page) -> Union[Tuple[float, float, float, float], None]:
    """Return overall bbox (min_x, max_x, min_y, max_y) across all objects.
    If no objects, returns None.
    """
    xs0, xs1, ys0, ys1 = [], [], [], []
    for obj in _iter_objects(page):
        try:
            # 좌표값이 숫자가 아닐 경우를 대비한 오류 처리
            xs0.append(float(obj["x0"]))
            xs1.append(float(obj["x1"]))
            ys0.append(float(obj["y0"]))
            ys1.append(float(obj["y1"]))
        except (ValueError, TypeError):
            continue  # 변환할 수 없는 좌표는 건너뜁니다.
    if not xs0:
        return None
    return min(xs0), max(xs1), min(ys0), max(ys1)


def _clamped_shift(min_val, max_val, target_min, page_min, page_max, margin=0.0):
    """Clamp ideal shift so that final bbox stays within [page_min+margin,page_max-margin]."""
    ideal = target_min - min_val
    lower_bound = page_min + margin - min_val
    upper_bound = page_max - margin - max_val
    return max(lower_bound, min(ideal, upper_bound))


def _compute_shift(page):
    """Return (tx, ty) needed to center all content on *page* without clipping."""
    bbox = _page_bbox(page)
    if bbox is None:
        return 0.0, 0.0

    min_x, max_x, min_y, max_y = bbox
    content_w = max_x - min_x
    content_h = max_y - min_y

    page_w, page_h = float(page.width), float(page.height)

    target_left = (page_w - content_w) / 2
    target_bottom = (page_h - content_h) / 2

    tx = _clamped_shift(min_x, max_x, target_left, 0, page_w)
    ty = _clamped_shift(min_y, max_y, target_bottom, 0, page_h)

    return tx, ty


def center_pdf(input_path: Union[str, Path], output_path: Union[str, Path]) -> bool:
    """
    PDF 파일의 콘텐츠를 중앙 정렬합니다.

    Args:
        input_path (Union[str, Path]): 원본 PDF 파일 경로.
        output_path (Union[str, Path]): 저장할 PDF 파일 경로.

    Returns:
        bool: 성공 시 True, 실패 시 False.
    """
    try:
        # 입력 경로를 Path 객체로 변환하여 안정성 확보
        input_p = Path(input_path)
        output_p = Path(output_path)

        # 출력 폴더가 없으면 생성
        output_p.parent.mkdir(parents=True, exist_ok=True)

        reader = PdfReader(input_p)
        writer = PdfWriter()

        with pdfplumber.open(input_p) as pdf:
            # pdfplumber와 PyPDF2가 인식하는 페이지 수가 다를 경우를 대비
            num_pages = min(len(pdf.pages), len(reader.pages))

            for i in range(num_pages):
                pl_page = pdf.pages[i]
                pd_page = reader.pages[i]

                tx, ty = _compute_shift(pl_page)

                # 이동 거리가 미미한 경우는 변환을 적용하지 않음
                if abs(tx) > 0.5 or abs(ty) > 0.5:
                    transformation = Transformation().translate(tx=tx, ty=ty)
                    pd_page.add_transformation(transformation)

                writer.add_page(pd_page)

        with output_p.open("wb") as f:
            writer.write(f)

        print(f"성공적으로 변환되어 '{output_p}'에 저장되었습니다.")
        return True

    except Exception as e:
        # 모든 종류의 오류를 포괄적으로 처리
        print(f"'{input_path}' 파일 변환 중 오류 발생: {e}", file=sys.stderr)
        return False


if __name__ == "__main__":
    pdfs_path = "pdfs"  # PDF 파일이 있는 폴더 경로
    prefix = "centered_"  # 변환된 PDF 파일의 접두사

    pdfs_dir = Path(pdfs_path)
    if not pdfs_dir.is_dir():
        print(f"오류: '{pdfs_path}' 폴더를 찾을 수 없습니다.", file=sys.stderr)
        sys.exit(1)

    pdfs = list(pdfs_dir.glob("*.pdf"))
    if not pdfs:
        print(f"'{pdfs_path}' 폴더에 PDF 파일이 없습니다.", file=sys.stderr)
        sys.exit(1)

    print(f"총 {len(pdfs)}개의 PDF 파일을 변환합니다...")
    for pdf_path in pdfs:
        output_pdf = pdf_path.with_name(f"{prefix}{pdf_path.name}")
        center_pdf(pdf_path, output_pdf)
