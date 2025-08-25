# General
  * After winning a VS AI game, and selecting "start a new round" to play again, the AI in the new game does not act at all!
  * Make 'q' prompt the player with a window asking if they want to concede(lose, triggers gameover) or resume instead of instantly aborting the game.
    Use the game over menu but modify it for concession.
  * Make the "...retches" appears in red text
  * Change furniture dec table to end table
  * Shift+Tab keybind functioning as just tab in TTY. Not picking up shift or dual key presses?
  * Remove "You can only use skills with your own units" message from the log (not from the UI).

# STAINED STONES - map
  * Change the floor and stained stone tiles to the same color as the help file text 'Units have unique skills...", to look like stained sandstone.

# GLAIVEMAN
  * Rework the animation for Judgement. It currently makes tiles around the flying projectile appear in black.

# GRAYMAN
  * Change the Estrange beam animation frames to a symbol that is more readily available in a basic terminal type setting.

# MARROW CONDENSER
  * Make the ground indicator appear at the location of an issued move command.
  * Unable to select units after issuing Marrow Condenser skills.  Can only tab to them.

# FOWL CONTRIVANCE
  * Make rails gray with a black background instead of having a red background.
  * Fragcrest blast back needs to state which coord affected targets are moved from and to, similar to other skills that displace, like divine dep.
  * Change fragcrest shrapnel embedding message to yellow and wording to "Shrapnel is embedded deeply in [unit]"
    Make it so that this message appears when the shrapnel status effect is applied to a unit.
  * Make Fragcrest damage message display the damage amount in yellow and remove the '!' at the end. 
  * Remove the extraneous message "The projectile pierces X target for 10 damage."
  * Remove the extraneous message "Fragmentation hits X units for Y damage and embeds shrapnel"

# GAS MACHINIST
  * Remove all heinous vapors when their owner dies.
  * Make henous vapor's follow the same convention of being asigned greek letters after their name's (COOLANT GAS α, BROACHING GAS β, etc). Make sure they get
    called by these names in all of the appropriate UI and log places.
  * Damage number in the log from CUTTING GAS needs to be in yellow.
  * Remove exclamation points from the end of GAS MACHINIST messages.
  * Make the untargettable effect caused by Saft-E-Gas a status effect with an appropriate status effect icon that appears next to the affected unit on the
    map and displays in the UI next to the label "Status:".

# DELPHIC APPRAISER
  * Make it so that when a unit is able to use a Market Futures teleport anchor, they recieve a status effect called "Anchor" with an appropriate status
    icon. This is simple a visible indiciator to the player and the effect falls of when they use the anchor to teleport or become unable to use the anchor.
  * Create a message log that displays re-rolled cosmic values of furniture affected by Divine Depreciation...: "[furniture]'s cosmic value has been re-rolled
    to [value]"
  * Make it so that units can't use the enemy's Market Futures teleport anchors.
  * Make damage numbers appear after the Divine Depreciation skill animation resolves instead of at the start.
  * Make it so that enemies pulled by Divine Depreciation take a flat 1 damage if they collide into terrain.  Gives a message like...
    "[unit] slams into the [furniture] for 1 damage".  Make sure the damage number is displayed in yellow

# INTERFERER
  * Change [C]arrier Rave to [K]arrier Rave in all applicable places and change the keybind for that skill for c to k
  * Make a note in the Interferer's help page, in his description at the top, to mention how he uses plutonium tipped
    carbiners to create deadly neutron radiation.
  * Remove "Radio warfare specialist" from the list of roles in help file.
  * Remove "(Radioactive interference)" and "Plutonium carabiner cross)" from help file.