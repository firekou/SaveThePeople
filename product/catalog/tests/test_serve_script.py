"""D1A-03: scripts/serve.sh safety (bind, PID ownership/identity, cleanup).

These tests run the real script with stub hooks only:
- STP_PRODUCT_DIR points at a temporary fake checkout whose manage.py just sleeps (no listener);
- STP_CURL is a stub that succeeds or fails the health check;
- STP_KILL is a stub that records every call; "foreign" tests assert it is called 0 times.
Every process signalled for real is one these tests spawned themselves. No unrelated process is touched.
"""
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from django.test import SimpleTestCase

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "serve.sh"
PORT = "18765"


def _gone(pid):
    """Exited: no /proc entry, or a zombie awaiting reaping by its (non-test) parent."""
    try:
        return Path(f"/proc/{pid}/stat").read_text().rsplit(") ", 1)[1].split()[0] in ("Z", "X")
    except FileNotFoundError:
        return True


def _start_time(pid):
    stat = Path(f"/proc/{pid}/stat").read_text()
    return stat.rsplit(") ", 1)[1].split()[19]


class ServeScriptTests(SimpleTestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="stp_serve_test_"))
        self.fake = self.tmp / "checkout"
        self.fake.mkdir()
        self.marker = self.tmp / "spawned.marker"
        (self.fake / "manage.py").write_text(
            "import sys, time, pathlib\n"
            f"pathlib.Path({str(self.marker)!r}).write_text(' '.join(sys.argv))\n"
            "time.sleep(60)\n")
        self.kill_log = self.tmp / "kill.log"
        self.stubs = self.tmp / "stubs"
        self.stubs.mkdir()
        self._stub("curl_ok", "exit 0")
        self._stub("curl_fail", "exit 22")
        self._stub("kill_log_only", f'echo "$@" >> {self.kill_log}; exit 0')
        self._stub("kill_real", f'echo "$@" >> {self.kill_log}; exec /bin/kill "$@"')
        self._stub("kill_fail", f'echo "$@" >> {self.kill_log}; exit 1')
        self.pidfile = self.tmp / "server.pid"
        self.spawned = []

    def tearDown(self):
        # only processes these tests started: the fake server (via record) and Popen sleepers
        for p in self.spawned:
            if p.poll() is None:
                p.kill()
                p.wait()
        if self.pidfile.exists() and not self.pidfile.is_symlink():
            for line in self.pidfile.read_text().splitlines():
                if line.startswith("pid="):
                    pid = int(line[4:])
                    try:
                        if str(self.fake) == os.readlink(f"/proc/{pid}/cwd"):
                            os.kill(pid, 9)
                    except (FileNotFoundError, ProcessLookupError, PermissionError, OSError):
                        pass
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _stub(self, name, body):
        p = self.stubs / name
        p.write_text("#!/usr/bin/env bash\n" + body + "\n")
        p.chmod(0o755)

    def run_script(self, cmd, curl="curl_ok", kill="kill_real", bind=f"127.0.0.1:{PORT}", extra=None):
        env = dict(os.environ, STP_PRODUCT_DIR=str(self.fake), STP_PIDFILE=str(self.pidfile),
                   STP_SERVER_LOG=str(self.tmp / "server.log"), STP_BIND=bind, STP_PYTHON=sys.executable,
                   STP_CURL=str(self.stubs / curl), STP_KILL=str(self.stubs / kill),
                   STP_HEALTH_TRIES="2", STP_STOP_WAIT="1")
        env.update(extra or {})
        return subprocess.run(["bash", str(SCRIPT), cmd], env=env, capture_output=True, text=True, timeout=60)

    def kill_calls(self):
        return self.kill_log.read_text().splitlines() if self.kill_log.exists() else []

    def record(self):
        return dict(line.split("=", 1) for line in self.pidfile.read_text().splitlines())

    def write_record(self, pid, start, token="0" * 32, checkout=None, mode=0o600, extra_line=None):
        lines = [f"pid={pid}", f"start={start}", f"checkout={checkout or os.path.realpath(self.fake)}",
                 f"bind=127.0.0.1:{PORT}", f"token={token}", f"python={sys.executable}"]
        if extra_line:
            lines.append(extra_line)
        self.pidfile.write_text("\n".join(lines) + "\n")
        os.chmod(self.pidfile, mode)

    def sleeper(self):
        p = subprocess.Popen(["sleep", "60"])
        self.spawned.append(p)
        time.sleep(0.1)
        return p

    # --- bind validation happens before spawn -------------------------------------------------
    def test_wildcard_lan_and_hostname_binds_are_refused_before_spawn(self):
        for bind in ["0.0.0.0:8765", "[::]:8765", ":::8765", "192.168.1.5:8765", "10.0.0.2:8765",
                     "localhost:8765", "127.0.0.1", "127.0.0.1:80", "127.0.0.1:99999", "127.0.0.2:8765", ""]:
            with self.subTest(bind=bind):
                r = self.run_script("start", bind=bind)
                self.assertEqual(r.returncode, 2, r.stderr)
                self.assertIn("refusing bind", r.stderr)
                self.assertFalse(self.marker.exists(), "nothing may be spawned for a refused bind")
                self.assertFalse(self.pidfile.exists())

    # --- legal control: normal start / status / stop ------------------------------------------
    def test_normal_start_status_stop(self):
        r = self.run_script("start")
        self.assertEqual(r.returncode, 0, r.stderr)
        rec = self.record()
        self.assertEqual(oct(self.pidfile.stat().st_mode & 0o777), "0o600")
        self.assertEqual(set(rec), {"pid", "start", "checkout", "bind", "token", "python"})
        pid = int(rec["pid"])
        self.assertIn("manage.py runserver 127.0.0.1:%s --noreload" % PORT, self.marker.read_text())
        self.assertEqual(self.run_script("status").stdout.strip(), f"running pid {pid} on 127.0.0.1:{PORT}")
        r = self.run_script("stop")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.kill_calls(), [f"-TERM {pid}"])
        self.assertFalse(self.pidfile.exists())
        self.assertTrue(_gone(pid))

    def test_failed_health_check_stops_only_own_process(self):
        r = self.run_script("start", curl="curl_fail")
        self.assertEqual(r.returncode, 1, r.stderr)
        self.assertIn("health check failed", r.stderr)
        calls = self.kill_calls()
        self.assertEqual(len(calls), 1)
        pid = int(calls[0].split()[1])
        self.assertTrue(_gone(pid), "own spawned process must be gone")
        self.assertFalse(self.pidfile.exists(), "record removed only after confirmed stop")

    # --- stop failures keep the record ----------------------------------------------------------
    def test_kill_failure_keeps_record_and_fails(self):
        self.assertEqual(self.run_script("start").returncode, 0)
        pid = int(self.record()["pid"])
        r = self.run_script("stop", kill="kill_fail")
        self.assertEqual(r.returncode, 4, r.stderr)
        self.assertTrue(self.pidfile.exists())
        self.assertFalse(_gone(pid))

    def test_process_still_alive_after_signal_keeps_record(self):
        self.assertEqual(self.run_script("start").returncode, 0)
        pid = int(self.record()["pid"])
        r = self.run_script("stop", kill="kill_log_only")   # "succeeds" but the process stays alive
        self.assertEqual(r.returncode, 4, r.stderr)
        self.assertIn("still alive", r.stderr)
        self.assertTrue(self.pidfile.exists())
        self.assertFalse(_gone(pid))

    # --- foreign / reused PIDs are never signalled ---------------------------------------------
    def test_foreign_pid_with_right_start_time_is_not_signalled(self):
        s = self.sleeper()   # unrelated process (not started by serve.sh): wrong cmdline/cwd/token
        self.write_record(s.pid, _start_time(s.pid))
        r = self.run_script("stop", kill="kill_log_only")
        self.assertEqual(r.returncode, 3, r.stderr)
        self.assertIn("not ours", r.stderr)
        self.assertEqual(self.kill_calls(), [])
        self.assertTrue(self.pidfile.exists())
        self.assertIsNone(s.poll())

    def test_reused_pid_start_time_mismatch_is_not_signalled(self):
        s = self.sleeper()
        self.write_record(s.pid, str(int(_start_time(s.pid)) + 12345))
        r = self.run_script("stop", kill="kill_log_only")
        self.assertEqual(r.returncode, 3, r.stderr)
        self.assertIn("start time differs", r.stderr)
        self.assertEqual(self.kill_calls(), [])

    def test_pid_1_is_never_signalled(self):
        self.write_record(1, _start_time(1))
        r = self.run_script("stop", kill="kill_log_only")
        self.assertEqual(r.returncode, 3, r.stderr)
        self.assertEqual(self.kill_calls(), [])

    def test_record_from_another_checkout_is_refused(self):
        self.assertEqual(self.run_script("start").returncode, 0)
        rec = self.record()
        self.write_record(rec["pid"], rec["start"], token=rec["token"], checkout="/somewhere/else")
        r = self.run_script("stop", kill="kill_log_only")
        self.assertEqual(r.returncode, 3, r.stderr)
        self.assertEqual(self.kill_calls(), [])

    def test_wrong_token_is_refused(self):
        self.assertEqual(self.run_script("start").returncode, 0)
        rec = self.record()
        self.write_record(rec["pid"], rec["start"], token="f" * 32)
        r = self.run_script("stop", kill="kill_log_only")
        self.assertEqual(r.returncode, 3, r.stderr)
        self.assertIn("launch token", r.stderr)
        self.assertEqual(self.kill_calls(), [])

    # --- pid file anomalies -------------------------------------------------------------------
    def test_pidfile_anomalies_are_refused_without_signals(self):
        s = self.sleeper()
        cases = {
            "malformed": lambda: (self.pidfile.write_text("garbage\n"), os.chmod(self.pidfile, 0o600)),
            "bad pid": lambda: self.write_record("abc", "1"),
            "extra key": lambda: self.write_record(s.pid, _start_time(s.pid), extra_line="note=x"),
            "mode 644": lambda: self.write_record(s.pid, _start_time(s.pid), mode=0o644),
            "symlink": lambda: (self.write_record(s.pid, _start_time(s.pid)),
                                os.rename(self.pidfile, self.tmp / "real.pid"),
                                os.symlink(self.tmp / "real.pid", self.pidfile)),
        }
        if os.geteuid() == 0:
            cases["foreign owner"] = lambda: (self.write_record(s.pid, _start_time(s.pid)), os.chown(self.pidfile, 65534, 65534))
        for name, make in cases.items():
            with self.subTest(case=name):
                if self.pidfile.exists() or self.pidfile.is_symlink():
                    self.pidfile.unlink()
                make()
                r = self.run_script("stop", kill="kill_log_only")
                self.assertEqual(r.returncode, 3, f"{name}: {r.stderr}")
                self.assertEqual(self.kill_calls(), [])
                self.assertTrue(self.pidfile.exists() or self.pidfile.is_symlink(), f"{name}: record must be kept")
                r = self.run_script("start", kill="kill_log_only")
                self.assertEqual(r.returncode, 3, f"{name}: start must refuse to overwrite: {r.stderr}")
                self.assertFalse(self.marker.exists())
        self.assertIsNone(s.poll())

    def test_stale_record_of_dead_own_process_is_cleared(self):
        p = subprocess.Popen(["sleep", "0"])
        p.wait()
        self.write_record(p.pid, "1")
        r = self.run_script("stop", kill="kill_log_only")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("already gone", r.stdout)
        self.assertEqual(self.kill_calls(), [])
        self.assertFalse(self.pidfile.exists())
