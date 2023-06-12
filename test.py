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
            sys.stderr.write(f'*** Expected: {o}, Got: {raw_o1}\n')
            return False
        else:
            return True

def main():
    tests = [
        ('test/abs.expr', '101', '(Integer 101)\n'),
        ('test/abs.expr', '0', '(Integer 0)\n'),
        ('test/abs.expr', '-501', '(Integer 501)\n'),

        ('test/binary-tree.expr', '', '1\n2\n3\n4\n5\nVoid\n'),
        
        ('test/comments.expr', '', 
            '123\n'
            '456 # message 2\n'
            '789\n'
            'Void\n'
        ),

        ('test/coroutines.expr', '',
            'main\n'
            'task 1\n'
            'main\n'
            'task 2\n'
            'main\n'
            'task 3\n'
            'Void\n'
        ),

        ('test/dynamic-scope.expr', '', '100\n200\nVoid\n'),

        ('test/echo.expr', '', 'Void\n'),
        ('test/echo.expr', '123 \n', '123 \nVoid\n'),
        ('test/echo.expr', '100', '100\nVoid\n'),
        ('test/echo.expr', ' \n  \n\n', ' \n  \n\nVoid\n'),

        ('test/exception.expr', '',
            'call n = 2\n'
            'call n = 1\n'
            'call n = 0\n'
            'return n = 0\n'
            'return n = 1\n'
            'return n = 2\n'
            'call n = 2\n'
            'call n = 1\n'
            'call n = 0\n'
            'exception\n'
            'Void\n'
        ),

        ('test/gcd.expr', '100\n0\n', '100\nVoid\n'),
        ('test/gcd.expr', '0\n100\n', '100\nVoid\n'),
        ('test/gcd.expr', '30\n30\n', '30\nVoid\n'),
        ('test/gcd.expr', '25\n45\n', '5\nVoid\n'),
        ('test/gcd.expr', '7\n100\n', '1\nVoid\n'),

        ('test/intensive.expr', '', '(Integer 50005000)\n'),

        ('test/lexical-scope.expr', '', '1\n100\nVoid\n'),

        ('test/mixed-scope.expr', '', '1\n303\nVoid\n'),

        ('test/multi-stage.expr', '', 'EVAL\nVoid\n'),

        ('test/mutual-recursion.expr', '', '10\n9\n8\n7\n6\n5\n4\n3\n2\n1\n0\nVoid\n'),

        ('test/oop.expr', '', '1\n2\n100\n2\nVoid\n'),

        ('test/quicksort.expr', '0\n', 'Void\n'),
        ('test/quicksort.expr', '1\n303\n', '303\nVoid\n'),
        ('test/quicksort.expr', '3\n1\n3\n7\n', '1\n3\n7\nVoid\n'),
        ('test/quicksort.expr', '5\n5\n4\n3\n2\n1\n', '1\n2\n3\n4\n5\nVoid\n'),
        ('test/quicksort.expr', '6\n8\n-1\n3\n0\n6\n-5\n', '-5\n-1\n0\n3\n6\n8\nVoid\n'),

        ('test/string-literals.expr', '',
            "aaa\"\n"
            "bbb\\\"\n"
            "ccc\\\n"
            "dddeee\n"
            "fff\n"
            "ggg\n"
            "Void\n"
        ),

        ('test/string-reverse.expr', "abcde\n", "edcba\nVoid\n"),
        ('test/string-reverse.expr', "12 ccc\n", "ccc 21\nVoid\n"),
        ('test/string-reverse.expr', "\t <>///\n", "///>< \t\nVoid\n"),

        ('test/type.expr', '', '0\n1\n2\n3\n4\nVoid\n')
    ]
    cnt = 0
    for test in tests:
        cnt += 1
        sys.stderr.write(f'Running on test {cnt}, program\n{test[0]}\nwith input\n{test[1]}\n')
        if not check_io(*test):
            sys.exit(f'*** Failed on test {cnt}, program\n{test[0]}\nwith input\n{test[1]}')
    sys.stderr.write(f'Passed all {cnt} tests\n')

if __name__ == '__main__':
    main()
