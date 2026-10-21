# 범례를 축 안 빈 자리에 놓기 — 메인 세션 실측 절차 (2026-08-24)

## 절차 (검증됨)

1. **빈 자리는 격자 탐색으로 찾는다.** 네 모서리만 보면 부족하다.
   범례 크기(축 단위 환산)의 창을 축 안쪽 전 영역에 26×26 격자로 훑어 데이터 점유
   최소점을 고른다. 곡선은 꼭짓점만 세지 말고 선분을 조밀 샘플링(densify)해서 센다.

2. **배치는 페이지 좌표(`legend.left`/`legend.top`)로 한다.** `legend.x`/`legend.y`
   (축 좌표)는 **앵커 기준이 일관되지 않았다**: 같은 스크립트에서 Graph6 은 y 값이
   범례 아래쪽 기준으로, Graph2 는 위쪽 기준으로 동작해 프레임 위로 삐져나갔다.
   레이어 페이지 사각형(`layer.left/top/width/height` × `page.width/height`)을 읽어
   축좌표 → 페이지좌표로 직접 환산하면 모호성이 없다 (`legend.top` = 위 모서리 확정).

   ```python
   left_pg = Lx + (bx - xf) / (xt - xf) * Lw
   top_pg  = Ly + (yt - by) / (yt - yf) * Lh    # 축 y 는 위가 크고 페이지 y 는 아래가 크다
   ```

3. **프레임·눈금에서 떨어뜨린다.** 격자 탐색 후보에서 범례 상자가 레이어 프레임 안쪽 여백
   (레이어 폭·높이의 **4% 이상**)을 침범하는 셀은 제외한다. 점유 0 이어도 프레임에 붙은 자리는
   답이 아니다 — 실측(2026-09-19): 점유 0 셀을 골랐는데 범례 스와치가 왼쪽 축선에 겹쳐 렌더됐다.
   곡선 점유 계산에도 프레임·눈금 라인을 점유로 넣는다.
   **점유 0 셀이 여럿이면 가장 먼 자리를 고른다** — 각 후보에서 곡선·프레임까지의 최소 거리를 재고
   그 최소 거리가 가장 큰 셀을 택한다.

4. **렌더 후 픽셀로 검증한다.** export png 에서 `legend.left/top/width/height` 를 픽셀로 환산해
   그 상자를 여백만큼 키운 영역 안에 곡선·축선 색 픽셀이 있으면 실패다 — 다음 후보 셀로 옮겨
   재렌더한다.

5. `legend.background=0` 은 **`legend.left/top` 보다 먼저** 설정한다. 뒤에 주면 반환값은 True 인데 위치가
   기본 위치만큼(+23,+24 page unit) 밀려 저장된다(agent-memory `feedback_origin_legend_page_coordinate_placement`).
   위치는 `verify(app, intended)` 의 `intended["legend"]` 로 되읽어 확인된다.

## ★ 함정 (실측)

- **`legendupdate;` 는 범례를 재생성한다.** 맞춤 `legend.text$` 가 있는 그래프에서
  위치만 옮기려고 부르면 내용이 날아가고 밴드·기준선까지 항목으로 붙는다
  (eps(theta) 에서 `K` `L` `N` `O` `Q` 쓰레기 항목 실측). 위치만 바꿀 때는 부르지 마라.
  범례 크기를 읽어야 하는데 맞춤 범례가 있다면: text$ 를 백업 → legendupdate →
  text$ 복원 순이 아니라, **그냥 legendupdate 없이 legend.width/height 를 읽으면 된다**
  (이미 존재하는 오브젝트라 값이 나온다).

- **`%(n)` 참조로 범례를 만들면 컬럼 Long Name 이 통째로 딸려온다** (한글·수치 포함).
  영어 전용 규칙 하에서는 **리터럴 이름을 직접 넣는다**: `\l(6) Zhou s1` 식.
  구분자는 진짜 개행 `"\n"` — `"\\n"` 로 이스케이프하면 리터럴 'n' 이 찍힌다(실측).

- 범례를 안으로 옮긴 뒤 **아래에 남는 옛 범례 자리(빈 여백)를 회수**한다:
  `page.height = xb.top + xb.height + 60` 으로 줄이고 `layer.top/height` 는 절대값
  보존으로 재환산. geometry 를 먼저 전부 끝낸 뒤에 범례를 측정·배치할 것
  (속성이 한 단계 늦게 반영됨 — agent-memory `feedback_origin_equal_scale_axis_and_page_layout`).
