"""
Research workflows using LangGraph.

Implements multi-agent research workflows including:
- Learning workflows (reading, comprehension, knowledge building)
- Research workflows (hypothesis, experiments, analysis)
- Collaboration workflows (joint research, co-authoring)
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, TypedDict
from uuid import UUID

from langgraph.graph import END, StateGraph

from src.activities.learning import LearningActivity
from src.activities.research import ResearchActivity
from src.activities.review import ReviewActivity
from src.activities.teaching import TeachingActivity
from src.core.agent import Agent
from src.orchestration.events import (
    EventType,
    emit_experiment_completed,
    emit_help_requested,
    emit_paper_read,
)
from src.orchestration.matchmaking import Matchmaker
from src.utils.logging import get_logger

logger = get_logger(__name__)


class WorkflowStatus(str, Enum):
    """Status of a workflow."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# State types for workflows


class LearningState(TypedDict):
    """State for learning workflow."""

    agent_id: UUID
    paper_id: str
    comprehension_level: str | None
    help_needed: bool
    mentor_id: UUID | None
    completed: bool
    error: str | None


class ResearchState(TypedDict):
    """State for research workflow."""

    agent_id: UUID
    topic: str
    papers_reviewed: list[str]
    hypothesis: str | None
    experiment_designed: bool
    experiment_completed: bool
    results: dict[str, Any] | None
    completed: bool
    error: str | None


class CollaborationState(TypedDict):
    """State for collaboration workflow."""

    lead_agent_id: UUID
    collaborator_ids: list[UUID]
    topic: str
    phase: str  # "planning", "execution", "writing", "review"
    paper_draft: str | None
    reviews: list[dict[str, Any]]
    completed: bool
    error: str | None


@dataclass
class WorkflowResult:
    """Result of a workflow execution."""

    workflow_id: str
    status: WorkflowStatus
    output: dict[str, Any]
    error: str | None = None


