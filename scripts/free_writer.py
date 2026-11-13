"""무료판 작성기: AI 없이 틀에 맞춰 3편을 만듭니다.

본문은 기사 요약과 원문 링크 중심입니다. 마이클이 직접 다듬을 초안 역할을 합니다.
"""
import re

NUM_RE = re.compile(r"(-?\d[\d,.]*\s*(?:억\s*\d[\d,]*만|억|조|만|%|％|건|가구|세대|층|㎡|평|원|명|년|개월|곳|배))")

QUESTION = {
    "개포단지": "그럼 우리 단지도 영향 있어요?",
    "강남시세": "그래서 지금 사요, 기다려요?",
    "정책·이슈": "저한테는 뭐가 달라지는데요?",
    "실거래": "요즘 얼마에 팔렸어요?",
}
SCENE = {
    "개포단지": "창밖으로 공사 가림막이 보인다",
    "강남시세": "손님이 휴대폰 화면을 내민다",
    "정책·이슈": "신문 한 면이 책상 위에 펼쳐진다",
    "실거래": "벽에 붙은 단지 배치도 앞",
}
TIP = {
    "개포단지": "기사 한 줄보다 조합 공지와 일정표를 먼저 보시는 게 좋다는 게 오늘 저의 생각입니다.",
    "강남시세": "주간 숫자보다 월간 흐름과 관심 단지 실거래가를 함께 보셔야 한다는 게 오늘 저의 생각입니다.",
    "정책·이슈": "시행일과 적용 대상을 먼저 확인하시고 세금은 세무사와 상의하셔야 한다는 게 오늘 저의 생각입니다.",
    "실거래": "같은 단지라도 동, 층, 향이 비슷한 거래끼리 비교하셔야 한다는 게 오늘 저의 생각입니다.",
}


SAY = {
    "개포단지": "조합 일정표부터 보세요.",
    "강남시세": "주간 숫자보다 실거래를 보세요.",
    "정책·이슈": "시행일과 대상부터 확인하세요.",
    "실거래": "같은 조건끼리 비교하세요.",
}


def first_number(*texts: str) -> str:
    for t in texts:
        m = NUM_RE.search(t or "")
        if m:
            return m.group(1).replace(" ", "")
    return ""


def cut(s: str, n: int) -> str:
    return s if len(s) <= n else s[: n - 1].rstrip() + "…"


def news_post(slot: int, c: dict, trend: dict) -> dict:
    cat = c["category"]
    number = first_number(c["title"], c.get("summary", ""))
    lines = [
        f"\"사장님, 이 기사 보셨어요?\"",
        f"{SCENE.get(cat, '아침, 사무실 문이 열린다')}.",
        "(위 내용은 이해를 돕기 위한 가상의 에피소드입니다.)",
        "",
        f"{c['title']}",
        "",
    ]
    if c.get("summary"):
        lines += [cut(c["summary"], 260), ""]
    lines += [f"중개사 한마디 — {TIP.get(cat, TIP['정책·이슈'])}"]
    return {
        "slot": slot,
        "id": c["id"],
        "category": cat,
        "title": cut(c["title"], 60),
        "hook": SCENE.get(cat, ""),
        "body": "\n".join(lines),
        "tip": TIP.get(cat, ""),
        "keywords": c.get("keywords", []),
        "sources": [{"title": c["title"], "link": c["link"], "press": c.get("press", "")}],
        "chart": trend,
        "comic": {
            "panels": [
                {"speaker": "손님", "line": "사장님, 이 기사 보셨어요?", "scene": "아침, 사무실 문이 열린다"},
                {"speaker": "사장님", "line": cut(c["title"], 42), "scene": SCENE.get(cat, "")},
                {"speaker": "손님", "line": QUESTION.get(cat, "그래서 어떻게 해야 돼요?"), "scene": "손님이 의자를 당겨 앉는다"},
                {"speaker": "사장님", "line": SAY.get(cat, "원문을 꼭 확인하세요."), "scene": "사장님이 웃으며 고개를 끄덕인다"},
            ],
            "number": number or cat,
            "number_caption": "오늘의 숫자" if number else "오늘의 주제",
        },
        "why": f"'{', '.join(c.get('keywords', [])[:3])}' 키워드, 점수 {c['score']}",
    }


def deals_post(slot: int, deals: list[dict], dong: str) -> dict:
    top = deals[:8]
    def label(d):
        return f"{cut(d['apt'], 8)} {round(d['area'])}㎡"
    def eok(m):
        return f"{m / 10000:.1f}억"
    hi = max(top, key=lambda d: d["amount"])
    lines = [
        "\"요즘 얼마에 팔렸어요?\"",
        "가장 많이 듣는 질문이다. 답은 신고된 거래에 있다.",
        "(위 내용은 이해를 돕기 위한 가상의 에피소드입니다.)",
        "",
        f"최근 신고된 {dong} 아파트 거래는 {len(deals)}건이다.",
        f"가장 비싼 거래는 {hi['apt']} 전용 {hi['area']}㎡, {eok(hi['amount'])}({hi['date']}, {hi['floor']}층)이었다.",
        "",
    ]
    lines += [f"· {d['date']} {d['apt']} {d['area']}㎡ {d['floor']}층 {eok(d['amount'])}" for d in top]
    lines += ["", f"중개사 한마디 — {TIP['실거래']}"]
    return {
        "slot": slot,
        "id": f"deals-{top[0]['date']}",
        "category": "실거래",
        "title": f"최근 {dong} 실거래 {len(deals)}건",
        "hook": "벽에 붙은 단지 배치도 앞",
        "body": "\n".join(lines),
        "tip": TIP["실거래"],
        "keywords": [dong, "실거래"],
        "sources": [{"title": "국토교통부 아파트 매매 실거래가", "link": "https://rt.molit.go.kr/", "press": "국토교통부"}],
        "chart": {
            "type": "bar", "title": f"최근 {dong} 실거래가", "unit": "억원",
            "labels": [label(d) for d in top], "values": [round(d["amount"] / 10000, 2) for d in top],
            "note": "국토교통부 실거래가 공개시스템. 해제 거래 제외.",
        },
        "comic": {
            "panels": [
                {"speaker": "손님", "line": "요즘 얼마에 팔렸어요?", "scene": "벽에 붙은 단지 배치도 앞"},
                {"speaker": "사장님", "line": f"최근 신고된 거래만 {len(deals)}건이에요.", "scene": "모니터에 실거래 목록이 뜬다"},
                {"speaker": "손님", "line": "제일 비싼 건요?", "scene": "손님이 몸을 앞으로 기울인다"},
                {"speaker": "사장님", "line": f"{cut(hi['apt'], 10)} {round(hi['area'])}㎡. 층과 향도 같이 보셔야 해요.", "scene": "사장님이 펜으로 화면을 짚는다"},
            ],
            "number": eok(hi["amount"]),
            "number_caption": "최근 최고가",
        },
        "why": "국토부 실거래 신고분",
    }
