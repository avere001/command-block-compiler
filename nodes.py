# TODO move prefix to macros
program_prefix = "EX"
import macros

from tree_util import flatten

# score in which the result of an expression is stored
result_score = "{}_result".format(program_prefix)


class Node(object):
    total_nodes = 0

    def __init__(self, content=None):
        if content is None:
            content = []

        self.id = self.total_nodes
        self.total_nodes += 1

        self.content = content

    def expand(self):
        """
        Convert node to CB assembly
        """
        expanded_nodes = Node.expand_list(self.content)
        return "\n".join([
            ".{}_BEGIN".format(program_prefix),
            expanded_nodes
        ])

    @staticmethod
    def expand_list(list_):
        # print [(node) for node in list_]
        # print [(node.type) for node in list_]
        return "\n".join([node.expand() for node in list_])


class EmptyNode(Node):
    def __init__(self, *content):
        super(EmptyNode, self).__init__("empty")
        # print "creating EmptyNode with content: {}".format(str(content))
        self.content = content

    def expand(self):
        """
        print the content for debugging
        """
        # print(str(content))
        return ''


class ExpressionNode(Node):

    def __init__(self, expr_tree):
        super().__init__()
        self.expr_tree = expr_tree

    def expand(self):

        stack = []
        num = 0
        tmp_prefix = "${}_expr_{}_".format(program_prefix, self.id)
        assembly_lines = []

        # evaluate postfix expression
        postfix_stack = flatten(self.expr_tree)
        # print postfix_stack
        import copy
        postfix_expr = copy.deepcopy(postfix_stack[::-1])

        def convert_to_id(val, obj):
            if val[0] != '$':
                assembly_lines.append(macros.set(val, macros.objective, val))
                return '$' + val, macros.objective
            else:
                return val, obj

        def get_value():
            val = stack.pop()
            # print val, type(val)
            if type(val) == type(''):
                return val, macros.objective
            else:
                return val['selector'], val.get('objective', macros.objective)

        while postfix_stack:

            num += 1
            tmp_name = tmp_prefix + str(num)
            # print tmp_name

            e = postfix_stack.pop()
            # print "found", e
            if type(e) in [MacroNode, CommandNode]:
                assembly_lines.append(e.expand())
                assembly_lines.append(macros.operation(
                    '=', tmp_name[1:], macros.objective, result_score, macros.objective))
                stack.append({'selector': tmp_name, 'objective': macros.objective})
            elif e in ('+', '-', '*', '/', '%', '<=', '==', '>=', '<', '>'):

                # print "before: ", stack
                val1, obj1 = get_value()
                val2, obj2 = get_value()

                if val1[0] != '$' and val2[0] != '$':
                    stack.append(str(int(eval(val1 + ' ' + e + ' ' + val2))))
                else:
                    val1, obj1 = convert_to_id(val1, obj1)
                    val2, obj2 = convert_to_id(val2, obj2)
                    if e in "+-*/%":
                        assembly_lines.append(macros.operation(
                            '=', tmp_name[1:], macros.objective, val1[1:], obj1))
                        assembly_lines.append(macros.operation(
                            e + '=', tmp_name[1:], macros.objective, val2[1:], obj2))

                        stack.append({'selector': tmp_name, 'objective': macros.objective})
                    elif e in ('<=', '==', '>=', '<', '>'):
                        mc_operator = e
                        if e == '==':
                            # Mojang decided that two equal signs were too many
                            mc_operator = '='

                        assembly_lines.append(f'U scoreboard players set {tmp_name[1:]} {macros.objective} 0')
                        assembly_lines.append(f'U execute if score {val1[1:]} {obj1} {mc_operator} {val2[1:]} {obj2} '
                                              f'run scoreboard players set {tmp_name[1:]} {macros.objective} 1')
                        stack.append({'selector': tmp_name, 'objective': macros.objective})
            elif e == '!=':
                val1, obj1 = get_value()
                val2, obj2 = get_value()
                # != is equivalent to (val1 == val2) == 0
                postfix_stack.append('==')
                postfix_stack.append('==')
                postfix_stack.append({'selector': val1, 'objective': obj1})
                postfix_stack.append({'selector': val2, 'objective': obj2})
                postfix_stack.append('0')
            elif e == 'not':
                val, obj = get_value()
                postfix_stack.append('==')
                postfix_stack.append({'selector': val, 'objective': obj})
                postfix_stack.append('0')
            elif e in ('and', 'or'):
                val1, obj1 = get_value()
                val2, obj2 = get_value()

                if val1[0] != '$' and val2[0] != '$':
                    stack.append(str(int(bool(eval(val1 + ' ' + e + ' ' + val2)))))
                else:
                    val1, obj1 = convert_to_id(val1, obj1)
                    val2, obj2 = convert_to_id(val2, obj2)

                    assembly_lines.append(macros.bool_of(val1[1:], obj1, tmp_name[1:] + "_L", macros.objective))
                    assembly_lines.append(macros.bool_of(val2[1:], obj2, tmp_name[1:] + "_R", macros.objective))
                    if e == 'and':
                        # and is equivalant to bool(val1) + bool(val2) == 2
                        postfix_stack.append('==')
                        postfix_stack.append('+')
                        postfix_stack.append({'selector': tmp_name + "_L", 'objective': macros.objective})
                        postfix_stack.append({'selector': tmp_name + "_R", 'objective': macros.objective})
                        postfix_stack.append('2')
                    elif e == 'or':
                        # or is equivalant to bool(val1) + bool(val2) >= 1
                        postfix_stack.append('>=')
                        postfix_stack.append('+')
                        postfix_stack.append({'selector': tmp_name + "_L", 'objective': macros.objective})
                        postfix_stack.append({'selector': tmp_name + "_R", 'objective': macros.objective})
                        postfix_stack.append('1')
            else:  # is a value
                stack.append(e)

        # FIXME: this seems too complex, probably a better way..
        final_val = stack[0]
        if isinstance(final_val, dict):
            final_val, obj = get_value()
        if final_val[0] == '$':
            assembly_lines.append(macros.operation(
                '=', result_score, macros.objective, final_val[1:], obj))
        else:  # only a number remains
            assembly_lines.append(macros.set(result_score, macros.objective, final_val))

        assembly_lines.append(f'U execute if score {result_score} {macros.objective} matches 1')

        return "\n".join(assembly_lines)


