# ORDNANCE GRAFT — Sound Checklist

**15 sound files to make.** Drop each one (as `<name>.ogg`, or `.wav`) into
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
| **Inoculant — the GRAFT (melee graft, 0.6s total)** ||||
| 5 | `inoculant_swing.ogg`   | ~0.24s | Sharp whoosh + ember crackle — pole winds back and sweeps. |
| 6 | `inoculant_strike.ogg`  | ~0.36s | Meaty thunk — spiked bomb driven in and embeds, then settles. |
| **Inoculant — the QUADCOPTER drone (fires a bomb round, 0.6s total)** ||||
| 7 | `drone_inoculant_fire.ogg`   | ~0.22s | Pneumatic muzzle pop over rotor buzz — bomb round launches. |
| 8 | `drone_inoculant_graft.ogg`  | ~0.34s | Sharp impact + graft hiss — bomb embeds in the target. |
| **Skyhook — drone-cable extraction + slam (0.95s total)** ||||
| 9 | `skyhook_launch.ogg`  | ~0.17s (tail to ~0.5s OK) | Winch crack + whoosh — cable yanks him up off the ground. |
| 10 | `skyhook_land.ogg`   | ~0.25s | Heavy ground slam + dust + shockwave — he drops in. |
| **Harvest — field-wide detonation, the showpiece** ||||
| 11 | `harvest_ignite.ogg`   | ~0.18s | Rising sizzling whine — fuses catch, glow builds before the barrage. |
| 12 | `harvest_detonate.ogg` | ~0.70s (per blast) | One bomb going off. **Plays once per detonating bomb** — see note below. |
| **Cast stingers (optional — play at t=0 the instant the skill fires)** ||||
| 13 | `inoculant.ogg`  | very short | "Skill is happening" stinger for Inoculant (graft AND drone share it). |
| 14 | `skyhook.ogg`    | very short | The "call the drone for extraction" signal. |
| 15 | `harvest.ogg`    | very short | The "thumb the firing key" trigger. |

---

## Two things worth knowing

**Harvest is a chain, not one boom.** `harvest_detonate` plays **once for every bomb that
detonates** (1 to N copies), each staggered up to ~0.1s apart, all starting ~0.18s in.
Make it **punchy and short** so overlapping copies stack into a satisfying barrage rather
than turning to mud. `harvest_ignite` fires once, right as the first bomb goes — think of
it as the lead-in crackle under the first blast, not a separate earlier beat.

**Cast stingers (13–15) are optional.** They fire at the exact same instant as the skill's
first beat (swing/launch/ignite), so they can feel doubled. If a cast sound muddies the
first hit, just don't make the file — the per-beat sounds (5–6, 9, 11–12) carry it fine.

---

## Files by priority (if you want an order to record in)

1. **Core hits first** (most-heard): `ordnance_attack_swing`/`_impact`,
   `inoculant_swing`/`_strike`, `harvest_detonate`, `harvest_ignite`.
2. **The drone**: `ordnance_drone_attack`/`_impact`, `drone_inoculant_fire`/`_graft`.
3. **Skyhook**: `skyhook_launch`, `skyhook_land`.
4. **Optional stingers** (skip if they double up): `inoculant`, `skyhook`, `harvest`.

> If the animation phase constants in `ordnance_graft.py` ever change, the lengths above
> should be re-checked against the file.
