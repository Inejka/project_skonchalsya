from dataclasses import dataclass
import re


# won't support types with identation
def parse(classname, strings: str):
    item_name: str = classname.__name__
    parse_params: dict[str, str] = classname.member_map()
    objs = []
    scratch: dict[str, str] = dict()
    for s in strings:
        if s.startswith(item_name):
            if "idtf" in scratch.keys():
                try:
                    new_instance = classname(**scratch)
                except TypeError:
                    print(s)
                    print(scratch["idtf"])
                    raise (Exception("NIGGER"))
                if not new_instance.is_placeholder():
                    objs.append(classname(**scratch))
                scratch = dict()
            scratch["idtf"] = re.match(rf"{item_name} (\d*)", s)[1]
        else:
            param = re.match(r'(.*?) = (".*"|nil|\d*)', s)
            # print(param)
            if (param is None) and s != "\n":
                raise (Exception("NIGGER"))
            elif s == "\n":
                pass
            elif param[1] in parse_params.keys():
                scratch[parse_params[param[1]]] = param[2]
            else:
                pass
    last_instance = classname(**scratch)
    if not last_instance.is_placeholder():
        objs.append(last_instance)
    return objs


def str_repr(obj) -> list[str]:
    repr_map = {value: key for key, value in obj.__class__.member_map().items()}
    repr_lines = list()
    repr_lines.append(f"{obj.__class__.__name__} {obj.idtf}\n")
    # construct parameters based on the member_map and field values of the object
    obj_attrs = dict(obj.__dict__)
    obj_attrs.pop("idtf")
    for line in [f"{repr_map[key]} = {value}\n" for key, value in obj_attrs.items()]:
        repr_lines.append(line)
    return repr_lines


@dataclass
class Item:
    idtf: str
    name: str
    desc: str
    note: str

    def member_map():
        return {"Name": "name", "Description": "desc", "Note": "note"}

    def is_placeholder(self):
        return self.name == '""' and self.desc == '""' and self.note == '""'

    @classmethod
    def parse(cls, strings: str):
        return parse(cls, strings)

    # custom deep equals magic method
    def __eq__(self, other):
        if self.is_placeholder() or other.is_placeholder():
            return False
        return (
            self.name == other.name
            and self.desc == other.desc
            and self.note == other.note
        )


@dataclass
class Armor:
    idtf: str
    name: str
    desc: str
    note: str

    def member_map():
        return {"Name": "name", "Description": "desc", "Note": "note"}

    def is_placeholder(self):
        return self.name == '""' and self.desc == '""' and self.note == '""'

    @classmethod
    def parse(cls, strings: str):
        return parse(cls, strings)

    def __eq__(self, other):
        if self.is_placeholder() or other.is_placeholder():
            return False
        return (
            self.name == other.name
            and self.desc == other.desc
            and self.note == other.note
        )


@dataclass
class Class:
    idtf: str
    name: str
    desc: str
    note: str

    def member_map():
        return {"Name": "name", "Description": "desc", "Note": "note"}

    def is_placeholder(self):
        return self.name == '""' and self.desc == '""' and self.note == '""'

    @classmethod
    def parse(cls, strings: str):
        return parse(cls, strings)

    def __eq__(self, other):
        if self.is_placeholder() or other.is_placeholder():
            return False
        return (
            self.name == other.name
            and self.desc == other.desc
            and self.note == other.note
        )


@dataclass
class Weapon:
    idtf: str
    name: str
    desc: str
    note: str

    def member_map():
        return {"Name": "name", "Description": "desc", "Note": "note"}

    @classmethod
    def parse(cls, strings: str):
        return parse(cls, strings)

    def is_placeholder(self):
        return self.name == '""' and self.desc == '""' and self.note == '""'

    def __eq__(self, other):
        if self.is_placeholder() or other.is_placeholder():
            return False
        return (
            self.name == other.name
            and self.desc == other.desc
            and self.note == other.note
        )


