# FDTD KB·공식 자료

우선순위: 현재 reference → 로컬 설치 예제·lumapi 예제 → Ansys Optics KB → forum → 웹.

| 로컬 | 용도 |
|---|---|
| `C:\Program Files\Lumerical\` | 설치·예제·Python API |
| 보존한 KB 예제 폴더(이 PC 환경 값) | 보존한 공식 KB 예제 원본 (내려받은 예제도 여기) |

| URL | 용도 |
|---|---|
| `https://optics.ansys.com/hc/en-us` | Ansys Optics KB |
| `https://optics.ansys.com/hc/en-us/categories/360001589433` | product documentation |
| `https://optics.ansys.com/hc/en-us/categories/360001515554` | 예제 파일·application gallery |
| `https://innovationspace.ansys.com/forum` | forum |

검색: `"lumapi" "<function or error>"` / `"Lumerical" "getresult" "<result name>"` / `"Lumerical FDTD" "BFAST"`, `"Bloch boundary"`, `"PML profile"` / `"Lumerical" "material fit" "RMS error"`.

403 → Chrome UA `curl`, 임시 HTML 작업 후 삭제:
```bash
# 작업 폴더에 받는다 — 따옴표 안 `~` 는 curl·Python 이 펼치지 않아 파일이 안 생긴다. 끝나면 지운다
curl -sS -L -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36" \
  -o fdtd_kb_page.html "<KB_URL>"
```

## article ID 재편 함정
구버전 article ID 에 다른 문서 매핑. 옛 ID curl → HTTP 200 인데 본문 다른 문서(BFAST ID → "Symmetric BCs").
- 받은 HTML 의 `<title>`·`<h1>` 이 의도한 주제인지 확인
- 올바른 URL: KB 검색결과의 `search/click?data=<base64>` 링크 디코드 → 현재 article ID
- 유효 ID: BFAST = `360034902273` (`https://optics.ansys.com/hc/en-us/articles/360034902273-Broadband-Fixed-Angle-Source-Technique-BFAST`). 내용·반박은 `fdtd_detail_bfast.md`
