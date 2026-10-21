# Script (구 On Air English) — 작업 인계

> 이 문서는 다른 Claude 계정의 새 세션이 이어받도록 쓴 인계 문서다. 시작할 때 이것부터 읽을 것.
> 이 파일도 Pages로 공개된다. 비밀값이나 개인 정보는 적지 말 것.

## 0. 사용자와 일하는 방법

- **한국어**로 소통한다. 답변은 짧고 핵심 위주. 긴 안내문·설명은 싫어한다.
- 사용자는 코드를 직접 읽지 않는 **바이브 코딩 초보**다. 원리를 물으면 일상 비유와 실제 예시로 쉽고 자세히 설명한다.
- **큰 디자인 변경은 시안(목업)을 먼저 보여 주고 고르게 한다.** 코드부터 짜지 않는다.
- 사용자가 다른 앱 세션과 공유하는 **공통 지시문**(CHANGELOG 번호별)을 붙여 넣는다. 형식은 늘 "0번 먼저 확인하고 보고 → 진행 → 로컬 확인 → `design/APPLIED.md` 기록 → 새 브랜치에서 PR". 0번 조건이 안 맞으면 **멈추고 알린다**. 지시에 없는 일은 하지 않고, 지시와 다르게 한 곳은 PR 본문과 보고에 적는다.
- **git 흐름**: `main`에 직접 푸시하지 않는다. 항상 **최신 `origin/main`에서 새 브랜치**를 따서 푸시하고 **PR만** 연다. 사용자가 PR을 열면 바로 직접 머지한다(머지는 사용자가 한다). 머지된 브랜치를 재사용하지 말 것. 다른 작업 브랜치 위에 PR을 쌓지 않는다.
- 커밋 메시지는 영어, 끝에 공동 작성자 줄. PR 본문 끝에도 안내된 출처 줄을 붙인다. GitHub는 `gh`가 아니라 **GitHub MCP 도구**(`mcp__github__*`)로 다룬다(필요하면 ToolSearch로 불러올 것).

## 1. 프로젝트 목적

영어 뉴스로 듣기·읽기를 공부하는 웹앱(PWA). 사용자는 아이폰 홈 화면에 설치해서 쓴다.

- 사이트: https://woowook-pixel.github.io/on-air-english/ (저장소 `woowook-pixel/on-air-english`)
- 배포: GitHub Pages (Source = GitHub Actions). `main`에 푸시되면 자동 배포.
- 서버·빌드 도구 없는 정적 사이트. `index.html` 하나(HTML+CSS+JS)와 JSON 데이터.
- 앱 이름은 **Script**(구 On Air → On Air Classic → Script). 개인 앱 패밀리(Bite, Script, Wayly, Lexi, Pitch, Strum)의 공통 디자인을 따른다.

### 콘텐츠 소스

- **뉴스 듣기 5개**: BBC Global News Podcast, NPR News Now, NPR Up First, BBC 6 Minute English, NPR Short Wave의 최신 편. 방송사 서버 파일을 그대로 재생한다. 청취 집계용 리다이렉트(podtrac, tritondigital 등)는 **우회하지 않는다**(방송사 통계 보호).
- **헤드라인 6개**: BBC World/Science/Technology, NPR News/World RSS의 제목·요약·썸네일. 본문은 저작권 때문에 싣지 않고 원문 링크로 보낸다.

## 2. 구조

