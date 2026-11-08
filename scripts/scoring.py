"""후보 점수 매기기와 학습.

학습은 단순합니다. 마이클이 준 1~5점을 유형(category)별, 키워드별로 평균 냅니다.
기록이 적을 때는 3점을 prior_count 만큼 깔아 두어 한두 번의 점수에 휘둘리지 않게 합니다.
평균이 3점보다 높은 유형은 더 자주, 낮은 유형은 덜 자주 추천됩니다.
"""
import datetime as dt
from collections import defaultdict

from common import DATA, KST, read_json


def match_tiers(cfg: dict, text: str) -> tuple[str, float, list[str]]:
    best_cat, best_w, hits = "기타", 0.0, []
    for tier in cfg["tiers"]:
        found = [k for k in tier["keywords"] if k in text]
        if found:
            hits += found
            if tier["weight"] > best_w:
                best_cat, best_w = tier["category"], float(tier["weight"])
    return best_cat, best_w, sorted(set(hits))


def learned_stats(cfg: dict) -> dict:
    every = read_json(DATA / "scores.json", [])
    scores = [s for s in every if s.get("kind", "post") == "post"]
    toons = [s for s in every if s.get("kind") == "comic" and s.get("comic")]
    prior = cfg.get("learning", {}).get("prior_count", 2)
    by_cat, by_kw = defaultdict(list), defaultdict(list)
    for s in scores:
        by_cat[s.get("category", "기타")].append(s["score"])
        for k in s.get("keywords", []):
            by_kw[k].append(s["score"])

    def smooth(v):
        return (sum(v) + 3 * prior) / (len(v) + prior)

    cat = {c: {"avg": round(smooth(v), 2), "n": len(v)} for c, v in by_cat.items()}
    kw = {k: {"avg": round(smooth(v), 2), "n": len(v)} for k, v in by_kw.items() if len(v) >= 2}
    best = sorted([s for s in scores if s["score"] >= 4], key=lambda s: (-s["score"], s["date"]))[:6]
    worst = sorted([s for s in scores if s["score"] <= 2], key=lambda s: (s["score"], s["date"]))[:6]
    tv = [t["score"] for t in toons]
    comic = {
        "total": len(toons),
        "avg": round(smooth(tv), 2) if tv else 0,
        # 높은 점수 4컷은 대본 전체를 본보기로, 낮은 점수 4컷은 제목과 메모만 씁니다
        "best": sorted(sorted([t for t in toons if t["score"] >= 4], key=lambda t: t["date"], reverse=True),
                       key=lambda t: (-t["score"], -int(bool(t.get("edited")))))[:3],
        "worst": sorted([t for t in toons if t["score"] <= 2], key=lambda t: (t["score"], t["date"]))[:4],
    }
    return {"total": len(scores), "category": cat, "keyword": kw, "best": best, "worst": worst, "comic": comic}


def category_multiplier(stats: dict, category: str) -> float:
    c = stats["category"].get(category)
    if not c:
        return 1.0
    return max(0.6, min(1.6, c["avg"] / 3))


def score_news(cfg: dict, stats: dict, item: dict, now: dt.datetime) -> dict:
    title, summary = item["title"], item.get("summary", "")
    cat, w, hits = match_tiers(cfg, title + " " + summary)
    title_hits = sum(1 for h in hits if h in title)
    s = w + 1.5 * title_hits + 0.5 * (len(hits) - title_hits)
    try:
        age_h = (now - dt.datetime.fromisoformat(item["published"])).total_seconds() / 3600
        s += 2 if age_h <= 24 else 1 if age_h <= 48 else 0
    except (KeyError, ValueError, TypeError):
        pass
    s *= category_multiplier(stats, cat)
    for h in hits:
        k = stats["keyword"].get(h)
        if k:
            s += (k["avg"] - 3)
    return {**item, "category": cat, "keywords": hits, "score": round(s, 2)}


def rank(cfg: dict, news: list[dict], stats: dict) -> list[dict]:
    now = dt.datetime.now(KST)
    scored = [score_news(cfg, stats, it, now) for it in news]
    scored = [x for x in scored if x["category"] != "기타"]
    return sorted(scored, key=lambda x: -x["score"])


def diverse_top(ranked: list[dict], k: int) -> list[dict]:
    """유형이 겹치지 않게 먼저 고르고, 모자라면 점수순으로 채웁니다."""
    out, used = [], set()
    for x in ranked:
        if x["category"] not in used:
            out.append(x)
            used.add(x["category"])
        if len(out) == k:
            return out
    for x in ranked:
        if x not in out:
            out.append(x)
        if len(out) == k:
            break
    return out
