# MATACS-TH-2026-02: AI Proposal Triage Design

**Name:** Rana Irtaza Ahmed
**Reference:** MATACS-TH-2026-02
**Time actually spent:** Approximately 1 hour 30 minutes

### Time Breakdown

|                         Task                                |      Time Spent       |
| Brief review and design planning                            |      15 minutes       |
| Writing `WRITEUP.md` and `ranking.json`                     |      30 minutes       |
| Writing `PROMPTS.md`                                        |      15 minutes       |
| Creating the process flow diagram                           |      15 minutes       |
| Developing the prototype and verifying results (`score.py`) |      15 minutes       |
| **Total**                                                   | **1 hour 30 minutes** |

---

## 1. Summary

The system uses AI only to read proposal documents, extract facts with supporting evidence quotes, and generate a one-line explanation for each proposal.

All evaluation decisions are handled by deterministic code, including mandatory eligibility checks, scoring calculations, and proposal ranking. Human reviewers examine flagged cases, verify the results, and make the final award decision.

Evaluation criteria are maintained as versioned configuration data rather than hard-coded into the application, making them easier to update and maintain.

## 2. Project Files

- [WRITEUP.md](WRITEUP.md): Answers to the five design questions.
- [PROMPTS.md](PROMPTS.md): Prompts for fact extraction, evidence auditing, and generating explanations.
- [ranking.json](ranking.json): Expected ranking of proposals A through E.
- [diagram/flow.png](diagram/flow.png): Process flow diagram illustrating the system workflow. Blue represents AI, grey represents rules, green represents human review, and orange represents flagged cases.
- [prototype/score.py](prototype/score.py): Implements deterministic eligibility checks, scoring, and ranking without requiring AI or network access.
- [prototype/criteria.json](prototype/criteria.json): Contains configurable evaluation criteria.
- [prototype/facts.json](prototype/facts.json): Contains structured proposal facts representing the output of the AI extraction stage.
- [.env.example](.env.example): Example environment configuration with placeholders only and no real API keys.

## 3. How to Run the Prototype

**Requirements:**
- Python 3.9 or later
- No additional dependencies

Run the following command from the project root directory:

```bash
python prototype/score.py
```

The script performs the eligibility checks, calculates scores, and ranks proposals according to the configured criteria.

## 4. How I Used AI Tools

I used Claude as a design collaborator, not as an answer generator. I used it to brainstorm the workflow, challenge my assumptions and draft the first version of the prompts. I then reviewed every output against the brief, edited the design myself, and checked the results by running the scoring script.

### Where I Disagreed with the AI

The first suggestion was to let the language model give each proposal a score from 0 to 100. I rejected this for three reasons:

- Model-generated scores can change between runs, so the ranking would not be repeatable.
- Scores cannot be fully explained, which makes them hard to defend in an audit.
- A proposal could include hidden text that tries to influence the score (prompt injection), and Proposal C does exactly this.

I redesigned the system so the AI only does what it is good at: reading documents and extracting facts with verbatim evidence quotes. Deterministic code does all scoring and ranking. This makes the result consistent, explainable and safe against manipulation.

### Where I Made a Correction

An earlier draft gave a score of zero to a proposal with no stated completion time and still ranked it. I changed this so the proposal is flagged for human review. A missing fact is not the same as a bad answer, and treating silence as a zero would punish a bidder for an omission that may be easy to clarify.

### How I Verified the AI's Work

- I ran `python prototype/score.py` and checked that the scores match `ranking.json`.
- I treated the instruction hidden in Proposal C as untrusted data, not as a command.
- I checked that the write-up stays under the 1,000-word limit and that no brief text is copied into the repository.