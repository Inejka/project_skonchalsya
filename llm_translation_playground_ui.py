from game_types import Actor
from llm_translation_engine import Engine
import streamlit as st
import translators as ts

from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever
from llm_translation_utils import get_maps_as_lagchain_documents 
from llm_translation_core_data_classes import Dialogue
import openai
import MeCab
import ahocorasick

from langchain_core.documents import Document
from translate import FOLDER_TO_PATCH


st.set_page_config(layout="wide")


@st.cache_resource()
def get_engine():
    return Engine()

engine = get_engine()
vectorstore = engine.vectorstore    

def get_maps_as_lagchain_documents_lol():
    return get_maps_as_lagchain_documents(engine.game_files)

@st.cache_resource()
def get_mecab():
    return MeCab.Tagger("-Owakati")

@st.cache_resource()
def calculate_bm25_retriever():
    with open('terms_folder/Actors_j.txt', 'r', encoding='utf-8') as file:
        new_lines = file.readlines()
        actors = Actor.parse(new_lines)
    documents = [Document(actor.name[1: -1], metadata={"idtf": actor.idtf, "type": "Actor"}) for actor in actors]
    for doc in documents:
        splitted_len = len(get_mecab().parse(doc.page_content).split())
        if splitted_len > 1:
            print(doc.page_content, splitted_len)
    return BM25Retriever.from_documents(documents, preprocess_func=get_mecab().parse)

@st.cache_resource()
def get_terms_mapping():
    map = {}
    with open('terms_folder/Actors_r.txt', 'r', encoding='utf-8') as file:
        new_lines = file.readlines()
        actors = Actor.parse(new_lines)
    map["Actor"] = {actor.idtf: actor.name[1: -1] for actor in actors}
    return map

st.session_state["bm25"] = calculate_bm25_retriever()

@st.cache_resource()
def get_automation():
    with open('terms_folder/Actors_j.txt', 'r', encoding='utf-8') as file:
        new_lines = file.readlines()
        actors = Actor.parse(new_lines)
    
    automaton = ahocorasick.Automaton()
    for idx, actor in enumerate(actors):
        automaton.add_word(actor.name[1: -1], idx)

    # Finalize the automaton
    automaton.make_automaton()
    return automaton, actors

def search_docs():
    ensemble_retriever = EnsembleRetriever(
        # retrievers=[vectorstore.as_retriever(search_kwargs={"k": 10})], weights=[1]
        retrievers=[st.session_state["bm25"]], weights=[1]
    )
    to_display = []
    # mapa = get_terms_mapping()
    # for word in get_mecab().parse(query).split():
    #     relevant_docs = ensemble_retriever.invoke(word)
    #     for doc in relevant_docs:
    #         if doc.page_content == word:
    #             to_display.append((doc.page_content, doc.metadata["type"], doc.metadata["idtf"]))
    #             to_display.append(mapa[doc.metadata["type"]][doc.metadata["idtf"]])
    # for doc in ensemble_retriever.invoke(query):
    #     to_display.append(doc.page_content)
    results = set()
    automation, actors = get_automation()
    for end_pos, string_idx in automation.iter(query):
        st.write(actors[string_idx].name[1: -1])
        # results.add(actors[string_idx])

    
    st.write(results)
    
    # translated_quary = ts.translate_text(query, from_language="ja", to_language="ru")
    # to_display.append(translated_quary)
    # index = engine.index
    # for doc in relevant_docs:
    #     translated_doc = ts.translate_text(
    #         doc.page_content, from_language="ja", to_language="ru"
    #     )
    #     to_display.append(doc.page_content)
    #     to_display.append(doc.metadata)
    #     if index.get(doc.page_content):
    #         to_display.append(
    #             index[doc.page_content].dialogue.get_part_of_dialogue(
    #                 index[doc.page_content].chunk_index
    #             )
    #         )
    #     to_display.append(translated_doc)
    # st.write(to_display)


def test_query():
    st.write(engine.get_context_from_query(query))

def translate_dialogue(dialogue: Dialogue):
    st.write("-----------------------------------------------------------------------------")
    for i in range(len(dialogue.text_chunks)):
            if dialogue.text_chunks[i].is_translated():
                st.write(f"Skipped {dialogue.text_chunks[i].raw_text}")
            st.write(dialogue.text_chunks[i].cleared_text)
            messages = [
                {
                    "role": "system",
                    "content": "Ты виртуальный переводчик. Твоя задача перевести сообщения пользователя с японского языка на русский. Тебе возможно будут представлены примеры перевода с японского на русский. В твоем ответе должен содержаться ТОЛЬКО ПЕРЕВОД. Перевод не должен быть дословным, но должен быть грамотным и верным. В сообщениях могут встречаться особые символы или техническая информация, их переводить нельзя",
                }
            ]
            context = engine.get_context_from_query("\n".join(dialogue.text_chunks[i].cleared_text))
            if len(context) > 0:
                st.write(f"Used context length: {len(context)}")
                used_chunks = 0
                for dialogue_chunk in context:
                    for context_chunk in dialogue_chunk:
                        if context_chunk[1] != "": 
                            messages.extend(
                                [
                                    {"role": "user", "content": context_chunk[0]},
                                    {"role": "assistant", "content": context_chunk[1]},
                                ]
                            )
                        used_chunks += 1
                st.write(f"Chunk used: {used_chunks}")

            for j in range(i):
                messages.extend(
                    [
                        {"role": "user", "content": "\n".join(dialogue.text_chunks[j].cleared_text)},
                        {"role": "assistant", "content": "\n".join(dialogue.text_chunks[j].translated_text)},
                    ]
                )

            messages.append(
                {
                    "role": "user",
                    "content": "\n".join(dialogue.text_chunks[i].cleared_text),
                }
            )
            client = openai.OpenAI(api_key="sk-qq", base_url="http://127.0.0.1:5000/v1")
            chat_completion = client.chat.completions.create(
                messages=messages,
                model="gpt-4o",
                temperature=0,
                max_tokens=1024,
            )
            st.write(chat_completion.choices[0].message.content)
            dialogue.text_chunks[i].translated_text = [x for x in chat_completion.choices[0].message.content.split("\n") if x != ""]

def test_model():
    docs = engine.game_files
    founded = None
    for doc in docs:
        # if "Map111.txt" in str(doc.filename):
        #     founded = doc
        #     break
        if "Data/Map023.txt" in str(doc.filename):
            founded = doc
            break
    for dialogue in founded.dialogues:
        translate_dialogue(dialogue)
    return

    # for doc in engine.game_files:
    #     if doc.require_translation():
    #         st.write(doc.filename)
    #         for dialogue in doc.dialogues:
    #             if dialogue.require_translation():
    #                 from copy import deepcopy
    #                 translate_dialogue(deepcopy(dialogue))
    #         break
        


query = st.text_input("Query")
st.button("Search", on_click=search_docs)
st.button("Test", on_click=test_query)
st.button("Test model", on_click=test_model)
