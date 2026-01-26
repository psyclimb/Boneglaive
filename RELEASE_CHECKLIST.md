# Boneglaive - itch.io Release Checklist

**Target Platform**: itch.io
**Future Platform**: Steam (post-itch.io launch)
**Date Created**: 2026-01-26

---

## Pre-Release Testing

### [ ] Graphical Version - Full Playthrough Testing
- [ ] Test vs AI mode - complete game from start to win condition
- [ ] Test local multiplayer mode - complete game with 2 players
- [ ] Test all units and their skills work correctly
- [ ] Test GP scoring system (10 GP to win)
- [ ] Test respawn system (3-turn timer, spawn selection)
- [ ] Test game-over/victory screens
- [ ] Test main menu navigation
- [ ] Test map selection
- [ ] Test settings persistence (config.json)
- [ ] Test all animations play correctly
- [ ] Test combat log scrolling and messages
- [ ] Test unit selection and movement
- [ ] Test attack targeting
- [ ] Test skill targeting for all skill types
- [ ] Test status effect icons appear/disappear correctly
- [ ] Test on different screen resolutions (1920x1080, 1366x768, 2560x1440)

### [ ] ASCII Version - Full Playthrough Testing
- [ ] Test vs AI mode - complete game from start to win
- [ ] Test local multiplayer mode
- [ ] Test LAN host/client modes
- [ ] Test respawn menu (press 'r')
- [ ] Test message log (press 'l' and 'L')
- [ ] Test all keyboard controls
- [ ] Test terminal resizing handling
- [ ] Test on different terminal emulators (if possible)

