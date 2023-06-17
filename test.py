import subprocess
import sys

def run_and_read(cmd: str, inp: str) -> str:
    return subprocess.run(cmd,
        input = inp,
        stdout = subprocess.PIPE,
        universal_newlines = True,
        timeout = 60
    ).stdout

def check_io(prog: str, i: str, o: str) -> bool:
    try:
        raw_o1 = run_and_read(['python3', 'src/interpreter.py', 'time', prog], i)
    except subprocess.TimeoutExpired:
        sys.stderr.write('*** Timeout expired on time mode\n')
        return False
    try:
        raw_o2 = run_and_read(['python3', 'src/interpreter.py', 'space', prog], i)
    except subprocess.TimeoutExpired:
        sys.stderr.write('*** Timeout expired on space mode\n')
        return False
    if raw_o1 != raw_o2:
        sys.stderr.write('*** Time mode and space mode give different outputs.\n')
        return False
    else:
        if raw_o1 != o:
            sys.stderr.write(f'*** Expected: [{o}], Got: [{raw_o1}]\n')
            return False
        else:
            return True

def read_file(path: str) -> str:
    with open(path, 'r', encoding = 'utf-8') as f:
        return f.read()

def main():
    tests = [
        ('test/binary-tree.expr', '', '1\n2\n3\n4\n5\n<void>\n'),
        
        ('test/coroutines.expr', '',
            'main\n'
            'task 1\n'
            'main\n'
            'task 2\n'
            'main\n'
            'task 3\n'
            '<void>\n'
        ),

        ('test/gcd.expr', '100\n0\n', '100\n<void>\n'),
        ('test/gcd.expr', '0\n100\n', '100\n<void>\n'),
        ('test/gcd.expr', '30\n30\n', '30\n<void>\n'),
        ('test/gcd.expr', '25\n45\n', '5\n<void>\n'),
        ('test/gcd.expr', '7\n100\n', '1\n<void>\n'),

        ('test/intensive.expr', '', '50005000\n'),

        ('test/lazy-evaluation.expr', '', '3\n2\n1\nthunk\n<void>\n'),

        ('test/scope.expr', '', '1\n303\n<void>\n'),

        ('test/multi-stage.expr', '', 'EVAL\nhello world\nhello world\n<void>\n'),

        ('test/oop.expr', '', '1\n2\n100\n2\n<void>\n'),

        ('test/strings-and-comments.expr', '', '''\
123
456 # message 2
aaa"
bbb\\"
ccc\\
ddd
eee
fff
ggg
<void>
'''),

        ('test/y-combinator.expr', '', '1 120 3628800\n<void>\n')
    ]
    cnt = 0
    for test in tests:
        cnt += 1
        sys.stderr.write(f'==========\n')
        sys.stderr.write(f'Running on test {cnt}, program\n{test[0]}\nwith input\n[{test[1]}]\n')
        if not check_io(*test):
            sys.exit(f'*** Failed on test {cnt}, program\n{test[0]}\nwith input\n[{test[1]}]')
    sys.stderr.write(f'Passed all {cnt} tests\n')

if __name__ == '__main__':
    main()
