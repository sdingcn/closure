import sys
from collections import deque
from typing import Union, Any
from copy import deepcopy

### helper functions

def unfold(value: Union[list[Any], tuple[Any, ...], set[Any], dict[Any, Any]]) -> str:
    if type(value) == list:
        s = '['
    elif type(value) == tuple:
        s = '('
    elif type(value) in [set, dict]:
        s = '{'
    else:
        sys.exit('[Expr Internal Error] unsupported argument given to unfold')
    if type(value) in [list, tuple, set]:
        for v in value:
            if type(v) in [list, tuple, set, dict]:
                s += unfold(v)
            else:
                s += str(v)
            s += ', '
        if s[-2:] == ', ':
            s = s[:-2]
    else:
        for k, v in value.items():
            if type(k) == tuple:
                s += unfold(k)
            else:
                s += str(k)
            s += ': '
            if type(v) in [list, tuple, set, dict]:
                s += unfold(v)
            else:
                s += str(v)
            s += ', '
        if s[-2:] == ', ':
            s = s[:-2]
    if type(value) == list:
        s += ']'
    elif type(value) == tuple:
        s += ')'
    else:
        s = '}'
    return s

### lexer

class SourceLocation:

    def __init__(self, line: int, col: int):
        self.line = line
        self.col = col

    def __str__(self) -> str:
        return f'(SourceLocation {self.line} {self.col})'

class Token:

    def __init__(self, sl: SourceLocation, val: str):
        self.sl = sl
        self.val = val

    def __str__(self) -> str:
        return f'(Token {self.sl} {self.val})'

def lex(source: str, debug: bool) -> deque[Token]:
    chars = deque(source)
    line = 1
    col = 1

    def next_token() -> Union[None, Token]:
        nonlocal line, col
        while chars and chars[0].isspace():
            space = chars.popleft()
            col += 1
            if space == '\n':
                line += 1
                col = 1
        if chars:
            sl = SourceLocation(line, col)
            if chars[0].isdigit():
                val = ''
                while chars and chars[0].isdigit():
                    val += chars.popleft()
            elif chars[0] in ('-', '+') and (len(chars) > 1 and chars[1].isdigit()):
                val = chars.popleft()
                while chars and chars[0].isdigit():
                    val += chars.popleft()
            elif chars[0].isalpha():
                val = ''
                while chars and chars[0].isalpha():
                    val += chars.popleft()
            elif chars[0] in ('(', ')', '{', '}', '[', ']', '='):
                val = chars.popleft()
            else:
                sys.exit(f'[Expr Lexer Error] unsupported or incomplete character sequence starting with {chars[0]} at {sl}')
            token = Token(sl, val)
            col += len(val)
            return token
        else:
            return None

    tokens = deque()
    while True:
        token = next_token()
        if token:
            if debug:
                sys.stderr.write(f'[Expr Debug] read token {token}\n')
            tokens.append(token)
        else:
            break
    return tokens

### parser

class Expr:

    def __init__(self):
        pass

    def __str__(self) -> str:
        return 'Expr'

class Int(Expr):

    def __init__(self, sl: SourceLocation, parent: Union[None, Expr], value: int):
        self.sl = sl
        self.parent = parent
        self.value = value

    def __str__(self) -> str:
        return f'(Int {self.sl} {self.value})'

class Var(Expr):

    def __init__(self, sl: SourceLocation, parent: Union[None, Expr], name: str):
        self.sl = sl
        self.parent = parent
        self.name = name

    def __str__(self) -> str:
        return f'(Var {self.sl} {self.name})'

class Lambda(Expr):

    def __init__(self, sl: SourceLocation, parent: Union[None, Expr], var_list: list[Var], expr: Expr):
        self.sl = sl
        self.parent = parent
        self.var_list = var_list
        self.expr = expr

    def __str__(self) -> str:
        return f'(Lambda {self.sl} {unfold(self.var_list)} {self.expr})'

class Letrec(Expr):

    def __init__(self, sl: SourceLocation, parent: Union[None, Expr], var_expr_list: list[tuple[Var, Expr]], expr: Expr):
        self.sl = sl
        self.parent = parent
        self.var_expr_list = var_expr_list
        self.expr = expr

    def __str__(self) -> str:
        return f'(Letrec {self.sl} {unfold(self.var_expr_list)} {self.expr})'

