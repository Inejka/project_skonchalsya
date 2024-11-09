from dataclasses import dataclass
from pathlib import Path
import re
from translate import FOLDER_TO_PATCH, MAPS_FOLDER, SOURCE_FOLDER_JAP, create_vocabulary, useful_words

def keep_line(line):
    if "ShowText(" in line:
            return True
    return False

DIALOGUE_START_SPLITTERS = []
DIALOGUE_END_SPLITTERS = ["JumpToLabel", "BranchEnd", "Page", "Label", " Name = ", "CommonEvent", "ConditionalBranch", "JumpToLabel"] 

def is_of_(line, splitters): 
    for splitter in splitters:
        if splitter in line:
            return True
    return False

def is_start_of_dialogue(line):
    return is_of_(line, DIALOGUE_START_SPLITTERS)

def is_end_of_dialogue(line):
    return is_of_(line, DIALOGUE_END_SPLITTERS)

# def get_keyword(text):
#     for word in useful_words:
#         if word in text:
#             return word
#     return None

def get_indents(line):
    return len(line) - len(line.lstrip())
@dataclass
class DialogueChunk:
    raw_text: str
    translated_text: list[str]
    cleared_text: list[str]
    start_line: int
    end_line: int
    raw_translated_text: str = ""

    def clear_text(self):
        #self.cleared_text = [re.match(r'ShowText\(\[\"(.*)\"\]\)', line)[1] for line in self.raw_text.split('\n')]
        for line in self.raw_text.split('\n'):
            self.cleared_text.append(re.match(r'\W*ShowText\(\[\"(.*)\"\]\)', line)[1])

    def __post_init__(self):
        self.clear_text()

    

@dataclass
class Dialogue:
    text_chunks: list[DialogueChunk]
    source_file: Path
    # childs: list["Dialogue"]

class EventDocument:
    def __init__(self, filename: Path) -> None:
        self.filename = filename
        with open(filename, 'r', encoding='utf-8') as file:
            self.text = file.read()
        self.text_splitted = self.text.split('\n')
        self.dialogues = [Dialogue([], filename)]
        self.generate_dialogues()

    def generate_dialogues(self):
        i = 0
        while i < len(self.text_splitted):
            if keep_line(self.text_splitted[i]):
                indent = get_indents(self.text_splitted[i])
                start_index = i
                while i < len(self.text_splitted) and keep_line(self.text_splitted[i]) and get_indents(self.text_splitted[i]) == indent:
                    i += 1
                self.dialogues[-1].text_chunks.append(DialogueChunk("\n".join(self.text_splitted[start_index:i]), [], [], start_index, i-1))
                if is_end_of_dialogue(self.text_splitted[i]) or get_indents(self.text_splitted[i]) is not indent:
                    self.dialogues.append(Dialogue([], self.filename))
            else:
                if is_end_of_dialogue(self.text_splitted[i]) and len(self.dialogues[-1].text_chunks) > 0:
                    self.dialogues.append(Dialogue([], self.filename))
                i += 1




    # attempt to make nested dialogues
    #     self.root = Dialogue([], [])
    #     i = 0
    #     while i < len(self.text_splitted):
    #         if keep_line(self.text_splitted[i]):
    #             pass
    #         else:
    #             i += 1

    
    # def generate_dialogue(self, dialogue: Dialogue, start_position: int) -> int:
    #     while start_position < len(self.text_splitted) and not keep_line(self.text_splitted[start_position]):
    #         start_position += 1

    #     i = start_position
    #     keyword = get_keyword(self.text_splitted[i])
    #     while i < len(self.text_splitted):
    #         if get_keyword(self.text_splitted[i]) == keyword:
    #             i += 1
    #         else:
    #             dialogue.text_chunks.append(self.text_splitted[start_position:i])
    #             if is_end_of_dialogue(self.text_splitted[i]):
    #                 pass
    #             elif is_start_of_dialogue(self.text_splitted[i]):
    #                 pass 
    #             else:
    #                 i += 1
    #                 start_position = i

    #     pass

def main():
    i = 0
    lenmax = 0
    documents = []
    for item in Path(f"{SOURCE_FOLDER_JAP}/{MAPS_FOLDER}").glob('**/*.txt'):
        print(item)
        documents.append(EventDocument(item))
        print(documents[-1].dialogues)
        i += 1
        for dialogue in documents[-1].dialogues:
            summm = sum(len(chunk.raw_text) for chunk in dialogue.text_chunks)
            lenmax = max(lenmax, summm)
    print(lenmax)

def check_split():
    vocabulary = {}
    vocabulary, simple_vocabulary = create_vocabulary()
    global_translations = 0
    global_chunks = 0
    for item in Path(f"{FOLDER_TO_PATCH}/{MAPS_FOLDER}").glob('**/*.txt'):
        doc = EventDocument(item)
        dialogues_passages = []
        for dialogue in doc.dialogues:
            translated_chunks = 0
            for chunk in dialogue.text_chunks:
                if vocabulary.get(chunk.raw_text):
                    chunk.raw_translated_text = vocabulary[chunk.raw_text]
                    translated_chunks += 1
                    global_translations += 1
                dialogues_passages.append(chunk.cleared_text)
            global_chunks += len(dialogue.text_chunks)
            print(f"Translated {translated_chunks} out of {len(dialogue.text_chunks)} chunks in {dialogue.source_file}")
            print(f"{global_translations} / {global_chunks}")
        
# check the percentage of lines with useful words out of all lines with useful words
def check_useful_words_percentage():
    freq_map = {i:0 for i in useful_words}
    total_lines = 0
    for item in Path(f"{SOURCE_FOLDER_JAP}/{MAPS_FOLDER}").glob('**/*.txt'):
        print(item)
        with open(item, 'r', encoding='utf-8') as file:
            text = file.read()
            for word in useful_words:
                freq_map[word] += text.count(word)
    total = sum(freq_map.values())
    for word in freq_map:
        print(f"{word}: {freq_map[word]/total}")


if __name__ == "__main__":
    # check_useful_words_percentage()
    check_split()