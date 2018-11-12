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
		properties.name = u"Properties"
		for k,v in self.properties.items():
			tag_prop = TAG_String(name=k, value=v)
			properties.tags.append(tag_prop)

		tag_name = TAG_String(name=u"Name", value=self.name)
		
		palette_compound = TAG_Compound()
		palette_compound.tags.append(properties)
		palette_compound.tags.append(tag_name)

		return palette_compound

class Block:
	def __init__(self, x, y, z, state):
		self.pos = TAG_List(name=u'pos', type=TAG_Int)
		self.pos.tags.extend(map(TAG_Int, (x, y, z)))
		self.state = state

	def convert_to_tag(self):
		tag = TAG_Compound()
		tag.tags.append(self.pos)
		tag.tags.append(TAG_Int(value=self.state, name=u'state'))
		return tag


class CommandBlock:
	def __init__(self, x, y, z, state, **nbt_data):

		def gen_tag(TAG_type, name, default):
			return TAG_type(name=name, value=nbt_data.get(name, default))
		
		self.pos = TAG_List(name=u'pos', type=TAG_Int)
		self.pos.tags.extend(map(TAG_Int, (x, y, z)))
		self.state = state
		self.nbt_data = TAG_Compound()
		self.nbt_data.name = "nbt"
		self.nbt_data.tags.append(gen_tag(TAG_Byte, 'conditionMet', 0))
		self.nbt_data.tags.append(gen_tag(TAG_Byte, 'auto', 0))
		self.nbt_data.tags.append(gen_tag(TAG_String, u'CustomName', u'@'))
		self.nbt_data.tags.append(gen_tag(TAG_Byte, u'powered', 0))
		self.nbt_data.tags.append(gen_tag(TAG_String, u'Command', u''))
		self.nbt_data.tags.append(gen_tag(TAG_String, u'id', u'Control'))
		self.nbt_data.tags.append(gen_tag(TAG_Int, u'SuccessCount', 0))
		self.nbt_data.tags.append(gen_tag(TAG_Byte, u'TrackOutput', 1))
		#print(self.nbt_data.pretty_tree())


	def convert_to_tag(self):
		tag = TAG_Compound()
		tag.tags.append(self.nbt_data)
		tag.tags.append(self.pos)
		tag.tags.append(TAG_Int(value=self.state, name=u'state'))
		return tag

def gen_size_tag(blocks):
	x = len(blocks)
	# y = x / 32
	# x = x % 32
	z = max(map(len, blocks))
	# if (y > 32):
	# 	print "Too many conditionals!"
	# if (z > 32):
	# 	print "Too large of block! ({})".format([bc for bc in blocks if len(bc) == z])
	size_tag = TAG_List(name=u"size", type=TAG_Int)
	# size_tag.tags.extend(map(TAG_Int, [x,1,z]))
	size_tag.tags.extend(map(TAG_Int, [min(x,32),1,min(z,32)]))
	return size_tag


