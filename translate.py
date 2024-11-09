from copy import deepcopy
import difflib
import itertools
import os
from game_types import Actor, Armor, Class, Enemy, Item, State, Weapon, Skill, str_repr
import shutil
from pathlib import Path

MAPS_ATTENSION = "translate_me_maps"
SOURCE_FOLDER_JAP = "demo_jap"
SOURCE_FOLDER_TRANSLATION = "demo_rus"
FOLDER_TO_PATCH = "jap_3_01"
TRANSLATION_FOLDER = "translation_files"
MAPS_FOLDER = "Maps"   
useful_words = ["ShowText(", "Display Name", "ShowChoices", "display_skill_name", "ScriptMore", "unlimited_choices", "ex_choice_add", "When"]

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

def is_end_of_chunk(text, inx, context_length):
    for i in range(inx, min(len(text), inx + context_length + 1)):
        if keep_line(text[i]):
            return False
    return True

def break_text_into_chunks(text, context_length=3):
        chunks = []
        text = text.split("\n")
        i = 0
        while i < len(text):
            if keep_line(text[i]):
                start_of_chunk = i
                j = i + 1
                while not is_end_of_chunk(text, j, context_length):
                    j += 1
                chunks.append(("\n".join(text[i-context_length:start_of_chunk]), "\n".join(text[start_of_chunk:j]), "\n".join(text[j:j+context_length])))
                i = j
            else:
                i += 1
        return chunks

def break_chunk(text):
        text = text.split("\n")
        first = 0
        last = 0
        while last < len(text):
            if not keep_line(text[last]):
                yield "\n".join(text[first:last])
                while last < len(text) and not keep_line(text[last]):
                    last += 1
                first = last
                last += 1
            else:
                last += 1
        yield "\n".join(text[first:last])


def create_vocabulary():
    vocabulary = {}
    simple_vocabulary = {}

    def process_chunks(chunks, translated_text):
        context_was_not_founded = False
        last_context_position = 0
        for chunk in chunks:
            start_position = translated_text.find(chunk[0], last_context_position)
            if start_position != -1:
                start_position += len(chunk[0])
            end_position = translated_text.find(chunk[2], start_position)           
            if start_position != -1 and end_position != -1:
                for source, target in zip(break_chunk(chunk[1]), break_chunk(translated_text[start_position+1: end_position-1])):
                    vocabulary[source] = target
            else:
                context_was_not_founded = True

            last_context_position = start_position
        return context_was_not_founded

    def create_simple_shunks(text):
        chunks = []
        lines = text.split("\n")
        start_position = 0
        end_position = 0
        i = 0
        while i < len(lines):
            if keep_line(lines[i]):
                start_position = i
                end_position = i + 1
                while end_position < len(lines) and keep_line(lines[end_position]):
                    end_position += 1
                chunks.append("\n".join(lines[start_position:end_position]))
                i = end_position + 1
            else:
                i += 1
        return chunks
            

    for item in Path(f"{SOURCE_FOLDER_JAP}/{MAPS_FOLDER}").glob('**/*.txt'):
        source_text = ""
        translated_text = ""
        with open(item, 'r', encoding='utf-8') as source_file:
            source_text = source_file.read()
        with open(str(item).replace(SOURCE_FOLDER_JAP, SOURCE_FOLDER_TRANSLATION), 'r', encoding='utf-8') as translate_file:
            translated_text = translate_file.read()
        chunks = break_text_into_chunks(source_text)
        process_chunks(chunks, translated_text)

        jap_simple_chunks = create_simple_shunks(source_text)
        rus_simple_chunks = create_simple_shunks(translated_text)
        if len(jap_simple_chunks) == len(rus_simple_chunks):
            for jap, rus in zip(jap_simple_chunks, rus_simple_chunks):
                simple_vocabulary[jap] = rus

    return (vocabulary, simple_vocabulary)

def patch_maps():

    vocabulary, simple_vocabulary = create_vocabulary()
    print(f"Len of simple vocabulary {len(simple_vocabulary)}")
    print(f"Len of complicated vocabulary {len(vocabulary)}")
 
    os.makedirs(f"{TRANSLATION_FOLDER}/{MAPS_FOLDER}/Map/Data", exist_ok=True)
    os.makedirs(f"{TRANSLATION_FOLDER}/{MAPS_FOLDER}/Map2/Data", exist_ok=True)
    os.makedirs(f"{TRANSLATION_FOLDER}/{MAPS_ATTENSION}/Map/Data", exist_ok=True)
    os.makedirs(f"{TRANSLATION_FOLDER}/{MAPS_ATTENSION}/Map2/Data", exist_ok=True)


    full_patched_maps = 0
    total_maps = 0
    with open("nigger.txt", 'w', encoding='utf-8') as file:
        file.write(str(vocabulary))
    for item in Path(f"{FOLDER_TO_PATCH}/{MAPS_FOLDER}").glob('**/*.txt'):
        succesfully_patched = True
        text = item.read_text(encoding='utf-8')
        chunks = break_text_into_chunks(text)
        total_maps += 1
        for chunk in chunks:
            for piece in break_chunk(chunk[1]):
                if piece in simple_vocabulary:
                    text = text.replace(piece, simple_vocabulary[piece])
                elif piece in vocabulary:
                    text = text.replace(piece, vocabulary[piece])
                else:
                    succesfully_patched = False

        if succesfully_patched:
            with open(str(item).replace(FOLDER_TO_PATCH, TRANSLATION_FOLDER), 'w', encoding="utf-8") as transition_file:
                transition_file.write(text)
            full_patched_maps += 1
        else:
            with open(str(item).replace(FOLDER_TO_PATCH, TRANSLATION_FOLDER).replace(MAPS_FOLDER,MAPS_ATTENSION), 'w', encoding="utf-8") as transition_file:
                transition_file.write(text)

    print(f"Maps fully patched {full_patched_maps} / {total_maps}")



if __name__ == "__main__":
    move_translation_files()
    move_translation_system_files()
    patch_maps()