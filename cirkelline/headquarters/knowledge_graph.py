"""
Knowledge Graph (NetworkX)
==========================
Graph-based knowledge representation for Cirkelline agents.

Uses NetworkX for:
- Agent relationship mapping
- Knowledge entity connections
- Tool capability graphs
- Causal reasoning chains

Node Types:
- AGENT: AI agents in the system
- TOOL: Tools available to agents
- KNOWLEDGE: Knowledge entities
- MISSION: Active missions
- USER: User context nodes

Edge Types:
- HAS_TOOL: Agent → Tool
- KNOWS: Agent → Knowledge
- WORKS_ON: Agent → Mission
- REQUIRES: Mission → Knowledge
- CAUSES: Knowledge → Knowledge (causal)
"""

import json
import logging
from enum import Enum
from typing import Optional, Dict, Any, List, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import uuid

try:
    import networkx as nx
except ImportError:
    nx = None

try:
    import redis.asyncio as aioredis
except ImportError:
    aioredis = None

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# NODE & EDGE TYPES
# ═══════════════════════════════════════════════════════════════════════════════

class NodeType(str, Enum):
    """Types of nodes in the knowledge graph."""
    AGENT = "agent"
    TOOL = "tool"
    KNOWLEDGE = "knowledge"
    MISSION = "mission"
    USER = "user"
    CONCEPT = "concept"
    DOCUMENT = "document"
    SESSION = "session"


class EdgeType(str, Enum):
    """Types of relationships between nodes."""
    # Agent relationships
    HAS_TOOL = "has_tool"
    KNOWS = "knows"
    WORKS_ON = "works_on"
    COLLABORATES = "collaborates"
    DELEGATES_TO = "delegates_to"

    # Knowledge relationships
    REQUIRES = "requires"
    CAUSES = "causes"
    RELATES_TO = "relates_to"
    PART_OF = "part_of"
    DERIVES_FROM = "derives_from"

    # Mission relationships
    ASSIGNED_TO = "assigned_to"
    DEPENDS_ON = "depends_on"
    PRODUCES = "produces"

    # User relationships
    OWNS = "owns"
    PREFERS = "prefers"
    CREATED = "created"


# ═══════════════════════════════════════════════════════════════════════════════
# NODE DATA CLASS
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class GraphNode:
    """
    Node in the knowledge graph.

    Attributes:
        node_id: Unique identifier
        node_type: Category of node
        name: Human-readable name
        properties: Additional metadata
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """
    node_id: str
    node_type: NodeType
    name: str
    properties: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "node_id": self.node_id,
            "node_type": self.node_type.value if isinstance(self.node_type, NodeType) else self.node_type,
            "name": self.name,
            "properties": self.properties,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GraphNode":
        """Reconstruct from dictionary."""
        return cls(
            node_id=data["node_id"],
            node_type=NodeType(data["node_type"]) if data["node_type"] in [n.value for n in NodeType] else data["node_type"],
            name=data["name"],
            properties=data.get("properties", {}),
            created_at=data.get("created_at", datetime.utcnow().isoformat()),
            updated_at=data.get("updated_at", datetime.utcnow().isoformat()),
        )


@dataclass
class GraphEdge:
    """
    Edge (relationship) in the knowledge graph.

    Attributes:
        source_id: Source node ID
        target_id: Target node ID
        edge_type: Type of relationship
        weight: Strength/confidence of relationship
        properties: Additional metadata
    """
    source_id: str
    target_id: str
    edge_type: EdgeType
    weight: float = 1.0
    properties: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "edge_type": self.edge_type.value if isinstance(self.edge_type, EdgeType) else self.edge_type,
            "weight": self.weight,
            "properties": self.properties,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# KNOWLEDGE GRAPH
# ═══════════════════════════════════════════════════════════════════════════════

