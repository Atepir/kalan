"""
PDF export functionality for research papers.

Converts paper content to well-formatted PDF documents.
"""

from pathlib import Path
from datetime import datetime
from typing import Any

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    PageBreak,
    Table,
    TableStyle,
)
from reportlab.lib import colors

from src.utils.logging import get_logger

logger = get_logger(__name__)


class PaperPDFExporter:
    """Export research papers to PDF format."""

    def __init__(self):
        """Initialize PDF exporter."""
        self.logger = get_logger(__name__)

    def export_paper(
        self,
        paper_id: str,
        title: str,
        authors: list[str],
        abstract: str,
        introduction: str,
        methodology: str,
        results: str,
        discussion: str,
        conclusion: str,
        references: list[str],
        keywords: list[str],
        timestamp: datetime,
        output_path: Path | str,
    ) -> Path:
        """
        Export paper to PDF.

        Args:
            paper_id: Paper identifier
            title: Paper title
            authors: List of author names
            abstract: Abstract text
            introduction: Introduction section
            methodology: Methodology section
            results: Results section
            discussion: Discussion section
            conclusion: Conclusion section
            references: List of references
            keywords: List of keywords
            timestamp: Publication timestamp
            output_path: Output file path

        Returns:
            Path to generated PDF
        """
        output_path = Path(output_path)
        
        self.logger.info(
            "exporting_paper_to_pdf",
            paper_id=paper_id,
            output_path=str(output_path),
        )

        try:
            # Create PDF document
            doc = SimpleDocTemplate(
                str(output_path),
                pagesize=letter,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18,
            )

            # Container for PDF elements
            story = []

            # Create styles
            styles = getSampleStyleSheet()
            
            # Custom styles
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=18,
                textColor=colors.HexColor('#1a1a1a'),
                spaceAfter=12,
                alignment=TA_CENTER,
                fontName='Helvetica-Bold',
            )
            
            author_style = ParagraphStyle(
                'AuthorStyle',
                parent=styles['Normal'],
                fontSize=12,
                textColor=colors.HexColor('#333333'),
                spaceAfter=6,
                alignment=TA_CENTER,
                fontName='Helvetica',
            )
            
            metadata_style = ParagraphStyle(
                'MetadataStyle',
                parent=styles['Normal'],
                fontSize=10,
                textColor=colors.HexColor('#666666'),
                spaceAfter=20,
                alignment=TA_CENTER,
                fontName='Helvetica',
            )
            
            section_title_style = ParagraphStyle(
                'SectionTitle',
                parent=styles['Heading2'],
                fontSize=14,
                textColor=colors.HexColor('#1a1a1a'),
                spaceAfter=12,
                spaceBefore=18,
                fontName='Helvetica-Bold',
            )
            
            body_style = ParagraphStyle(
                'BodyText',
                parent=styles['BodyText'],
                fontSize=11,
                textColor=colors.HexColor('#1a1a1a'),
                spaceAfter=12,
                alignment=TA_JUSTIFY,
                fontName='Helvetica',
                leading=14,
            )

            # Clean title (remove any markdown artifacts)
            clean_title = title.replace('**', '').replace('##', '').strip()
            
            # Add title
            story.append(Paragraph(clean_title, title_style))
            story.append(Spacer(1, 0.2 * inch))

            # Add authors
            authors_text = ", ".join(authors)
            story.append(Paragraph(f"<b>Authors:</b> {authors_text}", author_style))

            # Add metadata
            date_str = timestamp.strftime("%B %d, %Y")
            keywords_text = ", ".join(keywords)
            story.append(Paragraph(f"<b>Date:</b> {date_str}", metadata_style))
            story.append(Paragraph(f"<b>Keywords:</b> {keywords_text}", metadata_style))
            story.append(Spacer(1, 0.3 * inch))

            # Add horizontal line
            story.append(Spacer(1, 0.1 * inch))

            # Add Abstract
            story.append(Paragraph("<b>Abstract</b>", section_title_style))
            abstract_cleaned = self._clean_text(abstract)
            for para in abstract_cleaned.split('\n\n'):
                if para.strip():
                    story.append(Paragraph(para.strip(), body_style))
            story.append(Spacer(1, 0.2 * inch))

            # Add Introduction
            story.append(Paragraph("<b>Introduction</b>", section_title_style))
            intro_cleaned = self._clean_text(introduction)
            for para in intro_cleaned.split('\n\n'):
                if para.strip():
                    story.append(Paragraph(para.strip(), body_style))
            story.append(Spacer(1, 0.2 * inch))

            # Add Methodology
            story.append(Paragraph("<b>Methodology</b>", section_title_style))
            method_cleaned = self._clean_text(methodology)
            for para in method_cleaned.split('\n\n'):
                if para.strip():
                    story.append(Paragraph(para.strip(), body_style))
            story.append(Spacer(1, 0.2 * inch))

            # Add Results
            story.append(Paragraph("<b>Results</b>", section_title_style))
            results_cleaned = self._clean_text(results)
            for para in results_cleaned.split('\n\n'):
                if para.strip():
                    story.append(Paragraph(para.strip(), body_style))
            story.append(Spacer(1, 0.2 * inch))

            # Add Discussion
            story.append(Paragraph("<b>Discussion</b>", section_title_style))
            discussion_cleaned = self._clean_text(discussion)
            for para in discussion_cleaned.split('\n\n'):
                if para.strip():
                    story.append(Paragraph(para.strip(), body_style))
            story.append(Spacer(1, 0.2 * inch))

            # Add Conclusion
            story.append(Paragraph("<b>Conclusion</b>", section_title_style))
            conclusion_cleaned = self._clean_text(conclusion)
            for para in conclusion_cleaned.split('\n\n'):
                if para.strip():
                    story.append(Paragraph(para.strip(), body_style))
            story.append(Spacer(1, 0.3 * inch))

            # Add References
            if references:
                story.append(Paragraph("<b>References</b>", section_title_style))
                for i, ref in enumerate(references, 1):
                    ref_cleaned = self._clean_text(ref)
                    story.append(Paragraph(f"{i}. {ref_cleaned}", body_style))

            # Build PDF
            doc.build(story)

            self.logger.info(
                "paper_exported_to_pdf",
                paper_id=paper_id,
                output_path=str(output_path),
                file_size=output_path.stat().st_size,
            )

            return output_path

        except Exception as e:
            self.logger.error(
                "pdf_export_failed",
                paper_id=paper_id,
                error=str(e),
            )
            raise

    def _clean_text(self, text: str) -> str:
        """
        Clean text for PDF rendering.
        
        Removes markdown formatting and handles special characters.
        
        Args:
            text: Input text
            
        Returns:
            Cleaned text
        """
        # Remove markdown headers
        text = text.replace('###', '').replace('##', '').replace('#', '')
        
        # Remove bold/italic markdown
        text = text.replace('**', '').replace('__', '')
        text = text.replace('*', '').replace('_', '')
        
        # Handle special characters that might cause issues
        text = text.replace('&', '&amp;')
        text = text.replace('<', '&lt;')
        text = text.replace('>', '&gt;')
        
        # Clean up extra whitespace
        lines = [line.strip() for line in text.split('\n')]
        text = '\n'.join(lines)
        
        return text.strip()


# Convenience function
def export_paper_to_pdf(
    paper_id: str,
    title: str,
    authors: list[str],
    abstract: str,
    introduction: str,
    methodology: str,
    results: str,
    discussion: str,
    conclusion: str,
    references: list[str],
    keywords: list[str],
    timestamp: datetime,
    output_path: Path | str,
) -> Path:
    """
    Export a research paper to PDF format.

    Args:
        paper_id: Paper identifier
        title: Paper title
        authors: List of author names
        abstract: Abstract text
        introduction: Introduction section
        methodology: Methodology section
        results: Results section
        discussion: Discussion section
        conclusion: Conclusion section
        references: List of references
        keywords: List of keywords
        timestamp: Publication timestamp
        output_path: Output file path

    Returns:
        Path to generated PDF
    """
    exporter = PaperPDFExporter()
    return exporter.export_paper(
        paper_id=paper_id,
        title=title,
        authors=authors,
        abstract=abstract,
        introduction=introduction,
        methodology=methodology,
        results=results,
        discussion=discussion,
        conclusion=conclusion,
        references=references,
        keywords=keywords,
        timestamp=timestamp,
        output_path=output_path,
    )
