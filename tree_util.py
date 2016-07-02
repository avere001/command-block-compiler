def print_tree(L, indent=""):
    """
    Print out the list style tree (e.g. ['root',['subtree']])

    adapted from https://mail.python.org/pipermail/tutor/2009-July/070178.html
    """
    for i in L:
        if isinstance(i,str):
            print indent, "Root:", i
        else:
            print indent, '--Subtree: ', i
            print_tree(i, indent+"    ")

def flatten(tree):

    def _flatten(tree):
        if type(tree) == type(""):
            return tree
        else:
            return " ".join([_flatten(e) for e in tree])

    return _flatten(tree).split()