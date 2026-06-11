# Hornswoggle — Skill Trajectory Reference

## Overview

Hornswoggle is the Landscaper's bread-and-butter terrain manipulation skill. She emits
a beam from her Tibetan horn array in one of 8 directions. The beam travels until it hits
a piece of terrain or furniture. That terrain is grabbed, ripped from the ground, and
dragged along a perpendicular path rotated 90 degrees counter-clockwise from the beam
direction. As the terrain flies through the air, it becomes superheated and drops molten
slag along the drag path, which hardens into temporary walls. The terrain is deposited
at the end of the drag path.

## The Core Rule

**The drag direction is always 90 degrees counter-clockwise from the beam direction.**

This produces a pinwheel pattern when all 8 directions are visualized at once.
The player picks a direction to fire; the drag direction is entirely determined by that
choice — bizarre at first, completely predictable once learned.

## Drag Direction Table

| Fire Direction | Drag Direction (90° CCW) |
|----------------|--------------------------|
| N              | W                        |
| NE             | NW                       |
| E              | N                        |
| SE             | NE                       |
| S              | E                        |
| SW             | SE                       |
| W              | S                        |
| NW             | SW                       |

## Step-by-Step Mechanic

1. Landscaper chooses one of 8 directions (N, NE, E, SE, S, SW, W, NW)
2. A beam fires outward from the Landscaper in that direction
3. The beam travels tile-by-tile until it hits a **terrain or furniture tile**
   - If it hits a unit first, or reaches the edge of the map with no terrain: skill fails
   - Can grab dynamic terrain (Marrow Dike walls, Derelict buildings, Rails, etc.)
4. The terrain tile is **removed** from its position (ground becomes empty)
5. The terrain is then **dragged** from the grab point in the 90° CCW direction
6. For each tile along the drag path:
   - If the tile is **empty/passable**: deposit a **slag wall** (temporary blocking terrain)
   - If the tile is **blocked** (another terrain, unit, map edge): the terrain stops here
     and is deposited on the last valid empty tile. It does NOT replace existing terrain.
7. The original terrain/furniture is **deposited** at the final position of the drag path
8. Slag walls persist for a few turns, then crumble

## What Gets Created

- **Slag walls**: temporary blocking terrain deposited along the drag path
- **Relocated terrain**: the grabbed terrain/furniture placed at the end of the drag path
- The original position becomes **empty ground**

## All 8 Directions — Individual Diagrams

Legend: `@` = Landscaper, `*` = beam, `#` = terrain (start → end), `=` = slag wall

Each diagram shows the before state (beam firing) and after state (drag complete).

### Fire North → Drag West

```
. . . . . # . . .        . . . . . . . . .
. . . . . * . . .        . . . . . . . . .
. . . . . * . . .   →    . . . . . . . . .
. . . . . * . . .        . . . . . . . . .
. . . . . @ . . .        . # = = = @ . . .
```

Beam fires north 4 tiles, grabs terrain at top.
Terrain dragged west from grab point along Landscaper's row.
Slag deposited along westward path. Terrain deposited at west end.

### Fire Northeast → Drag Northwest

```
. . . . . . . . #        . . . . # . . . .
. . . . . . . * .        . . . . . = . . .
. . . . . . * . .   →    . . . . . . = . .
. . . . . * . . .        . . . . . . . = .
. . . . @ . . . .        . . . . @ . . . .
```

Beam fires NE, grabs terrain at top-right.
Terrain dragged NW from grab point. Slag along NW diagonal.

### Fire East → Drag North

```
. . . . . . . . .        . . . . . . . . #
. . . . . . . . .        . . . . . . . . =
. . . . . . . . .   →    . . . . . . . . =
. . . . . . . . .        . . . . . . . . =
. . . . @ * * * #        . . . . @ . . . .
```

Beam fires east, grabs terrain at right.
Terrain dragged north from grab point. Slag along northward column.

### Fire Southeast → Drag Northeast

```
. . . . @ . . . .        . . . . @ . . . #
. . . . . * . . .        . . . . . . . = .
. . . . . . * . .   →    . . . . . . = . .
. . . . . . . * .        . . . . . = . . .
. . . . . . . . #        . . . . . . . . .
```

Beam fires SE, grabs terrain at bottom-right.
Terrain dragged NE from grab point. Slag along NE diagonal.

### Fire South → Drag East

