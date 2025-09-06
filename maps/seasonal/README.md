# Seasonal Maps

This directory contains seasonal variants of maps that activate during astronomical events:

- **spring_equinox/** - Spring Equinox maps (March 19-22)
- **summer_solstice/** - Summer Solstice maps (June 19-22)  
- **autumn_equinox/** - Autumn Equinox maps (September 21-24)
- **winter_solstice/** - Winter Solstice maps (December 20-23)

## Creating Seasonal Maps

1. Copy an existing map JSON file to the appropriate seasonal directory
2. Modify terrain, cosmic values, and map name to match the seasonal theme
3. The game will automatically load seasonal variants when active

## Seasonal Themes

- **Spring Equinox**: Renewal and growth, light/dark balance, green colors
- **Summer Solstice**: Peak light and power, maximum energy, bright colors
- **Autumn Equinox**: Harvest and balance, preparation for rest, warm colors  
- **Winter Solstice**: Deepest night and reflection, inner strength, cool colors

## Example Structure

```
seasonal/
├── spring_equinox/
│   ├── lime_foyer.json      # Spring variant of lime foyer
│   └── stained_stones.json  # Spring variant of stained stones
├── summer_solstice/
│   └── edgecase.json        # Summer variant of edge case
└── ...
```
