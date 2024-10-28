import json
import os
import os.path
import shutil
import subprocess
import sys
import time
from typing import List, Tuple, Union

def execute(cmd: List[str], i: Union[None, str] = None) -> Tuple[int, str, str]:
    result = subprocess.run(
        cmd,
        text = True,
        input = i,
        capture_output = True
    )
    return (result.returncode, result.stdout, result.stderr)

def build() -> None:
    print("building the project ... ", end = "")
    sys.stdout.flush()
    start = time.time()
    if os.path.exists("build"):
        shutil.rmtree("build")
    os.mkdir("build")
    execute(["cmake", "-DCMAKE_BUILD_TYPE:STRING=Release", "-S", "src", "-B", "build"])
    execute(["cmake", "--build", "build"])
    end = time.time()
    print(f"completed in {end - start:.3f} seconds")

def test() -> None:
    for dirpath, _, filenames in os.walk("test/"):
        for filename in filenames:
            if filename.endswith(".clo"):
                filepath = os.path.join(dirpath, filename)
                print(f"running test {filepath} ... ", end = "")
                sys.stdout.flush()
                iopath = filepath[:-3] + "io"
                with open(iopath, "r") as f:
                    io = json.loads(f.read())
                start = time.time()
                res = execute(["build/closure", filepath], io["in"])
                end = time.time()
                if ((res[0] == 0) == (io["err"] == "") and
                    res[1] == io["out"] and
                    res[2] == io["err"]):
                    print(f"passed in {end - start:.3f} seconds")
                else:
                    sys.exit(f'failed\nres = {res}\ntruth = {(io["out"], io["err"])}')
                sys.stdout.flush()

if __name__ == "__main__":
    build()
    test()
