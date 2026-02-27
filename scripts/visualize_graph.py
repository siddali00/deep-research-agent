"""Generate a visual diagram of the LangGraph research workflow.

Usage:
    python scripts/visualize_graph.py

Output:
    docs/langgraph_diagram.png
"""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.graphs.research_graph import build_research_graph


def main():
    graph = build_research_graph()
    
    output_dir = Path("docs")
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / "langgraph_diagram.png"
    
    try:
        png_data = graph.get_graph().draw_mermaid_png()
        output_path.write_bytes(png_data)
        print(f"✓ Graph diagram saved to: {output_path}")
        print(f"  View it in VS Code or any image viewer")
    except Exception as e:
        print(f"✗ Failed to generate diagram: {e}")
        print(f"  Make sure you have: pip install grandalf")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