def gen_command_block_structure(blocks, stands, file_name):
	"""
	Generate an nbt file with filled with blocks and entities

	blocks is a 2d array of dictionaries. 
	each entry corresponds to a block of code
	"""

	#print dir(TAG_Compound())

	nbt_file = NBTFile()

	# TODO: add armor stands
	entities_tag = TAG_List(name=u"entities", type=TAG_Compound)
	for stand in stands:
		stand_tag = TAG_Compound()
		nbt_tag = TAG_Compound()
		nbt_tag.name = u"nbt"
		
		#type/gravity
		nbt_tag.tags.append(TAG_String(name=u"id", value="ArmorStand"))
		nbt_tag.tags.append(TAG_Byte(name=u"NoGravity", value=1))

		#name/tag
		tag_list_tag = TAG_List(name=u"Tags", type=TAG_String)
		tag_list_tag.tags.append(TAG_String(stand["name"]))
		nbt_tag.tags.append(tag_list_tag)
		nbt_tag.tags.append(TAG_String(name="CustomName", value=stand["name"]))
		nbt_tag.tags.append(TAG_Byte(name="CustomNameVisible", value=0))
		nbt_tag.tags.append(TAG_Byte(name="Marker", value=1))		

		#position
		blockPos_tag = TAG_List(name=u"blockPos", type=TAG_Int)
		pos_tag = TAG_List(name=u"pos", type=TAG_Double)
		blockPos_tag.tags.extend(map(TAG_Int, map(int, stand["position"])))
		pos_tag.tags.extend(map(TAG_Double, stand["position"]))

		stand_tag.tags.append(nbt_tag)
		stand_tag.tags.append(blockPos_tag)
		stand_tag.tags.append(pos_tag)

		entities_tag.tags.append(stand_tag)

	# Palettes
	# the nth entry is what u'blocks'->u''->u'state' refers to
	AIR = 0
	IMPULSE = 1
	UNCONDITIONAL = 2
	CONDITIONAL = 3
	palettes = [
		Palette(u"minecraft:air"),
		Palette(u"minecraft:command_block", conditional=u"false", facing=u"south"),
		Palette(u"minecraft:chain_command_block", conditional=u"false", facing=u"south"),
		Palette(u"minecraft:chain_command_block", conditional=u"true", facing=u"south")
		]
	palette_tag = TAG_List(name=u"palette", type=TAG_Compound)
	for palette in palettes:
		palette_tag.tags.append(palette.convert_to_tag())

	# list of blocks
	# contains a list of blocks
	# each entry contains:
	# (optional) NBT TAG_Compound(u'nbt') containing blocks nbt data
	# TAG_List(u'pos') of TAG_Int containing X,Y,Z position
	# TAG_Int(u'state') containing u"palette" number
	blocks_tag = TAG_List(name=u"blocks", type=TAG_Compound)
	for i, blocks_ in enumerate(blocks):
		for j, block in enumerate(blocks_):
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

	author_tag = TAG_String(u"fetusdip", name=u"author")
	version_tag = TAG_Int(1, name=u"version")

	nbt_file.tags.append(size_tag)
	nbt_file.tags.append(entities_tag)
	nbt_file.tags.append(blocks_tag)
	nbt_file.tags.append(author_tag)
	nbt_file.tags.append(palette_tag)
	nbt_file.tags.append(version_tag)

	nbt_file.write_file(file_name)

	return nbt_file

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
	
	for line_number, line in enumerate(file, start=1):

		line = line.strip()


		#TODO: finish jmp
		if line.startswith("jmp"):
			split_line = line.split()

			if len(split_line) == 2:
				lines = [
				"U execute @e[tag=LABEL] ~ ~ ~ blockdata ~ ~ ~ {auto:1b}",
				"U execute @e[tag=LABEL] ~ ~ ~ blockdata ~ ~ ~ {auto:0b}"
				]

				for i in range(len(lines)):
					lines[i] = lines[i].replace("LABEL", split_line[1])
					

			elif len(split_line) == 3:
				lines = [
				"C execute @e[tag=LABEL1] ~ ~ ~ blockdata ~ ~ ~ {auto:1b}",
				"C execute @e[tag=LABEL1] ~ ~ ~ blockdata ~ ~ ~ {auto:0b}",
				"U testforblock ~ ~ ~-3 minecraft:chain_command_block 3 {SuccessCount:0}",
				"C execute @e[tag=LABEL2] ~ ~ ~ blockdata ~ ~ ~ {auto:1b}",
				"C execute @e[tag=LABEL2] ~ ~ ~ blockdata ~ ~ ~ {auto:0b}"
				]

				for i in range(len(lines)):
					lines[i] = lines[i].replace("LABEL1", split_line[1])
					lines[i] = lines[i].replace("LABEL2", split_line[2])


			else:
				raise SyntaxError("line {}: jmp: jmp takes 1 or 2 arguments".format(line_number))

			assembly_dict[current_label] += lines



		#parse labels
		elif line.startswith("."):
			#print ("found label: {}".format(line))

			current_label = line[1:]
			#print current_label
			assembly_dict[current_label] = []
		
		elif line.startswith("#") or not line:
			pass #ignore comments and blank lines
		
		else:
			#print(current_label)
			if line[0] != "C" and line[0] != "U":
				raise SyntaxError("line {}: command must begin with U or C to specify conditionality".format(line_number))
			assembly_dict[current_label].append(line)

	return assembly_dict

def main():
	# nbt_file = NBTFile(u"test_structure.nbt", u"rb")
	# print(nbt_file.pretty_tree())

	cba_name = "compiled_example.cba"
	nbt_name = cba_name.rsplit(".")[0] + ".nbt"
	mc_dir = "C:/Users/Adam/AppData/Roaming/.minecraft/saves/Command Block Compiler Testzone/structures/"

	with open(cba_name) as f:
		assembly_dict = parse_mc_assembly(f)
	
	print assemble(cba_name).pretty_tree()


	from shutil import copyfile
	copyfile(nbt_name, mc_dir + nbt_name)

def assemble(file_name):


	with open(file_name) as f:
		assembly_dict = parse_mc_assembly(f)
	
	block_cols = []
	stands = []
	for i, pair  in enumerate(assembly_dict.iteritems()):
		label, lines = pair
		stands.append({"name": label, "position": (i+0.5, 0, 0.5)})
		block_row = [{"type":"impulse", "command": ""}]
		for line in lines:
			conditionality = line[0] == "C"
			line = line[1:].strip()
			block_row.append({"type":"chain", "command":line, "conditional": conditionality})
		block_cols.append(block_row)

	return gen_command_block_structure(block_cols, stands, file_name.rsplit(".")[0] + ".nbt")

if __name__ == '__main__':
	main()
	# os.remove()


