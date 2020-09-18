from nodes import *
from ply.lex import TOKEN

"""
This module scans and parses cbc scripts
"""

"""
Lex definitions (scanner)
"""

tokens = (
    'WHILE', 'DO', 'END',
    'IF', 'THEN', 'ELSE',
    'COMMAND',
    'LPAREN', 'RPAREN', 'COMMA',
    'FUNC_ID', 'ARG', 'ID', 'NUM',
    'ASSIGN', 'ADD_ASSIGN', 'MUL_ASSIGN', 'MOD_ASSIGN', 'SUB_ASSIGN', 'DIV_ASSIGN',
    'ADD', 'SUB', 'MUL', 'DIV', 'MOD',
    'AND', 'OR', 'NOT',
    'LT', 'GT', 'LTE', 'GTE', 'EQ', 'NE',
    'TRUE', 'FALSE'
)

states = (
    ('funcy', 'exclusive'),
)

t_COMMAND = r'`[^`]*`'
# selector = r'(@[prae](\[[^\]]*\])?)|([A-Za-z0-9_][A-Za-z0-9_]*)'
# t_ID = r'\$(' + selector + r')(:[A-Za-z0-9_][A-Za-z0-9_]*)?'
t_ID = r'((@[prae](\[[^\]]*\])?)|(\$[A-Za-z0-9_][A-Za-z0-9_]*))(:[A-Za-z0-9_][A-Za-z0-9_]*)?'
non_zero_num = r'-?[1-9][0-9]*'
t_NUM = r'0' + r'|' + non_zero_num

# assignment operators
t_ASSIGN = r'='
t_ADD_ASSIGN = r'\+='
t_SUB_ASSIGN = r'-='
t_MUL_ASSIGN = r'\*='
t_DIV_ASSIGN = r'/='
t_MOD_ASSIGN = r'%='

# comparison operators
t_LT = r'<'
t_LTE = r'<='
t_GT = r'>'
t_GTE = r'>='
t_EQ = r'=='
t_NE = r'!='

# math operators
t_ADD = r'\+'
t_SUB = r'-'
t_MUL = r'\*'
t_DIV = r'/'
t_MOD = r'%'


# bool operators
def t_AND(t): 'and'; return t;


def t_OR(t): 'or'; return t;


def t_NOT(t): 'not'; return t;


def t_TRUE(t): 'true'; return t;


def t_FALSE(t): 'false'; return t;


# Ignore whitespace
t_ignore = " \t"


def t_WHILE(t): 'while'; return t;


def t_DO(t): 'do'; return t;


def t_IF(t): 'if'; return t;


def t_THEN(t): 'then'; return t;


def t_ELSE(t): 'else'; return t;


def t_END(t): 'end'; return t;


def t_FUNC_ID(t):
    r'[A-Za-z][A-Za-z0-9_]*'
    t.lexer.begin('funcy')
    return t


def t_COMMENT(t):
    r'\#.*'
    pass


def t_newline(t):
    r'\n+'
    t.lexer.lineno += t.value.count("\n")


def t_error(t):
    # print("Illegal character '%s'" % t.value[0])
    t.lexer.skip(1)


"""
Macros
"""
t_funcy_INITIAL_LPAREN = r'\('
# t_funcy_ARG = r'[^,()][^,()]*'
# t_funcy_ARG = r'"[^\"]*"|\'[^\']*\''
# t_funcy_ARG = r"'(\'|[^'])*'"
double_quote_string = r'\"([^\\\n]|(\\.))*?\"'
single_quote_string = r'\'([^\\\n]|(\\.))*?\''
argument = r'(' + double_quote_string + r')' + r'|' + \
           r'(' + single_quote_string + r')' + r'|' + \
           r'(' + t_ID + r')' + r'|' + \
           r'(' + r'~?' + non_zero_num + r')'


# string constant recognition from PLY ansi C example
# modified to include single quotes
@TOKEN(argument)
def t_funcy_ARG(t):
    # FIXME can't escape a string that begins with $ or ~
    import ast
    if t.value[0] not in ['$', '~']:
        t.value = str(ast.literal_eval(t.value))
    return t


t_funcy_COMMA = r','
t_funcy_ignore = ""


def t_funcy_error(t):
    # print("Illegal character '%s'" % t.value[0])
    t.lexer.skip(1)


def t_funcy_INITIAL_RPAREN(t):
    r'\)'
    t.lexer.begin('INITIAL')
    return t


"""
Yacc definitions (parser)
"""
precedence = (
    ('left', 'OR'),
    ('left', 'AND'),
    ('nonassoc', 'GT', 'LT', 'LTE', 'GTE', 'EQ', 'NE'),
    ('left', 'ADD', 'SUB'),
    ('left', 'MUL', 'DIV', 'MOD'),
    ('right', 'NOT')
)


def p_start(t):
    'start : statements'
    t[0] = t[1]


def p_statements(t):
    '''
    statements : statements statement
               | statement
    '''
    if len(t) == 2:
        t[0] = [t[1]]
    else:
        t[0] = t[1] + [t[2]]


def p_statement(t):
    '''statement : command
                 | while_statement
                 | if_statement
                 | assign_statement
                 | func
    '''
    t[0] = t[1]


