"""PDF parsing service for extracting text from PDF files."""

from io import BytesIO
import PyPDF2
from typing import Optional

class PDFParserService:
    """Service for parsing PDF files and extracting text content."""

    @staticmethod
    def extract_text(file_bytes: bytes) -> Optional[str]:
        """
        Extract text from a PDF file.
        
        Args:
            file_bytes: Raw bytes of the PDF file
            
        Returns:
            Extracted text as a string, or None if extraction fails
        """
        try:
            # Create a BytesIO object from the file bytes
            pdf_file = BytesIO(file_bytes)
            
            # Create a PDF reader object
            reader = PyPDF2.PdfReader(pdf_file)
            
            # Extract text from all pages
            text = []
            for page in reader.pages:
                text.append(page.extract_text())
            
            return "\n\n".join(text)
        except Exception as e:
            print(f"Error extracting text from PDF: {str(e)}")
            return None
