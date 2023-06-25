import sys
import re
from collections import deque
from typing import Union, Callable
from copy import deepcopy

### helper functions

def quote(literal: str) -> str:
    ret = '"'
    for char in literal:
        if char == '\\':
            ret += '\\\\'
        elif char == '"':
            ret += '\\"'
        else:
            ret += char
    ret += '"'
    return ret

def gcd(a: int, b: int) -> int:
    if b == 0:
        return a
    return gcd(b, a % b)

### lexer

class SourceLocation:

    def __init__(self, line: int, col: int):
        self.line = line
        self.col = col

    def __str__(self) -> str:
        if self.line <= 0 or self.col <= 0:
            return f'(SourceLocation N/A)'
        return f'(SourceLocation {self.line} {self.col})'

def lexer_error(sl: SourceLocation, msg: str) -> None:
    sys.exit(f'[Lexer Error {sl}] {msg}')

def parser_error(sl: SourceLocation, msg: str) -> None:
    sys.exit(f'[Parser Error {sl}] {msg}')

def runtime_error(sl: SourceLocation, msg: str) -> None:
    sys.exit(f'[Runtime Error {sl}] {msg}')

class Token:

    def __init__(self, sl: SourceLocation, src: str):
        self.sl = sl
        self.src = src

def lex(source: str) -> deque[Token]:
    # only support these characters in source code
    charset = set(
        "abcdefghijklmnopqrstuvwxyz"
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        "0123456789"
        "`~!@#$%^&*()-_=+[{]}\\|;:'\",<.>/?"
        " \t\n"
    )
    line, col = 1, 1
    for char in source:
        if char not in charset:
            lexer_error(SourceLocation(line, col), 'unsupported character')
        if char == '\n':
            line += 1
            col = 1
        else:
            col += 1

    # number format regular expressions
    regex_head_nonzero = re.compile("[1-9][0-9]*")
    regex_tail_nonzero = re.compile("[0-9]*[1-9]")

    def is_number_literal(s: str) -> bool:
        if len(s) and s[0] in ('-', '+'):
            s = s[1:]
        if '/' in s:
            parts = s.split('/')
            if not len(parts) == 2:
                return False
            return (parts[0] == '0' or regex_head_nonzero.fullmatch(parts[0])) and regex_head_nonzero.fullmatch(parts[1])
        elif '.' in s:
            parts = s.split('.')
            if not len(parts) == 2:
                return False
            return (parts[0] == '0' or regex_head_nonzero.fullmatch(parts[0])) and regex_tail_nonzero.fullmatch(parts[1])
        else:
            return s == '0' or regex_head_nonzero.fullmatch(s)

    def count_trailing_escape(s: str) -> int:
        l = len(s)
        cnt = 0
        pos = l - 1
        while pos >= 0:
            if s[pos] == '\\':
                cnt += 1
                pos -= 1
            else:
                break
        return cnt

    # token stream
    chars = deque(source)
    line, col = 1, 1

    def next_token() -> Union[None, Token]:
        nonlocal line, col
        # skip whitespaces
        while chars and chars[0].isspace():
            space = chars.popleft()
            if space == '\n':
                line += 1
                col = 1
            else:
                col += 1
        # read the next token
        if chars:
            sl = SourceLocation(line, col)
            # number literal
            if chars[0].isdigit() or chars[0] in ('-', '+'):
                src = ''
                while chars and (chars[0].isdigit() or (chars[0] in ('-', '+', '.', '/'))):
                    src += chars.popleft()
                    col += 1
                if not is_number_literal(src):
                    lexer_error(sl, 'invalid number literal')
            # variable / keyword
            elif chars[0].isalpha():
                src = ''
                while chars and (chars[0].isalpha() or chars[0].isdigit() or chars[0] == '_'):
                    src += chars.popleft()
                    col += 1
            # intrinsic
            elif chars[0] == '.':
                src = ''
                while chars and (not (chars[0].isspace() or chars[0] == ')')):
                    src += chars.popleft()
                    col += 1
            # special symbol
            elif chars[0] in ('(', ')', '{', '}', '[', ']', '=', '@', '&'):
                src = chars.popleft()
                col += 1
            # string literal
            elif chars[0] == '"':
                src = chars.popleft()
                col += 1
                while chars and (chars[0] != '"' or (chars[0] == '"' and count_trailing_escape(src) % 2 != 0)):
                    # All original characters are kept, including real newlines (not escape sequences like "\n").
                    src += chars.popleft()
                    if src[-1] == '\n':
                        line += 1
                        col = 1
                    else:
                        col += 1
                if chars and chars[0] == '"':
                    src += chars.popleft()
                    col += 1
                else:
                    lexer_error(sl, 'incomplete string literal')
            # comment
            elif chars[0] == '#':
                chars.popleft()
                col += 1
                while chars and chars[0] != '\n':
                    chars.popleft()
                    col += 1
                # next_token() will consume the newline character.
                return next_token()
            else:
                lexer_error(sl, 'unsupported token starting character')
            token = Token(sl, src)
            return token
        else:
            # end of character stream
            return None

    # lexer entry
    tokens = deque()
    while True:
        token = next_token()
        if token:
            tokens.append(token)
        else:
            break
    return tokens

### parser

class ExprNode:
    ''' Normally we don't create instances of this base class. '''
    pass