class If(Expr):

    def __init__(self, sl: SourceLocation, parent: Union[None, Expr], cond: Expr, branch1: Expr, branch2: Expr):
        self.sl = sl
        self.parent = parent
        self.cond = cond
        self.branch1 = branch1
        self.branch2 = branch2

    def __str__(self) -> str:
        return f'(If {self.sl} {self.cond} {self.branch1} {self.branch2})'

class Call(Expr):

    def __init__(self, sl: SourceLocation, parent: Union[None, Expr], callee: Expr, arg_list: list[Expr]):
        self.sl = sl
        self.parent = parent
        self.callee = callee
        self.arg_list = arg_list

    def __str__(self) -> str:
        return f'(Call {self.sl} {self.callee} {unfold(self.arg_list)})'

class Seq(Expr):

    def __init__(self, sl: SourceLocation, parent: Union[None, Expr], expr_list: list[Expr]):
        self.sl = sl
        self.parent = parent
        self.expr_list = expr_list

    def __str__(self) -> str:
        return f'(Seq {self.sl} {unfold(self.expr_list)})'

def parse(tokens: deque[Token], debug: bool) -> Expr:
    
    def is_int(token: Token) -> bool:
        try:
            int(token.val)
            return True
        except ValueError:
            return False

    def is_var(token: Token) -> bool:
        return token.val.isalpha()

    def consume(expected: str) -> Token:
        if not tokens:
            sys.exit(f'[Expr Parser Error] incomplete token stream')
        token = tokens.popleft()
        if token.val == expected:
            return token
        else:
            sys.exit(f'[Expr Parser Error] expected {expected}, got {token}')

    def parse_int() -> Int:
        if not tokens:
            sys.exit(f'[Expr Parser Error] incomplete token stream')
        token = tokens.popleft()
        if not is_int(token):
            sys.exit(f'[Expr Parser Error] expected an integer, got {token}')
        node = Int(token.sl, None, int(token.val))
        return node

    def parse_lambda() -> Lambda:
        start = consume('lambda')
        consume('(')
        if not tokens:
            sys.exit(f'[Expr Parser Error] incomplete token stream')
        var_list = []
        while tokens and is_var(tokens[0]):
            var_list.append(parse_var())
        consume(')')
        consume('{')
        expr = parse_expr()
        consume('}')
        node = Lambda(start.sl, None, var_list, expr)
        for v in node.var_list:
            v.parent = node
        node.expr.parent = node
        return node

    def parse_letrec() -> Letrec:
        start = consume('letrec')
        consume('(')
        if not tokens:
            sys.exit(f'[Expr Parser Error] incomplete token stream')
        var_expr_list = []
        while tokens and is_var(tokens[0]):
            v = parse_var()
            consume('=')
            e = parse_expr()
            var_expr_list.append((v, e))
        consume(')')
        consume('{')
        expr = parse_expr()
        consume('}')
        node = Letrec(start.sl, None, var_expr_list, expr)
        for v, e in node.var_expr_list:
            v.parent = node
            e.parent = node
        node.expr.parent = node
        return node

    def parse_if() -> If:
        start = consume('if')
        cond = parse_expr()
        consume('then')
        branch1 = parse_expr()
        consume('else')
        branch2 = parse_expr()
        node = If(start.sl, None, cond, branch1, branch2)
        node.cond.parent = node
        node.branch1.parent = node
        node.branch2.parent = node
        return node

    def parse_var() -> Var:
        if not tokens:
            sys.exit(f'[Expr Parser Error] incomplete token stream')
        token = tokens.popleft()
        if not is_var(token):
            sys.exit(f'[Expr Parser Error] expected a variable, got {token}')
        node = Var(token.sl, None, token.val)
        return node

    def parse_call() -> Call:
        start = consume('(')
        callee = parse_expr()
        if not tokens:
            sys.exit(f'[Expr Parser Error] incomplete token stream')
        arg_list = []
        while tokens and tokens[0].val != ')':
            arg_list.append(parse_expr())
        consume(')')
        node = Call(start.sl, None, callee, arg_list)
        node.callee.parent = node
        for a in node.arg_list:
            a.parent = node
        return node

    def parse_seq() -> Seq:
        start = consume('[')
        if not tokens:
            sys.exit(f'[Expr Parser Error] incomplete token stream')
        expr_list = []
        while tokens and tokens[0].val != ']':
            expr_list.append(parse_expr())
        if len(expr_list) == 0:
            sys.exit('[Expr Parser Error] zero-length sequence at {start}')
        consume(']')
        node = Seq(start.sl, None, expr_list)
        for e in node.expr_list:
            e.parent = node
        return node

    def parse_expr() -> Expr:
        if not tokens:
            sys.exit(f'[Expr Parser Error] incomplete token stream')
        if debug:
            sys.stderr.write(f'[Expr Debug] parsing expression starting with {tokens[0]}\n')
        if is_int(tokens[0]):
            return parse_int()
        elif tokens[0].val == 'lambda':
            return parse_lambda()
        elif tokens[0].val == 'letrec':
            return parse_letrec()
        elif tokens[0].val == 'if':
            return parse_if()
        elif is_var(tokens[0]):
            return parse_var()
        elif tokens[0].val == '(':
            return parse_call()
        elif tokens[0].val == '[':
            return parse_seq()
        else:
            sys.exit(f'[Expr Parser Error] unrecognized expression starting with {tokens[0]}')
    
    return parse_expr()