| 파일 | 역할 |
|---|---|
| `index.html` | 앱 전체. 하단 탭 3개 **듣기 / 읽기 / 보관함**(보관함 안 밑줄 탭: 지난 목록, 저장함). 상단 바(`.pf-header`)는 최상위 화면에서 왼쪽 `SCRIPT`+캐릭터 GIF, 오른쪽 "설정", 하위 화면은 왼쪽 "← 목록". 탭바 위에 재생 중일 때만 미니 플레이어, 누르면 재생 화면(−15 −5 PLAY +5 +15 텍스트 버튼, 진행 위치 막대, 다음 방송·원문 열기·저장 행). 화면 전환은 `show()`/`setView()` 스택과 `history`로 한다. 설정 화면에는 "클릭 소리" 한 줄뿐. 새 버전 알림 띠(`#update`), 기기 진단 창(주소 뒤 `?layout-debug`)이 있다. 속도 조절 기능은 없다 |
| `scripts/update.py` | 매일 새 목록 생성 → `data/current.json`, 이전 목록은 `data/archive/<id>.json` + `index.json`, 이미 쓴 항목은 `data/state.json` |
| `scripts/embed_apple_icon.py` | 배포 단계에서 `design/shared/icons/apple-touch-icon.datauri.txt`를 읽어 `index.html`의 `__APPLE_TOUCH_ICON__` 자리에 넣고 검증(링크 1개, 파일과 동일, PNG 서명·CRC, 180×180) |
| `.github/workflows/update.yml` | 매일 06:00 KST(cron `0 21 * * *`)에 `update.py` → 데이터 커밋 → **Stamp version**(`version.json`과 `APP_VERSION`을 커밋 SHA로) → **Embed apple-touch-icon** → Pages 배포. 수동 실행 `force` 옵션으로 즉시 새 목록. `push` 때도 배포 |
| `version.json` | 저장소에는 없고 배포 때만 생긴다. 앱이 열릴 때·돌아올 때·5분마다 받아 `APP_VERSION`과 다르면 "새 버전이 있습니다" 띠를 띄운다 |
| `sw.js` | 서비스 워커. 같은 출처 파일은 네트워크 우선(`cache: 'no-cache'`), 실패하면 캐시. `version.json`은 가로채지 않는다. 화면을 바꾸면 `CACHE`(지금 `script-v22`)를 올릴 것 |
| `manifest.webmanifest` | 설치용. icons는 `design/shared/icons/script-192.png`, `script-512.png` |
| `design/shared/` | **다른 저장소(personal-design)에서 자동 동기화**되는 공통 파일(`tokens.css`, `symbols.js`, `characters/`, `icons/`, 문서). 동기화 PR("공통 디자인 동기화")이 자동으로 올라오고 머지된다. **직접 고치지 말 것.** 앱만의 예외 스타일은 `index.html`의 앱 CSS에 둔다 |
| `design/SCRIPT.md` | 이 앱 전용 화면 기준 |
| `design/APPLIED.md` | 적용한 공통 CHANGELOG 번호 기록 — 현재 **002, 003, 004, 005, 006, 009, 011, 012, 013**. 새 번호를 적용하면 여기에 추가 |

`index.html` 안의 **`__APP_VERSION__`, `__APPLE_TOUCH_ICON__` 자리는 지우지 말 것**(배포 때 채워진다). 로컬에서 `embed_apple_icon.py`를 돌렸다면 `git checkout index.html`로 되돌린다.

## 3. 확정된 결정 (되돌리지 말 것)

