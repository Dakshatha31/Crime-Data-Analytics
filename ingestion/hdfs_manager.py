"""
HDFS Manager: Unified bridge for Apache Hadoop HDFS operations.
Supports native Hadoop CLI (hdfs.cmd dfs) with graceful fallback and synchronization
to a structured local HDFS store (hdfs_store/crime/...).
"""
import os
import shutil
import subprocess
from pathlib import Path
from typing import List, Dict, Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOCAL_HDFS_ROOT = PROJECT_ROOT / "hdfs_store"
HADOOP_HOME = os.getenv("HADOOP_HOME", r"C:\hadoop-3.3.6")
HDFS_CMD = os.path.join(HADOOP_HOME, "bin", "hdfs.cmd") if os.path.exists(HADOOP_HOME) else "hdfs"


class HDFSManager:
    def __init__(self, local_root: Path = LOCAL_HDFS_ROOT):
        self.local_root = local_root
        self.local_root.mkdir(parents=True, exist_ok=True)
        self.hadoop_cli_available = os.path.exists(HDFS_CMD) or shutil.which("hdfs") is not None

    def _resolve_local_path(self, hdfs_path: str) -> Path:
        """Map HDFS URI/path like /crime/raw/datacenter/data.csv to local HDFS store path."""
        clean_path = hdfs_path.strip()
        if clean_path.startswith("hdfs://"):
            parts = clean_path.split("/", 3)
            clean_path = "/" + parts[3] if len(parts) > 3 else "/"
        clean_path = clean_path.lstrip("/\\").replace("/", os.sep)
        return self.local_root / clean_path

    def mkdir(self, hdfs_path: str) -> bool:
        """Create directory in HDFS and local mirrored store."""
        target_dir = self._resolve_local_path(hdfs_path)
        target_dir.mkdir(parents=True, exist_ok=True)

        if self.hadoop_cli_available:
            try:
                subprocess.run(
                    [HDFS_CMD, "dfs", "-mkdir", "-p", hdfs_path],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=8
                )
            except Exception:
                pass
        return True

    def put_file(self, local_src: str | Path, hdfs_dest: str) -> Dict[str, Any]:
        """Copy a file from local filesystem into HDFS (and local mirror)."""
        src = Path(local_src).resolve()
        if not src.exists():
            raise FileNotFoundError(f"Source file not found: {src}")

        target_dest = self._resolve_local_path(hdfs_dest)
        if target_dest.is_dir() or str(hdfs_dest).endswith("/"):
            target_dest = target_dest / src.name
        else:
            target_dest.parent.mkdir(parents=True, exist_ok=True)

        # Copy to local mirror store
        shutil.copy2(str(src), str(target_dest))

        # Try Hadoop CLI put (Windows or WSL)
        cli_success = False
        cli_msg = ""
        if self.hadoop_cli_available:
            try:
                res = subprocess.run(
                    [HDFS_CMD, "dfs", "-put", "-f", str(src), hdfs_dest],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=10
                )
                cli_success = res.returncode == 0
                cli_msg = res.stdout if cli_success else res.stderr
            except Exception as e:
                cli_msg = str(e)

        # Also support WSL Hadoop if available
        if not cli_success and shutil.which("wsl"):
            try:
                wsl_src = str(src.resolve()).replace("\\", "/").replace("D:", "/mnt/d").replace("d:", "/mnt/d").replace("C:", "/mnt/c").replace("c:", "/mnt/c")
                wsl_cmd = f"export JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64; export HADOOP_HOME=/opt/hadoop; /opt/hadoop/bin/hdfs dfs -mkdir -p {hdfs_dest}; /opt/hadoop/bin/hdfs dfs -put -f {wsl_src} {hdfs_dest}"
                wsl_res = subprocess.run(
                    ["wsl", "-e", "bash", "-c", wsl_cmd],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=15
                )
                if wsl_res.returncode == 0:
                    cli_success = True
                    cli_msg = "Successfully ingested into WSL Apache Hadoop HDFS"
            except Exception:
                pass

        return {
            "status": "success",
            "source": str(src),
            "hdfs_destination": hdfs_dest,
            "local_mirror_path": str(target_dest),
            "bytes_copied": target_dest.stat().st_size,
            "hadoop_cli_executed": self.hadoop_cli_available,
            "hadoop_cli_success": cli_success,
            "message": cli_msg.strip() if cli_msg else "Copied to HDFS namespace"
        }

    def get_file(self, hdfs_src: str, local_dest: str | Path) -> Dict[str, Any]:
        """Retrieve a file from HDFS into local destination."""
        dest = Path(local_dest).resolve()
        dest.parent.mkdir(parents=True, exist_ok=True)

        # Retrieve from local mirror
        mirror_src = self._resolve_local_path(hdfs_src)
        if mirror_src.is_dir():
            # Find first part-* or csv file if directory
            candidates = list(mirror_src.glob("part-*")) + list(mirror_src.glob("*.csv")) + list(mirror_src.glob("*.txt"))
            if candidates:
                mirror_src = candidates[0]

        if not mirror_src.exists():
            raise FileNotFoundError(f"HDFS resource not found in store: {hdfs_src}")

        shutil.copy2(str(mirror_src), str(dest))
        return {
            "status": "success",
            "hdfs_source": hdfs_src,
            "local_destination": str(dest),
            "bytes_retrieved": dest.stat().st_size
        }

    def list_dir(self, hdfs_path: str = "/crime") -> List[Dict[str, Any]]:
        """List files in HDFS path."""
        target = self._resolve_local_path(hdfs_path)
        if not target.exists():
            return []

        results = []
        for root, dirs, files in os.walk(target):
            rel_dir = "/" + os.path.relpath(root, self.local_root).replace("\\", "/")
            for f in files:
                f_path = Path(root) / f
                rel_file = "/" + os.path.relpath(f_path, self.local_root).replace("\\", "/")
                results.append({
                    "hdfs_path": rel_file,
                    "filename": f,
                    "size_bytes": f_path.stat().st_size,
                    "modified": f_path.stat().st_mtime,
                    "directory": rel_dir
                })
        return results

    def read_text(self, hdfs_path: str) -> str:
        """Read content of file in HDFS store."""
        target = self._resolve_local_path(hdfs_path)
        if target.is_dir():
            parts = list(target.glob("part-*")) + list(target.glob("*.csv"))
            if parts:
                target = parts[0]
        if not target.exists():
            raise FileNotFoundError(f"HDFS file not found: {hdfs_path}")
        return target.read_text(encoding="utf-8")

    def write_text(self, hdfs_path: str, content: str) -> Dict[str, Any]:
        """Write text file directly into HDFS namespace."""
        target = self._resolve_local_path(hdfs_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return {
            "status": "success",
            "hdfs_path": hdfs_path,
            "local_path": str(target),
            "size_bytes": len(content.encode("utf-8"))
        }


# Singleton instance
hdfs_manager = HDFSManager()
