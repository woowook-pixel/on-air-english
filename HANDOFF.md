# On Air English — 작업 인계

> 사용자와는 **한국어로** 소통한다. 답변은 짧고 핵심 위주로(안내 문구·설명이 길면 싫어함). 큰 디자인 변경은 시안을 먼저 보여주고 고르게 한다.

## 이 프로젝트

영어 뉴스로 듣기·읽기를 공부하는 웹앱(PWA). 사용자는 아이폰 홈 화면에 설치해서 쓴다.

- 사이트: https://woowook-pixel.github.io/on-air-english/
- 배포: GitHub Pages (Source = GitHub Actions)
- Cloudflare(workers.dev)로 도메인 분리를 시도했지만 잠금 화면 문제는 그대로여서 철회했다. 다시 시도할 필요 없음.
- 서버·빌드 도구 없음. `index.html` 하나(HTML+CSS+JS)와 JSON 데이터.

### 구조

| 파일 | 역할 |
|---|---|
| `index.html` | 앱 전체. **아이팟 클래식 스타일**(위는 LCD 화면, 아래는 클릭휠). 메뉴(뉴스 듣기 🎧 / 기사 읽기 📄 / 지난 목록 / 저장함 / 지금 재생 중, 줄 앞 아이콘으로 음성과 기사를 구분) → 목록 → 상세·재생 화면의 스택 구조. 휠을 돌리면 선택·스크롤, MENU는 뒤로, ◀◀▶▶는 15초 이동(▶▶ 길게 누르면 다음 방송), 가운데 버튼은 선택. 속도 조절 기능은 사용자 요청으로 뺐다. 시안은 `mockups/` |
| `scripts/update.py` | 매일 새 목록 생성 → `data/current.json`, 이전 목록은 `data/archive/<id>.json` + `index.json`, 이미 쓴 항목은 `data/state.json` |
| `.github/workflows/update.yml` | 매일 06:00 KST에 `update.py` 실행 → 커밋 → Pages 배포. 수동 실행 시 `force` 옵션으로 즉시 새 목록 |
| `sw.js` | 앱 화면 캐시(네트워크 우선). 화면을 바꾸면 `CACHE` 버전을 올릴 것 |
| `manifest.webmanifest`, `icons/` | 설치용 |

### 콘텐츠 소스 (현재)

- **뉴스 듣기 5개**: BBC Global News Podcast, NPR News Now, NPR Up First, BBC 6 Minute English, NPR Short Wave의 최신 편. 방송사 서버의 파일을 그대로 재생한다. 청취 집계용 리다이렉트(podtrac, tritondigital 등)는 **우회하지 않는다**(방송사 통계 보호).
- **헤드라인 6개**: BBC World/Science/Technology, NPR News/World RSS의 제목·요약·썸네일. 본문은 저작권 때문에 앱에 싣지 않고 원문 링크로 보낸다.

## 지금까지 결정된 것 (되돌리지 말 것)

- VOA·NASA·LibriVox·Wikipedia 등 이전 소스는 사용자가 "별로"라고 해서 BBC·NPR로 교체했다.
- **The Conversation은 쓰지 않는다**(재게시 조건: 추적 픽셀 필수·편집 금지·체계적 재게시 금지).
- 무료 사전 API로 단어 풀이 붙이는 기능은 느려서 사용자가 제거를 요청했다. 다시 넣지 말 것.
- 갱신 주기는 2일 → **매일**로 바꿨다.
- 외부에서 받은 텍스트는 `textContent`/DOM으로만 넣는다(XSS 방지). `innerHTML`은 고정 아이콘 SVG에만 쓴다.

## 알려진 문제

- 아이폰에서 홈 화면 웹앱이 여러 개 있으면, 잠금 화면 재생창을 눌렀을 때 **다른 웹앱이 열린다**(iOS 문제). 다른 웹앱을 지우자 해결됐다. 다시 생기면 이것부터 의심할 것.
- 뉴스 팟캐스트는 재생 시작까지 2~4초 걸린다(해외 서버 + 집계 리다이렉트). 앱 쪽에선 `preconnect`만 해 두었다.
- 저장소 git 이력에 The Conversation 기사 본문이 남아 있다. 지우려면 강제 푸시가 필요해서 사용자 결정 전까지 그대로 둔다.

## 남은 할 일

- 없음. 학습 기능(하루 루틴·번역·단어장·퀴즈·듣기 연습)은 사용자가 **추가하지 않고 지금 그대로 유지**하기로 했다. Claude API 번역·퀴즈 생성도 필요 없다고 했으니 `ANTHROPIC_API_KEY`를 요구하지 말고 다시 제안하지 말 것.

## 작업 방법

- 시작 전에 항상 `git pull` (봇이 매일 `main`에 커밋한다).
- 로컬 확인: `python -m http.server 8765` 후 `http://localhost:8765/` (휴대폰 크기 375×812로 확인). 서비스 워커가 옛 화면을 붙잡고 있으면 등록 해제 후 새로고침.
- 목록 생성 시험: `pip install requests && python scripts/update.py --force` — 시험으로 만든 목록이 아카이브에 남지 않게 주의(`data/archive/index.json`, 해당 JSON, `data/current.json`을 정리).
- 커밋 메시지는 영어, 끝에 `Co-Authored-By: Claude <noreply@anthropic.com>` 형식의 공동 작성자 줄.
- 푸시하면 Actions가 자동 배포한다. 배포 결과는 Actions 탭에서 확인.

> 참고: 이 파일도 Pages로 공개된다. 비밀값이나 개인 정보는 적지 말 것.