class LearningWorkflow:
    """
    Workflow for agent learning activities.

    Coordinates the process of reading papers, assessing comprehension,
    and seeking help from mentors when needed.
    """

    def __init__(self):
        """Initialize learning workflow."""
        self.logger = get_logger(__name__)
        self.matchmaker = Matchmaker()
        self.learning_activity = LearningActivity()

    def create_graph(self) -> StateGraph:
        """
        Create the learning workflow graph.

        Returns:
            StateGraph for learning
        """
        workflow = StateGraph(LearningState)

        # Add nodes
        workflow.add_node("read_paper", self._read_paper_node)
        workflow.add_node("assess_comprehension", self._assess_comprehension_node)
        workflow.add_node("seek_help", self._seek_help_node)
        workflow.add_node("receive_help", self._receive_help_node)

        # Add edges
        workflow.set_entry_point("read_paper")
        workflow.add_edge("read_paper", "assess_comprehension")

        # Conditional edge: need help or complete?
        workflow.add_conditional_edges(
            "assess_comprehension",
            self._should_seek_help,
            {
                "seek_help": "seek_help",
                "complete": END,
            },
        )

        workflow.add_edge("seek_help", "receive_help")
        workflow.add_edge("receive_help", END)

        return workflow

    async def _read_paper_node(self, state: LearningState) -> LearningState:
        """Read paper node."""
        try:
            # Get agent (in real implementation, fetch from community)
            agent_id = state["agent_id"]
            paper_id = state["paper_id"]

            self.logger.info(
                "workflow_read_paper",
                agent_id=str(agent_id),
                paper_id=paper_id,
            )

            # In real implementation, call learning activity
            # result = await self.learning_activity.read_paper(agent, paper_id)

            # For now, simulate
            state["comprehension_level"] = "partial"
            state["help_needed"] = False

            await emit_paper_read(agent_id, paper_id, "partial")

        except Exception as e:
            state["error"] = str(e)
            state["completed"] = True

        return state

    async def _assess_comprehension_node(self, state: LearningState) -> LearningState:
        """Assess comprehension node."""
        try:
            comprehension = state["comprehension_level"]

            # Determine if help is needed
            if comprehension in ["none", "minimal"]:
                state["help_needed"] = True
            else:
                state["help_needed"] = False
                state["completed"] = True

        except Exception as e:
            state["error"] = str(e)
            state["completed"] = True

        return state

    def _should_seek_help(self, state: LearningState) -> str:
        """Determine if agent should seek help."""
        return "seek_help" if state["help_needed"] else "complete"

    async def _seek_help_node(self, state: LearningState) -> LearningState:
        """Seek help from mentor node."""
        try:
            agent_id = state["agent_id"]
            paper_id = state["paper_id"]

            # In real implementation, use matchmaker to find mentor
            # mentor = await self.matchmaker.find_mentor_for_student(agent, topic)

            self.logger.info(
                "workflow_seeking_help",
                agent_id=str(agent_id),
                paper_id=paper_id,
            )

            await emit_help_requested(agent_id, f"paper:{paper_id}")

            # For now, simulate finding a mentor
            state["mentor_id"] = agent_id  # Placeholder

        except Exception as e:
            state["error"] = str(e)

        return state

    async def _receive_help_node(self, state: LearningState) -> LearningState:
        """Receive help from mentor node."""
        try:
            # In real implementation, mentor provides explanation
            # teaching_activity.create_lesson(...)

            self.logger.info(
                "workflow_help_received",
                student_id=str(state["agent_id"]),
                mentor_id=str(state["mentor_id"]),
            )

            state["completed"] = True

        except Exception as e:
            state["error"] = str(e)

        return state

    async def execute(self, agent_id: UUID, paper_id: str) -> WorkflowResult:
        """
        Execute learning workflow.

        Args:
            agent_id: Agent performing learning
            paper_id: Paper to learn from

        Returns:
            Workflow result
        """
        graph = self.create_graph()
        compiled = graph.compile()

        initial_state: LearningState = {
            "agent_id": agent_id,
            "paper_id": paper_id,
            "comprehension_level": None,
            "help_needed": False,
            "mentor_id": None,
            "completed": False,
            "error": None,
        }

        try:
            final_state = await compiled.ainvoke(initial_state)

            status = (
                WorkflowStatus.COMPLETED
                if final_state["completed"] and not final_state["error"]
                else WorkflowStatus.FAILED
            )

            return WorkflowResult(
                workflow_id=f"learning_{agent_id}_{paper_id}",
                status=status,
                output=dict(final_state),
                error=final_state["error"],
            )

        except Exception as e:
            self.logger.error("workflow_execution_failed", error=str(e))
            return WorkflowResult(
                workflow_id=f"learning_{agent_id}_{paper_id}",
                status=WorkflowStatus.FAILED,
                output={},
                error=str(e),
            )


