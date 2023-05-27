import sys
from collections import deque
from typing import Union, Any

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
            elif chars[0] in ('-', '+') and (len(chars) > 1 and chars[1].isdigit()):
                token = chars.popleft()
                while chars and chars[0].isdigit():
                    token += chars.popleft()
            elif chars[0].isalpha():
                token = ''
                while chars and chars[0].isalpha():
                    token += chars.popleft()
            elif chars[0] in ('(', ')', '{', '}', '[', ']', '+', '-', '*', '/', '%', '<', '='):
                token = chars.popleft()
            else:
                sys.exit(f'[Expr Lexer] error: unrecognized character "{chars[0]}"')
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

def unfold_to_string(value: Union[list[Any], tuple[Any, ...]]):
    if type(value) == list:
        s = '['
    elif type(value) == tuple:
        s = '('
    else:
        sys.exit('[Expr Internal] error: wrong type of argument given to "unfold_to_string"')
    for e in value:
        if type(e) == list or type(e) == tuple:
            s += unfold_to_string(e)
        else:
            s += str(e)
        s += ' '
    if s[-1] == ' ':
        s = s[:-1]
    if type(value) == list:
        s += ']'
    elif type(value) == tuple:
        s += ')'
    else:
        sys.exit('[Expr Internal] error: wrong type of argument given to "unfold_to_string"')
    return s

class Expr:

    def __init__(self):
        pass

    def __str__(self):
        return 'Expr'

class Int(Expr):

    def __init__(self, value: int):
        self.value = value

    def __str__(self):
        return f'(Int {self.value})'

class Var(Expr):

    def __init__(self, name: str):
        self.name = name

    def __str__(self):
        return f'(Var "{self.name}")'

class Lambda(Expr):

    def __init__(self, var_list: list[Var], expr: Expr):
        self.var_list = var_list
        self.expr = expr

    def __str__(self):
        return f'(Lambda {unfold_to_string(self.var_list)} {str(self.expr)})'

class Letrec(Expr):

    def __init__(self, var_expr_list: list[tuple[Var, Expr]], expr: Expr):
        self.var_expr_list = var_expr_list
        self.expr = expr

    def __str__(self):
        return f'(Letrec {unfold_to_string(self.var_expr_list)} {str(self.expr)})'

class If(Expr):

    def __init__(self, cond: Expr, branch1: Expr, branch2: Expr):
        self.cond = cond
        self.branch1 = branch1
        self.branch2 = branch2

    def __str__(self):
        return f'(If {str(self.cond)} {str(self.branch1)} {str(self.branch2)})'

class Icall(Expr):

    def __init__(self, intrinsic: str, arg_list: list[Expr]):
        self.intrinsic = intrinsic
        self.arg_list = arg_list

    def __str__(self):
        return f'(Icall {self.intrinsic} {unfold_to_string(self.arg_list)})'

class Call(Expr):

    def __init__(self, callee: Expr, arg_list: list[Expr]):
        self.callee = callee
        self.arg_list = arg_list

    def __str__(self):
        return f'(Call {str(self.callee)} {unfold_to_string(self.arg_list)})'

class Seq(Expr):

    def __init__(self, expr_list: list[Expr]):
        self.expr_list = expr_list

    def __str__(self):
        return f'(Seq {unfold_to_string(self.expr_list)})'

def parse(tokens: deque[str]) -> Expr:
    
    def is_int(token: str) -> bool:
        try:
            int(token)
            return True
        except ValueError:
            return False

    def is_intrinsic(token: str) -> bool:
        return token in { '+', '-', '*', '/', '%', '<', 'void', 'get', 'put', 'gc', 'exit' }

    def is_var(token: str) -> bool:
        return token.isalpha()

    def parse_int() -> Int:
        value = int(tokens.popleft())
        return Int(value)

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

    def parse_var() -> Var:
        name = tokens.popleft()
        return Var(name)

    def parse_icall() -> Icall:
        tokens.popleft() # (
        intrinsic = tokens.popleft()
        arg_list = []
        while tokens[0] != ')':
            arg_list.append(parse_expr())
        tokens.popleft() # )
        return Icall(intrinsic, arg_list)

    def parse_call() -> Call:
        tokens.popleft() # (
        callee = parse_expr()
        arg_list = []
        while tokens[0] != ')':
            arg_list.append(parse_expr())
        tokens.popleft() # )
        return Call(callee, arg_list)

    def parse_seq() -> Seq:
        tokens.popleft() # [
        expr_list = []
        while tokens[0] != ']':
            expr_list.append(parse_expr())
        tokens.popleft() # ]
        if len(expr_list) == 0:
            sys.exit('[Expr Parser] error: zero-length sequence')
        return Seq(expr_list)

    def parse_expr() -> Expr:
        if is_int(tokens[0]):
            return parse_int()
        elif tokens[0] == 'lambda':
            return parse_lambda()
        elif tokens[0] == 'letrec':
            return parse_letrec()
        elif tokens[0] == 'if':
            return parse_if()
        elif is_var(tokens[0]):
            return parse_var()
        elif tokens[0] == '(':
            if is_intrinsic(tokens[1]):
                return parse_icall()
            else:
                return parse_call()
        elif tokens[0] == '[':
            return parse_seq()
        else:
            sys.exit(f'[Expr Parser] error: unrecognized expression starting with "{tokens[0]}"')
    
    try:
        return parse_expr()
    except IndexError:
        sys.exit('[Expr Parser] error: incomplete expression')

