#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════╗
║  KuruAgent — KuruDash Widget Metrics Server              ║
║  Zero dependencies · Python 3.6+ · Cross-platform       ║
╚══════════════════════════════════════════════════════════╝

QUICK START:
  python3 kuruagent.py          # starts on port 9977
  python3 kuruagent.py --port 8080 --host 0.0.0.0

WIDGET URLS (use in KuruDash → Widgets modal):
  http://<your-server>:9977/cpu       → {"value": 23.4}
  http://<your-server>:9977/ram       → {"value": 61.2}
  http://<your-server>:9977/disk      → {"value": 55.0}
  http://<your-server>:9977/temp      → {"value": 48.5}  (Linux)
  http://<your-server>:9977/load      → {"value": 0.82}
  http://<your-server>:9977/uptime    → {"value": "3d 12h"}
  http://<your-server>:9977/net       → {"value": 142.3}  KB/s in
  http://<your-server>:9977/docker    → {"value": 12}  (if Docker running)
  http://<your-server>:9977/all       → all metrics as one JSON object

JSON Path for all endpoints: "value"
(except /all which uses e.g. "cpu", "ram", "disk" etc.)
"""

import sys
import os
import time
import json
import argparse
import subprocess
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

# ── Config ──────────────────────────────────────────────
DEFAULT_PORT = 9977
DEFAULT_HOST = "0.0.0.0"
CORS_ORIGIN  = "*"      # set to your KuruDash hostname for security
CACHE_TTL    = 2.0      # seconds between metric refreshes

# ── Metric cache ────────────────────────────────────────
_cache = {}
_cache_ts = 0
_cache_lock = threading.Lock()

# ── Platform detection ───────────────────────────────────
IS_LINUX   = sys.platform.startswith("linux")
IS_MAC     = sys.platform == "darwin"
IS_WINDOWS = sys.platform == "win32"


# ════════════════════════════════════════════════════════
#  METRICS
# ════════════════════════════════════════════════════════

def _read_file(path):
    try:
        with open(path) as f:
            return f.read().strip()
    except Exception:
        return None

def _run(cmd):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=3)
        return r.stdout.strip() if r.returncode == 0 else None
    except Exception:
        return None

# ── CPU ─────────────────────────────────────────────────
_prev_cpu = None

def get_cpu():
    global _prev_cpu
    if IS_LINUX:
        raw = _read_file("/proc/stat")
        if not raw:
            return None
        line = raw.splitlines()[0].split()
        vals = list(map(int, line[1:]))
        idle  = vals[3] + (vals[4] if len(vals) > 4 else 0)
        total = sum(vals)
        if _prev_cpu:
            d_total = total - _prev_cpu[1]
            d_idle  = idle  - _prev_cpu[0]
            pct = 100.0 * (1 - d_idle / d_total) if d_total else 0.0
        else:
            pct = 0.0
        _prev_cpu = (idle, total)
        return round(max(0, min(100, pct)), 1)
    elif IS_MAC:
        out = _run(["top", "-l", "1", "-n", "0", "-s", "0"])
        if out:
            for line in out.splitlines():
                if "CPU usage" in line:
                    # "CPU usage: 4.16% user, 8.33% sys, 87.50% idle"
                    parts = line.split(",")
                    idle = next((p for p in parts if "idle" in p), None)
                    if idle:
                        pct = 100 - float(idle.strip().split("%")[0])
                        return round(pct, 1)
    elif IS_WINDOWS:
        out = _run(["powershell", "-Command",
            "Get-WmiObject Win32_Processor | Measure-Object -Property LoadPercentage -Average | Select-Object -ExpandProperty Average"])
        if out:
            return round(float(out), 1)
    return None

# ── RAM ─────────────────────────────────────────────────
def get_ram():
    if IS_LINUX:
        raw = _read_file("/proc/meminfo")
        if not raw:
            return None
        m = {}
        for line in raw.splitlines():
            k, v = line.split(":")[0].strip(), line.split(":")[1].strip().split()[0]
            m[k] = int(v)
        total = m.get("MemTotal", 0)
        available = m.get("MemAvailable", m.get("MemFree", 0))
        if total == 0:
            return None
        return round(100.0 * (total - available) / total, 1)
    elif IS_MAC:
        out = _run(["vm_stat"])
        if out:
            page_size = 4096
            stats = {}
            for line in out.splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    stats[k.strip()] = int(v.strip().rstrip("."))
            free  = stats.get("Pages free", 0) * page_size
            total_cmd = _run(["sysctl", "-n", "hw.memsize"])
            if total_cmd:
                total = int(total_cmd)
                used  = total - free
                return round(100.0 * used / total, 1)
    elif IS_WINDOWS:
        out = _run(["powershell", "-Command",
            "$os = Get-WmiObject Win32_OperatingSystem; [math]::Round(($os.TotalVisibleMemorySize - $os.FreePhysicalMemory) / $os.TotalVisibleMemorySize * 100, 1)"])
        if out:
            return float(out)
    return None

# ── DISK ────────────────────────────────────────────────
def get_disk():
    try:
        import shutil
        usage = shutil.disk_usage("/")
        return round(100.0 * usage.used / usage.total, 1)
    except Exception:
        return None

# ── TEMP ────────────────────────────────────────────────
def get_temp():
    if IS_LINUX:
        # Try thermal zones
        for i in range(10):
            t = _read_file(f"/sys/class/thermal/thermal_zone{i}/temp")
            if t and int(t) > 0:
                return round(int(t) / 1000.0, 1)
        # Try hwmon
        import glob
        for f in sorted(glob.glob("/sys/class/hwmon/hwmon*/temp*_input")):
            t = _read_file(f)
            if t and int(t) > 0:
                return round(int(t) / 1000.0, 1)
    elif IS_MAC:
        out = _run(["sudo", "powermetrics", "--samplers", "smc", "-n", "1", "-i", "500"])
        if out:
            for line in out.splitlines():
                if "CPU die temperature" in line:
                    return round(float(line.split(":")[1].strip().split()[0]), 1)
    return None

# ── LOAD ────────────────────────────────────────────────
def get_load():
    if IS_LINUX or IS_MAC:
        t = _read_file("/proc/loadavg") if IS_LINUX else None
        if IS_MAC or not t:
            out = _run(["uptime"])
            if out:
                import re
                m = re.search(r"load averages?: ([\d.]+)", out)
                if m:
                    return round(float(m.group(1)), 2)
            return None
        return round(float(t.split()[0]), 2)
    return None

# ── UPTIME ──────────────────────────────────────────────
def get_uptime():
    if IS_LINUX:
        raw = _read_file("/proc/uptime")
        if raw:
            secs = int(float(raw.split()[0]))
            return _fmt_uptime(secs)
    elif IS_MAC or IS_WINDOWS:
        out = _run(["uptime"])
        if out:
            return out.split(",")[0].split("up")[-1].strip() if "up" in out else out
    return None

def _fmt_uptime(secs):
    d, rem = divmod(secs, 86400)
    h, rem = divmod(rem, 3600)
    m = rem // 60
    if d > 0:
        return f"{d}d {h}h"
    elif h > 0:
        return f"{h}h {m}m"
    return f"{m}m"

# ── NETWORK ─────────────────────────────────────────────
_prev_net = None

def get_net_kbps():
    global _prev_net
    if IS_LINUX:
        raw = _read_file("/proc/net/dev")
        if raw:
            rx_total = 0
            for line in raw.splitlines()[2:]:
                parts = line.split()
                if parts:
                    rx_total += int(parts[1])
            now = time.time()
            if _prev_net:
                dt = now - _prev_net[1]
                kbps = (rx_total - _prev_net[0]) / 1024 / max(dt, 0.1)
                _prev_net = (rx_total, now)
                return round(max(0, kbps), 1)
            _prev_net = (rx_total, now)
    return None

# ── DOCKER ──────────────────────────────────────────────
def get_docker():
    out = _run(["docker", "ps", "-q"])
    if out is None:
        return None
    return len(out.splitlines()) if out else 0


# ════════════════════════════════════════════════════════
#  CACHE
# ════════════════════════════════════════════════════════

def refresh_cache():
    global _cache, _cache_ts
    data = {}
    data["cpu"]    = get_cpu()
    data["ram"]    = get_ram()
    data["disk"]   = get_disk()
    data["temp"]   = get_temp()
    data["load"]   = get_load()
    data["uptime"] = get_uptime()
    data["net"]    = get_net_kbps()
    data["docker"] = get_docker()
    with _cache_lock:
        _cache = data
        _cache_ts = time.time()

def get_cached():
    with _cache_lock:
        age = time.time() - _cache_ts
    if age > CACHE_TTL:
        refresh_cache()
    with _cache_lock:
        return dict(_cache)


# ════════════════════════════════════════════════════════
#  HTTP SERVER
# ════════════════════════════════════════════════════════

class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass  # suppress default access logs

    def send_json(self, data, status=200):
        body = json.dumps(data, default=str).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", CORS_ORIGIN)
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", CORS_ORIGIN)
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.end_headers()

    def do_GET(self):
        path = self.path.split("?")[0].rstrip("/")
        metrics = get_cached()

        routes = {
            "/cpu":    lambda m: {"value": m["cpu"]},
            "/ram":    lambda m: {"value": m["ram"]},
            "/disk":   lambda m: {"value": m["disk"]},
            "/temp":   lambda m: {"value": m["temp"]},
            "/load":   lambda m: {"value": m["load"]},
            "/uptime": lambda m: {"value": m["uptime"]},
            "/net":    lambda m: {"value": m["net"]},
            "/docker": lambda m: {"value": m["docker"],
                                   "ContainersRunning": m["docker"]},
            "/all":    lambda m: {k: v for k, v in m.items()},
            "/health": lambda m: {"status": "ok", "agent": "kuruagent"},
        }

        if path in routes:
            result = routes[path](metrics)
            # Filter out None values for cleaner output
            result = {k: v for k, v in result.items() if v is not None}
            self.send_json(result)
        elif path == "" or path == "/":
            self.send_json({
                "agent": "KuruAgent",
                "endpoints": list(routes.keys()),
                "json_path": "value",
                "note": "Point KuruDash widgets at http://this-host:<port>/<metric>"
            })
        else:
            self.send_json({"error": "Not found", "endpoints": list(routes.keys())}, 404)


# ════════════════════════════════════════════════════════
#  MAIN
# ════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="KuruAgent — KuruDash widget metrics server"
    )
    parser.add_argument("--host", default=DEFAULT_HOST,
                        help=f"Bind host (default: {DEFAULT_HOST})")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT,
                        help=f"Port (default: {DEFAULT_PORT})")
    args = parser.parse_args()

    # Initial metric fetch (pre-warms CPU delta)
    print(f"\n  KuruAgent starting…")
    refresh_cache()
    time.sleep(1)
    refresh_cache()   # second pass gives accurate CPU delta

    server = HTTPServer((args.host, args.port), Handler)

    print(f"""
╔══════════════════════════════════════════════════════════╗
║  KuruAgent is running!                                   ║
╚══════════════════════════════════════════════════════════╝

  Listening on  http://{args.host}:{args.port}
  JSON path     value

  Available endpoints:
    /cpu    /ram    /disk   /load   /temp
    /uptime /net    /docker /all    /health

  Widget URL example:
    http://<this-machine>:{args.port}/cpu

  In KuruDash → Widgets → select a preset → paste the URL
  Press Ctrl+C to stop.
""")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  KuruAgent stopped.")
        server.server_close()


if __name__ == "__main__":
    main()
