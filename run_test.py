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
                with open(inpath, "r") as f:
                    res = execute(["build/closure", filepath], f.read())
                with open(outpath, "r") as g:
                    ref = g.read()
                if (res[0] == 0 and res[1] == ref and res[2] == ""):
                    print("passed")
                else:
                    sys.exit("failed")
                sys.stdout.flush()
