# Goldshine

개포동 중개사무소의 아침 부동산 이야기. (이전 이름: 개포 데일리 — 마이클 에디션)

지인용과 같은 엔진에 마이클의 글 원칙(『묘사의 힘』, 짧은 문장, 성인의 아이러니)을 `config.yaml`의 `writing.rules`와 `comic.rules`에 넣은 판입니다.

- 매일 블로그 글 3편과, 같은 기사로 만든 4컷 3개를 추천합니다.
- **글 점수**와 **4컷 점수**를 따로 매깁니다. 5점이 가장 좋습니다.
- 글 점수가 높은 유형(개포단지, 강남시세, 정책·이슈, 실거래)이 더 자주 추천됩니다.
- 4컷 점수가 높은 대본은 다음 날 AI에게 본보기로 보여 줍니다. 직접 고친 4컷에 높은 점수를 주면, 그 고친 대본이 본보기가 됩니다.


매일 아침 7시, 개포동과 강남 부동산 기사를 모아 **오늘의 3편**을 골라 줍니다.
3편은 홈페이지에 올라갑니다. 글 초안, 「개포 사무실 4컷」 만화, 도표가 함께 나옵니다.
1~5점으로 점수를 매기면 다음 날부터 점수가 높은 유형을 더 자주 추천합니다.

- Claude 유료 구독이 필요 없습니다. GitHub 무료 계정이면 됩니다.
- AI 초안은 두 가지 중 하나로 씁니다.
  - **Gemini 무료 키** (Google AI Studio): 돈이 들지 않습니다. 하루 한 번 실행이라 무료 한도 안에 넉넉히 들어갑니다.
  - **Anthropic API 키** (Claude): 쓴 만큼 요금이 나옵니다. 글 품질이 더 안정적입니다.
- 키가 하나도 없으면 **무료판**(기사 요약 + 틀에 맞춘 4컷)으로 돌아갑니다.

---

## 설치 (15분)

### 1. 저장소 만들기
1. github.com에 가입하고 로그인합니다.
2. 오른쪽 위 **+ → New repository**를 누릅니다.
3. Repository name에 `Goldshine`을 입력합니다.
4. **Public**을 고릅니다. 무료 계정은 공개 저장소에서만 홈페이지(GitHub Pages)를 열 수 있습니다.
5. **Create repository**를 누릅니다.

### 2. 파일 올리기
1. `Goldshine.zip`의 압축을 풉니다.
2. 저장소 화면의 **uploading an existing file** 링크를 누릅니다.
3. 풀린 `Goldshine` 폴더 **안의** 항목을 모두 선택해 끌어다 놓습니다.
   `.github` `data` `docs` `scripts` `config.yaml` `requirements.txt` `README.md` `.gitignore`
   - 맥: Finder에서 `Cmd + Shift + .` 를 눌러야 `.github`가 보입니다.
   - 윈도우: 탐색기 **보기 → 숨긴 항목**에 체크합니다.
4. **Commit changes**를 누릅니다.
5. 파일 목록에 `.github`가 있는지 확인합니다. 없으면 아래 「.github가 안 올라갔을 때」를 보세요.

### 3. 홈페이지 켜기
1. 저장소 **Settings → Pages**로 갑니다.
2. Source: **Deploy from a branch**
3. Branch: **main**, 폴더: **/docs** → **Save**
4. 1~2분 뒤 `https://내아이디.github.io/Goldshine/` 에서 예시 화면이 열립니다.

### 4. 키 넣기 (선택)
**Settings → Secrets and variables → Actions → New repository secret**

