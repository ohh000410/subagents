# LabTalk·COM 함정 — 명령 전송·되읽기·창 활성

## 준비 왕복

새로 띄운 Origin 은 LabTalk 이 살기 전에 COM 에 먼저 응답. 그때 `Execute` 는 True 를 반환하지만 아무 일도 하지 않음. `__ready=1234;` 를 보내고 `LTVar` 로 왕복을 확인한 뒤 시작.

## 그래프 창 생성과 활성 창

- 그래프 창은 만들 때 이름을 지정: `win -t plot <템플릿> <이름>;`. `win -r %H <새이름>` 은 상태에 따라 "Window Properties" 모달을 띄워 세션이 멈춤. 직접 만들지 않은 창은 이름을 바꾸지 말고 `__wn$=%H;` 로 읽음. `exist(<이름>)==3` 이면 그래프
- `ogl:=` 없는 `plotxy` 는 활성 창이 워크시트일 때만 새 그래프를 만듦. 활성 창이 그래프면 그 그래프에 레이어가 추가되고 `%H` 는 옛 이름을 그대로 돌려줌. 그래프를 여러 개 만들 때는 매번 `win -a <워크북>;` 으로 워크북을 활성화한 뒤 `plotxy` 하고, 직후 `%H` 가 서로 다른지 확인
- `newbook` 이후 `plotxy ... ogl:=[그래프]1!` 로 plot 을 올바른 그래프에 놓아도 활성 창은 새 북에 남음. 이후 `set`, `label -n`, `pfit2l`, 페이지 속성 읽기가 엉뚱한 페이지에 적용됨(증상: `set` 이 전부 False, 제목 객체가 png 에 없음, `pfit2l` False). 보조 데이터셋을 만든 직후 `win -a <그래프>;`
- `run -xf pfit2l -d;` 의 `-d` 는 대화상자 플래그라 "Fit Page to Layers" 창이 떠서 멈춤. 인자 없는 `pfit2l;` 만 씀

## 숫자를 명령 문자열에 넣기

- numpy ≥ 2.0 에서 `repr(np.float64(1150.68))` 은 `"np.float64(1150.68)"`. `%r` 로 만든 `legend.left=np.float64(...);` 은 `Execute` 가 True 인데 LabTalk 이 결측값(−1.23456789e−300)으로 평가해 속성이 0 이 되거나 기본값 그대로
- numpy 스칼라가 나오는 자리(`np.linspace` 인덱싱 등)에서 곧바로 `float()`/`int()` 로 바꿈. 명령 문자열에는 파이썬 기본형만 넣음
- 계산한 값을 적용한 `Execute` 직후 그 속성을 되읽어 대조 — 반환값과 진행 카운터는 이 실패를 통과시킴

## 속성 존재 판정(sentinel)

- 존재하지 않는 속성을 읽으면 Origin 은 오류 없이 변수도 바꾸지 않음. 3D 레이어에서는 `Execute` 반환값이 항상 1 이라 쓸 수 없음. `__v=-987654;` 를 넣고 `__v=<식>;` 을 실행한 뒤 `LTVar` 를 읽음 — 값이 그대로면 그 속성은 없음(2D 레이어의 `zb.fsize` 는 없음, 3D 레이어는 40)
- 문자열은 무효 속성이면 `__s$=<식>;` 에 표현식 문자열이 그대로 들어옴(`zb.text$` → `"zb.text$"`)
- 이것은 읽기 판정. 쓰기 판정은 2D 에서 `Execute` 반환값, 3D 에서 렌더 픽셀 차이로 함

## 워크시트에 데이터 넣기

- `app.PutWorksheet(book, data, 0, 0)` 의 `data` 는 행 우선(`data[row][col]`). 열 리스트 `[xs, a, b]` 를 넘기면 `xs` 가 1행, `a` 가 2행이 되고 반환값은 True → `rows = [[xs[i], a[i], b[i]] for i in range(n)]`
- `PutWorksheet` 직후 2행의 각 열(`col(k)[2]`)을 원본과 대조. True 는 모양을 보증하지 않음

## set 과 스타일 속성

- `set` 플래그는 한 호출에 하나씩 보냄. 묶으면 데이터플롯이 사라지거나 인덱싱이 깨짐
- 새 세션의 첫 `set` 은 True 를 반환해도 무효일 수 있음. 그리기·스타일·저장을 같은 세션 안에서 이어 처리하고 png 로 확인
- solid 심볼에서는 `-c color(...)` 가 테두리와 내부를 함께 바꿈. `-csf`/`-cf` 는 믿을 수 없음. 심볼 모양 `-k`, 크기 `-z` 는 단독 호출에서 안정적. 점선은 `-d`, 0.9 pt 는 잘 안 보여 1.3 pt 정도
- `Column` 객체에는 `SetComments()`/`SetLongName()` 이 없음. 속성 `Column.LongName`/`Column.Comments` 대입, LabTalk `wks.colN.lname$=`, `wcol(N)[C]$=` 는 됨
- `xb.bold`, `yl.bold`, `legend.pt` 는 무효. 유효 속성(`xb.fsize` 등)과 한 체인에 섞지 않음
- 기본 범례 텍스트는 `plotxy` 시점의 Comments. `plotxy` 뒤에 Comments 를 쓰고 `legendupdate;` 해도 열 문자(`B`, `D`)가 남음 → Comments 는 첫 `plotxy` 전에 설정
- 파이썬 raw string(`r"..."`)은 `\uXXXX` 도 해석하지 않아 12글자 ASCII 가 그대로 전송. `r"..."` 는 LabTalk 백슬래시 코드(`\b(`, `\+(`, `\g(`)만 있는 문자열에 쓰고, 한글은 비raw 문자열에 직접 적음