def p_assign_statement(t):
    '''
    assign_statement : id ASSIGN root_expression
                     | id ADD_ASSIGN root_expression
                     | id SUB_ASSIGN root_expression
                     | id DIV_ASSIGN root_expression
                     | id MUL_ASSIGN root_expression
                     | id MOD_ASSIGN root_expression
    '''
    # print "assign_statement"
    t[0] = AssignNode(t[1], t[2], t[3])


def p_root_expression(t):
    'root_expression : expression'
    t[0] = ExpressionNode(t[1])


def p_not_expression(t):
    '''expression : NOT expression
    '''
    t[0] = [t[1], t[2]]


def p_expression(t):
    '''expression : expression ADD expression %prec ADD
                  | expression SUB expression %prec SUB
                  | expression MUL expression %prec MUL
                  | expression DIV expression %prec DIV
                  | expression MOD expression %prec MOD
                  | expression GT expression  %prec GT
                  | expression GTE expression %prec GTE
                  | expression LT expression  %prec LT
                  | expression LTE expression %prec LTE
                  | expression NE expression  %prec NE
                  | expression EQ expression  %prec EQ
                  | expression OR expression  %prec OR
                  | expression AND expression %prec AND
                  | LPAREN expression RPAREN
                  | id
                  | const
                  | command
                  | func
    '''
    if len(t) == 2:
        if type(t[1]) in [MacroNode, CommandNode]:
            t[1].context = "expression"
        t[0] = t[1]
    elif t[1] == '(':
        t[0] = t[2]
    else:
        t[0] = [t[2], t[1], t[3]]
    # print t[0]


def p_id(t):
    ''' id : ID '''
    ident = t[1]
    if ident[0] == '@':
        ident = '$' + ident
    if ':' in ident:
        selector, objective = ident.split(':')
        t[0] = {'selector': selector, 'objective': objective}
    else:
        t[0] = {'selector': ident}


def p_const(t):
    '''const : NUM
             | TRUE
             | FALSE'''
    t[0] = {'true': '1', 'false': '0'}.get(t[1], t[1])


def p_func(t):
    '''func : FUNC_ID LPAREN args RPAREN'''
    t[0] = MacroNode(t[1], t[3])


def p_command(t):
    '''command : COMMAND'''
    t[0] = CommandNode(t[1][1:-1])


def p_args(t):
    '''args : arg
            | args COMMA arg
    '''
    if len(t) == 2:
        t[0] = [t[1]]
    else:
        t[0] = t[1] + [t[3]]


# FIXME: don't use a single generic terminal
def p_arg(t):
    '''arg : ARG'''
    t[0] = t[1]
    # print "found ARG: {}".format(t[0])


def p_if_statement(t):
    'if_statement : IF root_expression THEN statements END'
    t[0] = IfNode(condition=t[2], body=t[4])


def p_if_else_statement(t):
    'if_statement : IF root_expression THEN statements ELSE statements END'
    t[0] = IfNode(condition=t[2], body=t[4], else_body=t[6])


def p_while_statement(t):
    'while_statement : WHILE root_expression DO statements END'
    t[0] = WhileNode(t[2], t[4])


def p_error(t):
    if t:
        print("Syntax error at {} on line {}".format(t.value, t.lineno))
    else:
        print("Syntax error: Unexpected end of input (Perhaps a missing 'end')")


def compile(input_file, compiled_name):
    with open(input_file) as f:
        ast = Node("root", parser.parse(f.read()))

    with open(compiled_name + ".cba", "w") as f:
        f.write(ast.expand())

    return compiled_name + ".cba"


def concat_assembly(file_names, output_file_name):
    file_contents = []
    file_headers = []
    for file_name in file_names:
        with open(file_name) as i_file:
            file_content = i_file.read()
            header = file_content.split('\n')[0]

            file_contents.append(file_content)
            file_headers.append(header)

    with open(output_file_name, 'w') as o_file:
        # print file_headers
        print('.MIXED_{}'.format(file_headers[0][1:]), file=o_file)  # get rid of .
        for header in file_headers:
            print('jmp {}'.format(header[1:]), file=o_file)  # get rid of . in header
        for file_content in file_contents:
            print(file_content, file=o_file)

    return output_file_name


if __name__ == '__main__':

    import sys

    if len(sys.argv) != 3:
        print("Incorrect number of arguments")
        print("usage:   {} <input_file> <structure_name>".format(sys.argv[0]))
        print("example: {} example.cbc example_structure".format(sys.argv[0]))
        exit(1)

    input_file = sys.argv[1]
    compiled_name = sys.argv[2]

    import ply.lex as lex
    import ply.yacc as yacc

    # lexer = lex.lex()
    # with open(input_file) as f:
    #     lex.input(f.read())
    #     while True:
    #         tok = lexer.token()
    #         if not tok: 
    #             break      # No more input
    #         print(tok)

    macros.include(input_file)

    assembly_files = []
    while macros.includes:
        lexer = lex.lex()
        parser = yacc.yacc(debug=1)
        import os

        curr_file = macros.includes.pop()
        print("compiling {}".format(curr_file))
        assembly_files.append(compile(curr_file, curr_file))

    concat_assembly(assembly_files, compiled_name + ".cba")

    import assemble

    assemble.assemble(compiled_name + ".cba")

    from shutil import copyfile

    copyfile(compiled_name + ".nbt", "/home/ubuntu/workspace/structures/" + compiled_name + ".nbt")
