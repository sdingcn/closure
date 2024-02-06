import subprocess
import sys
from typing import Callable

def run_and_read(cmd: str, inp: str) -> str:
    return subprocess.run(cmd,
        input = inp,
        stdout = subprocess.PIPE,
        universal_newlines = True,
        timeout = 60
    ).stdout

def checker(i: str, o: str) -> bool:
    try:
        raw_o = run_and_read(['python3', 'src/closure.py'], i)
    except subprocess.TimeoutExpired:
        sys.stderr.write('*** Timeout expired\n')
        return False
    if raw_o != o:
        sys.stderr.write(f'*** Expected: [{o}], Got: [{raw_o}]\n')
        return False
    return True

if __name__ == '__main__':
    tests = [
(
'''\
letrec (
  leaf = lambda () {
    lambda () { 0 }
  }
  node = lambda (value left right) {
    lambda () { 1 }
  }
  dfs = lambda (tree) {
    if (.< (tree) 1) then 0
    else [
      (dfs &left tree)
      (.send 0 &value tree)
      (dfs &right tree)
    ]
  }
) {
  # in-order traversal
  (dfs
    (node 4
      (node 2
        (node 1 (leaf) (leaf))
        (node 3 (leaf) (leaf)))
      (node 5 (leaf) (leaf))))
}
'''
,
'''\
[Note] output buffer:
(0, 1)
(0, 2)
(0, 3)
(0, 4)
(0, 5)
[Note] evaluation value = 0
'''
),
(
'''\
letrec (
  sum = lambda (n s) {
    if (.< n 1) then s
    else (sum (.- n 1) (.+ n s))
  }
) {
  (.send 0 (sum 10000 0))
}
'''
,
'''\
[Note] output buffer:
(0, 50005000)
[Note] evaluation value = <void>
'''
)
    ]
    for i, test in enumerate(tests):
        sys.stderr.write(f'(\nRunning on test {i + 1}\n')
        if not checker(*test):
            sys.exit(f'*** Failed on test {i + 1}')
        sys.stderr.write(')\n')
    sys.stderr.write(f'\nPassed all {i + 1} tests\n')
