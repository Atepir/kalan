"""
LaTeX templates and document generation.

Provides templates and functions for generating research papers in LaTeX.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.llm import PromptTemplates, get_ollama_client
from src.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class LatexDocument:
    """LaTeX document representation."""

    title: str
    authors: list[str]
    abstract: str
    sections: list[dict[str, str]]  # [{"title": "...", "content": "..."}]
    bibliography: list[str]
    document_class: str = "article"


def get_latex_template(document_class: str = "article") -> str:
    """
    Get base LaTeX template.

    Args:
        document_class: LaTeX document class

    Returns:
        LaTeX template string
    """
    return r"""\documentclass[12pt]{article}
\usepackage[utf8]{inputenc}
\usepackage{amsmath}
\usepackage{amsfonts}
\usepackage{amssymb}
\usepackage{graphicx}
\usepackage{hyperref}
\usepackage{cite}

\title{{{title}}}
\author{{{authors}}}
\date{{\today}}

\begin{{document}}

\maketitle

\begin{{abstract}}
{abstract}
\end{{abstract}}

{sections}

\bibliographystyle{{plain}}
\bibliography{{references}}

\end{{document}}
"""


async def generate_latex_paper(
    title: str,
    authors: list[str],
    abstract: str,
    sections: list[dict[str, str]],
    bibliography: list[str] | None = None,
) -> str:
    """
    Generate a complete LaTeX paper.

    Args:
        title: Paper title
        authors: List of author names
        abstract: Paper abstract
        sections: List of sections with titles and content
        bibliography: Optional bibliography entries

    Returns:
        Complete LaTeX document
    """
    logger.info("generating_latex_paper", title=title)

    template = get_latex_template()

    # Format authors
    authors_str = " \\and ".join(authors)

    # Format sections
    sections_latex = []
    for section in sections:
        section_title = section.get("title", "Section")
        section_content = section.get("content", "")
        sections_latex.append(f"\\section{{{section_title}}}\n{section_content}\n")

    sections_str = "\n".join(sections_latex)

    # Fill template
    latex = template.format(
        title=title,
        authors=authors_str,
        abstract=abstract,
        sections=sections_str,
    )

    logger.info("latex_paper_generated", length=len(latex))
    return latex


async def generate_abstract(
    title: str,
    research_question: str,
    methodology: str,
    findings: str,
) -> str:
    """
    Generate a paper abstract using LLM.

    Args:
        title: Paper title
        research_question: Research question
        methodology: Methodology summary
        findings: Key findings

    Returns:
        Generated abstract
    """
    logger.info("generating_abstract", title=title)

    llm = get_ollama_client()

    prompt = f"""Generate a concise academic abstract for a research paper:

Title: {title}

Research Question: {research_question}

Methodology: {methodology}

Key Findings: {findings}

Write a structured abstract (150-250 words) following this format:
1. Background and motivation
2. Research question/objective
3. Methodology
4. Key findings
5. Implications

Be concise, professional, and follow academic writing conventions."""

    abstract = await llm.generate(
        prompt=prompt,
        max_tokens=500,
        temperature=0.7,
    )

    logger.info("abstract_generated", length=len(abstract))
    return abstract.strip()


async def generate_section(
    section_title: str,
    section_purpose: str,
    key_points: list[str],
    context: str = "",
) -> str:
    """
    Generate a paper section using LLM.

    Args:
        section_title: Title of the section
        section_purpose: Purpose of this section
        key_points: Key points to cover
        context: Additional context

    Returns:
        Generated section content
    """
    logger.info("generating_section", title=section_title)

    llm = get_ollama_client()

    key_points_str = "\n".join(f"- {point}" for point in key_points)

    prompt = f"""Generate a section for an academic research paper:

Section Title: {section_title}

Purpose: {section_purpose}

Key Points to Cover:
{key_points_str}

Context: {context}

Write a well-structured section that:
1. Flows naturally and logically
2. Uses appropriate academic language
3. Includes clear transitions between ideas
4. Supports claims with reasoning
5. Is approximately 300-500 words

Do not include LaTeX formatting in your response."""

    content = await llm.generate(
        prompt=prompt,
        max_tokens=800,
        temperature=0.7,
    )

    logger.info("section_generated", title=section_title, length=len(content))
    return content.strip()


async def generate_introduction(
    topic: str,
    motivation: str,
    research_gap: str,
    contribution: str,
) -> str:
    """
    Generate an introduction section.

    Args:
        topic: Research topic
        motivation: Why this research is important
        research_gap: Gap in existing literature
        contribution: Paper's contribution

    Returns:
        Generated introduction
    """
    key_points = [
        f"Topic: {topic}",
        f"Motivation: {motivation}",
        f"Research gap: {research_gap}",
        f"Our contribution: {contribution}",
    ]

    return await generate_section(
        section_title="Introduction",
        section_purpose="Introduce the research topic and establish motivation",
        key_points=key_points,
    )


async def generate_related_work(
    topic: str,
    papers: list[dict[str, str]],
) -> str:
    """
    Generate a related work section.

    Args:
        topic: Research topic
        papers: List of related papers with titles and summaries

    Returns:
        Generated related work section
    """
    key_points = [f"{p.get('title', '')}: {p.get('summary', '')}" for p in papers[:5]]

    return await generate_section(
        section_title="Related Work",
        section_purpose="Review relevant prior research",
        key_points=key_points,
        context=f"Research topic: {topic}",
    )


async def generate_methodology(
    approach: str,
    datasets: list[str],
    evaluation_metrics: list[str],
) -> str:
    """
    Generate a methodology section.

    Args:
        approach: Description of approach
        datasets: Datasets used
        evaluation_metrics: How results are evaluated

    Returns:
        Generated methodology section
    """
    key_points = [
        f"Approach: {approach}",
        f"Datasets: {', '.join(datasets)}",
        f"Evaluation: {', '.join(evaluation_metrics)}",
    ]

    return await generate_section(
        section_title="Methodology",
        section_purpose="Describe the research methodology",
        key_points=key_points,
    )


async def generate_conclusion(
    findings: list[str],
    limitations: list[str],
    future_work: list[str],
) -> str:
    """
    Generate a conclusion section.

    Args:
        findings: Key findings
        limitations: Study limitations
        future_work: Future research directions

    Returns:
        Generated conclusion
    """
    key_points = (
        [f"Finding: {f}" for f in findings]
        + [f"Limitation: {l}" for l in limitations]
        + [f"Future work: {fw}" for fw in future_work]
    )

    return await generate_section(
        section_title="Conclusion",
        section_purpose="Summarize findings and discuss implications",
        key_points=key_points,
    )


def format_bibliography(entries: list[dict[str, str]]) -> str:
    """
    Format bibliography entries in BibTeX format.

    Args:
        entries: List of bibliography entries

    Returns:
        BibTeX formatted bibliography
    """
    bibtex_entries = []

    for entry in entries:
        entry_type = entry.get("type", "article")
        cite_key = entry.get("cite_key", "unknown")

        fields = []
        for key, value in entry.items():
            if key not in ("type", "cite_key"):
                fields.append(f"  {key} = {{{value}}},")

        bibtex = f"@{entry_type}{{{cite_key},\n" + "\n".join(fields) + "\n}"
        bibtex_entries.append(bibtex)

    return "\n\n".join(bibtex_entries)
