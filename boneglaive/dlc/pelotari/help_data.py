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
        'A jai alai virtuoso wielding a cesta to launch ricocheting pelota balls with deadly precision.',
        'This conditionally tanky ranged unit excels in counterattacks, retaliating with four-directional',
        'spreads, stealing buffs through wall bounces, and delivering scaling finishers that end games.',
        '',
        'Role: Tank / Burst Damage / Disabler / Displacer',
        'Difficulty: *****'
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
            'description': 'Grants defensive stance that erupts into a four-directional counter-barrage when struck by basic attacks. Direction pattern (cardinal or diagonal) is chosen randomly. Each ricocheting ball deals damage before the stance enters cooldown.',
            'details': [
                'Type: Passive',
                'Effect: +4 Defense (3-turn cooldown after triggering)',
                'Counter Damage: 2 per ball × 4 balls = 8 total',
                'Counter Pattern: Cardinal (N,E,S,W) OR Diagonal (NE,SE,SW,NW), chosen randomly',
                'Counter Range: 4 tiles per ball',
                'Ricochets: Up to 2 bounces per ball',
                'Special: Only triggers on basic attacks, not skills; cannot be Poached (triggers counterattack instead)'
            ]
        },
        {
            'name': 'POACH (Active) [Key: 1]',
            'description': 'Launches a ricocheting ball that steals buffs from enemies only after bouncing off terrain, units, or furniture. The stolen buff becomes a projectile that allies can intercept to gain its effect.',
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
            'description': 'Enters a defensive stance that catches enemy single-target skills and reflects them back as ricocheting projectiles. The reflected skill bounces across the battlefield, applying its full effects to all enemies struck.',
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
            'description': 'The killing shot—launches a devastating ball that knocks targets into terrain for bonus damage. Gains exponentially more ricochets as enemy team health decreases, transforming into a map-wiping finisher.',
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
        '- Riposte provides +4 DEF but goes on cooldown after triggering—bait attacks when off cooldown',
        '- Riposte randomly fires cardinal OR diagonal spread—position near walls to maximize coverage',
        '- Poach requires the ball to ricochet before buff stealing works; angle shots off walls',
        '- Backhand nullifies the first enemy skill per turn—activate before enemy skill phase',
        '- Matador is a game-ending finisher: chip enemies down first, then unleash at 40-60% HP for 4-6 bounces',
        '- At 10% enemy HP, Matador gains 8 bounces—enough to cross the map 2.4x and wipe the team',
        '- 0 base defense means Riposte uptime is critical for survival',
        '- Poaching an enemy PELOTARI with active Riposte triggers their 4-ball counterattack'
    ],
    'tactical': [
        '- Strong against: Buff-dependent units (DELPHIC APPRAISER, POTPOURRIST), single-target skill users (INTERFERER, GRAYMAN), static formations',
        '- Weak against: Multi-target attacks, high-mobility units (MANDIBLE FOREMAN, GLAIVEMAN), units that bypass Backhand (area skills)',
        '- Positioning: Back line at 4-6 tile range, near walls for Poach angles, protect from dive units that ignore Riposte'
    ]
}
