# Paper Storage Implementation

## Problem
Previously, papers written by agents were only kept in memory and not persisted anywhere. This meant that all research papers generated during simulations were lost when the program ended.

## Solution
Added automatic paper persistence to both database and filesystem when agents write papers.

## Changes Made

### 1. Updated `src/activities/research.py`

**Added imports:**
```python
import json
from pathlib import Path
from src.storage.state_store import StateStore
from src.utils.config import get_config
```

**Added `_save_paper_to_storage()` method:**
- Saves papers to PostgreSQL database via `StateStore.save_paper()`
- Saves papers to filesystem in two formats:
  - **Markdown** (`.md`) - Human-readable format with full paper text
  - **JSON** (`.json`) - Structured format for programmatic access

**Modified `write_paper()` method:**
- Added call to `_save_paper_to_storage(paper)` after paper generation
- Papers are now automatically saved when created

### 2. Storage Locations

Papers are saved to:

1. **Database (PostgreSQL):**
   - Table: `papers`
   - Fields: `paper_id`, `title`, `abstract`, `content`, `metadata`, `created_at`

2. **Filesystem:**
   - Directory: `./data/papers/`
   - Files:
     - `{paper_id}.md` - Full paper in Markdown format
     - `{paper_id}.json` - Structured paper data in JSON format

### 3. Paper Format

**Markdown file includes:**
- Title, authors, keywords, date
- Abstract
- Introduction
- Methodology
- Results
- Discussion
- Conclusion
- References (numbered list)

**JSON file includes:**
All paper fields as structured data:
- paper_id, title, authors
- All sections (abstract, introduction, methodology, etc.)
- keywords, timestamp, experiment_ids

## Testing

Created `test_paper_saving.py` to verify functionality:
- Creates test agent and research activity
- Generates a complete paper
- Verifies files are saved to filesystem
- Checks database storage (via StateStore)

**To run the test:**
```powershell
poetry run python test_paper_saving.py
```

## Usage

No changes needed in existing code! Papers are now automatically saved when agents call `write_paper()`:

```python
from src.activities.research import ResearchActivity

research = ResearchActivity(agent)

# Papers are automatically saved to database and filesystem
paper = await research.write_paper(
    title="My Research Paper",
    research_question="How does X affect Y?",
    literature_review=lit_review,
    experiments=experiments,
    keywords=["ai", "ml"]
)
```

## Benefits

1. **Persistence:** Papers survive program restarts
2. **Accessibility:** Papers available in both database and filesystem
3. **Multiple Formats:** Markdown for reading, JSON for processing
4. **Searchability:** Papers stored in database can be queried
5. **Backward Compatible:** Existing code works without changes
6. **Error Handling:** Storage failures don't crash paper creation

## Next Steps

Potential enhancements:
- [ ] Export papers to LaTeX/PDF format
- [ ] Add paper versioning (revisions)
- [ ] Generate bibliography in standard formats (BibTeX, etc.)
- [ ] Add full-text search on paper content
- [ ] Create paper index/catalog view
- [ ] Add paper citation tracking
- [ ] Implement paper collaboration (multiple authors)

---

**Implementation Date:** October 16, 2025  
**Status:** ✅ Complete and tested
