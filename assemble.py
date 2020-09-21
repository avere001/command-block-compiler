#!/usr/bin/env python
import json
from pathlib import Path

from nbt.nbt import *
from collections import OrderedDict
import string
import os


class Palette:
    def __init__(self, name, **properties):
        self.name = name
        self.properties = properties

    def convert_to_tag(self):
        properties = TAG_Compound()
        properties.name = "Properties"
        for k, v in list(self.properties.items()):
            tag_prop = TAG_String(name=k, value=v)
            properties.tags.append(tag_prop)

        tag_name = TAG_String(name="Name", value=self.name)

        palette_compound = TAG_Compound()
        palette_compound.tags.append(properties)
        palette_compound.tags.append(tag_name)

        return palette_compound


class Block:
    def __init__(self, x, y, z, state):
        self.pos = TAG_List(name='pos', type=TAG_Int)
        self.pos.tags.extend(list(map(TAG_Int, (x, y, z))))
        self.state = state

    def convert_to_tag(self):
        tag = TAG_Compound()
        tag.tags.append(self.pos)
        tag.tags.append(TAG_Int(value=self.state, name='state'))
        return tag


class CommandBlock:
    def __init__(self, x, y, z, state, **nbt_data):
        def gen_tag(TAG_type, name, default):
            return TAG_type(name=name, value=nbt_data.get(name, default))

        self.pos = TAG_List(name='pos', type=TAG_Int)
        self.pos.tags.extend(list(map(TAG_Int, (x, y, z))))
        self.state = state
        self.nbt_data = TAG_Compound()
        self.nbt_data.name = "nbt"
        self.nbt_data.tags.append(gen_tag(TAG_Byte, 'conditionMet', 0))
        self.nbt_data.tags.append(gen_tag(TAG_Byte, 'auto', 0))
        self.nbt_data.tags.append(gen_tag(TAG_String, 'CustomName', '{"text":"@"}'))
        self.nbt_data.tags.append(gen_tag(TAG_Byte, 'powered', 0))
        self.nbt_data.tags.append(gen_tag(TAG_String, 'Command', ''))
        self.nbt_data.tags.append(gen_tag(TAG_String, 'id', 'minecraft:command_block'))
        self.nbt_data.tags.append(gen_tag(TAG_Int, 'SuccessCount', 0))
        self.nbt_data.tags.append(gen_tag(TAG_Byte, 'TrackOutput', 1))
        self.nbt_data.tags.append(gen_tag(TAG_Byte, 'UpdateLastExecution', 1))

    # print(self.nbt_data.pretty_tree())

    def convert_to_tag(self):
        tag = TAG_Compound()
        tag.tags.append(self.nbt_data)
        tag.tags.append(self.pos)
        tag.tags.append(TAG_Int(value=self.state, name='state'))
        return tag


def gen_size_tag(blocks):
    x = len(blocks)
    z = max(len(x) for x in blocks)
    size_tag = TAG_List(name="size", type=TAG_Int)
    size_tag.tags += [TAG_Int(x), TAG_Int(1), TAG_Int(z)]
    return size_tag


def gen_command_block_structure(blocks, stands, output_file_name):
    """
    Generate an nbt file with filled with blocks and entities

    blocks is a 2d array of dictionaries.
    each entry corresponds to a block of code
    """

    # print dir(TAG_Compound())

    nbt_file = NBTFile()

    entities_tag = generate_stands(stands)

    # Palettes
    # the nth entry is what u'blocks'->u''->u'state' refers to
    AIR = 0
    IMPULSE = 1
    UNCONDITIONAL = 2
    CONDITIONAL = 3
    palettes = [
        Palette("minecraft:air"),
        Palette("minecraft:command_block", conditional="false", facing="south"),
        Palette("minecraft:chain_command_block", conditional="false", facing="south"),
        Palette("minecraft:chain_command_block", conditional="true", facing="south")
    ]
    palette_tag = TAG_List(name="palette", type=TAG_Compound)
    for palette in palettes:
        palette_tag.tags.append(palette.convert_to_tag())

    # list of blocks
    # contains a list of blocks
    # each entry contains:
    # (optional) NBT TAG_Compound(u'nbt') containing blocks nbt data
    # TAG_List(u'pos') of TAG_Int containing X,Y,Z position
    # TAG_Int(u'state') containing u"palette" number
    blocks_tag = TAG_List(name="blocks", type=TAG_Compound)
    for i, blocks_ in enumerate(blocks):
        for j, block in enumerate(blocks_):
            pass
            if block.get("type", None) == "impulse":
                blocks_tag.tags.append(CommandBlock(i, 0, j, IMPULSE,
                                                    Command=block["command"]).convert_to_tag())
            if block.get("type", None) == "chain":
                type_ = CONDITIONAL if block.get("conditional", False) else UNCONDITIONAL
                blocks_tag.tags.append(CommandBlock(i, 0, j, type_,
                                                    Command=block["command"],
                                                    auto=1).convert_to_tag())

    # [X, Y, Z] size of the structure
    size_tag = gen_size_tag(blocks)

    # https://minecraft.gamepedia.com/Data_version#.dat_and_.nbt_files
    version_tag = TAG_Int(512, name="DataVersion")

    nbt_file.tags.append(size_tag)
    nbt_file.tags.append(entities_tag)
    nbt_file.tags.append(blocks_tag)
    nbt_file.tags.append(palette_tag)
    nbt_file.tags.append(version_tag)

    nbt_file.write_file(output_file_name)

    return nbt_file


