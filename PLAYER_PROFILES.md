# Player Profile System

## Overview

The player profile system tracks player statistics and preferences. Profiles are stored as JSON files in the `profiles/` directory.

## Features

### Current Stats Tracked:
- **Wins** - Total games won
- **Losses** - Total games lost
- **Games Played** - Total games completed
- **Unit Picks** - How many times each unit has been selected
- **Win Rate** - Calculated as wins/games_played * 100

### Profile Management:
- **8 character name limit** (automatically enforced and uppercased)
- **Multiple profiles** - Create and switch between different players
- **Persistent storage** - Profiles saved as JSON in `profiles/` directory
- **Easy expansion** - `achievements` and `preferences` dicts ready for future features

## File Structure

```
profiles/
├── .gitkeep          # Keeps directory in git
├── PLAYER1.json      # Profile files (excluded from git)
└── PLAYER2.json
```

## Usage

### Creating a Profile

```python
from boneglaive.game.player_profile import profile_manager

# Create new profile (name auto-truncated to 8 chars and uppercased)
try:
    profile = profile_manager.create_profile("PLAYER")
    profile_manager.set_current_profile(profile)
except ValueError as e:
    print(f"Error: {e}")  # Profile already exists
```

### Loading a Profile

```python
# Load existing profile
profile = profile_manager.load_profile("PLAYER")
if profile:
    profile_manager.set_current_profile(profile)
```

### Recording Stats

```python
from boneglaive.utils.constants import UnitType

# Get current profile
profile = profile_manager.get_current_profile()

if profile:
    # Record game result
    profile.record_win()
    # or profile.record_loss()

    # Record unit selection
    profile.record_unit_pick(UnitType.GRAYMAN)

    # Save changes
    profile_manager.save_profile(profile)
```

### Viewing Stats

```python
# Get profile stats
profile = profile_manager.get_current_profile()

print(f"Name: {profile.name}")
print(f"Win Rate: {profile.get_win_rate():.1f}%")
print(f"Record: {profile.wins}W - {profile.losses}L")
print(f"Favorite Unit: {profile.get_most_picked_unit()}")
print(f"Total Games: {profile.games_played}")

# Unit pick stats
for unit_name, picks in profile.unit_picks.items():
    print(f"{unit_name}: {picks} picks")
```

### Listing All Profiles

```python
# List all available profiles
profiles = profile_manager.list_profiles()
for name in profiles:
    print(name)
```

### Deleting a Profile

```python
# Delete a profile
if profile_manager.delete_profile("PLAYER"):
    print("Profile deleted")
else:
    print("Profile not found")
```

## Integration Points

### Game Engine Integration

Update `boneglaive/game/engine.py` to track stats:

```python
from boneglaive.game.player_profile import profile_manager

# When game ends:
def end_game(self, winner_player: int):
    profile = profile_manager.get_current_profile()
    if profile and self.current_player == winner_player:
        profile.record_win()
    elif profile:
        profile.record_loss()
    profile_manager.save_profile(profile)

# During unit recruitment:
def recruit_unit(self, unit_type: UnitType):
    profile = profile_manager.get_current_profile()
    if profile:
        profile.record_unit_pick(unit_type)
        profile_manager.save_profile(profile)
```

### Menu UI Integration

Add profile menu to `boneglaive/ui/menu_ui.py`:

```python
# In _create_main_menu():
profile_menu = Menu("Profile", [
    MenuItem("Select Profile", self._select_profile),
    MenuItem("Create Profile", self._create_profile),
    MenuItem("View Stats", self._view_stats),
    MenuItem("Delete Profile", self._delete_profile),
    MenuItem("Back", lambda: ("submenu", None))
])

# Add to main menu items
MenuItem("Profile", None, profile_menu)
```

## Data Structure

Profile JSON format:

```json
{
  "name": "PLAYER",
  "wins": 10,
  "losses": 5,
  "games_played": 15,
  "unit_picks": {
    "GLAIVEMAN": 12,
    "GRAYMAN": 8,
    "INTERFERER": 15,
    ...
  },
  "achievements": {},
  "preferences": {}
}
```

## Future Expansion Ideas

### Achievements Dict
```python
profile.achievements = {
    "first_win": True,
    "perfect_game": False,
    "all_units_played": True,
    "win_streak_10": False
}
```

### Preferences Dict
```python
profile.preferences = {
    "favorite_map": "edgecase",
    "preferred_difficulty": "hard",
    "theme": "autumn"
}
```

### Additional Stats
```python
# Add to PlayerProfile dataclass:
total_damage_dealt: int = 0
total_healing_done: int = 0
favorite_map: str = ""
longest_game_turns: int = 0
shortest_game_turns: int = 999
skill_usage_counts: Dict[str, int] = field(default_factory=dict)
```

## Notes

- Profile files are excluded from git (see `.gitignore`)
- Names are automatically sanitized for safe filenames
- All stats methods include logging for debugging
- Profile manager is a singleton accessible via `profile_manager`
- Easily extensible with new fields without breaking existing profiles
