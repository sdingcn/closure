import sys
import re
from collections import deque
from typing import Union, Callable
from copy import deepcopy
from functools import reduce

### helper functions and classes

def gcd(a: int, b: int) -> int:
    return a if b == 0 else gcd(b, a % b)

class SourceLocation:

    def __init__(self, line: int = 1, col: int = 1):
        self.line = line
        self.col = col

    def __str__(self) -> str:
        if self.line <= 0 or self.col <= 0:
            return f'(SourceLocation N/A)'
        return f'(SourceLocation {self.line} {self.col})'

    def revert(self) -> None:
        self.line = 1
        self.col = 1

    def update(self, char: str) -> None:
        if char == '\n':
            self.line += 1
            self.col = 1
        else:
            self.col += 1

def lexer_error(sl: SourceLocation, msg: str) -> None:
    sys.exit(f'[Lexer Error {sl}] {msg}')

def parser_error(sl: SourceLocation, msg: str) -> None:
    sys.exit(f'[Parser Error {sl}] {msg}')

def runtime_error(sl: SourceLocation, msg: str) -> None:
    sys.exit(f'[Runtime Error {sl}] {msg}')

### lexer

class Token:

    def __init__(self, sl: SourceLocation, src: str):
        self.sl = sl
        self.src = src

def lex(source: str) -> deque[Token]:
    charset = set(
        "abcdefghijklmnopqrstuvwxyz"
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        "0123456789"
        "`~!@#$%^&*()-_=+[{]}\\|;:'\",<.>/?"
        " \t\n"
    )
    number_regex = re.compile(
        r'''
        [+-]?
        (
            (0|[1-9][0-9]*) |
            ((0|[1-9][0-9]*)\.([0-9]*[1-9])) | 
            ((0|[1-9][0-9]*)/([1-9][0-9]*))
        )
        '''.replace(' ', '').replace('\n', '')
    )
    sl = SourceLocation()
    for char in source:
        if char not in charset:
            lexer_error(sl, 'unsupported character')
        sl.update(char)
    sl.revert()
    chars = deque(source)

    def count_trailing_escape(s: str) -> int:
        cnt = 0
        pos = len(s) - 1
        while pos >= 0:
            if s[pos] == '\\':
                cnt += 1
                pos -= 1
            else:
                break
        return cnt

    def next_token() -> Union[None, Token]:
        # skip whitespaces
        while chars and chars[0].isspace():
            sl.update(chars.popleft())
        # read the next token
        if chars:
            sl_copy = deepcopy(sl)
            src = ''
            # number literal
            if chars[0].isdigit() or chars[0] in ('-', '+'):
                while chars and (chars[0].isdigit() or (chars[0] in ('-', '+', '.', '/'))):
                    src += chars.popleft()
                    sl.update(src[-1])
                if not number_regex.fullmatch(src):
                    lexer_error(sl, 'invalid number literal')
            # variable / keyword
            elif chars[0].isalpha():
                while chars and (chars[0].isalpha() or chars[0].isdigit() or chars[0] == '_'):
                    src += chars.popleft()
                    sl.update(src[-1])
            # intrinsic
            elif chars[0] == '.':
                while chars and (not (chars[0].isspace() or chars[0] == ')')):
                    src += chars.popleft()
                    sl.update(src[-1])
            # special symbol
            elif chars[0] in '(){}[]=@&':
                src += chars.popleft()
                sl.update(src[-1])
            # string literal
            elif chars[0] == '"':
                src += chars.popleft()
                sl.update(src[-1])
                while chars and (chars[0] != '"' or (chars[0] == '"' and count_trailing_escape(src) % 2 != 0)):
                    # All original characters are kept, including real newlines (not escape sequences like "\n").
                    src += chars.popleft()
                    sl.update(src[-1])
                if chars and chars[0] == '"':
                    src += chars.popleft()
                    sl.update(src[-1])
                else:
                    lexer_error(sl, 'incomplete string literal')
            # comment
            elif chars[0] == '#':
                sl.update(chars.popleft())
                while chars and chars[0] != '\n':
                    sl.update(chars.popleft())
                # next_token() will consume the newline character.
                return next_token()
            else:
                lexer_error(sl, 'unsupported token starting character')
            return Token(sl_copy, src)
        # end of character stream
        else:
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
    is_number_token = lambda token: len(token.src) and (token.src[0].isdigit() or token.src[0] in ('-', '+'))
    is_string_token = lambda token: len(token.src) and token.src[0] == '"'
    is_intrinsic_token = lambda token: len(token.src) and token.src[0] == '.'
    is_variable_token = lambda token: len(token.src) and token.src[0].isalpha()

    def consume(predicate: Callable) -> Token:
        if not tokens:
            parser_error(SourceLocation(-1, -1), 'incomplete token stream')
        token = tokens.popleft()
        if not predicate(token):
            parser_error(token.sl, 'unexpected token')
        return token

    def parse_number() -> NumberNode:
        token = consume(is_number_token)
        s = token.src
        sign = 1
        if len(s) and s[0] in ('-', '+'):
            if s[0] == '-':
                sign = -1
            s = s[1:]
        if '/' in s:
            n, d = s.split('/')
            return NumberNode(token.sl, sign * int(n), int(d))
        elif '.' in s:
            n, d = s.split('.')
            return NumberNode(token.sl, sign * (int(n) * (10 ** len(d)) + int(d)), 10 ** len(d))
        else:
            return NumberNode(token.sl, sign * int(s), 1)

    def parse_string() -> StringNode:
        token = consume(is_string_token)
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
        return StringNode(token.sl, s)

    def parse_intrinsic() -> IntrinsicNode:
        token = consume(is_intrinsic_token)
        return IntrinsicNode(token.sl, token.src)

    def parse_lambda() -> LambdaNode:
        start = consume(lambda t: t.src == 'lambda')
        consume(lambda t: t.src == '(')
        var_list = []
        while tokens and is_variable_token(tokens[0]):
            var_list.append(parse_variable())
        consume(lambda t: t.src == ')')
        consume(lambda t: t.src == '{')
        expr = parse_expr()
        consume(lambda t: t.src == '}')
        return LambdaNode(start.sl, var_list, expr)

    def parse_letrec() -> LetrecNode:
        start = consume(lambda t: t.src == 'letrec')
        consume(lambda t: t.src == '(')
        var_expr_list = []
        while tokens and is_variable_token(tokens[0]):
            v = parse_variable()
            consume(lambda t: t.src == '=')
            e = parse_expr()
            var_expr_list.append((v, e))
        consume(lambda t: t.src == ')')
        consume(lambda t: t.src == '{')
        expr = parse_expr()
        consume(lambda t: t.src == '}')
        return LetrecNode(start.sl, var_expr_list, expr)

    def parse_if() -> IfNode:
        start = consume(lambda t: t.src == 'if')
        cond = parse_expr()
        consume(lambda t: t.src == 'then')
        branch1 = parse_expr()
        consume(lambda t: t.src == 'else')
        branch2 = parse_expr()
        return IfNode(start.sl, cond, branch1, branch2)

    def parse_variable() -> VariableNode:
        token = consume(is_variable_token)
        return VariableNode(token.sl, token.src)

    def parse_call() -> CallNode:
        start = consume(lambda t: t.src == '(')
        if not tokens:
            parser_error(start.sl, 'incomplete token stream')
        if is_intrinsic_token(tokens[0]):
            callee = parse_intrinsic()
        else:
            callee = parse_expr()
        arg_list = []
        while tokens and tokens[0].src != ')':
            arg_list.append(parse_expr())
        consume(lambda t: t.src == ')')
        return CallNode(start.sl, callee, arg_list)

    def parse_sequence() -> SequenceNode:
        start = consume(lambda t: t.src == '[')
        expr_list = []
        while tokens and tokens[0].src != ']':
            expr_list.append(parse_expr())
        if len(expr_list) == 0:
            parser_error(start.sl, 'zero-length sequence')
        consume(lambda t: t.src == ']')
        return SequenceNode(start.sl, expr_list)

    def parse_query() -> QueryNode:
        start = consume(lambda t: t.src == '@')
        var = parse_variable()
        expr = parse_expr()
        return QueryNode(start.sl, var, [expr])

    def parse_access() -> AccessNode:
        start = consume(lambda t: t.src == '&')
        var = parse_variable()
        expr = parse_expr()
        return AccessNode(start.sl, var, expr)

    def parse_expr() -> ExprNode:
        if not tokens:
            parser_error(SourceLocation(-1, -1), 'incomplete token stream')
        elif is_number_token(tokens[0]):
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

    def __init__(self, n: Union[int, bool], d: Union[int, None] = None):
        self.location = None
        if type(n) == bool:
            self.n = 1 if n else 0
            self.d = 1
        else:
            self.n = n
            self.d = 1 if d is None else d

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
        return f'<closure evaluated at {self.fun.sl}>'

