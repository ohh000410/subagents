# TFSF + Cross-section 측정

단일 입자 `C_sca`, `C_abs`, `Q_sca`, `Q_abs`.

## setup
1. 6면 PML, `background material`
2. 입자 + override mesh (`addmesh` box)
3. `addtfsf(injection_axis, direction, wavelength_start/stop)` — 입자 표면에서 떨어뜨림
4. 6면 박스 monitor 2세트 (TFSF 안: 흡수, 밖: 산란). 각 면 2D power monitor

박스 위치는 입자 크기·near-field·PML 거리·mesh 에 맞춰 별도 검증.

## 정규화
- `transmission()` = net +축방향 power / source_power (무차원)
- TFSF: `sourceintensity(f) = sourcepower(f) / A_actual`

```python
# A_source: TFSF box 의 injection_axis 수직 단면 면적 (monitor 면적 아님)
# sourcepower(f)/sourceintensity(f) readback 과 대조 — 불일치(mesh snap) 시 readback 우선
A_source = (2 * tfsf_half) ** 2

def box_outward_net(prefix):
    net = np.zeros(n_freq)
    for axis in ("x", "y", "z"):
        tp = np.squeeze(fdtd.getresult(f"{prefix}_{axis}p", "T")["T"])
        tn = np.squeeze(fdtd.getresult(f"{prefix}_{axis}n", "T")["T"])
        net += np.asarray(tp) - np.asarray(tn)      # outward = T(+면) - T(-면)
    return net

C_abs = -box_outward_net("abs") * A_source   # TFSF 안 박스, outward < 0
C_sca = +box_outward_net("sca") * A_source   # TFSF 밖 박스, outward > 0
Q_abs = C_abs / (np.pi * r_m**2)
Q_sca = C_sca / (np.pi * r_m**2)
```

## 단일 파장 (fit 회피)

```python
fdtd.addtfsf(..., wavelength_start=lam, wavelength_stop=lam)
mat_idx = fdtd.addmaterial("(n,k) Material")
fdtd.setmaterial(mat_idx, "name", "particle_at_lam")
fdtd.setmaterial("particle_at_lam", "Refractive Index", n_at_lam)
fdtd.setmaterial("particle_at_lam", "Imaginary Refractive Index", k_at_lam)
```
파장당 별도 실행. dispersive 재료의 단일 파장 (n,k) 시간영역 변환 방식은 KB 확인.
