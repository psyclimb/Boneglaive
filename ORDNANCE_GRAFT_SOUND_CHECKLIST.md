# ORDNANCE GRAFT — Sound Checklist

**17 sound files to make.** Drop each one (as `<name>.ogg`, or `.wav`) into
`sounds/skills/` and it plays automatically — no code changes. Missing files are skipped,
so add them one at a time.

- **44.1 kHz** OGG, please (96 kHz silently breaks in-game). Stereo, `-q:a 6` is fine.
- **Length** = how long the on-screen beat lasts. Match it or go a touch shorter; much
  longer overlaps the next beat.
- Timings are pulled straight from `boneglaive/graphical/animations/ordnance_graft.py`.

---

## The list

| # | File (`sounds/skills/…`) | Length | What it is |
|---|---|---|---|
| **Basic attack — the GRAFT (linstock pole, 0.45s total)** ||||
| 1 | `ordnance_attack_swing.ogg`  | ~0.18s | Heavy wooden whoosh — the pole sweeps in. |
| 2 | `ordnance_attack_impact.ogg` | ~0.27s | Gunmetal head cracks into the body — blunt metal thud + spark. |
| **Basic attack — the QUADCOPTER drone (tracer shot, 0.40s total)** ||||
| 3 | `ordnance_drone_attack.ogg`  | ~0.16s | Rotor buzz + light tracer report — drone fires. |
| 4 | `ordnance_drone_impact.ogg`  | ~0.22s | Small spark hit on the target (no bomb). |
| **Inoculant — the GRAFT (melee graft, ~1.18s total; the bomb now burrows + arms)** ||||
| 5 | `inoculant_swing.ogg`   | ~0.24s | Sharp whoosh + ember crackle — pole winds back and sweeps. |
| 6 | `inoculant_strike.ogg`  | ~0.12s | The hit — bomb-tipped staff connects, bomb sits proud. A short meaty metal thunk. |
| 7 | `inoculant_burrow.ogg`  | ~0.45s | The bomb screws/augers DOWN under the skin — a wet grinding bore as the wound closes over it. |
| 8 | `inoculant_arm.ogg`     | ~0.32s | It wakes up — three soft amber pulses / a rising electronic arm-up tick. |
| **Inoculant — the QUADCOPTER drone (fires a bomb round, ~1.20s total)** ||||
| 9 | `drone_inoculant_fire.ogg`   | ~0.22s | Pneumatic muzzle pop over rotor buzz — bomb round launches. |
| 10 | `drone_inoculant_graft.ogg` | ~0.5s | Sharp impact + grinding graft hiss — the round drills in, settles, and arms. (Covers the drone's whole graft-in; it does NOT use the graft's burrow/arm sounds.) |
| **Skyhook — drone-cable extraction + slam (~0.95s; graft-ins run on to ~2.0s, silent)** ||||
| 11 | `skyhook_launch.ogg`  | ~0.17s (tail to ~0.5s OK) | Winch crack + whoosh — cable yanks him up off the ground. |
| 12 | `skyhook_land.ogg`   | ~0.25s | Heavy ground slam + dust + shockwave — he drops in. Also covers the bombs grafting into the enemies around him (those graft-ins make no sound of their own). |
| **Harvest — field-wide detonation, the showpiece** ||||
| 13 | `harvest_ignite.ogg`   | ~0.18s | Rising sizzling whine — fuses catch, glow builds before the barrage. |
| 14 | `harvest_detonate.ogg` | ~0.70s (per blast) | One bomb going off. **Plays once per detonating bomb** — see note below. (Chain Reaction's chained seed is silent — this blast covers it.) |
| **Cast stingers (optional — play at t=0 the instant the skill fires)** ||||
| 15 | `inoculant.ogg`  | very short | "Skill is happening" stinger for Inoculant (graft AND drone share it). |
| 16 | `skyhook.ogg`    | very short | The "call the drone for extraction" signal. |
| 17 | `harvest.ogg`    | very short | The "thumb the firing key" trigger. |

---

## Three things worth knowing

**The graft-in sound fires once per CAST, not per bomb.** `inoculant_burrow`/`inoculant_arm`
play exactly once even when several bombs seat at once — Booster Charge (2 bombs), Skyhook
(every adjacent enemy) and Chain Reaction all show extra graft-in *visuals* but make no extra
graft sound (their slam / detonation / strike already carries it). So you never get N
overlapping burrow squelches — author these two as single clean sounds.

**Harvest is a chain, not one boom.** `harvest_detonate` plays **once for every bomb that
detonates** (1 to N copies), each staggered up to ~0.1s apart, all starting ~0.18s in.
Make it **punchy and short** so overlapping copies stack into a satisfying barrage rather
than turning to mud. `harvest_ignite` fires once, right as the first bomb goes — think of
it as the lead-in crackle under the first blast, not a separate earlier beat.

**Cast stingers (15–17) are optional.** They fire at the exact same instant as the skill's
first beat (swing/launch/ignite), so they can feel doubled. If a cast sound muddies the
first hit, just don't make the file — the per-beat sounds (5–8, 9–10, 11–14) carry it fine.

---

## Files by priority (if you want an order to record in)

1. **Core hits first** (most-heard): `ordnance_attack_swing`/`_impact`,
   `inoculant_swing`/`_strike`, `harvest_detonate`, `harvest_ignite`.
2. **The graft-in textures** (the new weird beats): `inoculant_burrow`, `inoculant_arm`.
3. **The drone**: `ordnance_drone_attack`/`_impact`, `drone_inoculant_fire`/`_graft`.
4. **Skyhook**: `skyhook_launch`, `skyhook_land`.
5. **Optional stingers** (skip if they double up): `inoculant`, `skyhook`, `harvest`.

> If the animation phase constants in `ordnance_graft.py` ever change, the lengths above
> should be re-checked against the file.
