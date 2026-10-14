# 적용된 공통 디자인

- 공통 파일: design/shared (자동 동기화). 이 폴더는 직접 고치지 않는다.
- 불러오는 방식: 빌드 없는 정적 사이트(GitHub Pages `/on-air-english/`)라 `index.html`이 앞에 빗금 없는 상대 경로로 직접 링크한다(`design/shared/tokens.css`, `design/shared/symbols.js`, favicon `design/shared/icons/script.svg`). manifest icons도 `design/shared/icons/script-192.png`, `script-512.png`.
- apple-touch-icon: `index.html`에는 `__APPLE_TOUCH_ICON__` 자리만 두고, 배포 워크플로가 `scripts/embed_apple_icon.py`로 `design/shared/icons/apple-touch-icon.datauri.txt`를 읽어 넣은 뒤 검증한다(head에 1개, 디코딩해 datauri.txt와 같은지, PNG 서명과 CRC, 180x180).
- 사용 중인 공통 CSS: design/shared/tokens.css (VERSION 파일 참조)
- 적용한 CHANGELOG 번호: 002, 003, 004, 005, 006, 009, 011, 012, 013
- 하단 바 잘림 수정(013 보완): 소스에서 원인(100vh 상자, 안쪽 스크롤 상자 등)은 찾지 못했다. 가로 스크롤 밑줄 탭의 세로 스크롤 방지, 서비스 워커가 옛 파일을 쓰지 않게 서버 확인(`cache: 'no-cache'`), 기기에서 값을 읽는 진단 창(`?layout-debug`)을 추가했다.
