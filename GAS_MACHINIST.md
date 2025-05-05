GAS MACHINIST (Pet Class Version)

  Base Stats

  - HP: 18
  - Attack: 4
  - Defense: 1
  - Move Range: 3
  - Attack Range: 1

  Passive: "Effluvium Lathe"

  The Gas Machinist's spine-mounted apparatus continuously refines ambient 
  particles into weaponized effluvium, which coalesces into semi-autonomous
   vapor entities.

  - Automatically generates 1 Effluvium charge at the start of each turn
  (max 3)
  - Summoning a HEINOUS VAPOR uses up all charges an extends the duration of the summon by 1 turn per charge.
  - Player can control the movement of their summoned HEINOUS VAPORS.
  - Each HEINOUS VAPOR's effects "tick" only during the owner's combat round.
  - Heinous vapor effects are 3x3 "clouds", but visually they are just one character, so the effects are applied adjacent.

  HEINOUS VAPOR Stats

  - HP: N/A (cannot be damaged directly)
  - Attack: N/A
  - Defense: N/A
  - Move Range: 3
  - Duration: 1 turn base (extended by charges)

  Three Active Skills:

  1. "Enbroachment Gas" (Key: E)

  - Range: 3
  - Cooldown: 2 turns
  - Effect: Summons a HEINOUS VAPOR that dissolves status effects from allies.
  - VAPOR effect: Deals 2 damage to enemies and cleanses any ally within 1 tile of all negative status effects.
  - Counter Role: Neutralizes Mandible Foreman traps and Jawline effects by
   cleansing affected allies
  - Vapor Appearance: 'Φ'

  2. "Saft-E-Gas" (Key: S)

  - Range: 3
  - Cooldown: 3 turns
  - Effect: Summons a HEINOUS VAPOR that creates a protective 3x3 cloud
  - VAPOR Effects:
    - PROTECTION (always active): Allied units inside the cloud cannot be targeted 
      by enemy attacks or skills from outside. Enemies must enter the cloud to engage.
    - HEALING (activates each turn): Heals allies within the cloud by 1 HP per turn
    - Maintains line of sight - units can see through the cloud
  - Counter Role: Creates safe zones that force enemies to move into the cloud 
    to engage allies, providing strategic control over engagements
  - Vapor Appearance: 'Θ'

  3. "Diverge" (Key: D)

  - Range: 5 (HEINOUS VAPOR or Self)
  - Cooldown: 4 turns
  - Effect: Violently splits an existing HEINOUS VAPOR or self into two specialized
   entities
  - Target any existing VAPOR and split it into:
    a. Coolant Mist: Heals allies inside for 3 HP.
  - Vapor Appearance: 'Σ'
    b. Cutting Mist: Deals 3 damage to enemies and bypasses def.
   -Vapor Apperance: '%'
  - Both new VAPORS have 2 turns of duration and can be controlled
  independently.
  - Each has movement value of 3.
  - Counter Role: Provides burst healing against area damage while creating
   offensive pressure.
   - When casting Diverge on himself (rather than on a vapor), the Gas
  Machinist is removed from play
  - He's replaced by both Coolant Mist (Σ) and a Cutting Mist (%) at his
  position or adjacent tiles
  - After their duration expires, the Gas Machinist reforms at the location of either mist

  Strategic Applications:

  1. Vapor Multiplication
    - Effectively doubles your vapor control presence on the battlefield
    - Converts a single-purpose vapor into dual-purpose offense and defense
    - Creates unexpected tactical opportunities from existing board
  position
  2. Emergency Response
    - Provides on-demand healing when allies are dangerously low
    - Creates surprise offensive pressure when enemies think they're safe
    - Allows rapid response to changing battlefield conditions
  3. Efficient Resource Management
    - Maximizes the value of each Effluvium charge
    - Extends vapor presence on the battlefield
    - Creates difficult decisions for opponents (which vapor to avoid?)
  4. Counter Capabilities
    - Medicinal Mist provides healing counter to Fowl Contrivance's area
  attacks
    - Corrosive Cloud can punish units that rely on defense stats
    - The sudden multiplication of threats can disrupt enemy positioning
  strategies

  This revised skill 3 maintains the pet class theme with even more
  strategic depth by allowing vapor multiplication. It creates exciting
  moments of tactical decision-making while providing both the healing
  support and additional offensive options that make the Gas Machinist a
  versatile counter to powerful enemy units.

Simplified Implementation Approach

  How It Would Work:

  1. HEINOUS VAPORS as Standard Units:
    - Create vapors as a special unit type that can't be attacked
    - They appear in the normal unit selection rotation
    - Player controls them directly like any other unit
  2. Relationship to Gas Machinist:
    - Gas Machinist still generates Effluvium charges
    - Skills still create/modify the vapors
    - Lore-wise, the Gas Machinist is still "controlling" them, but
  mechanically the player handles them separately
  3. Turn Structure:
    - No special turn phase needed - vapors just get normal turns
    - Player can move vapors in any order relative to the Gas Machinist

  Advantages of This Approach:

  1. Uses Existing Systems:
    - Leverages the current unit turn system
    - No need for complex pet control mechanics
    - Can use standard unit movement code
  2. Easier to Understand:
    - Players already know how to control units
    - No special pet interface to learn
    - Clearer feedback on which vapor is currently active
  3. Simpler UI Requirements:
    - No need for "pet control mode" UI
    - Can use existing unit selection interface
    - Only need to track Effluvium charges
  4. Faster Development:
    - Much less custom code needed
    - Lower risk of bugs and edge cases
    - Can reuse most existing unit management code