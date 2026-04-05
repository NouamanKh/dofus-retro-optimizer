# Optimiseur d'Élément Dofus Retro

## Concept & Vision

A sleek, nostalgic item optimizer for Dofus Retro (1.29) that helps players find the perfect equipment combination to maximize their chosen element. The app captures the game's retro MMORPG aesthetic while providing powerful optimization algorithms. It's like having a theorycrafter's spreadsheet, but with the visual charm of the Dofus universe.

## Design Language

### Aesthetic Direction
Medieval fantasy meets pixel-art nostalgia. Think warm parchment textures, ornate borders reminiscent of the game's UI, and elemental color coding that feels magical.

### Color Palette
- **Primary**: `#2D1B4E` (Deep Purple - Dofus theme)
- **Secondary**: `#F4E4BC` (Parchment cream)
- **Accent Vitalité**: `#E74C3C` (Red - heart)
- **Accent Sagesse**: `#9B59B6` (Purple - wisdom)
- **Accent Force**: `#E67E22` (Orange - strength)
- **Accent Intelligence**: `#3498DB` (Blue - magic)
- **Accent Chance**: `#2ECC71` (Green - luck)
- **Accent Agilité**: `#F1C40F` (Yellow - agility)
- **Background**: `#1A1A2E` (Dark navy)
- **Text**: `#F4E4BC` (Cream)
- **Text Secondary**: `#8B8B8B`

### Typography
- **Headings**: "MedievalSharp" (Google Font) - fantasy serif feel
- **Body**: "Inter" (Google Font) - clean readability
- **Stats**: "JetBrains Mono" (Google Font) - for numbers

### Spatial System
- Base unit: 8px
- Card padding: 24px
- Section gaps: 32px
- Border radius: 8px (slightly rounded, not too modern)

### Motion Philosophy
- Subtle fade-ins for results (300ms ease-out)
- Element icons pulse gently when selected
- Results slide in from bottom with stagger effect
- Tooltip animations on item hover

## Layout & Structure

### Page Structure
1. **Header** - App title with Dofus-style decorative elements
2. **Selection Panel** - Element selector (visual icons) + Level slider
3. **Results Section** - Top optimized sets with item breakdowns
4. **Item Details Modal** - Expanded view when clicking an item

### Responsive Strategy
- Desktop: Two-column layout (selection left, results right)
- Tablet/Mobile: Stacked single column
- Breakpoints: 768px, 1024px

## Features & Interactions

### Core Features

1. **Element Selection**
   - 5 clickable element icons: Fire, Water, Earth, Air, Neutral
   - Active state: glowing border + scale up
   - Default: None selected

2. **Level Range Selection**
   - Slider from level 1 to 200
   - Quick presets: 100, 150, 180, 200
   - Shows min/max level constraints

3. **Optimization Engine**
   - Brute-force combination generator
   - Equipment slots: Weapon, Hat, Cloak, Amulet, Ring (x2), Belt, Boots, Shield
   - Ranks combinations by total element value
   - Handles set bonuses if items are from same set
   - Respects level requirements

4. **Results Display**
   - Top 10 combinations ranked by element score
   - Each result shows:
     - Total element value
     - Item list with individual stats
     - Level requirement
     - Set name (if applicable)
   - Click item to see full details

5. **Item Database**
   - Curated list of notable Dofus Retro items
   - Each item has: name, type, level, element bonuses, set bonus, image URL

### Interaction Details

- **Hover on element icon**: Scale 1.1, glow effect
- **Click element**: Sets as active, updates results
- **Drag level slider**: Debounced update (300ms), shows current value
- **Click result card**: Expands to show item details
- **Empty state**: "Select an element to begin optimizing"

### Edge Cases
- No items found for criteria: Show helpful message
- Level too low for any items: Suggest raising level
- API/load errors: Graceful fallback message

## Component Inventory

### ElementIcon
- States: default, hover, active, disabled
- Props: element type, isActive, onClick
- Visual: Custom SVG icons for each element

### LevelSlider
- States: default, dragging
- Shows current value tooltip while dragging
- Tick marks at preset levels

### ResultCard
- States: default, hover, expanded
- Shows rank badge, total score, item thumbnails
- Expandable to show full item list

### ItemChip
- Small badge showing single item with icon and key stat
- Hover shows quick tooltip

### SetBonusBadge
- Special styling for items belonging to a set
- Shows set name and bonus effect

## Technical Approach

### Stack
- **Framework**: React with Vite
- **Styling**: Tailwind CSS
- **State**: React hooks (useState, useMemo for optimization)
- **Build**: Single page app

### Architecture
```
/src
  /components
    - ElementSelector.jsx
    - LevelSlider.jsx
    - ResultsPanel.jsx
    - ResultCard.jsx
    - ItemModal.jsx
  /data
    - items.js (item database)
    - elements.js (element constants)
  /utils
    - optimizer.js (combination algorithm)
  /hooks
    - useOptimizer.js
  App.jsx
  main.jsx
  index.css
```

### Item Data Structure
```javascript
{
  id: "dofus_2411",
  name: "Gobball Headgear",
  type: "hat",
  level: 20,
  elements: {
    vitalite: 0,
    sagesse: 0,
    force: 0,
    intelligence: 0,
    chance: 0,
    agilite: 0
  },
  set: "Gobball Set",
  apiId: 2411
}
```

### Set Bonus Structure
```javascript
{
  id: "set_1",
  name: "Gobball Set",
  items: ["dofus_2411", "dofus_2412", ...],
  bonuses: {
    2: { vitalite: 5, sagesse: 5, agilite: 5 },
    3: { vitalite: 10, sagesse: 10, agilite: 10 },
    ...
  }
}
```

### Optimization Algorithm
**JavaScript Version (Greedy + Local Search):**
1. Greedy initial selection - pick best element item for each slot
2. Multiple iterations to improve selection
3. Local search - swap items to improve score
4. Set bonus optimization - try adding set pieces
5. Random variations + local search for alternative solutions

**Python Version (MILP with PuLP):**
1. Binary decision variables for each item
2. Binary variables for set bonus activation
3. Maximize element value with constraints
4. Proper set bonus logic (only one tier active, requires minimum pieces)
5. Exact optimal solution guaranteed

### Performance Considerations
- JavaScript: Fast greedy approach, suitable for browser
- Python: Uses CBC solver for exact optimization
- Both respect equipment slot limits and level constraints
