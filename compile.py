#!/usr/bin/env python
from pathlib import Path

from nodes import *
from ply.lex import TOKEN

import sys
import assemble

import ply.lex as lex
import ply.yacc as yacc

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
double_quote_string = r'\"([^\\\n]|(\\.))*?\"'
single_quote_string = r'\'([^\\\n]|(\\.))*?\''
argument = fr'({double_quote_string})|' \
           fr'({single_quote_string})|' \
           fr'({t_ID})|' \
           fr'(~?{non_zero_num})'


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
    """start : statements"""
    t[0] = t[1]


def p_statements(t):
    """
    statements : statements statement
               | statement
    """
    if len(t) == 2:
        t[0] = [t[1]]
    else:
        t[0] = t[1] + [t[2]]


def p_statement(t):
    """statement : command
                 | while_statement
                 | if_statement
                 | assign_statement
                 | func
    """
    t[0] = t[1]


def p_assign_statement(t):
    """
    assign_statement : id ASSIGN root_expression
                     | id ADD_ASSIGN root_expression
                     | id SUB_ASSIGN root_expression
                     | id DIV_ASSIGN root_expression
                     | id MUL_ASSIGN root_expression
                     | id MOD_ASSIGN root_expression
    """
    # print "assign_statement"
    t[0] = AssignNode(t[1], t[2], t[3])


def p_root_expression(t):
    """root_expression : expression"""
    t[0] = ExpressionNode(t[1])


def p_not_expression(t):
    """expression : NOT expression
    """
    t[0] = [t[1], t[2]]


def p_expression(t):
    """expression : expression ADD expression %prec ADD
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
    """
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
    """ id : ID """
    ident = t[1]
    if ident[0] == '@':
        ident = '$' + ident
    if ':' in ident:
        selector, objective = ident.split(':')
        t[0] = {'selector': selector, 'objective': objective}
    else:
        t[0] = {'selector': ident}


def p_const(t):
    """const : NUM
             | TRUE
             | FALSE"""
    t[0] = {'true': '1', 'false': '0'}.get(t[1], t[1])


def p_func(t):
    """func : FUNC_ID LPAREN args RPAREN"""
    t[0] = MacroNode(t[1], t[3])


def p_command(t):
    """command : COMMAND"""
    t[0] = CommandNode(t[1][1:-1])


def p_args(t):
    """args : arg
            | args COMMA arg
    """
    if len(t) == 2:
        t[0] = [t[1]]
    else:
        t[0] = t[1] + [t[3]]


# FIXME: don't use a single generic terminal
def p_arg(t):
    """arg : ARG"""
    t[0] = t[1]
    # print "found ARG: {}".format(t[0])


def p_if_statement(t):
    """if_statement : IF root_expression THEN statements END"""
    t[0] = IfNode(condition=t[2], body=t[4])


def p_if_else_statement(t):
    """if_statement : IF root_expression THEN statements ELSE statements END"""
    t[0] = IfNode(condition=t[2], body=t[4], else_body=t[6])


def p_while_statement(t):
    """while_statement : WHILE root_expression DO statements END"""
    t[0] = WhileNode(t[2], t[4])


def p_error(t):
    if t:
        print("Syntax error at {} on line {}".format(t.value, t.lineno))
    else:
        print("Syntax error: Unexpected end of input (Perhaps a missing 'end')")


def compile_cbc(input_file):
    assemblies = [Node(parser.parse(Path(input_file).read_text())).expand()]
    seen_includes = set()
    while macros.includes:
        include = macros.includes.pop()
        if include not in seen_includes:
            seen_includes.add(include)
            assemblies.append(Node(parser.parse(Path(include).read_text())).expand())
    return concat_assembly(assemblies)


def concat_assembly(assemblies):
    assembly_headers = [x.splitlines()[0] for x in assemblies]
    new_assembly_parts = [f'.MIXED_{assembly_headers[0][1:]}']

    for header in assembly_headers:
        new_assembly_parts.append(f'jmp {header[1:]}')
    for body in assemblies:
        new_assembly_parts.append(body)

    return '\n'.join(new_assembly_parts)


if __name__ == '__main__':

    if len(sys.argv) != 3:
        print("Incorrect number of arguments")
        print(f"usage:   {sys.argv[0]} <input_file> <structure_name>")
        print(f"example: {sys.argv[0]} example.cbc example_structure")
        exit(1)

    input_file_name = sys.argv[1]
    output_file_name = sys.argv[2]

    lexer = lex.lex()
    parser = yacc.yacc(debug=1)

    print(f"compiling {input_file_name}")
    assembly_file = compile_cbc(input_file_name)
    Path(input_file_name.rsplit('.', maxsplit=1)[0] + '.cba').write_text(assembly_file)
    assemble.assemble(assembly_file, output_file_name).write_file()
