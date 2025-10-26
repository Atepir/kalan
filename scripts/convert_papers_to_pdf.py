"""
Batch convert existing papers to PDF format.

This script converts all existing JSON papers to PDF.
"""

import asyncio
import json
from pathlib import Path
from datetime import datetime

from src.utils.pdf_export import export_paper_to_pdf
from src.utils.logging import get_logger

logger = get_logger(__name__)


async def convert_papers_to_pdf():
    """Convert all existing papers to PDF format."""
    
    print("=" * 80)
    print("Converting Existing Papers to PDF")
    print("=" * 80)
    
    papers_dir = Path("data/papers")
    
    if not papers_dir.exists():
        print("\n❌ Papers directory not found!")
        return False
    
    # Find all JSON paper files
    json_files = list(papers_dir.glob("*.json"))
    
    if not json_files:
        print("\n⚠️  No paper JSON files found!")
        return False
    
    print(f"\nFound {len(json_files)} papers to convert\n")
    
    converted = 0
    skipped = 0
    errors = 0
    
    for json_file in json_files:
        paper_id = json_file.stem
        pdf_file = papers_dir / f"{paper_id}.pdf"
        
        # Skip if PDF already exists
        if pdf_file.exists():
            print(f"⏭️  Skipping {paper_id} (PDF already exists)")
            skipped += 1
            continue
        
        try:
            # Load paper data
            with open(json_file, 'r', encoding='utf-8') as f:
                paper_data = json.load(f)
            
            # Convert timestamp
            timestamp_str = paper_data.get('timestamp', datetime.utcnow().isoformat())
            if isinstance(timestamp_str, str):
                # Try parsing ISO format
                try:
                    timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                except:
                    timestamp = datetime.utcnow()
            else:
                timestamp = datetime.utcnow()
            
            # Export to PDF
            print(f"📄 Converting {paper_id}...")
            export_paper_to_pdf(
                paper_id=paper_data.get('paper_id', paper_id),
                title=paper_data.get('title', 'Untitled'),
                authors=paper_data.get('authors', ['Unknown']),
                abstract=paper_data.get('abstract', ''),
                introduction=paper_data.get('introduction', ''),
                methodology=paper_data.get('methodology', ''),
                results=paper_data.get('results', ''),
                discussion=paper_data.get('discussion', ''),
                conclusion=paper_data.get('conclusion', ''),
                references=paper_data.get('references', []),
                keywords=paper_data.get('keywords', []),
                timestamp=timestamp,
                output_path=pdf_file,
            )
            
            print(f"   ✅ Created {pdf_file.name} ({pdf_file.stat().st_size:,} bytes)")
            converted += 1
            
        except Exception as e:
            print(f"   ❌ Error converting {paper_id}: {e}")
            logger.error("pdf_conversion_failed", paper_id=paper_id, error=str(e))
            errors += 1
    
    print("\n" + "=" * 80)
    print("Conversion Complete!")
    print("=" * 80)
    print(f"\n✅ Converted: {converted}")
    print(f"⏭️  Skipped (already exists): {skipped}")
    print(f"❌ Errors: {errors}")
    print(f"\n📁 PDF files saved to: {papers_dir.absolute()}")
    print("=" * 80)
    
    return errors == 0


if __name__ == "__main__":
    success = asyncio.run(convert_papers_to_pdf())
    exit(0 if success else 1)
