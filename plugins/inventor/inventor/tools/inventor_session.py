"""Inventor 세션 헬퍼: 이미 떠 있는 Inventor 는 붙지도 죽이지도 않고 거부, 종료는 자기 PID 만.

COM Dispatch("Inventor.Application") 은 실행 중 인스턴스가 있으면 거기에 붙는다(ROT).
그래서 Dispatch 전에 프로세스를 확인해야 한다.

사용:
    from inventor_session import launch, kill_own, InventorAlreadyRunning
    app, pid = launch()          # 이미 떠 있으면 InventorAlreadyRunning(PID·창 제목 메시지)
    try: ...
    finally:
        # 문서 Close(True) -> app.Quit() 후, 남아 있으면 자기 PID 만
        app.Quit(); kill_own(pid)
"""
import csv, io, subprocess, time


class InventorAlreadyRunning(RuntimeError):
    pass


def list_inventor():
    """[(pid, window_title)] — Inventor.exe 프로세스 전부."""
    out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq Inventor.exe", "/V", "/FO", "CSV", "/NH"],
                         capture_output=True, text=True, encoding="cp949", errors="replace").stdout
    rows = [r for r in csv.reader(io.StringIO(out)) if len(r) >= 9 and r[0].lower() == "inventor.exe"]
    return [(int(r[1]), r[-1]) for r in rows]


def launch():
    """새 Inventor 를 띄워 (app, 자기 PID) 반환. 이미 있으면 붙지 않고 예외."""
    import win32com.client as win32
    before = list_inventor()
    if before:
        raise InventorAlreadyRunning(
            "Inventor 가 이미 실행 중 — 붙지도 죽이지도 않음: "
            + ", ".join("PID %d '%s'" % p for p in before))
    app = win32.Dispatch("Inventor.Application")
    app.Visible = True
    deadline = time.time() + 30
    own = []
    while not own and time.time() < deadline:
        own = [p for p, _ in list_inventor()]
        time.sleep(0.5)
    if len(own) != 1:
        raise RuntimeError("자기 PID 확보 실패: 새 Inventor 프로세스 %s" % own)
    return app, own[0]


def kill_own(pid, wait=15):
    """자기 PID 가 아직 살아 있으면(Quit 후 wait 초 대기) 그 PID 만 강제 종료. 끝났는지는 프로세스 목록으로 본다."""
    deadline = time.time() + wait
    while time.time() < deadline:
        if pid not in [p for p, _ in list_inventor()]:
            return False
        time.sleep(0.5)
    # taskkill 종료코드로 판정하지 않는다 — 대기 끝 무렵 스스로 끝나면 128(없는 PID)로 예외였다(2026-10-22 교차 검토)
    subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True)
    deadline = time.time() + 5
    while pid in [p for p, _ in list_inventor()]:
        if time.time() > deadline:
            raise RuntimeError("자기 PID %d 강제 종료 실패" % pid)
        time.sleep(0.5)
    return True
