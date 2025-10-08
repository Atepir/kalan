"""
Agent activity modules.

This package contains implementations of various activities that agents
can perform: learning, teaching, research, and peer review.
"""

from src.activities.learning import (
    LearningActivity,
    PaperReadingResult,
    assess_comprehension,
    read_paper,
    seek_mentor_help,
)
from src.activities.research import (
    ExperimentResult,
    HypothesisEvaluation,
    ResearchActivity,
    conduct_experiment,
    generate_hypothesis,
    review_literature,
)
from src.activities.review import (
    PeerReview,
    ReviewActivity,
    ReviewDecision,
    ReviewRecommendation,
    review_paper,
)
from src.activities.teaching import (
    TeachingActivity,
    TeachingSession,
    assess_student,
    create_lesson,
    provide_feedback,
)

__all__ = [
    # Learning
    "LearningActivity",
    "PaperReadingResult",
    "read_paper",
    "assess_comprehension",
    "seek_mentor_help",
    # Teaching
    "TeachingActivity",
    "TeachingSession",
    "assess_student",
    "create_lesson",
    "provide_feedback",
    # Research
    "ResearchActivity",
    "HypothesisEvaluation",
    "ExperimentResult",
    "review_literature",
    "generate_hypothesis",
    "conduct_experiment",
    # Review
    "ReviewActivity",
    "PeerReview",
    "ReviewDecision",
    "ReviewRecommendation",
    "review_paper",
]
