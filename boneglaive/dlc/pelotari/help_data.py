#!/usr/bin/env python3
"""
PELOTARI Unit Help Data

This file contains the help/documentation data for the PELOTARI DLC unit,
displayed in the ASCII UI help system when players press '?' during gameplay.
"""

# PELOTARI help data following the format used in ui_components.py
UNIT_HELP_DATA = {
    'title': 'PELOTARI',
    'overview': [
        'The PELOTARI is a jai alai specialist who launches ricocheting ball projectiles with deadly',
        'precision. Mastering wall angles and trajectory planning is essential to leverage this unit\'s',
        'buff-stealing, skill-reflecting, and displacement capabilities. High skill floor and ceiling.',
        '',
        'Role: Burst Damage / Disabler / Displacer',
        'Difficulty: ***** (5 Glaives - Highest Complexity)'
    ],
    'stats': [
        'HP: 18',
        'Attack: 4',
        'Defense: 0',
        'Movement: 4',
        'Range: 4',
        'Symbol: J'
    ],
    'skills': [
        {
            'name': 'RIPOSTE (Passive)',
            'description': 'Grants +2 defense. When PELOTARI is hit by a basic attack, fires 8 balls in all directions (N, NE, E, SE, S, SW, W, NW), each dealing 2 damage with 2 ricochets off terrain. After triggering, loses the defense bonus and enters a 2-turn cooldown before Riposte reactivates.',
            'details': [
                'Type: Passive',
                'Effect: +2 Defense (2-turn cooldown after triggering)',
                'Counter Damage: 2 per ball × 8 balls = 16 total',
                'Counter Range: 4 tiles per ball',
                'Ricochets: Up to 2 bounces per ball',
                'Special: Only triggers on basic attacks, not skills; cannot be Poached (triggers counterattack instead)'
            ]
        },
        {
            'name': 'POACH (Active) [Key: 1]',
            'description': 'Fires a ball that MUST ricochet to steal buffs. Initial straight-line shot deals 4 damage but steals nothing. After ricocheting off terrain/units/furniture, the ball deals 6 damage and steals one buff from the next enemy hit, converting it into a projectile. Allied units can catch the buff ball to gain the stolen effect.',
            'details': [
                'Type: Active',
                'Range: 6',
                'Damage: 4 (pre-ricochet), 6 (post-ricochet)',
                'Cooldown: 3 turns',
                'Steal-able Buffs: Parallax, Investment, Partition, Severance, Pumped Up, Karrier Rave, Trauma Processing, Site Inspection, Ossify, Valuation Oracle',
                'Special: Ricochet required for buff stealing; enemy PELOTARI with Riposte triggers counterattack'
            ]
        },
        {
            'name': 'BACKHAND (Active) [Key: 2]',
            'description': 'Readies a counter stance for 3 turns. When an enemy uses a single-target skill on PELOTARI, catches and reflects it back as a ricocheting ball projectile. The ball bounces up to 2 times (6 tiles per bounce) and applies full skill effects to anyone hit. Allies are protected from friendly fire. Ends counter after reflecting one skill.',
            'details': [
                'Type: Active',
                'Range: Self (counter stance)',
                'Duration: 3 turns (ends early if reflects a skill)',
                'Cooldown: 4 turns',
                'Reflectable Skills: Judgement, Estrange, Neural Shunt, Granite Geas, Pry, Auction Curse, Fragcrest, Expedite',
                'Special: Nullifies original skill; reflected ball can hit multiple targets along path; one reflection per turn'
            ]
        },
        {
            'name': 'MATADOR (Active) [Key: 3]',
            'description': 'The killing shot. Launches a devastating ball nuke in a straight line. Deals 4 damage and knocks targets back 3 tiles. Targets slammed into terrain take +2 damage. Gains additional ricochets based on enemy team HP loss: +1 bounce per 15% HP lost (max 8 bounces). The lower their HP, the more devastating this shot becomes. Furniture hit is launched 3 tiles.',
            'details': [
                'Type: Active',
                'Range: 6 (straight line only)',
                'Damage: 4 base, +2 slam bonus, 4 per furniture collision',
                'Displacement: 3 tiles knockback',
                'Cooldown: 7 turns',
                'Bounces: 2 base, up to 8 total (+1 per 15% enemy HP lost)',
                'Special: Scales with enemy HP loss; always travels straight; launches furniture; game-ending finisher'
            ]
        }
    ],
    'tips': [
        '- Riposte provides +2 DEF but goes on cooldown after triggering—bait attacks when off cooldown',
        '- Poach requires the ball to ricochet before buff stealing works; angle shots off walls',
        '- Backhand nullifies the first enemy skill per turn—activate before enemy skill phase',
        '- Matador is a game-ending finisher: chip enemies down first, then unleash at 40-60% HP for 4-6 bounces',
        '- At 10% enemy HP, Matador gains 8 bounces—enough to cross the map 2.4x and wipe the team',
        '- 0 base defense means Riposte uptime is critical for survival',
        '- Poaching an enemy PELOTARI with active Riposte triggers their diagonal counterattack'
    ],
    'tactical': [
        '- Strong against: Buff-dependent units (DELPHIC APPRAISER, POTPOURRIST), single-target skill users (INTERFERER, GRAYMAN), static formations',
        '- Weak against: Multi-target attacks, high-mobility units (MANDIBLE FOREMAN, GLAIVEMAN), units that bypass Backhand (area skills)',
        '- Positioning: Back line at 4-6 tile range, near walls for Poach angles, protect from dive units that ignore Riposte'
    ]
}
