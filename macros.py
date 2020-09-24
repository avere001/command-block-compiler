import nodes

objective = "vars"
compiler_objective = "_{}".format(objective)


############### debug ##############################
def print_scores(*args):
    """
    print player scores (in game)
    """
    template = '"{0}: ",{{"score":{{"name":"{0}","objective":"{1}"}}}}'
    joined_scores = ",".join([template.format(arg, objective) for arg in args])
    return "".join([
        "U tellraw @a [",
        joined_scores,
        "]"])


def print_args(*args):
    """
    print the arguments passed into a macro (during compilation)
    """
    print(args)


############## compiler environment #######################################
def set_objective(objective_):
    global objective
    objective = objective_
    compiler_objective = "_{}".format(objective)
    if len(compiler_objective) > 10:
        print("warning: a long objective name will limit the number of statements in a program")


def set_prefix(prefix):
    nodes.program_prefix = prefix
    set_objective("{}_v".format(prefix))
    nodes.result_score = "{}_result".format(prefix)


##################### argument validation #############
def validate_coord(coord):
    new_coord = coord
    if coord[0] == '~':
        new_coord = coord[1:]
    try:
        int(new_coord)
    except ValueError:
        print("Warning: {} is not a valid coordinate".format(coord))


def validate_selector(selector):
    """ TODO """
    pass


##################### TEAMS ##########################
teams = []


def empty_team(teamname):
    if not teamname in teams:
        print("Warning: teamname may not have been created")
    return 'U scoreboard teams empty {}'.format(teamname)


def add_team(teamname):
    if teamname not in teams:
        teams.append(teamname)
    return f'team add {teamname}'


################## TP ##########################
def tp(*args):
    if len(args) >= 4:
        return tp_location(*args)
    elif len(args) == 2:
        return tp_player()
    else:
        print("Invalid number of arguments for tp")


def tp_location(selector, x, y, z, yaw=None, pitch=None):
    for coord in (x, y, z, yaw, pitch):
        validate_coord(coord)
    valid_selector(selector)
    return ""


# def set_title(selector, title, title_color, subtitle, subtitle_color):
# 	`title @a[team=werewolf,type=Player] title ["",{"text":"You're onto something","color":"dark_red"}]`#range is 150
#     `title @a[team=werewolf,type=Player] subtitle ["",{"text":"(150 blocks)","color":"dark_red"}]`

# TODO: create annotation for only allowing macro to be called once

############### Used by compiler ##############################
def set_to_literal(var, obj, val):
    return "U scoreboard players set {} {} {}".format(var, obj, val)


def add(var, obj, val):
    return "U scoreboard players add {} {} {}".format(var, obj, val)



def lt(var1, obj1, var2, obj2):
    pass


def _exec(expression):
    exec(expression)
    return ''


def bool_of(var, obj, result_var, result_obj):
    return "\n".join([
        set(result_var, obj, '1'),
        cmp(var, obj, 0),
        "C scoreboard players set {} {} {}".format(result_var, result_obj, '0')
    ])


def operation(op, var1, obj1, var2, obj2):
    return 'U scoreboard players operation {} {} {} {} {}'.format(var1, obj1, op, var2, obj2)


# add all macros to a dict for ease of use
import types

macros_dict = dict([(f.__name__, f) for f in list(globals().values()) if type(f) == types.FunctionType])
macros_dict['exec'] = _exec