class ResearchWorkflow:
    """
    Workflow for research activities.

    Coordinates literature review, hypothesis generation,
    experiment design and execution, and results analysis.
    """

    def __init__(self):
        """Initialize research workflow."""
        self.logger = get_logger(__name__)
        self.research_activity = ResearchActivity()

    def create_graph(self) -> StateGraph:
        """
        Create the research workflow graph.

        Returns:
            StateGraph for research
        """
        workflow = StateGraph(ResearchState)

        # Add nodes
        workflow.add_node("review_literature", self._review_literature_node)
        workflow.add_node("generate_hypothesis", self._generate_hypothesis_node)
        workflow.add_node("design_experiment", self._design_experiment_node)
        workflow.add_node("run_experiment", self._run_experiment_node)
        workflow.add_node("analyze_results", self._analyze_results_node)

        # Add edges
        workflow.set_entry_point("review_literature")
        workflow.add_edge("review_literature", "generate_hypothesis")
        workflow.add_edge("generate_hypothesis", "design_experiment")
        workflow.add_edge("design_experiment", "run_experiment")
        workflow.add_edge("run_experiment", "analyze_results")
        workflow.add_edge("analyze_results", END)

        return workflow

    async def _review_literature_node(self, state: ResearchState) -> ResearchState:
        """Review literature node."""
        try:
            topic = state["topic"]

            self.logger.info("workflow_reviewing_literature", topic=topic)

            # In real implementation, search and review papers
            # results = await self.research_activity.review_literature(agent, topic)

            # Simulate
            state["papers_reviewed"] = ["paper1", "paper2", "paper3"]

        except Exception as e:
            state["error"] = str(e)

        return state

    async def _generate_hypothesis_node(self, state: ResearchState) -> ResearchState:
        """Generate hypothesis node."""
        try:
            self.logger.info("workflow_generating_hypothesis")

            # In real implementation, use LLM to generate hypothesis
            # hypothesis = await self.research_activity.generate_hypothesis(...)

            state["hypothesis"] = "Simulated hypothesis based on literature review"

        except Exception as e:
            state["error"] = str(e)

        return state

    async def _design_experiment_node(self, state: ResearchState) -> ResearchState:
        """Design experiment node."""
        try:
            self.logger.info("workflow_designing_experiment")

            # In real implementation, design experiment methodology
            # design = await self.research_activity.design_experiment(...)

            state["experiment_designed"] = True

        except Exception as e:
            state["error"] = str(e)

        return state

    async def _run_experiment_node(self, state: ResearchState) -> ResearchState:
        """Run experiment node."""
        try:
            agent_id = state["agent_id"]

            self.logger.info("workflow_running_experiment", agent_id=str(agent_id))

            # In real implementation, execute experiment code
            # result = await self.research_activity.conduct_experiment(...)

            state["experiment_completed"] = True
            state["results"] = {"success": True, "data": [1, 2, 3]}

            await emit_experiment_completed(agent_id, "exp_001", True)

        except Exception as e:
            state["error"] = str(e)

        return state

    async def _analyze_results_node(self, state: ResearchState) -> ResearchState:
        """Analyze results node."""
        try:
            self.logger.info("workflow_analyzing_results")

            # In real implementation, analyze experiment results
            # analysis = await self.research_activity.analyze_results(...)

            state["completed"] = True

        except Exception as e:
            state["error"] = str(e)

        return state

    async def execute(self, agent_id: UUID, topic: str) -> WorkflowResult:
        """
        Execute research workflow.

        Args:
            agent_id: Agent performing research
            topic: Research topic

        Returns:
            Workflow result
        """
        graph = self.create_graph()
        compiled = graph.compile()

        initial_state: ResearchState = {
            "agent_id": agent_id,
            "topic": topic,
            "papers_reviewed": [],
            "hypothesis": None,
            "experiment_designed": False,
            "experiment_completed": False,
            "results": None,
            "completed": False,
            "error": None,
        }

        try:
            final_state = await compiled.ainvoke(initial_state)

            status = (
                WorkflowStatus.COMPLETED
                if final_state["completed"] and not final_state["error"]
                else WorkflowStatus.FAILED
            )

            return WorkflowResult(
                workflow_id=f"research_{agent_id}_{topic}",
                status=status,
                output=dict(final_state),
                error=final_state["error"],
            )

        except Exception as e:
            self.logger.error("workflow_execution_failed", error=str(e))
            return WorkflowResult(
                workflow_id=f"research_{agent_id}_{topic}",
                status=WorkflowStatus.FAILED,
                output={},
                error=str(e),
            )


