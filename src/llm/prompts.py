"""
Prompt templates for various agent activities.

This module provides structured prompts for learning, teaching, research,
and other agent interactions with the LLM.
"""

from __future__ import annotations

from typing import Any


class PromptTemplates:
    """Collection of prompt templates for agent activities."""

    # ==================== LEARNING PROMPTS ====================

    @staticmethod
    def paper_comprehension(
        paper_title: str,
        paper_abstract: str,
        agent_background: str,
    ) -> str:
        """Generate a prompt for assessing paper comprehension."""
        return f"""You are an AI research agent learning about new topics.

Your Background:
{agent_background}

Paper to Study:
Title: {paper_title}
Abstract: {paper_abstract}

Tasks:
1. Summarize the main contributions of this paper in 2-3 sentences
2. List 3 key concepts you need to understand to fully grasp this paper
3. Generate 3 specific questions you have about the methodology
4. Rate your confidence in understanding this paper (0-100%)

Format your response as:
SUMMARY: [your summary]
KEY CONCEPTS: [concept 1], [concept 2], [concept 3]
QUESTIONS:
1. [question 1]
2. [question 2]
3. [question 3]
CONFIDENCE: [0-100]%
"""

    @staticmethod
    def concept_explanation_request(
        concept: str,
        context: str,
        current_understanding: str,
    ) -> str:
        """Generate a prompt for requesting concept explanation from mentor."""
        return f"""I am learning about "{concept}" in the context of: {context}

My current understanding:
{current_understanding}

Please provide:
1. A clear explanation of {concept} appropriate for my level
2. How it relates to: {context}
3. A simple example to illustrate the concept
4. Common misconceptions to avoid

Keep the explanation focused and practical."""

    @staticmethod
    def self_assessment(
        topic: str,
        learning_materials: list[str],
        time_spent_hours: float,
    ) -> str:
        """Generate a prompt for self-assessment after learning."""
        materials_str = "\n".join(f"- {m}" for m in learning_materials)
        return f"""You just completed a learning session on: {topic}

Materials studied:
{materials_str}

Time spent: {time_spent_hours:.1f} hours

Perform a self-assessment:
1. What are the 3 most important things you learned?
2. What concepts are still unclear?
3. Can you explain this topic to someone else?
4. What should you study next to deepen your understanding?
5. Rate your mastery of this topic (0-100%)

Be honest and specific in your assessment."""

    # ==================== TEACHING PROMPTS ====================

    @staticmethod
    def assess_student_knowledge(
        student_background: str,
        topic: str,
        student_questions: list[str],
    ) -> str:
        """Generate a prompt for assessing student's knowledge level."""
        questions_str = "\n".join(f"{i+1}. {q}" for i, q in enumerate(student_questions))
        return f"""You are mentoring a student with the following background:
{student_background}

They want to learn about: {topic}

Their questions:
{questions_str}

Based on their background and questions, assess:
1. Their current knowledge level (novice/beginner/intermediate/advanced)
2. Which prerequisites they likely have
3. Which prerequisites they might be missing
4. The best starting point for teaching them
5. An appropriate learning pace

Provide your assessment in a structured format."""

    @staticmethod
    def create_explanation(
        topic: str,
        student_level: str,
        learning_goal: str,
    ) -> str:
        """Generate a prompt for creating student-appropriate explanations."""
        return f"""Create an explanation of "{topic}" for a student at the {student_level} level.

Learning Goal: {learning_goal}

Your explanation should:
1. Start with the fundamentals they need
2. Build up concepts progressively
3. Use clear examples and analogies
4. Avoid jargon unless you define it
5. Include a simple exercise to test understanding
6. End with what they should study next

Be patient, clear, and encouraging."""

    @staticmethod
    def verify_student_understanding(
        concept: str,
        student_explanation: str,
    ) -> str:
        """Generate a prompt for verifying student understanding."""
        return f"""A student just tried to explain "{concept}" to you:

Student's explanation:
{student_explanation}

Evaluate their understanding:
1. What did they get right?
2. What misconceptions do they have?
3. What key points are they missing?
4. How would you rate their understanding (0-100%)?
5. What specific feedback would help them improve?

Be constructive and specific."""

    # ==================== RESEARCH PROMPTS ====================

    @staticmethod
    def literature_review(
        research_question: str,
        papers: list[dict[str, str]],
    ) -> str:
        """Generate a prompt for conducting literature review."""
        papers_str = "\n".join(
            f"{i+1}. {p['title']}\n   Abstract: {p['abstract'][:200]}..."
            for i, p in enumerate(papers)
        )
        return f"""Conduct a literature review for the research question:
"{research_question}"

Papers to review:
{papers_str}

Your analysis should cover:
1. Current state of research in this area
2. Key methodologies being used
3. Major findings and conclusions
4. Gaps in the literature
5. Contradictions or debates
6. Promising directions for future research

Focus on insights relevant to the research question."""

    @staticmethod
    def hypothesis_generation(
        research_area: str,
        background_knowledge: str,
        literature_gaps: list[str],
    ) -> str:
        """Generate a prompt for hypothesis generation."""
        gaps_str = "\n".join(f"- {gap}" for gap in literature_gaps)
        return f"""Generate research hypotheses in: {research_area}

Background:
{background_knowledge}

Identified gaps in literature:
{gaps_str}

For each hypothesis:
1. State the hypothesis clearly
2. Explain why it's worth investigating
3. Suggest how it could be tested
4. Identify required resources
5. Estimate feasibility (high/medium/low)

Generate 3-5 promising hypotheses."""

    @staticmethod
    def experiment_design(
        hypothesis: str,
        available_resources: list[str],
        constraints: list[str],
    ) -> str:
        """Generate a prompt for experimental design."""
        resources_str = "\n".join(f"- {r}" for r in available_resources)
        constraints_str = "\n".join(f"- {c}" for c in constraints)
        return f"""Design an experiment to test this hypothesis:
{hypothesis}

Available resources:
{resources_str}

Constraints:
{constraints_str}

Design should include:
1. Methodology overview
2. Variables to measure
3. Control conditions
4. Data collection plan
5. Analysis approach
6. Expected outcomes
7. Potential issues and mitigation

Be specific and practical."""

    @staticmethod
    def results_analysis(
        hypothesis: str,
        results: dict[str, Any],
        methodology: str,
    ) -> str:
        """Generate a prompt for analyzing experimental results."""
        results_str = "\n".join(f"{k}: {v}" for k, v in results.items())
        return f"""Analyze experimental results:

Hypothesis: {hypothesis}

Methodology: {methodology}

Results:
{results_str}

Provide:
1. Summary of findings
2. Statistical significance (if applicable)
3. Support for or against hypothesis
4. Alternative explanations
5. Limitations of the study
6. Implications of findings
7. Recommendations for future work

Be objective and thorough."""

    # ==================== PEER REVIEW PROMPTS ====================

    @staticmethod
    def paper_review(
        paper_title: str,
        paper_abstract: str,
        paper_content: str,
        review_criteria: dict[str, str],
    ) -> str:
        """Generate a prompt for peer reviewing a paper."""
        criteria_str = "\n".join(f"- {k}: {v}" for k, v in review_criteria.items())
        return f"""Review this research paper:

Title: {paper_title}
Abstract: {paper_abstract}

Content:
{paper_content[:2000]}...

Review Criteria:
{criteria_str}

Provide a structured review covering:
1. NOVELTY: Is this work original and significant?
2. METHODOLOGY: Are methods sound and appropriate?
3. RESULTS: Are findings well-supported?
4. CLARITY: Is the paper well-written?
5. CONTRIBUTION: What is the impact?
6. WEAKNESSES: What are the main issues?
7. STRENGTHS: What does it do well?
8. RECOMMENDATION: Accept/Revise/Reject

Be fair, constructive, and specific."""

    @staticmethod
    def revision_suggestions(
        paper_section: str,
        identified_issues: list[str],
    ) -> str:
        """Generate a prompt for suggesting paper revisions."""
        issues_str = "\n".join(f"{i+1}. {issue}" for i, issue in enumerate(identified_issues))
        return f"""Suggest revisions for this paper section:

{paper_section}

Identified issues:
{issues_str}

For each issue, provide:
1. Specific suggested change
2. Reason for the change
3. Example of improved text (if applicable)

Be constructive and actionable."""

    # ==================== COLLABORATION PROMPTS ====================

    @staticmethod
    def project_discussion(
        project_goal: str,
        participant_roles: dict[str, str],
        current_status: str,
    ) -> str:
        """Generate a prompt for collaborative project discussion."""
        roles_str = "\n".join(f"- {name}: {role}" for name, role in participant_roles.items())
        return f"""Collaborative project discussion:

Project Goal: {project_goal}

Participants:
{roles_str}

Current Status: {current_status}

Discuss:
1. Progress so far
2. Challenges encountered
3. Division of next steps
4. Timeline adjustments
5. Resources needed
6. How you can contribute

Be collaborative and solution-oriented."""

    @staticmethod
    def knowledge_sharing(
        topic: str,
        your_expertise: str,
        colleagues_interest: str,
    ) -> str:
        """Generate a prompt for knowledge sharing session."""
        return f"""Share your knowledge about: {topic}

Your Expertise: {your_expertise}

Colleague's Interest: {colleagues_interest}

Structure your knowledge sharing:
1. Key concepts and definitions
2. Why this topic matters
3. Current best practices
4. Common pitfalls to avoid
5. Resources for further learning
6. Open questions in the field

Make it engaging and practical."""

    # ==================== UTILITY PROMPTS ====================

    @staticmethod
    def summarize_text(
        text: str,
        target_length: str = "brief",
        focus: str = "main points",
    ) -> str:
        """Generate a prompt for text summarization."""
        return f"""Summarize the following text.

Length: {target_length}
Focus on: {focus}

Text:
{text}

Provide a clear, accurate summary."""

    @staticmethod
    def extract_key_concepts(
        text: str,
        domain: str,
    ) -> str:
        """Generate a prompt for extracting key concepts."""
        return f"""Extract key concepts from this {domain} text:

{text}

For each concept:
1. Concept name
2. Brief definition
3. Importance in this context

List the 5-10 most important concepts."""

    @staticmethod
    def generate_questions(
        content: str,
        question_type: str = "comprehension",
        difficulty: str = "moderate",
    ) -> str:
        """Generate a prompt for creating questions about content."""
        return f"""Generate {difficulty} {question_type} questions about:

{content}

Create 5 questions that:
1. Test understanding of key concepts
2. Encourage critical thinking
3. Are clear and specific
4. Have definitive answers

Include brief answer keys."""
