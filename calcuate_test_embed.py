from llm_translation_utils import (
    get_maps_as_event_documents,
    get_maps_as_lagchain_documents,
)
from llm_translation_engine import Engine
from langchain_community.embeddings.sentence_transformer import (
    SentenceTransformerEmbeddings,
)
import sqlite3
from langchain_community.vectorstores import SQLiteVSS

engine = Engine()

# con = sqlite3.connect("./vss.db")
# cur = con.cursor()
# test = cur.execute("SELECT metadata FROM skonchalsya LIMIT 10").fetchall()
# for i in test:
#     print(i)

# vectorstore = SQLiteVSS(
#     embedding=SentenceTransformerEmbeddings(
#         model_name="intfloat/multilingual-e5-large"
#     ),
#     connection=None,
#     table="skonchalsya",
#     db_file="./vss.db",
# )

# maps, _ = get_maps_as_event_documents()
# documents = get_maps_as_lagchain_documents(maps)
# texts = [d.page_content for d in documents]
# metadatas = [d.metadata for d in documents]


# ids = [doc.id for doc in documents]

# kwargs = {}
# if any(ids):
#     kwargs["ids"] = ids

# vectorstore.from_texts(
#     texts,
#     embedding=SentenceTransformerEmbeddings(
#         model_name="intfloat/multilingual-e5-large"
#     ),
#     table="skonchalsya",
#     metadatas=metadatas,
#     **kwargs,
# )

for dialogue_chunk in engine.get_context_from_query("【ルカ・キリエ】 ドッペル達、村を制圧しなさい！ ここにいる者は、みな敵よ！"):
    for context_chunk in dialogue_chunk:
        print(context_chunk)