class AssignNode(Node):
    def __init__(self, var, operator, expression):
        super().__init__()
        self.var = var
        self.operator = operator
        self.expression = expression

    def expand(self):
        assign_tmp = macros.operation(self.operator, self.var['selector'].strip('$'),
                                      self.var.get('objective', macros.objective), result_score, macros.objective)
        return "\n".join([
            str(self.expression.expand()),
            assign_tmp
        ])


class MacroNode(Node):
    def __init__(self, macro_name, args):
        super().__init__()
        self.macro_name = macro_name
        self.args = args
        self.context = "statement"

    def expand(self):
        from macros import macros_dict
        macro = macros_dict[self.macro_name](*self.args)
        macro = macro if macro is not None else ''

        if not isinstance(macro, str):
            raise ValueError("Macro must return string or None, instead got {}".format(type(macro)))
        if self.context == "statement":
            return macro
        else:
            expansion = []
            expansion += [f'U scoreboard players set {result_score} {macros.objective} 0']
            expansion += [macro]
            expansion += [f'C scoreboard players set {result_score} {macros.objective} 1']
            return "\n".join(expansion)


class CommandNode(Node):
    def __init__(self, command):
        super(CommandNode, self).__init__()
        self.command = command
        self.context = "statement"

    def expand(self):
        if self.context == "statement":
            return "U " + self.command
        else:
            expansion = []
            expansion += ["U scoreboard players set {} {} 0".format(result_score, macros.objective)]
            expansion += ["U " + self.command.strip()]
            expansion += ["C scoreboard players set {} {} 1".format(result_score, macros.objective)]
            return "\n".join(expansion)


class WhileNode(Node):
    def __init__(self, condition, body):
        super(WhileNode, self).__init__()
        self.condition = condition
        self.body = body

    def expand(self):
        # labels used by this while loop
        # WC: WHILE_CHECK
        # WB: WHILE_BODY
        # WE: WHILE_END

        self.WC = "{}_WC_{}".format(program_prefix, self.id)
        self.WB = "{}_WB_{}".format(program_prefix, self.id)
        self.WE = "{}_WE_{}".format(program_prefix, self.id)

        # print self.condition

        expansion = "\n".join([
            'jmp ' + self.WC,
            '.' + self.WC,
            str(self.condition.expand()),
            'jmp {} {}'.format(self.WB, self.WE),
            '.' + self.WB,
            str(Node.expand_list(self.body)),
            'jmp {}'.format(self.WC),
            '.' + self.WE
        ])
        return expansion


WhileNode.count = 0


class IfNode(Node):
    def __init__(self, condition, body, else_body=None):
        super().__init__()

        self.body = body
        self.condition = condition
        self.else_body = else_body

    def expand(self):
        # labels used by this if statement
        label_body = f'{program_prefix}_IB_{self.id}'
        label_else = f'{program_prefix}_IL_{self.id}'
        label_end = f'{program_prefix}_IE_{self.id}'

        expansion = []

        expansion = [
            self.condition.expand(),
            'jmp {} {}'.format(label_body, label_else if self.else_body else label_end),
            '.' + label_body,
            Node.expand_list(self.body),
            'jmp {}'.format(label_end)
        ]

        if self.else_body:
            expansion += [
                '.' + label_else,
                Node.expand_list(self.else_body),
                'jmp {}'.format(label_end),
            ]

        expansion += ['.' + label_end]

        return "\n".join(expansion)


IfNode.count = 0
