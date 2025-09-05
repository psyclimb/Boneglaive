# Boneglaive Map Format Specification

## JSON Map Format v1.0

### Basic Structure
```json
{
  "format_version": "1.0",
  "name": "Map Name",
  "width": 20,
  "height": 10,
  "terrain": {
    "y,x": "TERRAIN_TYPE"
  },
  "cosmic_values": {
    "y,x": value
  }
}
```

### Terrain Types
Valid terrain type strings (from TerrainType enum):
- `EMPTY` - Basic empty tile, no effects
- `LIMESTONE` - Blocks movement and unit placement
- `DUST` - Light limestone dusting, visual only (passable)
- `PILLAR` - Large limestone pillar, blocks movement and unit placement
- `FURNITURE` - Generic furniture, blocks movement but not line of sight
- `COAT_RACK` - Coat rack, blocks movement but not line of sight
- `OTTOMAN` - Ottoman seating, blocks movement but not line of sight
- `CONSOLE` - Console table, blocks movement but not line of sight
- `DEC_TABLE` - Decorative table, blocks movement but not line of sight
- `MARROW_WALL` - Marrow Dike wall, blocks movement and unit placement but not permanently
- `RAIL` - Rail track, passable by all units but FOWL_CONTRIVANCE gets special movement
- `TIFFANY_LAMP` - Tiffany-style decorative lamp, blocks movement but not line of sight
- `STAINED_STONE` - Stained stone formation, blocks movement and unit placement
- `EASEL` - Artist's easel with canvas, blocks movement but not line of sight
- `SCULPTURE` - Stone sculpture pedestal, blocks movement but not line of sight
- `BENCH` - Viewing bench for art gallery, blocks movement but not line of sight
- `PODIUM` - Display podium, blocks movement but not line of sight
- `VASE` - Decorative pottery vase, blocks movement but not line of sight
- `CANYON_FLOOR` - Canyon floor with natural sediment, visual only (passable)
- `HYDRAULIC_PRESS` - Industrial hydraulic press, blocks movement and unit placement
- `WORKBENCH` - Industrial workbench, blocks movement but not line of sight
- `COUCH` - Household couch, blocks movement but not line of sight
- `TOOLBOX` - Industrial toolbox, blocks movement but not line of sight
- `COT` - Temporary sleeping cot, blocks movement but not line of sight
- `CONVEYOR` - Industrial conveyor belt, blocks movement but not line of sight
- `CONCRETE_FLOOR` - Industrial concrete floor, visual only (passable)

### Validation Rules
1. **Grid Bounds**: x ∈ [0, width-1], y ∈ [0, height-1]
2. **Standard Size**: width=20, height=10 (current game constant)
3. **Terrain Types**: Must be valid TerrainType enum values
4. **Cosmic Values**: Only valid on furniture terrain types, range 1-9
5. **Coordinate Format**: "y,x" string format (matches Python tuple keys)
6. **Missing Tiles**: Default to EMPTY if not specified

### Example: Simple Map
```json
{
  "format_version": "1.0",
  "name": "Test Arena",
  "width": 20,
  "height": 10,
  "terrain": {
    "5,10": "PILLAR",
    "2,5": "FURNITURE",
    "7,15": "OTTOMAN"
  },
  "cosmic_values": {
    "2,5": 7,
    "7,15": 3
  }
}
```

### File Naming Convention
- Map files: `maps/{map_name}.json`
- Map name derived from filename (snake_case)
- Example: `maps/stained_stones.json` → map_name "stained_stones"

### External Editor Requirements
1. **Grid Editor**: Visual 20x10 grid interface
2. **Terrain Palette**: Clickable terrain type selector
3. **Cosmic Value Editor**: Numeric input for furniture pieces
4. **Real-time Validation**: Constraint checking as user edits
5. **Export/Import**: JSON file handling
6. **Preview Mode**: Visual representation of terrain types