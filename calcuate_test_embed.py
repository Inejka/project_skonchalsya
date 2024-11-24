from llm_translation_utils import (
    get_maps_as_lagchain_documents,
)
from llm_translation_engine import Engine


engine = Engine()

# TODO: fix error in last five chunks
chunk_size = 5
chunks = [engine.game_files[i : i + chunk_size] for i in range(0, len(engine.game_files), chunk_size)]
for i, chunk in enumerate(chunks):
    print(f"Processing chunk {i+1} of {len(chunks)}")
    engine.embed(get_maps_as_lagchain_documents(chunk))


for dialogue_chunk in engine.get_context_from_query("【ルカ・キリエ】 ドッペル達、村を制圧しなさい！ ここにいる者は、みな敵よ！"):
    for context_chunk in dialogue_chunk:
        print(context_chunk)
