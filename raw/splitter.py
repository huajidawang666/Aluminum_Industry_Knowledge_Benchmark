from langchain_text_splitters import MarkdownHeaderTextSplitter
from pathlib import Path
import argparse

def split_markdown_text(
    text: str,
) -> list[str]:
    """Split markdown text into chunks based on headers.

    Args:
        text: The markdown text to split.
        chunk_size: The maximum size of each chunk.
        chunk_overlap: The number of overlapping characters between chunks.
        headers: A list of tuples defining header prefixes and their levels.

    Returns:
        A list of text chunks.
    """
    
    headers_to_split_on = [
        ("#", "H1"),
        ("##", "H2"),
        ("###", "H3"),
    ]
    
    splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=headers_to_split_on,
    )
    return splitter.split_text(text)

def _parse_args():
    parser = argparse.ArgumentParser(
        description="Split a markdown file into chunks based on headers."
    )
    parser.add_argument(
        "markdown_file",
        type=Path,
        help="Path to the markdown file to split.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("./materials/split_markdown/"),
        help="Output file or path to store the split markdown chunks.",
    )
    return parser.parse_args()

def write_chunks_to_file(chunks: list[str], output_file: Path):
    output_file.parent.mkdir(parents=True, exist_ok=True)
    data_to_save = [
        {
            "content": doc.page_content,
            "metadata": doc.metadata
        }
        for doc in chunks
    ]
    with output_file.open("w", encoding="utf-8") as f:
        import json
        json.dump(data_to_save, f, ensure_ascii=False, indent=4)
        
        
def main():
    args = _parse_args()
    
    markdown_file = Path(args.markdown_file).read_text(encoding="utf-8")
    chunks = split_markdown_text(markdown_file)
    
    output_file = Path()
    if args.output.is_dir() or not args.output.suffix:
        output_file = args.output / f"{Path(args.markdown_file).stem}_chunks.json"
    else:
        output_file = args.output
        
    write_chunks_to_file(chunks, output_file)
        
    
if __name__ == "__main__":
    main()