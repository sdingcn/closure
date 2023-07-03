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

def check_io(batch: str) -> Callable:
    if batch == 'expr':
        prefix = ['python3', 'src/exprscript.py']
    elif batch == 'py':
        prefix = ['python3']
    else:
        sys.exit(f'*** Unknown batch {batch}')
    def checker(path: str, i: str, o: str) -> bool:
        try:
            raw_o = run_and_read(prefix + [path], i)
        except subprocess.TimeoutExpired:
            sys.stderr.write('*** Timeout expired\n')
            return False
        if raw_o != o:
            sys.stderr.write(f'*** Expected: [{o}], Got: [{raw_o}]\n')
            return False
        return True
    return checker

if __name__ == '__main__':
    tests = [
        ('test/average.expr', '', '500943/77000\n'),
        ('test/binary-tree.expr', '',
'''\
1
2
3
4
5
'''),
        ('test/comprehensive.expr', '', '01' * 17),
        ('test/coroutines.expr', '',
'''\
main
task 1
main
task 2
main
task 3
'''),
        ('test/gcd.expr', '100\n0\n', '100\n'),
        ('test/gcd.expr', '0\n100\n', '100\n'),
        ('test/gcd.expr', '30\n30\n', '30\n'),
        ('test/gcd.expr', '25\n45\n', '5\n'),
        ('test/gcd.expr', '7\n100\n', '1\n'),
        ('test/intensive.expr', '', '50005000\n'),
        ('test/lazy-evaluation.expr', '',
'''\
3
2
1
thunk
'''),
        ('test/multi-stage.expr', '',
'''\
EVAL
hello world
hello world
'''),
        ('test/oop.expr', '',
'''\
1
2
100
2
'''),
        ('test/values.expr', '',
'''\
<void>
1/2
str
<closure evaluated at (SourceLocation 5 7)>
<continuation evaluated at (SourceLocation 6 7)>
'''),
        ('test/y-combinator.expr', '', '1 120 3628800\n'),
        ('src/interaction-examples.py', '', '-5\neman\n')
    ]
    for i, test in enumerate(tests):
        sys.stderr.write(f'(\nRunning on test {i + 1}\n')
        if not check_io(test[0].split('.')[-1])(*test):
            sys.exit(f'*** Failed on test {i + 1}')
        sys.stderr.write(')\n')
    sys.stderr.write(f'\nPassed all {i + 1} tests\n')
