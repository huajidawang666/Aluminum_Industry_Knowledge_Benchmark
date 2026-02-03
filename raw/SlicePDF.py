"""Split a PDF in the `materials/` directory into per-page PDFs.

Usage (from repo root):
    python -m raw.SlicePDF <pdf_filename_or_path>

Examples:
    python -m raw.SlicePDF "铝冶炼工艺 (王克勤主编, 王克勤主编, 王克勤) (Z-Library).pdf"
    python -m raw.SlicePDF materials/sample.pdf
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional

from pypdf import PdfReader, PdfWriter


def split_pdf(pdf_path: Path, materials_dir: Optional[Path] = None, from_z_lib: bool = False) -> Path:
    """Split a PDF into single-page PDFs inside a folder named after the file.

    Args:
        pdf_path: Path to the PDF file. Can be absolute or relative. If relative,
            it is resolved against the provided ``materials_dir`` or the default
            ``materials`` folder at the repo root.
        materials_dir: Base directory containing PDF materials. If omitted, the
            repo's ``materials`` folder is used.

    Returns:
        Path to the output folder containing the per-page PDFs.

    Raises:
        FileNotFoundError: If the PDF file does not exist.
        ValueError: If the path does not point to a PDF file.
    """
    
    base_dir = materials_dir or Path(__file__).resolve().parent.parent
    resolved_pdf = (base_dir / pdf_path).resolve() if not pdf_path.is_absolute() else pdf_path
     
    if not resolved_pdf.exists():
        raise FileNotFoundError(f"PDF not found: {resolved_pdf}")
    if resolved_pdf.suffix.lower() != ".pdf":
        raise ValueError(f"Expected a PDF file, got: {resolved_pdf.suffix}")
    output_dir = resolved_pdf.parent.parent / "processed" / resolved_pdf.stem
    output_dir.mkdir(parents=True, exist_ok=True)
    reader = PdfReader(resolved_pdf)
    idx = 0
    
    fullpage = PdfWriter()
    about_to_remove = False
    for page in reader.pages:
        if from_z_lib:
            if page.mediabox.width > page.mediabox.height:
                about_to_remove = True
                continue
            if about_to_remove and page.mediabox.width <= page.mediabox.height:
                fullpage.remove_page(idx-1)
                idx -= 1
                about_to_remove = False
        idx += 1
        writer = PdfWriter()
        writer.add_page(page)
        fullpage.add_page(page)
        out_path = output_dir / f"page_{idx:03d}.pdf"
        with out_path.open("wb") as f:
            writer.write(f)
    # for page in reader.pages:
    #     if page.mediabox.width > page.mediabox.height:
    #         continue
    #     idx += 1
    #     writer = PdfWriter()
    #     writer.add_page(page)
    #     fullpage.add_page(page)
    #     out_path = output_dir / f"page_{idx:03d}.pdf"
    #     with out_path.open("wb") as f:
    #         writer.write(f)
    fullpage_path = output_dir.parent / f"{resolved_pdf.stem}_fullpages.pdf"
    with fullpage_path.open("wb") as f:
        fullpage.write(f)
    return output_dir


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Split a PDF into single-page PDFs in a folder named after the file.")
    parser.add_argument("--dir", default="./materials/raw/", help="Path to the PDF inside materials/ (can be absolute).")
    parser.add_argument("--z-library", type=bool, default=False, help="Remove redundant scans from Z-Library PDFs.")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    pdf_path = Path(args.dir)
    if pdf_path.is_dir():
        for pdf_file in pdf_path.glob("*.pdf"):
            print(f"Processing {pdf_file.name}...")
            try:
                output_dir = split_pdf(pdf_file, from_z_lib=args.z_library)
                print(f"  -> Split complete. Pages saved to: {output_dir}")
            except (FileNotFoundError, ValueError) as e:
                print(f"  -> Error processing {pdf_file.name}: {e}")
        return
    else:
        try:
            output_dir = split_pdf(pdf_path, from_z_lib=args.z_library)
            print(f"Split complete. Pages saved to: {output_dir}")
        except (FileNotFoundError, ValueError) as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()
