from pathlib import Path
from translate import generate_maps_vocabulary
from llm_translation_core_data_classes import GameFile, RawTextPointer
from translate import FOLDER_TO_PATCH, MAPS_FOLDER

from langchain_core.documents import Document

def get_maps_as_event_documents() -> tuple[list[GameFile], dict[str, RawTextPointer]]:
    raw_chunk_to_position = {}
    documents = []
    vocabulary = generate_maps_vocabulary()
    for doc in Path(f"{FOLDER_TO_PATCH}/{MAPS_FOLDER}").glob("**/*.txt"):
        document = GameFile(doc)
        documents.append(document)
        for i in range(len(document.dialogues)):
            for j in range(len(document.dialogues[i].text_chunks)):
                if vocabulary.get(document.dialogues[i].text_chunks[j].raw_text):
                    document.dialogues[i].text_chunks[j].set_translation(
                        vocabulary[document.dialogues[i].text_chunks[j].raw_text]
                    )
                raw_chunk_to_position[
                    "\n".join(document.dialogues[i].text_chunks[j].cleared_text)
                ] = RawTextPointer(
                    document,
                    document.dialogues[i],
                    document.dialogues[i].text_chunks[j],
                    len(documents) - 1,
                    i,
                    j,
                )
    return documents, raw_chunk_to_position


def get_maps_as_lagchain_documents(maps_as_event_documents: list[GameFile]) -> list[Document]:
    docs = []
    for doc in maps_as_event_documents:
        for dialogue in doc.dialogues:
            for chunk in dialogue.text_chunks:
                docs.append(
                    Document(
                        "\n".join(chunk.cleared_text),
                        metadata={
                            "file": str(doc.filename),
                            "start_line": chunk.start_line,
                            "end_line": chunk.end_line,
                            "translated": str(chunk.is_translated()),
                            "translation": chunk.raw_translated_text,
                        },
                        id=f"{doc.filename}-{chunk.start_line}-{chunk.end_line}",
                    )
                )
    return docs
