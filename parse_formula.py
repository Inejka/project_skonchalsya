from typing import Tuple
import re
FILE = "formulas.txt"


simle_formula = re.compile(r"^((a|b).(atk|agi|mat|luk|def|mdf|mhp|mmp|hp|wp_atk|mp_cost)|(v\[108\])|(v\[102\]))$")
max_formula = re.compile(r"^\[(((a\.mat)|(a\.agi)|(a\.atk)|(a\.luk)|(a\.def)|(a\.mdf))(, )?)+\]\.max$")
summarization_formula = re.compile(r"^\((((a\.mat)|(a\.agi)|(a\.atk)|(a\.luk)|(a\.def)|(a\.mdf))( \+ )?)+\)$")
const_damage_formula = re.compile(r"^\d+$")

multiplyer_formula = re.compile(r"^((([0-9]*[.])?[0-9]+)( \* )?)+$")
divider_formula = re.compile(r"( / )([0-9]*[.])?[0-9]+")

formula_to_view = {
    "atk": "АТК",
    "agi": "ЛОВ",
    "luk": "СНР",
    "mat": "МАГ",
    "def": "ЗАЩ",
    "mdf": "ВОЛ",
    "hp": "HP",
    "mhp": "MHP",
    "mmp": "MMP",
    "wp_atk": "АТК",
    "mp_cost": "MP",
    "v[108]": "УР",
    "v[102]": "ШАГИ",
}


def parse(line: str) -> Tuple[int,str]:
    if simle_formula.match(line):
        return (100, formula_to_view[line[2:]])
    
    # prepare line
    line = line.split("-")[0]
    line = line.replace ("* a.hp / a.mhp ", "")
    test = re.match(r".*( / )(([0-9]*[.])?[0-9]+).*", line)
    if test:
        line = line.replace("/", "*")
        line = line.replace(test[2], str(1/float(test[2])))
    temp = line.split("*")
    left = temp[0].strip()
    right = "*".join(temp[1:]).strip()

    # can't handle these
    if "a." in right or "b." in right:
        return (-1, None)
    
    percent = 100
    if not right=="":
        if "+" in right:
            right = right.split("+")[0].strip()

        if multiplyer_formula.match(right):
            temp = 1
            for num in right.split("*"):
                temp *= float(num)
            percent = temp * 100
        else:
            return (-1, None)
    
    attributes_in_formula = []
    for key in formula_to_view.keys():
        if key in left:
            attributes_in_formula.append(formula_to_view[key])
    
    attribute_str = ""
    if simle_formula.match(left):
        attribute_str = attributes_in_formula[0]
    if max_formula.match(left):
        attribute_str = "[" + "/".join(attributes_in_formula)+"]"
    if summarization_formula.match(left):
        attribute_str = "(" + "+".join(attributes_in_formula)+")"
    
    return (int(percent), attribute_str)
    



if __name__ == "__main__":
    with open(FILE, "r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            # check_rule(line.strip())
            a, b = parse(line)
            if a == -1:
                print(line)


            # fuck these three formulas i will ignore them
            # if "-" in line:
            #     f = line.split("-")
            #     b = "-".join(f[1:])
            #     if "a." in b:
            #         print(line)


def check_rule(line, print_filtered = False) -> None:
    init_line = line
    if print_filtered:
        if simle_formula.match(line):
            print(line)
            return
        
        if const_damage_formula.match(line):
            print(line)
            return

        return
    
    
    if simle_formula.match(line):
        return
    
    if const_damage_formula.match(line):
        return
    
    line = line.split("-")[0]
    line = line.replace (" / 5", " * 0.2")
    line = line.replace (" / 2", " * 0.5")
    line = line.replace (" / 10", " * 0.1")
    line = line.replace (" / 3", " * 0.33")
    line = line.replace (" / 4", " * 0.25")
    line = line.replace (" / 6", " * 0.166")
    temp = line.split("*")
    left = temp[0].strip()
    right = "*".join(temp[1:]).strip()
    # print(f"{left} = {right}")
    if "a." in right or "b." in right:
        # print(f"{left} = {right}, {init_line}")
        pass
    else:
        # if simle_formula.match(left):
        #     return
        # if max_formula.match(left):
        #     return
        # if summarization_formula.match(left):
        #     return
        # print(f"{left} = {right}, {init_line}")
        
        # if "max" in left and not max_formula.match(left.strip()):
            # print(f"{left} = {right}, {init_line}")
        # print(f"{left} = {right}, {init_line}")
        if multiplyer_formula.match(right):
            return
        print(right, init_line)