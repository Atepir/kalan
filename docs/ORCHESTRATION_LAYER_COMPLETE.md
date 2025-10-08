# Orchestration Layer - Complete ✅

## Overview

The orchestration layer coordinates multi-agent activities in the Research Collective. It provides:
- **Community management**: Agent lifecycle, registration, coordination
- **Event-driven architecture**: Pub-sub system for agent communication
- **Matchmaking**: Mentor-student pairing, collaboration partners, peer reviewers
- **Workflows**: LangGraph-based workflows for learning, research, and collaboration

---

## Modules

### 1. `events.py` - Event System (350 lines)

**Purpose**: Event-driven communication between agents and system components.

**Key Components**:

```python
class EventType(Enum):
    # Agent lifecycle
    AGENT_CREATED = "agent_created"
    AGENT_PROMOTED = "agent_promoted"
    
    # Learning
    PAPER_READ = "paper_read"
    CONCEPT_LEARNED = "concept_learned"
    HELP_REQUESTED = "help_requested"
    
    # Research
    HYPOTHESIS_GENERATED = "hypothesis_generated"
    EXPERIMENT_COMPLETED = "experiment_completed"
    
    # Collaboration
    COLLABORATION_PROPOSED = "collaboration_proposed"
    REVIEW_SUBMITTED = "review_submitted"
```

**Event Bus**:
```python
event_bus = get_event_bus()

# Subscribe to events
async def handle_agent_promoted(event: Event):
    logger.info(f"Agent {event.source_agent_id} promoted!")

event_bus.subscribe(EventType.AGENT_PROMOTED, handle_agent_promoted)

# Publish events
event = Event(
    event_type=EventType.PAPER_READ,
    source_agent_id=agent.id,
    data={"paper_id": "arxiv:2401.12345", "comprehension": "good"}
)
await event_bus.publish(event)
```

**Features**:
- Async publish-subscribe pattern
- Event history tracking
- Concurrent handler execution
- Error handling for handlers
- Event filtering and statistics

**Convenience Functions**:
```python
await emit_agent_created(agent.id, agent_data)
await emit_agent_promoted(agent.id, old_stage, new_stage)
await emit_paper_read(agent.id, paper_id, comprehension_level)
await emit_help_requested(student_id, topic, mentor_id)
await emit_experiment_completed(agent.id, experiment_id, success)
```

---

### 2. `community.py` - Community Management (350 lines)

**Purpose**: Centralized agent lifecycle and coordination.

**Key Components**:

```python
community = get_community()

# Register new agent
agent = Agent(name="Alice", stage=DevelopmentalStage.APPRENTICE)
await community.register_agent(agent)

# List agents with filters
teachers = await community.list_agents(
    stage=DevelopmentalStage.TEACHER,
    active_only=True
)

# Get agent status
status = await community.get_agent_status(agent.id)
print(f"Papers read: {status.papers_read}")
print(f"Reputation: {status.reputation_score}")

# Promote agent
success = await community.promote_agent(agent.id)

# Get community stats
stats = await community.get_community_stats()
print(f"Total agents: {stats['total_agents']}")
print(f"By stage: {stats['agents_by_stage']}")
```

**AgentStatus**:
```python
@dataclass
class AgentStatus:
    agent_id: UUID
    name: str
    stage: DevelopmentalStage
    specialization: str
    active: bool
    last_activity: datetime
    papers_read: int
    papers_reviewed: int
    experiments_run: int
    students_taught: int
    reputation_score: float
```

**Features**:
- Agent registration and unregistration
- Active agent tracking
- Async task management per agent
- Stage promotion with validation
- Community-wide statistics
- Integration with event bus and metrics

**Task Management**:
```python
# Start agent activity
async def learning_activity():
    result = await learning.read_paper(agent, paper_id)
    
await community.start_agent_activity(agent.id, learning_activity())

# Stop agent activity
await community.stop_agent_activity(agent.id)

# Shutdown all
await community.shutdown()
```

---

### 3. `matchmaking.py` - Mentor-Student Matching (400 lines)

**Purpose**: Find optimal matches for mentorship, collaboration, and peer review.

