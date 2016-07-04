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

# adapted from Mu Mind's answer @ http://stackoverflow.com/questions/12472338/flattening-a-list-recursively
def flatten(S):
    if isinstance(S, list):
        if S == []:
            return S
        if isinstance(S[0], list):
            return flatten(S[0]) + flatten(S[1:])
        return S[:1] + flatten(S[1:])
    else:
        return [S]
