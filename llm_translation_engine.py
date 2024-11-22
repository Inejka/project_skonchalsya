import sqlite3
from langchain_community.vectorstores import SQLiteVSS
from langchain_community.embeddings.sentence_transformer import (
    SentenceTransformerEmbeddings,
)

from langchain_core.documents import Document
from langchain.retrievers import EnsembleRetriever

from llm_translation_utils import get_maps_as_event_documents

class Engine:
    def __init__(self):
        print("Engine initialized")
        self.embedding_function = SentenceTransformerEmbeddings(
            model_name="intfloat/multilingual-e5-large", model_kwargs={"device": "cpu"}
        )
        self.vectorstore = self.get_async_vectorstore("./vss.db")
        self.game_files, self.index = get_maps_as_event_documents()

    def get_async_vectorstore(self, db_file: str) -> SQLiteVSS:
        import sqlite_vss

        connection = sqlite3.connect(db_file, check_same_thread=False)
        connection.row_factory = sqlite3.Row
        connection.enable_load_extension(True)
        sqlite_vss.load(connection)
        connection.enable_load_extension(False)
        return SQLiteVSS(
            embedding=self.embedding_function,
            table="skonchalsya",
            connection=connection,
        )

    def embed(self, documents: list[Document]) -> None:
        self.vectorstore.from_documents(documents, embedding=self.embedding_function)

    def get_context_from_query(self, query: str) -> list[list[tuple[str,str]]]:
        ensemble_retriever = EnsembleRetriever(
            retrievers=[self.vectorstore.as_retriever(search_kwargs={"k": 7})], weights=[1]
        )
        relevant_docs = ensemble_retriever.invoke(query)
        to_return = []
        for doc in relevant_docs:
            if self.index.get(doc.page_content):
                to_return.append(
                        self.index[doc.page_content].dialogue.get_part_of_dialogue(
                            self.index[doc.page_content].chunk_index, 3
                    )
                )
        return to_return

