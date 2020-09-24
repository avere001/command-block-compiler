# Minecraft Command Block Compiler
MCBC is a compiler for minecraft command blocks. It compiles a custom higher level language (Command Block Scripting Language) down to "command block assembly" and ultimately into an NBT file containing the command blocks. The NBT can then can be imported with the [structure block](https://minecraft.gamepedia.com/Structure_Block).

# Command Block Scripting Language
The following example will teleport the player forward 64 times.
```
$i = 0
while $i < 64 do
	$i += 1
	`execute as @p at @s run tp ^ ^ ^1`
end
```

More examples can be found in the "examples" directory

## Usage
Make sure you have python 3.8 (3.6+ *might* work as well) and Pipenv.
Install the dependencies with `pipenv install` and activate the environment with `pipenv shell`.

You can compile a script with `./compile.py <cbc_script> <output_file>`.
The output file should have the extensions `.nbt` and must be in `<minecraft directory>/saves/<save name>/generated/minecraft/structures/`.

Load the script into minecraft with a structure block.
Put the structure block in "Load" mode with "Include Entities" on.
As of now the structure will not spawn if there are any blocks in the way, so do this in the air.

Quick tips:
- Minecraft caches structure files in memory, so you must reload the world after ever compilation of the script.
- Kill the script with `/kill @e[type=armor_stand]`.
- You will usually need to clear the area after revision of the script. `/fill ~ ~-1 ~ ~50 ~-1 ~50` while standing on the first block

## Language Features

### Variables
Integers can be stored in variables.
All variables are prefixed with a '$'.

### Scores
The score of an entity can be referenced using a selector followed by a colon and the objective.
Example:
```
`team add red`
`team join red @p`
`scoreboard objectives add kills minecraft.custom:minecraft.mob_kills`

@p[team=red]:kills = 0
while @p[team=red]:kills < 5 do
    `say kill more enemies, red team!`
end
`say took you long enough..`
```

### Includes
In a more complex program you may need multiple scripts running in parallel.
This can be achieved by putting `include('otherscriptname')` at the top of your main script.

Each compiled program must have a unique prefix to prevent them from executing eachothers branches.
This is simply a string prepended to all temporary variable names and labels.
You can do this with `prefix('PRFX')`.

This should be kept very short for technical reasons that I can't remember.
(TODO: Remember)


# Command Block Assembly
A simple assembly language for command blocks.
This is the intermediate language for the compiler.

## CBA instructions
```
[ICR][UC][NA] [commandblock text]
ICR:
	I: Impulse
	C: Chain
	R: Repeat
UC:
	U: Unconditional
	C: Conditional
NA:
	N: Needs Redstone
	A: Always Active
```

Example:

`IUN say hello world!`
would generate a "default" command block that says "hello world!" when triggered

## Labels and Jump statements
All jumps are conditional based on the output of the previous command.
If the output of the previous command was true, then jump to LABEL_1.
Otherwise jump to LABEL_2, or if LABEL_2 is not supplied, continue to the next line.
`jmp <LABEL_1> [LABEL_2]`

# Known issues

## Timing
There is no way to control the timing of commands.
The rate at which commands are executed depends on the number of conditional statements involved.

# Possible Improvements
- The variables should be stored as the objective/score instead of the target of a scoreboard.
- Sleep statements
- Automatically creating objectives
- Add some helper command blocks for script cleanup.