**Key Components**:

**Mentor Matching**:
```python
matchmaker = Matchmaker()

# Find mentor for student
criteria = MatchingCriteria(
    topic="neural networks",
    min_expertise_gap=1,
    max_expertise_gap=3,
    min_mentor_reputation=0.5
)

match = await matchmaker.find_mentor_for_student(
    student=agent,
    topic="neural networks",
    criteria=criteria
)

if match:
    print(f"Mentor: {match.mentor_id}")
    print(f"Compatibility: {match.compatibility_score}")
    print(f"Shared topics: {match.shared_topics}")
    print(f"Reasoning: {match.reasoning}")
```

**MentorshipMatch**:
```python
@dataclass
class MentorshipMatch:
    mentor_id: UUID
    student_id: UUID
    compatibility_score: float  # 0-1
    shared_topics: list[str]
    mentor_expertise_level: int
    student_current_level: int
    reasoning: str
```

**Collaboration Matching**:
```python
# Find research collaborators
partners = await matchmaker.find_collaboration_partners(
    agent=researcher,
    topic="reinforcement learning",
    max_partners=3
)

for partner in partners:
    print(f"Partner: {partner.name} (stage: {partner.stage})")
```

**Reviewer Matching**:
```python
# Find peer reviewers
reviewers = await matchmaker.find_reviewers_for_paper(
    paper_id="paper_123",
    topics=["machine learning", "optimization"],
    exclude_agent_ids=[author.id],
    num_reviewers=3
)
```

**Matching Algorithm**:

Compatibility score (0-1) calculated from:
- **Expertise gap** (0.4 max): 1-2 level gap is ideal
- **Shared topics** (0.3 max): 0.05 per shared topic
- **Reputation** (0.2 max): Mentor's reputation score
- **Teaching experience** (0.1 max): Number of students taught

**Features**:
- Graph-based expertise matching (uses Neo4j)
- Multi-criteria filtering
- Scored ranking of candidates
- Support for mentorship, collaboration, and review
- Integration with knowledge graph

---

### 4. `workflows.py` - LangGraph Workflows (550 lines)

**Purpose**: Orchestrate multi-step agent activities using LangGraph state machines.

**Key Components**:

**Learning Workflow**:
```python
workflow = LearningWorkflow()

result = await workflow.execute(
    agent_id=agent.id,
    paper_id="arxiv:2401.12345"
)

if result.status == WorkflowStatus.COMPLETED:
    print(f"Comprehension: {result.output['comprehension_level']}")
    if result.output['mentor_id']:
        print(f"Help received from: {result.output['mentor_id']}")
```

**Learning Workflow Graph**:
```
read_paper → assess_comprehension → [need help?]
                                    ├─ Yes → seek_help → receive_help → END
                                    └─ No → END
```

**Research Workflow**:
```python
workflow = ResearchWorkflow()

result = await workflow.execute(
    agent_id=researcher.id,
    topic="meta-learning"
)

if result.status == WorkflowStatus.COMPLETED:
    print(f"Papers reviewed: {result.output['papers_reviewed']}")
    print(f"Hypothesis: {result.output['hypothesis']}")
    print(f"Experiment results: {result.output['results']}")
```

**Research Workflow Graph**:
```
review_literature → generate_hypothesis → design_experiment → 
run_experiment → analyze_results → END
```

**Collaboration Workflow**:
```python
workflow = CollaborationWorkflow()

result = await workflow.execute(
    lead_agent_id=lead.id,
    collaborator_ids=[collab1.id, collab2.id],
    topic="transfer learning"
)

if result.status == WorkflowStatus.COMPLETED:
    print(f"Paper draft: {result.output['paper_draft']}")
    print(f"Reviews: {result.output['reviews']}")
```

**Collaboration Workflow Graph**:
```
plan_research → execute_research → write_paper → 
peer_review → revise_paper → END
```

**Workflow State Types**:

