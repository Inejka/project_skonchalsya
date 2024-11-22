from dataclasses import dataclass
from pathlib import Path
import re


def get_indents(line):
    return len(line) - len(line.lstrip())


def keep_line(line):
    if "ShowText(" in line:
        return True
    return False


DIALOGUE_START_SPLITTERS = []
DIALOGUE_END_SPLITTERS = [
    "JumpToLabel",
    "BranchEnd",
    "Page",
    "Label",
    " Name = ",
    "CommonEvent",
    "ConditionalBranch",
    "JumpToLabel",
]


def is_of_(line, splitters):
    for splitter in splitters:
        if splitter in line:
            return True
    return False


def is_start_of_dialogue(line):
    return is_of_(line, DIALOGUE_START_SPLITTERS)


def is_end_of_dialogue(line):
    return is_of_(line, DIALOGUE_END_SPLITTERS)


@dataclass
class DialogueChunk:
    raw_text: str
    start_line: int
    end_line: int
    translated_text: list[str]
    cleared_text: list[str]
    raw_translated_text: str = ""

    def clear_text(self) -> None:
        for line in self.raw_text.split("\n"):
            self.cleared_text.append(re.match(r"\W*ShowText\(\[\"(.*)\"\]\)", line)[1])

    def clear_translated_text(self) -> None:
        for line in self.raw_translated_text.split("\n"):
            self.translated_text.append(
                re.match(r"\W*ShowText\(\[\"(.*)\"\]\)", line)[1]
            )

    def __post_init__(self):
        self.clear_text()

    def set_translation(self, translation: str) -> None:
        self.raw_translated_text = translation
        self.clear_translated_text()
    
    def is_translated(self) -> bool:
        return len(self.translated_text) > 0
    
    def is_translation_handmade(self) -> bool:
        return self.raw_translated_text != "" and len(self.translated_text) > 0


@dataclass
class Dialogue:
    text_chunks: list[DialogueChunk]
    source_file: Path

    def get_cleared_dialogue(self) -> list[tuple[str, str]]:
        to_return = []
        for chunk in self.text_chunks:
            to_return.append(
                ("\n".join(chunk.cleared_text), "\n".join(chunk.translated_text))
            )
        return to_return

    def get_part_of_dialogue(
        self, chunk_position: int, radius: int = 5
    ) -> list[tuple[str, str]]:
        to_return = []
        for chunk in self.text_chunks[
            max(0, chunk_position - radius) : min(
                len(self.text_chunks), chunk_position + radius + 1
            )
        ]:
            to_return.append(
                ("\n".join(chunk.cleared_text), "\n".join(chunk.translated_text))
            )
        return to_return
    
    def require_translation(self) -> bool:
        return not all([chunk.is_translated() for chunk in self.text_chunks])


class GameFile:
    def __init__(self, filename: Path) -> None:
        self.filename = filename
        with open(filename, "r", encoding="utf-8") as file:
            self.text = file.read()
        self.text_splitted = self.text.split("\n")
        self.dialogues = [Dialogue([], filename)]
        self.generate_dialogues()

    def generate_dialogues(self):
        i = 0
        while i < len(self.text_splitted):
            if keep_line(self.text_splitted[i]):
                indent = get_indents(self.text_splitted[i])
                start_index = i
                while (
                    i < len(self.text_splitted)
                    and keep_line(self.text_splitted[i])
                    and get_indents(self.text_splitted[i]) == indent
                ):
                    i += 1
                self.dialogues[-1].text_chunks.append(
                    DialogueChunk(
                        "\n".join(self.text_splitted[start_index:i]),
                        start_index,
                        i - 1,
                        [],
                        [],
                    )
                )
                if (
                    is_end_of_dialogue(self.text_splitted[i])
                    or get_indents(self.text_splitted[i]) is not indent
                ):
                    self.dialogues.append(Dialogue([], self.filename))
            else:
                if (
                    is_end_of_dialogue(self.text_splitted[i])
                    and len(self.dialogues[-1].text_chunks) > 0
                ):
                    self.dialogues.append(Dialogue([], self.filename))
                i += 1

    def require_translation(self) -> bool:
        return any([dialogue.require_translation() for dialogue in self.dialogues])


@dataclass
class RawTextPointer:
    event_document: GameFile
    dialogue: Dialogue
    chunk: DialogueChunk
    event_document_index: int
    dialogue_index: int
    chunk_index: int
