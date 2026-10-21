# rcwa_gpu_investigation — RCWA GPU batch 전수조사 (research-compute)

**결론만 필요하면 안 읽어도 됨** — [[rcwa_reference_index]] 공통 2 한 줄("GPU batch 불가 → CPU Pool")로 충분. 이 파일은 **GPU batch/최적화를 다시 시도할까 고민할 때만** (또는 환경이 WSL2/클라우드로 바뀌었을 때) 참고. 전수 실측 2026-07-11~13.

## 이 환경(Windows + RTX 3050)에서 GPU batch 전 경로 불가

| 경로 | 결과 |
|---|---|
| meent torch backend | 각도 batch 미지원 (`inc_ang` 배열 → shape 에러, 내부 스칼라 가정) |
| torcwa | 공식 예제 전부 for-loop 순차(batch 텐서 없음). fp64 507s(RTX3050 fp64=fp32의 1/64)·fp32는 near-singular crash. 게다가 **O(N_z²)** ([[torcwa_api]]) |
| meent JAX + pmap/vmap | **JAX가 Windows GPU 미지원**(`[CpuDevice]`만). README 병렬은 pmap(멀티디바이스) |
| MPS (멀티프로세스 1 GPU) | Linux 전용 |

- meent GPU 단일 solve도 이득 ≈0 (fto67서 1.01x — eigendecomp가 CPU라 batch여도 커널이 GPU에서 약함).
- **개념적으론 옳음**: 독립 계산점(각도·파장) 병렬화는 정당. 다만 이 OS+GPU+라이브러리 조합이 전부 미지원.

## 진짜 GPU batch가 필요해지면 (대량 inverse design 등)
- **WSL2/Linux**: JAX GPU + MPS 열림. 단 RTX3050 fp64 penalty(1/64)는 그대로 → fp64 RCWA는 CPU도 못 이김. fp32는 near-singular 불안정.
- **클라우드 A100/H100**: fp64 강력(A100 9.7 TFLOPS ≈ 3050의 ~70배) → 진짜 실익. JAX-native RCWA(**fmmax**, 미검증)가 vmap 정공법 후보.
- 값은 세 라이브러리 어디서나 동일(memory `reference_rcwa_wedge_s1_values.md`) — 순수 성능/병렬 선택이지 정확도 문제 아님.

