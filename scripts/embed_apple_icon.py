"""icons/apple-touch-icon.png를 base64로 바꿔 index.html의 apple-touch-icon 링크에 직접 넣는다.

iOS가 파일 주소의 apple-touch-icon을 받아 오지 못하고 회색 글자 타일을 보여 주는 문제를 피하려고
data 주소를 쓴다. 아이콘 이미지를 바꾼 뒤에는 이 스크립트를 다시 실행할 것:
    python3 scripts/embed_apple_icon.py
PNG는 IHDR, IDAT, IEND 같은 기본 조각만 있는 표준 PNG여야 한다(C2PA 같은 메타데이터 제거).
"""
import base64, re, struct, sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent
png = (root / 'icons' / 'apple-touch-icon.png').read_bytes()

# 기본 조각 외의 것이 있으면 멈춘다
chunks, i = [], 8
while i < len(png):
    n = struct.unpack('>I', png[i:i + 4])[0]
    chunks.append(png[i + 4:i + 8].decode())
    i += 12 + n
extra = [c for c in chunks if c not in ('IHDR', 'PLTE', 'IDAT', 'IEND')]
if extra:
    sys.exit(f'PNG에 메타데이터 조각이 있습니다: {extra}. 먼저 제거하세요.')

b64 = base64.b64encode(png).decode()
link = f'<link rel="apple-touch-icon" sizes="180x180" href="data:image/png;base64,{b64}">'
page = root / 'index.html'
html = page.read_text(encoding='utf-8')
new, n = re.subn(r'<link rel="apple-touch-icon"[^>]*>', lambda m: link, html, count=1)
if n != 1:
    sys.exit('index.html에서 apple-touch-icon 링크를 찾지 못했습니다.')
page.write_text(new, encoding='utf-8')
print(f'apple-touch-icon을 data 주소로 넣었습니다 ({len(b64)}자)')
