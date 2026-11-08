"""출처 점검: 후보 출처가 실제로 기사를 가져오는지 확인합니다. 데이터는 바꾸지 않습니다.

사용: python check_sources.py ../tests/source_candidates.json
"""
import json
import sys

from collect import fetch_source


def main() -> int:
    path = sys.argv[1] if len(sys.argv) > 1 else "../tests/source_candidates.json"
    for src in json.load(open(path, encoding="utf-8")):
        try:
            items = fetch_source(src)
            inc = src.get("include") or []
            if inc:
                items = [i for i in items if any(w in i["title"] + i.get("summary", "") for w in inc)]
            sample = " | ".join(i["title"][:40] for i in items[:2])
            print(f"OK   {src['id']:<18} {len(items):>3}건  {sample}")
        except Exception as e:
            print(f"FAIL {src['id']:<18} {str(e)[:120]}")
    return 0


if __name__ == "__main__" and "--resolve" not in sys.argv:
    sys.exit(main())


def check_resolve(query: str = "개포동", n: int = 6) -> None:
    """구글뉴스 링크를 원문 주소로 바꾸고 본문을 읽을 수 있는지 확인합니다."""
    import gnews
    from ai_writer import article_text
    from collect import fetch_google_news
    for it in fetch_google_news(query)[:n]:
        real = gnews.resolve(it["link"])
        text = article_text(real) if real else ""
        print(f"{'RESOLVED' if real else 'NOLINK  '} {len(text):>5}자  {it['title'][:30]}  →  {real[:80]}")


if __name__ == "__main__" and "--resolve" in sys.argv:
    check_resolve()
