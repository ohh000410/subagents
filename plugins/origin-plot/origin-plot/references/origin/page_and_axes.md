# 페이지·축·눈금

## 눈금 방향과 개수

- `layer.<축>.ticks` 는 비트필드이고 방향 = `값 & 3`(0 없음, 1 안쪽, 2 바깥쪽, 3 양쪽). 4/8/12 는 없음, 5/9 는 안쪽, 10 은 바깥쪽(4개 프레임 변의 눈금 픽셀로 확인)
- 기본값은 x/y = 10(바깥쪽), x2/y2 = 5(안쪽). 안쪽 눈금 스타일 = x·y `ticks=1`, x2·y2 `ticks=0`. 바깥쪽 눈금이 나오면 `layer.x.ticks` 를 되읽는다 — 10 이면 set 이 적용되지 않은 것. 위·오른쪽 눈금은 `showAxes=3` 일 때만 보인다
- 주눈금 = `layer.x.inc` 의 배수 중 `[from, to]` 안에 있는 것. 배수는 0 부터 센다(`from` 부터가 아니다). `layer.x.anchor` 계열은 True 를 반환하지만 눈금을 옮기지 못한다. 개수 = `floor(to/inc) − ceil(from/inc) + 1`(29개 범위 모두 png 와 일치). 예: ±70 눈금을 20 간격으로 = `from=-90 to=90 inc=20`
- `from/to` 만 수동으로 쓰면 `inc` 는 autoscale 값에 남는다(데이터 0.3~2.5 에 `from=0.3 to=2.5` 면 inc=1 → 눈금 2개). `from/to` 와 함께 `layer.x.inc` 를 쓰고 되읽는다. 너무 촘촘한 `inc` 는 클램프된다(0.1 → 0.5)
- Origin 자동 눈금은 주눈금 3~7개. 로그 축에서는 `inc` 의미가 달라 이 개수 식을 쓰지 않는다

## plotxy 와 자동 스케일

- `plotxy` 는 호출할 때마다 레이어를 다시 autoscale 한다 — 그 전에 쓴 축 범위는 사라진다. 마지막 `plotxy` 뒤에 `layer.x/y.from/to` 를 다시 쓰고 되읽어 대조한다. 값은 `%.12g` 로 쓴다(`%g` 6자리에서 되읽기 대조가 깨졌다)
- 맞춤 `legend.text$` 를 줘도 자동 범례가 하나 더 생기는 일이 있다. 직접 범례는 견본 데이터 plot 과 페이지 레이블로 만들고, 마지막 `plotxy` 뒤에 `label -r Legend;`

## 축 제목 위치

`xb`/`yl` 은 레이어 스케일에 붙어 있다(`attach=2`). 레이어 기하·축을 바꾼 직후 `xb.top` 을 쓰면 낡은 페이지↔스케일 매핑으로 반영될 수 있다(x 제목이 프레임 중간에 그려짐, `app.Load` 후 같은 쓰기는 정상). 결정적 방법 = `xb.text$`/`yl.text$` 를 비우고 제목을 페이지 레이블(`label -s`, `.left/.top`, y 제목은 `.rotate=90`)로 둔다. 회전된 레이블의 `.width/.height` 는 회전된 상자의 값이다.

## merge_graph 와 페이지 비율

- `merge_graph` 의 여백·간격 매개변수 = `leftmg` `topmg` `rightmg` `bottommg` `xgap`. 없는 이름(`keepsrc:=`, `rescale:=`)이 하나라도 있으면 호출 전체가 False 가 되고 아무것도 병합되지 않는다
- `page.width` 는 읽히지만 export 비율은 바뀌지 않는다 — `page.height` 만 반영된다. 가로로 긴 그림은 높이를 줄여 만든다. 병합 뒤 레이어는 `layer -s N; layer.left/top/width/height`(페이지 %)로 배치하고, 글꼴은 기하를 끝낸 뒤 맞춘다
- `merge_graph` 는 범례를 옮기므로 병합 뒤 해당 레이어(`layer -s N`)에서 위치를 정한다. 자동 범례가 필요 없는 레이어는 `label -r Legend;`. `legend.fsize` 는 유효, `legend.pt` 는 무효
- `expGraph ... tr1.Unit:=2 tr1.Width:=3600` 이 동작한다(대소문자 주의). 유효 해상도 = px 폭 ÷ 페이지 폭(인치)
- 같은 형식의 그래프 시리즈에서는 첫 그래프만 보지 말고 모든 그래프에서 빈 사분면을 고른다

## 로그 축

로그 축(`layer.y.type=2`)의 `from/to` 는 log10 이 아니라 실제 데이터 값이다. `plotxy` 마다 다시 설정한다.

## 1:1 축 비율

- `layer.width/height` 는 서로 다른 기준(`page.width`, `page.height`)의 퍼센트다. 퍼센트를 그대로 비교하면 page 가 정사각형이 아닐 때 렌더 비율이 약 30 % 어긋난다. 절대 단위로 바꾼다: `tw = layer.width/100*PW`, `th = layer.height/100*PH`. `dx/tw > dy/th` 이면 `layer.height = (dy/dx*tw/PH*100)%`, 아니면 `layer.width = (dx/dy*th/PW*100)%`. `from/to` 를 정한 뒤 한 번만 적용한다
- 퍼센트 공간에서 `dx/tw == dy/th` 가 되는 것은 검증이 아니다 — 절대 공간 비율을 다시 계산하거나 png 를 본다

## 기하 쓰기 순서

- 레이어 퍼센트는 쓰는 시점의 `page.height` 를 기준으로 해석되므로 `page.height` 를 먼저 정한다. `page.width` 는 쓰기가 반영되지 않는다
- `layer.top`/`layer.height` 를 쓰는 중에는 `xb.top/height` 와 `legend.width/height` 가 한 명령씩 늦은 값을 돌려준다(예: 실제 약 1346/94 인데 약 1580/157, 범례 크기 약 1.58배). 페이지 배치는 글꼴 크기로 계산하고(한 줄 높이 = `9.67*fsize`), `page.height` 와 `layer.height/top` 쓰기를 모두 끝낸 뒤 `legendupdate;` 와 범례 측정·배치를 한다
- `pfit2l` 이 만드는 `page.height` 는 재현되지 않는다(같은 데이터·레이어 크기에서 실행마다 1644, 4632). `pfit2l` 결과로 제목·범례 배치를 계산하지 않는다