### [ ] Critical Bug Fixes
- [x] MANDIBLE FOREMAN Expedite desync bug (sprite position not syncing to clickable location) - FIXED 2026-01-26
- [ ] Fix any game-breaking bugs found during testing
- [ ] Fix any crashes or freezes
- [ ] Fix any softlocks (situations where game can't progress)
- [ ] Fix any major visual glitches
- [ ] Ensure game can be quit properly from all screens

---

## Polish & User Experience

### [ ] In-Game Tutorial/Help
- [ ] Create tutorial screen explaining GP system
- [ ] Create tutorial screen explaining controls
- [ ] Create tutorial screen explaining unit selection
- [ ] Create tutorial screen explaining skills
- [ ] Add help button/screen accessible from main menu
- [ ] Consider first-time player experience walkthrough

### [ ] Victory/Defeat Screens
- [ ] Implement victory screen showing winner
- [ ] Display final GP score
- [ ] Show game statistics (turns played, kills, etc.)
- [ ] Add "Return to Menu" button
- [ ] Add "Play Again" button
- [ ] Add transition animations

### [ ] Main Menu Polish
- [ ] Verify all menu options work
- [ ] Add version number display
- [ ] Add credits/about section
- [ ] Ensure clean quit to desktop
- [ ] Test keyboard and mouse navigation

### [ ] Audio (Optional but Recommended)
- [ ] Add background music (or decision to release without)
- [ ] Add sound effects for attacks (or decision to release without)
- [ ] Add sound effects for menu interactions (or decision to release without)
- [ ] Add volume controls if audio is included

---

## Packaging & Distribution

### [ ] Code Cleanup
- [ ] Remove debug print statements
- [ ] Remove unused imports
- [ ] Remove commented-out code
- [ ] Remove development-only files from distribution
- [ ] Verify all file paths are relative (not hardcoded absolute paths)

### [ ] Asset Check
- [ ] Verify all graphics files are included
- [ ] Verify all font files are included
- [ ] Verify all sound files are included (if audio added)
- [ ] Check file sizes are reasonable
- [ ] Verify all assets are properly licensed or original

### [ ] Dependencies
- [ ] Create requirements.txt for graphical version
- [ ] Document Python version requirement (3.8+)
- [ ] Test with minimal Python installation
- [ ] Verify pygame version compatibility

### [ ] Build Executables (PyInstaller or cx_Freeze)

#### Windows Build
- [ ] Install PyInstaller: `pip install pyinstaller`
- [ ] Create build spec for graphical version
- [ ] Create build spec for ASCII version (if distributing)
- [ ] Build Windows executable
- [ ] Test executable on clean Windows machine (no Python installed)
- [ ] Verify all assets are bundled correctly
- [ ] Check executable size (compress if too large)
- [ ] Test on Windows 10 and Windows 11 if possible

#### Linux Build
- [ ] Create Linux executable or AppImage
- [ ] Test on Ubuntu/Debian
- [ ] Test on Arch/Fedora if possible
- [ ] Verify dependencies are bundled or documented

#### macOS Build (if targeting)
- [ ] Create macOS .app bundle
- [ ] Test on macOS (Intel and M1/M2 if possible)
- [ ] Handle code signing (or note as unsigned)

### [ ] Distribution Package
- [ ] Create game folder structure
- [ ] Include README.txt with installation instructions
- [ ] Include LICENSE.txt
- [ ] Include CONTROLS.txt or control reference
- [ ] Create ZIP files for each platform
- [ ] Test unzipping and running from ZIP

---

## itch.io Page Setup

### [ ] Game Page Content
- [ ] Write compelling game description
- [ ] List key features (GP system, unit variety, game modes)
- [ ] Specify platform support (Windows/Linux/macOS)
- [ ] List system requirements
- [ ] Document controls clearly
- [ ] Add installation instructions

### [ ] Screenshots & Media
- [ ] Capture 5-10 high-quality screenshots (graphical version)
- [ ] Include screenshots showing:
  - Main menu
  - Combat with multiple units
  - Skill effects and animations
  - Victory screen
  - Different maps
- [ ] Capture 1-2 screenshots of ASCII version (optional, as alternate)
- [ ] Create cover image (630x500 or 315x250)
- [ ] Create banner image if desired
- [ ] Record gameplay video/GIF (30-60 seconds recommended)

### [ ] Game Metadata
- [ ] Choose appropriate genre tags (Strategy, Turn-Based, Tactical)
- [ ] Choose appropriate theme tags
- [ ] Set multiplayer tags (Local Multiplayer)
- [ ] Set price (free or paid - recommend free for initial launch)
- [ ] Set release status (Released vs Early Access)
- [ ] Set content rating
- [ ] Add accessibility features (if any)

### [ ] Upload Files
- [ ] Upload Windows build
- [ ] Upload Linux build
- [ ] Upload macOS build (if created)
- [ ] Mark executables as executable files
- [ ] Set proper platform flags
- [ ] Test download from itch.io

### [ ] Pre-Launch Check
- [ ] Preview game page
- [ ] Verify all links work
- [ ] Verify all images display correctly
- [ ] Verify download buttons work
- [ ] Read through all text for typos
- [ ] Check formatting and layout

---

## Launch Day

### [ ] Publishing
- [ ] Set game to "Published" status
- [ ] Share link on social media (if applicable)
- [ ] Post in relevant communities (with permission)
- [ ] Monitor comments and feedback
- [ ] Respond to questions promptly

### [ ] Post-Launch Monitoring
- [ ] Check for bug reports
- [ ] Monitor download statistics
- [ ] Collect player feedback
- [ ] Plan first patch if critical bugs found

---

## Future - Steam Release Preparation

### [ ] Steam-Specific Requirements (Do After itch.io Launch)
- [ ] Steam SDK integration
- [ ] Steam achievements system
- [ ] Steam cloud saves
- [ ] Steam overlay support
- [ ] Trading cards (optional)
- [ ] Workshop support for mods (optional)
- [ ] Controller support (recommended for Steam)
- [ ] Steam-specific build testing
- [ ] Create store page assets (capsule images, library graphics)
- [ ] Write store description
- [ ] Set up Steamworks account
- [ ] Pay Steam Direct fee ($100)
- [ ] Submit for Steam review

---

## Notes

**Current Status**: Documentation cleanup complete (2026-01-26)

**Priority Order**:
1. Testing (catch critical bugs first)
2. Victory/defeat screens (essential for game loop)
3. Tutorial/help system (essential for new players)
4. Packaging and builds
5. itch.io page setup
6. Launch

**Estimated Timeline**:
- Testing & Bug Fixes: 3-5 days
- Polish (victory screens, tutorial): 2-3 days
- Packaging & Builds: 2-3 days
- itch.io Page Setup: 1 day
- **Total: ~8-12 days to launch**

**Open Questions**:
- Include audio or release without it?
- Distribute ASCII version or graphical only?
- Free or paid on itch.io? (Recommend free initially)
- Target all platforms or start with one?
