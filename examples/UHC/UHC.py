include('dayloop')

set_prefix('WW')
set_objective('vars')

#################Initialization###################
`gamerule commandBlockOutput false`
`scoreboard objectives add vars dummy`
`scoreboard objectives add testing dummy`

`scoreboard teams add alive`
`scoreboard teams add dead`

`scoreboard teams option dead nametagVisibility never`

# `gamerule sendCommandFeedback false`
`gamerule logAdminCommands false`

# `kill @e[name=spawndummy]`
if not `testfor @e[name=spawndummy]` then
    `tellraw @a ["",{"text":"Please Wait: finding suitable spawn point"}]`
    `summon ArmorStand -1 256 -1 {CustomName:spawndummy,Invisible:1b,Invulnerable:1b,DisabledSlots:2039583,Marker:1}`
    while `execute @e[name=spawndummy] ~ ~ ~ testforblock ~ ~-1 ~ minecraft:air` do `` end
    `tellraw @a ["",{"text":"Spawn point found!"}]`
end
while not $dayloopready do `` end



##################################################

while true do
    
    
    #####################Setup/Lobby########################
    
    $isday = true
    `gamemode a @a`
    
    `tp @a @e[name=spawndummy]`
    `execute @e[name=spawndummy] ~ ~ ~ worldborder center ~ ~`
    `worldborder set 10`
    
    `execute @e[name=spawndummy] ~ ~ ~ spawnpoint @a ~ ~ ~`
    `execute @e[name=spawndummy] ~ ~ ~ setworldspawn ~ ~ ~`
    `gamerule spawnRadius 0`
    
    `execute @e[name=spawndummy] ~ ~ ~ setblock ~ ~1 ~ minecraft:standing_sign`
    
    `time set 0`
    `gamerule doDaylightCycle false`
    
    `scoreboard objectives remove start_trigger`
    `scoreboard objectives add start_trigger trigger Ready`
    `scoreboard objectives setdisplay sidebar start_trigger`
    `scoreboard players enable @a start_trigger`
    
    `scoreboard teams add lobby`
    
    @a[team=lobby]:start_trigger = 0
    `execute @e[name=spawndummy] ~ ~ ~  blockdata ~ ~1 ~ {Text1:"{\"text\":\"Right Click\",\"clickEvent\":{\"action\":\"run_command\",\"value\":\"/trigger start_trigger set 1\"}}",Text2:"{\"text\":\"to\"}",Text3:"{\"text\":\"Ready Up!\"}"}`
    # wait for sign to be pressed
    while `scoreboard players test @a start_trigger 0 0` do
        `gamemode a @a[m=s,team=!lobby]`
        `scoreboard players enable @a start_trigger`
        `weather clear 1000000`
        `effect @a[m=a] minecraft:saturation 9999 0`
        `effect @a[m=a] minecraft:instant_health 1 20`
        `clear @a[m=a]`
        `time set 0`
        if `testfor @a[team=!lobby]` then
            @a[team=!lobby]:start_trigger = 0
            `tp @a[team=!lobby] @e[name=spawndummy]`
            `scoreboard teams join lobby @a`
        end
    end
    
    `gamerule doDaylightCycle true`
    `effect @a clear`
    `execute @e[name=spawndummy] ~ ~ ~ setblock ~ ~1 ~ air`
    `difficulty easy`
    `gamemode s @a`
    
    `scoreboard objectives add health health Health`
    
    `time set 0`
    `worldborder set 300`
    
    `scoreboard teams join alive @a`
    ##################################################
    
    ##################GameLoop########################
    
    
    # wait for all players to respawn
    while `scoreboard players test @p[team=werewolf] health 0 0` do `` end
    
    # display gameover message
    `title @a times 10 100 10`
    if $living_werewolf then
        #the wereolf won
        `title @a title ["",{"text":"The Werewolf Wins!","color":"dark_red"}]`
    else
        #the civilians won
        if $days == $initial_civilians then
            `title @a title ["",{"text":"The Civilians Escaped!","color":"green"}]`
        else
            `title @a title ["",{"text":"The Civilians Killed The Werewolf!","color":"green"}]`
        end
    end
    
    `clear @a`
    `effect @a clear`
    
    `scoreboard teams empty werewolf`
    `scoreboard teams empty civilians`
    
    `scoreboard objectives remove deaths`
    
    ##################################################
end