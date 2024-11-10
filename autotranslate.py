from dataclasses import dataclass
from pathlib import Path
import re
import sqlite3
from translate import (
    FOLDER_TO_PATCH,
    MAPS_FOLDER,
    SOURCE_FOLDER_JAP,
    generate_maps_vocabulary,
    useful_words,
)
import streamlit as st
import numpy as np
import pandas as pd

from langchain_community.embeddings.sentence_transformer import (
    SentenceTransformerEmbeddings,
)
from langchain_community.vectorstores import SQLiteVSS
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document
from langchain.retrievers import EnsembleRetriever

st.set_page_config(layout="wide")


embedding_function = SentenceTransformerEmbeddings(
    model_name="intfloat/multilingual-e5-large"
)

def keep_line(line):
    if "ShowText(" in line:
        return True
    return False


DIALOGUE_START_SPLITTERS = []
DIALOGUE_END_SPLITTERS = [
    "JumpToLabel",
    "BranchEnd",
    "Page",
    "Label",
    " Name = ",
    "CommonEvent",
    "ConditionalBranch",
    "JumpToLabel",
]


def is_of_(line, splitters):
    for splitter in splitters:
        if splitter in line:
            return True
    return False


def is_start_of_dialogue(line):
    return is_of_(line, DIALOGUE_START_SPLITTERS)


def is_end_of_dialogue(line):
    return is_of_(line, DIALOGUE_END_SPLITTERS)


def get_indents(line):
    return len(line) - len(line.lstrip())


@dataclass
class DialogueChunk:
    raw_text: str
    start_line: int
    end_line: int
    translated_text: list[str]
    cleared_text: list[str]
    raw_translated_text: str = ""

    def clear_text(self):
        for line in self.raw_text.split("\n"):
            self.cleared_text.append(re.match(r"\W*ShowText\(\[\"(.*)\"\]\)", line)[1])

    def clear_translated_text(self):
        # try:
        for line in self.raw_translated_text.split("\n"):
            self.translated_text.append(
                re.match(r"\W*ShowText\(\[\"(.*)\"\]\)", line)[1]
            )
        # except TypeError:
        #     print("NIGGER")
        #     print(self.raw_text)
        #     print(self.raw_translated_text)

    def __post_init__(self):
        self.clear_text()

    def set_translation(self, translation: str):
        self.raw_translated_text = translation
        self.clear_translated_text()


@dataclass
class Dialogue:
    text_chunks: list[DialogueChunk]
    source_file: Path
    # childs: list["Dialogue"]


class EventDocument:
    def __init__(self, filename: Path) -> None:
        self.filename = filename
        with open(filename, "r", encoding="utf-8") as file:
            self.text = file.read()
        self.text_splitted = self.text.split("\n")
        self.dialogues = [Dialogue([], filename)]
        self.generate_dialogues()

    def generate_dialogues(self):
        i = 0
        while i < len(self.text_splitted):
            if keep_line(self.text_splitted[i]):
                indent = get_indents(self.text_splitted[i])
                start_index = i
                while (
                    i < len(self.text_splitted)
                    and keep_line(self.text_splitted[i])
                    and get_indents(self.text_splitted[i]) == indent
                ):
                    i += 1
                self.dialogues[-1].text_chunks.append(
                    DialogueChunk(
                        "\n".join(self.text_splitted[start_index:i]),
                        start_index,
                        i - 1,
                        [],
                        [],
                    )
                )
                if (
                    is_end_of_dialogue(self.text_splitted[i])
                    or get_indents(self.text_splitted[i]) is not indent
                ):
                    self.dialogues.append(Dialogue([], self.filename))
            else:
                if (
                    is_end_of_dialogue(self.text_splitted[i])
                    and len(self.dialogues[-1].text_chunks) > 0
                ):
                    self.dialogues.append(Dialogue([], self.filename))
                i += 1


def main():
    i = 0
    lenmax = 0
    documents = []
    for item in Path(f"{SOURCE_FOLDER_JAP}/{MAPS_FOLDER}").glob("**/*.txt"):
        print(item)
        documents.append(EventDocument(item))
        print(documents[-1].dialogues)
        i += 1
        for dialogue in documents[-1].dialogues:
            summm = sum(len(chunk.raw_text) for chunk in dialogue.text_chunks)
            lenmax = max(lenmax, summm)
    print(lenmax)


def translate_chunks():
    vocabulary = {}
    vocabulary = generate_maps_vocabulary()  # uses simple_vocabulary instead
    global_translations = 0
    global_chunks = 0
    for item in Path(f"{FOLDER_TO_PATCH}/{MAPS_FOLDER}").glob("**/*.txt"):
        doc = EventDocument(item)
        for dialogue in doc.dialogues:
            translated_chunks = 0
            for chunk in dialogue.text_chunks:
                if vocabulary.get(chunk.raw_text):
                    chunk.set_translation(vocabulary[chunk.raw_text])
                    translated_chunks += 1
                    global_translations += 1
            global_chunks += len(dialogue.text_chunks)

    print(f"{item}: {global_translations}/{global_chunks} chunks translated")
    return


# check the percentage of lines with useful words out of all lines with useful words
def check_useful_words_percentage():
    freq_map = {i: 0 for i in useful_words}
    total_lines = 0
    for item in Path(f"{SOURCE_FOLDER_JAP}/{MAPS_FOLDER}").glob("**/*.txt"):
        print(item)
        with open(item, "r", encoding="utf-8") as file:
            text = file.read()
            for word in useful_words:
                freq_map[word] += text.count(word)
    total = sum(freq_map.values())
    for word in freq_map:
        print(f"{word}: {freq_map[word]/total}")

@st.cache_resource()
def embed():
    vectorstore = SQLiteVSS(
        embedding=embedding_function,
        table="skonchalsya",
        db_file="./vss.db",
        connection=None
    )
    docs = []
    for doc in Path(f"{SOURCE_FOLDER_JAP}/{MAPS_FOLDER}").glob("**/*.txt"):
        doc = EventDocument(doc)
        for dialogue in doc.dialogues:
            for chunk in dialogue.text_chunks:
                docs.append(
                    Document(
                        "\n".join(chunk.cleared_text),
                        metadata={
                            "file": str(doc.filename),
                            "start_line": chunk.start_line,
                            "end_line": chunk.end_line,
                        },
                        id=f"{doc.filename}-{chunk.start_line}-{chunk.end_line}",
                    )
                )
    bm25 = BM25Retriever.from_documents(docs)
    vectorstore.from_documents(docs, embedding=embedding_function)
    st.session_state["bm25"] = bm25

def search_docs():
    vectorstore = SQLiteVSS(
        embedding=embedding_function,
        table="skonchalsya",
        db_file="./vss.db",
        connection=None
    )
    ensemble_retriever = EnsembleRetriever(
    retrievers=[st.session_state["bm25"], vectorstore.as_retriever(search_kwargs={"k": 10})], 
    weights=[0.3, 0.7])
    relevant_docs = ensemble_retriever.invoke(query)
    st.write(relevant_docs)

st.button("Embed", on_click=embed)


query = st.text_input("Query")


st.button("Search", on_click=search_docs)

if __name__ == "__main__":
    # check_useful_words_percentage()
    translate_chunks()
