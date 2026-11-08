"""홈페이지(docs/)가 읽을 데이터를 모아 둡니다: 날짜 목록, 출처, 점수, 학습 요약, 저장소 이름."""
import os

from common import DATA, DOCS, load_config, read_json, write_json
from scoring import learned_stats


def build() -> None:
    cfg = load_config()
    days = sorted((p.stem for p in (DOCS / "data" / "days").glob("*.json")), reverse=True)
    stats = learned_stats(cfg)
    write_json(DOCS / "data" / "site.json", {
        "title": cfg["site"]["title"],
        "comic": {k: v for k, v in (cfg.get("comic") or {}).items() if k != "rules"},
        "region": cfg["site"]["region"],
        "repo": os.environ.get("GITHUB_REPOSITORY") or read_json(DOCS / "data" / "site.json", {}).get("repo", ""),
        "days": days,
        "sources": read_json(DATA / "sources.json", []),
        "scores": read_json(DATA / "scores.json", []),
        "learning": {"total": stats["total"], "category": stats["category"],
                     "comic": {"total": stats["comic"]["total"], "avg": stats["comic"]["avg"]}},
    })


if __name__ == "__main__":
    build()
    print("docs/data/site.json 갱신")
