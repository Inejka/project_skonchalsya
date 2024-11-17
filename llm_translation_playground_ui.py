from llm_translation_engine import Engine
import streamlit as st
import translators as ts

from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever
from llm_translation_utils import get_maps_as_lagchain_documents 

import openai


st.set_page_config(layout="wide")


@st.cache_resource()
def get_engine():
    return Engine()

engine = get_engine()
vectorstore = engine.vectorstore    

def get_maps_as_event_documents_lol():
    return engine.game_files, engine.index

def get_maps_as_lagchain_documents_lol():
    return get_maps_as_lagchain_documents(engine.game_files)

@st.cache_resource()
def calculate_bm25_retriever():
    return BM25Retriever.from_documents(get_maps_as_lagchain_documents_lol())

st.session_state["bm25"] = calculate_bm25_retriever()

def search_docs():
    ensemble_retriever = EnsembleRetriever(
        retrievers=[vectorstore.as_retriever(search_kwargs={"k": 10})], weights=[1]
    )
    relevant_docs = ensemble_retriever.invoke(query)
    to_display = []
    translated_quary = ts.translate_text(query, from_language="ja", to_language="ru")
    to_display.append(translated_quary)
    _, index = get_maps_as_event_documents_lol()
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
    st.write(engine.get_context_from_query(query))


def test_model():
    docs, _ = get_maps_as_event_documents_lol()
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
            context = engine.get_context_from_query("\n".join(chunk.cleared_text))
            if len(context) > 0:
                for dialogue_chunk in context:
                    for context_chunk in dialogue_chunk:
                        messages.extend(
                            [
                                {"role": "user", "content": context_chunk[0]},
                                {"role": "assistant", "content": context_chunk[1]},
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
                messages=messages,
                model="gemini-1.5-flash",
                temperature=0,
                max_tokens=1024,
            )
            # st.write(messages)
            st.write(chat_completion.choices[0].message.content)
            # break


query = st.text_input("Query")
st.button("Search", on_click=search_docs)
st.button("Test", on_click=test_query)
st.button("Test model", on_click=test_model)
