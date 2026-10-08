"""Run UMAP in an isolated process and poll it from the Tk event loop."""

import pickle
import subprocess
import sys
import tempfile
from pathlib import Path


class UmapProcessError(RuntimeError):
    pass


class UmapJob:
    def __init__(self, src_df, **params):
        self._temp = tempfile.TemporaryDirectory(prefix="behavior_senpai_umap_")
        self._process = None
        self._log = None
        self._closed = False
        root = Path(self._temp.name)
        self._result = root / "result.pkl"
        self._log_path = root / "worker.log"
        try:
            # Only numerical input crosses the boundary, never Tk objects or attrs.
            columns = list(dict.fromkeys(["timestamp", *params["tar_cols"]]))
            data = src_df.loc[:, columns].copy()
            data.attrs = {}
            request = root / "request.pkl"
            with request.open("wb") as stream:
                pickle.dump((data, params), stream, protocol=pickle.HIGHEST_PROTOCOL)
            self._log = self._log_path.open("wb")
            self._process = subprocess.Popen(
                [sys.executable, "-X", "utf8", "-u", str(Path(__file__).with_name("umap_worker.py")), str(request), str(self._result)],
                stdin=subprocess.DEVNULL,
                stdout=self._log,
                stderr=subprocess.STDOUT,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
        except BaseException:
            self.close()
            raise

    def poll(self):
        """Return None while running, a DataFrame on success, or raise on failure."""
        if self._closed:
            raise UmapProcessError("UMAP calculation has been closed.")
        code = self._process.poll()
        if code is None:
            return None
        try:
            self._log.close()
            log = self._log_path.read_text(encoding="utf-8", errors="replace")
            if log:
                print(log, end="" if log.endswith("\n") else "\n")
            if code != 0:
                raise UmapProcessError(f"UMAP process exited with code {code}.\n\n{log[-4000:]}")
            import pandas as pd

            return pd.read_pickle(self._result)
        finally:
            self.close()

    def close(self):
        """Stop outstanding work and remove temporary input, output and logs."""
        if self._closed:
            return
        self._closed = True
        if self._process is not None and self._process.poll() is None:
            self._process.terminate()
            try:
                self._process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self._process.kill()
                self._process.wait()
        if self._log is not None:
            self._log.close()
        self._temp.cleanup()
