"""
Knowledge representation and graph module.

This module implements personal knowledge graphs for agents, tracking what they know,
how well they know it, and where that knowledge came from.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field, ConfigDict


class KnowledgeSource(BaseModel):
    """Represents the source of a piece of knowledge."""

    model_config = ConfigDict(frozen=True)

    source_type: str  # "paper", "mentor", "experiment", "self-study"
    source_id: str  # Paper ID, mentor agent ID, experiment ID, etc.
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    reliability: float = Field(default=1.0, ge=0.0, le=1.0)


class TopicKnowledge(BaseModel):
    """Represents knowledge about a specific topic."""

    model_config = ConfigDict(frozen=False)

    topic_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    depth_score: float = Field(default=0.0, ge=0.0, le=1.0)  # How deep is understanding
    breadth_score: float = Field(default=0.0, ge=0.0, le=1.0)  # How broad across subtopics
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)  # Agent's self-assessed confidence
    validated: bool = False  # Has knowledge been tested/validated
    validation_count: int = 0  # Number of times validated
    last_accessed: datetime = Field(default_factory=datetime.utcnow)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    sources: list[KnowledgeSource] = Field(default_factory=list)
    prerequisites: list[str] = Field(default_factory=list)  # Other topic names required
    subtopics: list[str] = Field(default_factory=list)
    related_papers: list[str] = Field(default_factory=list)
    notes: str = ""

    def add_source(self, source: KnowledgeSource) -> None:
        """Add a knowledge source."""
        self.sources.append(source)
        self.last_updated = datetime.utcnow()

    def update_understanding(
        self,
        depth_delta: float = 0.0,
        breadth_delta: float = 0.0,
        confidence_delta: float = 0.0,
    ) -> None:
        """Update understanding scores with deltas."""
        self.depth_score = max(0.0, min(1.0, self.depth_score + depth_delta))
        self.breadth_score = max(0.0, min(1.0, self.breadth_score + breadth_delta))
        self.confidence = max(0.0, min(1.0, self.confidence + confidence_delta))
        self.last_updated = datetime.utcnow()

    def validate(self, success: bool) -> None:
        """Mark knowledge as validated (or not)."""
        self.validation_count += 1
        if success:
            self.validated = True
            # Boost confidence on successful validation
            self.confidence = min(1.0, self.confidence + 0.1)
        else:
            # Reduce confidence on failed validation
            self.confidence = max(0.0, self.confidence - 0.15)
        self.last_updated = datetime.utcnow()

    def access(self) -> None:
        """Record that this knowledge was accessed."""
        self.last_accessed = datetime.utcnow()

    @property
    def overall_mastery(self) -> float:
        """Calculate overall mastery score combining depth, breadth, and confidence."""
        return (self.depth_score * 0.4 + self.breadth_score * 0.3 + self.confidence * 0.3)

    @property
    def needs_review(self) -> bool:
        """Check if knowledge needs review based on recency and validation."""
        days_since_access = (datetime.utcnow() - self.last_accessed).days
        return (
            days_since_access > 30
            or not self.validated
            or self.confidence < 0.6
        )


class ConceptRelation(BaseModel):
    """Represents a relationship between two concepts/topics."""

    model_config = ConfigDict(frozen=True)

    from_topic: str
    to_topic: str
    relation_type: str  # "prerequisite", "related", "subtopic", "application"
    strength: float = Field(default=1.0, ge=0.0, le=1.0)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class KnowledgeGraph(BaseModel):
    """
    Personal knowledge graph for an agent.

    Tracks topics, their relationships, and the agent's understanding of each.
    Supports semantic search, competency assessment, and knowledge transfer.
    """

    model_config = ConfigDict(frozen=False)

    graph_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    topics: dict[str, TopicKnowledge] = Field(default_factory=dict)
    relations: list[ConceptRelation] = Field(default_factory=list)
    total_updates: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_modified: datetime = Field(default_factory=datetime.utcnow)

    def add_topic(
        self,
        name: str,
        depth_score: float = 0.0,
        confidence: float = 0.0,
        sources: Optional[list[KnowledgeSource]] = None,
        prerequisites: Optional[list[str]] = None,
    ) -> TopicKnowledge:
        """Add a new topic to the knowledge graph."""
        if name in self.topics:
            # Topic already exists, return existing
            return self.topics[name]

        topic = TopicKnowledge(
            name=name,
            depth_score=depth_score,
            confidence=confidence,
            sources=sources or [],
            prerequisites=prerequisites or [],
        )
        self.topics[name] = topic
        self.total_updates += 1
        self.last_modified = datetime.utcnow()
        return topic

    def get_topic(self, name: str) -> Optional[TopicKnowledge]:
        """Get a topic by name."""
        topic = self.topics.get(name)
        if topic:
            topic.access()
        return topic

    def update_topic(
        self,
        name: str,
        depth_delta: float = 0.0,
        breadth_delta: float = 0.0,
        confidence_delta: float = 0.0,
        add_source: Optional[KnowledgeSource] = None,
    ) -> Optional[TopicKnowledge]:
        """Update an existing topic's understanding."""
        topic = self.topics.get(name)
        if not topic:
            return None

        topic.update_understanding(depth_delta, breadth_delta, confidence_delta)
        if add_source:
            topic.add_source(add_source)

        self.total_updates += 1
        self.last_modified = datetime.utcnow()
        return topic

    def add_relation(
        self,
        from_topic: str,
        to_topic: str,
        relation_type: str,
        strength: float = 1.0,
    ) -> ConceptRelation:
        """Add a relationship between two topics."""
        relation = ConceptRelation(
            from_topic=from_topic,
            to_topic=to_topic,
            relation_type=relation_type,
            strength=strength,
        )
        self.relations.append(relation)
        self.last_modified = datetime.utcnow()
        return relation

    def get_related_topics(self, topic_name: str, relation_type: Optional[str] = None) -> list[str]:
        """Get all topics related to a given topic."""
        related = []
        for rel in self.relations:
            if rel.from_topic == topic_name:
                if relation_type is None or rel.relation_type == relation_type:
                    related.append(rel.to_topic)
            elif rel.to_topic == topic_name:
                if relation_type is None or rel.relation_type == relation_type:
                    related.append(rel.from_topic)
        return related

    def get_prerequisites(self, topic_name: str) -> list[str]:
        """Get all prerequisite topics for a given topic."""
        topic = self.topics.get(topic_name)
        if topic:
            return topic.prerequisites
        return []

    def check_prerequisites_met(self, topic_name: str, threshold: float = 0.6) -> bool:
        """Check if all prerequisites for a topic are met (mastery >= threshold)."""
        prerequisites = self.get_prerequisites(topic_name)
        for prereq in prerequisites:
            prereq_topic = self.topics.get(prereq)
            if not prereq_topic or prereq_topic.overall_mastery < threshold:
                return False
        return True

    def get_topics_needing_review(self) -> list[TopicKnowledge]:
        """Get all topics that need review."""
        return [topic for topic in self.topics.values() if topic.needs_review]

    def get_average_depth(self) -> float:
        """Calculate average knowledge depth across all topics."""
        if not self.topics:
            return 0.0
        return sum(t.depth_score for t in self.topics.values()) / len(self.topics)

    def get_average_confidence(self) -> float:
        """Calculate average confidence across all topics."""
        if not self.topics:
            return 0.0
        return sum(t.confidence for t in self.topics.values()) / len(self.topics)

    def get_mastery_by_topic(self) -> dict[str, float]:
        """Get mastery scores for all topics."""
        return {name: topic.overall_mastery for name, topic in self.topics.items()}

    def assess_competency(self, topic_name: str) -> dict[str, Any]:
        """
        Assess agent's competency in a specific topic.

        Returns comprehensive assessment including:
        - Overall mastery score
        - Individual component scores
        - Prerequisites status
        - Validation status
        - Recommendations
        """
        topic = self.topics.get(topic_name)
        if not topic:
            return {
                "topic": topic_name,
                "known": False,
                "mastery": 0.0,
                "message": "Topic not in knowledge graph",
            }

        prereqs_met = self.check_prerequisites_met(topic_name)
        related_topics = self.get_related_topics(topic_name)

        # Generate recommendations
        recommendations = []
        if topic.confidence < 0.6:
            recommendations.append("Practice more to build confidence")
        if topic.depth_score < 0.7:
            recommendations.append("Study topic more deeply")
        if topic.breadth_score < 0.5:
            recommendations.append("Explore subtopics and applications")
        if not topic.validated:
            recommendations.append("Validate knowledge through testing or teaching")
        if not prereqs_met:
            recommendations.append("Review prerequisite topics")

        return {
            "topic": topic_name,
            "known": True,
            "mastery": topic.overall_mastery,
            "depth": topic.depth_score,
            "breadth": topic.breadth_score,
            "confidence": topic.confidence,
            "validated": topic.validated,
            "validation_count": topic.validation_count,
            "prerequisites_met": prereqs_met,
            "related_topics": related_topics,
            "needs_review": topic.needs_review,
            "recommendations": recommendations,
        }

    def export_for_teaching(self, topic_name: str) -> dict[str, Any]:
        """
        Export knowledge about a topic in a format suitable for teaching.

        Includes what the agent knows, confidence level, and teaching notes.
        """
        assessment = self.assess_competency(topic_name)
        topic = self.topics.get(topic_name)

        if not topic:
            return assessment

        return {
            **assessment,
            "teaching_notes": topic.notes,
            "sources": [
                {
                    "type": s.source_type,
                    "id": s.source_id,
                    "reliability": s.reliability,
                }
                for s in topic.sources
            ],
            "subtopics": topic.subtopics,
            "related_papers": topic.related_papers,
        }

    def merge_knowledge(self, other_knowledge: dict[str, Any]) -> None:
        """
        Merge knowledge from another source (e.g., teacher, paper).

        Used during teaching sessions to transfer knowledge.
        """
        for topic_name, info in other_knowledge.items():
            if topic_name in self.topics:
                # Update existing topic
                topic = self.topics[topic_name]
                topic.update_understanding(
                    depth_delta=info.get("depth_boost", 0.0),
                    breadth_delta=info.get("breadth_boost", 0.0),
                    confidence_delta=info.get("confidence_boost", 0.0),
                )
            else:
                # Add new topic
                self.add_topic(
                    name=topic_name,
                    depth_score=info.get("initial_depth", 0.3),
                    confidence=info.get("initial_confidence", 0.4),
                )

    def get_learning_path(self, target_topic: str) -> list[str]:
        """
        Generate a learning path to reach a target topic.

        Returns ordered list of topics to study, respecting prerequisites.
        """
        # Simple topological sort based on prerequisites
        visited = set()
        path = []

        def dfs(topic: str) -> None:
            if topic in visited:
                return
            visited.add(topic)

            # Visit prerequisites first
            prereqs = self.get_prerequisites(topic)
            for prereq in prereqs:
                dfs(prereq)

            path.append(topic)

        dfs(target_topic)
        return path

    def to_dict(self) -> dict[str, Any]:
        """Convert knowledge graph to dictionary."""
        return self.model_dump(mode="json")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> KnowledgeGraph:
        """Create knowledge graph from dictionary."""
        return cls.model_validate(data)

    def __repr__(self) -> str:
        """String representation of knowledge graph."""
        return (
            f"KnowledgeGraph(topics={len(self.topics)}, "
            f"avg_depth={self.get_average_depth():.2f}, "
            f"avg_confidence={self.get_average_confidence():.2f})"
        )
