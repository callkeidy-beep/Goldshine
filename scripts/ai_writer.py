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

import gnews

SYSTEM = """너는 서울 강남구 개포동에서 20년 가까이 부동산을 중개해 온 사장님이다.
사장님은 중년 여성이다. 키가 크고 예쁘며 피부가 곱다. 성격이 밝고 다정해서 손님이 편하게 속을 털어놓는다.
안경이나 돋보기를 쓰는 묘사, 남성으로 읽히는 묘사는 하지 않는다. 사장님의 몸짓은 미소, 따뜻한 차를 내미는 손, 고개를 끄덕이는 모습처럼 그린다.
매일 아침 사무실 블로그에 글 한 편을 올린다. 오늘은 후보 기사 중 3편을 골라 초안을 만든다.

[문장 원칙 — 에세이]
- 블로그 에세이처럼 쓴다. 감성적이고 부드러운 만연체다. 오래 알고 지낸 이웃에게 차 한 잔 앞에 두고 들려주는 말투다.
- 본문은 합니다체로 쓴다. "~습니다", "~입니다"에 "~지요", "~더군요", "~하곤 합니다"를 섞어 결을 부드럽게 한다.
  "~다", "~했다"로 끝나는 반말 평서문은 본문에 쓰지 않는다. (대사와 괄호 속 속말은 예외다.)
- 문장을 짧게 끊지 않는다. "~고", "~는데", "~면서", "~듯" 같은 연결어미로 장면과 생각을 이어 한 문장을 40~80자로 흐르게 쓴다.
- 한 줄에 한 문장씩 끊어 쓰지 않는다. 문단 안에서는 문장을 이어 쓰고, 줄바꿈은 문단 사이(빈 줄)에만 둔다.
- 첫 문단은 손님의 말 한마디와 그날 사무실의 계절, 빛, 냄새, 소리로 연다.
- 대사를 2번 이상, 사장님의 속마음을 1번 이상 넣는다. 속마음은 괄호나 "~싶었습니다"처럼 자연스럽게 녹인다.
- 숫자와 사실은 이야기 속에 부드럽게 녹인다. 보고서처럼 나열하지 않는다.
- 감정을 이름으로 단정하지 않고, 표정과 손짓, 창밖 풍경에 기대어 느끼게 한다. 따뜻한 비유를 한두 개 쓴다.
- 훈계는 "확인할 것" 문단과 "중개사 한마디"에만 둔다. 그 두 곳은 짧고 정확하게 쓴다.
- 과장, 공포 마케팅, "지금 꼭 사야" 같은 권유는 쓰지 않는다.

[본문 예시 — 결을 따라라. 내용과 문장은 베끼지 않는다]
"사장님, 이 동네도 이제 떨어지는 거예요?" 문을 열고 들어선 손님이 숨을 고를 새도 없이 휴대폰 화면을 제 쪽으로 돌려 보였는데, 기사 제목 아래로 붉은 화살표가 길게 내려가 있었습니다.

저는 대답 대신 따뜻한 보리차를 한 잔 따라 손님 앞에 놓아 드리고, 잠시 창밖을 바라보았습니다. 늦가을 햇살이 공사 가림막 위에 비스듬히 내려앉아 있었고, 그 너머로 크레인 한 대가 아무 일 없다는 듯 천천히 고개를 돌리고 있었지요. 숫자는 늘 사람보다 한 걸음 먼저 움직인다는 걸, 이 자리에서 스무 해 가까이 지내며 몸으로 배웠습니다.

[인용 원칙 — 저작권]
- 기사에 나온 전문가, 교수, 연구원, 애널리스트, 업계 관계자, 다른 중개업소 대표의 말은 쓰지 않는다.
  따옴표로 옮기는 것도, "~라고 전망했다"처럼 바꿔 쓰는 것도 하지 않는다. 그 사람의 이름과 소속도 쓰지 않는다.
- 기사 문장을 그대로 옮기지 않는다. 숫자와 사실만 가져와 사장님의 말로 다시 쓴다.
- 예외: 대통령, 장관·정부 부처, 국회의원·시장·구청장 같은 정치인의 공개 발언, 정부·지자체의 공식 정책 발표,
  유튜버 등의 공개 방송 발언처럼 여러 매체가 함께 다뤄 누구나 알 수 있는 발언은 쓸 수 있다.
  이때는 누가, 어떤 자리에서 말했는지 밝힌다.
- 4컷 대사에도 같은 원칙을 지킨다.

[사실 원칙]
- "본문_확보"가 true인 기사를 우선 고른다.
- "본문_확보"가 false인 기사는 제목과 요약에 적힌 사실만 쓴다. 누가 누구에게 돈을 빌려줬는지, 왜 그렇게 됐는지 같은
  구조와 원인을 짐작해 쓰지 않는다. 제목 속 말이 두 가지로 읽힐 수 있으면(예: "집주인 대출") 풀어 설명하지 않는다.
  그 기사로 1000자 가까이 쓰기 어렵다면 고르지 않는다.
- 일반 상식이라도 자료에 없는 수치(비율, 금리, 기준)는 쓰지 않는다.
- 숫자, 날짜, 단지명, 금액은 주어진 자료에 있는 것만 쓴다. 없으면 쓰지 않는다.
- 자료에 없는 내용을 추측해 사실처럼 쓰지 않는다.
- 세금, 대출 이야기는 "세무사·은행과 확인하세요"를 덧붙인다.

[구성]
- episode: 글을 여는 가상의 에피소드 한 문단(2~3문장). 손님의 대사로 시작해 사무실의 계절, 빛, 소리로 장면을 세운다.
  episode에는 "가상의 에피소드" 같은 안내 문구를 쓰지 않는다. 안내 문구는 프로그램이 붙인다.
- body: episode 다음에 이어질 본문. episode를 다시 쓰지 않는다. 900~1300자. 문단 4~6개, 문단 사이는 빈 줄. 아래 순서로 쓴다.
  1) 장면 잇기: 에피소드 속 손님과 나눈 이야기를 이어 간다.
  2) 사실: 기사 속 숫자, 날짜, 단지명을 2~3개 짚는다.
  3) 배경: 왜 이런 일이 생겼는지 제도, 일정, 시장 흐름으로 풀어 준다. 자료에 있는 것만.
  4) 현장: 이 소식이 개포동 손님에게 실제로 무엇을 바꾸는지, 사무실에서 본 장면으로 보여준다.
  5) 확인할 것: 매수·매도·전세 손님이 챙길 서류나 날짜 2~3가지를 짧은 문장으로.
  6) 여운: 한두 줄로 닫는다.
  마지막 줄은 "중개사 한마디 — "로 시작하는 실전 조언.
- comic: 「개포 사무실 4컷」. 1~3컷은 손님과 사장님의 대화, 4컷은 사장님의 한마디. 대사는 한 컷에 20자 안쪽, 길어도 26자를 넘기지 않는다. scene은 15자 안쪽.
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
                    "episode": {"type": "string"},
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
                "required": ["candidate_id", "category", "title", "hook", "episode", "body", "tip", "why", "comic", "chart"],
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
        self.parts, self.loose, self.desc, self._in_p, self._skip = [], [], "", False, 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "meta" and a.get("property") in ("og:description",) and a.get("content"):
            self.desc = a["content"]
        if tag in ("script", "style", "nav", "header", "footer", "noscript"):
            self._skip += 1
        if tag == "p":
            self._in_p = True

    def handle_endtag(self, tag):
        if tag in ("script", "style", "nav", "header", "footer", "noscript") and self._skip:
            self._skip -= 1
        if tag == "p":
            self._in_p = False

    def handle_data(self, data):
        t = data.strip()
        if self._skip:
            return
        if self._in_p and len(t) > 20:
            self.parts.append(t)
        elif len(t) > 40 and t.endswith(("다.", "다", ".", "요.", "”", '"')):
            self.loose.append(t)  # <p>를 쓰지 않는 모바일·AMP 기사용


def article_text(url: str, limit: int = 2500) -> str:
    """원문에서 본문을 대강 뽑습니다. 실패하면 빈 문자열."""
    if not url or "news.google.com" in url:
        return ""
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=8)
        r.encoding = r.apparent_encoding or r.encoding
        p = _Text()
        p.feed(r.text)
        body = " ".join(p.parts)
        if len(body) < 300:
            body = " ".join(p.parts + p.loose) or p.desc
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


def recent_topics(day: str, days: int = 7) -> list[str]:
    """지난 며칠 동안 이미 올린 글 제목들 (같은 이야기를 되풀이하지 않도록)."""
    import datetime as dt
    from common import DOCS, read_json
    base = dt.date.fromisoformat(day)
    out = []
    for i in range(1, days + 1):
        d = (base - dt.timedelta(days=i)).isoformat()
        for p in read_json(DOCS / "data" / "days" / f"{d}.json", {}).get("posts", []):
            out.append(f"{d} {p['title']}")
    return out


def build_prompt(cfg: dict, day: str, cands: list[dict], deals: list[dict], stats: dict) -> str:
    blocks = []
    for c in cands:
        # 구글뉴스 링크는 원문 주소를 찾아 본문을 읽고, 블로그 출처 링크도 원문으로 바꿉니다
        if "news.google.com" in c.get("link", ""):
            real = gnews.resolve(c["link"])
            if real:
                c["link"] = real
        text = article_text(c["link"])
        c["has_article"] = len(text) >= 300
        blocks.append({
            "candidate_id": c["id"], "category": c["category"], "title": c["title"],
            "press": c.get("press", ""), "published": c.get("published", ""),
            "summary": c.get("summary", ""),
            "본문_확보": c["has_article"],
            "article": text,
        })
    got = sum(1 for c in cands if c.get("has_article"))
    print(f"  원문 본문 확보: {got}/{len(cands)}건")
    deal_note = ""
    if deals:
        deal_note = "\n[최근 실거래 (만원 단위)]\n" + "\n".join(
            f"{d['date']} {d['apt']} {d['area']}㎡ {d['floor']}층 {d['amount']}" for d in deals[:15])
        blocks.append({"candidate_id": "deals", "category": "실거래", "title": f"최근 {cfg['deals']['dong']} 실거래", "summary": "아래 실거래 목록 참고"})
    return (
        f"오늘은 {day}이다.\n\n[학습 기록]\n{feedback_block(stats)}\n\n"
        + ("[최근 7일 동안 이미 올린 글 — 같은 사건·같은 소재는 고르지 않는다. 후속 보도라면 새로 밝혀진 사실이 있을 때만 고르고, 그 새 사실을 중심으로 쓴다]\n"
           + "\n".join(recent_topics(day)) + "\n\n" if recent_topics(day) else "")
        + 
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
                "generationConfig": {"responseMimeType": "application/json", "maxOutputTokens": 32000},
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


DISCLAIMER = "(위 내용은 이해를 돕기 위한 가상의 에피소드입니다.)"


def with_episode(episode: str, body: str) -> str:
    """에피소드 문단 바로 뒤에 가상 에피소드 안내 문구를 붙여 본문을 만듭니다."""
    body = body.replace(DISCLAIMER, "").strip()
    episode = episode.replace(DISCLAIMER, "").strip()
    if not episode:  # 에피소드를 따로 주지 않았으면 본문 첫 문단을 에피소드로 봅니다
        parts = re.split(r"\n\s*\n", body, maxsplit=1)
        episode, body = parts[0].strip(), (parts[1].strip() if len(parts) > 1 else "")
    return f"{episode}\n{DISCLAIMER}\n\n{body}".strip()


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
        "body": with_episode(p.get("episode") or "", p.get("body") or "") if (p.get("body") or p.get("episode")) else "",
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


EXPERT = re.compile(r"(교수|연구원|연구위원|애널리스트|관계자|전문가|센터장|소장|팀장|이사|대표|수석|위원)[^.\n]{0,40}"
                    r"(말했|밝혔|설명했|전망했|분석했|지적했|강조했|덧붙였|예상했|내다봤|조언했|평가했|라고|이라고|고 했)")
PLAIN = re.compile(r"(?<!니)(다|었다|였다|했다)[.!?]?\s*$")


def style_problems(posts: list[dict]) -> list[str]:
    """문체 검사: 설명조 존댓말, 긴 문장, 대사 없음, 긴 4컷 대사를 찾습니다."""
    out = []
    for i, p in enumerate(posts, 1):
        body = p["body"].split("중개사 한마디")[0]
        sents = [x.strip() for x in re.split(r"(?<=[.!?])\s+|\n+", body) if x.strip()]
        narr = [x for x in sents if not x.startswith(("\"", "“", "(", "‘", "'"))]
        plain = [x for x in narr if PLAIN.search(x)]
        if plain and len(plain) >= max(2, len(narr) // 4):
            out.append(f"{i}번 본문에 '~다'로 끝나는 반말 문장이 {len(plain)}개다. '~습니다' 합니다체로 고쳐라. 예: {plain[0][:30]}")
        if narr and sum(len(x) for x in narr) / len(narr) < 30:
            out.append(f"{i}번 본문이 짧게 끊긴 문장 위주다(평균 {sum(len(x) for x in narr) // len(narr)}자). 연결어미로 이어 40~80자의 부드러운 만연체로 고치고, 문단 안에서는 줄을 바꾸지 마라.")
        quoted = EXPERT.findall(p["body"]) or [m for x in p["comic"]["panels"] for m in EXPERT.findall(x.get("line", ""))]
        if quoted:
            m = EXPERT.search(p["body"]) or next(EXPERT.search(x.get("line", "")) for x in p["comic"]["panels"] if EXPERT.search(x.get("line", "")))
            out.append(f"{i}번에 기사 속 전문가·관계자 발언이 들어갔다(저작권). 빼고 사장님의 말로 다시 써라. 예: {m.group(0)[:30]}")
        if len(body) < 750:
            out.append(f"{i}번 본문이 {len(body)}자로 짧다. 배경과 현장, 확인할 것을 더해 900~1300자로 늘려라.")
        if not re.search(r'["“]', body):
            out.append(f"{i}번 본문에 대사가 없다. 손님의 말 한 줄로 열어라.")
        longline = [x["line"] for x in p["comic"]["panels"] if len(x.get("line", "")) > 26]
        if longline:
            out.append(f"{i}번 4컷 대사가 길다(26자 초과). 짧게 줄여라. 예: {longline[0][:30]}")
    return out


def write(cfg: dict, day: str, cands: list[dict], deals: list[dict], stats: dict) -> list[dict]:
    user = build_prompt(cfg, day, cands, deals, stats)
    call = call_claude if provider() == "claude" else call_gemini
    text = call(cfg, user)
    posts = [normalize(p) for p in parse_json(text).get("posts", [])][:3]
    posts = [p for p in posts if p["title"] and p["body"]]
    # 문체·분량·인용이 원칙에서 벗어나면 고칠 점을 알려 주고 최대 두 번 다시 쓰게 합니다.
    # 가장 문제가 적은 초안(같으면 더 긴 초안)을 고릅니다.
    def rank(ps):
        return (len(style_problems(ps)), -sum(len(x["body"]) for x in ps))
    best, best_text = posts, text
    for attempt in range(2):
        issues = style_problems(best) if len(best) == 3 else []
        if not issues:
            break
        print(f"  문체 다시 쓰기 {attempt + 1}: " + " / ".join(issues))
        retry = (user + "\n\n[처음 쓴 초안]\n" + best_text + "\n\n[고칠 점]\n- " + "\n- ".join(issues)
                 + "\n\n같은 기사 3편을 유지하고, 고칠 점을 모두 반영해 다시 써라. 본문은 반드시 900자 이상이다.")
        try:
            again_text = call(cfg, retry)
            again = [normalize(p) for p in parse_json(again_text).get("posts", [])][:3]
            again = [p for p in again if p["title"] and p["body"]]
            if len(again) == 3 and rank(again) < rank(best):
                best, best_text = again, again_text
        except Exception as e:  # 다시 쓰기가 실패하면 그때까지의 가장 나은 초안을 씁니다
            print(f"  다시 쓰기 실패: {str(e)[:120]}")
            break
    posts = best
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