class NumberNode(ExprNode):

    def __init__(self, sl: SourceLocation, n: int, d: int):
        self.sl = sl
        # simplify it to avoid repeatedly doing this when evaluating the AST node
        g = gcd(abs(n), d)
        self.n = n // g
        self.d = d // g

class StringNode(ExprNode):

    def __init__(self, sl: SourceLocation, value: str):
        self.sl = sl
        self.value = value

class IntrinsicNode(ExprNode):

    def __init__(self, sl: SourceLocation, name: str):
        self.sl = sl
        self.name = name

class VariableNode(ExprNode):

    def __init__(self, sl: SourceLocation, name: str):
        self.sl = sl
        self.name = name

    def is_lex(self) -> bool:
        return self.name[0].islower()

    def is_dyn(self) -> bool:
        return self.name[0].isupper()

class LambdaNode(ExprNode):

    def __init__(self, sl: SourceLocation, var_list: list[VariableNode], expr: ExprNode):
        self.sl = sl
        self.var_list = var_list
        self.expr = expr

class LetrecNode(ExprNode):

    def __init__(self, sl: SourceLocation, var_expr_list: list[tuple[VariableNode, ExprNode]], expr: ExprNode):
        self.sl = sl
        self.var_expr_list = var_expr_list
        self.expr = expr

class IfNode(ExprNode):

    def __init__(self, sl: SourceLocation, cond: ExprNode, branch1: ExprNode, branch2: ExprNode):
        self.sl = sl
        self.cond = cond
        self.branch1 = branch1
        self.branch2 = branch2

class CallNode(ExprNode):

    def __init__(self, sl: SourceLocation, callee: ExprNode, arg_list: list[ExprNode]):
        self.sl = sl
        self.callee = callee
        self.arg_list = arg_list

class SequenceNode(ExprNode):

    def __init__(self, sl: SourceLocation, expr_list: list[ExprNode]):
        self.sl = sl
        self.expr_list = expr_list

class QueryNode(ExprNode):

    def __init__(self, sl: SourceLocation, var: VariableNode, expr_box: list[ExprNode]):
        self.sl = sl
        self.var = var
        self.expr_box = expr_box

class AccessNode(ExprNode):

    def __init__(self, sl: SourceLocation, var: VariableNode, expr: ExprNode):
        self.sl = sl
        self.var = var
        self.expr = expr

