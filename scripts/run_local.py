"""Run the local FastAPI and Streamlit processes in the current Python environment."""
import argparse
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.request
import urllib.error

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--api-port",type=int,default=8000)
    parser.add_argument("--ui-port",type=int,default=8501)
    args=parser.parse_args()
    env={**os.environ,"PHISHSHIELD_ROOT":str(ROOT),"PHISHSHIELD_API_URL":f"http://127.0.0.1:{args.api_port}",
         "PYTHONPATH":str(ROOT/"src")+os.pathsep+os.environ.get("PYTHONPATH",""),"PHISHSHIELD_ISOLATED_EGRESS":"0"}
    commands=[["uvicorn","phishshield.api.app:app","--host","127.0.0.1","--port",str(args.api_port)],
              ["streamlit","run",str(ROOT/"src/phishshield/ui/app.py"),"--server.address","127.0.0.1","--server.port",str(args.ui_port),
               "--server.headless","true","--browser.gatherUsageStats","false","--server.maxUploadSize","8"]]
    control=ROOT/".runtime"/f"{args.api_port}-{args.ui_port}.stop"
    control.parent.mkdir(exist_ok=True)
    control.unlink(missing_ok=True)
    procs=[]
    try:
        for index,command in enumerate(commands):
            procs.append(subprocess.Popen([sys.executable,"-m",*command],env=env,cwd=ROOT))
            if index == 0:
                deadline = time.monotonic() + 60
                while time.monotonic() < deadline and procs[0].poll() is None:
                    try:
                        with urllib.request.urlopen(env["PHISHSHIELD_API_URL"]+"/ready",timeout=3) as ready:
                            if ready.status == 200:
                                break
                    except OSError:
                        time.sleep(0.3)
                else:
                    raise RuntimeError("API readiness failed")
        print(f"Streamlit http://127.0.0.1:{args.ui_port}  |  Swagger {env['PHISHSHIELD_API_URL']}/docs",flush=True)
        while all(p.poll() is None for p in procs):
            if control.exists():
                return 0
            time.sleep(0.5)
        return next(p.returncode for p in procs if p.returncode is not None)
    except KeyboardInterrupt:
        return 0
    finally:
        control.unlink(missing_ok=True)
        for p in procs:
            if p.poll() is None:
                p.terminate()
            p.wait()


if __name__=="__main__":
    sys.exit(main())

