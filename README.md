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

The **ZQM Labs scavenger-hunt organizer toolkit** helps a host prepare and run a location-based game in a school, workplace, neighborhood, or community venue. It covers setup checklists, QR-sign generation and printing, event-day troubleshooting, and FAQs. Organizers should verify venue permissions, supervision, weather plans, accessibility, and the specific kit's requirements before an event.

## Repository role and status

**Status:** Active, public. Organizer ("Lab Assistant") operations documentation for ZQM Labs games.

**What this repository is:** The day-of operations kit for organizers: the setup checklist, QR sign generation guidance, print specs, day-of troubleshooting guide, and FAQ (`guides/`, `faq.md`).

**What it contributes:** It is the operational half of running an event — everything an organizer needs between receiving a kit and event night. Game content itself lives in quest-packs; field failures and adaptations found using this toolkit are recorded in playtests.

## Start here

1. [`guides/setup-checklist.md`](guides/setup-checklist.md) — the
   week-by-week countdown: what to do 2 weeks out, 1 week out, the day
   before, and day-of.
2. [`guides/qr-generator.md`](guides/qr-generator.md) — generate, test,
   and print QR signs for your kit (uses the in-repo
   [`qr-kit/`](qr-kit/) generator).
3. [`guides/print-specs.md`](guides/print-specs.md) — how to print the
   QR signs so they scan in sunlight, rain, and low light.
4. [`guides/day-of-troubleshooting.md`](guides/day-of-troubleshooting.md)
   — QR won't scan, GPS drift, ties, rain plan. Read once before the
   event; keep on your phone during it.
5. [`faq.md`](faq.md) — the questions organizers actually ask.

## Installation

No build step: the toolkit is Markdown guides, templates, and small Python
scripts. Clone the repo and work from its root:

```bash
git clone https://github.com/ZQM-Labs/organizer-toolkit.git
cd organizer-toolkit
```

To run the documentation checks locally (Python 3, no extra dependencies):

```bash
python scripts/check_docs.py
```

## The 60-second version

You get a kit: 6 QR signs + a start poster, a placement map, an answer key,
and
a link players open on their phones (no app). You print the signs, place them,
pick a scare level on the Dial (Cozy / Spooky / After Dark /
Overdrive), and the game runs itself. Every kit is the same generic kit — no setup call, no customized stories or puzzles.

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

- [quest-player](https://github.com/ZQM-Labs/quest-player) — the player PWA
- quest-analytics — team analytics + tracking backend (private repo)
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

## Usage

Work through the setup checklist before your event, print your materials
using the print specs, and keep the day-of troubleshooting guide handy
while the game runs. Start with [Start here](#start-here) if this is your
first event.
