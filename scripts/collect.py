"""매일 아침 기사와 실거래를 모아 data/candidates/날짜.json 에 저장합니다.

출처는 data/sources.json 에 있습니다. 출처 하나가 실패해도 나머지는 계속 모읍니다.
"""
import datetime as dt
import email.utils
import os
import sys
import urllib.parse
import xml.etree.ElementTree as ET

import requests

from common import DATA, KST, clean_text, load_config, norm_title, read_json, short_id, today, write_json

UA = {"User-Agent": "Mozilla/5.0 (compatible; gaepo-daily/1.0)"}
TIMEOUT = 20


def parse_date(s: str) -> str:
    if not s:
        return ""
    try:
        return email.utils.parsedate_to_datetime(s).astimezone(KST).isoformat()
    except (TypeError, ValueError):
        return s


def fetch_rss(url: str, source_name: str) -> list[dict]:
    r = requests.get(url, headers=UA, timeout=TIMEOUT)
    r.raise_for_status()
    root = ET.fromstring(r.content)
    items = []
    for it in root.iter("item"):
        title = clean_text(it.findtext("title", ""))
        src = it.find("source")
        items.append({
            "title": title,
            "link": (it.findtext("link") or "").strip(),
            "summary": clean_text(it.findtext("description", ""))[:400],
            "published": parse_date(it.findtext("pubDate", "")),
            "press": clean_text(src.text) if src is not None and src.text else source_name,
        })
    return items


def fetch_google_news(query: str) -> list[dict]:
    q = urllib.parse.quote(f"{query} when:3d")
    url = f"https://news.google.com/rss/search?q={q}&hl=ko&gl=KR&ceid=KR:ko"
    items = fetch_rss(url, "구글뉴스")
    for it in items:
        # 구글뉴스 제목은 "제목 - 언론사" 형식
        if " - " in it["title"]:
            head, press = it["title"].rsplit(" - ", 1)
            it["title"], it["press"] = head.strip(), press.strip()
        if it["summary"].startswith(it["title"]):
            it["summary"] = ""
    return items


def fetch_naver_news(query: str) -> list[dict]:
    cid = os.environ.get("NAVER_NEWS_CLIENT_ID") or os.environ.get("NAVER_CLIENT_ID")
    sec = os.environ.get("NAVER_NEWS_CLIENT_SECRET") or os.environ.get("NAVER_CLIENT_SECRET")
    if not (cid and sec):
        raise RuntimeError("네이버 키 없음 (건너뜀)")
    r = requests.get(
        "https://openapi.naver.com/v1/search/news.json",
        params={"query": query, "display": 50, "sort": "date"},
        headers={"X-Naver-Client-Id": cid, "X-Naver-Client-Secret": sec},
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    out = []
    for it in r.json().get("items", []):
        link = it.get("originallink") or it.get("link", "")
        host = urllib.parse.urlparse(link).netloc.replace("www.", "")
        out.append({
            "title": clean_text(it.get("title", "")),
            "link": link,
            "summary": clean_text(it.get("description", ""))[:400],
            "published": parse_date(it.get("pubDate", "")),
            "press": host,
        })
    return out


def fetch_source(src: dict) -> list[dict]:
    kind = src.get("type")
    if kind == "google_news":
        return fetch_google_news(src["query"])
    if kind == "naver_news":
        return fetch_naver_news(src["query"])
    if kind == "rss":
        return fetch_rss(src["url"], src.get("name", ""))
    raise RuntimeError(f"모르는 출처 종류: {kind}")


# ---------- 국토부 실거래 ----------

def fetch_deals(cfg: dict, day: str) -> list[dict]:
    key = os.environ.get("PUBLIC_DATA_API_KEY")
    if not key:
        raise RuntimeError("공공데이터 키 없음 (건너뜀)")
    key = urllib.parse.unquote(key)  # 인코딩된 키를 넣어도 두 번 인코딩되지 않게
    d = cfg["deals"]
    base = dt.date.fromisoformat(day)
    months = sorted({(base - dt.timedelta(days=x)).strftime("%Y%m") for x in (0, 31, 62)})
    url = "https://apis.data.go.kr/1613000/RTMSDataSvcAptTrade/getRTMSDataSvcAptTrade"
    rows = []
    for ym in months:
        r = requests.get(url, params={"serviceKey": key, "LAWD_CD": d["lawd_cd"], "DEAL_YMD": ym,
                                      "numOfRows": 1000, "pageNo": 1}, timeout=TIMEOUT)
        r.raise_for_status()
        root = ET.fromstring(r.content)
        for it in root.iter("item"):
            g = lambda *names: next((it.findtext(n).strip() for n in names if it.findtext(n)), "")
            dong = g("umdNm", "법정동")
            if d["dong"] not in dong:
                continue
            if g("cdealType", "해제여부") in ("O", "Y"):
                continue  # 해제된 거래 제외
            y, m, dd = g("dealYear", "년"), g("dealMonth", "월"), g("dealDay", "일")
            amount = int(g("dealAmount", "거래금액").replace(",", "") or 0)  # 만원
            rows.append({
                "date": f"{y}-{int(m):02d}-{int(dd):02d}",
                "apt": g("aptNm", "아파트"),
                "area": float(g("excluUseAr", "전용면적") or 0),
                "floor": g("floor", "층"),
                "amount": amount,
            })
    rows.sort(key=lambda x: x["date"], reverse=True)
    return rows


def main() -> int:
    cfg = load_config()
    day = today()
    sources = read_json(DATA / "sources.json", [])
    excl = cfg.get("exclude", [])
    seen, cands, log = set(), [], []

    for src in sources:
        if not src.get("enabled", True):
            continue
        try:
            items = fetch_source(src)
        except Exception as e:  # 출처 하나 실패는 전체를 멈추지 않습니다
            log.append({"source": src["id"], "ok": False, "error": str(e)[:200]})
            print(f"  ✗ {src['name']}: {e}", file=sys.stderr)
            continue
        inc = src.get("include") or []
        n = 0
        for it in items:
            text = it["title"] + " " + it["summary"]
            if not it["title"] or any(x in text for x in excl):
                continue
            if inc and not any(w in text for w in inc):
                continue
            key = norm_title(it["title"])[:28]
            if key in seen:
                continue
            seen.add(key)
            it.update(id=short_id(it["title"], it["link"]), source_id=src["id"], kind="news")
            cands.append(it)
            n += 1
        log.append({"source": src["id"], "ok": True, "count": n})
        print(f"  ✓ {src['name']}: {n}건")

    deals = []
    try:
        deals = fetch_deals(cfg, day)
        print(f"  ✓ 실거래: {len(deals)}건")
        log.append({"source": "molit", "ok": True, "count": len(deals)})
    except Exception as e:
        print(f"  ✗ 실거래: {e}", file=sys.stderr)
        log.append({"source": "molit", "ok": False, "error": str(e)[:200]})

    write_json(DATA / "candidates" / f"{day}.json", {"date": day, "news": cands, "deals": deals, "log": log})
    print(f"후보 {len(cands)}건, 실거래 {len(deals)}건 저장")
    return 0


if __name__ == "__main__":
    sys.exit(main())
