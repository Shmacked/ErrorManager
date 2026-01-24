from langgraph.graph.state import CompiledStateGraph
from IPython.display import Image
import PIL.Image
from io import BytesIO


def save_langgraph_graph(path: str, graph: CompiledStateGraph) -> None:
    mermaid = graph.get_graph().draw_mermaid_png()
    buffer = BytesIO(Image(mermaid).data)
    img = PIL.Image.open(buffer)
    print(f"Saving graph to '{path}'.")
    img.save(path)
    return None
