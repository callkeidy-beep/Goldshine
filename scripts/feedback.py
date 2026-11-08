"""홈페이지에서 보낸 이슈(점수, 출처 추가·끄기·삭제)를 데이터에 반영합니다.

이슈 제목 형식
  [점수] 2026-11-08            본문: 글 "1: 4", 4컷 "c1: 5", "memo1: ...", "cmemo1: ...", "comic1: {고친 대본}" 줄
  [출처추가] 이름              본문: "type: google_news" / "query: ..." / "url: ..." / "include: a, b"
  [출처끄기] 출처ID   [출처켜기] 출처ID   [출처삭제] 출처ID

GitHub 앱 댓글처럼 본문에 "1:4 2:3 3:5 c1:5 c2:3" 한 줄만 써도 됩니다.
결과 메시지를 표준출력으로 남기면 워크플로가 이슈 댓글로 답합니다.
"""
import datetime as dt
import json
import os
import re
import sys

from build_site import build
from common import DATA, DOCS, KST, read_json, short_id, write_json


def kv(body: str) -> dict:
    out = {}
    for line in body.splitlines():
        m = re.match(r"\s*([A-Za-z_0-9]+)\s*[:：]\s*(.*)$", line)
        if m:
            out[m.group(1).lower()] = m.group(2).strip()
    return out


def apply_scores(title: str, body: str) -> str:
    """글 점수(1: 4)와 4컷 점수(c1: 5)를 함께 받습니다. comic1: {...} 줄은 직접 고친 4컷 대본입니다."""
    m = re.search(r"(\d{4}-\d{2}-\d{2})", title + " " + body)
    day = m.group(1) if m else dt.datetime.now(KST).strftime("%Y-%m-%d")
    daily = read_json(DOCS / "data" / "days" / f"{day}.json", None)
    if not daily:
        return f"{day} 추천 기록을 찾지 못했습니다."
    plain = "\n".join(l for l in body.splitlines() if not re.match(r"\s*(c?memo|comic)\d", l))
    post = {int(a): int(b) for a, b in re.findall(r"(?<![\w-])([1-3])\s*[:：]\s*([1-5])(?!\d)", plain)}
    toon = {int(a): int(b) for a, b in re.findall(r"(?<![\w-])[cC컷]\s*([1-3])\s*[:：]\s*([1-5])(?!\d)", plain)}
    if not post and not toon:
        return "점수를 읽지 못했습니다. 글은 1: 4, 4컷은 c1: 5 처럼 적어 주세요."
    f = kv(body)
    scores = read_json(DATA / "scores.json", [])
    done = []

    def put(kind: str, p: dict, score: int, memo_key: str, extra: dict) -> None:
        nonlocal scores
        same = lambda s: s["date"] == day and s["slot"] == p["slot"] and s.get("kind", "post") == kind
        old = next((s for s in scores if same(s)), {})
        scores = [s for s in scores if not same(s)]  # 다시 매기면 덮어쓰기
        scores.append({
            "kind": kind, "date": day, "slot": p["slot"], "id": p["id"], "category": p["category"],
            "title": p["title"], "mode": daily.get("mode", ""), "score": score,
            "memo": (f.get(memo_key) or old.get("memo", ""))[:200], **extra,
        })

    for p in daily["posts"]:
        n = p["slot"]
        if n in post:
            put("post", p, post[n], f"memo{n}", {"keywords": p.get("keywords", [])})
            done.append(f"{n}번 글 {post[n]}점")
        if n in toon:
            comic, edited = p.get("comic"), False
            try:
                if f.get(f"comic{n}"):
                    comic, edited = json.loads(f[f"comic{n}"]), True
            except json.JSONDecodeError:
                pass
            put("comic", p, toon[n], f"cmemo{n}", {"comic": comic, "edited": edited})
            done.append(f"{n}번 4컷 {toon[n]}점" + (" (고친 대본)" if edited else ""))
    scores.sort(key=lambda s: (s["date"], s["slot"], s.get("kind", "post")))
    write_json(DATA / "scores.json", scores)
    return f"{day} 점수 반영: " + ", ".join(done) + ". 내일 아침 추천부터 적용됩니다."


def apply_source(cmd: str, arg: str, body: str) -> str:
    sources = read_json(DATA / "sources.json", [])
    if cmd == "출처추가":
        f = kv(body)
        kind = f.get("type", "google_news")
        if kind not in ("google_news", "naver_news", "rss"):
            return f"모르는 종류입니다: {kind}"
        need = "url" if kind == "rss" else "query"
        if not f.get(need):
            return f"{need} 값이 비어 있습니다."
        src = {
            "id": f"u-{short_id(arg, f.get(need, ''))[:6]}",
            "name": arg or f.get(need),
            "type": kind,
            need: f[need],
            "include": [w.strip() for w in f.get("include", "").split(",") if w.strip()],
            "enabled": True,
        }
        if any(s.get(need) == src[need] and s["type"] == kind for s in sources):
            return "이미 있는 출처입니다."
        sources.append(src)
        write_json(DATA / "sources.json", sources)
        return f"출처 추가: {src['name']} ({src['id']}). 내일 아침 수집부터 들어갑니다."
    target = next((s for s in sources if s["id"] == arg.strip()), None)
    if not target:
        return f"출처 ID를 찾지 못했습니다: {arg}"
    if cmd == "출처삭제":
        sources.remove(target)
        msg = f"출처 삭제: {target['name']}"
    else:
        target["enabled"] = cmd == "출처켜기"
        msg = f"출처 {'켜기' if target['enabled'] else '끄기'}: {target['name']}"
    write_json(DATA / "sources.json", sources)
    return msg


def main() -> int:
    title = os.environ.get("ISSUE_TITLE", "")
    body = os.environ.get("ISSUE_BODY", "") or ""
    m = re.match(r"\s*\[(점수|Goldshine|개포 데일리|출처추가|출처끄기|출처켜기|출처삭제)\]\s*(.*)$", title)
    if not m:
        print("처리할 형식이 아닙니다.")
        return 0
    cmd, arg = m.group(1), m.group(2).strip()
    # "[Goldshine] 날짜" 알림 이슈(예전 이름 "[개포 데일리]" 포함)에 단 댓글도 점수로 받습니다
    msg = apply_scores(title, body) if cmd in ("점수", "Goldshine", "개포 데일리") else apply_source(cmd, arg, body)
    build()
    print(msg)
    return 0


if __name__ == "__main__":
    sys.exit(main())
