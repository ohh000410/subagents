# structure group 회전

cluster·다중 입자 회전: `addstructuregroup` + group rotation.

## 회전 convention = intrinsic (body-fixed)

회전 표기 "z축 30도, y축 45도" = intrinsic z(30°) → y(45°). 미명시 → intrinsic 적용 + 보고에 convention 명시.

## 함정 0 — sphere 가 group 밖

structure group = 컨테이너. sphere 를 group scope 안에서 add 하지 않으면 root 에 들어가 회전 0.

```python
# 잘못: group 만 만들고 root 에 addsphere → setnamed("cluster","rotation 1",45) 는 빈 group 회전
```
증상: orientation sweep 결과 σ 전부 동일 (cube symmetry 면 1~5% 변동 정상). baseline 과는 ~0.5% 차이(group 객체의 mesh staircase 영향).

## 함정 1 — `addtogroup()` 좌표 자동 변환

global 좌표 sphere 를 `addtogroup("cluster")` 하면 group local 로 inverse transform → base 좌표 아님.

## 함정 2 — group rotation = extrinsic

`first axis`+`rotation 1` → `second axis`+`rotation 2`, 글로벌 축 기준. intrinsic A(α)→B(β) = extrinsic B(β)→A(α).
intrinsic z(30°)→y(45°) → `first axis=y, rotation 1=45, second axis=z, rotation 2=30`.

## 올바른 패턴 (intrinsic z→y)

```python
ALPHA_DEG, BETA_DEG = 30.0, 45.0
fdtd.addstructuregroup(); fdtd.set("name", "cluster")
fdtd.groupscope("::model::cluster")                     # base 좌표 그대로 local
for (x, y, z) in BASE_COORDS_NM:
    fdtd.addsphere(name=..., x=x*1e-9, y=y*1e-9, z=z*1e-9, ...)
fdtd.groupscope("::model")
fdtd.setnamed("cluster", "first axis", "y");  fdtd.setnamed("cluster", "rotation 1", BETA_DEG)
fdtd.setnamed("cluster", "second axis", "z"); fdtd.setnamed("cluster", "rotation 2", ALPHA_DEG)
```

## 좌표 직접 회전 (intrinsic z→y)

```python
def rotate_coords_intrinsic_zy(coords, alpha_deg, beta_deg):
    a = np.radians(alpha_deg); b = np.radians(beta_deg); rot = []
    for (x, y, z) in coords:
        xp = x*np.cos(b) + z*np.sin(b); yp = y; zp = -x*np.sin(b) + z*np.cos(b)   # global y, β
        rot.append((xp*np.cos(a) - yp*np.sin(a), xp*np.sin(a) + yp*np.cos(a), zp))  # global z, α
    return rot
```
검산: (-50,0,0) → R_y(45°) (-35.36, 0, 35.36) → R_z(30°) (-30.62, -17.68, 35.36).

- 한 case → 좌표 회전 / orientation sweep → structuregroup + rotation

## 시뮬 전 검증

```python
fdtd.groupscope("::model::cluster_group")
n_children = int(fdtd.getnumber())   # 0 또는 부족 → 함정 0
for i in range(1, n_children + 1):
    print(fdtd.get("name", i), fdtd.get("x", i)*1e9, fdtd.get("y", i)*1e9, fdtd.get("z", i)*1e9)
fdtd.groupscope("::model")
```
sweep 첫 case 시작 전 회전 적용 좌표를 expected 와 대조.
