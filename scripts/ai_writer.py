"""AI 작성기: 후보 중 3편을 골라 블로그 글, 4컷 대본, 도표를 만듭니다.

ANTHROPIC_API_KEY 가 있으면 Claude, 없고 GEMINI_API_KEY 가 있으면 Gemini를 씁니다.
둘 다 없거나 실패하면 make_daily.py 가 무료판으로 넘어갑니다.
"""
import json
import os
import re
from html.parser import HTMLParser

import anthropic
import requests

SYSTEM = """너는 서울 강남구 개포동에서 20년 가까이 부동산을 중개해 온 사장님이다.
매일 아침 사무실 블로그에 글 한 편을 올린다. 오늘은 후보 기사 중 3편을 골라 초안을 만든다.

[문장 원칙 — 『묘사의 힘』]
- 주어와 술어 중심의 짧은 문장으로 쓴다.
- 해설하지 말고 장면으로 보여준다. 사무실, 손님, 단지 풍경, 달력, 서류 같은 구체적 이미지로 시작한다.
- 감정을 직접 말하지 않는다. 표정, 행동, 대화로 느끼게 한다.
- 대화와 짧은 내적 독백을 쓴다. 손님의 질문 한 줄로 여는 것이 좋다.
- 과장, 공포 마케팅, "지금 꼭 사야" 같은 권유는 쓰지 않는다.

[사실 원칙]
- 숫자, 날짜, 단지명, 금액은 주어진 자료에 있는 것만 쓴다. 없으면 쓰지 않는다.
- 자료에 없는 내용을 추측해 사실처럼 쓰지 않는다.
- 세금, 대출 이야기는 "세무사·은행과 확인하세요"를 덧붙인다.

[구성]
- body: 400~700자. 장면 → 사실 → 의미 순서. 마지막 줄은 "중개사 한마디 — "로 시작하는 실전 조언.
- comic: 「개포 사무실 4컷」. 1~3컷은 손님과 사장님의 대화, 4컷은 사장님의 한마디. 대사는 한 컷에 25자 안팎.
  number는 4컷에 크게 박힐 숫자 하나(예: "14건 중 10건", "-1.38%"). 자료에 숫자가 없으면 핵심 단어 하나.
- chart: 자료 속 숫자로 도표를 만들 수 있을 때만 has_chart=true. labels와 values 개수는 같아야 한다.
  숫자를 지어내지 않는다. 만들 수 없으면 has_chart=false, 배열은 비운다.
- 3편은 서로 다른 유형이면 좋다. 개포동 직접 관련 기사가 있으면 1편 이상 넣는다.
"""

SCHEMA = {
    "type": "object",
    "properties": {
        "posts": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "candidate_id": {"type": "string"},
                    "category": {"type": "string"},
                    "title": {"type": "string"},
                    "hook": {"type": "string"},
                    "body": {"type": "string"},
                    "tip": {"type": "string"},
                    "why": {"type": "string"},
                    "comic": {
                        "type": "object",
                        "properties": {
                            "panels": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "speaker": {"type": "string", "enum": ["손님", "사장님"]},
                                        "line": {"type": "string"},
                                        "scene": {"type": "string"},
                                    },
                                    "required": ["speaker", "line", "scene"],
                                    "additionalProperties": False,
                                },
                            },
                            "number": {"type": "string"},
                            "number_caption": {"type": "string"},
                        },
                        "required": ["panels", "number", "number_caption"],
                        "additionalProperties": False,
                    },
                    "chart": {
                        "type": "object",
                        "properties": {
                            "has_chart": {"type": "boolean"},
                            "type": {"type": "string", "enum": ["bar", "line"]},
                            "title": {"type": "string"},
                            "unit": {"type": "string"},
                            "labels": {"type": "array", "items": {"type": "string"}},
                            "values": {"type": "array", "items": {"type": "number"}},
                            "note": {"type": "string"},
                        },
                        "required": ["has_chart", "type", "title", "unit", "labels", "values", "note"],
                        "additionalProperties": False,
                    },
                },
                "required": ["candidate_id", "category", "title", "hook", "body", "tip", "why", "comic", "chart"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["posts"],
    "additionalProperties": False,
}


class _Text(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts, self.desc, self._in_p, self._skip = [], "", False, 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "meta" and a.get("property") in ("og:description",) and a.get("content"):
            self.desc = a["content"]
        if tag in ("script", "style"):
            self._skip += 1
        if tag == "p":
            self._in_p = True

    def handle_endtag(self, tag):
        if tag in ("script", "style") and self._skip:
            self._skip -= 1
        if tag == "p":
            self._in_p = False

    def handle_data(self, data):
        if self._in_p and not self._skip and len(data.strip()) > 20:
            self.parts.append(data.strip())


def article_text(url: str, limit: int = 2500) -> str:
    """원문에서 본문을 대강 뽑습니다. 실패하면 빈 문자열."""
    if not url or "news.google.com" in url:
        return ""
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=8)
        r.encoding = r.apparent_encoding or r.encoding
        p = _Text()
        p.feed(r.text)
        body = " ".join(p.parts) or p.desc
        return re.sub(r"\s+", " ", body)[:limit]
    except Exception:
        return ""


