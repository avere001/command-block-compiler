Minecraft Command Block Compiler

WARNING: This code does not currently work.

MCBC is a compiler for minecraft command blocks. It compiles a custom higher level language down to "command block assembly" and ultimately into command blocks that can be imported with the [structure block](https://minecraft.gamepedia.com/Structure_Block).

Command Block Scripting Language
--------------------------------
TODO

Command Block Assembly
---
CBA format is as follows
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
e.g.
`IUN say hello world!`
would be a default command block that says "hello world!" when triggered


TODO
----
- Update to work with the latest minecraft version.
- Change from *.py to a custom line ending for the scripting language
