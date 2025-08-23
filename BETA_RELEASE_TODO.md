# Boneglaive Beta Release Todo

This document tracks the tasks needed to prepare Boneglaive for beta release on itch.io.

## 🎯 High Priority (Must Complete)

### [ ] 1. Create standalone executable with PyInstaller
- **Goal**: Package game for easy installation on Windows and Linux
- **Tasks**:
  - Install PyInstaller: `pip install pyinstaller`
  - Create Windows executable: `pyinstaller --onefile boneglaive/main.py`
  - Create Linux executable (if needed)
  - Test executables on target platforms
  - Include `requirements.txt` and launcher scripts in distribution

### [ ] 2. Test complete gameplay loop
- **Goal**: Verify win/lose conditions work properly
- **Tasks**:
  - Play full VS AI game to completion
  - Play full Local Multiplayer game to completion
  - Verify game ends correctly when all enemy units defeated
  - Test what happens when player loses
  - Ensure proper game state transitions

### [ ] 3. Write basic tutorial or improved README
- **Goal**: Help new players understand how to play
- **Tasks**:
  - Create basic "How to Play" guide
  - Document game controls (movement, combat, skills)
  - Explain win conditions and game objectives
  - Add unit overview with roles/capabilities
  - Include installation instructions

### [ ] 4. Take screenshots for itch.io page
- **Goal**: Professional presentation on itch.io
- **Tasks**:
  - Screenshot of main menu
  - Screenshot of gameplay (units on battlefield)
  - Screenshot of unit help pages
  - Screenshot of settings menu
  - Screenshot showing different maps

## 🔄 Medium Priority (Should Complete)

### [ ] 5. Test and verify AI difficulty levels
- **Goal**: Ensure AI provides appropriate challenge
- **Tasks**:
  - Test "easy" difficulty - should be beatable for new players
  - Test "medium" difficulty - balanced challenge
  - Test "hard" difficulty - challenging but fair
  - Verify AI difficulty actually changes behavior

### [ ] 6. Create itch.io page description and game details
- **Goal**: Compelling game description for potential players
- **Tasks**:
  - Write engaging game summary
  - List key features (tactical combat, 8 unit types, multiple maps)
  - Describe target audience
  - Set appropriate tags (strategy, turn-based, tactical)
  - Choose appropriate content rating

### [ ] 7. Test cross-platform compatibility on actual Windows system
- **Goal**: Verify Windows compatibility works in practice
- **Tasks**:
  - Test on actual Windows machine
  - Verify `windows-curses` installation works
  - Test all game features on Windows
  - Verify launcher scripts work correctly

### [ ] 8. Verify all game modes work correctly
- **Goal**: Ensure both game modes are functional
- **Tasks**:
  - Test VS AI mode thoroughly
  - Test Local Multiplayer mode thoroughly
  - Verify setup phase works in both modes
  - Test unit recruitment system

## 🎨 Low Priority (Nice to Have)

### [ ] 9. Test all maps and ensure balanced gameplay
- **Goal**: Verify all maps provide good tactical experiences
- **Tasks**:
  - Play games on "The Lime Foyer"
  - Play games on "Stained Stones" 
  - Play games on "Edge Case"
  - Ensure maps offer different tactical challenges
  - Verify no obvious balance issues

### [ ] 10. Polish UI messaging and error handling for release
- **Goal**: Professional user experience
- **Tasks**:
  - Review all error messages for clarity
  - Ensure consistent terminology throughout
  - Test edge cases and error conditions
  - Polish help text and instructions

## 📋 Beta Release Strategy

**Target**: Text-based tactical combat game beta
**Platform**: itch.io
**Audience**: Strategy game enthusiasts, tactical combat fans
**Scope**: Core gameplay without audio/graphics assets

## 📝 Notes

- Beta version will not include sound or sprite assets
- Focus on solid core gameplay and easy installation
- Professional presentation is key for itch.io success
- Cross-platform compatibility is a major selling point

## ✅ Completed Tasks

(Move completed tasks here as they are finished)

---

**Last Updated**: $(date)
**Next Review**: Check progress weekly