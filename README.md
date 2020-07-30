Minecraft Command Block Compiler
-------------------------------
MCBC is a compiler for minecraft command blocks. It compiles a custom higher level language (Command Block Scripting Language) down to "command block assembly" and ultimately into an NBT file containing the command blocks. The NBT can then can be imported with the [structure block](https://minecraft.gamepedia.com/Structure_Block).

Command Block Scripting Language
--------------------------------
The following example will teleport the player 16 blocks in the x direction one block per tick.
```
$i = 0
while $i < 16 do
	$i += 1
	`tp @p ~1 ~ ~`
endwhile
```

More examples can be found in the "examples" directory

Command Block Assembly
---
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

TODO
----
- Update to work with the latest minecraft version.
