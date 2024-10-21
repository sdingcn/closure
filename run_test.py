import os
import os.path
import subprocess
import sys
from typing import List, Tuple, Union

def execute(cmd: List[str], i: Union[None, str] = None) -> Tuple[int, str, str]:
    result = subprocess.run(
        cmd,
        text = True,
        input = i,
        capture_output = True
    )
    return (result.returncode, result.stdout, result.stderr)

if __name__ == "__main__":
    if not os.path.exists("build/closure"):
        sys.exit("please build the project before running the tests")
    for dirpath, _, filenames in os.walk("test/"):
        for filename in filenames:
            if filename.endswith(".clo"):
                filepath = os.path.join(dirpath, filename)
                print(f"running test {filepath} ... ", end = "")
                sys.stdout.flush()
                inpath = filepath[:-3] + "in"
                outpath = filepath[:-3] + "out"
                errpath = filepath[:-3] + "err"
                with open(inpath, "r") as f:
                    res = execute(["build/closure", filepath], f.read())
                with open(outpath, "r") as g:
                    out = g.read()
                with open(errpath, "r") as h:
                    err = h.read()
                if ((res[0] == 0) == (err == "") and res[1] == out and res[2] == err):
                    print("passed")
                else:
                    sys.exit(f"failed\nres = {res}\ntruth = {(out, err)}")
                sys.stdout.flush()
