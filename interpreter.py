import sys
from collections import deque

# lexing

def lex(source):
    chars = deque(source)

    def next_token():
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
            return None

    tokens = deque()
    while True:
        token = next_token()
        if token:
            tokens.append(token)
        else:
            break
    return tokens

# parsing

class Int:

    def __init__(self, value):
        self.value = value

class Var:

    def __init__(self, name):
        self.name = name

class Lambda:

    def __init__(self, var_list, expr):
        self.var_list = var_list
        self.expr = expr

class Letrec:

    def __init__(self, var_expr_list, expr):
        self.var_expr_list = var_expr_list
        self.expr = expr

class If:

    def __init__(self, cond, branch1, branch2):
        self.cond = cond
        self.branch1 = branch1
        self.branch2 = branch2

class Call:

    def __init__(self, fun, arg_list):
        self.fun = fun
        self.arg_list = arg_list

class Seq:

    def __init__(self, expr_list):
        self.expr_list = expr_list

def parse(tokens):

    def is_int(s):
        try:
            int(s)
            return True
        except ValueError:
            return False

    def is_var(s):
        return s.isalpha()

    def parse_int():
        value = int(tokens.popleft())
        return Int(value)

    def parse_var():
        name = tokens.popleft()
        return Var(name)

    def parse_lambda():
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

    def parse_letrec():
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

    def parse_if():
        tokens.popleft() # if
        cond = parse_expr()
        tokens.popleft() # then
        branch1 = parse_expr()
        tokens.popleft() # else
        branch2 = parse_expr()
        return If(cond, branch1, branch2)

    def parse_call():
        tokens.popleft() # (
        fun = parse_expr()
        arg_list = []
        while tokens[0] != ')':
            arg_list.append(parse_expr())
        tokens.popleft() # )
        return Call(fun, arg_list)

    def parse_seq():
        tokens.popleft() # [
        expr_list = []
        while tokens[0] != ']':
            expr_list.append(parse_expr())
        tokens.popleft() # ]
        return Seq(expr_list)

    def parse_expr():
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

# interpreting

class Integer:

    def __init__(self, value):
        self.value = value

class Closure:

    def __init__(self, env, fun):
        self.env = env
        self.fun = fun

class Void:

    def __init__(self):
        pass

class Frame:

    def __init__(self):
        self.env = []

    def push(self, var, loc):
        self.env.append((var, loc))

    def pop(self):
        self.env.pop()

def interpret(tree):
    store = {}
    stack = []
    env = []

    def collect():
        visited = set()

        def mark(location):
            visited.add(location)
            if type(store[location]) == Closure:
                for var, loc in store[location].env:
                    if loc not in visited:
                        mark(loc)

        def sweep():
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
        sys.stderr.write('GC: collected {} locations\n'.format(n))

    def recurse(node, env):
        pass

    def install_builtin():
        pass

    install_builtin()
    return recurse(tree, env)

# main entry

def main():
    source = sys.stdin.read()
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
    main()