class KnowledgeGraph:
    """
    NetworkX-based knowledge graph for agent orchestration.

    Features:
    - Multi-graph with typed nodes and edges
    - Persistence to Redis for distributed access
    - Query capabilities (path finding, neighbors, subgraphs)
    - Visualization export
    """

    REDIS_KEY = "cirkelline:knowledge_graph"

    def __init__(self, redis_url: Optional[str] = None):
        if nx is None:
            raise ImportError("networkx is required: pip install networkx")

        self._graph: nx.MultiDiGraph = nx.MultiDiGraph()
        self._redis_url = redis_url
        self._redis: Optional[aioredis.Redis] = None
        self._node_index: Dict[str, GraphNode] = {}

    async def connect_redis(self) -> bool:
        """Connect to Redis for persistence."""
        if aioredis is None or not self._redis_url:
            return False

        try:
            self._redis = aioredis.from_url(
                self._redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
            await self._redis.ping()
            logger.info("KnowledgeGraph connected to Redis")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            return False

    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self._redis:
            await self._redis.close()
            self._redis = None

    # ═══════════════════════════════════════════════════════════════════════════
    # NODE OPERATIONS
    # ═══════════════════════════════════════════════════════════════════════════

    def add_node(self, node: GraphNode) -> str:
        """
        Add a node to the graph.

        Args:
            node: GraphNode to add

        Returns:
            Node ID
        """
        self._graph.add_node(
            node.node_id,
            node_type=node.node_type.value if isinstance(node.node_type, NodeType) else node.node_type,
            name=node.name,
            properties=node.properties,
            created_at=node.created_at,
            updated_at=node.updated_at,
        )
        self._node_index[node.node_id] = node
        return node.node_id

    def get_node(self, node_id: str) -> Optional[GraphNode]:
        """Get a node by ID."""
        if node_id in self._node_index:
            return self._node_index[node_id]

        if node_id in self._graph.nodes:
            data = self._graph.nodes[node_id]
            return GraphNode(
                node_id=node_id,
                node_type=data.get("node_type", "unknown"),
                name=data.get("name", ""),
                properties=data.get("properties", {}),
                created_at=data.get("created_at", ""),
                updated_at=data.get("updated_at", ""),
            )
        return None

    def remove_node(self, node_id: str) -> bool:
        """Remove a node and all its edges."""
        if node_id in self._graph.nodes:
            self._graph.remove_node(node_id)
            self._node_index.pop(node_id, None)
            return True
        return False

    def update_node(self, node_id: str, properties: Dict[str, Any]) -> bool:
        """Update node properties."""
        if node_id in self._graph.nodes:
            self._graph.nodes[node_id]["properties"].update(properties)
            self._graph.nodes[node_id]["updated_at"] = datetime.utcnow().isoformat()

            if node_id in self._node_index:
                self._node_index[node_id].properties.update(properties)
                self._node_index[node_id].updated_at = datetime.utcnow().isoformat()

            return True
        return False

    def get_nodes_by_type(self, node_type: NodeType) -> List[GraphNode]:
        """Get all nodes of a specific type."""
        type_value = node_type.value if isinstance(node_type, NodeType) else node_type
        nodes = []

        for node_id, data in self._graph.nodes(data=True):
            if data.get("node_type") == type_value:
                nodes.append(GraphNode(
                    node_id=node_id,
                    node_type=data.get("node_type"),
                    name=data.get("name", ""),
                    properties=data.get("properties", {}),
                ))

        return nodes

    # ═══════════════════════════════════════════════════════════════════════════
    # EDGE OPERATIONS
    # ═══════════════════════════════════════════════════════════════════════════

    def add_edge(self, edge: GraphEdge) -> bool:
        """
        Add an edge between nodes.

        Args:
            edge: GraphEdge to add

        Returns:
            True if successful
        """
        if edge.source_id not in self._graph.nodes:
            logger.warning(f"Source node {edge.source_id} not found")
            return False
        if edge.target_id not in self._graph.nodes:
            logger.warning(f"Target node {edge.target_id} not found")
            return False

        self._graph.add_edge(
            edge.source_id,
            edge.target_id,
            edge_type=edge.edge_type.value if isinstance(edge.edge_type, EdgeType) else edge.edge_type,
            weight=edge.weight,
            properties=edge.properties,
        )
        return True

    def get_edges(
        self,
        source_id: Optional[str] = None,
        target_id: Optional[str] = None,
        edge_type: Optional[EdgeType] = None,
    ) -> List[GraphEdge]:
        """Get edges matching criteria."""
        edges = []
        type_value = edge_type.value if edge_type else None

        for src, tgt, data in self._graph.edges(data=True):
            if source_id and src != source_id:
                continue
            if target_id and tgt != target_id:
                continue
            if type_value and data.get("edge_type") != type_value:
                continue

            edges.append(GraphEdge(
                source_id=src,
                target_id=tgt,
                edge_type=data.get("edge_type"),
                weight=data.get("weight", 1.0),
                properties=data.get("properties", {}),
            ))

        return edges

    def remove_edge(
        self,
        source_id: str,
        target_id: str,
        edge_type: Optional[EdgeType] = None,
    ) -> bool:
        """Remove an edge between nodes."""
        try:
            if edge_type:
                # Remove specific edge type
                type_value = edge_type.value if isinstance(edge_type, EdgeType) else edge_type
                keys_to_remove = []
                for key, data in self._graph[source_id][target_id].items():
                    if data.get("edge_type") == type_value:
                        keys_to_remove.append(key)

                for key in keys_to_remove:
                    self._graph.remove_edge(source_id, target_id, key=key)
            else:
                # Remove all edges between nodes
                self._graph.remove_edge(source_id, target_id)

            return True
        except (KeyError, nx.NetworkXError):
            return False

    # ═══════════════════════════════════════════════════════════════════════════
    # QUERY OPERATIONS
    # ═══════════════════════════════════════════════════════════════════════════

    def get_neighbors(
        self,
        node_id: str,
        edge_type: Optional[EdgeType] = None,
        direction: str = "out",
    ) -> List[GraphNode]:
        """
        Get neighboring nodes.

        Args:
            node_id: Source node
            edge_type: Filter by edge type
            direction: "out", "in", or "both"

        Returns:
            List of neighboring nodes
        """
        if node_id not in self._graph.nodes:
            return []

        neighbor_ids: Set[str] = set()

        if direction in ("out", "both"):
            for _, target, data in self._graph.out_edges(node_id, data=True):
                if edge_type is None or data.get("edge_type") == edge_type.value:
                    neighbor_ids.add(target)

        if direction in ("in", "both"):
            for source, _, data in self._graph.in_edges(node_id, data=True):
                if edge_type is None or data.get("edge_type") == edge_type.value:
                    neighbor_ids.add(source)

        return [self.get_node(nid) for nid in neighbor_ids if self.get_node(nid)]

    def find_path(
        self,
        source_id: str,
        target_id: str,
    ) -> Optional[List[str]]:
        """Find shortest path between nodes."""
        try:
            return nx.shortest_path(self._graph, source_id, target_id)
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return None

    def get_subgraph(
        self,
        center_id: str,
        depth: int = 2,
    ) -> "KnowledgeGraph":
        """
        Extract subgraph around a center node.

        Args:
            center_id: Center node ID
            depth: How many hops to include

        Returns:
            New KnowledgeGraph with subgraph
        """
        if center_id not in self._graph.nodes:
            return KnowledgeGraph()

        # BFS to find nodes within depth
        nodes_to_include = {center_id}
        frontier = {center_id}

        for _ in range(depth):
            new_frontier = set()
            for node in frontier:
                new_frontier.update(self._graph.predecessors(node))
                new_frontier.update(self._graph.successors(node))
            nodes_to_include.update(new_frontier)
            frontier = new_frontier

        # Create subgraph
        subgraph = KnowledgeGraph()
        subgraph._graph = self._graph.subgraph(nodes_to_include).copy()

        return subgraph

    def search_nodes(
        self,
        query: str,
        node_type: Optional[NodeType] = None,
        limit: int = 10,
    ) -> List[GraphNode]:
        """
        Search nodes by name or properties.

        Args:
            query: Search string
            node_type: Filter by type
            limit: Max results

        Returns:
            List of matching nodes
        """
        query_lower = query.lower()
        results = []

        for node_id, data in self._graph.nodes(data=True):
            if node_type:
                type_value = node_type.value if isinstance(node_type, NodeType) else node_type
                if data.get("node_type") != type_value:
                    continue

            # Search in name
            name = data.get("name", "")
            if query_lower in name.lower():
                results.append(GraphNode(
                    node_id=node_id,
                    node_type=data.get("node_type"),
                    name=name,
                    properties=data.get("properties", {}),
                ))
                continue

            # Search in properties
            props = data.get("properties", {})
            for value in props.values():
                if isinstance(value, str) and query_lower in value.lower():
                    results.append(GraphNode(
                        node_id=node_id,
                        node_type=data.get("node_type"),
                        name=name,
                        properties=props,
                    ))
                    break

            if len(results) >= limit:
                break

        return results[:limit]

    # ═══════════════════════════════════════════════════════════════════════════
    # AGENT-SPECIFIC HELPERS
    # ═══════════════════════════════════════════════════════════════════════════

    def register_agent(
        self,
        agent_id: str,
        name: str,
        capabilities: List[str],
        tools: List[str] = None,
    ) -> str:
        """
        Register an agent in the graph.

        Args:
            agent_id: Unique agent ID
            name: Agent name
            capabilities: List of capability strings
            tools: List of tool names

        Returns:
            Agent node ID
        """
        agent_node = GraphNode(
            node_id=agent_id,
            node_type=NodeType.AGENT,
            name=name,
            properties={
                "capabilities": capabilities,
                "status": "registered",
                "registered_at": datetime.utcnow().isoformat(),
            },
        )
        self.add_node(agent_node)

        # Add tool connections
        if tools:
            for tool_name in tools:
                tool_id = f"tool:{tool_name}"

                # Ensure tool node exists
                if tool_id not in self._graph.nodes:
                    tool_node = GraphNode(
                        node_id=tool_id,
                        node_type=NodeType.TOOL,
                        name=tool_name,
                        properties={},
                    )
                    self.add_node(tool_node)

                # Connect agent to tool
                self.add_edge(GraphEdge(
                    source_id=agent_id,
                    target_id=tool_id,
                    edge_type=EdgeType.HAS_TOOL,
                ))

        return agent_id

    def get_agent_tools(self, agent_id: str) -> List[GraphNode]:
        """Get all tools available to an agent."""
        return self.get_neighbors(agent_id, EdgeType.HAS_TOOL, direction="out")

    def find_agents_with_capability(self, capability: str) -> List[GraphNode]:
        """Find agents that have a specific capability."""
        agents = []

        for node_id, data in self._graph.nodes(data=True):
            if data.get("node_type") != NodeType.AGENT.value:
                continue

            caps = data.get("properties", {}).get("capabilities", [])
            if capability in caps:
                agents.append(GraphNode(
                    node_id=node_id,
                    node_type=data.get("node_type"),
                    name=data.get("name", ""),
                    properties=data.get("properties", {}),
                ))

        return agents

    # ═══════════════════════════════════════════════════════════════════════════
    # PERSISTENCE
    # ═══════════════════════════════════════════════════════════════════════════

    async def save(self) -> bool:
        """Save graph to Redis."""
        if not self._redis:
            logger.warning("Redis not connected - cannot save")
            return False

        try:
            # Serialize graph
            data = {
                "nodes": [],
                "edges": [],
            }

            for node_id, attrs in self._graph.nodes(data=True):
                data["nodes"].append({
                    "node_id": node_id,
                    **attrs,
                })

            for src, tgt, attrs in self._graph.edges(data=True):
                data["edges"].append({
                    "source_id": src,
                    "target_id": tgt,
                    **attrs,
                })

            await self._redis.set(
                self.REDIS_KEY,
                json.dumps(data),
            )

            logger.info(f"Saved graph: {len(data['nodes'])} nodes, {len(data['edges'])} edges")
            return True

        except Exception as e:
            logger.error(f"Failed to save graph: {e}")
            return False

    async def load(self) -> bool:
        """Load graph from Redis."""
        if not self._redis:
            return False

        try:
            data_str = await self._redis.get(self.REDIS_KEY)
            if not data_str:
                return False

            data = json.loads(data_str)

            # Clear current graph
            self._graph.clear()
            self._node_index.clear()

            # Load nodes
            for node_data in data.get("nodes", []):
                node_id = node_data.pop("node_id")
                self._graph.add_node(node_id, **node_data)

            # Load edges
            for edge_data in data.get("edges", []):
                src = edge_data.pop("source_id")
                tgt = edge_data.pop("target_id")
                self._graph.add_edge(src, tgt, **edge_data)

            logger.info(f"Loaded graph: {self._graph.number_of_nodes()} nodes, {self._graph.number_of_edges()} edges")
            return True

        except Exception as e:
            logger.error(f"Failed to load graph: {e}")
            return False

    def to_dict(self) -> Dict[str, Any]:
        """Export graph as dictionary."""
        return {
            "nodes": [
                {"node_id": nid, **data}
                for nid, data in self._graph.nodes(data=True)
            ],
            "edges": [
                {"source_id": src, "target_id": tgt, **data}
                for src, tgt, data in self._graph.edges(data=True)
            ],
            "stats": {
                "node_count": self._graph.number_of_nodes(),
                "edge_count": self._graph.number_of_edges(),
            },
        }

    @property
    def node_count(self) -> int:
        """Get number of nodes."""
        return self._graph.number_of_nodes()

    @property
    def edge_count(self) -> int:
        """Get number of edges."""
        return self._graph.number_of_edges()


# ═══════════════════════════════════════════════════════════════════════════════
# SINGLETON ACCESS
# ═══════════════════════════════════════════════════════════════════════════════

_knowledge_graph_instance: Optional[KnowledgeGraph] = None


def get_knowledge_graph(redis_url: Optional[str] = None) -> KnowledgeGraph:
    """
    Get the singleton KnowledgeGraph instance.

    Args:
        redis_url: Optional Redis URL for persistence

    Returns:
        KnowledgeGraph singleton instance
    """
    global _knowledge_graph_instance

    if _knowledge_graph_instance is None:
        _knowledge_graph_instance = KnowledgeGraph(redis_url=redis_url)

    return _knowledge_graph_instance


async def init_knowledge_graph(redis_url: str = "redis://localhost:6379/0") -> KnowledgeGraph:
    """Initialize and connect the knowledge graph."""
    graph = get_knowledge_graph(redis_url)
    await graph.connect_redis()
    await graph.load()
    return graph