- 학습 기능(하루 루틴·번역·단어장·퀴즈·듣기 연습)은 **추가하지 않는다**. Claude API 번역·퀴즈도 필요 없다고 했으니 `ANTHROPIC_API_KEY`를 요구하거나 다시 제안하지 말 것.
- VOA·NASA·LibriVox·Wikipedia 등 이전 소스는 "별로"라서 BBC·NPR로 교체했다. **The Conversation은 쓰지 않는다**(재게시 조건 위반). 무료 사전 API 단어 풀이는 느려서 제거했다.
- 갱신 주기는 **매일**.
- 아이팟 스킨·클릭휠·속도 조절은 **제거했고 옵션으로도 남기지 않는다**. 디자인은 패밀리 공통(흑백, 모서리 0, 그림자·그라데이션 없음, 다크 모드 없음). Ember(#FF7A3D)는 "지금 재생 중" 표시에만 쓴다.
- 외부에서 받은 텍스트는 `textContent`/DOM으로만 넣는다(XSS 방지). `innerHTML`은 고정 아이콘 SVG에만 쓴다.
- Cloudflare(workers.dev)로 도메인을 분리해 봤지만 잠금 화면 문제가 그대로여서 **철회**했다. 다시 시도할 필요 없다.
- 홈 화면 아이콘(apple-touch-icon)은 **파일 주소가 아니라 data 주소로 배포 때 HTML에 넣는다**. iOS가 파일 주소 아이콘을 못 받아 회색 글자 타일이 나오는 문제를 피하려는 것이다(다른 앱 사례 포함). 파일 주소로 되돌리지 말 것. 아이콘이 안 보이면 가장 먼저 의심할 것.
- 앱 아이콘 파일과 캐릭터는 중앙(`design/shared`) 것을 쓴다. 앱 자체 `icons/`는 지웠다.

## 4. 열린 PR과 진행 중인 일

**현재 열린 PR: 없음** (이 인계 PR 제외). 진행 중인 코드 변경도 없다.

| PR | 목적 | 상태 |
|---|---|---|
| 이 HANDOFF 갱신 PR | 계정 이전용 인계 문서 정리 (HANDOFF.md만 변경) | 머지 예정 |
| #29 주황색 점 제거 | 미니 플레이어·재생 화면 "음성" 라벨의 주황 점 제거 | **폐기(닫음, 머지 안 됨)**. 사용자가 말한 "주황색 점"은 앱이 아니라 Claude 앱 화면의 표시였다. 앱은 그대로 둔다 |
| #1~#28 | 아래 요약 | 모두 머지됨(닫힘) |

머지된 PR 요약(참고): #1~#3 아이팟 디자인·음성/기사 구분·이름 On Air Classic / #4 Script 패밀리 디자인 전환 / #5 공통 CSS 중앙 링크 / #6 CHANGELOG 002(상단 헤더) / #7·#8·#10 홈 아이콘(PNG 정리, data 주소, 006) / #9 CHANGELOG 003·004(새 버전 띠, 아이콘) / #10 005(기호) / #15 `design/shared` 전환 + 009(제목 줄) / #18 011 / #21 012 / #25 013(탭바·캐릭터 크기, 알림 띠와 미니 플레이어 겹침 수정) / #26 하단 바 잘림 대응(안쪽 스크롤 방지, 파일 재확인, 진단 창) / #11~#14, #16, #17, #19, #20, #22~#24, #27, #28 공통 디자인 자동 동기화.

### 다음 할 일

- 지금 정해진 것은 없다. 사용자가 새 CHANGELOG 번호나 요청을 주면 위 "작업 방법"대로 처리한다.
- **하단 바 잘림(아이폰 홈 화면 앱)**: 사용자가 증상을 보고했고 #26을 머지한 뒤 "다 됐어"라고 해서 종료된 것으로 본다. 다만 소스에서 원인을 찾지 못했고 재현도 못 했다. 재발하면 홈 화면 앱을 `.../on-air-english/?layout-debug`로 열어 읽기창(`visualViewport`, `inner` 높이, 안전 영역, 탭바 위치) 캡처를 요청해 그 값으로 고친다.
- 실제 아이폰에서의 확인(홈 화면 아이콘, 기호 모양, 알림 띠 모양)은 사용자가 직접 한다.

## 5. 주의할 점

- **아이폰 잠금 화면 재생창**을 누르면 다른 웹앱이 열리는 건 iOS 문제다. 코드·도메인으로 못 고친다(앱 삭제·재설치, 다른 웹앱 삭제로 해결된 적 있다). 다시 생기면 이것부터 의심할 것.
- 이 클라우드 세션에서는 **배포 사이트(github.io)와 중앙 디자인 주소, 방송사 서버에 접속할 수 없다**. 그래서 실제 재생·배포본 확인은 못 한다. 확인은 가상 브라우저(Playwright + `/opt/pw-browsers`의 Chromium)로 390×844 화면에서 하고, 못 한 것은 PR 본문에 "못 한 것"으로 적는다.
- 로컬 확인: `python3 -m http.server <포트>` 후 접속. 서버 종료는 **포트로**(`lsof -ti:<포트> | xargs -r kill`). `pkill`로 이름을 찾아 죽이면 실행 중인 셸까지 종료된다(실제로 겪음). 서비스 워커가 옛 화면을 붙잡으면 등록 해제 후 새로고침.
- 목록 생성 시험: `pip install requests && python scripts/update.py --force` — 시험 목록이 아카이브에 남지 않게 정리(`data/archive/index.json`, 해당 JSON, `data/current.json`).
- 배포 워크플로는 `concurrency: pages`라서 **예약 실행이 대기열에 오래 걸려 있으면 뒤의 푸시 배포가 막힌다**(겪음). Actions에서 막힌 실행을 취소하면 풀린다.
- 홈 화면 앱은 서비스 워커·브라우저 캐시 때문에 옛 화면이 남을 수 있다. 완전히 종료 후 다시 열거나, 삭제 후 Safari에서 다시 추가한다. 새 버전 띠가 이를 알려 준다. 매일 아침 목록 갱신 커밋도 SHA를 바꾸므로 코드가 그대로여도 하루 한 번 띠가 뜰 수 있다.
- 저장소 git 이력에 The Conversation 기사 본문이 남아 있다. 지우려면 강제 푸시가 필요해서 사용자 결정 전까지 그대로 둔다.
- 원격 브랜치 `fix/remove-orange-dot`는 PR #29를 닫을 때 남았고, 이 환경에서는 삭제가 막혀 있다. 저장소 Branches 화면에서 지워도 된다(앱 영향 없음). 머지된 옛 브랜치들(`design/*`, `fix/*`, `claude/fervent-euler-y5rbju`)도 남아 있다.
- 저장함은 기기 브라우저(localStorage)에만 저장된다. 주소(도메인)가 바뀌면 비어 보인다.
- 시험용 스크립트와 스크린샷은 세션 임시 폴더에만 있어서 이전되지 않는다. 필요하면 새로 만든다.