class CollaborationWorkflow:
    """
    Workflow for collaborative research.

    Coordinates multiple agents working together on research,
    including joint paper writing and peer review.
    """

    def __init__(self):
        """Initialize collaboration workflow."""
        self.logger = get_logger(__name__)
        self.research_activity = ResearchActivity()
        self.review_activity = ReviewActivity()

    def create_graph(self) -> StateGraph:
        """
        Create the collaboration workflow graph.

        Returns:
            StateGraph for collaboration
        """
        workflow = StateGraph(CollaborationState)

        # Add nodes
        workflow.add_node("plan_research", self._plan_research_node)
        workflow.add_node("execute_research", self._execute_research_node)
        workflow.add_node("write_paper", self._write_paper_node)
        workflow.add_node("peer_review", self._peer_review_node)
        workflow.add_node("revise_paper", self._revise_paper_node)

        # Add edges
        workflow.set_entry_point("plan_research")
        workflow.add_edge("plan_research", "execute_research")
        workflow.add_edge("execute_research", "write_paper")
        workflow.add_edge("write_paper", "peer_review")
        workflow.add_edge("peer_review", "revise_paper")
        workflow.add_edge("revise_paper", END)

        return workflow

    async def _plan_research_node(
        self, state: CollaborationState
    ) -> CollaborationState:
        """Plan research node."""
        try:
            self.logger.info(
                "workflow_planning_collaboration",
                lead=str(state["lead_agent_id"]),
                num_collaborators=len(state["collaborator_ids"]),
            )

            state["phase"] = "planning"

        except Exception as e:
            state["error"] = str(e)

        return state

    async def _execute_research_node(
        self, state: CollaborationState
    ) -> CollaborationState:
        """Execute research node."""
        try:
            self.logger.info("workflow_executing_collaborative_research")

            state["phase"] = "execution"

        except Exception as e:
            state["error"] = str(e)

        return state

    async def _write_paper_node(
        self, state: CollaborationState
    ) -> CollaborationState:
        """Write paper node."""
        try:
            self.logger.info("workflow_writing_paper")

            # Get lead agent
            lead_agent_id = state["lead_agent_id"]
            topic = state["topic"]
            
            # In a real implementation, fetch agent from community and call write_paper
            # For now, mark as written with placeholder content
            state["phase"] = "writing"
            state["paper_draft"] = f"Research paper on {topic} (generated by collaboration workflow)"
            
            # TODO: Integrate with ResearchActivity.write_paper()
            # from src.orchestration.community import get_community
            # from src.activities.research import write_paper
            # community = get_community()
            # agent = await community.get_agent(lead_agent_id)
            # paper = await write_paper(agent, title, research_question, lit_review, experiments)
            # state["paper_draft"] = paper.abstract

        except Exception as e:
            state["error"] = str(e)

        return state

    async def _peer_review_node(
        self, state: CollaborationState
    ) -> CollaborationState:
        """Peer review node."""
        try:
            self.logger.info("workflow_peer_review")

            state["phase"] = "review"
            state["reviews"] = [
                {"reviewer_id": "reviewer1", "decision": "accept"},
                {"reviewer_id": "reviewer2", "decision": "minor_revisions"},
            ]

        except Exception as e:
            state["error"] = str(e)

        return state

    async def _revise_paper_node(
        self, state: CollaborationState
    ) -> CollaborationState:
        """Revise paper node."""
        try:
            self.logger.info("workflow_revising_paper")

            state["completed"] = True

        except Exception as e:
            state["error"] = str(e)

        return state

    async def execute(
        self,
        lead_agent_id: UUID,
        collaborator_ids: list[UUID],
        topic: str,
    ) -> WorkflowResult:
        """
        Execute collaboration workflow.

        Args:
            lead_agent_id: Lead agent
            collaborator_ids: Collaborating agents
            topic: Research topic

        Returns:
            Workflow result
        """
        graph = self.create_graph()
        compiled = graph.compile()

        initial_state: CollaborationState = {
            "lead_agent_id": lead_agent_id,
            "collaborator_ids": collaborator_ids,
            "topic": topic,
            "phase": "planning",
            "paper_draft": None,
            "reviews": [],
            "completed": False,
            "error": None,
        }

        try:
            final_state = await compiled.ainvoke(initial_state)

            status = (
                WorkflowStatus.COMPLETED
                if final_state["completed"] and not final_state["error"]
                else WorkflowStatus.FAILED
            )

            return WorkflowResult(
                workflow_id=f"collab_{lead_agent_id}_{topic}",
                status=status,
                output=dict(final_state),
                error=final_state["error"],
            )

        except Exception as e:
            self.logger.error("workflow_execution_failed", error=str(e))
            return WorkflowResult(
                workflow_id=f"collab_{lead_agent_id}_{topic}",
                status=WorkflowStatus.FAILED,
                output={},
                error=str(e),
            )
