<!-- markdownlint-disable MD033 MD012 -->

# Lab Assistant's Toolkit — ZQM Labs

<!-- ZQM-START -->
<!-- markdownlint-disable MD033 -->
<p align="center">
  <strong>ZQM Labs — Z's Quests & Mischief</strong><br>
  <a href="https://zqmlabs.com">zqmlabs.com</a> •
  <a href="https://github.com/ZQM-Labs">GitHub</a>
</p>
<!-- markdownlint-enable MD033 -->
<!-- ZQM-END -->

Everything an organizer ("Lab Assistant") needs to run a
**ZQM Labs — Z's Quests & Mischief** scavenger-hunt game in their own
space. *Games, gear & a little mischief.*

## Start here

1. [`guides/setup-checklist.md`](guides/setup-checklist.md) — the
   week-by-week countdown: what to do 2 weeks out, 1 week out, the day
   before, and day-of.
2. [`guides/qr-generator.md`](guides/qr-generator.md) — generate, test,
   and print QR signs for your kit (uses the lantern-kit generator).
3. [`guides/print-specs.md`](guides/print-specs.md) — how to print the
   QR signs so they scan in sunlight, rain, and low light.
4. [`guides/day-of-troubleshooting.md`](guides/day-of-troubleshooting.md)
   — QR won't scan, GPS drift, ties, rain plan. Read once before the
   event; keep on your phone during it.
5. [`faq.md`](faq.md) — the questions organizers actually ask.

## The 60-second version

You get a kit: 6 QR signs + a start poster, a placement map, an answer key,
and
a link players open on their phones (no app). You print the signs, place them,
pick a scare level on the Dial (Cozy / Spooky / After Dark /
Overdrive), and the game runs itself. One setup call with us before
the event is included in every kit.

## Quest packs

Game content lives in
[ZQM-Labs/quest-packs](https://github.com/ZQM-Labs/quest-packs) —
including a **free sample quest** you can run today.

## Community-first hosting

ZQM Labs is designed around communities using shared stories to bring people
together. The current operational kit is still a location-based event format;
adapt each run to the venue, audience, access needs, and support capacity
rather than assuming every location or format is already supported.

Before hosting:

1. **Choose a safe, accessible route.** Confirm permission for every stop,
   avoid traffic hazards and inaccessible paths, and offer a non-GPS
   alternative where practical.
2. **Adapt the experience to the group.** Consider age range, language,
   cultural context, sensory needs, weather, and whether the event should be
   spooky or family-friendly.
3. **Keep participation voluntary.** Explain what location permissions the
   game uses, do not collect unnecessary personal information, and provide a
   clear way to participate without sharing a public team name.
4. **Capture feedback responsibly.** Ask participants before taking or
   publishing photos. Send playtest observations without names or identifying
   details unless participants have explicitly agreed.
5. **Report what changed.** Note venue-specific adaptations, accessibility
   barriers, technical failures, and suggestions for the next community.

The toolkit supports local hosts today. Worldwide event fulfillment,
translation coverage, and a global organizer network should not be assumed
unless separately confirmed.

Questions? <zqmcomputing@gmail.com> · <https://zqmlabs.com>

*Play more. Plan less.*

<!-- ZQM-FOOTER-START -->
<!-- markdownlint-disable MD033 -->
---

<p align="center">
  <em>Play more. Plan less.</em><br>
  <a href="https://zqmlabs.com">zqmlabs.com</a> •
  <a href="https://github.com/ZQM-Labs">ZQM Labs</a> •
  <a href="https://github.com/ZQM-Computing">ZQM Computing</a>
</p>
<!-- markdownlint-enable MD033 -->
<!-- ZQM-FOOTER-END -->

## Field-readiness gate

The checklist and print instructions are operational guidance; they do not prove that a particular route or kit has been physically validated. Before an event, record the specific edition and player version, then verify:

- Permission and safe placement for every sign; no placement requiring entry onto private property or unsafe crossing.
- QR readability from realistic approach distance, at actual print size, in expected lighting and weather.
- GPS behavior on the intended devices and route, including drift and no-fix conditions.
- The manual/observation fallback for people without GPS, location permission, or a working camera.
- A practical accessible alternative for each checkpoint and a clear stop/withdrawal option.
- Battery/network failure, offline resume, and who to contact if the game cannot continue.
- Content, answer key, route map, and print set all match the same released edition.

Record failures and adaptations in the [playtest repository](https://github.com/ZQM-Labs/playtests). Never describe a route as safe or accessible solely because the digital player works in a browser.

## Related repos

- [lantern-player](https://github.com/ZQM-Labs/lantern-player) — the player PWA
- [wisps-tracker](https://github.com/ZQM-Labs/wisps-tracker) — team tracking backend
- [quest-authoring](https://github.com/ZQM-Labs/quest-authoring) — quest pack spec, validator, and generator
- [quest-packs](https://github.com/ZQM-Labs/quest-packs) — ready-to-play quest packs
- [playtests](https://github.com/ZQM-Labs/playtests) — playtest protocol and results
- [zqmlabs-site](https://github.com/ZQM-Labs/zqmlabs-site) — the public website

## License

MIT — see [LICENSE](LICENSE).

## Validation

This repository uses GitHub Actions for continuous integration. See [CI workflow](.github/workflows/ci.yml) for details.

To validate locally:

```bash
# Run documentation checks
python scripts/check_docs.py
```
