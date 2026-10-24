# lumapi 기본 패턴 (검증된)

import → 결과 추출. 고급(커스텀 n,k / TFSF / Override mesh / BFAST) → `fdtd_lumapi_patterns_advanced.md`.

## 실패를 흡수하지 않음 (모든 패턴에 우선)

- 파일 없음·포맷 불일치에 sentinel 문자열(`"parse_fail"` 등) 반환 금지. `open()`·정규식 예외를 그대로 둠
- 모르는 값을 요청값·기본값으로 채워 기록 금지
- 부호 이상에 `abs()` 금지 — 부호는 배치 의존(`fdtd_principles_extraction.md`)
- 조건을 바꿔 자동 재실행 금지. cap 도달·이상값 = 플래그 컬럼으로 기록, 처방은 호출자

## 임포트·인스턴스

```python
import sys
sys.path.append(r"<Lumerical 설치 경로>\api\python")   # 설치 경로 = 이 PC 환경 값
import lumapi
import numpy as np
import os

fdtd = lumapi.FDTD(hide=False)   # 기본 GUI. hide=True 는 명시 요청 시만
```

## FDTD 영역 + 경계

```python
fdtd.addfdtd(x_min=-L_m/2, x_max=L_m/2, y_min=-L_m/2, y_max=L_m/2, z_min=-H_m/2, z_max=H_m/2,
             mesh_accuracy=1)   # 1~8, 기본 2
fdtd.setnamed("FDTD", "x min bc", "Periodic"); fdtd.setnamed("FDTD", "x max bc", "Periodic")
fdtd.setnamed("FDTD", "y min bc", "Periodic"); fdtd.setnamed("FDTD", "y max bc", "Periodic")
fdtd.setnamed("FDTD", "z min bc", "PML");      fdtd.setnamed("FDTD", "z max bc", "PML")
# 6면 PML 은 기본값 — setnamed 생략 가능
```

## 재질 — 내장 DB

`"Au (Gold) - Johnson and Christy"`, `"Au (Gold) - Palik"`, `"H2O (Water) - Palik"`, `"SiO2 (Glass) - Palik"`, `"Ag (Silver) - Johnson and Christy"`

```python
fdtd.setnamed("sphere", "material", "Au (Gold) - Johnson and Christy")
```

## 구조물

```python
fdtd.addsphere(x=0, y=0, z=0, radius=r); fdtd.setnamed("sphere", "name", "Au_sphere")
fdtd.addrect(x=0, y=0, z=0, x_span=Lx, y_span=Ly, z_span=Lz)
```

## 광원 — 평면파

```python
fdtd.addplane(injection_axis="z", direction="forward", x_span=L_m, y_span=L_m, z=z_src,
              wavelength_start=lam_min, wavelength_stop=lam_max)
```

### 도메인 축 span 통일 (source·monitor·local mesh)

면축(injection 수직, 2D: x / 3D: x·z) span 은 FDTD 도메인 폭에 맞춤. 경계 종류 무관 — 도메인 밖은 clip, 작으면 그만큼 누락.

| 요소 | 면축 | 전파축 |
|---|---|---|
| source | ≥ 도메인 (over-cover) | 위치 |
| monitor | = 도메인 | 위치 |
| local mesh | = 도메인 | 구조 높이만 |

- source 면축 span < 도메인 → 도메인 일부 미조사. Bloch 면 unit cell 균일 평면파까지 깨짐. `addplane()` 후 면축 span 미설정 금지(기본 span 의존 → L 커지면 under-cover)
- monitor 면축 < 도메인 → flux 누락, R/T 과소
- local mesh 를 경사 구조의 한 객체 bbox 로 잡으면 span = 그 객체의 가로 이동량(shear) → shear < L 이면 구조 일부가 coarse 로 남음

```python
for obj in ("src", "T_mon", "R_mon"):
    fdtd.setnamed(obj, "x min", x_min); fdtd.setnamed(obj, "x max", x_max)   # (+3D: z min/z max)
fdtd.set("x min", x_min); fdtd.set("x max", x_max)                # local mesh 주기축 = 도메인
fdtd.set("y", struct_y_cen); fdtd.set("y span", struct_y_span)   # 비주기축 = 구조 높이
```

## 모니터

```python
fdtd.addpower(); fdtd.setnamed("monitor", "name", "T_monitor")    # addpower 기본 이름 = "monitor"
fdtd.setnamed("T_monitor", "monitor type", "2D Z-normal")
fdtd.setnamed("T_monitor", "x", 0.0); fdtd.setnamed("T_monitor", "y", 0.0)
fdtd.setnamed("T_monitor", "x span", L_m); fdtd.setnamed("T_monitor", "y span", L_m)
fdtd.setnamed("T_monitor", "z", z_T)
```

