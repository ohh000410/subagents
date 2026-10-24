# PPT 네이티브 도형으로 그림 그리기 — 라우팅 인덱스

**이 파일은 항상 읽음.** 나머지는 모드에 따라 필요한 것만 읽음.

**적용 범위**: `python-pptx` 로 도형을 생성하고 필요 시 win32com(COM)으로 후처리하는
모든 작업. 데이터 플롯은 관할 외(Origin/matplotlib).

절대 규칙(입체는 네이티브 3D 만, `Depth=0` 시트 포함)·환경·입출력 계약은 **에이전트
본문이 소유.** 이 인덱스는 지식 라우팅만 함.

## ★ 먼저 모드를 정함

| | **창작** | **재현** |
|---|---|---|
| 입력 | 실제 치수(mm·in) + 내가 고른 카메라 | 원본 이미지 |
| 방향 | `project3d` **순방향** — 치수 → 화면 | `solve_3d` **역방향** — 화면 → 카메라·치수 |
| 카메라 | **하나를 전 층에 공유**(구조적으로 일치) | 요소마다 역산(실측상 RotX 60~82 로 흩어짐) |
| 측정 | **없음** | 작업의 대부분이자 오류의 최대 원인 |
| 읽을 것 | 이 파일 + `pptx_3d_core.md` + `pptx_creation.md` | 이 파일 + `pptx_3d_core.md` + `pptx_reproduction.md` |

호출자가 모드를 안 밝혔으면 **원본 이미지 경로가 있으면 재현, 없으면 창작**.
애매하면 호출자에게 물음.

## 파일

| 파일 | 언제 |
|---|---|
| **이 파일** | 항상 |
| `pptx_3d_core.md` | 입체를 만들면 항상. 투영 모델 · 단차 · 그룹 · 진짜 구멍 |
| `pptx_api_dict.md` | **조회용.** 3D 속성·enum·병합 상수·XML 주입(투명도·그라디언트)·python-pptx 함정. 통째로 읽지 마라 |
| `pptx_creation.md` | 창작 모드 |
| `pptx_reproduction.md` | 재현 모드. 좌표계(원본 px) · 측정 방법론 · 원본 대조 |
| `snippets/pptx_frame.py` | **복사해서 소유한 뒤 import.** 복사 직후 self-test 필수 |

## python-pptx 함정 (전부 실측)

| 증상 | 원인 | 조치 |
|---|---|---|
| 텍스트가 전부 좌상단 (0,0) 에 뭉침 | `add_textbox`는 **EMU**를 받는데 인치 float 을 넘김 → 3.6 EMU ≈ 0 | `emu(X(...))`로 감쌀 것. 텍스트에만 빠뜨리기 쉬움 |
| `RGBColor.__new__() missing 2 args` | `RGBColor(0xRRGGBB)` 는 없음 | `RGBColor.from_string("RRGGBB")` |
| 한 줄 텍스트가 두 줄로 접힘 | `word_wrap=True` 가 상자 폭에서 임의 개행 | `tf.word_wrap = False`. 줄바꿈은 명시적 `\n` 으로만 |
| 선·화살표에만 드롭섀도가 붙음 | `add_connector`에 `shadow.inherit=False` 누락 | 아래 `no_shadow()` |
| 파일이 아예 안 열림 (PowerPoint 오류) | `shadow.inherit=False` 가 이미 빈 `<a:effectLst/>` 를 넣는데 softEdge 용으로 하나 더 append → effectLst 2개 = 스키마 위반 | 기존 원소를 찾아 그 **안에** 넣음 |
| 내보낸 PNG 가 세로로 늘어남 | `Export(..., 1600, 900)` 고정 | 슬라이드 비율에서 세로를 계산 |

```python
def no_shadow(s):
    """커넥터에는 shadow.inherit 이 없다. 빈 effectLst 삽입이 같은 효과."""
    spPr = s._element.spPr
    if spPr.find(qn("a:effectLst")) is None:
        spPr.append(parse_xml("<a:effectLst %s/>" % nsdecls("a")))
    return s

def soft(s, rad_in):
    """부드러운 가장자리. ★ 기존 effectLst 안에 넣어야 한다."""
    spPr = s._element.spPr
    lst = spPr.find(qn("a:effectLst"))
    if lst is None:
        lst = parse_xml("<a:effectLst %s/>" % nsdecls("a")); spPr.append(lst)
    lst.append(parse_xml('<a:softEdge %s rad="%d"/>' % (nsdecls("a"), emu(rad_in))))
    return s
```

내보내기는 슬라이드 비율에서 픽셀 크기 계산:

```python
sw, sh_ = pres.PageSetup.SlideWidth, pres.PageSetup.SlideHeight
pres.Slides(1).Export(dst, "PNG", target_w, int(round(target_w * sh_ / sw)))
```

## PPT 도형으로 되는 것 / 안 되는 것

**됨** — AutoShape 180종, freeform 임의 다각형, 불리언 5종, 3D 돌출·베벨·재질,
투명도, 다중 stop 선형/방사 그라디언트, 부드러운 가장자리, 화살촉, 점선.
흐린 구름·나무 실루엣도 soft edge 로 됨.

**안 됨**
- **사진 질감**(아스팔트 미세 노이즈 등). 원본 밝기 표준편차 8.1 vs 도형 2.1.
- **블렌드 모드**(screen/add). 어두운 배경 위 반투명 난색은 배경 쪽으로 끌려가
  채도 저하 — "발광" 표현이 안 됨.
- **도형 간 깊이 정렬**. z-order 로 겹칠 뿐.
- **곡선 경로를 따라가는 그라디언트**. 선형 그라디언트는 bbox 기준이라
  휜 리본을 따라 색이 흐르게 할 수 없음 → 다중 stop 으로 근사하거나 도형을 쪼갬.

## 논문 투고 시

- Elsevier 는 MS Office 파일을 받음. Nature 는 `.ppt` 를 허용하되
  **"fully editable and without styling effects"** 조건 — 3D·베벨·반투명·그림자가 전부 걸림.
- PNG 는 기본 96 dpi 라 저널 요구(300~1000 dpi)에 못 미침. **PDF 로 저장하면 벡터 유지**.
- 폰트는 Arial/Helvetica. 한글 폰트는 임베딩에서 깨짐. RGB 로 둠(PPT 는 CMYK 불가).
