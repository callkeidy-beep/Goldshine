"""오늘의 3편을 만듭니다.

1) data/candidates/오늘.json 을 읽어 점수를 매깁니다(학습 반영).
2) ANTHROPIC_API_KEY 가 있으면 Claude, GEMINI_API_KEY 가 있으면 Gemini가 3편을 씁니다. 없거나 실패하면 무료판으로 씁니다.
3) docs/data/days/오늘.json 에 저장하고 홈페이지 데이터를 다시 만듭니다.
"""
import datetime as dt
import os
import sys

import free_writer
import scoring
from build_site import build
from common import DATA, DOCS, KST, load_config, read_json, today, write_json


def trend_chart(cfg: dict, category: str, day: str) -> dict:
    """최근 7일 동안 이 유형 기사가 몇 건 모였는지."""
    base = dt.date.fromisoformat(day)
    labels, values = [], []
    for i in range(6, -1, -1):
        d = (base - dt.timedelta(days=i)).isoformat()
        news = read_json(DATA / "candidates" / f"{d}.json", {}).get("news", [])
        n = sum(1 for it in news if scoring.match_tiers(cfg, it["title"] + " " + it.get("summary", ""))[0] == category)
        labels.append(d[5:].replace("-", "/"))
        values.append(n)
    return {"type": "line", "title": f"최근 7일 '{category}' 기사 수", "unit": "건",
            "labels": labels, "values": values, "note": "Goldshine이 매일 모은 기사 기준"}


def main() -> int:
    cfg = load_config()
    day = today()
    raw = read_json(DATA / "candidates" / f"{day}.json", None)
    if raw is None:
        print("오늘 후보가 없습니다. collect.py 를 먼저 실행하세요.", file=sys.stderr)
        return 1

    stats = scoring.learned_stats(cfg)
    ranked = scoring.rank(cfg, raw.get("news", []), stats)
    cutoff = (dt.date.fromisoformat(day) - dt.timedelta(days=cfg["deals"]["days"])).isoformat()
    deals = [d for d in raw.get("deals", []) if d["date"] >= cutoff]
    print(f"점수 매긴 후보 {len(ranked)}건, 최근 실거래 {len(deals)}건, 학습 기록 {stats['total']}건")

    posts, mode, note, ai_name = [], "free", "", ""
    if os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("GEMINI_API_KEY"):
        try:
            import ai_writer
            pool = scoring.diverse_top(ranked, cfg["ai"].get("candidates_to_send", 9))
            posts = ai_writer.write(cfg, day, pool, deals, stats)
            mode = "ai"
            ai_name = "Claude" if ai_writer.provider() == "claude" else "Gemini"
        except Exception as e:
            note = f"AI 작성 실패로 무료판을 썼습니다: {str(e)[:160]}"
            print(note, file=sys.stderr)

    # 같은 날 다시 돌렸는데 AI가 실패했다면, 이미 있는 AI 초안을 무료판으로 덮어쓰지 않습니다
    existing = read_json(DOCS / "data" / "days" / f"{day}.json", {})
    if not posts and existing.get("mode") == "ai" and not existing.get("sample"):
        print(f"AI 작성 실패 — 오늘 이미 만든 AI 초안을 그대로 둡니다. ({note[:120]})")
        build()
        return 0

    if not posts:
        deal_mult = scoring.category_multiplier(stats, "실거래")
        picks = scoring.diverse_top(ranked, 3)
        posts = []
        use_deals = bool(deals) and (deal_mult >= 0.9 or len(picks) < 3)
        if use_deals:
            picks = picks[:2]
        for i, c in enumerate(picks, 1):
            posts.append(free_writer.news_post(i, c, trend_chart(cfg, c["category"], day)))
        if use_deals:
            posts.append(free_writer.deals_post(len(posts) + 1, deals, cfg["deals"]["dong"]))

    if not posts:
        print("추천할 기사가 없습니다.", file=sys.stderr)
        return 1

    write_json(DOCS / "data" / "days" / f"{day}.json", {
        "date": day,
        "mode": mode,
        "ai": ai_name,
        "note": note,
        "generated_at": dt.datetime.now(KST).isoformat(timespec="minutes"),
        "candidate_count": len(raw.get("news", [])),
        "posts": posts,
    })
    build()
    print(f"{day} 추천 {len(posts)}편 저장 ({ai_name or '무료판'})")
    for p in posts:
        print(f"  {p['slot']}. [{p['category']}] {p['title']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
