"""Deterministic gating, scoring and ranking. No AI, no network, no randomness.
The AI step only produces facts.json; everything that affects rank happens here.
Usage: python prototype/score.py
"""
import json
from pathlib import Path

HERE = Path(__file__).parent


def clamp(x: float) -> float:
    return max(0.0, min(1.0, x))


def points(c: dict, f: dict, k: dict) -> float:
    """Points for one weighted criterion, driven entirely by admin config."""
    r, w, t = c["rule"], c["weight"], c["rule"]["type"]
    if t == "capped_linear":
        return w * clamp((f.get(r["field"]) or 0) / r["cap"])
    if t == "price_vs_ceiling":
        p, ceil = f.get("price"), k["budget_ceiling"]
        if p is None:
            return 0.0
        full = r["full_marks_pct_of_ceiling"] * ceil
        return w * clamp((ceil - p) / (ceil - full))
    if t == "inverse_linear":
        v = f.get(r["field"])
        if v is None:
            return 0.0
        return w * clamp((r["worst"] - v) / (r["worst"] - r["best"]))
    if t == "split":
        return sum(w * p["share"] * clamp((f.get(p["field"]) or 0) / p["cap"])
                   for p in r["parts"])
    if t == "checklist":
        return w * sum(bool(f.get(i)) for i in r["items"]) / len(r["items"])
    raise ValueError(f"Unknown rule type: {t}")


def evaluate(crit: dict, facts: dict) -> list:
    k = crit["constraints"]
    assert round(sum(c["weight"] for c in crit["weighted"]), 6) == 100, "Weights must sum to 100"
    rows = []
    for pid, f in sorted(facts.items()):
        failed = [m["id"] for m in crit["mandatory"] if f.get(m["id"]) is not True]
        hard = []
        if f.get("price") is not None and f["price"] > k["budget_ceiling"]:
            hard.append("over_budget")
        if f.get("weeks") is not None and f["weeks"] > k["max_weeks"]:
            hard.append("over_schedule")
        flags = list(f.get("flags", [])) + [
            f"missing_{x}" for x in k["required_for_ranking"] if f.get(x) is None]
        breakdown = {c["id"]: round(points(c, f, k), 2) for c in crit["weighted"]}
        total = round(sum(breakdown.values()), 1)
        if failed or hard:
            status = "ineligible"
        elif flags:
            status = "flagged"
        else:
            status = "ranked"
        rows.append({"proposal": pid, "status": status, "total": total,
                     "breakdown": breakdown, "failed_gates": failed + hard,
                     "flags": flags, "price": f.get("price")})
    ranked = sorted((r for r in rows if r["status"] == "ranked"),
                    key=lambda r: (-r["total"], -r["breakdown"]["experience"],
                                   r["price"], r["proposal"]))
    for i, r in enumerate(ranked, 1):
        r["rank"] = i
    return rows


if __name__ == "__main__":
    crit = json.loads((HERE / "criteria.json").read_text())
    facts = json.loads((HERE / "facts.json").read_text())
    rows = evaluate(crit, facts)
    for r in sorted(rows, key=lambda r: (r.get("rank") or 99, r["proposal"])):
        shown = r["total"] if r["status"] == "ranked" else None
        print(f'{r["proposal"]}  rank={r.get("rank")}  status={r["status"]:<10} '
              f'score={shown}  shadow={r["total"]}  gates={r["failed_gates"]}  flags={r["flags"]}')
    out = HERE / "output"
    out.mkdir(exist_ok=True)
    (out / "audit.json").write_text(json.dumps(rows, indent=2))  # full breakdown for reviewers