| 이름 | 없으면 | 받는 곳 |
|---|---|---|
| `GEMINI_API_KEY` | 무료 AI 초안이 빠짐 | aistudio.google.com → Get API key (무료) |
| `ANTHROPIC_API_KEY` | Claude 초안이 빠짐. 두 키가 다 있으면 Claude를 씁니다 | console.anthropic.com (유료) |
| `PUBLIC_DATA_API_KEY` | 실거래 카드가 빠짐 | data.go.kr 「국토교통부_아파트 매매 실거래가 자료」 활용신청 |
| `NAVER_CLIENT_ID`, `NAVER_CLIENT_SECRET` | 네이버뉴스 출처를 건너뜀 | developers.naver.com 「검색」 API |

키 없이 시작해도 됩니다. 구글뉴스와 신문사 RSS만으로도 돌아갑니다.
처음에는 `GEMINI_API_KEY` 하나만 넣는 것을 권합니다.

### 5. 첫 실행
1. **Actions** 탭을 엽니다. 노란 안내가 나오면 **I understand my workflows, go ahead and enable them**을 누릅니다.
2. 왼쪽 **Goldshine (매일 아침)** → **Run workflow** → **Run workflow**.
3. 3~5분 뒤 홈페이지를 새로고침하면 오늘의 3편이 보입니다.

이후로는 매일 오전 7시에 저절로 돕니다.

### 6. 휴대폰 알림 (선택)
GitHub 앱에서 저장소를 열고 **Watch → All activity**를 누릅니다.
매일 아침 「[Goldshine] 날짜」 알림이 옵니다. 그 이슈에 댓글로 `1:4 2:3 3:5 c1:5 c2:3 c3:4`만 달아도 점수가 들어갑니다. 숫자만은 글 점수, `c`가 붙으면 4컷 점수입니다.

---

## 매일 쓰는 법

1. 홈페이지에서 세 편을 봅니다. 카드마다 **4컷 · 도표 · 글** 버튼으로 바꿔 봅니다.
2. 카드마다 **글 점수**와 **4컷 점수**를 1~5점으로 따로 누릅니다. 이유가 있으면 메모 칸에 한 줄 적습니다.
3. 아래 **점수 보내기**를 누릅니다. GitHub 화면이 열리면 **Submit new issue**를 누릅니다. 1~2분 뒤 반영되고, 이슈에 결과 댓글이 달립니다.
4. 올릴 글을 골라 **4컷 저장**, **글 복사**로 블로그에 옮깁니다.

5점은 "이대로 올리겠다", 1점은 "이런 건 다시 보고 싶지 않다"입니다.

### 자료 출처 바꾸기
홈페이지 **자료 출처** 탭에서 추가, 끄기, 삭제를 누릅니다. 점수와 같은 방식으로 GitHub 이슈가 열리고, Submit하면 반영됩니다.

- **구글뉴스 검색어**: 가장 쉽습니다. 단지명이나 "강남구청 재건축"처럼 넣습니다.
- **네이버뉴스 검색어**: 네이버 키가 있어야 합니다.
- **RSS 주소**: 신문사 섹션 RSS를 넣습니다.
- 로그인이 필요한 단지 홈페이지는 자동으로 모을 수 없습니다.

---

## Gemini 무료 키 받기

1. aistudio.google.com 에 구글 계정으로 들어갑니다.
2. 왼쪽 아래 **Get API key → Create API key**를 누릅니다.
3. 나온 키를 복사해 GitHub **Settings → Secrets → Actions**에 `GEMINI_API_KEY`로 넣습니다.
4. 결제 정보를 넣지 않으면 무료 등급으로 남습니다. 한도를 넘으면 그날은 무료판으로 넘어갈 뿐, 요금이 나오지 않습니다.

알아 둘 점
- 무료 등급에서 보낸 내용은 구글이 서비스 개선에 쓸 수 있습니다. 공개 뉴스 기사라 큰 문제는 없지만, 손님 개인정보는 넣지 마세요.
- 무료로 쓸 수 있는 모델과 한도는 구글이 자주 바꿉니다. `config.yaml`의 `gemini.models`를 위에서부터 차례로 시도하고, 모두 막히면 무료판으로 돌아갑니다. Actions 기록에 `Gemini 모델: …`으로 실제 쓴 모델이 찍힙니다.
- 모델 이름이 바뀌면 AI Studio의 모델 목록에서 이름을 복사해 `gemini.models`를 고치세요.
- Gemini는 Claude처럼 답의 모양을 강제하지 못합니다. 그래서 빈 칸이 생기면 채우고, 도표 숫자가 맞지 않으면 도표를 빼고 올립니다.

