from langchain_postgres import PGVector
from langchain_community.embeddings.sentence_transformer import (
    SentenceTransformerEmbeddings,
)

from langchain_core.documents import Document
from langchain.retrievers import EnsembleRetriever
from llm_translation_utils import get_maps_as_event_documents

connection = "postgresql+psycopg://langchain:langchain@localhost:6024/langchain"  # Uses psycopg3!
collection_name = "skonchalsya"


class Engine:
    def __init__(self):
        print("Engine initialized")
        self.embedding_function = SentenceTransformerEmbeddings(
            model_name="intfloat/multilingual-e5-large"
        )
        self.vectorstore = PGVector(
            embeddings=self.embedding_function,
            collection_name=collection_name,
            connection=connection,
            use_jsonb=True,
        )
        self.game_files, self.index = get_maps_as_event_documents()

    def embed(self, documents: list[Document]) -> None:
        self.vectorstore.from_documents(
            documents,
            embedding=self.embedding_function,
            connection=connection,
            collection_name=collection_name,
            use_jsonb=True,
        )

    def get_context_from_query(self, query: str) -> list[list[tuple[str, str]]]:
        ensemble_retriever = EnsembleRetriever(
            retrievers=[self.vectorstore.as_retriever(search_kwargs={"k": 7, "filter": {"translated": {"$eq": "True"}}},)],
            weights=[1],
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