### runtime

class Value:
    
    def __init__(self):
        pass

    def __str__(self) -> str:
        return 'value'

class Void(Value):

    def __init__(self):
        pass

    def __str__(self) -> str:
        return 'void'

class Integer(Value):

    def __init__(self, value: int):
        self.value = value

    def __str__(self) -> str:
        return str(self.value)

class Closure(Value):

    def __init__(self, env: list[tuple[str, int]], fun: Lambda):
        self.env = env
        self.fun = fun

    def __str__(self) -> str:
        return f'(closure {unfold(self.env)} {self.fun})'

# the layer class for the evaluation stack; each layer contains the expression currently under evaluation
class Layer:

    def __init__(self,
            env: list[tuple[str, int]],
            expr: Expr,
            pc: int,
            local: dict[str, Any]
        ):
        self.env = env
        self.expr = expr
        self.pc = pc # program counter (the i-th step of evaluating this layer)
        self.local = local

    def __str__(self) -> str:
        return f'(layer {unfold(self.env)} {self.expr} {self.pc} {unfold(self.local)})'

class Continuation(Value):

    def __init__(self, stack: list[Layer]):
        self.stack = stack

    def __str__(self) -> str:
        return f'(continuation {unfold(self.stack)})'

# the global state
class State:

    def __init__(self, expr: Expr):
        self.stack = [Layer([], expr, 0, {})]
        self.store = {}
        self.location = 0

    def __str__(self) -> str:
        return f'(state {unfold(self.stack)} {unfold(self.store)} {self.location})'

    def new(self, value: Value) -> int:
        self.store[self.location] = value
        self.location += 1
        return self.location - 1

    def collect(self) -> int: # TODO
        visited = set()

        def mark(loc: int) -> None:
            visited.add(loc)
            if type(self.store[loc]) == Closure:
                for v, l in self.store[loc].env:
                    if l not in visited:
                        mark(l)

        def sweep() -> int:
            to_remove = set()
            for k, v in self.store.items():
                if k not in visited:
                    to_remove.add(k)
            for k in to_remove:
                del self.store[k]
            return len(to_remove)

        for layer in self.stack:
            for v, l in layer.env:
                mark(l)
        return sweep()

def lexical_lookup(var: str, env: list[tuple[str, int]]) -> int:
    for i in range(len(env) - 1, -1, -1):
        if env[i][0] == var:
            return env[i][1]
    sys.exit(f'[Expr Runtime Error] undefined variable {var}')

def dynamic_lookup(var: str, stack: list[Layer]) -> int: # TODO
    pass

### interpreter

