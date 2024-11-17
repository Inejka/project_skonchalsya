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
import translators as ts

from langchain_community.embeddings.sentence_transformer import (
    SentenceTransformerEmbeddings,
)
from langchain_community.vectorstores import SQLiteVSS
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document
from langchain.retrievers import EnsembleRetriever
import openai

openai.api_key = "qq"
openai.api_base = "http://127.0.0.1:5000/v1"
openai.api_version = "2023-05-15"


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

    def get_cleared_dialogue(self) -> list[tuple[str, str]]:
        to_return = []
        for chunk in self.text_chunks:
            to_return.append(
                ("\n".join(chunk.cleared_text), "\n".join(chunk.translated_text))
            )
        return to_return

    def get_part_of_dialogue(
        self, chunk_position: int, radius: int = 5
    ) -> list[tuple[str, str]]:
        to_return = []
        for chunk in self.text_chunks[
            max(0, chunk_position - radius) : min(
                len(self.text_chunks), chunk_position + radius
            )
        ]:
            to_return.append(
                ("\n".join(chunk.cleared_text), "\n".join(chunk.translated_text))
            )
        return to_return


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


@dataclass
class RawTextPointer:
    event_document: EventDocument
    dialogue: Dialogue
    chunk: DialogueChunk
    event_document_index: int
    dialogue_index: int
    chunk_index: int


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


@st.cache_resource
def get_maps_vocabulary():
    return generate_maps_vocabulary()


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
    for item in Path(f"{SOURCE_FOLDER_JAP}/{MAPS_FOLDER}").glob("**/*.txt"):
        print(item)
        with open(item, "r", encoding="utf-8") as file:
            text = file.read()
            for word in useful_words:
                freq_map[word] += text.count(word)
    total = sum(freq_map.values())
    for word in freq_map:
        print(f"{word}: {freq_map[word]/total}")


st.set_page_config(layout="wide")


@st.cache_resource
def get_embedding_function():
    return SentenceTransformerEmbeddings(model_name="intfloat/multilingual-e5-large", model_kwargs = {'device': 'cpu'}  )


embedding_function = get_embedding_function()


@st.cache_resource()
def get_maps_as_event_documents() -> (
    tuple[list[EventDocument], dict[str, RawTextPointer]]
):
    raw_chunk_to_position = {}
    documents = []
    vocabulary = get_maps_vocabulary()
    for doc in Path(f"{FOLDER_TO_PATCH}/{MAPS_FOLDER}").glob("**/*.txt"):
        document = EventDocument(doc)
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


@st.cache_resource()
def get_maps_as_lagchain_documents():
    docs = []
    maps_as_event_documents, _ = get_maps_as_event_documents()
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
                        },
                        id=f"{doc.filename}-{chunk.start_line}-{chunk.end_line}",
                    )
                )
    return docs


@st.cache_resource()
def calculate_bm25_retriever():
    return BM25Retriever.from_documents(get_maps_as_lagchain_documents())


st.session_state["bm25"] = calculate_bm25_retriever()


@st.cache_resource()
def embed():
    vectorstore = SQLiteVSS(
        embedding=embedding_function,
        table="skonchalsya",
        db_file="./vss.db",
        connection=None,
    )
    docs = get_maps_as_lagchain_documents()
    calculate_bm25_retriever()
    vectorstore.from_documents(docs, embedding=embedding_function)


def get_async_vectorstore(db_file: str) -> sqlite3.Connection:
    import sqlite_vss

    connection = sqlite3.connect(db_file, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    connection.enable_load_extension(True)
    sqlite_vss.load(connection)
    connection.enable_load_extension(False)
    return SQLiteVSS(
        embedding=embedding_function,
        table="skonchalsya",
        connection=connection,
    )


vectorstore = get_async_vectorstore("./vss.db")


def get_context_from_query(query: str) -> list[list[tuple[str,str]]]:
    ensemble_retriever = EnsembleRetriever(
        retrievers=[vectorstore.as_retriever(search_kwargs={"k": 10})], weights=[1]
    )
    relevant_docs = ensemble_retriever.invoke(query)
    _, index = get_maps_as_event_documents()
    to_return = []
    for doc in relevant_docs:
        if index.get(doc.page_content):
            to_return.append(
                    index[doc.page_content].dialogue.get_part_of_dialogue(
                        index[doc.page_content].chunk_index
                )
            )
    return to_return


def search_docs():
    ensemble_retriever = EnsembleRetriever(
        retrievers=[vectorstore.as_retriever(search_kwargs={"k": 10})], weights=[1]
    )
    relevant_docs = ensemble_retriever.invoke(query)
    to_display = []
    translated_quary = ts.translate_text(query, from_language="ja", to_language="ru")
    to_display.append(translated_quary)
    _, index = get_maps_as_event_documents()
    for doc in relevant_docs:
        translated_doc = ts.translate_text(
            doc.page_content, from_language="ja", to_language="ru"
        )
        to_display.append(doc.page_content)
        if index.get(doc.page_content):
            to_display.append(
                index[doc.page_content].dialogue.get_part_of_dialogue(
                    index[doc.page_content].chunk_index
                )
            )
        to_display.append(translated_doc)
    st.write(to_display)


def test_query():
    st.write(get_context_from_query(query))


def test_model():
    docs, _ = get_maps_as_event_documents()
    founded = None
    for doc in docs:
        # if "Map111.txt" in str(doc.filename):
        #     founded = doc
        #     break
        if "Data/Map111.txt" in str(doc.filename):
            founded = doc
            break

    for dialogue in founded.dialogues:
        for chunk in dialogue.text_chunks:
            st.write(chunk.cleared_text)
            messages = [
                {
                    "role": "system",
                    "content": "Ты виртуальный переводчик. Твоя задача перевести сообщения пользователя с японского языка на русский. Тебе возможно будут представлены примеры перевода с японского на русский. В твоем ответе должен содержаться ТОЛЬКО ПЕРЕВОД. Перевод не должен быть дословным, но должен быть грамотным и верным. В сообщениях могут встречаться особые символы или техническая информация, их переводить нельзя",
                }
            ]
            context = get_context_from_query("\n".join(chunk.cleared_text))
            if len(context) > 0:
                for dialogue_chunk in context:
                    for context_chunk in dialogue_chunk:
                        messages.extend(
                            [
                                {
                                    "role": "user",
                                    "content": context_chunk[0]
                                }, 
                                {
                                    "role": "assistant",
                                    "content": context_chunk[1]
                                }
                        ]
                        )
            messages.append(
                {
                    "role": "user",
                    "content": "\n".join(chunk.cleared_text),
                }
            )
            client = openai.OpenAI(api_key="sk-qq", base_url="http://127.0.0.1:5000/v1")

            chat_completion = client.chat.completions.create(
                messages=messages, model="gemini-1.5-flash", temperature=0, max_tokens=1024
            )
            # st.write(messages)
            st.write(chat_completion.choices[0].message.content)
            # break


st.button("Embed", on_click=embed)
st.button("Calculate BM25", on_click=calculate_bm25_retriever)
query = st.text_input("Query")
st.button("Search", on_click=search_docs)
st.button("Test", on_click=test_query)
st.button("Test model", on_click=test_model)
