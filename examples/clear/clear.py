set_prefix('CL')
set_objective('vars')

`summon minecraft:armor_stand ~2 ~ ~-1 {CustomName:Deleter,NoGravity:1b,Marker:1b}`
`tellraw @p ["",{"text":"Clearing.."}]`
while `execute as @e[name=Deleter] at @s run testforblock ~ ~ ~ command_block` do
    `execute as @e[name=Deleter] at @s run fill ~ ~ ~ ~ ~ ~ air`
    `execute as @e[name=Deleter] at @s run fill ~ ~ ~ ~ ~ ~125 air 0 replace chain_command_block`
    `execute as @e[name=Deleter] at @s run kill @e[r=1,type=minecraft:armor_stand,name=!Deleter]`
    `execute as @e[name=Deleter] at @s run tp @e[name=Deleter] ~1 ~ ~`
end
`kill @e[name=Deleter]`
`tellraw @e[r=25] ["",{"text":"Finished Clearing!"}]`
`kill @e[type=minecraft:armor_stand,r=20]`
# `summon Creeper ~ ~1 ~ {ignited:1,NoGravity:1,ExplosionRadius:4}`
`fill ~-5 ~ ~-4 ~5 ~ ~7 air`