class Layer:
    '''Each layer on the stack contains the (sub-)expression currently under evaluation.'''

    def __init__(self, env: list[tuple[str, int]], expr: ExprNode, frame: Union[bool, None] = None, tail: Union[bool, None] = None):
        # environment (shared among layers in each frame) for the evaluation of the current expression
        self.env = env 
        # the current expression under evaluation
        self.expr = expr
        # whether this layer starts a frame (a closure call or the initial layer)
        self.frame = False if frame is None else frame
        # whether this layer is in tail position (for tail call optimization)
        self.tail = False if tail is None else tail
        # program counter (the pc-th step of evaluating this expression)
        self.pc = 0
        # temporary variables for this layer, where variables can only hold Values or lists of Values
        self.local = {}

class Continuation(Value):

    def __init__(self, sl: SourceLocation, stack: list[Layer]):
        self.location = None
        self.sl = sl
        # we only need to store the stack, because objects in the heap are immutable
        self.stack = stack

    def __str__(self) -> str:
        return f'<continuation evaluated at {self.sl}>'

def check_or_exit(sl: SourceLocation, args: list[Value], ts: list[type]) -> bool:
    ''' check whether arguments conform to types '''
    if len(args) != len(ts):
        runtime_error(sl, 'wrong number of arguments given to callee')
    for i in range(len(args)):
        if not isinstance(args[i], ts[i]):
            runtime_error(sl, 'wrong type of arguments given to callee')

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
        # stack (tail call optimization never removes the main frame)
        main_env = []
        self.stack = [Layer(main_env, None, frame = True), Layer(main_env, expr)]
        # heap
        self.store = []
        self.end = 0
        # evaluation result
        self.value = None
    
    def execute(self) -> 'State':
        # we just update "state.stack" and "stack.value"
        # the evaluation will automatically continue along the while loop
        while True:

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
                # evaluation result for each binding expression
                if 1 < layer.pc <= len(layer.expr.var_expr_list) + 1:
                    var = layer.expr.var_expr_list[layer.pc - 2][0]
                    last_location = lookup_env(var.name, layer.env)
                    if last_location is None:
                        runtime_error(var.sl, 'undefined variable')
                    self.store[last_location] = self.value
                # letrec always create new locations
                if layer.pc == 0:
                    for v, _ in layer.expr.var_expr_list:
                        layer.env.append((v.name, self._new(Void())))
                    layer.pc += 1
                # evaluate binding expressions
                elif layer.pc <= len(layer.expr.var_expr_list):
                    self.stack.append(Layer(layer.env, layer.expr.var_expr_list[layer.pc - 1][1]))
                    layer.pc += 1
                # evaluate body expression
                elif layer.pc == len(layer.expr.var_expr_list) + 1:
                    self.stack.append(Layer(layer.env, layer.expr.expr, tail = layer.frame or layer.tail))
                    layer.pc += 1
                # finish letrec
                else:
                    # this is necessary because letrec layer's env is shared with its previous frame
                    for i in range(len(layer.expr.var_expr_list)):
                        layer.env.pop()
                    # we cannot pop this layer earlier,
                    # because we need to revert the environment before popping it
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
                    # evaluation result for each argument
                    if 1 < layer.pc <= len(layer.expr.arg_list) + 1:
                        layer.local['args'].append(self.value)
                    # initialize args
                    if layer.pc == 0:
                        layer.local['args'] = []
                        layer.pc += 1
                    # evaluate arguments
                    elif layer.pc <= len(layer.expr.arg_list):
                        self.stack.append(Layer(layer.env, layer.expr.arg_list[layer.pc - 1]))
                        layer.pc += 1
                    # intrinsic call doesn't need to grow the stack, so this is the final step for this call
                    else:
                        intrinsic = layer.expr.callee.name
                        args = layer.local['args']
                        # a gigantic series of if conditions, one for each intrinsic function
                        if intrinsic == '.+':
                            check_or_exit(layer.expr.sl, args, [Number] * len(args))
                            self.value = reduce(lambda x, y: x.add(y), args, Number(0))
                        elif intrinsic == '.-':
                            check_or_exit(layer.expr.sl, args, [Number, Number])
                            self.value = args[0].sub(args[1])
                        elif intrinsic == '.*':
                            check_or_exit(layer.expr.sl, args, [Number] * len(args))
                            self.value = reduce(lambda x, y: x.mul(y), args, Number(1))
                        elif intrinsic == './':
                            check_or_exit(layer.expr.sl, args, [Number, Number])
                            self.value = args[0].div(args[1], layer.expr.sl)
                        elif intrinsic == '.%':
                            check_or_exit(layer.expr.sl, args, [Number, Number])
                            self.value = args[0].mod(args[1], layer.expr.sl)
                        elif intrinsic == '.<':
                            check_or_exit(layer.expr.sl, args, [Number, Number])
                            self.value = Number(args[0].lt(args[1]))
                        elif intrinsic == '.slen':
                            check_or_exit(layer.expr.sl, args, [String])
                            self.value = Number(len(args[0].value))
                        elif intrinsic == '.ssub':
                            check_or_exit(layer.expr.sl, args, [String, Number, Number])
                            if args[1].d != 1 or args[2].d != 1:
                                runtime_error(layer.expr.sl, '.strcut is applied to non-integer(s)')
                            self.value = String(args[0].value[args[1].n : args[2].n])
                        elif intrinsic == '.s+':
                            check_or_exit(layer.expr.sl, args, [String] * len(args))
                            self.value = String(reduce(lambda x, y: x + y.value, args, ''))
                        elif intrinsic == '.s<':
                            check_or_exit(layer.expr.sl, args, [String, String])
                            self.value = Number(args[0].value < args[1].value)
                        elif intrinsic == '.s->n':
                            check_or_exit(layer.expr.sl, args, [String])
                            node = parse(deque([Token(layer.expr.sl, args[0].value)]))
                            if not isinstance(node, NumberNode):
                                runtime_error(layer.expr.sl, '.strnum is applied to non-number-string')
                            self.value = Number(node.n, node.d)
                        elif intrinsic == '.squote':
                            check_or_exit(layer.expr.sl, args, [String])
                            quoted = '"'
                            for char in args[0].value:
                                if char in ('\\', '"'):
                                    quoted += '\\'
                                quoted += char
                            quoted += '"'
                            self.value = String(quoted)
                        elif intrinsic == '.getline':
                            check_or_exit(layer.expr.sl, args, [])
                            try:
                                self.value = String(input())
                            except EOFError:
                                self.value = Void()
                        elif intrinsic == '.put':
                            if not (len(args) >= 1 and all(map(lambda v : isinstance(v, Value), args))):
                                runtime_error(layer.expr.sl, 'wrong number/type of arguments given to .put')
                            output = ''
                            for v in args:
                                output += str(v)
                            print(output, end = '', flush = True)
                            # the return value of put is void
                            self.value = Void()
                        elif intrinsic == '.call/cc':
                            check_or_exit(layer.expr.sl, args, [Closure])
                            self.stack.pop()
                            # obtain the continuation (this deepcopy will not copy the store)
                            addr = self._new(Continuation(layer.expr.sl, deepcopy(self.stack)))
                            closure = args[0]
                            # make a closure call layer and pass in the continuation
                            self.stack.append(Layer(closure.env[:] + [(closure.fun.var_list[0].name, addr)], closure.fun.expr, frame = True))
                            # we already popped the stack in this case, so just continue the evaluation
                            continue
                        elif intrinsic == '.n?':
                            check_or_exit(layer.expr.sl, args, [Value])
                            self.value = Number(isinstance(args[0], Number))
                        elif intrinsic == '.s?':
                            check_or_exit(layer.expr.sl, args, [Value])
                            self.value = Number(isinstance(args[0], String))
                        elif intrinsic == '.c?':
                            check_or_exit(layer.expr.sl, args, [Value])
                            self.value = Number(isinstance(args[0], Closure))
                        elif intrinsic == '.cont?':
                            check_or_exit(layer.expr.sl, args, [Value])
                            self.value = Number(isinstance(args[0], Continuation))
                        elif intrinsic == '.eval':
                            check_or_exit(layer.expr.sl, args, [String])
                            self.value = run_code(args[0].value)
                        elif intrinsic == '.exit':
                            check_or_exit(layer.expr.sl, args, [])
                            # the interpreter returns 0
                            sys.exit()
                        else:
                            runtime_error(layer.expr.sl, 'unrecognized intrinsic function call')
                        self.stack.pop()
                # closure or continuation call
                else:
                    # evaluation result for each argument
                    if 2 < layer.pc <= len(layer.expr.arg_list) + 2:
                        layer.local['args'].append(self.value)
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
                    elif layer.pc <= len(layer.expr.arg_list) + 1:
                        self.stack.append(Layer(layer.env, layer.expr.arg_list[layer.pc - 2]))
                        layer.pc += 1
                    # evaluate the call
                    elif layer.pc == len(layer.expr.arg_list) + 2:
                        callee = layer.local['callee']
                        args = layer.local['args']
                        if type(callee) == Closure:
                            closure = callee
                            # types will be checked inside the closure call
                            if len(args) != len(closure.fun.var_list):
                                runtime_error(layer.expr.sl, 'wrong number of arguments given to callee')
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
                                runtime_error(layer.expr.sl, 'wrong number of arguments given to callee')
                            # "self.value" already contains the last evaluation result of the args
                            # replace the stack
                            self.stack = deepcopy(cont.stack)
                            # the stack has been replaced, so we don't need to pop the previous stack's call layer
                            continue
                        else:
                            runtime_error(layer.expr.sl, 'calling non-callable object')
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
                    runtime_error(layer.expr.sl, '@ query on non-lex variable')
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

    def _new(self, value: Value) -> int:
        if self.end < len(self.store):
            self.store[self.end] = value
        else:
            self.store.append(value)
        value.location = self.end
        self.end += 1
        return self.end - 1

    def _traverse(self, value_callback: Callable, location_callback: Callable) -> None:
        # ids
        visited_values = set()
        # locations
        visited_locations = set()

        def traverse_value(value: Value) -> None:
            if id(value) not in visited_values:
                value_callback(value)
                visited_values.add(id(value))
                if type(value) == Closure:
                    for _, loc in value.env:
                        traverse_location(loc)
                elif type(value) == Continuation:
                    for layer in value.stack:
                        if layer.frame:
                            for _, loc in layer.env:
                                traverse_location(loc)
                        if layer.local:
                            for _, v in layer.local.items():
                                traverse_value(v)

        def traverse_location(location: int) -> None:
            if location not in visited_locations:
                location_callback(location)
                visited_locations.add(location)
                traverse_value(self.store[location])

        traverse_value(Continuation(SourceLocation(-1, -1), self.stack))
        traverse_value(self.value)

    def _mark(self) -> set[int]:
        visited_locations = set()
        self._traverse(lambda _: None, lambda location: visited_locations.add(location))
        return visited_locations

    def _sweep_and_compact(self, visited_locations: set[int]) -> tuple[int, dict[int, int]]:
        removed = 0
        # maps old locations to new locations
        relocation_dict = {}
        i, j = 0, 0
        while j < self.end:
            if j in visited_locations:
                self.store[i] = self.store[j]
                self.store[i].location = i
                relocation_dict[j] = i
                i += 1
            else:
                removed += 1
            j += 1
        # adjust the next available location
        self.end = i
        return (removed, relocation_dict)
    
    def _relocate(self, relocation_dict: dict[int, int]) -> None:
        
        def value_callback(value: Value) -> None:
            if type(value) == Closure:
                for i in range(len(value.env)):
                    value.env[i] = (value.env[i][0], relocation_dict[value.env[i][1]])
            elif type(value) == Continuation:
                for layer in value.stack:
                    if layer.frame:
                        for i in range(len(layer.env)):
                            layer.env[i] = (layer.env[i][0], relocation_dict[layer.env[i][1]])

        self._traverse(value_callback, lambda _: None)

    def _gc(self) -> int:
        visited_locations = self._mark()
        removed, relocation_dict = self._sweep_and_compact(visited_locations)
        self._relocate(relocation_dict)
        return removed
        
### main

def run_code(source: str) -> Value:
    return State(parse(lex(source))).execute().value

if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit(f'[Note] Usage:\n\tpython3 {sys.argv[0]} <source-file>')
    with open(sys.argv[1], 'r', encoding = 'utf-8') as f:
        sys.stderr.write(f'[Note] program value = {run_code(f.read())}\n')
    if sys.platform.startswith('linux') or sys.platform.startswith('darwin'):
        import resource
        ru = resource.getrusage(resource.RUSAGE_SELF)
        mem_factor = 1048576 / 1000 if sys.platform.startswith('linux') else 1048576
        sys.stderr.write(
            f'User time (seconds) = {round(ru.ru_utime, 3)}\n'
            f'System time (seconds) = {round(ru.ru_stime, 3)}\n'
            f'Peak memory (MiB) = {round(ru.ru_maxrss / mem_factor, 3)}\n'
        )
