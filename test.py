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

def build() -> None:
    pass

def check(i: str, o: str) -> bool:
    try:
        raw_o = run_and_read(['src/build/cvm'], i)
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
  leaf = lambda ()
    lambda () 0
  node = lambda (value left right)
    lambda () 1
  dfs = lambda (tree)
    if (.< (tree) 1)
       0
       [
         (dfs &left tree)
         (.send 0 &value tree)
         (dfs &right tree)
       ]
)
  # in-order traversal
  (dfs
    (node 4
      (node 2
        (node 1 (leaf) (leaf))
        (node 3 (leaf) (leaf)))
      (node 5 (leaf) (leaf))))
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
  sum = lambda (n s)
    if (.< n 1)
       s
       (sum (.- n 1) (.+ n s))
)
  (.send 0 (sum 10000 0))
'''
,
'''\
[Note] output buffer:
(0, 50005000)
[Note] evaluation value = <void>
'''
),
(
'''\
letrec (
  x = 0
  change = lambda (y v) set y v
) [
  set x 1
  (.send 0 x)
  set x 2
  (.send 0 x)
  set x 3
  (.send 0 x)
  (change x 4)
  (.send 0 x)
  (change x 5)
  (.send 0 x)
  letrec (z = x) set z 6
  (.send 0 x)
  while (.< x 10) set x (.+ 1 x)
  (.send 0 x)
]
'''
,
'''\
[Note] output buffer:
(0, 1)
(0, 2)
(0, 3)
(0, 4)
(0, 5)
(0, 5)
(0, 10)
[Note] evaluation value = <void>
'''
)
    ]
    build()
    # for i, test in enumerate(tests):
    #     sys.stderr.write(f'>>> Running on test {i + 1}\n')
    #     if not check(*test):
    #         sys.exit(f'*** Failed on test {i + 1}')
    # sys.stderr.write(f'>>> Passed all {i + 1} tests\n')
