# PDF 래스터·이미지 입출력

## 래스터 그림의 SMask

- 논문 그림이 래스터 하나로만 들어 있고 축 글자까지 그림 안에 있는 경우가 있음(벡터 drawing·페이지 텍스트 없음). PDF 그림은 벡터인지 래스터인지부터 확인.
- `doc.extract_image(xref)` 로 RGB 만 꺼내면 검은 축·눈금이 사라질 수 있음. 투명 배경과 검은 글자가 RGB 에서는 둘 다 검정이고, 둘을 가르는 불투명도는 soft mask(`/SMask`)에 있음.
- 배경이나 검은 내용이 이상하면 `doc.xref_object(xref)` 에 `/SMask` 가 있는지 확인.
- 축·눈금만 빨리 살릴 때: `page.get_pixmap(..., clip=...)` 이 mask 를 흰 배경에 합성.
- 가는 곡선이나 흰색에 가까운 곡선의 색을 가를 때: 원본 해상도보다 크게 렌더링하지 않음(보간은 정보를 늘리지 않고 색 경계를 흐림). base 와 SMask 를 따로 읽어 원본 픽셀 격자에서 합성:

```python
import fitz                        # pymupdf
import numpy as np

b = fitz.Pixmap(doc, base_xref)    # page.get_images() 의 xref
a = fitz.Pixmap(doc, smask_xref)   # doc.xref_object(base_xref) 의 /SMask 값
b_arr = np.frombuffer(b.samples, dtype=np.uint8).reshape(b.height, b.width, b.n)
a_arr = np.frombuffer(a.samples, dtype=np.uint8).reshape(a.height, a.width, a.n)
alpha = a_arr[..., 0].astype(np.float32) / 255.0
comp = b_arr[..., :3].astype(np.float32) * alpha[..., None] + 255.0 * (1 - alpha[..., None])
```

`fitz.Pixmap(doc, base_xref)` 의 4번째 채널은 255 로 고정된 가짜 alpha — 진짜 alpha 는 SMask xref 에서 읽음.

## 한글·유니코드 경로

- Windows 에서 `cv2.imread`·`cv2.imwrite` 는 경로에 한글 등 non-ASCII 가 있으면 실패. `imwrite` 는 예외 없이 파일만 안 생김(같은 폴더에 `open()`·csv 쓰기는 정상).
- 읽기 `cv2.imdecode(np.fromfile(path, np.uint8), cv2.IMREAD_COLOR)`, 쓰기 `ok, buf = cv2.imencode(".png", img); buf.tofile(path)`.
- 스크립트의 모든 쓰기를 이렇게 바꾸고, 끝나면 출력 폴더에 파일이 실제로 생겼는지 확인. 종료 코드만 믿지 않음.
