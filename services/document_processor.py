"""
Document processor for detecting file types, converting DOCX to PDF, and extracting text.
"""
import os
import subprocess
import tempfile


class DocumentProcessor:
    """Process documents: detect type, extract text."""

    SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt"}

    @staticmethod
    def get_file_extension(filename: str) -> str:
        """Get the file extension from filename."""
        return os.path.splitext(filename)[1].lower()

    @staticmethod
    def is_supported(filename: str) -> bool:
        """Check if file type is supported."""
        ext = DocumentProcessor.get_file_extension(filename)
        return ext in DocumentProcessor.SUPPORTED_EXTENSIONS

    @staticmethod
    def convert_docx_to_pdf(docx_content: bytes) -> bytes:
        """Convert DOCX to PDF using LibreOffice headless."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            docx_path = os.path.join(tmp_dir, "document.docx")
            with open(docx_path, "wb") as f:
                f.write(docx_content)

            subprocess.run(
                [
                    "libreoffice",
                    "--headless",
                    "--convert-to", "pdf",
                    "--outdir", tmp_dir,
                    docx_path,
                ],
                check=True,
                timeout=120,
                capture_output=True,
            )

            pdf_path = os.path.join(tmp_dir, "document.pdf")
            with open(pdf_path, "rb") as f:
                return f.read()

    @staticmethod
    def extract_text_from_txt(file_content: bytes) -> str:
        """Extract text from TXT file."""
        try:
            return file_content.decode("utf-8")
        except UnicodeDecodeError:
            return file_content.decode("latin-1")

    @staticmethod
    def get_filename_from_url(url: str) -> str:
        """Extract filename from URL."""
        filename = url.split("/")[-1].split("?")[0]
        if not filename:
            filename = "document"
        return filename
