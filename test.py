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

def checker(path: str, i: str, o: str) -> bool:
    try:
        raw_o = run_and_read(['python3', 'src/closure.py', path], i)
    except subprocess.TimeoutExpired:
        sys.stderr.write('*** Timeout expired\n')
        return False
    if raw_o != o:
        sys.stderr.write(f'*** Expected: [{o}], Got: [{raw_o}]\n')
        return False
    return True

if __name__ == '__main__':
    tests = [
        ('test/binary-tree.expr', '',
'''\
1
2
3
4
5
'''),
        ('test/gcd.expr', '100\n0\n', '100\n'),
        ('test/gcd.expr', '0\n100\n', '100\n'),
        ('test/gcd.expr', '30\n30\n', '30\n'),
        ('test/gcd.expr', '25\n45\n', '5\n'),
        ('test/gcd.expr', '7\n100\n', '1\n'),
        ('test/intensive.expr', '', '50005000\n'),
    ]
    for i, test in enumerate(tests):
        sys.stderr.write(f'(\nRunning on test {i + 1}\n')
        if not checker(*test):
            sys.exit(f'*** Failed on test {i + 1}')
        sys.stderr.write(')\n')
    sys.stderr.write(f'\nPassed all {i + 1} tests\n')
