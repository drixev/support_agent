import re
import uuid

from support_agent.domain.rag import Chunk

_HEADER = re.compile(r"^(#{1,3})\s+(.*)$", re.MULTILINE)
_NAMESPACE = uuid.UUID("6f1c2a52-1b7e-4c1a-9d3e-5a8f0c2b7e11")


def split_section(markdown: str) -> list[tuple[str, str]]:
    """Divide por headers H1 - H3 -> [(titulo, cuerpo)]."""
    matches = list(_HEADER.finditer(markdown))
    if not matches:
        return [("", markdown)]
    sections = [("", markdown[:matches[0].start()])] if matches[0].start() > 0 else []
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i +1 < len(matches) else len(markdown)
        sections.append((m.group(2).strip(), markdown[m.end() : end]))
    
    return sections


def chunk_markdown(
    doc_id: str, markdown: str, max_words: int = 200, overlap: int = 40
):
    if not 0 <= overlap < max_words:
        raise ValueError("overlap must be in [0, maxwords)")
    step = max_words - overlap
    chunks: list[Chunk] = []
    for title, body in split_section(markdown):
        words = body.split()
        for start in range(0, len(words), step):
            window = " ".join(words[start: start + max_words])
            text = f"{title}\n{window}" if title else window
            chunk_id = str(uuid.uuid5(_NAMESPACE, f"{doc_id}:{len(chunks)}"))
            chunks.append(Chunk(chunk_id, doc_id, text, {"section": title}))
            if start + max_words >= len(words):
                break
    
    return chunks
    
    
