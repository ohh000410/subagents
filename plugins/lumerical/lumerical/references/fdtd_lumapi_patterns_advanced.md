# lumapi 고급 패턴

기본 패턴 → `fdtd_lumapi_patterns_basic.md`.

## mesh refinement / autoshutoff (구문만)

```python
fdtd.setnamed("FDTD", "mesh refinement", "conformal variant 1")
fdtd.setnamed("FDTD", "auto shutoff min", 1e-7)
```
값 선택 = 수렴 셋업 단계. mesh refinement → `fdtd_detail_mesh_grazing.md`, autoshutoff → `fdtd_convergence_protocol.md` 1단계.

## 재질 — 커스텀 n,k

```python
mat_idx = fdtd.addmaterial("(n,k) Material")          # 인덱스 반환. name 지정 후 이름 접근 가능
fdtd.setmaterial(mat_idx, "name", "my_material")
fdtd.setmaterial("my_material", "Refractive Index", n_val)
fdtd.setmaterial("my_material", "Imaginary Refractive Index", k_val)
fdtd.setnamed("sphere", "material", "my_material")
```

## 재질 — Sampled data (broadband)

```python
mat_idx = fdtd.addmaterial("Sampled data")
fdtd.setmaterial(mat_idx, "name", "my_dispersive")
fdtd.setmaterial("my_dispersive", "sampled data", sampled)   # N×2: col0 frequency[Hz], col1 complex eps
fdtd.setmaterial("my_dispersive", "max coefficients", 10)    # 기본 6
fdtd.setmaterial("my_dispersive", "tolerance", 1e-4)         # 기본 0.1
fdtd.setmaterial("my_dispersive", "imaginary weight", 1)     # 기본 1
```
재질별 검증 fit 값 → agent-memory.

## TFSF

```python
fdtd.addtfsf(x_min=-tfsf_half, x_max=tfsf_half, y_min=-tfsf_half, y_max=tfsf_half,
             z_min=-tfsf_half, z_max=tfsf_half, injection_axis="z", direction="forward",
             wavelength_start=lam_min, wavelength_stop=lam_max)   # 단일 λ: start = stop
```
cross-section 전체 setup → `fdtd_cross_section_setup.md`.

## Override mesh (축별)

```python
fdtd.addmesh(x_min=-mesh_box, x_max=mesh_box, y_min=-mesh_box, y_max=mesh_box, z_min=-mesh_box, z_max=mesh_box)
fdtd.set("override x mesh", 1); fdtd.set("dx", dx)
fdtd.set("override y mesh", 0); fdtd.set("override z mesh", 0)
```
- 필요한 축만 refine (grazing = 접선축 → `fdtd_detail_mesh_grazing.md`)
- dx 가 span 의 정수약수가 아니면 snap → readback
- 켠 축 span = 도메인(면축). tensor mesh 라 켠 축 extent 만 유효. 전파축은 구조 높이 (`fdtd_lumapi_patterns_basic.md` 도메인 축 span 통일)

## BFAST

```python
fdtd.addplane(); fdtd.set("name", "src")
fdtd.setnamed("src", "injection axis", "y-axis"); fdtd.setnamed("src", "direction", "Backward")
fdtd.setnamed("src", "y", y_src)
fdtd.setnamed("src", "angle theta", float(theta_deg)); fdtd.setnamed("src", "polarization angle", float(pol_angle_deg))
fdtd.setnamed("src", "wavelength start", lam_min_m); fdtd.setnamed("src", "wavelength stop", lam_max_m)   # 단일 λ → Bloch
fdtd.setnamed("src", "plane wave type", "BFAST")
# 면축 span = 도메인. x BC Bloch 여도 BFAST 가 override. y BC PML
```
정규화·정확도·발산·보정 → `fdtd_detail_bfast.md` (요약 `fdtd_principles_source.md`).

## 레이아웃 — 평면파 -z 입사

```
PML (+z)
R_monitor   z = +H/2 * 0.83
source      z = +H/2 * 0.67   (-z 입사)
입자        z = 0
T_monitor   z = -H/2 * 0.83
PML (-z)
```
r_particle < |z_T|. 사입사 배치 → `fdtd_detail_rt_signs.md`. 부호: T 음수 → abs / R 양수.
