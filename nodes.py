# TODO move prefix to macros
program_prefix = "EX"
import macros

from tree_util import flatten

# score in which the result of an expression is stored
result_score = "{}_result".format(program_prefix)


class Node(object):
    total_nodes = 0

    @classmethod
    def next_id(cls):
        cls.total_nodes += 1
        return cls.total_nodes

    def __init__(self, content=None):
        if content is None:
            content = []

        self.id = Node.next_id()
        self.content = content

    def expand(self):
        """
        Convert node to CB assembly
        """
        expanded_nodes = Node.expand_list(self.content)
        return "\n".join([
            ".{}_BEGIN".format(program_prefix),
            f"U scoreboard objectives add {macros.objective} dummy",
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

        postfix_stack = flatten(self.expr_tree)

        def convert_to_id(val, obj):
            if val[0] != '$':
                assembly_lines.append(macros.set_to_literal(val, macros.objective, val))
                return '$' + val, macros.objective
            else:
                return val, obj

        def pop_variable():
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
            elif e in ('+', '-', '*', '/', '%', '<=', '==', '>=', '<', '>', '!=', 'and', 'or'):

                # print "before: ", stack
                val1, obj1 = convert_to_id(*pop_variable())
                val2, obj2 = convert_to_id(*pop_variable())

                if e in ('+', '-', '*', '/', '%'):
                    assembly_lines.append(macros.operation(
                        '=', tmp_name[1:], macros.objective, val1[1:], obj1))
                    assembly_lines.append(macros.operation(
                        e + '=', tmp_name[1:], macros.objective, val2[1:], obj2))
                elif e in ('<=', '==', '>=', '<', '>', '!='):
                    mc_operator = e
                    if e == '==':
                        # Mojang decided that two equal signs were too many
                        mc_operator = '='

                    if_or_unless = 'unless' if mc_operator == '!=' else 'if'

                    assembly_lines.append(f'U scoreboard players set {tmp_name[1:]} {macros.objective} 0')
                    assembly_lines.append(f'U execute {if_or_unless} score {val1[1:]} {obj1} {mc_operator} {val2[1:]} {obj2} '
                                          f'run scoreboard players set {tmp_name[1:]} {macros.objective} 1')
                elif e == 'and':
                    assembly_lines.append(f'U scoreboard players set {tmp_name[1:]} {macros.objective} 0')
                    assembly_lines.append(f'U execute unless score {val1} {obj1} matches 0 '
                                          f'run execute unless score {val2} {obj2} matches 0 '
                                          f'run scoreboard players set {tmp_name[1:]} {macros.objective} 1')
                elif e == 'or':
                    assembly_lines.append(f'U scoreboard players set {tmp_name[1:]} {macros.objective} 0')
                    assembly_lines.append(f'U execute unless score {val1} {obj1} matches 0 '
                                          f'run scoreboard players set {tmp_name[1:]} {macros.objective} 1')
                    assembly_lines.append(f'U execute unless score {val2} {obj2} matches 0 '
                                          f'run scoreboard players set {tmp_name[1:]} {macros.objective} 1')

                stack.append({'selector': tmp_name, 'objective': macros.objective})

            elif e == 'not':
                val, obj = convert_to_id(*pop_variable())

                assembly_lines.append(f'U scoreboard players set {tmp_name[1:]} {macros.objective} 0')
                assembly_lines.append(f'U execute if score {val[1:]} {obj} matches 0 '
                                      f'run scoreboard players set {tmp_name[1:]} {macros.objective} 1')

                stack.append({'selector': tmp_name, 'objective': macros.objective})
            else:  # is a value
                stack.append(e)

        # FIXME: this seems too complex, probably a better way..
        final_val = stack[0]
        if isinstance(final_val, dict):
            final_val, obj = pop_variable()
        else:
            obj = macros.objective
        if final_val[0] == '$':
            assembly_lines.append(macros.operation(
                '=', result_score, macros.objective, final_val[1:], obj))
        else:  # only a number remains
            assembly_lines.append(macros.set_to_literal(result_score, macros.objective, final_val))

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