def generate_stands(stands):
    entities_tag = TAG_List(name="entities", type=TAG_Compound)
    for stand in stands:
        stand_tag = TAG_Compound()
        nbt_tag = TAG_Compound()
        nbt_tag.name = "nbt"

        # type/gravity
        nbt_tag.tags.append(TAG_String(name="id", value="minecraft:armor_stand"))
        nbt_tag.tags.append(TAG_Byte(name="NoGravity", value=1))

        # name/tag
        tag_list_tag = TAG_List(name="Tags", type=TAG_String)
        tag_list_tag.tags.append(TAG_String(stand["name"]))
        nbt_tag.tags.append(tag_list_tag)
        nbt_tag.tags.append(TAG_String(name="CustomName", value=json.dumps({'text': stand["name"]})))
        nbt_tag.tags.append(TAG_Byte(name="CustomNameVisible", value=1))
        nbt_tag.tags.append(TAG_Byte(name="Marker", value=1))

        # position
        blockPos_tag = TAG_List(name="blockPos", type=TAG_Int)
        blockPos_tag.tags.extend([TAG_Int(int(x)) for x in stand["position"]])

        pos_tag = TAG_List(name="pos", type=TAG_Double)
        pos_tag.tags.extend([TAG_Double(x) for x in stand["position"]])

        stand_tag.tags.append(nbt_tag)
        stand_tag.tags.append(blockPos_tag)
        stand_tag.tags.append(pos_tag)

        entities_tag.tags.append(stand_tag)
    return entities_tag


def parse_mc_assembly(file):
    """
    Parse the MC assembly file and return a dictionary of
    lists of the following format:

    {'LABEL_NAME1': ['line_1', 'line_2', ..., line_n],
    'LABEL_NAME2': ['line_1', 'line_2', ..., line_n],
    ...
    'LABEL_NAMEN': ['line_1', 'line_2', ..., line_n]
    }
    """
    assembly_dict = OrderedDict()
    current_label = None

    for line_number, line in enumerate(file.splitlines(), start=1):

        line = line.strip()

        if line.startswith("jmp"):
            split_line = line.split()

            if len(split_line) == 2:
                lines = [
                    "U execute as @e[tag=LABEL] at @s run data merge block ~ ~ ~ {auto:1b}",
                    "U execute as @e[tag=LABEL] at @s run data merge block ~ ~ ~ {auto:0b}"
                ]

                for i in range(len(lines)):
                    lines[i] = lines[i].replace("LABEL", split_line[1])

            elif len(split_line) == 3:
                lines = [
                    "C execute as @e[tag=LABEL1] at @s run data merge block ~ ~ ~ {auto:1b}",
                    "C execute as @e[tag=LABEL1] at @s run data merge block ~ ~ ~ {auto:0b}",
                    "U execute if data block ~ ~ ~-3 {SuccessCount:0}",
                    "C execute as @e[tag=LABEL2] at @s run data merge block ~ ~ ~ {auto:1b}",
                    "C execute as @e[tag=LABEL2] at @s run data merge block ~ ~ ~ {auto:0b}"
                ]

                for i in range(len(lines)):
                    lines[i] = lines[i].replace("LABEL1", split_line[1])
                    lines[i] = lines[i].replace("LABEL2", split_line[2])

            else:
                raise SyntaxError("line {}: jmp: jmp takes 1 or 2 arguments".format(line_number))

            assembly_dict[current_label] += lines

        # parse labels
        elif line.startswith("."):
            # print ("found label: {}".format(line))

            current_label = line[1:]
            # print current_label
            assembly_dict[current_label] = []

        elif line.startswith("#") or not line:
            pass  # ignore comments and blank lines

        else:
            # print(current_label)
            if line[0] != "C" and line[0] != "U":
                raise SyntaxError(
                    "line {}: command must begin with U or C to specify conditionality".format(line_number))
            assembly_dict[current_label].append(line)

    return assembly_dict


def assemble(assembly, output_file_name):
    assembly_dict = parse_mc_assembly(assembly)

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

    return gen_command_block_structure(block_cols, stands, output_file_name)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print(f'usage: {sys.argv[0]} <input_file> <output_file>')
        exit(1)

    input_file_name = sys.argv[1]
    output_file_name = sys.argv[2]

    assemble(Path(input_file_name).read_text(), output_file_name)
