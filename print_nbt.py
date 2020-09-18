from nbt.nbt import *
from collections import OrderedDict
import string
import os


def main():
    nbt_file = NBTFile("../werewolf/werewolf.nbt", "rb")
    print((nbt_file.pretty_tree()))


# 	cba_name = "../werewolf/werewolf.cba"
# 	nbt_name = cba_name.rsplit(".")[0] + ".nbt"
# 	mc_dir = "../werewolf/"

# 	with open(cba_name) as f:
# 		assembly_dict = parse_mc_assembly(f)

# 	print assemble(cba_name).pretty_tree()


# 	from shutil import copyfile
# 	copyfile(nbt_name, mc_dir + nbt_name)

def assemble(file_name):
    with open(file_name) as f:
        assembly_dict = parse_mc_assembly(f)

    block_cols = []
    stands = []
    for i, pair in enumerate(assembly_dict.items()):
        label, lines = pair
        stands.append({"name": label, "position": (i + 0.5, 0, 0.5)})
        block_row = [{"type": "impulse", "command": ""}]
        for line in lines:
            conditionality = line[0] == "C"
            line = line[1:].strip()
            block_row.append({"type": "chain", "command": line, "conditional": conditionality})
        block_cols.append(block_row)

    return gen_command_block_structure(block_cols, stands, file_name.rsplit(".")[0] + ".nbt")


if __name__ == '__main__':
    main()
# os.remove()
