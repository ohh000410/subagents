"""inventor_session.kill_own 판정 시험 (Inventor 불필요, 프로세스 목록·taskkill 을 가짜로). 실행: tools 폴더에서 python -m unittest discover -s tests"""
import os, sys, unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import inventor_session as s  # noqa: E402


class Done:
    def __init__(self, returncode):
        self.returncode = returncode


class KillOwn(unittest.TestCase):
    def setUp(self):
        self.saved = (s.list_inventor, s.subprocess.run)
        self.calls = []

    def tearDown(self):
        s.list_inventor, s.subprocess.run = self.saved

    def fake(self, alive_after_kill, taskkill_rc):
        state = {"killed": False}
        s.list_inventor = lambda: [] if state["killed"] and not alive_after_kill else [(4242, "Autodesk Inventor")]

        def run(cmd, **kw):
            self.calls.append(cmd)
            state["killed"] = True
            return Done(taskkill_rc)
        s.subprocess.run = run

    def test_exited_on_its_own_returns_false(self):
        s.list_inventor = lambda: []
        self.assertFalse(s.kill_own(4242, wait=0.1))

    def test_gone_during_taskkill_is_not_an_error(self):  # taskkill 128(없는 PID) 이 CalledProcessError 였다(2026-10-22 교차 검토)
        self.fake(alive_after_kill=False, taskkill_rc=128)
        self.assertTrue(s.kill_own(4242, wait=0))
        self.assertEqual(self.calls, [["taskkill", "/PID", "4242", "/F"]])

    def test_still_alive_after_taskkill_raises(self):
        self.fake(alive_after_kill=True, taskkill_rc=1)
        with self.assertRaises(RuntimeError):
            s.kill_own(4242, wait=0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
