from langgraph.graph.state import CompiledStateGraph
from IPython.display import Image
import PIL.Image
from io import BytesIO
from pathlib import Path


def save_langgraph_graph(path: str, graph: CompiledStateGraph) -> None:
    mermaid = graph.get_graph().draw_mermaid_png()
    buffer = BytesIO(Image(mermaid).data)
    img = PIL.Image.open(buffer)
    current_dir = Path(__file__).resolve().parent.joinpath(path)
    print(f"Path: {path}")
    print(f"Saving graph to '{current_dir}'.")
    img.save(path)
    return None
