# ORDNANCE GRAFT — Sound File Reference

All sound files for the ORDNANCE GRAFT and its QUADCOPTER drone. **Drop a matching
`.ogg` (or `.wav`) into `sounds/skills/` and it plays automatically** — no code changes needed.
Missing files are silently skipped, so you can add them one at a time.

- **Filename** = the `.ogg` to create (lives in `sounds/skills/<name>.ogg`).
- **Fires at** = the moment in the animation the sound is triggered (seconds from the
  start of that animation).
- **Event length** = how long the matching on-screen beat lasts. Author the sound to fit
  this window (a sound a little shorter is fine; much longer will overlap the next beat).

All durations are taken directly from the animation timings in
`boneglaive/graphical/animations/ordnance_graft.py`.

---

## Cast sounds (play once at the very start of the skill)

These are the `SKILL_SOUNDS` entries — the AnimationFactory plays them the instant the
skill animation is created (t = 0). Short "the skill is happening" stingers.

| Filename | Skill | Fires at | Event length | Notes |
|---|---|---|---|---|
| `inoculant.ogg` | Inoculant (cast) | 0.00s | ~0.6s (whole anim) | Plays for BOTH the graft's and the drone's Inoculant (same skill name). Keep it short — the per-beat sounds below carry the detail. |
| `skyhook.ogg` | Skyhook (cast) | 0.00s | ~0.95s (whole anim) | The "call the drone for extraction" signal. |
| `harvest.ogg` | Harvest (cast) | 0.00s | varies (whole anim) | The "thumb the firing key" trigger. |

> Optional: if a cast sound feels doubled with the first phase beat below (they fire ~1
> frame apart), you can leave the `.ogg` out and rely on the phase sounds alone.

---

## ORDNANCE GRAFT — basic attack (linstock pole-strike)
`OrdnanceGraftLinstockAttack` · total animation 0.45s

| Filename | Fires at | Event length | What it covers |
|---|---|---|---|
| `ordnance_attack_swing.ogg` | 0.00s | ~0.18s | Linstock sweeps through its arc toward the target — heavy wooden whoosh. |
| `ordnance_attack_impact.ogg` | 0.18s | ~0.27s (0.18→0.45) | Gunmetal head cracks into the target — blunt metal-on-body thud + spark. |

## ORDNANCE GRAFT — Inoculant (graft melee graft)
`InoculantAnimation` · WINDUP 0.12s · STRIKE 0.24s · total 0.6s

| Filename | Fires at | Event length | What it covers |
|---|---|---|---|
| `inoculant_swing.ogg` | 0.00s | ~0.24s | Linstock winds back and sweeps in — sharp whoosh with an ember crackle. |
| `inoculant_strike.ogg` | 0.24s | ~0.36s (0.24→0.6) | Spiked bomb driven into the body — meaty thunk + metallic embed, then it settles. |

## ORDNANCE GRAFT — Skyhook (drone-cable extraction + arrival slam)
`SkyhookAnimationController` · YANK 0→0.17s · CARRY 0.17→0.70s · DROP/SLAM 0.70→0.95s

| Filename | Fires at | Event length | What it covers |
|---|---|---|---|
| `skyhook_launch.ogg` | 0.00s | ~0.17s (the yank; lift continues to ~0.70s) | Cable snaps taut and yanks him up — winch crack + sudden whoosh of lift. A longer "being hauled" tail up to ~0.5s is fine. |
| `skyhook_land.ogg` | ~0.70s | ~0.25s (0.70→0.95) | Dropped from the cable into an arrival slam — heavy ground impact + dust + shockwave. |

## ORDNANCE GRAFT — Harvest (field-wide detonation, the showpiece)
`HarvestAnimation` · ignite glow ~0.18s · each blast fireball lives 0.70s · blasts staggered ~0.10s apart

| Filename | Fires at | Event length | What it covers |
|---|---|---|---|
| `harvest_ignite.ogg` | 0.00s | ~0.18s | Fuses catch field-wide, warm-up glow building — rising sizzling whine before the barrage. |
| `harvest_detonate.ogg` | ~0.18s, then once per bomb | ~0.70s per blast | Each fused bomb goes off. **Plays once per detonating bomb** (1–N times, staggered ~0.1s), so it reads as a chain/barrage. Keep it punchy so overlapping copies layer well. |

---

## QUADCOPTER (drone) — basic attack (tracer shot)
`OrdnanceDroneShotAttack` · total animation 0.40s

| Filename | Fires at | Event length | What it covers |
|---|---|---|---|
| `ordnance_drone_attack.ogg` | 0.02s | ~0.16s | Drone fires its tracer round — buzzing rotor + light report. |
| `ordnance_drone_impact.ogg` | 0.18s | ~0.22s (0.18→0.40) | Tracer round hits the target — small spark impact (no bomb). |

## QUADCOPTER (drone) — Inoculant (fires a bomb round that grafts)
`DroneInoculantAnimation` · FIRE 0.04s · HIT 0.26s · total 0.6s

| Filename | Fires at | Event length | What it covers |
|---|---|---|---|
| `drone_inoculant_fire.ogg` | 0.04s | ~0.22s (0.04→0.26) | Drone fires a bomb round — pneumatic muzzle pop over rotor buzz; round flies to target. |
| `drone_inoculant_graft.ogg` | 0.26s | ~0.34s (0.26→0.6) | Bomb round embeds in the target — sharp impact + graft hiss, then it settles in. |

---

## Quick checklist (15 files total)

Cast (3): `inoculant` · `skyhook` · `harvest`
Graft (2): `inoculant_swing` · `inoculant_strike`
Drone graft (2): `drone_inoculant_fire` · `drone_inoculant_graft`
Skyhook (2): `skyhook_launch` · `skyhook_land`
Harvest (2): `harvest_ignite` · `harvest_detonate`
Graft basic (2): `ordnance_attack_swing` · `ordnance_attack_impact`
Drone basic (2): `ordnance_drone_attack` · `ordnance_drone_impact`

> Timings reflect the animation code as of this writing. If an animation's phase constants
> change, the "fires at / event length" values here should be updated to match.