def parse(tokens: deque[Token]) -> ExprNode:
    # token checkers

    def is_number_token(token: Token) -> bool:
        return len(token.src) and (token.src[0].isdigit() or token.src[0] in ('-', '+'))

    def is_string_token(token: Token) -> bool:
        return len(token.src) and token.src[0] == '"'

    def is_intrinsic_token(token: Token) -> bool:
        return len(token.src) and token.src[0] == '.'

    def is_variable_token(token: Token) -> bool:
        return len(token.src) and token.src[0].isalpha()

    # token consumer

    def consume(expected: str) -> Token:
        if not tokens:
            parser_error(SourceLocation(-1, -1), 'incomplete token stream')
        token = tokens.popleft()
        if token.src == expected:
            return token
        else:
            parser_error(token.sl, 'unexpected token')

    # parsers

    def parse_number() -> NumberNode:
        if not tokens:
            parser_error(SourceLocation(-1, -1), 'incomplete token stream')
        token = tokens.popleft()
        if not is_number_token(token):
            parser_error(token.sl, 'unexpected token')
        s = token.src
        sign = 1
        if len(s) and s[0] in ('-', '+'):
            if s[0] == '-':
                sign = -1
            s = s[1:]
        if '/' in s:
            parts = s.split('/')
            node = NumberNode(token.sl, sign * int(parts[0]), int(parts[1]))
        elif '.' in s:
            parts = s.split('.')
            depth = len(parts[1])
            node = NumberNode(token.sl, sign * (int(parts[0]) * (10 ** depth) + int(parts[1])), 10 ** depth)
        else:
            node = NumberNode(token.sl, sign * int(s), 1)
        return node

    def parse_string() -> StringNode:
        if not tokens:
            parser_error(SourceLocation(-1, -1), 'incomplete token stream')
        token = tokens.popleft()
        if not is_string_token(token):
            parser_error(token.sl, 'unexpected token')
        content = deque(token.src[1:-1])
        s = ''
        while content:
            char = content.popleft()
            if char == '\\':
                if content:
                    nxt = content.popleft()
                    if nxt == '\\':
                        s += '\\'
                    elif nxt == '"':
                        s += '"'
                    elif nxt == 't':
                        s += '\t'
                    elif nxt == 'n':
                        s += '\n'
                    else:
                        parser_error(token.sl, 'unsupported escape sequence')
                else:
                    parser_error(token.sl, 'incomplete escape sequence')
            else:
                s += char
        node = StringNode(token.sl, s)
        return node

    def parse_intrinsic() -> IntrinsicNode:
        if not tokens:
            parser_error(SourceLocation(-1, -1), 'incomplete token stream')
        token = tokens.popleft()
        if not is_intrinsic_token(token):
            parser_error(token.sl, 'unexpected token')
        node = IntrinsicNode(token.sl, token.src)
        return node

    def parse_lambda() -> LambdaNode:
        start = consume('lambda')
        consume('(')
        var_list = []
        while tokens and is_variable_token(tokens[0]):
            var_list.append(parse_variable())
        consume(')')
        consume('{')
        expr = parse_expr()
        consume('}')
        node = LambdaNode(start.sl, var_list, expr)
        return node

    def parse_letrec() -> LetrecNode:
        start = consume('letrec')
        consume('(')
        var_expr_list = []
        while tokens and is_variable_token(tokens[0]):
            v = parse_variable()
            consume('=')
            e = parse_expr()
            var_expr_list.append((v, e))
        consume(')')
        consume('{')
        expr = parse_expr()
        consume('}')
        node = LetrecNode(start.sl, var_expr_list, expr)
        return node

    def parse_if() -> IfNode:
        start = consume('if')
        cond = parse_expr()
        consume('then')
        branch1 = parse_expr()
        consume('else')
        branch2 = parse_expr()
        node = IfNode(start.sl, cond, branch1, branch2)
        return node

    def parse_variable() -> VariableNode:
        if not tokens:
            parser_error(SourceLocation(-1, -1), 'incomplete token stream')
        token = tokens.popleft()
        if not is_variable_token(token):
            parser_error(token.sl, 'unexpected token')
        node = VariableNode(token.sl, token.src)
        return node

    def parse_call() -> CallNode:
        start = consume('(')
        if tokens and is_intrinsic_token(tokens[0]):
            callee = parse_intrinsic()
        else:
            # if len(tokens) == 0 then delegate parse_expr() to handle the error
            callee = parse_expr()
        arg_list = []
        while tokens and tokens[0].src != ')':
            arg_list.append(parse_expr())
        consume(')')
        node = CallNode(start.sl, callee, arg_list)
        return node

    def parse_sequence() -> SequenceNode:
        start = consume('[')
        expr_list = []
        while tokens and tokens[0].src != ']':
            expr_list.append(parse_expr())
        if len(expr_list) == 0:
            parser_error(start.sl, 'zero-length sequence')
        consume(']')
        node = SequenceNode(start.sl, expr_list)
        return node

    def parse_query() -> QueryNode:
        start = consume('@')
        var = parse_variable()
        if var.is_lex():
            expr = parse_expr()
            node = QueryNode(start.sl, var, [expr])
        else:
            node = QueryNode(start.sl, var, [])
        return node

    def parse_access() -> AccessNode:
        start = consume('&')
        var = parse_variable()
        expr = parse_expr()
        node = AccessNode(start.sl, var, expr)
        return node

    def parse_expr() -> ExprNode:
        if not tokens:
            parser_error(SourceLocation(-1, -1), 'incomplete token stream')
        if is_number_token(tokens[0]):
            return parse_number()
        elif is_string_token(tokens[0]):
            return parse_string()
        elif tokens[0].src == 'lambda':
            return parse_lambda()
        elif tokens[0].src == 'letrec':
            return parse_letrec()
        elif tokens[0].src == 'if':
            return parse_if()
        # check keywords before var to avoid recognizing keywords as vars
        elif is_variable_token(tokens[0]):
            return parse_variable()
        elif tokens[0].src == '(':
            return parse_call()
        elif tokens[0].src == '[':
            return parse_sequence()
        elif tokens[0].src == '@':
            return parse_query()
        elif tokens[0].src == '&':
            return parse_access()
        else:
            parser_error(tokens[0].sl, 'unrecognized token')
    
    # parser entry
    expr = parse_expr()
    if tokens:
        parser_error(tokens[0].sl, 'redundant token(s)')
    return expr

### runtime

class Value:
    ''' Normally we don't create instances of this base class. '''
    pass

class Void(Value):

    def __init__(self):
        # the location of this value (object) in the store (if allocated)
        self.location = None

    def __str__(self) -> str:
        return '<void>'

