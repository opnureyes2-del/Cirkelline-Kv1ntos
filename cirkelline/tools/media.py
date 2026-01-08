"""
Document Processing Tools for Cirkelline
Handles DOCX conversion guidance and structured text extraction
"""

from agno.tools import Toolkit
import os
from typing import Optional


class DocumentProcessingTools(Toolkit):
    """Tools for document file processing - DOCX conversion guidance and text extraction"""

    def __init__(self):
        super().__init__(
            name="document_processing",
            instructions="""
            Use these tools for processing document files uploaded by the user.
            Use convert_docx_to_pdf when user uploads DOCX files that need conversion.
            Use extract_structured_text for text-based files (TXT, MD, HTML, XML).
            """,
            add_instructions=True
        )
        self.register(self.convert_docx_to_pdf)
        self.register(self.extract_structured_text)

    def convert_docx_to_pdf(self, docx_path: str) -> str:
        """
        Provide guidance for converting DOCX files to PDF for Gemini processing.

        Args:
            docx_path: Path to the DOCX file

        Returns:
            Guidance message for DOCX conversion
        """
        try:
            return (
                f"DOCX files are not natively supported by Gemini. "
                f"Please convert {docx_path} to PDF format first. "
                f"You can use:\n"
                f"- Online converters (e.g., Smallpdf, CloudConvert)\n"
                f"- Desktop software (Microsoft Word, LibreOffice)\n"
                f"- Command-line tools (libreoffice --headless --convert-to pdf)\n\n"
                f"Once converted to PDF, upload the PDF file for full analysis including "
                f"layout, charts, tables, and diagrams."
            )
        except Exception as e:
            return f"Error with DOCX file: {str(e)}"

    def extract_structured_text(self, file_path: str, preserve_formatting: bool = True) -> str:
        """
        Extract text from text-based document files (TXT, MD, HTML, XML).

        Args:
            file_path: Path to the text document
            preserve_formatting: Whether to attempt preserving structure (limited for non-PDF)

        Returns:
            Extracted text content with formatting note
        """
        try:
            # For text-based files, read directly
            if file_path.lower().endswith(('.txt', '.md', '.html', '.xml')):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                if preserve_formatting:
                    return (
                        f"Note: Text extracted from {file_path}. "
                        f"Original formatting may not be fully preserved.\n\n{content}"
                    )
                return content

            # For other files, inform user to use PDF
            return (
                f"For best results with document processing, please convert "
                f"{file_path} to PDF format. Gemini has full native support for PDFs "
                f"including layout, charts, tables, and diagrams."
            )

        except Exception as e:
            return f"Error extracting text: {str(e)}"