@dataclass
class Enemy:
    idtf: str
    battler_name: str
    name: str
    desc: str
    note: str

    def member_map():
        return {
            "Battler Name": "battler_name",
            "Name": "name",
            "Description": "desc",
            "Note": "note",
        }

    def is_placeholder(self):
        return (
            self.name == '""'
            and self.desc == '""'
            and self.note == '""'
            and self.battler_name == '""'
        )

    @classmethod
    def parse(cls, strings: str):
        return parse(cls, strings)

    def __eq__(self, other):
        if self.is_placeholder() or other.is_placeholder():
            return False
        return (
            self.battler_name == other.battler_name
            and self.name == other.name
            and self.desc == other.desc
            and self.note == other.note
        )


@dataclass
class State:
    idtf: str
    icon_idx: int
    msg_1: str
    msg_2: str
    msg_3: str
    msg_4: str
    name: str
    desc: str
    note: str

    def member_map():
        return {
            "Icon Index": "icon_idx",
            "Message 1": "msg_1",
            "Message 2": "msg_2",
            "Message 3": "msg_3",
            "Message 4": "msg_4",
            "Name": "name",
            "Description": "desc",
            "Note": "note",
        }

    def is_placeholder(self):
        return (
            self.msg_1 == '""'
            and self.msg_2 == '""'
            and self.msg_3 == '""'
            and self.msg_4 == '""'
            and self.name == '""'
            and self.desc == '""'
            and self.note == '""'
        )

    @classmethod
    def parse(cls, strings: str):
        return parse(cls, strings)

    def __eq__(self, other):
        if self.is_placeholder() or other.is_placeholder():
            return False
        return (
            # self.icon_idx == other.icon_idx and
            self.msg_1 == other.msg_1
            and self.msg_2 == other.msg_2
            and self.msg_3 == other.msg_3
            and self.msg_4 == other.msg_4
            and self.name == other.name
            and self.desc == other.desc
            and self.note == other.note
        )


@dataclass
class Actor:
    idtf: str
    nickname: str
    character_name: str
    face_name: str
    name: str
    desc: str
    note: str

    def member_map():
        return {
            "Nickname": "nickname",
            "Character Name": "character_name",
            "Face Name": "face_name",
            "Name": "name",
            "Description": "desc",
            "Note": "note",
        }

    def is_placeholder(self):
        return (
            self.nickname == '""'
            and self.character_name == '""'
            and self.face_name == '""'
            and self.name == '""'
            and self.desc == '""'
            and self.note == '""'
        )

    @classmethod
    def parse(cls, strings: str):
        return parse(cls, strings)

    def __eq__(self, other):
        if self.is_placeholder() or other.is_placeholder():
            return False
        return (
            self.nickname == other.nickname
            and self.character_name == other.character_name
            and self.face_name == other.face_name
            and self.name == other.name
            and self.desc == other.desc
            and self.note == other.note
        )


@dataclass
class Skill:
    idtf: str
    msg_1: str
    msg_2: str
    name: str
    desc: str
    note: str

    def member_map():
        return {
            "Message 1": "msg_1",
            "Message 2": "msg_2",
            "Name": "name",
            "Description": "desc",
            "Note": "note",
        }

    @classmethod
    def parse(cls, strings: str):
        return parse(cls, strings)

    def is_placeholder(self):
        return (
            self.msg_1 == '""'
            and self.msg_2 == '""'
            and self.name == '""'
            and self.desc == '""'
            and self.note == '""'
        )

    def __eq__(self, other):
        if self.is_placeholder() or other.is_placeholder():
            return False
        return (
            self.msg_1 == other.msg_1
            and self.msg_2 == other.msg_2
            and self.name == other.name
            and self.desc == other.desc
            and self.note == other.note
        )

parse(Skill, open('demo_rus/Skills.txt', 'r', encoding='utf-8').readlines())