# Tiebreakers and scoring — Wisp's Lost Lanterns

> **PUBLIC-SAFE — contains no puzzle answers.** This file may live in
> `organizer-toolkit/guides/` AND inside the private kit. The tiebreaker
> QUESTIONS and answers themselves live only in the kit-only answer key —
> this file states the procedure, never the questions.

## What the game actually scores (verified from the player code)

There is NO points total in the player. A comment in the player code mentions
a portal formula (“solved × POINTS_PER_STOP”), but no `POINTS_PER_STOP`
value exists in the player code, so no points figure is quoted here — any
points table would be invented. What the player DOES implement, in
`teamScore()` for its local leaderboard, is a ranking — lower is better —
over the finale stats every run records: lanterns lit, hints used, clean
solves, elapsed minutes, wrong guesses, on-site GPS verifications.
The backend sort intent noted in the same code is simply “finished, then
hints”. The organizer ranking below follows the player's implemented order,
not an invented points system.

Definitions (player code):

- **Lanterns lit / solved:** stops whose puzzle (or fallback, or sign code)
  the team completed. Maximum 6.
- **Clean solve:** a stop solved with ZERO hints used at that stop. Using any
  hint at a stop — even hint 1 — makes that stop not clean. Hint budget is
  18 total (3 per stop × 6 stops); hints are free in the sense that the game
  never blocks on hints, but they cost ranking position.
- **Elapsed time:** whole minutes from start to finale, rounded by the player.
- **Wrong guesses:** total incorrect answers entered across all stops.
- **On-site verification:** stops where the team confirmed GPS within 30 m
  (code-only unlocks count as solved but NOT as verified).
- **Titles (player display only, not ranking):** zero hints = “Purist”; all
  stops clean = “Flawless”; all stops GPS-verified = “True Explorer”.

## Ranking order (apply in order; first difference decides)

1. **Finished beats unfinished, always.** A team with fewer than 6 lanterns
   ranks below every team with 6, regardless of hints or speed (player code:
   unfinished runs score 1,000,000,000+ and can never beat a finished run).
2. **Most lanterns lit** (among unfinished teams, this is the whole contest —
   the setup checklist's “Most solved wins”).
3. **Fewest hints used** (player weight: 1,000 per hint — the single biggest
   factor among finishers).
4. **Most clean solves** (player weight: −150 per clean solve).
5. **Fastest elapsed time** (player weight: +1 per minute).
6. **Fewest wrong guesses** (player weight: +10 per guess).
7. **Most on-site GPS verifications** (player weight: −5 per verified stop).
8. **Spoken tiebreaker** — the organizer reads the sealed tiebreaker question
   from the kit-only answer key aloud; first correct shout wins (toolkit
   troubleshooting rule). A second tiebreaker question is in the key if the
   first also ties.
9. **Co-champions.** If still tied, declare co-champions — “it's a party”
   (toolkit troubleshooting rule). Do not invent a further round.

Player formula, for organizers who have the finale stats (lower wins):

```text
score = hintsUsed × 1000 − cleanSolves × 150 + minutes + wrongGuesses × 10 − verified × 5
(unfinished team: score = 1,000,000,000 + hintsUsed × 100)
```

## Paper fallback (no finale stats available)

If the organizer is tallying on paper at the finale table and only has solved
counts and the clock (the setup checklist's finale step: “tally solved
counts”), rank by: (1) most lanterns lit, (2) fastest elapsed time,
(3) spoken tiebreaker, (4) co-champions. Say so out loud: the paper fallback
drops the hint / clean-solve / wrong-guess / verification signals the player
would have used, so a paper result and a player-leaderboard result can
differ. When the player finale stats exist, they govern.

## Worked example (ILLUSTRATIVE teams — not real results)

Four fictional finishing/unfinished teams, scored with the player formula above:

| Team | Finished | Lanterns | Hints | Clean | Minutes | Wrong guesses | Verified | Score | Rank |
|---|---|---|---|---|---|---|---|---|---|
| Maple | yes | 6 | 0 | 6 | 50 | 0 | 6 | -880 | 1 |
| Oak | yes | 6 | 2 | 5 | 38 | 3 | 6 | 1,288 | 2 |
| Birch | yes | 6 | 2 | 4 | 30 | 1 | 6 | 1,410 | 3 |
| Elm | no | 5 | 1 | 4 | 40 | 2 | 5 | 1,000,000,100 | 4 |

Reading it:

- **Maple wins** despite the slowest time (50 min): zero hints and 6 clean
  solves give 0 − 900 + 50 + 0 − 30 = **−880**, the lowest score.
- **Oak beats Birch** despite being 8 minutes slower: both used 2 hints, but
  Oak has 5 clean solves to Birch's 4 (2,000 − 750 + 38 + 30 − 30 = **1,288**
  vs 2,000 − 600 + 30 + 10 − 30 = **1,410**). Clean solves outrank speed.
- **Elm ranks last** despite 5 lanterns and a decent time: unfinished runs
  score 1,000,000,100 and can never beat a finisher.
- If Maple and Oak had tied on every stat above, the organizer would read the
  sealed tiebreaker from the answer key (first correct shout), then the
  second tiebreaker, then declare co-champions.

## Disputes

- The answer key governs what counts as correct; the player already enforces
  it case- and punctuation-insensitively, so spelling-case disputes are not
  disputes — accept them.
- A team that solved on paper after a lost/damaged sign (toolkit rule) counts
  that stop as solved; record it in the tally by hand.
- A team that is way behind or lost: hints are free, and the organizer may
  walk them to the next stop. “Fun beats fairness” (toolkit rule) — but a
  walked team still keeps whatever hints/solves the tally shows; do not
  retroactively clean a hinted solve.
