import itertools
import os
from game_types import Actor, Armor, Class, Enemy, Item, State, Weapon, Skill, str_repr
import shutil

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

files_map = {
    "Actors": Actor,
    "Armors": Armor,
    "Classes": Class,
    "Enemies": Enemy,
    "Items": Item,
    "States": State,
    "Weapons": Weapon,
    "Skills": Skill}

patched_folder = "jap_3_1_patched"
source_folder = "jap_3_01"
shutil.rmtree(patched_folder, ignore_errors=True)
shutil.copytree(source_folder, patched_folder, dirs_exist_ok=True)
translation_folder = "translation_files"
os.makedirs(translation_folder, exist_ok=True)

# create patchfiles for translation
for filename, fileclass in files_map.items():
    old_items = []
    new_items = []
    translated_items = []
    changelog = []
    with open(f'{source_folder}/{filename}.txt', 'r', encoding='utf-8') as file:
        new_lines = file.readlines()
        new_items = fileclass.parse(new_lines)

    with open(f'demo_jap/{filename}.txt', 'r', encoding='utf-8') as old_file:
        old_items = fileclass.parse(old_file.readlines())
    
    ids_map = id_map(old_items, new_items)
    print(f"{filename}: {check_percentage(old_items, new_items)}, shifted ids: {len([0 for x in ids_map.keys() if ids_map[x] != x])}/{len(ids_map)}")

    with open(f'demo_rus/{filename}.txt', 'r', encoding='utf-8') as rus_file:
        translated_items = fileclass.parse(rus_file.readlines())


    with open(f'{translation_folder}/{filename}.txt', 'w', encoding='utf-8') as patched_file:
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

    with open(f'{translation_folder}/{filename}.txt.changelog', 'w', encoding='utf-8') as changelog_file:
        changelog_file.writelines(changelog)
    
    with open(f'{translation_folder}/{filename}.txt.missing_entries', 'w', encoding='utf-8') as missing_entries_file:
        missing_entries_file.writelines([f"{fileclass.__name__} {obj.idtf} -- missing old entry\n" for obj in old_items if obj.idtf not in ids_map.keys()])
    with open(f'{translation_folder}/{filename}.txt.to_translate', 'w', encoding='utf-8') as to_translate_file:
        to_translate_file.writelines([f"{fileclass.__name__} {obj.idtf} -- missing new entry\n" for obj in new_items if obj.idtf not in ids_map.values()])

        
# compile patched files