#TODO move prefix to macros
program_prefix = "EX"
import macros

from tree_util import flatten
import ast

#score in which the result of an expression is stored
result_score = "{}_result".format(program_prefix)

class Node(object):
	def __init__(self, type_, content=()):
		self.content = list(content)
		self.type = type_

	def expand(self):
		"""
		Convert node to CB assembly
		"""
		expanded_nodes = Node.expand_list(self.content);
		return "\n".join([
			".{}_BEGIN".format(program_prefix),
			expanded_nodes
			])

	@staticmethod
	def expand_list(list_):
		#print [(node) for node in list_]
		#print [(node.type) for node in list_]
		return "\n".join([node.expand() for node in list_])

class EmptyNode(Node):
	def __init__(self, *content):
		super(EmptyNode, self).__init__("empty")
		#print "creating EmptyNode with content: {}".format(str(content))
		self.content = content

	def expand(self):
		"""
		print the content for debugging
		"""
		#print(str(content))
		return ''
		
		


class ExpressionNode(Node):
	def __init__(self, expr_tree):
		super(ExpressionNode, self).__init__("expression")
		self.id = ExpressionNode.count
		ExpressionNode.count += 1
		self.expr_tree = expr_tree

	def expand(self):
		# if (expression):

		is_cmp_op = lambda e: e in ('<=', '==', '>=', '<', '>')
		is_math_op = lambda e: e in "+-*/%"
		is_and_or_op = lambda e: e in ('and','or')
		
		is_op = lambda e: is_cmp_op(e) or is_math_op(e) or is_and_or_op(e)

		# print flatten(self.expr_tree)
		stack = []
		num = 0
		tmp_prefix = "${}_expr_{}_".format(program_prefix, self.id)
		tmp_name = tmp_prefix + str(num)
		expansion = []
		
		def convert_to_id(val):
			if val[0] != '$':
				expansion.append(macros.set(val, macros.objective, val))
				return '$' + val
			else:
				return val

		#evaluate postfix expression
		postfix_stack = flatten(self.expr_tree)
		import copy
		postfix_expr = copy.deepcopy(postfix_stack[::-1])
		while postfix_stack:
			e = postfix_stack.pop()
			# print "found", e
			if is_op(e):
				# print "is_op"
				# pop 2 values from stack.
				# if both are constant push the result of that
				# on the stack (no need to compute that in-game).
				# else expand the expression to compute and store
				# the values into a temporary score and push
				# the name of the score on the stack
				tmp_name = tmp_prefix + str(num)

				# print "before: ", stack
				val1 = stack.pop()
				val2 = stack.pop()
				
				if val1[0] != '$' and val2[0] != '$':
					if is_and_or_op(e):
						ast.literal_eval(str(int(bool(eval(val1 + ' ' + e + ' ' + val2)))))
					else:
						ast.literal_eval(str(int(eval(val1 + ' ' + e + ' ' + val2))))
				else:
					val1 = convert_to_id(val1)
					val2 = convert_to_id(val2)
					if is_math_op(e):
						expansion.append(macros.operation(
								'=', tmp_name[1:], macros.objective, val1[1:], macros.objective))
						expansion.append(macros.operation(
								e + '=', tmp_name[1:], macros.objective, val2[1:], macros.objective))

						stack.append(tmp_name)
					elif is_cmp_op(e):
						cmp_map = {
							'<': ('*', '-1'),
							'<=': ('*', '0'),
							'>': ('1', '*'),
							'>=': ('0', '*'),
							'==': ('0', '0')
						}
						expansion.append(macros.operation(
								'=', tmp_name[1:], macros.objective, val1[1:], macros.objective))
						expansion.append(macros.operation(
								'-=', tmp_name[1:], macros.objective, val2[1:], macros.objective))
						expansion.append(macros.cmp(
								tmp_name[1:], macros.objective, *cmp_map[e]))
						expansion.append("C scoreboard players set {} {} 1".format(tmp_name[1:], macros.objective))
						expansion.append("U testforblock ~ ~ ~-2 minecraft:chain_command_block 3 {SuccessCount:0}")
						expansion.append("C scoreboard players set {} {} 0".format(tmp_name[1:], macros.objective))
						stack.append(tmp_name)
					elif is_and_or_op(e):
						#TODO convert to bool val1, val2 (and push as tmp vars)
						expansion.append(macros.bool_of(val1[1:], macros.objective, tmp_name[1:] + "_L", macros.objective))
						expansion.append(macros.bool_of(val2[1:], macros.objective, tmp_name[1:] + "_R", macros.objective))
						if e == 'and':
							postfix_stack.append('==')
							postfix_stack.append('+')
							postfix_stack.append(tmp_name + "_L")
							postfix_stack.append(tmp_name + "_R")
							postfix_stack.append('2')
						elif e == 'or':
							postfix_stack.append('>=')
							postfix_stack.append('+')
							postfix_stack.append(tmp_name + "_L")
							postfix_stack.append(tmp_name + "_R")
							postfix_stack.append('1')
							
						

				num += 1
				tmp_prefix = "${}_expr_{}_".format(program_prefix, self.id)
				
			else: #!is_op(e)
				stack.append(e)

		final_val = stack[0]
		if final_val[0] == '$' and len(postfix_expr) > 1:
			expansion.append(macros.operation(
				'=', result_score, macros.objective, tmp_name[1:], macros.objective))
		elif final_val[0] == '$' and len(postfix_expr) == 1:
			expansion.append(macros.operation(
				'=', result_score, macros.objective, postfix_expr[0][1:], macros.objective))
		else: #only a number remains
			expansion.append(macros.set(result_score, macros.objective, final_val))

		expansion.append(macros.cmp(result_score, macros.objective, '1', '*'))

		return "\n".join(expansion)

