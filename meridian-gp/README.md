# Meridian Grand Prix

A scroll-driven Formula 1 night race in **one hand-written HTML file** — no
frameworks, no build step. A design study: fictional event, fictional teams,
fictional data.

Open `index.html` in any modern browser (or serve the folder statically).

## What's inside

- **The race** — a canvas-rendered night circuit scrubbed by scroll: five start
  lights, launch, DRS down the straight, a 5.4 G braking zone, a tunnel trailing
  titanium sparks, a 2.14 s pit stop, and the flag. Broadcast HUD (speed, gear,
  DRS, sectors) plus a live circuit minimap. Rendered at device resolution with
  a smoothed scroll scrub, so it plays like video but never blurs.
- **The machine** — the same car geometry drawn once and shared between the
  canvas painter (`Path2D`) and an SVG inspector. Tap any hotspot to open a
  component; the drawing resolves with zoom depth: callouts → fasteners and
  dimension lines → carbon weave. The rear-wing view has a working DRS toggle.
- **Telemetry** — a speed-profile generator (forward acceleration pass vs
  backward 5 g braking pass over 14 corners) drives the speed trace; lap times
  and tyre models are seeded and deterministic. Charts are plain SVG with a
  crosshair tooltip, keyboard navigation, and a raw data-table twin per chart.
- **Timing** — championship standings and pit-stop tables, tabular numerals.

## Design notes

- Committed single world: a street circuit at 21:00 — deep blue-black night,
  floodlight gold (`#e8b84b`), black-and-gold livery for the fictional Auriga
  team (Auriga: the Charioteer).
- Type: Big Shoulders Display (headlines), Archivo (text), IBM Plex Mono
  (telemetry).
- Chart colors are validated for color-vision safety and contrast against the
  card surface; tyre compounds use a single ordered gold ramp
  (`#ffd98a → #cf9a2c → #8a5a10`), soft → hard.
- Respects `prefers-reduced-motion` (no particles or smoothing; scroll still
  scrubs), keyboard focus styles throughout, table equivalents for every chart.
