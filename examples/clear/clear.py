set_prefix('CL')
set_objective('vars')

`summon ArmorStand ~2 ~ ~-1 {CustomName:Deleter,NoGravity:1b,Marker:1b}`
`tellraw @p ["",{"text":"Clearing.."}]`
while `execute @e[name=Deleter] ~ ~ ~ testforblock ~ ~ ~ command_block` do
    `execute @e[name=Deleter] ~ ~ ~ fill ~ ~ ~ ~ ~ ~ air`
    `execute @e[name=Deleter] ~ ~ ~ fill ~ ~ ~ ~ ~ ~125 air 0 replace chain_command_block`
    `execute @e[name=Deleter] ~ ~ ~ kill @e[r=1,type=ArmorStand,name=!Deleter]`
    `execute @e[name=Deleter] ~ ~ ~ tp @e[name=Deleter] ~1 ~ ~`
end
`kill @e[name=Deleter]`
`tellraw @e[r=25] ["",{"text":"Finished Clearing!"}]`
`kill @e[type=ArmorStand,r=20]`
# `summon Creeper ~ ~1 ~ {ignited:1,NoGravity:1,ExplosionRadius:4}`
`fill ~-5 ~ ~-4 ~5 ~ ~7 air`