Frequency points = 모니터 설정 (source 아님):
```python
fdtd.setglobalmonitor("frequency points", 300)
# monitor별: setnamed(mon, "override global monitor settings", 1); setnamed(mon, "frequency points", 300)
# 불가: setnamed("source", "frequency points") / setglobalsource("number of frequency points") → property not found
```

### source 파장 대역은 소스 본체에
- `addplane()` 은 `override global source settings`=1 로 만들어지고, 그 순간의 전역 소스 대역(새 프로젝트 기본 400–700 nm)을 자기 `wavelength start/stop` 에 복사. override=1 인 동안 `setglobalsource()` 는 전역 값만 바꾸고 소스는 자기 값을 씀 — 오류·경고 없이 대역이 잘리고 R+T 도 맞아 정상처럼 보임
- `deleteall()` 은 전역 대역을 되돌리지 않아, 재사용 세션에선 우연히 값이 같아 가려지고 새 세션에서 드러남. 주파수 모니터는 소스 본체가 아니라 전역 소스 대역을 샘플
- 소스 객체에 `set("wavelength start/stop")` 를 쓰고 `setglobalsource()` 도 같은 값으로 쓴 뒤, `getnamed`·`getglobalsource` 로 둘 다 되읽음. `setglobalmonitor` 에는 파장 대역 속성이 없음

## 저장 & 실행

```python
fdtd.save(SAVE_PATH)   # run 전 절대경로
fdtd.run()
```

### Save As 모달 방지 (hide=False sweep)

세션이 "Untitled" 이면 `save(절대경로)` 여도 Save As 창 → 무인 sweep 정지.

```python
os.makedirs(OUT_DIR, exist_ok=True)
fdtd = lumapi.FDTD(hide=False)
fdtd.save(os.path.join(OUT_DIR, "untitled_guard.fsp"))   # 루프 전 파일명 각인(Untitled 해소)
for case_id, params in sweep:
    fdtd.switchtolayout(); fdtd.deleteall()
    # ... 설정 ...
    fdtd.save(os.path.join(OUT_DIR, f"{case_id}.fsp"))   # case 마다 다른 .fsp — 같은 경로면 _p0.log 를 덮어 행-로그 대조가 깨진다
    fdtd.run()
```
case 마다 `.fsp`·`_p0.log` 가 따로 남아야 함(`fdtd_pitfalls_api.md` case_id 규칙, `tools/assess_run.py` 의 `log_shared` FAIL).
같은 .fsp 가 이전 GUI 에 열려 있으면 충돌 → 새 `lumapi.FDTD()` 인스턴스.

## Cleanup

```python
with lumapi.FDTD(hide=False) as fdtd:   # Ansys 권장. 블록 종료 시 close()
    ...
# 또는
fdtd = lumapi.FDTD(hide=False)
try:
    ...
finally:
    fdtd.close()
del fdtd
```
`close()` 를 `except: pass` 로 감싸지 않음. GUI 보존은 사용자가 "GUI 남겨" 명시 시만.

## 결과 추출 — 스펙트럼

```python
T_data = fdtd.getresult("T_monitor", "T")   # dict: "T", "lambda"
R_data = fdtd.getresult("R_monitor", "T")
lam_arr = np.squeeze(T_data["lambda"]) * 1e9
T_arr = np.abs(np.squeeze(T_data["T"])); R_arr = np.abs(np.squeeze(R_data["T"])); A_arr = 1.0 - T_arr - R_arr
```
source -z: T_monitor(아래) transmission 음수 → abs / R_monitor(위) 양수.

## 결과 추출 — 단일 파장

```python
T = abs(float(np.real(fdtd.transmission("T_monitor"))))
R = abs(float(np.real(fdtd.transmission("R_monitor"))))
```
전제: R_monitor 가 source 상류(입사 반대편). R_mon 이 source 와 구조 사이면 net flux = R−1 → `R = 1 + transmission` (`fdtd_detail_rt_signs.md`).

## 주요 함수

```
addfdtd, addplane, addsphere, addrect, addpower, addtfsf, addmesh
addmaterial, setmaterial, getmaterial, materialexists
setnamed, getnamed, run, save, load, close
transmission, transmission_avg, transmission_pavg, getresult, haveresult
sourcepower(f), sourceintensity(f)
```
