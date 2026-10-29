# Write-up: AI Proposal Triage

## Assumptions
- Sample summaries stand in for text extracted from PDFs.
- "Named" lead or project manager is taken at face value; the reviewer still sees the quote.
- "Last 5 years" means installs from 2021 onward.
- A missing required fact (price, timeline) is a question for a human, not a zero.

## Result on the sample set

| Rank| Proposal| Score |                       Note                      |
|-----|---------|-------|-------------------------------------------------|
|  1  |    A    |  79.3 | Best overall; full marks on experience and team |
|  2  |    E    |  65.9 | Best warranty; fewer qualifying installs        |
|     |    B    |       | **Ineligible**: licence not held by bidder      |
|     |    C    |       | **Flagged**: embedded instruction to reviewers  |
|     |    D    |       | **Flagged**: no completion time given           |

---

## 1. AI vs. rules
**AI (two places):** (a) *Extraction*: turning free-form PDFs into structured facts, each with a
verbatim quote and page; (b) a one-line plain-English reason, written only from numbers code has
already computed.
**Plain code:** file checks, injection pre-screen, schema and quote validation, mandatory gates,
completeness checks, every score formula, ranking, tie-breaks and logging.
**Why there:** AI is good at interpreting language, so it reads. Rank must be repeatable and
defensible, so code decides. No model output is ever a number that moves a proposal's rank.
That also makes re-weighting free and instant.

## 2. Consistency and explainability
- Extraction runs at temperature 0 with pinned model and prompt versions, strict JSON, and **one
  proposal per call** (adding bidder F cannot change A's facts).
- Results are cached by `hash(text + prompt version + model version + criteria version)`. Ranking the
  same set twice reads the cache and gives an identical result. A fresh re-extraction can wobble
  slightly, so low-confidence fields are extracted twice and any disagreement flags the item.
- Scores are **absolute**, not relative: price is measured against the budget ceiling, not against
  other bids, so a proposal's score never changes because another bid arrived.
- Ties break by experience points, then lower price, then go to a human.
- The reviewer sees one row per criterion: fact, evidence quote and page, formula, points.
  Example for A, experience: 14 installs, capped at 12, gives 30/30.

## 3. Human in the loop
Checkpoints:
1. **Flag queue**: injection attempts, missing facts, conditional claims, low confidence, failed validation.
2. **Ineligible list** must be confirmed; a reviewer can reinstate with a written reason.
3. **Fact override**: reviewers can correct any extracted value; code recomputes and the original is kept.
4. **Rank override**: allowed only with a mandatory justification, shown beside the computed rank.
5. **Award**: always a human; the tool never awards.

**Audit log (append-only):** user and timestamp, file hashes, criteria version, model and prompt
versions, raw model output, validator results, flags, per-criterion points, final rank, every
override (before, after, reason), and the final decision.

## 4. Changing criteria
Criteria are versioned records. Every scoring run pins a `criteria_version`. An edit creates a new
version and old results are never overwritten; they are labelled "scored under v1" with a stale banner.
- **Weights or formula parameters only:** re-score in code from stored facts (seconds, no AI cost).
- **Criterion wording, threshold or a new criterion:** re-extract *only* that criterion.
- **Mandatory criterion changed:** re-run the gate; eligibility may flip.

Weights must sum to 100 (validated on save). A ranking never mixes versions. The reviewer sees a
before/after rank diff and must confirm adopting the new run. Admins can also be required to "open a
new round" once scoring has started.

## 5. Risks and safeguards
- **Wrong extraction:** the validator checks every quote appears *verbatim* in the source; a second
  "auditor" call checks that the quote supports the value; confidence and ambiguity fields route to review.
- **Made-up facts:** absent means `null`, never a guess; an invented quote fails validation and the
  field is rejected.
- **Manipulation:** C contains text claiming pre-approval and demanding first place. Text is treated as
  untrusted data (delimited, instruction-hardened prompt, regex pre-screen). It is quoted, flagged and
  excluded from ranking pending review, and may be worth escalating as a bidder-integrity issue. Even a
  successful injection could not raise a score, because the model never scores.
- **Ambiguous compliance:** B has the lowest price, but a licence "to be confirmed after award" is not a
  licence held, so it fails the mandatory gate. Cheapest does not override pass/fail. D gives no
  timeline, so the 16-week limit cannot be verified. It is flagged, not zeroed. Provisionally it scores
  62.7 and would rank 2nd if the bidder confirmed 14 weeks or fewer, which is why a human should ask.
- **Bias:** scoring uses only the criteria fields. Bidder names are replaced by IDs during extraction,
  and outcomes should be monitored by bidder size over time.
- **Cost:** one call per proposal, cached; re-weighting is free; small model for extraction, larger
  model only for low-confidence audits; page and size caps with spend alerts.
- **Privacy:** PDFs may hold personal data; use no-training API terms and a retention limit.
- **Drift:** pinned versions plus a golden regression test (these five samples must keep producing this ranking).
- **Over-trust:** the UI labels output "advisory" and shows flags first.
