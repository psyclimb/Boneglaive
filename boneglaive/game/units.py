#!/usr/bin/env python3
from boneglaive.utils.constants import UNIT_STATS

class Unit:
    def __init__(self, unit_type, player, y, x):
        self.type = unit_type
        self.player = player  # 1 or 2
        self.y = y
        self.x = x
        self.hp, self.attack, self.defense, self.move_range, self.attack_range = UNIT_STATS[unit_type]
        self.max_hp = self.hp
        self.move_target = None
        self.attack_target = None
        
    def is_alive(self):
        return self.hp > 0