```python
class LearningState(TypedDict):
    agent_id: UUID
    paper_id: str
    comprehension_level: str | None
    help_needed: bool
    mentor_id: UUID | None
    completed: bool
    error: str | None

class ResearchState(TypedDict):
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
    lead_agent_id: UUID
    collaborator_ids: list[UUID]
    topic: str
    phase: str  # "planning", "execution", "writing", "review"
    paper_draft: str | None
    reviews: list[dict[str, Any]]
    completed: bool
    error: str | None
```

**Features**:
- LangGraph state machines for complex workflows
- Conditional branching (e.g., seek help if comprehension low)
- Error handling and recovery
- Integration with activities modules
- Event emission at key points
- Extensible workflow patterns

---

## Architecture Patterns

### Event-Driven Communication

**Pattern**: Loose coupling between components via events

```python
# Publisher (e.g., LearningActivity)
async def read_paper(agent, paper_id):
    result = await _analyze_paper(paper_id)
    await emit_paper_read(agent.id, paper_id, result.comprehension)
    return result

# Subscriber (e.g., CommunityManager)
async def on_paper_read(event: Event):
    agent_id = event.source_agent_id
    paper_id = event.data['paper_id']
    # Update agent statistics
    await update_reading_count(agent_id)

event_bus.subscribe(EventType.PAPER_READ, on_paper_read)
```

### Singleton Pattern

Global instances for system-wide coordination:

```python
# Get global instances
community = get_community()
event_bus = get_event_bus()

# Ensures all components share same state
```

### Graph-Based Matching

Uses Neo4j knowledge graph for intelligent matching:

```python
# Find mentors via Cypher query
query = """
MATCH (mentor:Agent)-[:KNOWS]->(c:Concept {name: $topic})
WHERE mentor.stage IN ['teacher', 'researcher', 'expert']
RETURN mentor
ORDER BY c.depth DESC
"""
```

### Workflow State Machines

LangGraph provides declarative workflow definition:

```python
workflow = StateGraph(LearningState)
workflow.add_node("read_paper", read_paper_node)
workflow.add_conditional_edges(
    "assess_comprehension",
    should_seek_help,
    {"seek_help": "seek_help", "complete": END}
)
compiled = workflow.compile()
result = await compiled.ainvoke(initial_state)
```

---

## Integration Examples

### Complete Learning Session

```python
from src.orchestration import get_community, LearningWorkflow
from src.core.agent import Agent, DevelopmentalStage

# Create community
community = get_community()

# Create agent
agent = Agent(
    name="Alice",
    stage=DevelopmentalStage.APPRENTICE,
    specialization="machine learning"
)
await community.register_agent(agent)

# Execute learning workflow
workflow = LearningWorkflow()
result = await workflow.execute(
    agent_id=agent.id,
    paper_id="arxiv:2401.12345"
)

if result.status == WorkflowStatus.COMPLETED:
    # Check if promotion possible
    success = await community.promote_agent(agent.id)
    if success:
        print(f"Agent promoted to {agent.stage}")
```

### Research Collaboration

```python
from src.orchestration import Matchmaker, CollaborationWorkflow

# Find collaboration partners
matchmaker = Matchmaker()
partners = await matchmaker.find_collaboration_partners(
    agent=lead_researcher,
    topic="reinforcement learning",
    max_partners=2
)

# Execute collaboration workflow
workflow = CollaborationWorkflow()
result = await workflow.execute(
    lead_agent_id=lead_researcher.id,
    collaborator_ids=[p.id for p in partners],
    topic="reinforcement learning"
)

# Find reviewers for resulting paper
reviewers = await matchmaker.find_reviewers_for_paper(
    paper_id=result.output['paper_id'],
    topics=["reinforcement learning", "optimization"],
    exclude_agent_ids=[lead_researcher.id] + [p.id for p in partners],
    num_reviewers=3
)
```

### Event-Driven Mentorship

```python
from src.orchestration import get_event_bus, EventType, Matchmaker

event_bus = get_event_bus()
matchmaker = Matchmaker()

# Subscribe to help requests
async def handle_help_request(event: Event):
    student_id = event.source_agent_id
    topic = event.data['topic']
    
    # Find mentor
    student = await community.get_agent(student_id)
    match = await matchmaker.find_mentor_for_student(student, topic)
    
    if match:
        # Notify mentor
        await emit_teaching_request(match.mentor_id, student_id, topic)

event_bus.subscribe(EventType.HELP_REQUESTED, handle_help_request)
```