## 4컷 만화 바꾸기

세 군데를 바꿀 수 있습니다. 위로 갈수록 쉽습니다.

### 1. 오늘 것만 고치기: 홈페이지 「4컷 고치기」
- 카드 아래 **4컷 고치기**를 누릅니다.
- 컷마다 **누가 · 대사 · 장면**, 4컷째 **한마디 · 큰 숫자 · 숫자 설명**을 고칩니다.
- **적용**을 누르면 바로 바뀌고, **4컷 저장**으로 고친 그림을 받습니다.
- 고친 내용은 그 기기 브라우저에만 남습니다. **원래대로**를 누르면 AI가 만든 4컷으로 돌아갑니다.

### 2. 모양 바꾸기: `config.yaml`의 `comic`
```yaml
comic:
  title: 개포동 사무실 4컷   # 만화 맨 위 제목. 예: "마이클 부동산 4컷"
  guest: 손님                # 말풍선 위 이름. 예: "김 여사님"
  boss: 사장님               # 예: "마이클 대표"
  color: "#f2cf3d"           # 4컷째 숫자 칸 색. 예: 하늘색 "#9fd3f2"
```
GitHub 저장소에서 `config.yaml`을 열고 연필 버튼(Edit)으로 고친 뒤 **Commit changes**를 누릅니다. 다음 실행부터 바뀝니다. 바로 보려면 Actions에서 Run workflow를 누르세요.

### 3. 이야기 방식 바꾸기: `config.yaml`의 `comic.rules`
AI에게 주는 4컷 규칙입니다. 평소 말로 적으면 됩니다.
```yaml
  rules: |
    1컷은 손님의 질문 한 줄로 연다.
    4컷 숫자는 기사에서 가장 놀라운 숫자 하나로 고른다.
    3컷에는 손님의 속마음을 괄호로 한 줄 넣는다.
    사장님은 반말을 쓰지 않는다.
```
- 점수 메모와 함께 쓰면 효과가 큽니다. "4컷이 너무 설명조"처럼 메모를 남기면 다음 날 AI가 참고합니다.
- 무료판(키 없음)의 4컷은 정해진 틀이라 이 규칙을 따르지 않습니다. 무료판 대사는 `scripts/free_writer.py`의 `QUESTION`, `SCENE`, `SAY`를 고칩니다.

### 더 깊이 바꾸고 싶을 때
- 인물 그림: `docs/index.html`의 `GUEST`, `BOSS` (SVG 그림)
- 칸 배치, 글자 크기: `docs/index.html`의 `.panel` 스타일
- 4컷 대신 다른 형식(한 장 그림, 지도 일기 등): `scripts/ai_writer.py`의 `SYSTEM` 글과 `docs/index.html`의 `comicNode`를 함께 바꿉니다. Claude에게 "Goldshine 4컷을 ○○ 형식으로 바꿔줘"라고 맡기면 됩니다.

## 어떻게 학습하나요

