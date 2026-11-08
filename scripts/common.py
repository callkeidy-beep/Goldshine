"""공통 도구: 경로, 설정, 날짜, JSON 읽고 쓰기."""
import datetime as dt
import hashlib
import json
import os
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
DOCS = ROOT / "docs"
KST = dt.timezone(dt.timedelta(hours=9))


def today() -> str:
    """오늘 날짜(한국 시간). TODAY 환경변수로 바꿔 시험할 수 있습니다."""
    return os.environ.get("TODAY") or dt.datetime.now(KST).strftime("%Y-%m-%d")


def load_config() -> dict:
    with open(ROOT / "config.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


def read_json(path: Path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def clean_text(s: str) -> str:
    s = re.sub(r"<[^>]+>", " ", s or "")
    for a, b in (("&quot;", '"'), ("&#39;", "'"), ("&amp;", "&"), ("&lt;", "<"), ("&gt;", ">"), ("&nbsp;", " "), ("&middot;", "·")):
        s = s.replace(a, b)
    return re.sub(r"\s+", " ", s).strip()


def short_id(*parts: str) -> str:
    return hashlib.sha1("|".join(parts).encode("utf-8")).hexdigest()[:10]


def norm_title(t: str) -> str:
    """중복 판정용 제목: 언론사 꼬리, 괄호, 기호를 지웁니다."""
    t = re.sub(r"\s[-|]\s[^-|]+$", "", t)
    t = re.sub(r"[\[\(【<].*?[\]\)】>]", "", t)
    return re.sub(r"[^0-9A-Za-z가-힣]", "", t)