```
. . . . . @ . . .        . . . . . @ . . .
. . . . . * . . .        . . . . . . . . .
. . . . . * . . .   →    . . . . . . . . .
. . . . . * . . .        . . . . . . . . .
. . . . . # . . .        . . . . . # = = #
```

Beam fires south, grabs terrain at bottom.
Terrain dragged east from grab point along bottom row.
Slag deposited along eastward path. Terrain deposited at east end.

### Fire Southwest → Drag Southeast

```
. . . . . . . . @        . . . . . . . . @
. . . . . . . * .        . . . . . . . . .
. . . . . . * . .   →    . . . . . . . . .
. . . . . * . . .        . . . . . = . . .
. . . . # . . . .        . . . . . . = . .
. . . . . . . . .        . . . . . . . = .
. . . . . . . . .        . . . . . . . . #
```

Beam fires SW, grabs terrain at bottom-left.
Terrain dragged SE from grab point. Slag along SE diagonal.

### Fire West → Drag South

```
. . . . . . . . .        . . . . . . . . .
. . . . . . . . .        . . . . . . . . .
. . . . . . . . .        . . . . . . . . .
. . . . . . . . .        . . . . . . . . .
# * * * @ . . . .        . . . . @ . . . .
. . . . . . . . .        = . . . . . . . .
. . . . . . . . .        = . . . . . . . .
. . . . . . . . .        = . . . . . . . .
. . . . . . . . .        # . . . . . . . .
```

Beam fires west, grabs terrain at left.
Terrain dragged south from grab point. Slag along southward column.

### Fire Northwest → Drag Southwest

```
# . . . . . . . .        . . . . . . . . .
. * . . . . . . .        = . . . . . . . .
. . * . . . . . .   →    . = . . . . . . .
. . . * . . . . .        . . = . . . . . .
. . . . @ . . . .        . . . # @ . . . .
```

Beam fires NW, grabs terrain at top-left.
Terrain dragged SW from grab point. Slag along SW diagonal.

## Pinwheel Visualization (all 8 at once — final state)

All 8 beams fired simultaneously, showing grab points (`*`), slag walls (`=`),
and deposited terrain (`#`):

```
. . . . . . . . . . . . . . . . . . . . .
. . . . . . . . . . . . . . . . . . . . .
. . . . . . . . . . . . . . . . . . . . .
. . . . . . . . . . . . . . . . . . . . .
. . . . . . . . . . . . . . . . . . . . .
. . . . . . . . . . . . . . # . . . . . .
. . . . . . # . . . = . . = . . . . . . .
. . . . . . . = . = . . . = . . . . . . .
. . . . . . . . = . . . = . . . . . . . .
. . . . . . . = . = . = . . . . . . . . .
. . . . . . # = = = @ = = = # . . . . . .
. . . . . . . . . . = . = . . . . . . . .
. . . . . . . . . . . = . = . . . . . . .
. . . . . . . . . . = . . . = . . . . . .
. . . . . . . . . = . . . . . = . . . . .
. . . . . . . . # . . . . . . . # . . . .
. . . . . . . . . . . . . . . . . . . . .
. . . . . . . . . . . . . . . . . . . . .
. . . . . . . . . . . . . . . . . . . . .
. . . . . . . . . . . . . . . . . . . . .
. . . . . . . . . . . . . . . . . . . . .
```

This forms the counter-clockwise pinwheel pattern. Each spoke extends outward from
the Landscaper (beam path), and from each spoke's tip, the drag arm branches off
perpendicular in the CCW direction, depositing slag and terrain.

## Implementation Notes

- Beam range: TBD (may be unlimited until hitting terrain or map edge)
- Drag distance: TBD (fixed length, or until blocked?)
- Slag wall duration: TBD (a few turns)
- Slag wall terrain type: new TerrainType needed (SLAG_WALL or similar)
- The beam does NOT pass through units — if a unit is in the beam path before
  terrain, the skill fails or stops at the unit
- The drag path deposits slag on empty tiles; if it hits a blocked tile, the
  terrain drops on the last empty tile before the obstruction
- Grabbed terrain is fully removed from its original position
- Dynamic terrain (Marrow Dike, Derelict Building, Rails) CAN be grabbed
- Cooldown: TBD (needs careful balancing with Translative Stroke passive)

## STATUS: CONFIRMED — trajectory mechanic verified with user