ExpressionNode.count = 0




class AssignNode(Node):
	def __init__(self, var, operator, expression):
		super(AssignNode, self).__init__("assign")
		self.var = var.strip('$')
		self.operator = operator
		self.expression = expression
		#print ("Expression: {}".format(expression))

	def expand(self):
		# print "expanding assign"
		# print "expression: {}".format(self.expression.expand())
		assign_tmp = macros.operation(self.operator, self.var, macros.objective, result_score, macros.objective)
		return "\n".join([
			str(self.expression.expand()),
			assign_tmp
			])

class MacroNode(Node):
	def __init__(self, macro_name, args):
		super(MacroNode, self).__init__("macro")
		self.macro_name = macro_name
		self.args = args
		#print "args:".format(str(args))

	def expand(self):
		from macros import macros_dict
		macro = macros_dict[self.macro_name](*self.args)
		# print macro
		if macro is None:
			return ''
		elif type(macro) == type(''):
			return macro
		else:
			raise ValueError("Macro must return string or None, instead got {}".format(type(macro)))

class CommandNode(Node):
	def __init__(self, command):
		super(CommandNode, self).__init__("command")
		self.command = "U " + command

	def expand(self):
		return self.command

class WhileNode(Node):
	def __init__(self, condition, body):
		super(WhileNode, self).__init__("while_statement")

		self.body = body
		self.condition = condition
		
		self.id = WhileNode.count
		WhileNode.count += 1


	def expand(self):

		#labels used by this while loop
		# WC: WHILE_CHECK
		# WB: WHILE_BODY
		# WE: WHILE_END

		self.WC = "{}_WC_{}".format(program_prefix, self.id)
		self.WB = "{}_WB_{}".format(program_prefix, self.id)
		self.WE = "{}_WE_{}".format(program_prefix, self.id)

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
	def __init__(self, condition, body):
		super(IfNode, self).__init__("if_statement")

		self.body = body
		self.condition = condition
		
		self.id = IfNode.count
		IfNode.count += 1

		#labels used by this if statement
		# IB: IF_BEGIN
		# IE: IF_END
		self.IB = "{}_IB_{}".format(program_prefix, self.id)
		self.IE = "{}_IE_{}".format(program_prefix, self.id)


	def expand(self):
		self.IB = "{}_IB_{}".format(program_prefix, self.id)
		self.IE = "{}_IE_{}".format(program_prefix, self.id)
		
		expansion = "\n".join([
			str(self.condition.expand()),
			'jmp {} {}'.format(self.IB, self.IE),
			'.' + self.IB,
			str(Node.expand_list(self.body)),
			'jmp {}'.format(self.IE),
			'.' + self.IE
		])
		return expansion
IfNode.count = 0