def interpret(tree: Expr, debug: bool) -> Value:
    intrinsics = ['void', 'add', 'sub', 'mul', 'div', 'mod', 'lt', 'get', 'put', 'callcc', 'type', 'exit']
    state = State(tree)
    value = None

    while True:
        # TODO: maybe call GC once for every 100 iterations
        if len(state.stack) == 0:
            return value
        layer = state.stack[-1]
        node = layer.expr
        if debug:
            sys.stderr.write(f'[Expr Debug] evaluating AST node of type {type(node)} at {node.sl}\n')
        if type(node) == Int:
            value = Integer(node.value)
            state.stack.pop()
        elif type(node) == Lambda:
            value = Closure(layer.env, node)
            state.stack.pop()
        elif type(node) == Letrec:
            if layer.pc == 0:
                layer.local['new_env'] = layer.env[:]
                for v, e in node.var_expr_list:
                    loc = state.new(Void())
                    layer.local['new_env'].append((v.name, loc))
                layer.pc += 1
            elif layer.pc <= len(node.var_expr_list):
                if layer.pc > 1:
                    last_location = lexical_lookup(node.var_expr_list[layer.pc - 2][0].name, layer.local['new_env'])
                    state.store[last_location] = value
                v, e = node.var_expr_list[layer.pc - 1]
                state.stack.append(Layer(layer.local['new_env'][:], e, 0, {}))
                layer.pc += 1
            elif layer.pc == len(node.var_expr_list) + 1:
                if layer.pc > 1:
                    last_location = lexical_lookup(node.var_expr_list[layer.pc - 2][0].name, layer.local['new_env'])
                    state.store[last_location] = value
                state.stack.append(Layer(layer.local['new_env'][:], node.expr, 0, {}))
                layer.pc += 1
            else:
                state.stack.pop()
        elif type(node) == If:
            if layer.pc == 0:
                state.stack.append(Layer(layer.env[:], node.cond, 0, {}))
                layer.pc += 1
            elif layer.pc == 1:
                if value.value != 0:
                    state.stack.append(Layer(layer.env[:], node.branch1, 0, {}))
                else:
                    state.stack.append(Layer(layer.env[:], node.branch2, 0, {}))
                layer.pc += 1
            else:
                state.stack.pop()
        elif type(node) == Var:
            value = state.store[lexical_lookup(node.name, layer.env)]
            state.stack.pop()
        elif type(node) == Call:
            if type(node.callee) == Var and node.callee.name in intrinsics:
                if layer.pc == 0:
                    layer.local['arg_vals'] = []
                    layer.pc += 1
                elif layer.pc <= len(node.arg_list):
                    if layer.pc > 1:
                        layer.local['arg_vals'].append(value)
                    state.stack.append(Layer(layer.env[:], node.arg_list[layer.pc - 1], 0, {}))
                    layer.pc += 1
                else:
                    if layer.pc > 1:
                        layer.local['arg_vals'].append(value)
                    if node.callee.name == 'void':
                        value = Void()
                    elif node.callee.name == 'add':
                        value = Integer(layer.local['arg_vals'][0].value + layer.local['arg_vals'][1].value)
                    elif node.callee.name == 'sub':
                        value = Integer(layer.local['arg_vals'][0].value - layer.local['arg_vals'][1].value)
                    elif node.callee.name == 'mul':
                        value = Integer(layer.local['arg_vals'][0].value * layer.local['arg_vals'][1].value)
                    elif node.callee.name == 'div':
                        value = Integer(layer.local['arg_vals'][0].value / layer.local['arg_vals'][1].value)
                    elif node.callee.name == 'mod':
                        value = Integer(layer.local['arg_vals'][0].value % layer.local['arg_vals'][1].value)
                    elif node.callee.name == 'lt':
                        value = Integer(1) if layer.local['arg_vals'][0].value < layer.local['arg_vals'][1].value else Integer(0)
                    elif node.callee.name == 'get':
                        try:
                            s = input()
                            value = Integer(int(s.strip()))
                        except ValueError:
                            sys.exit(f'[Expr Runtime Error] unsupported input {s}')
                    elif node.callee.name == 'put':
                        print(layer.local['arg_vals'][0].value)
                        value = Void()
                    elif node.callee.name == 'callcc': # this is like calling a function
                        state.stack.pop()
                        cont = Continuation(deepcopy(state.stack))
                        if debug:
                            sys.stderr.write(f'[Expr Debug] captured continuation {cont}\n')
                        state.stack.append(Layer(layer.local['arg_vals'][0].env[:]
                            + [(layer.local['arg_vals'][0].fun.var_list[0].name, state.new(cont))],
                            layer.local['arg_vals'][0].fun.expr, 0, {}))
                        continue
                    elif node.callee.name == 'type':
                        if type(layer.local['arg_vals'][0]) == Void:
                            value = Integer(0)
                        elif type(layer.local['arg_vals'][0]) == Integer:
                            value = Integer(1)
                        elif type(layer.local['arg_vals'][0]) == Closure:
                            value = Integer(2)
                        elif type(layer.local['arg_vals'][0]) == Continuation:
                            value = Integer(3)
                        else:
                            sys.exit(f'[Expr Runtime Error] the "type" intrinsic function found a value of unknown type')
                    elif node.callee.name == 'exit':
                        if debug:
                            sys.stderr.write('[Expr Debug] execution stopped by the "exit" intrinsic function\n')
                    state.stack.pop()
            else:
                if layer.pc == 0:
                    state.stack.append(Layer(layer.env[:], node.callee, 0, {}))
                    layer.pc += 1
                elif layer.pc == 1:
                    layer.local['callee'] = value
                    layer.local['arg_vals'] = []
                    layer.pc += 1
                elif layer.pc - 1 <= len(node.arg_list):
                    if layer.pc - 1 > 1:
                        layer.local['arg_vals'].append(value)
                    state.stack.append(Layer(layer.env[:], node.arg_list[layer.pc - 2], 0, {}))
                    layer.pc += 1
                elif layer.pc - 1 == len(node.arg_list) + 1:
                    if layer.pc - 1 > 1:
                        layer.local['arg_vals'].append(value)
                    if type(layer.local['callee']) == Closure:
                        layer.local['new_env'] = layer.local['callee'].env[:]
                        for i, v in enumerate(layer.local['callee'].fun.var_list):
                            layer.local['new_env'].append((v.name, state.new(layer.local['arg_vals'][i])))
                        state.stack.append(Layer(layer.local['new_env'][:], layer.local['callee'].fun.expr, 0, {}))
                        layer.pc += 1
                    elif type(layer.local['callee']) == Continuation:
                        cont = layer.local['callee']
                        state.stack = deepcopy(cont.stack)
                        if debug:
                            sys.stderr.write(f'[Expr Debug] applied continuation {cont}, stack switched\n')
                        continue
                else:
                    state.stack.pop()
        elif type(node) == Seq:
            if layer.pc < len(node.expr_list):
                state.stack.append(Layer(layer.env[:], node.expr_list[layer.pc], 0, {}))
                layer.pc += 1
            else:
                state.stack.pop()
        else:
            sys.exit(f'[Expr Runtime Error] unrecognized AST node {node}')

### main

def main(option: str, source: str) -> None:
    if option == 'run':
        tokens = lex(source, False)
        tree = parse(tokens, False)
        result = interpret(tree, False)
        print(result)
    elif option == 'debug':
        sys.stderr.write('[Expr Debug] *** starting lexer ***\n')
        tokens = lex(source, True)
        sys.stderr.write('[Expr Debug] *** starting parser ***\n')
        tree = parse(tokens, True)
        sys.stderr.write('[Expr Debug] *** starting interpreter ***\n')
        result = interpret(tree, True)
        print(result)
    elif option == 'dump-ast':
        tokens = lex(source, False)
        tree = parse(tokens, False)
        print(tree)

if __name__ == '__main__':
    if len(sys.argv) != 3 or sys.argv[1] not in ['run', 'debug', 'dump-ast']:
        sys.exit(
            'Usage:\n'
            f'\tpython3 {sys.argv[0]} run <source-file>\n'
            f'\tpython3 {sys.argv[0]} debug <source-file>\n'
            f'\tpython3 {sys.argv[0]} dump-ast <source-file>'
        )
    with open(sys.argv[2], 'r') as f:
        main(sys.argv[1], f.read())
