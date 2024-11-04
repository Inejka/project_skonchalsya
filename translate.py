import difflib
import itertools
import os
from game_types import Actor, Armor, Class, Enemy, Item, State, Weapon, Skill, str_repr
import shutil

SOURCE_FOLDER_JAP = "demo_jap"
SOURCE_FOLDER_TRANSLATION = "demo_rus"
FOLDER_TO_PATCH = "jap_3_01"
TRANSLATION_FOLDER = "translation_files"

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
    system_folder = "System"
    file_list = ["Armor Types.txt", "Elements.txt", "Skill Types.txt", "Terms.txt", "Weapon Types.txt"]
    os.makedirs(f"{TRANSLATION_FOLDER}/{system_folder}", exist_ok=True)

    for filename in file_list:
        old_text = ""
        new_text = ""
        
        with open(f'{SOURCE_FOLDER_JAP}/{system_folder}/{filename}', 'r', encoding='utf-8') as old_file:
            old_text = old_file.read()
        with open(f'{FOLDER_TO_PATCH}/{system_folder}/{filename}', 'r', encoding='utf-8') as new_file:
            new_text = new_file.read()

        simularity_score = difflib.SequenceMatcher(None, old_text, new_text).ratio()
        print(f"{filename}: {simularity_score}")
        if simularity_score == 1.0:
            shutil.copyfile(f'{SOURCE_FOLDER_TRANSLATION}/{system_folder}/{filename}', f'{TRANSLATION_FOLDER}/{system_folder}/{filename}')
        else:
            print(f"{filename} NOT COPIED, CHECK SIMULARITY: {simularity_score} AND TRANSLATE IT MANUALLY, SYSTEM WILL NOT BE COMPILED")

    shutil.copyfile(f'{FOLDER_TO_PATCH}/{system_folder}/Switches.txt', f'{TRANSLATION_FOLDER}/{system_folder}/Switches.txt')
    shutil.copyfile(f'{FOLDER_TO_PATCH}/{system_folder}/Variables.txt', f'{TRANSLATION_FOLDER}/{system_folder}/Variables.txt')
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

if __name__ == "__main__":
    # move_translation_files()
    move_translation_system_files()
    