import sys
from collections import deque

# intrinsics

IMAP = {
    '+': ,
    '-': ,
    '*': ,
    '/': ,
    '%': ,
    '<': ,
    'void': ,
    'get': ,
    'put': ,
    'gc': ,
    'error':
}

# lexer

def lex(source: str) -> deque[str]:
    chars = deque(source)

    def next_token() -> str:
        while chars and chars[0].isspace():
            chars.popleft()
        if chars:
            if chars[0].isdigit():
                token = ''
                while chars and chars[0].isdigit():
                    token += chars.popleft()
            elif chars[0] in ('-', '+') and chars[1].isdigit():
                token = chars.popleft()
                while chars and chars[0].isdigit():
                    token += chars.popleft()
            elif chars[0].isalpha():
                token = ''
                while chars and chars[0].isalpha():
                    token += chars.popleft()
            elif chars[0] in ('(', ')', '{', '}', '[', ']', '+', '-', '*', '/', '%', '<'):
                token = chars.popleft()
            return token
        else:
            return ''

    tokens = deque()
    while True:
        token = next_token()
        if token:
            tokens.append(token)
        else:
            break
    return tokens

# AST and parser

class Expr:
    pass

class Int(Expr):

    def __init__(self, value: int):
        self.value = value

class Var(Expr):

    def __init__(self, name: str):
        self.name = name

class Lambda(Expr):

    def __init__(self, var_list: list[Var], expr: Expr):
        self.var_list = var_list
        self.expr = expr

class Letrec(Expr):

    def __init__(self, var_expr_list: list[tuple[Var, Expr]], expr: Expr):
        self.var_expr_list = var_expr_list
        self.expr = expr

class If(Expr):

    def __init__(self, cond: Expr, branch1: Expr, branch2: Expr):
        self.cond = cond
        self.branch1 = branch1
        self.branch2 = branch2

class IntrinsicCall(Expr):

    def __init__(self, intrinsic: str, arg_list: list[Expr]):
        self.intrinsic = intrinsic
        self.arg_list = arg_list

class Call(Expr):

    def __init__(self, fun: Expr, arg_list: list[Expr]):
        self.fun = fun
        self.arg_list = arg_list

class Seq(Expr):

    def __init__(self, expr_list: list[Expr]):
        self.expr_list = expr_list

def parse(tokens: deque[str]) -> Node:

    def is_int(s: str) -> bool:
        try:
            int(s)
            return True
        except ValueError:
            return False

    def is_intrinsic(s: str) -> bool:
        return s in []

    def is_var(s: str) -> bool:
        return s.isalpha()

    def parse_int() -> Int:
        value = int(tokens.popleft())
        return Int(value)

    def parse_var() -> Var:
        name = tokens.popleft()
        return Var(name)

    def parse_lambda() -> Lambda:
        tokens.popleft() # lambda
        tokens.popleft() # (
        var_list = []
        while tokens[0].isalpha():
            var_list.append(parse_var())
        tokens.popleft() # )
        tokens.popleft() # {
        expr = parse_expr()
        tokens.popleft() # }
        return Lambda(var_list, expr)

    def parse_letrec() -> Letrec:
        tokens.popleft() # letrec
        tokens.popleft() # (
        var_expr_list = []
        while tokens[0].isalpha():
            v = parse_var()
            tokens.popleft() # =
            e = parse_expr()
            var_expr_list.append((v, e))
        tokens.popleft() # )
        tokens.popleft() # {
        expr = parse_expr()
        tokens.popleft() # }
        return Letrec(var_expr_list, expr)

    def parse_if() -> If:
        tokens.popleft() # if
        cond = parse_expr()
        tokens.popleft() # then
        branch1 = parse_expr()
        tokens.popleft() # else
        branch2 = parse_expr()
        return If(cond, branch1, branch2)

    def parse_call() -> Call:
        tokens.popleft() # (
        fun = parse_expr()
        arg_list = []
        while tokens[0] != ')':
            arg_list.append(parse_expr())
        tokens.popleft() # )
        return Call(fun, arg_list)

    def parse_seq() -> Seq:
        tokens.popleft() # [
        expr_list = []
        while tokens[0] != ']':
            expr_list.append(parse_expr())
        tokens.popleft() # ]
        return Seq(expr_list)

    def parse_expr() -> Expr:
        if is_int(tokens[0]):
            return parse_int()
        elif is_var(tokens[0]):
            return parse_var()
        elif tokens[0] == 'lambda':
            return parse_lambda()
        elif tokens[0] == 'letrec':
            return parse_letrec()
        elif tokens[0] == 'if':
            return parse_if()
        elif tokens[0] == '(':
            return parse_call()
        elif tokens[0] == '[':
            return parse_seq()
    
    return parse_expr()

# runtime classes

class Value:
    pass

class Integer(Value):

    def __init__(self, value: int):
        self.value = value

class Closure(Value):

    def __init__(self, env: list[tuple[str, int]], fun: Lambda):
        self.env = env
        self.fun = fun

class Void(Value):

    def __init__(self):
        pass

class Frame:

    def __init__(self):
        self.env = []

    def push(self, var: str, loc: int) -> None:
        self.env.append((var, loc))

    def pop(self) -> None:
        self.env.pop()

# garbage collector

def collect(store: dict[int, Value], stack: list[tuple[str, int]]) -> None:
    visited = set()

    def mark(location: int) -> None:
        visited.add(location)
        if type(store[location]) == Closure:
            for var, loc in store[location].env:
                if loc not in visited:
                    mark(loc)

    def sweep() -> None:
        to_remove = set()
        for k, v in store.items():
            if k not in visited:
                to_remove.add(k)
        for k in to_remove:
            del store[k]

    for frame in stack:
        for var, loc in frame.env:
            mark(loc)
    n = sweep()
    sys.stderr.write(f'GC: collected {n} locations\n')

# interpreter

def interpret(tree: Expr) -> Value:
    store = {}
    location = 0

    def new(value: Value) -> int:
        store[location] = value
        location += 1
        return location

    stack = []

    def recurse(node: Expr, env: list[tuple[str, int]]) -> Value:
        pass

    return recurse(tree, [])

# main entry

def main(source) -> None:
    tokens = lex(source)
    tree = parse(tokens)
    result = interpret(tree)
    if type(result) == Integer:
        print(result.value)
    elif type(result) == Closure:
        print('Closure')
    elif type(result) == Void:
        print('Void')

if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit(f'Usage: python3 {sys.argv[0]} <source-file>')
    with open(sys.argv[1], 'r') as f:
        main(f.read())
