# Host outcome metrics — offline aggregate calculator

**Status:** a local reporting aid, **not** event telemetry, a published dashboard, a revenue report, a verified booking, or a player integration.

The [November 2026 ZQM Trending Content & Strategy Brief] recommends host-facing completion and engagement metrics, zero-install acquisition, and an organizer-funded model. This tool implements only the privacy-preserving **measurement definitions**. It does not adopt case-study lift percentages from Pinterest, Starbucks, Flipkart, Alibaba or Trivago as evidence for ZQM. Those figures describe third-party products, periods and methodologies and should be independently revalidated before public use.

## Run

Python 3.11+, no packages or network required. From this repository root:

```bash
python event-kit/summarize_outcomes.py event-kit/examples/outcomes.synthetic.json
python -m unittest discover -s tests -p 'test_outcomes.py' -v
```

The bundled fixture is explicitly synthetic. **Never present its output as observed ZQM sales, share rates, retention or conversion.**

## Input: manually counted group aggregates only

The strict version-1 JSON has `schema_version: 1` and
`source_basis: "synthetic_demo"` or `"manual_host_aggregate"`.
Every other field is a nonnegative integer, capped at one million:

| Input key | Definition |
| --- | --- |
| `teams_invited` | Distinct invited teams in the host-defined cohort |
| `teams_started` | Distinct invited teams that started, counted by the host |
| `teams_completed` | Started teams completing the reviewed six-stop experience |
| `teams_sharing_offered` | Completed teams *offered an optional share opportunity* |
| `teams_shared_reported` | Those offered teams that voluntarily reported sharing; no proof of actual social distribution |
| `teams_with_timing` | Completed teams with a voluntarily recorded valid completion duration |
| `total_completion_minutes` | Sum of these durations (one through 480 minutes per timed team) |
| `qualified_host_inquiries` | Distinct organizer inquiries passing the Lab's written qualification criteria |
| `proposals_sent` | Subset of qualified inquiries receiving a scoped proposal |
| `pilots_accepted` | Subset of those proposals with a host's documented acceptance, **not** proof of payment |

## Six output metrics, with clear denominators

| Metric | Calculation |
| --- | --- |
| Team start rate | `teams_started / teams_invited` |
| Team completion rate | `teams_completed / teams_started` |
| Voluntary share response rate | `teams_shared_reported / teams_sharing_offered` |
| Mean completion duration | `total_completion_minutes / teams_with_timing` |
| Host proposal rate | `proposals_sent / qualified_host_inquiries` |
| Pilot acceptance rate | `pilots_accepted / proposals_sent` |

Percentages are reported to one decimal place. **No null or omitted denominator is treated as zero.** A share *response* is not an independently verified share, reach or new installation. A proposal or accepted pilot is not a completed checkout, collected revenue or recurring license.

### Privacy and methodological controls

The calculator accepts aggregate integers only and fails closed on unknown fields, duplicate JSON keys, non-finite values, negative values, impossible funnel relationships, nonsensical duration totals, and oversized input. Do not feed team names, IP addresses, phone numbers, GPS coordinates, exact location histories, photos, EXIF, payment identifiers, rosters, or raw event logs.

Its JSON output **does not repeat raw counts or individual information**. Rate output is withheld when the denominator is fewer than ten teams, the numerator is fewer than five, or fewer than five participants fall in the complementary category. Duration output is withheld unless at least ten completed teams have durations. These are conservative output safeguards, **not** differential privacy or proof of anonymity. Do not infer outcomes for small school groups from suppressed metrics.

Source-grade flags always read `source_verified: false` and `publishable_sales_proof: false`. Even `manual_host_aggregate` means the host entered data, not that any source is audited. Public case studies require independent provenance, permitted data use, documented sampling and consent, and review by the responsible organizer. Report uncertainty and participation limitations, and separate visitor analytics from group completions.

### Integration and release boundaries

This tool does not contact the player, API, Stripe, browsers, cameras, geolocation or social platforms. It cannot collect timestamps or track anyone. Host contacts and quote details must remain in approved private operational systems; **never commit live event data to this public repo**. A public sales funnel must not assume verified checkout until the separate fulfillment/authorization gates are green.

The existing [host event kit](README.md) supplies **planning** schedules and consent-safe observation prompts. The [quest-player](https://github.com/ZQM-Labs/quest-player) remains the source for actual PWA behavior. Do not equate planning-file generation, a GitHub merge or a PWA's service worker presence with completed, published or paid experiences.

## What to validate next

Collect an **explicitly authorized** baseline of actual anonymous host counts from a reviewed pilot, confirm the target device and offline behavior, and compare a scoped organizer inquiry flow before changing onboarding or advertising conversion rates. Any live analytics would require separate privacy, security, retention, accessibility and anti-abuse review. No tracking code is added here.
