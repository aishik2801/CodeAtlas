import json
import os
import networkx as nx
from backend.parsing.code_parser import FileMetadata


class DependencyGraphBuilder:
    """Builds a dependency graph from parsed file metadata using NetworkX."""

    def __init__(self):
        self.graph = nx.DiGraph()

    def build_graph(self, parsed_files: list[FileMetadata]) -> nx.DiGraph:
        """Analyse imports across all parsed files and build a directed graph.

        Nodes = file paths.
        Edges = file A imports something defined in file B.
        """
        # Map module/file basenames to full paths for resolution
        path_lookup: dict[str, str] = {}
        for meta in parsed_files:
            basename = os.path.splitext(os.path.basename(meta.file_path))[0]
            path_lookup[basename] = meta.file_path
            # Also register by dotted path  (e.g. "services.auth")
            dotted = meta.file_path.replace("/", ".").replace("\\", ".")
            if dotted.endswith(".py"):
                dotted = dotted[:-3]
            path_lookup[dotted] = meta.file_path

        # Add nodes
        for meta in parsed_files:
            self.graph.add_node(meta.file_path, language=meta.language)

        # Add edges based on imports
        for meta in parsed_files:
            for imp in meta.imports:
                # Try to resolve import to a project file
                resolved = self._resolve_import(imp, path_lookup)
                if resolved and resolved != meta.file_path:
                    self.graph.add_edge(meta.file_path, resolved, import_name=imp)

        return self.graph

    @staticmethod
    def _resolve_import(imp: str, lookup: dict[str, str]):
        """Try to resolve an import string to a project file path."""
        # Direct match
        if imp in lookup:
            return lookup[imp]
        # Try last segment (e.g. "from services.auth import ..." → "auth")
        parts = imp.split(".")
        for i in range(len(parts)):
            candidate = ".".join(parts[i:])
            if candidate in lookup:
                return lookup[candidate]
        return None

    def to_json(self) -> dict:
        """Serialize the graph as a JSON-friendly dict."""
        nodes = [{"id": n, **self.graph.nodes[n]} for n in self.graph.nodes]
        edges = [
            {"source": u, "target": v, **d}
            for u, v, d in self.graph.edges(data=True)
        ]
        return {"nodes": nodes, "edges": edges}

    def save_json(self, path: str = "data/dependency_graph.json"):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_json(), f, indent=2)

    def to_plotly_figure(self):
        """Generate an interactive Plotly figure of the dependency graph."""
        import plotly.graph_objects as go

        pos = nx.spring_layout(self.graph, k=2, seed=42)

        # Edge traces
        edge_x, edge_y = [], []
        for u, v in self.graph.edges():
            x0, y0 = pos[u]
            x1, y1 = pos[v]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])

        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=1, color="#888"),
            hoverinfo="none",
            mode="lines",
        )

        # Node traces
        node_x = [pos[n][0] for n in self.graph.nodes()]
        node_y = [pos[n][1] for n in self.graph.nodes()]
        node_text = [os.path.basename(n) for n in self.graph.nodes()]
        node_hover = [n for n in self.graph.nodes()]
        connections = [self.graph.degree(n) for n in self.graph.nodes()]

        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode="markers+text",
            text=node_text,
            textposition="top center",
            hovertext=node_hover,
            hoverinfo="text",
            marker=dict(
                size=10,
                color=connections,
                colorscale="Viridis",
                colorbar=dict(title="Connections"),
                line=dict(width=1, color="#333"),
            ),
        )

        fig = go.Figure(
            data=[edge_trace, node_trace],
            layout=go.Layout(
                title="Dependency Graph",
                showlegend=False,
                hovermode="closest",
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                plot_bgcolor="#0e1117",
                paper_bgcolor="#0e1117",
                font=dict(color="white"),
                margin=dict(l=20, r=20, t=50, b=20),
            ),
        )
        return fig