- 점수는 `data/scores.json`에 쌓입니다. 글 점수(`kind: post`)와 4컷 점수(`kind: comic`)를 따로 저장합니다.
- **4컷 학습**: 4점 이상 받은 4컷 대본 중 최근 3개를 다음 날 AI에게 본보기로 보여 줍니다. 「4컷 고치기」로 고친 뒤 점수를 보내면 고친 대본이 저장되고, 고친 대본을 먼저 본보기로 씁니다. 2점 이하는 "피할 것"으로 메모와 함께 보여 줍니다.
- 4컷 학습은 AI 키(Gemini 무료 키 또는 Anthropic 키)가 있을 때 작동합니다. 무료판 4컷은 정해진 틀입니다.
- 유형(개포단지, 강남시세, 정책·이슈, 실거래)별 평균을 냅니다. 평균이 3점보다 높으면 그 유형의 후보 점수를 올리고, 낮으면 내립니다(0.6~1.6배).
- 같은 키워드가 두 번 이상 점수를 받으면 키워드에도 가산·감산이 붙습니다.
- AI 모드에서는 고득점·저득점 글 제목과 메모를 AI(Claude 또는 Gemini)에게 함께 보여 줍니다. "이런 글이 좋았다"를 보고 고르게 합니다.
- 처음 몇 번의 점수에 너무 흔들리지 않도록 3점을 2개 깔고 평균을 냅니다(`config.yaml`의 `prior_count`).

## 동네 바꾸기

- `config.yaml`: `site`의 이름과 지역, `tiers`의 키워드, `deals`의 법정동 코드와 동 이름을 바꿉니다.
- `data/sources.json`: 구글뉴스 검색어를 그 동네로 바꿉니다. 홈페이지에서 바꿔도 됩니다.

## 비용

- GitHub: 무료. 공개 저장소의 Actions는 무료입니다.
- Gemini: 무료 등급이면 0원입니다.
- Anthropic API: 하루 한 번, 기사 9편을 읽고 3편을 씁니다. 한 달 1만 원 안팎으로 예상합니다(실측 전 추정). console.anthropic.com에서 월 한도를 걸어 두세요.
- 모델은 `config.yaml`의 `ai.model`에서 바꿀 수 있습니다.

## 알아 둘 점

- 저장소가 공개라서 추천 글과 점수 기록을 누구나 볼 수 있습니다. 점수와 출처 변경은 **저장소 주인이 쓴 이슈만** 반영됩니다. API 키는 Secrets에 있어 공개되지 않습니다.
- 처음 들어 있는 11월 8일 추천은 **예시**입니다. 첫 실행 뒤에는 날짜 화살표로 지난 예시를 볼 수 있습니다. 지우려면 `docs/data/days/2026-11-08.json`을 삭제하세요.
- 기사 원문의 저작권은 각 언론사에 있습니다. 블로그에는 요약과 출처 링크를 함께 올리세요.
- 세금·대출 내용은 반드시 세무사와 은행에 확인하세요.

## .github가 안 올라갔을 때
1. 저장소에서 **Add file → Create new file**을 누릅니다.
2. 이름 칸에 `.github/workflows/daily.yml`을 입력합니다.
3. 압축 푼 같은 파일을 메모장으로 열어 전체를 복사해 붙여 넣고 **Commit changes**를 누릅니다.
4. `.github/workflows/feedback.yml`도 같은 방법으로 만듭니다.

## 실행 중 빨간 X가 뜰 때
Actions 탭에서 빨간 X를 누르고, 빨간 단계의 내용을 캡처해 Claude에게 보여 주세요.

## 파일 구성

```
.github/workflows/daily.yml     매일 아침 수집 → 3편 작성 → 홈페이지 갱신 → 알림 이슈
.github/workflows/feedback.yml  점수·출처 이슈를 데이터에 반영
scripts/collect.py              구글뉴스·네이버·RSS·국토부 실거래 수집
scripts/scoring.py              후보 점수와 학습
scripts/ai_writer.py            Claude 또는 Gemini가 3편, 4컷 대본, 도표 작성
scripts/free_writer.py          키가 없을 때 쓰는 무료판 작성기
scripts/make_daily.py           오늘의 3편 만들기
scripts/feedback.py             점수·출처 반영
scripts/build_site.py           홈페이지 데이터 갱신
docs/index.html                 홈페이지
data/sources.json               자료 출처
data/scores.json                점수 기록
config.yaml                     동네, 키워드, 모델 설정
```