def feedback_block(stats: dict) -> str:
    if not stats["total"]:
        return "아직 점수 기록이 없다. 개포동 직접 관련성과 구체적 숫자를 우선한다."
    lines = [f"사장님이 지금까지 {stats['total']}편에 점수를 줬다(5점 만점)."]
    if stats["category"]:
        cats = ", ".join(f"{c} {v['avg']}점({v['n']}편)" for c, v in sorted(stats["category"].items(), key=lambda x: -x[1]["avg"]))
        lines.append(f"유형별 평균: {cats}")
    if stats["best"]:
        lines.append("좋은 점수를 받은 글: " + " / ".join(f"[{b['score']}점] {b['title']}" + (f" — 메모: {b['memo']}" if b.get("memo") else "") for b in stats["best"]))
    if stats["worst"]:
        lines.append("낮은 점수를 받은 글: " + " / ".join(f"[{w['score']}점] {w['title']}" + (f" — 메모: {w['memo']}" if w.get("memo") else "") for w in stats["worst"]))
    lines.append("높은 점수 쪽의 소재와 결을 따라가되, 같은 기사를 반복하지 않는다.")
    lines += comic_feedback(stats.get("comic") or {})
    return "\n".join(lines)


def comic_feedback(c: dict) -> list[str]:
    """4컷 점수 학습: 5점에 가까운 4컷 대본을 본보기로 보여 줍니다."""
    if not c.get("total"):
        return []
    out = [f"\n[4컷 점수] 4컷 {c['total']}개에 점수를 받았다. 평균 {c['avg']}점."]
    for t in c.get("best", []):
        cm = t.get("comic") or {}
        script = " / ".join(f"{x.get('speaker', '')}: {x.get('line', '')}" for x in cm.get("panels", []))
        tag = " (사장님이 직접 고친 대본)" if t.get("edited") else ""
        out.append(f"본보기 [{t['score']}점]{tag} 「{t['title']}」 → {script} / 숫자 칸: {cm.get('number', '')}"
                   + (f" — 메모: {t['memo']}" if t.get("memo") else ""))
    for t in c.get("worst", []):
        out.append(f"피할 것 [{t['score']}점] 「{t['title']}」" + (f" — 메모: {t['memo']}" if t.get("memo") else ""))
    out.append("오늘 4컷은 본보기의 리듬, 말투, 반전 방식을 따르고, 피할 것의 메모를 반복하지 않는다. 대사를 베끼지는 않는다.")
    return out


def build_prompt(cfg: dict, day: str, cands: list[dict], deals: list[dict], stats: dict) -> str:
    blocks = []
    for c in cands:
        blocks.append({
            "candidate_id": c["id"], "category": c["category"], "title": c["title"],
            "press": c.get("press", ""), "published": c.get("published", ""),
            "summary": c.get("summary", ""), "article": article_text(c["link"]),
        })
    deal_note = ""
    if deals:
        deal_note = "\n[최근 실거래 (만원 단위)]\n" + "\n".join(
            f"{d['date']} {d['apt']} {d['area']}㎡ {d['floor']}층 {d['amount']}" for d in deals[:15])
        blocks.append({"candidate_id": "deals", "category": "실거래", "title": f"최근 {cfg['deals']['dong']} 실거래", "summary": "아래 실거래 목록 참고"})
    return (
        f"오늘은 {day}이다.\n\n[학습 기록]\n{feedback_block(stats)}\n\n"
        f"[후보 자료]\n{json.dumps(blocks, ensure_ascii=False, indent=1)}\n{deal_note}\n\n"
        "후보 중 정확히 3편을 골라 posts 배열에 담아라. 가장 추천하는 글을 첫 번째에 둔다."
    )


def system_prompt(cfg: dict) -> str:
    """기본 원칙 + config.yaml 의 writing.rules(글), comic.rules(4컷)."""
    out = SYSTEM
    w = (cfg.get("writing") or {}).get("rules", "").strip()
    if w:
        out += f"\n[글 추가 규칙 — 사장님이 정한 것]\n{w}\n"
    c = (cfg.get("comic") or {}).get("rules", "").strip()
    if c:
        out += f"\n[4컷 추가 규칙 — 사장님이 정한 것]\n{c}\n"
    return out


# ---------- Claude (Anthropic) ----------

def call_claude(cfg: dict, user: str) -> str:
    client = anthropic.Anthropic()
    ai = cfg.get("ai", {})
    resp = client.beta.messages.create(
        model=ai.get("model", "claude-opus-5-5"),
        max_tokens=16000,
        system=system_prompt(cfg),
        messages=[{"role": "user", "content": user}],
        output_config={"effort": ai.get("effort", "medium"), "format": {"type": "json_schema", "schema": SCHEMA}},
        betas=["server-side-fallback-2026-07-01"],
        extra_body={"fallbacks": "default"},  # 안전 거절 시 서버가 다른 모델로 이어서 답합니다
    )
    if resp.stop_reason == "refusal":
        raise RuntimeError("AI가 이 요청을 거절했습니다")
    if resp.stop_reason == "max_tokens":
        raise RuntimeError("AI 응답이 길이 제한에 걸렸습니다")
    return next(b.text for b in resp.content if b.type == "text")


