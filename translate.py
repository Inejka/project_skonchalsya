import difflib
import itertools
import logging
import os
import re
from typing import Iterator
from game_types import Actor, Armor, Class, Enemy, Item, State, Weapon, Skill, str_repr
import shutil
from pathlib import Path

MAPS_ATTENTION = "translate_me_maps"
EVENTS_ATTENTION = "translate_me_events"
SOURCE_FOLDER_JAP = "demo_jap"
SOURCE_FOLDER_TRANSLATION = "demo_rus"
FOLDER_TO_PATCH = "jap_3_01"
TRANSLATION_FOLDER = "translation_files"
MAPS_FOLDER = "Maps"   
EVENTS_FOLDER = "CommonEvents"
useful_words = ["ShowText(", "Display Name", "ShowChoices", "display_skill_name", "ScriptMore", "unlimited_choices", "ex_choice_add", "When"]

japanese_pattern = re.compile(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]')
total_missed = 0
logging.basicConfig(filename='translation.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def keep_line(line):
    for word in useful_words:
        if word in line:
            return True
    return False

def check_percentage(old_items, new_items):
    found = 0       
    for obj in old_items:
        if obj in new_items:
            found += 1

    return(f"{found}/{len(new_items)}")

def id_map(old_items: list, new_items: list):
    map: dict[str, str] = {}
    for obj in old_items:
        new_obj = next((x for x in new_items if x == obj), None)
        if new_obj is not None:
            map[obj.idtf] = new_obj.idtf 
    return map

def move_translation_files():
    files_map = {
        "Actors": Actor,
        "Armors": Armor,
        "Classes": Class,
        "Enemies": Enemy,
        "Items": Item,
        "States": State,
        "Weapons": Weapon,
        "Skills": Skill}
    os.makedirs(TRANSLATION_FOLDER, exist_ok=True)

    # create patchfiles for translation
    for filename, fileclass in files_map.items():
        old_items = []
        new_items = []
        translated_items = []
        changelog = []
        with open(f'{FOLDER_TO_PATCH}/{filename}.txt', 'r', encoding='utf-8') as file:
            new_lines = file.readlines()
            new_items = fileclass.parse(new_lines)

        with open(f'{SOURCE_FOLDER_JAP}/{filename}.txt', 'r', encoding='utf-8') as old_file:
            old_items = fileclass.parse(old_file.readlines())
        
        ids_map = id_map(old_items, new_items)
        print(f"{filename}: {check_percentage(old_items, new_items)}, shifted ids: {len([0 for x in ids_map.keys() if ids_map[x] != x])}/{len(ids_map)}")

        with open(f'{SOURCE_FOLDER_TRANSLATION}/{filename}.txt', 'r', encoding='utf-8') as rus_file:
            translated_items = fileclass.parse(rus_file.readlines())


        with open(f'{TRANSLATION_FOLDER}/{filename}.txt', 'w', encoding='utf-8') as patched_file:
            patched_lines = new_lines
            replace_counter = 0
            for old_idtf, new_idtf in ids_map.items():
                
                # find the range in the patched_lines
                # TODO: perf optimization, start lookup from the last range_end (requires ordered id_map)
                range_start = next(idx for idx in range(len(patched_lines)) if f"{fileclass.__name__} {new_idtf}" in patched_lines[idx])
                range_end = next((idx for idx in range(range_start+1, len(patched_lines)) if f"{fileclass.__name__} " in patched_lines[idx]), len(patched_lines)-1)

                patched_object = next(x for x in translated_items if x.idtf == old_idtf)
                patched_object.idtf = new_idtf
                patched_lines = list(itertools.chain(patched_lines[:range_start], str_repr(patched_object), ["\n"], patched_lines[range_end:]))
                replace_counter += 1
                changelog.append(f"{fileclass.__name__} {old_idtf} -> {fileclass.__name__} {new_idtf} was replaced in range {range_start} - {range_end}" + (" SHIFTED" if old_idtf != new_idtf else "") +"\n")
            print(f"{replace_counter} replaced in {filename}")
            patched_file.writelines(patched_lines)

        with open(f'{TRANSLATION_FOLDER}/{filename}.txt.changelog', 'w', encoding='utf-8') as changelog_file:
            changelog_file.writelines(changelog)
        
        with open(f'{TRANSLATION_FOLDER}/{filename}.txt.missing_entries', 'w', encoding='utf-8') as missing_entries_file:
            missing_entries_file.writelines([f"{fileclass.__name__} {obj.idtf} -- missing old entry\n" for obj in old_items if obj.idtf not in ids_map.keys()])
        with open(f'{TRANSLATION_FOLDER}/{filename}.txt.to_translate', 'w', encoding='utf-8') as to_translate_file:
            to_translate_file.writelines([f"{fileclass.__name__} {obj.idtf} -- missing new entry\n" for obj in new_items if obj.idtf not in ids_map.values()])

        
    # TODO: compile patched files

def move_translation_system_files():
    SYSTEM_FOLDER = "System"
    file_list = ["Armor Types.txt", "Elements.txt", "Skill Types.txt", "Terms.txt", "Weapon Types.txt"]
    os.makedirs(f"{TRANSLATION_FOLDER}/{SYSTEM_FOLDER}", exist_ok=True)

    for filename in file_list:
        old_text = ""
        new_text = ""
        
        with open(f'{SOURCE_FOLDER_JAP}/{SYSTEM_FOLDER}/{filename}', 'r', encoding='utf-8') as old_file:
            old_text = old_file.read()
        with open(f'{FOLDER_TO_PATCH}/{SYSTEM_FOLDER}/{filename}', 'r', encoding='utf-8') as new_file:
            new_text = new_file.read()

        simularity_score = difflib.SequenceMatcher(None, old_text, new_text).ratio()
        print(f"{filename}: {simularity_score}")
        if simularity_score == 1.0:
            shutil.copyfile(f'{SOURCE_FOLDER_TRANSLATION}/{SYSTEM_FOLDER}/{filename}', f'{TRANSLATION_FOLDER}/{SYSTEM_FOLDER}/{filename}')
        else:
            print(f"{filename} NOT COPIED, CHECK SIMULARITY: {simularity_score} AND TRANSLATE IT MANUALLY, SYSTEM WILL NOT BE COMPILED")

    shutil.copyfile(f'{FOLDER_TO_PATCH}/{SYSTEM_FOLDER}/Switches.txt', f'{TRANSLATION_FOLDER}/{SYSTEM_FOLDER}/Switches.txt')
    shutil.copyfile(f'{FOLDER_TO_PATCH}/{SYSTEM_FOLDER}/Variables.txt', f'{TRANSLATION_FOLDER}/{SYSTEM_FOLDER}/Variables.txt')
    with open(f'{SOURCE_FOLDER_JAP}/System.txt', 'r', encoding='utf-8') as old_file:
        old_text = old_file.read()
    with open(f'{FOLDER_TO_PATCH}/System.txt', 'r', encoding='utf-8') as new_file:
        new_text = new_file.read()
    simularity_score = difflib.SequenceMatcher(None, old_text, new_text).ratio()
    print(f"System.txt: {simularity_score}")
    if simularity_score == 1.0:
        shutil.copyfile(f'{SOURCE_FOLDER_TRANSLATION}/System.txt', f'{TRANSLATION_FOLDER}/System.txt')
    else:
        print(f"System.txt NOT COPIED, CHECK SIMULARITY: {simularity_score} AND TRANSLATE IT MANUALLY, SYSTEM WILL NOT BE COMPILED")

def reduce_text_to_commands(text: str) -> list[str]:
    return list(map(lambda line: list(filter(lambda word: word in line, useful_words))[0], text.split("\n")))

def clear_commands_list(commands: list[str]) -> list[str]:
    to_return = [commands[0]]
    for i in range(1, len(commands)):
        if commands[i] != commands[i-1]:
            to_return.append(commands[i])
    return to_return

def validate_pairs(original_text, translated_text):
    original = reduce_text_to_commands(original_text)
    translated = reduce_text_to_commands(translated_text)
    return clear_commands_list(original) == clear_commands_list(translated) 

def iterate_folder_pair(source_folder_root: str, translation_folder_root:str, folder_name: str) -> Iterator[tuple[str, str, str, str]]:
    for item in Path(f"{source_folder_root}/{folder_name}").glob("**/*.txt"):
            source_text = item.read_text(encoding="utf-8")
            translation_text = Path(str(item).replace(source_folder_root, translation_folder_root)).read_text(encoding="utf-8")
            yield source_text, translation_text, str(item), str(Path(str(item).replace(source_folder_root, translation_folder_root)))

def break_text_into_chunks(text: str) -> Iterator[str]:
    text = text.split("\n")
    first = 0
    last = 0
    while last < len(text):
        while first < len(text) and not keep_line(text[first]):
            first += 1
        last = first + 1
        while last < len(text) and keep_line(text[last]):
            last += 1
        if first != len(text):
            yield "\n".join(text[first:last])
        first = last


def generate_vocabulary_from_text_pair(text_original: str, text_translated: str, original_file:str = None, translated_file:str = None) -> dict[str, str]:
    vocabulary = {}    
    s = difflib.SequenceMatcher(None, text_original, text_translated)
    for tag, i1, i2, j1, j2 in s.get_opcodes():
        if tag == "equal":
             continue
        if tag == "replace":
            original_chunks = [x for x in break_text_into_chunks("\n".join(text_original[i1:i2]))]
            translated_chunks = [x for x in break_text_into_chunks("\n".join(text_translated[j1:j2]))]
            if len(original_chunks) != len(translated_chunks):
                global total_missed
                total_missed += 1
                logging.warning('{}   ->   {}    {:7}   a[{}:{}] --> b[{}:{}] {!r:>8} --> {!r}'.format(original_file, translated_file,tag, i1, i2, j1, j2, text_original[i1:i2], text_translated[j1:j2]))
            else:
                for original_chunk, translated_chunk in zip(original_chunks, translated_chunks):
                    if not validate_pairs(original_chunk, translated_chunk):
                        print("Validation of vocabulary failed, please ping author")
                    else:
                        vocabulary[original_chunk] = translated_chunk

        else:
            logging.warning('{}   ->   {}    {:7}   a[{}:{}] --> b[{}:{}] {!r:>8} --> {!r}'.format(original_file, translated_file,tag, i1, i2, j1, j2, text_original[i1:i2], text_translated[j1:j2]))
    return vocabulary

def generate_maps_vocabulary():
    vocabulary = {}
    for source_text, translation_text, original_file, translated_file in iterate_folder_pair(SOURCE_FOLDER_JAP, SOURCE_FOLDER_TRANSLATION, MAPS_FOLDER):
        vocabulary.update(generate_vocabulary_from_text_pair(source_text.split("\n"), translation_text.split("\n"), original_file, translated_file))
    print(f"map vocabulary size: {len(vocabulary)}")
    return vocabulary

def generate_events_vocabulary():
    vocabulary = {}
    for source_text, translation_text, original_file, translated_file in iterate_folder_pair(SOURCE_FOLDER_JAP, SOURCE_FOLDER_TRANSLATION, EVENTS_FOLDER):
        vocabulary.update(generate_vocabulary_from_text_pair(source_text.split("\n"), translation_text.split("\n"), original_file, translated_file))
    print(f"common events vocabulary size: {len(vocabulary)}")
    return vocabulary

def patch_pair(vocabulary: dict[str, str], folder_to_patch: str, translation_folder_root: str, folder_name: str, attention_folder: str):
    full_patched_items = 0
    total_items = 0
    for item in Path(f"{folder_to_patch}/{folder_name}").glob('**/*.txt'):
        text = item.read_text(encoding='utf-8')
        chunks = break_text_into_chunks(text)
        total_items += 1
        japanese_was = japanese_pattern.search(text)
        for chunk in chunks:
            if chunk in vocabulary:
                text = text.replace(chunk, vocabulary[chunk])
        
        succesfully_patched = japanese_pattern.search(text) is None

        if succesfully_patched:
            with open(str(item).replace(folder_to_patch, translation_folder_root), 'w', encoding="utf-8") as transition_file:
                transition_file.write(text)
            if japanese_was:
                full_patched_items += 1
        else:
            with open(str(item).replace(folder_to_patch, translation_folder_root).replace(folder_name,attention_folder), 'w', encoding="utf-8") as transition_file:
                transition_file.write(text)

    print(f"items fully patched {full_patched_items} / {total_items}")



def patch_maps():
    maps_vocabulary = generate_maps_vocabulary()
 
    os.makedirs(f"{TRANSLATION_FOLDER}/{MAPS_FOLDER}/Map/Data", exist_ok=True)
    os.makedirs(f"{TRANSLATION_FOLDER}/{MAPS_FOLDER}/Map2/Data", exist_ok=True)
    os.makedirs(f"{TRANSLATION_FOLDER}/{MAPS_ATTENTION}/Map/Data", exist_ok=True)
    os.makedirs(f"{TRANSLATION_FOLDER}/{MAPS_ATTENTION}/Map2/Data", exist_ok=True)
    print("patching maps")
    patch_pair(maps_vocabulary, FOLDER_TO_PATCH, TRANSLATION_FOLDER, MAPS_FOLDER, MAPS_ATTENTION)

def patch_common_events():
    events_vocabulary = generate_events_vocabulary()
    os.makedirs(f"{TRANSLATION_FOLDER}/{EVENTS_FOLDER}", exist_ok=True)
    os.makedirs(f"{TRANSLATION_FOLDER}/{EVENTS_ATTENTION}", exist_ok=True)
    print("patching common events")
    patch_pair(events_vocabulary, FOLDER_TO_PATCH, TRANSLATION_FOLDER, EVENTS_FOLDER, EVENTS_ATTENTION)

if __name__ == "__main__":
    move_translation_files()
    move_translation_system_files()
    patch_maps()
    patch_common_events()