---

## Testing Checklist

### Unit Tests

- [ ] **EventBus**: Subscribe, publish, history, statistics
- [ ] **Community**: Register, unregister, promote, list agents
- [ ] **Matchmaker**: Find mentors, collaborators, reviewers
- [ ] **Workflows**: Execute learning, research, collaboration workflows

### Integration Tests

- [ ] **Event propagation**: Events trigger correct handlers
- [ ] **Workflow execution**: Complete workflows end-to-end
- [ ] **Matchmaking accuracy**: Scores calculated correctly
- [ ] **Community coordination**: Multi-agent scenarios

### Performance Tests

- [ ] **Event throughput**: Handle 1000+ events/second
- [ ] **Concurrent workflows**: Run 10+ workflows simultaneously
- [ ] **Matchmaking speed**: Find matches in <100ms
- [ ] **Community scaling**: Manage 100+ active agents

---

## Configuration

### Environment Variables

```env
# Community settings
MAX_ACTIVE_AGENTS=100
AGENT_TASK_TIMEOUT=300  # seconds

# Matchmaking thresholds
MIN_MENTOR_REPUTATION=0.5
DEFAULT_EXPERTISE_GAP=2

# Event bus settings
EVENT_HISTORY_LIMIT=10000
ENABLE_EVENT_PERSISTENCE=true
```

### LangGraph Configuration

```python
# Configure workflow compilation
compiled = workflow.compile(
    checkpointer=MemorySaver(),  # Or PostgresSaver for persistence
    interrupt_before=["seek_help"],  # Optional human-in-the-loop
    interrupt_after=["run_experiment"]
)
```

---

## Performance Considerations

### Event Bus

- **Concurrent handlers**: All handlers run in parallel via `asyncio.gather`
- **Error isolation**: Handler failures don't affect other handlers
- **History pruning**: Limit event history to prevent memory growth

### Community

- **Task management**: One task per agent prevents resource exhaustion
- **Lock usage**: Async locks prevent race conditions during registration
- **Lazy loading**: Load agents from DB only when needed

### Matchmaking

- **Graph queries**: Use indexed Cypher queries for fast matching
- **Caching**: Cache frequent queries (e.g., potential mentors by topic)
- **Parallel scoring**: Score candidates concurrently

### Workflows

- **State persistence**: Use checkpointers for long-running workflows
- **Error recovery**: Workflows can be resumed from checkpoints
- **Resource limits**: Set timeouts and max iterations

---

## Dependencies

From `pyproject.toml`:
```toml
langgraph = "^0.2.0"  # Workflow orchestration
```

---

## Summary

The orchestration layer provides:

✅ **Event System** (350 lines):
- 20+ event types for agent lifecycle, learning, research, collaboration
- Pub-sub pattern with concurrent handler execution
- Event history and statistics

✅ **Community Management** (350 lines):
- Agent registration and lifecycle
- Active agent tracking and coordination
- Promotion logic with validation
- Community-wide statistics

✅ **Matchmaking** (400 lines):
- Mentor-student pairing (graph-based)
- Collaboration partner finding
- Peer reviewer selection
- Compatibility scoring algorithm

✅ **Workflows** (550 lines):
- LangGraph state machines
- Learning workflow (read → assess → seek help)
- Research workflow (literature → hypothesis → experiment → analysis)
- Collaboration workflow (plan → execute → write → review)

**Total**: ~1,650 lines of orchestration code

This completes the core infrastructure for multi-agent coordination. The system can now:
1. Manage agent lifecycles and activities
2. Match students with mentors based on knowledge graphs
3. Orchestrate complex multi-step research workflows
4. Enable event-driven communication between all components

---

## Next Steps

After completing the orchestration layer, continue with:
1. **Test suite**: Unit and integration tests
2. **Scripts**: Seed data, run simulations, analyze results
3. **Configuration**: YAML files for curricula, templates, rubrics
4. **Data structure**: Seed agents, knowledge, curricula