class Number(Value):

    def __init__(self, n: Union[int, bool], d: int = None):
        self.location = None
        if type(n) == bool:
            if n:
                self.n = 1
            else:
                self.n = 0
            self.d = 1
        else:
            if d is None:
                d = 1
            self.n = n
            self.d = d

    def __str__(self) -> str:
        s = str(self.n)
        if self.d != 1:
            s += '/'
            s += str(self.d)
        return s

    def to_int(self, sl: SourceLocation) -> int:
        if self.d != 1:
            runtime_error(sl, 'cannot convert a non-integer Number to a Python int')
        return self.n

    def add(self, other: 'Number') -> 'Number':
        n1 = self.n * other.d + other.n * self.d
        d1 = self.d * other.d
        g1 = gcd(abs(n1), d1)
        return Number(n1 // g1, d1 // g1)

    def sub(self, other: 'Number') -> 'Number':
        n1 = self.n * other.d - other.n * self.d
        d1 = self.d * other.d
        g1 = gcd(abs(n1), d1)
        return Number(n1 // g1, d1 // g1)

    def mul(self, other: 'Number') -> 'Number':
        n1 = self.n * other.n
        d1 = self.d * other.d
        g1 = gcd(abs(n1), d1)
        return Number(n1 // g1, d1 // g1)

    def div(self, other: 'Number', sl: SourceLocation) -> 'Number':
        if other.n == 0:
            runtime_error(sl, 'division by zero')
        n1 = self.n * other.d
        d1 = self.d * other.n
        if d1 < 0:
            n1 = -n1
            d1 = -d1
        g1 = gcd(abs(n1), d1)
        return Number(n1 // g1, d1 // g1)

    def mod(self, other: 'Number', sl: SourceLocation) -> 'Number':
        if self.d != 1 or other.d != 1:
            runtime_error(sl, 'non-integer mod')
        if self.n < 0 or other.n <= 0:
            runtime_error(sl, 'non-positive integer mod')
        return Number(self.n % other.n, 1)

    def floor(self) -> 'Number':
        return Number(self.n // self.d, 1)

    def ceil(self) -> 'Number':
        rest = 0
        if self.n % self.d != 0:
            rest = 1
        return Number(self.n // self.d + rest, 1)

    def lt(self, other: 'Number') -> bool:
        n_left = self.n * other.d
        n_right = self.d * other.n
        return n_left < n_right

class String(Value):

    def __init__(self, value: str):
        self.location = None
        self.value = value

    def __str__(self) -> str:
        return self.value

class Closure(Value):

    def __init__(self, env: list[tuple[str, int]], fun: LambdaNode):
        self.location = None
        self.env = env
        self.fun = fun

    def __str__(self) -> str:
        return '<closure>'

class Layer:
    '''Each layer on the stack contains the (sub-)expression currently under evaluation.'''

    def __init__(self, env: list[tuple[str, int]], expr: ExprNode, frame: bool = None, tail: bool = None):
        if frame is None:
            frame = False
        if tail is None:
            tail = False
        # environment (shared among layers in each frame) for the evaluation of the current expression
        self.env = env 
        # the current expression under evaluation
        self.expr = expr
        # whether this layer starts a frame (a closure call or the initial layer)
        self.frame = frame
        # whether this layer is in tail position (for tail call optimization)
        self.tail = tail
        # program counter (the pc-th step of evaluating this expression)
        self.pc = 0
        # variables local to this evaluation layer
        self.local = {}

class Continuation(Value):

    def __init__(self, stack: list[Layer]):
        self.location = None
        # we only need to store the stack, because objects in the heap are immutable
        self.stack = stack

    def __str__(self) -> str:
        return '<continuation>'

def check_or_exit(callee: ExprNode, args: list[Value], ts: list[type]) -> bool:
    ''' check whether arguments conform to types '''
    if len(args) != len(ts):
        runtime_error(callee.sl, 'wrong number of arguments given to callee')
    for i in range(len(args)):
        if not isinstance(args[i], ts[i]):
            runtime_error(callee.sl, 'wrong type of arguments given to callee')

def filter_lexical(env: list[tuple[str, int]]) -> list[tuple[str, int]]:
    ''' find out lexical variable-location pairs in an environment '''
    return [t for t in env if len(t[0]) and t[0][0].islower()]

def lookup_env(name: str, env: list[tuple[str, int]]) -> Union[int, None]:
    ''' lexically scoped variable lookup '''
    for i in range(len(env) - 1, -1, -1):
        if env[i][0] == name:
            return env[i][1]
    return None

def lookup_stack(name: str, stack: list[Layer]) -> Union[int, None]:
    ''' dynamically scoped variable lookup '''
    for i in range(len(stack) - 1, -1, -1):
        if stack[i].frame:
            for j in range(len(stack[i].env) - 1, -1, -1):
                if stack[i].env[j][0] == name:
                    return stack[i].env[j][1]
    return None

class State:
    '''The class for the complete execution state'''

    def __init__(self, expr: ExprNode):
        # stack
        ## tail call optimization never removes the main frame
        self.stack = [Layer([], None, frame = True)]
        ## layer.tail == False for the first layer
        self.stack.append(Layer(self.stack[0].env, expr))
        # heap
        self.store = []
        self.end = 0
        # evaluation result
        self.value = None
        # Python FFI
        self.python_functions = {}
        # private values
        self._ref_size = 8 if sys.maxsize > 2 ** 32 else 4
        self._empty_store_size = sys.getsizeof(self.store)

    def register_python_function(self, name: str, f: Callable[..., Union[str, int]]) -> 'State':
        self.python_functions[name] = f
        return self
    
    def call_expr_function(self, name: str, args: list[Union[str, int]]) -> Union[str, int]:
        sl = SourceLocation(-1, -1)
        callee = VariableNode(sl, name)
        arg_list = []
        for a in args:
            if type(a) == str:
                arg_list.append(StringNode(sl, a))
            elif type(a) == int:
                arg_list.append(NumberNode(sl, a, 1))
            else:
                runtime_error(sl, 'Python can only use str/int as arguments when calling ExprScript functions')
        call = CallNode(sl, callee, arg_list)
        self.stack.append(Layer(self.stack[0].env, call))
        self.execute()
        if type(self.value) == String:
            return self.value.value
        elif type(self.value) == Number:
            return self.value.to_int(SourceLocation(-1, -1))
        else:
            runtime_error(sl, 'ExprScript returned a non-String non-Number result')

    def execute(self) -> 'State':
        # insufficient_capacity is the last capacity on which GC failed
        insufficient_capacity = -1

        # we just adjust "state.stack" and "stack.value"
        # the evaluation will automatically continue along the while loop
        while True:

            # GC control
            capacity = self._get_store_capacity()
            # the capacity has been expanded since last GC failure, so we may try GC
            if capacity > insufficient_capacity:
                # try GC
                if self.end >= 0.8 * capacity:
                    self._gc()
                    # GC failed to release enough memory, so the capacity should grow in the next iteration
                    # in the next iteration capacity == insufficient_capacity so GC will not run until the capacity grows
                    if self.end >= 0.8 * capacity:
                        insufficient_capacity = capacity

            # evaluating the current layer
            layer = self.stack[-1]
            if layer.expr is None:
                # found the main frame, which is the end of evaluation
                return self
            elif type(layer.expr) == NumberNode:
                self.value = Number(layer.expr.n, layer.expr.d)
                self.stack.pop()
            elif type(layer.expr) == StringNode:
                self.value = String(layer.expr.value)
                self.stack.pop()
            elif type(layer.expr) == LambdaNode:
                # closures always save all variables (no matter whether they are used in the body or not)
                # so you can use the @ query in an intuitive way
                self.value = Closure(filter_lexical(layer.env), layer.expr)
                self.stack.pop()
            elif type(layer.expr) == LetrecNode:
                # letrec always create new locations
                if layer.pc == 0:
                    for v, _ in layer.expr.var_expr_list:
                        layer.env.append((v.name, self._new(Void())))
                    layer.pc += 1
                # evaluate binding expressions
                elif layer.pc <= len(layer.expr.var_expr_list):
                    # update location content
                    if layer.pc > 1:
                        var = layer.expr.var_expr_list[layer.pc - 2][0]
                        last_location = lookup_env(var.name, layer.env)
                        if last_location is None:
                            runtime_error(var.sl, 'undefined variable')
                        self.store[last_location] = self.value
                    self.stack.append(Layer(layer.env, layer.expr.var_expr_list[layer.pc - 1][1]))
                    layer.pc += 1
                # evaluate body expression
                elif layer.pc == len(layer.expr.var_expr_list) + 1:
                    # update location content
                    if layer.pc > 1:
                        var = layer.expr.var_expr_list[layer.pc - 2][0]
                        last_location = lookup_env(var.name, layer.env)
                        if last_location is None:
                            runtime_error(var.sl, 'undefined variable')
                        self.store[last_location] = self.value
                    self.stack.append(Layer(layer.env, layer.expr.expr, tail = layer.frame or layer.tail))
                    layer.pc += 1
                # finish letrec
                else:
                    # this is necessary because letrec layer's env is shared with its previous frame
                    for i in range(len(layer.expr.var_expr_list)):
                        layer.env.pop()
                    # we cannot pop this layer earlier,
                    # because we need to revert the environment before popping it,
                    # and reverting the environment will make the body expression's evaluation go wrong
                    self.stack.pop()
            elif type(layer.expr) == IfNode:
                # evaluate the condition
                if layer.pc == 0:
                    self.stack.append(Layer(layer.env, layer.expr.cond))
                    layer.pc += 1
                # choose the branch to evaluate
                elif layer.pc == 1:
                    if type(self.value) != Number:
                        runtime_error(layer.expr.cond.sl, 'wrong condition type')
                    if self.value.n != 0:
                        self.stack.append(Layer(layer.env, layer.expr.branch1, tail = layer.frame or layer.tail))
                    else:
                        self.stack.append(Layer(layer.env, layer.expr.branch2, tail = layer.frame or layer.tail))
                    layer.pc += 1
                # finish if
                else:
                    self.stack.pop()
            elif type(layer.expr) == VariableNode:
                # two types of variables
                if layer.expr.is_lex():
                    location = lookup_env(layer.expr.name, layer.env)
                else:
                    location = lookup_stack(layer.expr.name, self.stack)
                if location is None:
                    runtime_error(layer.expr.sl, 'undefined variable')
                self.value = self.store[location]
                self.stack.pop()
            elif type(layer.expr) == CallNode:
                # intrinsic call
                if type(layer.expr.callee) == IntrinsicNode:
                    # initialize args
                    if layer.pc == 0:
                        layer.local['args'] = []
                        layer.pc += 1
                    # evaluate arguments
                    elif layer.pc <= len(layer.expr.arg_list):
                        if layer.pc > 1:
                            layer.local['args'].append(self.value)
                        self.stack.append(Layer(layer.env, layer.expr.arg_list[layer.pc - 1]))
                        layer.pc += 1
                    # intrinsic call doesn't need to grow the stack, so this is the final step for this call
                    else:
                        if layer.pc > 1:
                            layer.local['args'].append(self.value)
                        intrinsic = layer.expr.callee.name
                        args = layer.local['args']
                        # a gigantic series of if conditions, one for each intrinsic function
                        if intrinsic == '.void':
                            check_or_exit(layer.expr.callee, args, [])
                            self.value = Void()
                        elif intrinsic == '.+':
                            check_or_exit(layer.expr.callee, args, [Number] * len(args))
                            self.value = Number(0)
                            for a in args:
                                self.value = self.value.add(a)
                        elif intrinsic == '.-':
                            check_or_exit(layer.expr.callee, args, [Number, Number])
                            self.value = args[0].sub(args[1])
                        elif intrinsic == '.*':
                            check_or_exit(layer.expr.callee, args, [Number] * len(args))
                            self.value = Number(1)
                            for a in args:
                                self.value = self.value.mul(a)
                        elif intrinsic == './':
                            check_or_exit(layer.expr.callee, args, [Number, Number])
                            self.value = args[0].div(args[1], layer.expr.sl)
                        elif intrinsic == '.%':
                            check_or_exit(layer.expr.callee, args, [Number, Number])
                            self.value = args[0].mod(args[1], layer.expr.sl)
                        elif intrinsic == '.floor':
                            check_or_exit(layer.expr.callee, args, [Number])
                            self.value = args[0].floor()
                        elif intrinsic == '.ceil':
                            check_or_exit(layer.expr.callee, args, [Number])
                            self.value = args[0].ceil()
                        elif intrinsic == '.<':
                            check_or_exit(layer.expr.callee, args, [Number, Number])
                            self.value = Number(args[0].lt(args[1]))
                        elif intrinsic == '.<=':
                            check_or_exit(layer.expr.callee, args, [Number, Number])
                            self.value = Number(not args[1].lt(args[0]))
                        elif intrinsic == '.>':
                            check_or_exit(layer.expr.callee, args, [Number, Number])
                            self.value = Number(args[1].lt(args[0]))
                        elif intrinsic == '.>=':
                            check_or_exit(layer.expr.callee, args, [Number, Number])
                            self.value = Number(not args[0].lt(args[1]))
                        elif intrinsic == '.==':
                            check_or_exit(layer.expr.callee, args, [Number, Number])
                            self.value = Number((not args[0].lt(args[1])) and (not args[1].lt(args[0])))
                        elif intrinsic == '.!=':
                            check_or_exit(layer.expr.callee, args, [Number, Number])
                            self.value = Number(args[0].lt(args[1]) or args[1].lt(args[0]))
                        elif intrinsic == '.and':
                            check_or_exit(layer.expr.callee, args, [Number] * len(args))
                            b = True
                            for a in args:
                                b = b and (a.n != 0)
                            self.value = Number(b)
                        elif intrinsic == '.or':
                            check_or_exit(layer.expr.callee, args, [Number] * len(args))
                            b = False
                            for a in args:
                                b = b or (a.n != 0)
                            self.value = Number(b)
                        elif intrinsic == '.not':
                            check_or_exit(layer.expr.callee, args, [Number])
                            self.value = Number(args[0].n == 0)
                        elif intrinsic == '.strlen':
                            check_or_exit(layer.expr.callee, args, [String])
                            self.value = Number(len(args[0].value))
                        elif intrinsic == '.strcut':
                            check_or_exit(layer.expr.callee, args, [String, Number, Number])
                            if args[1].d != 1 or args[2].d != 1:
                                runtime_error(layer.expr.sl, '.strcut is applied to non-integer(s)')
                            self.value = String(args[0].value[args[1].n : args[2].n])
                        elif intrinsic == '.str+':
                            check_or_exit(layer.expr.callee, args, [String] * len(args))
                            s = ""
                            for a in args:
                                s += a.value
                            self.value = String(s)
                        elif intrinsic == '.str<':
                            check_or_exit(layer.expr.callee, args, [String, String])
                            self.value = Number(args[0].value < args[1].value)
                        elif intrinsic == '.str<=':
                            check_or_exit(layer.expr.callee, args, [String, String])
                            self.value = Number(args[0].value <= args[1].value)
                        elif intrinsic == '.str>':
                            check_or_exit(layer.expr.callee, args, [String, String])
                            self.value = Number(args[0].value > args[1].value)
                        elif intrinsic == '.str>=':
                            check_or_exit(layer.expr.callee, args, [String, String])
                            self.value = Number(args[0].value >= args[1].value)
                        elif intrinsic == '.str==':
                            check_or_exit(layer.expr.callee, args, [String, String])
                            self.value = Number(args[0].value == args[1].value)
                        elif intrinsic == '.str!=':
                            check_or_exit(layer.expr.callee, args, [String, String])
                            self.value = Number(args[0].value != args[1].value)
                        elif intrinsic == '.strnum':
                            check_or_exit(layer.expr.callee, args, [String])
                            node = parse(deque([Token(layer.expr.sl, args[0].value)]))
                            if not isinstance(node, NumberNode):
                                runtime_error(layer.expr.sl, '.strnum is applied to non-number-string')
                            self.value = Number(node.n, node.d)
                        elif intrinsic == '.strquote':
                            check_or_exit(layer.expr.callee, args, [String])
                            self.value = String(quote(args[0].value))
                        elif intrinsic == '.getline':
                            check_or_exit(layer.expr.callee, args, [])
                            try:
                                self.value = String(input())
                            except EOFError:
                                self.value = Void()
                        elif intrinsic == '.put':
                            if not (len(args) >= 1 and all(map(lambda v : isinstance(v, Value), args))):
                                runtime_error(layer.expr.callee.sl, 'wrong number/type of arguments given to .put')
                            output = ''
                            for v in args:
                                output += str(v)
                            print(output, end = '', flush = True)
                            # the return value of put is void
                            self.value = Void()
                        elif intrinsic == '.call/cc':
                            check_or_exit(layer.expr.callee, args, [Closure])
                            self.stack.pop()
                            # obtain the continuation (this deepcopy will not copy the store)
                            cont = Continuation(deepcopy(self.stack))
                            closure = args[0]
                            # make a closure call layer and pass in the continuation
                            addr = cont.location if cont.location != None else self._new(cont)
                            self.stack.append(Layer(closure.env[:] + [(closure.fun.var_list[0].name, addr)], closure.fun.expr, frame = True))
                            # we already popped the stack in this case, so just continue the evaluation
                            continue
                        elif intrinsic == '.void?':
                            check_or_exit(layer.expr.callee, args, [Value])
                            self.value = Number(isinstance(args[0], Void))
                        elif intrinsic == '.num?':
                            check_or_exit(layer.expr.callee, args, [Value])
                            self.value = Number(isinstance(args[0], Number))
                        elif intrinsic == '.str?':
                            check_or_exit(layer.expr.callee, args, [Value])
                            self.value = Number(isinstance(args[0], String))
                        elif intrinsic == '.clo?':
                            check_or_exit(layer.expr.callee, args, [Value])
                            self.value = Number(isinstance(args[0], Closure))
                        elif intrinsic == '.cont?':
                            check_or_exit(layer.expr.callee, args, [Value])
                            self.value = Number(isinstance(args[0], Continuation))
                        elif intrinsic == '.eval':
                            check_or_exit(layer.expr.callee, args, [String])
                            arg = args[0]
                            self.value = run_code(arg.value)
                        elif intrinsic == '.exit':
                            check_or_exit(layer.expr.callee, args, [])
                            # the interpreter returns 0
                            sys.exit()
                        elif intrinsic == '.py':
                            if not (len(args) > 0 and type(args[0]) == String):
                                runtime_error(layer.expr.sl, '.py FFI expects a string (Python function name) as the first argument')
                            py_args = []
                            for i in range(1, len(args)):
                                if type(args[i]) == Number:
                                    py_args.append(args[i].to_int(layer.expr.sl))
                                elif type(args[i]) == String:
                                    py_args.append(args[i].value)
                                else:
                                    runtime_error(layer.expr.sl, '.py FFI only supports Number/String arguments')
                            if args[0].value not in self.python_functions:
                                runtime_error(layer.expr.sl, '.py FFI encountered unregistered function')
                            ret = self.python_functions[args[0].value](*py_args)
                            if type(ret) == int:
                                self.value = Number(ret)
                            elif type(ret) == str:
                                self.value = String(ret)
                            else:
                                runtime_error(layer.expr.sl, '.py FFI only supports Number/String return value')
                        elif intrinsic == '.reg':
                            if not (len(args) == 2 and type(args[0]) == String and type(args[1]) == Closure):
                                runtime_error(layer.expr.sl, '.reg can only register a String name for a Closure')
                            self.stack[0].env.insert(0, (args[0].value, args[1].location if args[1].location != None else self._new(args[1])))
                            self.value = Void()
                        else:
                            runtime_error(layer.expr.sl, 'unrecognized intrinsic function call')
                        self.stack.pop()
                # closure or continuation call
                else:
                    # evaluate the callee
                    if layer.pc == 0:
                        self.stack.append(Layer(layer.env, layer.expr.callee))
                        layer.pc += 1
                    # initialize callee and args
                    elif layer.pc == 1:
                        layer.local['callee'] = self.value
                        layer.local['args'] = []
                        layer.pc += 1
                    # evaluate arguments
                    elif layer.pc - 1 <= len(layer.expr.arg_list):
                        if layer.pc - 1 > 1:
                            layer.local['args'].append(self.value)
                        self.stack.append(Layer(layer.env, layer.expr.arg_list[layer.pc - 2]))
                        layer.pc += 1
                    # evaluate the call
                    elif layer.pc - 1 == len(layer.expr.arg_list) + 1:
                        if layer.pc - 1 > 1:
                            layer.local['args'].append(self.value)
                        callee = layer.local['callee']
                        args = layer.local['args']
                        if type(callee) == Closure:
                            closure = callee
                            # types will be checked inside the closure call
                            if len(args) != len(closure.fun.var_list):
                                runtime_error(layer.expr.callee.sl, 'wrong number of arguments given to callee')
                            new_env = closure.env[:]
                            for i, v in enumerate(closure.fun.var_list):
                                addr = args[i].location if args[i].location != None else self._new(args[i])
                                new_env.append((v.name, addr))
                            # tail call optimization
                            if layer.frame or layer.tail:
                                while not self.stack[-1].frame:
                                    self.stack.pop()
                                # pop the last frame
                                self.stack.pop()
                            # evaluate the closure call
                            self.stack.append(Layer(new_env, closure.fun.expr, frame = True))
                            layer.pc += 1
                        elif type(callee) == Continuation:
                            cont = callee
                            if len(args) != 1:
                                runtime_error(layer.expr.callee.sl, 'wrong number of arguments given to callee')
                            # "self.value" already contains the last evaluation result of the args, so we just continue
                            # replace the stack
                            self.stack = deepcopy(cont.stack)
                            # the stack has been replaced, so we don't need to pop the previous stack's call layer
                            # the previous stack is simply discarded
                            continue
                        else:
                            runtime_error(layer.expr.callee.sl, 'calling non-callable object')
                    # finish the (closure) call
                    else:
                        self.stack.pop()
            elif type(layer.expr) == SequenceNode:
                # evaluate the expressions, without the need of storing the results to local
                if layer.pc < len(layer.expr.expr_list) - 1:
                    self.stack.append(Layer(layer.env, layer.expr.expr_list[layer.pc]))
                    layer.pc += 1
                elif layer.pc == len(layer.expr.expr_list) - 1:
                    self.stack.append(Layer(layer.env, layer.expr.expr_list[layer.pc], tail = layer.frame or layer.tail))
                    layer.pc += 1
                # finish the sequence
                else:
                    self.stack.pop()
            elif type(layer.expr) == QueryNode:
                if layer.expr.var.is_lex():
                    # evaluate the closure
                    if layer.pc == 0:
                        self.stack.append(Layer(layer.env, layer.expr.expr_box[0]))
                        layer.pc += 1
                    else:
                        if type(self.value) != Closure:
                            runtime_error(layer.expr.sl, 'lexical variable query applied to non-closure type')
                        # the closure's value is already in "self.value", so we just use it and then update it
                        self.value = Number(not (lookup_env(layer.expr.var.name, self.value.env) is None))
                        self.stack.pop()
                else:
                    self.value = Number(not (lookup_stack(layer.expr.var.name, self.stack) is None))
                    self.stack.pop()
            elif type(layer.expr) == AccessNode:
                # evaluate the closure
                if layer.pc == 0:
                    self.stack.append(Layer(layer.env, layer.expr.expr))
                    layer.pc += 1
                else:
                    if type(self.value) != Closure:
                        runtime_error(layer.expr.sl, 'lexical variable access applied to non-closure type')
                    # again, "self.value" already contains the closure's evaluation result
                    location = lookup_env(layer.expr.var.name, self.value.env)
                    if location is None:
                        runtime_error(layer.expr.sl, 'undefined variable')
                    self.value = self.store[location]
                    self.stack.pop()
            else:
                runtime_error(layer.expr.sl, 'unrecognized AST node')

    def _get_store_capacity(self) -> int:
        # capacity >= length
        return (sys.getsizeof(self.store) - self._empty_store_size) // self._ref_size

    def _new(self, value: Value) -> int:
        ''' heap space allocation '''
        if self.end < len(self.store):
            self.store[self.end] = value
            value.location = self.end
        else:
            # the self.store array is managed by Python and will automatically grow
            self.store.append(value)
            value.location = self.end
        self.end += 1
        return self.end - 1

    def _mark(self) -> tuple[set[int], list[Value]]:
        # ids
        visited_closures = set()
        # ids
        visited_stacks = set()
        # integer locations
        visited_locations = set()

        def mark_closure(closure: Closure) -> None:
            if id(closure) not in visited_closures:
                visited_closures.add(id(closure))
                for v, l in closure.env:
                    mark_location(l)
        
        def mark_stack(stack: list[Layer]) -> None:
            if id(stack) not in visited_stacks:
                visited_stacks.add(id(stack))
                for layer in stack:
                    if layer.frame:
                        for v, l in layer.env:
                            mark_location(l)
                    if layer.local:
                        for name, value in layer.local.items():
                            if type(value) == Closure:
                                mark_closure(value)
                            elif type(value) == Continuation:
                                mark_stack(value.stack)
                            elif type(value) == list:
                                for elem in value:
                                    if type(elem) == Closure:
                                        mark_closure(elem)
                                    elif type(elem) == Continuation:
                                        mark_stack(elem.stack)

        def mark_location(location: int) -> None:
            if location not in visited_locations:
                visited_locations.add(location)
                val = self.store[location]
                if type(val) == Closure:
                    mark_closure(val)
                elif type(val) == Continuation:
                    mark_stack(val.stack)
        
        # mark both the value and the stack
        if type(self.value) == Closure:
            mark_closure(self.value)
        elif type(self.value) == Continuation:
            mark_stack(self.value.stack)
        mark_stack(self.stack)
        return visited_locations

    def _sweep_and_compact(self, visited_locations: set[int]) -> tuple[int, dict[int, int]]:
        removed = 0
        # old location -> new location
        relocation = {}
        i = 0
        j = 0
        while j < self.end:
            if j in visited_locations:
                self.store[i] = self.store[j]
                self.store[i].location = i
                relocation[j] = i
                i += 1
            else:
                removed += 1
            j += 1
        # adjust the next available location
        self.end = i
        return (removed, relocation)
    
    def _relocate(self, relocation: dict[int, int]) -> None:
        relocated = set()

        def reloc(val: Value) -> None:
            if id(val) not in relocated:
                relocated.add(id(val))
                if type(val) == Closure:
                    for i in range(len(val.env)):
                        val.env[i] = (val.env[i][0], relocation[val.env[i][1]])
                elif type(val) == Continuation:
                    for layer in val.stack:
                        if layer.frame:
                            for i in range(len(layer.env)):
                                layer.env[i] = (layer.env[i][0], relocation[layer.env[i][1]])
                        if layer.local:
                            for name, value in layer.local.items():
                                if type(value) == Closure:
                                    reloc(value)
                                elif type(value) == Continuation:
                                    reloc(value)
                                elif type(value) == list:
                                    for elem in value:
                                        if type(elem) == Closure:
                                            reloc(elem)
                                        elif type(elem) == Continuation:
                                            reloc(elem)

        reloc(self.value)
        reloc(Continuation(self.stack))
        for i in range(self.end):
            reloc(self.store[i])

    def _gc(self) -> int:
        ''' mark-and-sweep garbage collection '''
        visited_locations = self._mark()
        removed, relocation = self._sweep_and_compact(visited_locations)
        self._relocate(relocation)
        return removed
        
### main

def run_code(source: str) -> Value:
    tokens = lex(source)
    tree = parse(tokens)
    state = State(tree)
    return state.execute().value

if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit(f'Usage:\n\tpython3 {sys.argv[0]} <source-file>')
    with open(sys.argv[1], 'r', encoding = 'utf-8') as f:
        print(run_code(f.read()))
    if sys.platform.startswith('linux') or sys.platform.startswith('darwin'):
        import resource
        ru = resource.getrusage(resource.RUSAGE_SELF)
        sys.stderr.write(
            f'User time (seconds) = {round(ru.ru_utime, 3)}\n'
            f'System time (seconds) = {round(ru.ru_stime, 3)}\n'
            f'Peak memory (MiB) = {round(ru.ru_maxrss / 1048576, 3)}\n'
        )
