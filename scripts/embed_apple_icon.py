"""배포용 빌드 단계: design/shared/icons/apple-touch-icon.datauri.txt를 읽어 index.html의 apple-touch-icon 링크에 넣고 검증한다.

index.html에는 __APPLE_TOUCH_ICON__ 자리만 두고, 이 스크립트가 배포 직전에 실제 data 주소로 바꾼다.
(iOS가 파일 주소의 apple-touch-icon을 받아 오지 못하고 회색 글자 타일을 보여 주는 문제를 피하려고 data 주소를 쓴다.)

검증: head에 apple-touch-icon 링크가 1개, HTML 속 data 주소가 datauri.txt와 같고, 디코딩한 PNG의
서명, 모든 조각의 CRC, 크기(180x180)가 맞아야 한다. 하나라도 틀리면 실패한다.

    python3 scripts/embed_apple_icon.py          # 배포 워크플로에서만 실행. 로컬에서 돌렸다면 git checkout index.html
"""
import base64, re, struct, sys, zlib
from pathlib import Path

root = Path(__file__).resolve().parent.parent
PLACEHOLDER = '__APPLE_TOUCH_ICON__'
uri_file = root / 'design' / 'shared' / 'icons' / 'apple-touch-icon.datauri.txt'
page = root / 'index.html'


def fail(msg):
    sys.exit('실패: ' + msg)


if not uri_file.exists():
    fail(f'{uri_file.relative_to(root)}가 없습니다. design/shared가 동기화되었는지 확인하세요.')
uri = uri_file.read_text(encoding='utf-8').strip()
html = page.read_text(encoding='utf-8')
if html.count(PLACEHOLDER) != 1:
    fail(f'index.html에 {PLACEHOLDER} 자리가 정확히 1개 있어야 합니다(현재 {html.count(PLACEHOLDER)}개).')
html = html.replace(PLACEHOLDER, uri)
page.write_text(html, encoding='utf-8')

# ---- 검증: 빌드한 HTML에서 다시 읽어 확인 ----
built = page.read_text(encoding='utf-8')
links = re.findall(r'<link rel="apple-touch-icon"[^>]*>', built)
if len(links) != 1:
    fail(f'apple-touch-icon 링크가 {len(links)}개입니다(1개여야 함).')
m = re.search(r'href="(data:image/png;base64,[^"]+)"', links[0])
if not m:
    fail('apple-touch-icon 링크에 data 주소가 없습니다.')
if m.group(1) != uri:
    fail('HTML 속 data 주소가 datauri.txt와 다릅니다.')
png = base64.b64decode(m.group(1).split(',', 1)[1], validate=True)
if png[:8] != b'\x89PNG\r\n\x1a\n':
    fail('PNG 서명이 틀립니다.')
i, kinds = 8, []
while i < len(png):
    n = struct.unpack('>I', png[i:i + 4])[0]
    kind, body = png[i + 4:i + 8], png[i + 8:i + 8 + n]
    crc = struct.unpack('>I', png[i + 8 + n:i + 12 + n])[0]
    if zlib.crc32(kind + body) & 0xffffffff != crc:
        fail(f'{kind.decode()} 조각의 CRC가 틀립니다.')
    kinds.append(kind.decode())
    i += 12 + n
w, h = struct.unpack('>II', png[16:24])
if (w, h) != (180, 180):
    fail(f'크기가 {w}x{h}입니다(180x180이어야 함).')
print(f'apple-touch-icon 삽입과 검증 완료: {w}x{h}, 조각 {kinds}, data 주소 {len(uri)}자')
