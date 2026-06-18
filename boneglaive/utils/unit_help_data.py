"""Unit help data — canonical source for unit descriptions, shared by all UI layers.

Holds the static help/lore data for every unit and summon (title, overview, stats,
skills, tips, tactical notes). This is pure data with no UI dependency; the graphical
help screens read it via get_unit_help_data().
"""

from boneglaive.utils.constants import UnitType


def get_unit_help_data():
    """Return the unit help data dict for all units and summons.

    Keys are UnitType enum members for real units, plus string keys for summon
    variants ('GRAYMAN_ECHO', 'HEINOUS_VAPOR_BROACHING', etc.).
    """
    unit_help_dict = {
        UnitType.GLAIVEMAN: {
            'title': 'GLAIVEMAN',
            'overview': [
                'The GLAIVEMAN is a versatile melee warrior wielding a polearm and sacred spinning glaives. Balanced between offense and defense, this unit excels at close combat with mobility options. The GLAIVEMAN serves as a reliable frontline fighter with powerful retaliatory abilities.',
                '',
                'Role: Frontline Fighter / Disabler / Displacer / Escape Artist',
                'Difficulty: **'
            ],
            'stats': [
                'HP: 22',
                'Attack: 5',
                'Defense: 1',
                'Movement: 3',
                'Range: 2'
            ],
            'skills': [
                {
                    'name': 'AUTOCLAVE (Passive)',
                    'description': 'When the GLAIVEMAN is brought to critical health or takes damage while already at critical health, he unleashes a desperate cross-shaped retaliation in four cardinal directions with range 3. The burst deals 8 damage to all enemies in its path and heals the GLAIVEMAN for half the total damage dealt. Can only trigger once per life and requires at least one enemy within range to activate. Resets on respawn.',
                    'details': [
                        'Range: 3',
                        'Damage: 8'
                    ]
                },
                {
                    'name': 'PRY (Active)',
                    'description': 'The GLAIVEMAN pries an adjacent enemy straight up into the ceiling, causing them to crash down with falling debris. The primary target takes 6 damage and is staggered by the brutal impact, suffering -1 movement for 2 turns with Pried. All adjacent enemies take 3 splash damage from the falling debris.',
                    'details': [
                        'Range: 1',
                        'Damage: 6, 3 splash',
                        'Cooldown: 3 turns'
                    ]
                },
                {
                    'name': 'VAULT (Active)',
                    'description': 'The GLAIVEMAN performs an athletic vault, leaping over obstacles and units to land on any empty passable tile within range 2. This movement ignores pathing restrictions and does not require line of sight, allowing repositioning over impassable terrain and enemy units.',
                    'details': [
                        'Range: 2',
                        'Cooldown: 4 turns'
                    ]
                },
                {
                    'name': 'JUDGEMENT (Active)',
                    'description': 'The GLAIVEMAN hurls a sacred spinning glaive that pierces enemy defenses, dealing 4 damage. Against enemies at critical health, divine judgement activates and deals 8 damage. Requires line of sight to the target.',
                    'details': [
                        'Range: 4',
                        'Damage: 4, 8 to critical health',
                        'Cooldown: 4 turns'
                    ]
                }
            ],
            'tips': [
                '- Use Pry to control enemy positioning and reduce their mobility',
                '- Vault provides excellent positioning and escape options',
                '- Judgement is devastating against wounded enemies',
                '- Autoclave makes the GLAIVEMAN dangerous even when near death',
                '- Maintain front-line position to threaten enemies with Autoclave'
            ],
            'tactical': [
                '- Strong against: Clustered enemies, high-defense units',
                '- Vulnerable to: Long-range attacks, status effects',
                '- Best positioning: Front-center to maximize Pry coverage'
            ]
        },
        UnitType.MANDIBLE_FOREMAN: {
            'title': 'MANDIBLE FOREMAN',
            'overview': [
                'The MANDIBLE FOREMAN is a mechanical supervisor wielding industrial jaw contraptions for area control and battlefield management. This durable frontline unit excels at trapping and immobilizing enemies while providing tactical support to allies in open terrain. The MANDIBLE FOREMAN serves as a close-range specialist focused on movement denial and crowd control.',
                '',
                'Role: Frontline Fighter / Disabler',
                'Difficulty: **'
            ],
            'stats': [
                'HP: 22',
                'Attack: 3',
                'Defense: 1',
                'Movement: 3',
                'Range: 1'
            ],
            'skills': [
                {
                    'name': 'VISEROY (Passive)',
                    'description': 'Every basic attack automatically traps the target. Trapped enemies cannot move or use skills and take continuous damage each turn until the MANDIBLE FOREMAN moves away, is displaced, or is killed. While a unit is trapped, the MANDIBLE FOREMAN cannot basic attack.',
                    'details': []
                },
                {
                    'name': 'EXPEDITE (Active)',
                    'description': 'The MANDIBLE FOREMAN rushes forward up to 4 tiles in a straight line, stopping at the first enemy encountered. The collision deals 5 damage and applies Viseroy. Cannot target adjacent enemies.',
                    'details': [
                        'Range: 4',
                        'Damage: 5',
                        'Cooldown: 5 turns'
                    ]
                },
                {
                    'name': 'SITE INSPECTION (Active)',
                    'description': 'The MANDIBLE FOREMAN surveys a 3x3 area. Areas with 0 terrain obstacles grant allies +1 attack and +1 movement for 3 turns. Areas with 1 terrain obstacle grant +1 movement only. Areas with 2+ terrain obstacles grant no effect. The inspection also reveals hidden traps.',
                    'details': [
                        'Range: 3',
                        'Cooldown: 4 turns'
                    ]
                },
                {
                    'name': 'JAWLINE (Active)',
                    'description': 'The MANDIBLE FOREMAN deploys mechanical jaws across all 8 adjacent tiles. Each adjacent enemy takes 4 damage and is immobilized for 2 turns.',
                    'details': [
                        'Range: 0',
                        'Damage: 4',
                        'Cooldown: 3 turns'
                    ]
                }
            ],
            'tips': [
                '- Use Viseroy to control enemy positioning with every attack',
                '- Expedite provides both gap-closing and guaranteed trap application',
                '- Position teams strategically: clear areas give full bonuses, lightly obstructed areas give partial',
                '- Jawline is devastating in chokepoints or when surrounded by multiple enemies',
                '- High HP allows aggressive frontline positioning despite melee range'
            ],
            'tactical': [
                '- Strong against: Isolated units, melee-focused teams',
                '- Vulnerable to: Ranged attackers, immunity effects, heavily cluttered terrain',
                '- Best positioning: Frontline in moderately open areas, near chokepoints'
            ]
        },
        UnitType.GRAYMAN: {
            'title': 'GRAYMAN',
            'overview': [
                'The GRAYMAN is a gray alien-human hybrid occupying an unchangeable state, immune to all external manipulation. This ranged specialist teleports freely, weakens key targets, and creates doppelgangers that explode when destroyed.',
                '',
                'Role: Escape Artist / Disabler / Summoner',
                'Difficulty: *'
            ],
            'stats': [
                'HP: 18',
                'Attack: 4',
                'Defense: 0',
                'Movement: 4',
                'Range: 5'
            ],
            'skills': [
                {
                    'name': 'STASIALITY (Passive)',
                    'description': 'The GRAYMAN exists in a state of permanent stasis outside normal spacetime, granting immunity to all status effects, stat modifications, forced movement, and terrain effects.',
                    'details': []
                },
                {
                    'name': 'DELTA CONFIG (Active)',
                    'description': 'The GRAYMAN teleports to any unoccupied passable tile on the battlefield with no regard for distance, obstacles, or line of sight.',
                    'details': [
                        'Range: Unlimited',
                        'Cooldown: 6 turns'
                    ]
                },
                {
                    'name': 'ESTRANGE (Active)',
                    'description': 'The GRAYMAN fires a beam that deals 4 damage and applies Estrangement, reducing all of the target\'s stats by 2. Requires line of sight.',
                    'details': [
                        'Range: 5',
                        'Damage: 4',
                        'Cooldown: 3 turns'
                    ]
                },
                {
                    'name': 'GRÆ EXCHANGE (Active)',
                    'description': 'The GRAYMAN banishes a target enemy unit for 2 turns and creates a psychic doppelganger in their place with 12 HP and 4 attack. The doppelganger cannot move or use skills. When the doppelganger is destroyed or expires, it explodes for 6 damage to all adjacent enemies, and the banished unit returns. Requires line of sight.',
                    'details': [
                        'Range: 5',
                        'Cooldown: 3 turns'
                    ]
                }
            ],
            'tips': [
                '- Use Stasiality immunity to ignore enemy control abilities and debuffs',
                '- Delta Config provides unmatched repositioning; use for flanking or escaping danger',
                '- Estrange permanently weakens key enemy units; prioritize high-value targets',
                '- Græ Exchange temporarily removes dangerous enemies while creating a combat presence',
                '- Banish high-value targets at critical moments to disrupt enemy strategy',
                '- Position doppelgangers to maximize explosion damage when they expire'
            ],
            'tactical': [
                '- Strong against: Control-heavy teams, stationary units, long-term engagements',
                '- Vulnerable to: High direct damage',
                '- Best positioning: Back lines with escape routes, flanking positions using teleportation'
            ]
        },
        'GRAYMAN_ECHO': {
            'title': 'GRAYMAN DOPPELGANGER',
            'overview': [
                'GRAYMAN doppelgangers are temporary psychic projections manifested through the Græ Exchange skill. When the GRAYMAN banishes an enemy unit to the temporal void, a doppelganger takes their place, maintaining battlefield control while the original target remains displaced. These immobile entities can perform basic attacks and explode when destroyed, serving as both combat units and area denial threats that guard the position until the banished unit returns.',
                '',
                'Role: Area Controller / Temporary Replacement'
            ],
            'stats': [
                'HP: 12',
                'Attack: 4',
                'Defense: 0',
                'Movement: 0',
                'Range: 1'
            ],
            'skills': [
                {
                    'name': 'IMMOBILITY (Passive)',
                    'description': 'Cannot move from creation position.',
                    'details': []
                },
                {
                    'name': 'DEATH EXPLOSION (On Death)',
                    'description': 'When destroyed or when its duration expires, the doppelganger explodes, dealing 6 damage to all adjacent enemy units. The banished unit then returns to the doppelganger\'s position.',
                    'details': [
                        'Damage: 6'
                    ]
                }
            ],
            'tips': [
                '- Doppelganger replaces banished enemy at their exact position',
                '- Use to temporarily remove key threats while maintaining board control',
                '- Explosion threat forces enemies to keep distance from the doppelganger',
                '- Remember the banished unit will return when the doppelganger expires',
                '- Cannot use skills, only basic attacks within range 1'
            ],
            'tactical': [
                '- Strong against: Melee units, clustered formations, key enemy pieces',
                '- Limitations: Cannot move, no skills, 1-turn duration, low HP',
                '- Strategic value: Temporarily neutralizes threats while providing combat presence',
                '- Timing consideration: Banished unit returns at doppelganger\'s position when it expires'
            ]
        },
        UnitType.MARROW_CONDENSER: {
            'title': 'MARROW CONDENSER',
            'overview': [
                'The MARROW CONDENSER is a quadrupedal bone manipulator that creates wall structures to trap enemies. Each death within a Marrow Dike triggers Dominion, upgrading the unit\'s stats and active skills. This tank grows stronger throughout battle, draining life from trapped enemies while reinforcing its defenses.',
                '',
                'Role: Tank / Frontline Fighter / Displacer',
                'Difficulty: ***'
            ],
            'stats': [
                'HP: 22',
                'Attack: 4',
                'Defense: 2',
                'Movement: 3',
                'Range: 1'
            ],
            'skills': [
                {
                    'name': 'DOMINION (Passive)',
                    'description': 'When any unit dies within the interior of a Marrow Dike, the MARROW CONDENSER gains upgrades. The first death grants +1 movement. The second death grants +1 attack. The third death grants +1 defense. Additionally, each death upgrades one active skill in sequence: Marrow Dike → Ossify → Bone Tithe.',
                    'details': []
                },
                {
                    'name': 'OSSIFY (Active)',
                    'description': 'The MARROW CONDENSER hardens for 3 turns, gaining +2 defense at the cost of -1 movement. When upgraded, the defense bonus increases to +3.',
                    'details': [
                        'Cooldown: 3 turns'
                    ]
                },
                {
                    'name': 'MARROW DIKE (Active)',
                    'description': 'The MARROW CONDENSER creates bone marrow walls in a 5x5 perimeter around itself. Enemy units on the perimeter tiles are pulled one tile inward. The walls last 3 turns and block movement and line of sight. When upgraded, walls take an additional hit to destroy, and enemies starting their turn inside suffer -1 attack and -1 movement with Mired.',
                    'details': [
                        'Range: 5x5 perimeter',
                        'Cooldown: 4 turns'
                    ]
                },
                {
                    'name': 'BONE TITHE (Active)',
                    'description': 'The MARROW CONDENSER drains all enemies in a 5x5 area, dealing 1 damage to each and increasing both max HP and current HP by +1 for each enemy hit. When upgraded, the damage scales with total Dominion kills and HP gain per enemy increases to +2.',
                    'details': [
                        'Range: 5x5 area',
                        'Damage: 1',
                        'Cooldown: 1 turn'
                    ]
                }
            ],
            'tips': [
                '- Use Marrow Dike to trap enemies and control battlefield positioning',
                '- Bone Tithe frequently for sustained healing and HP growth',
                '- Ossify when expecting heavy damage to maximize survivability',
                '- Position centrally to maximize Bone Tithe hits and Dominion kill opportunities',
                '- High HP allows aggressive frontline positioning'
            ],
            'tactical': [
                '- Strong against: Melee units, sustained engagements, clustered enemies',
                '- Vulnerable to: Long-range attackers, high mobility units, piercing damage',
                '- Best positioning: Center of enemy groups, chokepoints for wall placement'
            ]
        },
        UnitType.FOWL_CONTRIVANCE: {
            'title': 'FOWL CONTRIVANCE',
            'overview': [
                'The FOWL CONTRIVANCE is a mechanical peacock rail artillery platform. Upon deployment, this unit establishes a rail network that detonates when any FOWL CONTRIVANCE dies, damaging enemies on rails. This heavy artillery excels at long-range bombardment with mortar shells, piercing rail cannon shots, and directional fragmentation bursts.',
                '',
                'Role: Burst Damage / Displacer',
                'Difficulty: ***'
            ],
            'stats': [
                'HP: 18',
                'Attack: 4',
                'Defense: 0',
                'Movement: 3',
                'Range: 3'
            ],
            'skills': [
                {
                    'name': 'RAIL GENESIS (Passive)',
                    'description': 'The first FOWL CONTRIVANCE to deploy establishes a rail network across passable terrain, shared by all FOWL CONTRIVANCES. Whenever any FOWL CONTRIVANCE dies, the rail network detonates, dealing 6 damage to all enemy units standing on rail tiles. FOWL CONTRIVANCE units are immune to this explosion. When the last FOWL CONTRIVANCE dies, the rail network is removed.',
                    'details': [
                        'Damage: 6'
                    ]
                },
                {
                    'name': 'GAUSSIAN DUSK (Active)',
                    'description': 'The FOWL CONTRIVANCE fires its rail cannon in a cardinal direction, piercing through all units in a straight line across the entire map. Damage follows a bell curve based on target HP, peaking at 9 damage for targets near 50% HP. Destroys terrain at the beam midpoint.',
                    'details': [
                        'Range: Unlimited',
                        'Damage: 9',
                        'Cooldown: 4 turns'
                    ]
                },
                {
                    'name': 'PARABOL (Active)',
                    'description': 'The FOWL CONTRIVANCE launches a mortar shell to bombard a 3x3 area. The indirect fire ignores line of sight and cannot target adjacent tiles. The center tile takes 8 damage while the surrounding tiles each take 5 damage.',
                    'details': [
                        'Range: 6',
                        'Damage: 8 center, 5 surrounding',
                        'Cooldown: 4 turns'
                    ]
                },
                {
                    'name': 'FRAGCREST (Active)',
                    'description': 'The FOWL CONTRIVANCE fires a directional fragmentation burst in a 90-degree cone. The primary target takes 4 damage and is knocked back 2 tiles. All other enemies in the cone take 2 damage and are also knocked back. All hit enemies take Shrapnel, suffering 1 damage per turn for 3 turns. Requires line of sight to the primary target.',
                    'details': [
                        'Range: 4',
                        'Damage: 4 primary, 2 cone',
                        'Cooldown: 3 turns'
                    ]
                }
            ],
            'tips': [
                '- Cardinal direction restriction requires careful positioning before firing Gaussian Dusk',
                '- Parabol excels against clustered enemies and ignores line of sight restrictions',
                '- Fragcrest provides crowd control through knockback and area denial via shrapnel',
                '- Low movement requires careful positioning near rail network'
            ],
            'tactical': [
                '- Strong against: Clustered enemies, static formations, low-mobility units, units with high defence',
                '- Vulnerable to: High-mobility rushers, units that can close distance quickly, area denial, high burst damage',
                '- Best positioning: Behind cover, near rail network'
            ]
        },
        UnitType.GAS_MACHINIST: {
            'title': 'GAS MACHINIST',
            'overview': [
                'An industrial chemist who deploys autonomous vapor entities in areas that passively affect all units within each turn. This utility specialist excels at area control and sustained support through strategic vapor deployment.',
                '',
                'Role: Summoner / Utility / Healer',
                'Difficulty: *****'
            ],
            'stats': [
                'HP: 20',
                'Attack: 3',
                'Defense: 1',
                'Movement: 2',
                'Range: 1',
            ],
            'skills': [
                {
                    'name': 'EFFLUVIUM LATHE (Passive)',
                    'description': 'The GAS MACHINIST generates 1 Effluvium charge at the start of each turn, up to a maximum of 4. When summoning or splitting vapors, all accumulated charges are consumed to extend the vapor\'s duration. Starts each match with 1 charge. No charges generate while diverged.',
                    'details': []
                },
                {
                    'name': 'BROACHING GAS (Active)',
                    'description': 'The GAS MACHINIST deploys a HEINOUS VAPOR to an empty tile, creating a 3x3 gas cloud centered on the vapor. Each turn, the vapor damages enemies within the cloud for 1 damage and cleanses one random negative status effect from each ally in the cloud. The vapor persists for a duration equal to consumed Effluvium charges and is invulnerable.',
                    'details': [
                        'Range: 4',
                        'Damage: 1 per turn',
                        'Cooldown: 3 turns'
                    ]
                },
                {
                    'name': 'SAFT-E-GAS (Active)',
                    'description': 'The GAS MACHINIST deploys a HEINOUS VAPOR to an empty tile, creating a 3x3 gas cloud centered on the vapor. The vapor grants +1 defense to all allies within the cloud and heals them for 1 HP each turn. The vapor persists for a duration equal to consumed Effluvium charges and is invulnerable.',
                    'details': [
                        'Range: 4',
                        'Cooldown: 3 turns'
                    ]
                },
                {
                    'name': 'DIVERGE (Active)',
                    'description': 'The GAS MACHINIST splits an existing HEINOUS VAPOR or themselves into two specialized vapors that appear in adjacent spaces. The split creates Coolant Gas, which heals allies for 3 HP per turn in a 3x3 area, and Cutting Gas, which deals 3 piercing damage per turn to enemies in a 3x3 area. When targeting self, the GAS MACHINIST is removed from the board until both vapors expire, then reforms at the last vapor\'s position. Both vapors inherit duration from consumed Effluvium charges.',
                    'details': [
                        'Range: 4',
                        'Cooldown: 4 turns'
                    ]
                },
                {
                    'name': 'AEROSOLIZE ARMS (Active)',
                    'description': 'The GAS MACHINIST aerosolizes a target\'s weaponry, disarming them and spawning a LIVING AEROSOL adjacent to them under their player\'s control. The LIVING AEROSOL inherits the target\'s attack stat and acts independently. Both the disarm and the LIVING AEROSOL persist for a duration equal to consumed Effluvium charges. Requires line of sight.',
                    'details': [
                        'Target: Enemy or ally unit',
                        'Range: 4',
                        'Cooldown: 3 turns',
                        'Learned through upgrading Effluvium Lathe.'
                    ]
                }
            ],
            'tips': [
                '- Build up Effluvium charges early to maximize vapor duration',
                '- Use Broaching Gas for enemy damage and ally cleansing',
                '- Deploy Saft-E-Gas defensively to block ranged attacks and heal',
                '- Diverge gasses to extend their effectiveness',
                '- Self-diverge to become invulnerable, maximize area control, or escape'
            ],
            'tactical': [
                '- Strong against: Status effect users, ranged attackers, sustained damage teams',
                '- Vulnerable to: Burst damage, high mobility units that can avoid vapors, area denial',
                '- Best positioning: Behind frontlines, near allies for vapor support, central locations for maximum vapor coverage'
            ]
        },
        UnitType.DELPHIC_APPRAISER: {
            'title': 'DELPHIC APPRAISER',
            'overview': [
                'The DELPHIC APPRAISER is an antique dealer with oracular sight who perceives the astral value (1-9) of every furniture piece on the battlefield. This utility specialist weaponizes furniture appraisals to teleport allies, curse enemies with damage-over-time, and collapse furniture values to create damaging pull effects. The APPRAISER thrives on furniture-rich maps where astral values create opportunities for tactical repositioning and area control.',
                '',
                'Role: Utility / Displacer / Disabler / Burst Damage / Escape Artist',
                'Difficulty: ****'
            ],
            'stats': [
                'HP: 20',
                'Attack: 3',
                'Defense: 0',
                'Movement: 4',
                'Range: 2',
            ],
            'skills': [
                {
                    'name': 'VALUATION ORACLE (Passive)',
                    'description': 'The DELPHIC APPRAISER perceives the astral value of every furniture piece when the match begins. Values range from 1-9 and can reach a maximum of 14. Allies standing adjacent to furniture with astral value 9 or greater gain +1 defense and +1 attack range. These bonuses persist as long as they remain adjacent to high-value furniture.',
                    'details': []
                },
                {
                    'name': 'MARKET FUTURES (Active)',
                    'description': 'The DELPHIC APPRAISER imbues a furniture piece with investment energy, creating a teleportation locus. The locus remains active for 3 turns or until one ally activates it. Allies adjacent to the locus can use Parallax to teleport through it.',
                    'details': [
                        'Range: 4',
                        'Cooldown: 5 turns'
                    ]
                },
                {
                    'name': 'PARALLAX (Active)',
                    'description': 'Appears when the DELPHIC APPRAISER or an ally is adjacent to an active Market Futures locus. Instantly teleports the unit to any passable destination within a range equal to the locus\'s astral value. Upon arrival, the unit gains the Investment effect: +1 attack range for 3 turns and growing attack bonuses (+1 attack on turn 1, +2 on turn 2, +3 on turn 3). The locus deactivates after one use.',
                    'details': [
                        'Range: Equal to locus\'s astral value (1-14)',
                        'Cooldown: None',
                        'Appears when adjacent to a Market Futures locus.'
                    ]
                },
                {
                    'name': 'AUCTION CURSE (Active)',
                    'description': 'The DELPHIC APPRAISER curses a target enemy, dealing 1 damage per turn and preventing all healing. The curse duration equals the average astral value of furniture within 2 tiles of the target, rounded up. Duration ranges from 1-14 turns. Each turn the curse persists, all furniture within 2 tiles of the target inflates by +1 astral value, capped at 14.',
                    'details': [
                        'Range: 3',
                        'Damage: 1 per turn',
                        'Cooldown: 3 turns'
                    ]
                },
                {
                    'name': 'DIVINE DEPRECIATION (Active)',
                    'description': 'The DELPHIC APPRAISER collapses a furniture piece\'s astral value to 1, creating a 7x7 cascading sinkhole. All enemies in the area take piercing damage equal to the average astral value of other furniture in the area minus 1. Maximum damage is 13. Enemies are pulled toward the center by a distance equal to the original furniture value minus 1, then reduced by their movement value. Minimum pull is 1 tile. All other furniture in the area rerolls astral values randomly from 1-9.',
                    'details': [
                        'Range: 3',
                        'Area: 7x7',
                        'Cooldown: 4 turns'
                    ]
                },
                {
                    'name': 'DEFT(?) REROLL (Active)',
                    'icon': 'deft_reroll',
                    'description': 'A temporary skill that replaces Divine Depreciation after it is used. Instantly rerolls all furniture values 1-14 in the area affected by the last Divine Depreciation, allowing the DELPHIC APPRAISER to immediately re-randomize the astral landscape. Increases Divine Depreciation\'s cooldown by 1 turn. Disappears after use.',
                    'details': [
                        'Cooldown: None',
                        'Learned through upgrading Divine Depreciation.'
                    ]
                }
            ],
            'tips': [
                '- Position allies near high-value furniture (9+) for defense and range bonuses',
                '- Use Market Futures on high-value furniture for longer teleport distances',
                '- Auction Curse scales with surrounding furniture density and values',
                '- Divine Depreciation damage and pull scale with furniture values in the area',
                '- High-mobility enemies resist the pull from Divine Depreciation better'
            ],
            'tactical': [
                '- Strong against: Static formations, low-mobility units, furniture-heavy maps',
                '- Vulnerable to: High burst damage, open area engagements without furniture',
                '- Best positioning: Near furniture clusters for Valuation Oracle bonuses'
            ]
        },
        UnitType.INTERFERER: {
            'title': 'INTERFERER',
            'overview': [
                'The INTERFERER is a telecommunications engineer who uses a remote radio tower array as a directed energy weapon. This glass cannon specializes in neural hijacking, phasing out of reality to avoid damage, and placing invisible traps. Basic attacks radiate RF energy in directional patterns that inflict stacking RF burn over time.',
                '',
                'Role: Burst Damage / Disabler',
                'Difficulty: **'
            ],
            'stats': [
                'HP: 18',
                'Attack: 4',
                'Defense: 0',
                'Movement: 4',
                'Range: 1',
            ],
            'skills': [
                {
                    'name': 'RADIO EFFULGENT (Passive)',
                    'description': 'The antenna array energizes the carabiners, causing RF burn that spreads directionally on attack. Attacking along cardinal directions spreads RF burn diagonally. Attacking diagonally spreads RF burn cardinally. Each RF burn stack deals 1 damage per turn for 2 turns and accumulates with repeated attacks.',
                    'details': [
                        'Damage: 1 per turn for 2 turns'
                    ]
                },
                {
                    'name': 'NEURAL SHUNT (Active)',
                    'description': 'The INTERFERER hijacks a target\'s motor functions for 1 turn, dealing 6 damage. The afflicted unit performs random moves, attacks, or skills.',
                    'details': [
                        'Range: 1',
                        'Damage: 6',
                        'Cooldown: 4 turns'
                    ]
                },
                {
                    'name': 'KARRIER RAVE (Active)',
                    'description': 'The INTERFERER phases out of reality for 2 turns, becoming untargetable by any attacks or skills. Upon returning, the next melee attack strikes three times in rapid succession.',
                    'details': [
                        'Cooldown: 6 turns'
                    ]
                },
                {
                    'name': 'SCALAR NODE (Active)',
                    'description': 'The INTERFERER creates an invisible trap at a target location. The trap is completely silent when placed. When any enemy ends their turn on the trapped tile, it detonates and deals 8 damage. The trap persists until triggered.',
                    'details': [
                        'Range: 3',
                        'Damage: 8',
                        'Cooldown: 2 turns'
                    ]
                }
            ],
            'tips': [
                '- Radiation spread creates persistent damage zones that force enemies to reposition',
                '- Neural Shunt disrupts enemy strategy by causing random actions',
                '- Use Karrier Rave to avoid burst damage and set up triple-strike attacks',
                '- Place Scalar Nodes on likely enemy movement paths or retreat routes'
            ],
            'tactical': [
                '- Strong against: High-HP units, predictable formations, static enemies',
                '- Vulnerable to: Area attacks, burst damage before phasing',
                '- Best positioning: Behind cover, flanking positions for RF burn coverage'
            ]
        },
        UnitType.DERELICTIONIST: {
            'title': 'DERELICTIONIST',
            'overview': [
                'The DERELICTIONIST is a distance-based healer who manipulates interpersonal distance to provide powerful healing and protective effects that scale with range. This utility specialist clears status effects, pushes allies to safety while healing them, and shields allies from fatal damage. Healing effectiveness increases with distance from the DERELICTIONIST.',
                '',
                'Role: Utility / Healer / Disabler / Displacer',
                'Difficulty: ****'
            ],
            'stats': [
                'HP: 18',
                'Attack: 0',
                'Defense: 0',
                'Movement: 4',
                'Range: 1',
            ],
            'skills': [
                {
                    'name': 'SEVERANCE (Passive)',
                    'description': 'After issuing a skill or basic attack, gains +1 to MV for 1 turn and is given the opportunity to move. Can still only be issued 1 move command each turn. Basic attack damage is also increased based on the distance between the DERELICTIONIST and his target.',
                    'details': [
                        'Attack damage bypasses defense.'
                    ]
                },
                {
                    'name': 'VAGAL RUN (Active)',
                    'description': 'The DERELICTIONIST clears all status effects from an ally. The effect varies with distance: 1-3 tiles deals 3 piercing damage that cannot kill, 4 tiles deals 2 damage, 5 tiles deals 1 damage, 6 tiles has no effect, 7+ tiles heals for distance minus 6 HP. After 3 turns, the distance-based effect repeats and clears status effects again.',
                    'details': [
                        'Range: 3',
                        'Cooldown: 4 turns'
                    ]
                },
                {
                    'name': 'DERELICT (Active)',
                    'description': 'The DERELICTIONIST pushes an ally away in a straight line up to 4 tiles. The ally heals for an amount based on the final distance between them and the DERELICTIONIST after the push resolves, scaling at 1.7x distance. Obstacles and map boundaries can interrupt the push, affecting final distance and healing.',
                    'details': [
                        'Range: 3',
                        'Cooldown: 4 turns'
                    ]
                },
                {
                    'name': 'PARTITION (Active)',
                    'description': 'The DERELICTIONIST shields an ally, reducing all incoming damage by 1 for 3 turns. If the ally would receive fatal damage while the shield is active, the ally ignores all damage that turn and the partition ends. When this emergency effect triggers, the DERELICTIONIST teleports 4 tiles away.',
                    'details': [
                        'Target: Ally (including self)',
                        'Range: 3',
                        'Cooldown: 4 turns'
                    ]
                }
            ],
            'tips': [
                '- Use Severance to reposition after skills for optimal healing distances',
                '- Vagal Run at distance 7+ provides powerful healing and delayed second trigger',
                '- Derelict pushes allies out of danger while healing based on final distance',
                '- Partition emergency intervention can save critically wounded allies'
            ],
            'tactical': [
                '- Strong against: Status effect teams, burst damage, sustained fights',
                '- Vulnerable to: Mobility denial',
                '- Best positioning: Mid-range support with space to create distance'
            ]
        },
        UnitType.POTPOURRIST: {
            'title': 'POTPOURRIST',
            'overview': [
                'The POTPOURRIST is a durable tank who wields a granite pedestal as both weapon and incense burner. This unit heals continuously each turn and can infuse potpourri to double healing and empower offensive skills. The POTPOURRIST specializes in damage mitigation through debuffs that reduce incoming damage and magical bindings that force enemies to attack or grant healing.',
                '',
                'Role: Tank / Frontline Fighter',
                'Difficulty: *'
            ],
            'stats': [
                'HP: 24',
                'Attack: 5',
                'Defense: 0',
                'Movement: 3',
                'Range: 1'
            ],
            'skills': [
                {
                    'name': 'MELANGE EMINENCE (Passive)',
                    'description': 'The POTPOURRIST heals 1 HP at the start of every turn, including enemy turns. This healing cannot be prevented. When infused with potpourri, healing increases to 2 HP per turn.',
                    'details': []
                },
                {
                    'name': 'INFUSE (Active)',
                    'description': 'The POTPOURRIST infuses potpourri for 2 turns, doubling Melange Eminence healing from 1 HP to 2 HP per turn and empowering Demilune and Granite Geas with additional effects. Goes on cooldown when consumed or when it expires.',
                    'details': [
                        'Cooldown: 1 turn'
                    ]
                },
                {
                    'name': 'DEMILUNE (Active)',
                    'description': 'The POTPOURRIST swings their pedestal in a forward crescent arc, striking enemies in 3 tiles ahead plus 2 diagonal sides. Hit enemies suffer Lunacy, halving all damage they deal to the POTPOURRIST for 2 turns. When enhanced with potpourri, Lunacy lasts 3 turns and damage increases by 1. Consumes infusion.',
                    'details': [
                        'Damage: 3, 4 if enhanced',
                        'Cooldown: 3 turns'
                    ]
                },
                {
                    'name': 'GRANITE GEAS (Active)',
                    'description': 'The POTPOURRIST strikes an enemy with their pedestal, marking them with a magical binding for 1 turn. If the target fails to attack or use a skill against the POTPOURRIST during their turn, the binding breaks and heals the POTPOURRIST for 4 HP. When enhanced with potpourri, the geas lasts 2 turns for up to 8 HP total healing. Consumes infusion.',
                    'details': [
                        'Range: 1',
                        'Damage: 5',
                        'Cooldown: 3 turns'
                    ]
                }
            ],
            'tips': [
                '- Infuse before engaging to gain enhanced healing during combat',
                '- Use Demilune to debuff multiple enemies simultaneously',
                '- Granite Geas punishes enemies who ignore you and rewards positioning',
                '- Melange Eminence healing stacks with other healing sources'
            ],
            'tactical': [
                '- Strong against: Sustained damage teams, low-damage units, attrition strategies',
                '- Vulnerable to: Negative status effects, multi-target focus fire',
                '- Best positioning: Front line, absorbing attacks and protecting allies'
            ]
        },
        UnitType.LANDSCAPER: {
            'title': 'LANDSCAPER',
            'overview': [
                'The LANDSCAPER is a four-armed terrain manipulator who reshapes the battlefield through acoustic resonance. She wields quartz crystal tuning forks and a Tibetan horn array to grab terrain and furniture, build slag walls, turn units into topiary sculptures, and shatter terrain and furniture for piercing shrapnel.',
                '',
                'Role: Displacer / Disabler / Utility'
            ],
            'stats': [
                'HP: 20',
                'Attack: 1',
                'Defense: 1',
                'Movement: 2',
                'Range: 1'
            ],
            'skills': [
                {
                    'name': 'TRANSLATIVE STROKE (Passive)',
                    'description': 'Basic attacks hit 4 times simultaneously (one per tuning fork). All skill cooldowns are reduced by the total damage dealt across all four hits. ATK buffs from teammates dramatically increase both damage and cooldown cycling.',
                    'details': []
                },
                {
                    'name': 'HORNSWOGGLE (Active)',
                    'description': 'Fire a sonic wave in one of 8 directions. The wave grabs the first terrain or furniture it hits and drags it 90 degrees counter-clockwise. Terrain flies over all obstacles to max drag range. Slag walls are deposited along the drag path, displacing any units or terrain in the way. Can grab any terrain or furniture including topiaries.',
                    'details': [
                        'Wave range: 4, Drag range: 4',
                        'Slag wall duration: 3 turns',
                        'Cooldown: 9 turns',
                        'Upgrade: matching terrain near the grab point also shifts, leaving more slag'
                    ]
                },
                {
                    'name': 'TOPIARY BREATH (Active)',
                    'description': 'Blast a cone of petrifying resonance that transforms ALL units caught (allies and enemies) into invulnerable topiary terrain sculptures for 2 turns. Units are rearranged into a checker pattern. Topiaries have 999 PRT, block movement and LOS, are immune to status effects, and cannot act. Topiaries can be Hornswoggled or shattered by Dissonance.',
                    'details': [
                        'Cone: 3/5/7/7 tiles wide (cardinal), 5/5/5/5 diamond (diagonal)',
                        'Duration: 2 turns',
                        'Cooldown: 13 turns'
                    ]
                },
                {
                    'name': 'DISSONANCE (Active)',
                    'description': 'Launch an acoustic gyre that shatters terrain or furniture from within. Shrapnel flies in all 8 directions dealing 5 piercing damage (ignores DEF). Shrapnel stops at terrain but passes through multiple units. Shattering a topiary frees the unit inside.',
                    'details': [
                        'Cast range: 4, Shrapnel range: 2',
                        'Damage: 5 piercing (shrapnel)',
                        'Cooldown: 9 turns'
                    ]
                }
            ],
            'tips': [
                '- Hornswoggle to build slag walls, then Dissonance to shatter them near enemies',
                '- Topiary Breath + Dissonance: turn enemy into terrain, shatter to free them into shrapnel zone',
                '- Topiary Breath + Hornswoggle: drag a petrified enemy across the map',
                '- Get ATK buffs from teammates to increase Translative Stroke cycling speed',
                '- Careful with Topiary Breath — it affects your allies too!',
                '- Slag walls displace units and overwrite existing terrain and furniture'
            ],
            'tactical': [
                '- Strong against: Static defensive units, clustered formations, terrain-dependent strategies',
                '- Vulnerable to: Ranged focus fire, PRT (blocks each Translative Stroke hit), Stasiality (resists Topiary)',
                '- Best positioning: Mid-line near terrain or furniture, in melee range for Translative Stroke cooldown cycling'
            ]
        },
        'HEINOUS_VAPOR_BROACHING': {
            'title': 'BROACHING GAS (1)',
            'overview': [
                'BROACHING GAS is a HEINOUS VAPOR entity summoned by the GAS MACHINIST using the Broaching Gas skill. This vapor specializes in dual-purpose area control, dealing 2 damage to enemies while randomly cleansing one negative status effect from each ally within its 3x3 area of influence each turn.',
                '',
                'Role: Utility / Area Controller'
            ],
            'stats': [
                'HP: 10',
                'Attack: 0',
                'Defense: 0',
                'Movement: 3',
                'Range: 1'
            ],
            'skills': [
                {
                    'name': 'INVULNERABILITY (Passive)',
                    'description': 'Complete immunity to all damage sources and status effects.',
                    'details': [
                        'Type: Passive',
                        'Range: Self',
                        'Target: Self',
                        'Line of Sight: No',
                        'Damage: None',
                        'Pierce: No',
                        'Effects: Cannot take damage, immune to all debuffs',
                        'Cooldown: None',
                        'Special: Can only be removed through natural expiration'
                    ]
                },
                {
                    'name': 'ENEMY DAMAGE (Area Damage)',
                    'description': 'Deals 2 damage to all enemy units within the 3x3 area each turn.',
                    'details': [
                        'Type: Area Damage',
                        'Range: 3x3 centered on vapor',
                        'Target: Enemy units in area',
                        'Line of Sight: No',
                        'Damage: 2 per turn',
                        'Pierce: No',
                        'Effects: None',
                        'Cooldown: None',
                        'Special: Activates during owner\'s turn'
                    ]
                },
                {
                    'name': 'ALLY CLEANSING (Status Cleansing)',
                    'description': 'Randomly removes one negative status effect from each allied unit within the area each turn.',
                    'details': [
                        'Type: Status Cleansing',
                        'Range: 3x3 centered on vapor',
                        'Target: Allied units in area',
                        'Line of Sight: No',
                        'Damage: None',
                        'Pierce: No',
                        'Effects: Cleansing (Estrangement, Pry penalty, Jawline immobilization)',
                        'Cooldown: None',
                        'Special: Immediate upon entering area or start of turn'
                    ]
                }
            ],
            'tips': [
                '- Position to maximize enemy exposure while protecting allies',
                '- Use movement to chase retreating enemies or reposition for optimal coverage',
                '- Coordinate with team movement to ensure allies benefit from cleansing',
                '- Build maximum Effluvium charges before summoning for longest duration'
            ],
            'tactical': [
                '- Strong against: Debuff-heavy teams, clustered formations, low-mobility enemies',
                '- Limitations: Cannot directly attack, requires positioning for effectiveness',
                '- Best positioning: Chokepoints, objective areas, ally support zones'
            ]
        },
        'HEINOUS_VAPOR_SAFT_E': {
            'title': 'SAFT-E-GAS (0)',
            'overview': [
                'SAFT-E-GAS is a HEINOUS VAPOR entity summoned by the GAS MACHINIST using the Saft-E-Gas skill. This vapor specializes in defensive area control, blocking ranged attacks while healing allied units within its 3x3 protective area.',
                '',
                'Role: Utility / Area Controller'
            ],
            'stats': [
                'HP: 10',
                'Attack: 0',
                'Defense: 0',
                'Movement: 3',
                'Range: 1'
            ],
            'skills': [
                {
                    'name': 'INVULNERABILITY (Passive)',
                    'description': 'Complete immunity to all damage sources and status effects.',
                    'details': [
                        'Type: Passive',
                        'Range: Self',
                        'Target: Self',
                        'Line of Sight: No',
                        'Damage: None',
                        'Pierce: No',
                        'Effects: Cannot take damage, immune to all debuffs',
                        'Cooldown: None',
                        'Special: Can only be removed through natural expiration'
                    ]
                },
                {
                    'name': 'RANGED ATTACK BLOCKING (Defensive Barrier)',
                    'description': 'Prevents enemies outside the vapor cloud from targeting allies within the protected area.',
                    'details': [
                        'Type: Defensive Barrier',
                        'Range: 3x3 centered on vapor',
                        'Target: Allied units in area',
                        'Line of Sight: No',
                        'Damage: None',
                        'Pierce: No',
                        'Effects: Protection from external ranged attacks',
                        'Cooldown: None',
                        'Special: Enemies inside same vapor cloud can still target protected allies'
                    ]
                },
                {
                    'name': 'ALLY HEALING (Area Healing)',
                    'description': 'Heals allied units within the area for 1 HP per turn.',
                    'details': [
                        'Type: Area Healing',
                        'Range: 3x3 centered on vapor',
                        'Target: Allied units below max HP',
                        'Line of Sight: No',
                        'Damage: None',
                        'Pierce: No',
                        'Effects: Healing +1 HP per turn',
                        'Cooldown: None',
                        'Special: Activates during owner\'s turn'
                    ]
                }
            ],
            'tips': [
                '- Position to cover the maximum number of vulnerable allies',
                '- Use movement to maintain protection as allies advance or retreat',
                '- Place strategically to force enemies into melee engagement',
                '- Build maximum Effluvium charges before summoning for longest duration'
            ],
            'tactical': [
                '- Strong against: Ranged attackers, sustained damage teams, area denial strategies',
                '- Limitations: Cannot directly damage enemies, requires positioning for effectiveness',
                '- Best positioning: Between allies and enemy ranged units, near damaged allies'
            ]
        },
        'HEINOUS_VAPOR_COOLANT': {
            'title': 'COOLANT GAS (2)',
            'overview': [
                'COOLANT GAS is a HEINOUS VAPOR entity created by the GAS MACHINIST using the Diverge skill. This vapor specializes in healing, providing 3 HP healing per turn to allies within its 3x3 area of influence.',
                '',
                'Role: Utility / Area Controller'
            ],
            'stats': [
                'HP: 10',
                'Attack: 0',
                'Defense: 0',
                'Movement: 3',
                'Range: 1'
            ],
            'skills': [
                {
                    'name': 'INVULNERABILITY (Passive)',
                    'description': 'Complete immunity to all damage sources and status effects.',
                    'details': [
                        'Type: Passive',
                        'Range: Self',
                        'Target: Self',
                        'Line of Sight: No',
                        'Damage: None',
                        'Pierce: No',
                        'Effects: Cannot take damage, immune to all debuffs',
                        'Cooldown: None',
                        'Special: Can only be removed through natural expiration'
                    ]
                },
                {
                    'name': 'ALLY HEALING (Area Healing)',
                    'description': 'Heals allied units within the area for 3 HP per turn.',
                    'details': [
                        'Type: Area Healing',
                        'Range: 3x3 centered on vapor',
                        'Target: Allied units below max HP',
                        'Line of Sight: No',
                        'Damage: None',
                        'Pierce: No',
                        'Effects: Healing +3 HP per turn',
                        'Cooldown: None',
                        'Special: Activates during owner\'s turn'
                    ]
                }
            ],
            'tips': [
                '- Build maximum Effluvium charges before using Diverge for longest healing duration',
                '- Position to cover the most critically wounded allies',
                '- Use movement to maintain healing coverage as battle lines shift',
                '- Coordinate with CUTTING GAS for simultaneous healing and damage pressure'
            ],
            'tactical': [
                '- Strong against: Attrition strategies, sustained damage, low-healing teams',
                '- Limitations: No protective or offensive capabilities, requires positioning',
                '- Best positioning: Central ally clusters, objective defense points, critical unit support zones'
            ]
        },
        'HEINOUS_VAPOR_CUTTING': {
            'title': 'CUTTING GAS (%)',
            'overview': [
                'CUTTING GAS is a HEINOUS VAPOR entity created by the GAS MACHINIST using the Diverge skill. This vapor specializes in offensive area control, dealing 3 piercing damage per turn to all enemies within its 3x3 area of influence.',
                '',
                'Role: Utility / Area Controller'
            ],
            'stats': [
                'HP: 10',
                'Attack: 0',
                'Defense: 0',
                'Movement: 3',
                'Range: 1'
            ],
            'skills': [
                {
                    'name': 'INVULNERABILITY (Passive)',
                    'description': 'Complete immunity to all damage sources and status effects.',
                    'details': [
                        'Type: Passive',
                        'Range: Self',
                        'Target: Self',
                        'Line of Sight: No',
                        'Damage: None',
                        'Pierce: No',
                        'Effects: Cannot take damage, immune to all debuffs',
                        'Cooldown: None',
                        'Special: Can only be removed through natural expiration'
                    ]
                },
                {
                    'name': 'PIERCING DAMAGE (Area Damage)',
                    'description': 'Deals 3 piercing damage per turn to all enemy units in the area.',
                    'details': [
                        'Type: Area Damage',
                        'Range: 3x3 centered on vapor',
                        'Target: Enemy units in area',
                        'Line of Sight: No',
                        'Damage: 3 piercing per turn',
                        'Pierce: Yes',
                        'Effects: Bypasses all defense',
                        'Cooldown: None',
                        'Special: Activates during owner\'s turn'
                    ]
                }
            ],
            'tips': [
                '- Build maximum Effluvium charges before using Diverge for longest damage duration',
                '- Position to cover enemy clusters or chokepoints',
                '- Use movement to chase retreating enemies or deny key areas',
                '- Coordinate with COOLANT GAS for simultaneous healing and damage pressure'
            ],
            'tactical': [
                '- Strong against: High-defense units, clustered enemies, static formations',
                '- Limitations: Cannot heal or protect allies, requires positioning for effectiveness',
                '- Best positioning: Enemy clusters, chokepoints, high-value target areas'
            ]
        },
        UnitType.HEINOUS_VAPOR: {
            'title': 'HEINOUS VAPOR',
            'overview': [
                'HEINOUS VAPOR entities are summoned by the GAS MACHINIST and serve as battlefield manipulators with diverse abilities. Each vapor type has unique properties and effects based on the skill used to create it.',
                '',
                'Role: Summoned Entity / Area Control / Support'
            ],
            'stats': [
                'HP: 10',
                'Attack: 0',
                'Defense: 0',
                'Movement: 3',
                'Range: 1'
            ],
            'skills': [
                {
                    'name': 'INVULNERABILITY (Passive)',
                    'description': 'Complete immunity to all damage sources and status effects.',
                    'details': [
                        'Type: Passive',
                        'Range: Self',
                        'Target: Self',
                        'Line of Sight: No',
                        'Damage: None',
                        'Pierce: No',
                        'Effects: Cannot take damage, immune to all debuffs',
                        'Cooldown: None',
                        'Special: Can only be removed through natural expiration or Diverge skill'
                    ]
                }
            ],
            'tips': [
                '- Each vapor type has unique area effects and abilities',
                '- Duration depends on GAS MACHINIST\'s Effluvium charges when summoned',
                '- Can be targeted by Diverge skill to split into two different vapor types',
                '- Move strategically to maximize area coverage and effects'
            ],
            'tactical': [
                '- Abilities vary by vapor type - check specific vapor help for details',
                '- Generally strong against: Status effect users, clustered enemies',
                '- Best positioning: Strategic locations for maximum area control'
            ]
        }
    }

    return unit_help_dict