# runtime

class Value:
    
    def __init__(self):
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

    def __init__(self, env):
        self.env = env

class Runtime:

    def __init__(self):
        self.stack = [Frame([])]
        self.store = {}
        self.location = 0

        def get() -> Integer:
            try:
                return Integer(int(input().strip()))
            except ValueError:
                sys.exit('[Expr Runtime] error: unsupported input')

        def put(a: Integer) -> Void:
            print(a.value)
            return Void()
    
        def collect(stack: list[Frame], store: dict[int, Value]) -> Void:
            visited = set()

            def mark(loc: int) -> None:
                visited.add(loc)
                if type(store[loc]) == Closure:
                    for v, l in store[loc].env:
                        if l not in visited:
                            mark(l)

            def sweep() -> None:
                to_remove = set()
                for k, v in store.items():
                    if k not in visited:
                        to_remove.add(k)
                for k in to_remove:
                    del store[k]

            for frame in stack:
                for v, l in frame.env:
                    mark(l)
            n = sweep()
            sys.stderr.write(f'[Expr Runtime] message: GC released {n} objects\n')
            return Void()

        self.intrinsics = {
            '+': lambda a, b : Integer(a.value + b.value),
            '-': lambda a, b : Integer(a.value - b.value),
            '*': lambda a, b : Integer(a.value * b.value),
            '/': lambda a, b : Integer(a.value / b.value),
            '%': lambda a, b : Integer(a.value % b.value),
            '<': lambda a, b : Integer(a.value < b.value),
            'void': lambda : Void(),
            'get': get,
            'put': put,
            'gc': lambda : collect(self.stack, self.store),
            'exit': lambda : sys.exit('[Expr Runtime] message: execution stopped by the "exit" intrinsic function')
        }


    def new(self, value: Value) -> int:
        self.store[self.location] = value
        self.location += 1
        return self.location - 1

# interpreter

def interpret(tree: Expr) -> Value:
    runtime = Runtime()

    def var_to_location(var: str, env: list[tuple[str, int]]) -> int:
        for i in range(len(env) - 1, -1, -1):
            if env[i][0] == var:
                return env[i][1]
        sys.exit(f'[Expr Runtime] error: undefined variable "{var}"')

    def evaluate(node: Expr, env: list[tuple[str, int]]) -> Value:
        if type(node) == Int:
            return Integer(node.value)
        elif type(node) == Lambda:
            return Closure(env[:], node)
        elif type(node) == Letrec:
            new_env = env[:]
            for v, e in node.var_expr_list:
                loc = runtime.new(Void())
                new_env.append((v.name, loc))
            for v, e in node.var_expr_list:
                runtime.store[var_to_location(v.name, new_env)] = evaluate(e, new_env[:])
            old_env = runtime.stack[-1].env
            runtime.stack[-1].env = new_env[:]
            value = evaluate(node.expr, new_env[:])
            runtime.stack[-1].env = old_env
            return value
        elif type(node) == If:
            c = evaluate(node.cond, env[:])
            if type(c) != Integer:
                sys.exit('[Expr Runtime] error: "if" condition does not evaluate to an integer')
            if c.value != 0:
                return evaluate(node.branch1, env[:])
            else:
                return evaluate(node.branch2, env[:])
        elif type(node) == Var:
            return runtime.store[var_to_location(node.name, env)]
        elif type(node) == Icall:
            arg_vals = []
            for arg in node.arg_list:
                arg_vals.append(evaluate(arg, env[:]))
            try:
                return runtime.intrinsics[node.intrinsic](*arg_vals)
            except TypeError as e:
                sys.exit(f'[Expr Runtime] error: wrong number/type of arguments given to the intrinsic function "{node.intrinsic}"')
        elif type(node) == Call:
            closure = evaluate(node.callee, env[:])
            new_env = closure.env[:]
            n_args = len(closure.fun.var_list)
            if n_args != len(node.arg_list):
                sys.exit(f'[Expr Runtime] error: wrong number of arguments given to the lambda "{str(closure.fun)}"')
            for i in range(n_args):
                new_env.append((closure.fun.var_list[i].name, runtime.new(evaluate(node.arg_list[i], env[:]))))
            runtime.stack.append(Frame(new_env[:]))
            value = evaluate(closure.fun.expr, new_env[:])
            runtime.stack.pop()
            return value
        elif type(node) == Seq:
            value = None
            for e in node.expr_list:
                value = evaluate(e, env[:])
            return value
        else:
            sys.exit('[Expr Runtime] error: unrecognized AST node')

    return evaluate(tree, [])

# main entry

def main(source) -> None:
    tokens = lex(source)
    tree = parse(tokens)
    print(tree)
    result = interpret(tree)
    if type(result) == Integer:
        print(result.value)
    elif type(result) == Closure:
        print('Closure')
    elif type(result) == Void:
        print('Void')
    else:
        sys.exit('[Expr Main] error: unknown evaluation result')

if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit(f'Usage: python3 {sys.argv[0]} <source-file>')
    with open(sys.argv[1], 'r') as f:
        main(f.read())