# ---------- Gemini (Google AI Studio 무료 키) ----------

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


def call_gemini(cfg: dict, user: str) -> str:
    """config.yaml 의 gemini.models 를 차례로 시도합니다. 모델이 없거나(404) 한도 초과(429)면 다음 모델로."""
    key = os.environ["GEMINI_API_KEY"]
    models = (cfg.get("gemini") or {}).get("models") or ["gemini-3.5-flash"]
    shape = json.dumps(SCHEMA, ensure_ascii=False)
    prompt = user + "\n\n아래 JSON 스키마를 정확히 따르는 JSON 하나만 출력하라. 설명이나 마크다운은 쓰지 않는다.\n" + shape
    errors = []
    for model in models:
        r = requests.post(
            GEMINI_URL.format(model=model),
            headers={"x-goog-api-key": key, "Content-Type": "application/json"},
            json={
                "systemInstruction": {"parts": [{"text": system_prompt(cfg)}]},
                "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                "generationConfig": {"responseMimeType": "application/json", "maxOutputTokens": 16000},
            },
            timeout=180,
        )
        if r.status_code in (404, 429, 503):
            errors.append(f"{model}: {r.status_code}")
            continue
        r.raise_for_status()
        cand = (r.json().get("candidates") or [{}])[0]
        parts = (cand.get("content") or {}).get("parts") or []
        text = "".join(pt.get("text", "") for pt in parts if not pt.get("thought"))
        if not text:
            errors.append(f"{model}: 빈 응답 ({cand.get('finishReason', '?')})")
            continue
        print(f"  Gemini 모델: {model}")
        return text
    raise RuntimeError("Gemini 호출 실패 — " + ", ".join(errors))


def parse_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text)
    return json.loads(text)


def normalize(p: dict) -> dict:
    """스키마를 강제하지 못하는 모델(Gemini)의 답을 홈페이지가 읽는 모양으로 맞춥니다."""
    comic = p.get("comic") or {}
    panels = [x for x in (comic.get("panels") or []) if isinstance(x, dict) and x.get("line")][:4]
    while len(panels) < 4:
        panels.append({"speaker": "사장님", "line": "", "scene": ""})
    for x in panels:
        x["speaker"] = "사장님" if x.get("speaker") == "사장님" else "손님"
        x["scene"] = x.get("scene") or ""
    ch = p.get("chart") or {}
    labels, values = ch.get("labels") or [], ch.get("values") or []
    try:
        values = [float(v) for v in values]
    except (TypeError, ValueError):
        values = []
    ok = bool(ch.get("has_chart")) and labels and len(labels) == len(values)
    return {
        "candidate_id": str(p.get("candidate_id", "")),
        "category": p.get("category") or "기타",
        "title": p.get("title") or "",
        "hook": p.get("hook") or "",
        "body": p.get("body") or "",
        "tip": p.get("tip") or "",
        "why": p.get("why") or "",
        "comic": {"panels": panels, "number": str(comic.get("number") or ""), "number_caption": comic.get("number_caption") or ""},
        "chart": ({"type": ch.get("type") if ch.get("type") in ("bar", "line") else "bar", "title": ch.get("title") or "",
                   "unit": ch.get("unit") or "", "labels": [str(x) for x in labels], "values": values, "note": ch.get("note") or ""}
                  if ok else None),
    }


def provider() -> str:
    if os.environ.get("ANTHROPIC_API_KEY"):
        return "claude"
    if os.environ.get("GEMINI_API_KEY"):
        return "gemini"
    return ""


def write(cfg: dict, day: str, cands: list[dict], deals: list[dict], stats: dict) -> list[dict]:
    user = build_prompt(cfg, day, cands, deals, stats)
    who = provider()
    text = call_claude(cfg, user) if who == "claude" else call_gemini(cfg, user)
    posts = [normalize(p) for p in parse_json(text).get("posts", [])][:3]
    posts = [p for p in posts if p["title"] and p["body"]]
    if len(posts) < 3:
        raise RuntimeError(f"AI가 쓸 만한 글을 {len(posts)}편만 만들었습니다")

    by_id = {c["id"]: c for c in cands}
    out = []
    for i, p in enumerate(posts, 1):
        src = by_id.get(p["candidate_id"])
        out.append({
            **{k: v for k, v in p.items() if k != "candidate_id"},
            "category": src["category"] if src and p["category"] == "기타" else ("실거래" if p["candidate_id"] == "deals" else p["category"]),
            "slot": i,
            "id": p["candidate_id"] or f"ai-{day}-{i}",
            "keywords": src.get("keywords", []) if src else [cfg["deals"]["dong"], "실거래"],
            "sources": ([{"title": src["title"], "link": src["link"], "press": src.get("press", "")}] if src
                        else [{"title": "국토교통부 아파트 매매 실거래가", "link": "https://rt.molit.go.kr/", "press": "국토교통부"}]),
        })
    return out
