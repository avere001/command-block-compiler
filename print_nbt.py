from nbt.nbt import *


def main():
    # nbt_file = NBTFile("../werewolf/werewolf.nbt", "rb")
    nbt_file = NBTFile("werewolf.nbt", "rb")
    print((nbt_file.pretty_tree()))


if __name__ == '__main__':
    main()
