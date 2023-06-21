import sys
import time
import tracemalloc
import re
from collections import deque
from typing import Union, Any
from copy import deepcopy

### helper functions

def unfold(value: Union[list[Any], tuple[Any, ...], set[Any], dict[Any, Any]]) -> str:
    '''Recursively unfold a container to a readable string'''
    if type(value) == list:
        s = '['
    elif type(value) == tuple:
        s = '('
    elif type(value) in [set, dict]:
        s = '{'
    else:
        sys.exit('[Internal Error] unsupported argument given to unfold')
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

def indent(source: str, cnt: int) -> str:
    return '\n'.join(list(map(lambda s: (' ' * cnt) + s, source.splitlines())))

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
    else:
        return gcd(b, a % b)

### lexer

class SourceLocation:

    def __init__(self, line: int, col: int):
        self.line = line
        self.col = col

    def __str__(self) -> str:
        return f'(SourceLocation {self.line} {self.col})'

class Token:

    def __init__(self, sl: SourceLocation, src: str):
        self.sl = sl
        self.src = src

    def __str__(self) -> str:
        return f'(Token {self.sl} {self.src})'

def lex(source: str, debug: bool) -> deque[Token]:
    if debug:
        sys.stderr.write('[Debug] *** starting lexer ***\n')

    # only support these characters in source code
    charset = set(
        "abcdefghijklmnopqrstuvwxyz"
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        "0123456789"
        "`~!@#$%^&*()-_=+[{]}\\|;:'\",<.>/?"
        " \t\n"
    )

    for char in source:
        if char not in charset:
            sys.exit(f'[Lexer Error] unsupported character {char} in the source')

    # number format checker

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

    # escape counting

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

    # token reader

    chars = deque(source)
    line = 1
    col = 1

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
                    sys.exit(f'[Lexer Error] invalid number literal at {sl} (note: do not use leading zeros or trailing zeros)')
            # variable / keyword
            elif chars[0].isalpha():
                src = ''
                while chars and chars[0].isalpha():
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
                    sys.exit(f'[Lexer Error] incomplete string literal at {sl}')
            # comment
            elif chars[0] == '#':
                chars.popleft()
                col += 1
                while chars and chars[0] != '\n':
                    chars.popleft()
                    col += 1
                return next_token()
            else:
                sys.exit(f'[Lexer Error] unsupported character {chars[0]} at {sl}')
            token = Token(sl, src)
            return token
        else:
            return None

    # lexer entry
    tokens = deque()
    while True:
        token = next_token()
        if token:
            if debug:
                sys.stderr.write(f'[Debug] read token {token}\n')
            tokens.append(token)
        else:
            break
    return tokens

### parser

class ExprNode:
    ''' Normally we don't create instances of this base class. '''

    def __init__(self):
        pass

    def __str__(self) -> str:
        return 'ExprNode'

    def pretty_print(self) -> str:
        return ''

class NumberNode(ExprNode):

    def __init__(self, sl: SourceLocation, parent: Union[None, ExprNode], n: int, d: int):
        self.sl = sl
        self.parent = parent
        # simplify it to avoid repeatedly doing this when evaluating the AST node
        g = gcd(abs(n), d)
        self.n = n // g
        self.d = d // g

    def __str__(self) -> str:
        return f'(NumberNode {self.sl} {self.n} {self.d})'

    def pretty_print(self) -> str:
        s = repr(self.n)
        if self.d != 1:
            s += '/'
            s += repr(self.d)
        return s

class StringNode(ExprNode):

    def __init__(self, sl: SourceLocation, parent: Union[None, ExprNode], value: str):
        self.sl = sl
        self.parent = parent
        self.value = value

    def __str__(self) -> str:
        return f'(StringNode {self.sl} {quote(self.value)})'

    def pretty_print(self) -> str:
        return quote(self.value)

class IntrinsicNode(ExprNode):

    def __init__(self, sl: SourceLocation, parent: Union[None, ExprNode], name: str):
        self.sl = sl
        self.parent = parent
        self.name = name

    def __str__(self) -> str:
        return f'(IntrinsicNode {self.sl} {self.name})'

    def pretty_print(self) -> str:
        return self.name

class VariableNode(ExprNode):

    def __init__(self, sl: SourceLocation, parent: Union[None, ExprNode], name: str):
        self.sl = sl
        self.parent = parent
        self.name = name

    def __str__(self) -> str:
        return f'(VariableNode {self.sl} {self.name})'

    def pretty_print(self) -> str:
        return self.name

    def is_lex(self) -> bool:
        return self.name[0].islower()

    def is_dyn(self) -> bool:
        return self.name[0].isupper()

class LambdaNode(ExprNode):

    def __init__(self, sl: SourceLocation, parent: Union[None, ExprNode], var_list: list[VariableNode], expr: ExprNode):
        self.sl = sl
        self.parent = parent
        self.var_list = var_list
        self.expr = expr

    def __str__(self) -> str:
        return f'(LambdaNode {self.sl} {unfold(self.var_list)} {self.expr})'

    def pretty_print(self) -> str:
        return ('lambda (' + ' '.join(list(map(lambda v: v.pretty_print(), self.var_list))) + ') ' + '{\n'
              + indent(self.expr.pretty_print(), 2) + '\n'
              + '}')

class LetrecNode(ExprNode):

    def __init__(self, sl: SourceLocation, parent: Union[None, ExprNode], var_expr_list: list[tuple[VariableNode, ExprNode]], expr: ExprNode):
        self.sl = sl
        self.parent = parent
        self.var_expr_list = var_expr_list
        self.expr = expr

    def __str__(self) -> str:
        return f'(LetrecNode {self.sl} {unfold(self.var_expr_list)} {self.expr})'

    def pretty_print(self) -> str:
        return ('letrec (\n'
              + indent('\n'.join(list(map(lambda ve: ve[0].pretty_print() + ' = ' + ve[1].pretty_print(), self.var_expr_list))), 2) + '\n'
              + ') {\n'
              + indent(self.expr.pretty_print(), 2) + '\n'
              + '}')

class IfNode(ExprNode):

    def __init__(self, sl: SourceLocation, parent: Union[None, ExprNode], cond: ExprNode, branch1: ExprNode, branch2: ExprNode):
        self.sl = sl
        self.parent = parent
        self.cond = cond
        self.branch1 = branch1
        self.branch2 = branch2

    def __str__(self) -> str:
        return f'(IfNode {self.sl} {self.cond} {self.branch1} {self.branch2})'

    def pretty_print(self) -> str:
        return ('if ' + self.cond.pretty_print() + ' then ' + self.branch1.pretty_print() + '\n'
              + 'else ' + self.branch2.pretty_print())

class CallNode(ExprNode):

    def __init__(self, sl: SourceLocation, parent: Union[None, ExprNode], callee: ExprNode, arg_list: list[ExprNode]):
        self.sl = sl
        self.parent = parent
        self.callee = callee
        self.arg_list = arg_list

    def __str__(self) -> str:
        return f'(CallNode {self.sl} {self.callee} {unfold(self.arg_list)})'

    def pretty_print(self) -> str:
        return '(' + ' '.join([self.callee.pretty_print()] + list(map(lambda a: a.pretty_print(), self.arg_list))) + ')'

class SequenceNode(ExprNode):

    def __init__(self, sl: SourceLocation, parent: Union[None, ExprNode], expr_list: list[ExprNode]):
        self.sl = sl
        self.parent = parent
        self.expr_list = expr_list

    def __str__(self) -> str:
        return f'(SequenceNode {self.sl} {unfold(self.expr_list)})'

    def pretty_print(self) -> str:
        return ('[\n'
              + indent('\n'.join(list(map(lambda e: e.pretty_print(), self.expr_list))), 2) + '\n'
              + ']')

class QueryNode(ExprNode):

    def __init__(self, sl: SourceLocation, parent: Union[None, ExprNode], var: VariableNode, expr_box: list[ExprNode]):
        self.sl = sl
        self.parent = parent
        self.var = var
        self.expr_box = expr_box

    def __str__(self) -> str:
        return f'(QueryNode {self.sl} {self.var} {unfold(self.expr_box)})'

    def pretty_print(self) -> str:
        if len(self.expr_box) == 0:
            tail = ''
        else:
            tail = ' ' + self.expr_box[0].pretty_print()
        return '@' + self.var.pretty_print() + tail

class AccessNode(ExprNode):

    def __init__(self, sl: SourceLocation, parent: Union[None, ExprNode], var: VariableNode, expr: ExprNode):
        self.sl = sl
        self.parent = parent
        self.var = var
        self.expr = expr

    def __str__(self) -> str:
        return f'(AccessNode {self.sl} {self.var} {self.expr})'

    def pretty_print(self) -> str:
        return '&' + self.var.pretty_print() + ' ' + self.expr.pretty_print()

def parse(tokens: deque[Token], debug: bool) -> ExprNode:
    if debug:
        sys.stderr.write('[Debug] *** starting parser ***\n')
    
    # token checkers

    def is_number_token(token: Token) -> bool:
        return len(token.src) and (token.src[0].isdigit() or token.src[0] in ('-', '+'))

    def is_string_token(token: Token) -> bool:
        return len(token.src) and token.src[0] == '"'

    def is_intrinsic_token(token: Token) -> bool:
        return len(token.src) and token.src[0] == '.'

    def is_variable_token(token: Token) -> bool:
        return token.src.isalpha()

    # specific token consumer

    def consume(expected: str) -> Token:
        if not tokens:
            sys.exit(f'[Parser Error] incomplete token stream')
        token = tokens.popleft()
        if token.src == expected:
            return token
        else:
            sys.exit(f'[Parser Error] expected {expected}, got {token}')

    # parsers

    def parse_number() -> NumberNode:
        if not tokens:
            sys.exit(f'[Parser Error] incomplete token stream')
        token = tokens.popleft()
        if not is_number_token(token):
            sys.exit(f'[Parser Error] expected a number, got {token}')
        s = token.src
        sign = 1
        if len(s) and s[0] in ('-', '+'):
            if s[0] == '-':
                sign = -1
            s = s[1:]
        if '/' in s:
            parts = s.split('/')
            node = NumberNode(token.sl, None, sign * int(parts[0]), int(parts[1]))
        elif '.' in s:
            parts = s.split('.')
            depth = len(parts[1])
            node = NumberNode(token.sl, None, sign * (int(parts[0]) * (10 ** depth) + int(parts[1])), 10 ** depth)
        else:
            node = NumberNode(token.sl, None, sign * int(s), 1)
        return node

    def parse_string() -> StringNode:
        if not tokens:
            sys.exit(f'[Parser Error] incomplete token stream')
        token = tokens.popleft()
        if not is_string_token(token):
            sys.exit(f'[Parser Error] expected a string, got {token}')
        # "abc" -> deque(abc)
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
                        sys.exit(f'[Parser Error] unsupported escape sequence at {token}')
                else:
                    sys.exit(f'[Parser Error] incomplete escape sequence at {token}')
            else:
                s += char
        node = StringNode(token.sl, None, s)
        return node

    def parse_intrinsic() -> IntrinsicNode:
        if not tokens:
            sys.exit(f'[Parser Error] incomplete token stream')
        token = tokens.popleft()
        if not is_intrinsic_token(token):
            sys.exit(f'[Parser Error] expected an intrinsic function, got {token}')
        node = IntrinsicNode(token.sl, None, token.src)
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
        node = LambdaNode(start.sl, None, var_list, expr)
        for v in node.var_list:
            v.parent = node
        node.expr.parent = node
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
        node = LetrecNode(start.sl, None, var_expr_list, expr)
        for v, e in node.var_expr_list:
            v.parent = node
            e.parent = node
        node.expr.parent = node
        return node

    def parse_if() -> IfNode:
        start = consume('if')
        cond = parse_expr()
        consume('then')
        branch1 = parse_expr()
        consume('else')
        branch2 = parse_expr()
        node = IfNode(start.sl, None, cond, branch1, branch2)
        node.cond.parent = node
        node.branch1.parent = node
        node.branch2.parent = node
        return node

    def parse_variable() -> VariableNode:
        if not tokens:
            sys.exit(f'[Parser Error] incomplete token stream')
        token = tokens.popleft()
        if not is_variable_token(token):
            sys.exit(f'[Parser Error] expected a variable, got {token}')
        node = VariableNode(token.sl, None, token.src)
        return node

    def parse_call() -> CallNode:
        start = consume('(')
        callee = parse_expr()
        arg_list = []
        while tokens and tokens[0].src != ')':
            arg_list.append(parse_expr())
        consume(')')
        node = CallNode(start.sl, None, callee, arg_list)
        node.callee.parent = node
        for a in node.arg_list:
            a.parent = node
        return node

    def parse_sequence() -> SequenceNode:
        start = consume('[')
        expr_list = []
        while tokens and tokens[0].src != ']':
            expr_list.append(parse_expr())
        if len(expr_list) == 0:
            sys.exit('[Parser Error] zero-length sequence at {start}')
        consume(']')
        node = SequenceNode(start.sl, None, expr_list)
        for e in node.expr_list:
            e.parent = node
        return node

    def parse_query() -> QueryNode:
        start = consume('@')
        var = parse_variable()
        if var.is_lex():
            expr = parse_expr()
            node = QueryNode(start.sl, None, var, [expr])
            var.parent = node
            expr.parent = node
        else:
            node = QueryNode(start.sl, None, var, [])
            var.parent = node
        return node

    def parse_access() -> AccessNode:
        start = consume('&')
        var = parse_variable()
        expr = parse_expr()
        node = AccessNode(start.sl, None, var, expr)
        var.parent = node
        expr.parent = node
        return node

    def parse_expr() -> ExprNode:
        if not tokens:
            sys.exit(f'[Parser Error] incomplete token stream')
        if debug:
            sys.stderr.write(f'[Debug] parsing expression starting with {tokens[0]}\n')
        if is_number_token(tokens[0]):
            return parse_number()
        elif is_string_token(tokens[0]):
            return parse_string()
        elif is_intrinsic_token(tokens[0]):
            return parse_intrinsic()
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
            sys.exit(f'[Parser Error] unrecognized expression starting with {tokens[0]}')
    
    # parser entry
    expr = parse_expr()
    if tokens:
        sys.exit(f'[Parser Error] redundant token stream starting at {tokens[0]}')
    return expr

### runtime

class Value:
    ''' Normally we don't create instances of this base class. '''
    
    def __init__(self):
        pass

    def __str__(self) -> str:
        return 'Value'

    def pretty_print(self) -> str:
        return ''

class Void(Value):

    def __init__(self):
        # the location of this value (object) in the store (if allocated)
        self.location = None

    def __str__(self) -> str:
        return 'Void'

    def pretty_print(self) -> str:
        return '<void>'

class Number(Value):

    def __init__(self, n: int, d: int = None):
        if d is None:
            d = 1
        self.location = None
        self.n = n
        self.d = d

    def __str__(self) -> str:
        return f'(Number {self.n} {self.d})'

    def pretty_print(self) -> str:
        s = repr(self.n)
        if self.d != 1:
            s += '/'
            s += repr(self.d)
        return s

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

    def div(self, other: 'Number', expr: ExprNode) -> 'Number':
        if other.n == 0:
            sys.exit(f'[Runtime Error] division by zero at {expr}')
        n1 = self.n * other.d
        d1 = self.d * other.n
        if d1 < 0:
            n1 = -n1
            d1 = -d1
        g1 = gcd(abs(n1), d1)
        return Number(n1 // g1, d1 // g1)

    def mod(self, other: 'Number', expr: ExprNode) -> 'Number':
        if self.d != 1 or other.d != 1:
            sys.exit(f'[Runtime Error] mod applied to non-integer(s) at {expr}')
        if self.n < 0 or other.n < 0:
            sys.exit(f'[Runtime Error] mod applied to negative integer(s) at {expr}')
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
        return f'(String {quote(self.value)})'

    def pretty_print(self) -> str:
        return self.value

class Closure(Value):

    def __init__(self, env: list[tuple[str, int]], fun: LambdaNode):
        self.location = None
        self.env = env
        self.fun = fun

    def __str__(self) -> str:
        return f'(Closure {unfold(self.env)} {self.fun})'

    def pretty_print(self) -> str:
        return '<closure>'

class Layer:
    '''The layer class in the evaluation stack, where each layer is the expression currently under evaluation'''

    def __init__(self,
            # env will be shared among layers in each frame
            env: list[tuple[str, int]], 
            expr: ExprNode,
            pc: int = None,
            local: dict[str, Union[Value, list[Value]]] = None,
            frame: bool = None
        ):
        if pc is None:
            pc = 0
        if local is None:
            local = {}
        if frame is None:
            frame = False
        # environment for the evaluation of the current expression
        self.env = env 
        # the current expression under evaluation
        self.expr = expr
        # program counter (the pc-th step of evaluating this expression)
        self.pc = pc
        # variables local to this evaluation layer
        self.local = local
        # whether this layer starts a frame (a closure call or the initial layer)
        self.frame = frame

    def __str__(self) -> str:
        return f'(Layer {unfold(self.env)} {self.expr} {self.pc} {unfold(self.local)} {self.frame})'

class Continuation(Value):

    def __init__(self, stack: list[Layer]):
        self.location = None
        # we only need to store the stack, because objects in the heap are immutable
        self.stack = stack

    def __str__(self) -> str:
        return f'(Continuation {unfold(self.stack)})'

    def pretty_print(self) -> str:
        return '<continuation>'

class State:
    '''The state class for the interpretation, where each state object completely determines the current state (stack and store)'''

    def __init__(self, expr: ExprNode):
        # the first layer is always a frame
        self.stack = [Layer([], expr, frame = True)]
        # the heap
        self.store = []
        # the next available addess in the store
        self.location = 0
        # private values
        self._ref_size = 8
        self._empty_store_size = sys.getsizeof(self.store)

    def __str__(self) -> str:
        return f'(State {unfold(self.stack)} {unfold(self.store)} {self.location})'

    def get_store_capacity(self) -> int:
        # capacity >= length
        return (sys.getsizeof(self.store) - self._empty_store_size) // self._ref_size

    def new(self, value: Value) -> int:
        ''' heap space allocation '''
        if self.location < len(self.store):
            self.store[self.location] = value
            value.location = self.location
        else:
            # the self.store array is managed by Python and will automatically grow
            self.store.append(value)
            value.location = self.location
        self.location += 1
        return self.location - 1

    def mark(self, value: Value) -> tuple[set[int], list[Value]]:
        # ids
        visited_closures = set()
        # ids
        visited_stacks = set()
        # integer locations
        visited_locations = set()
        # Python references
        visited_values = []

        def mark_closure(closure: Closure) -> None:
            if id(closure) not in visited_closures:
                visited_closures.add(id(closure))
                visited_values.append(closure)
                for v, l in closure.env:
                    mark_location(l)
        
        def mark_stack(stack: list[Layer]) -> None:
            if id(stack) not in visited_stacks:
                visited_stacks.add(id(stack))
                visited_values.append(stack)
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
        if type(value) == Closure:
            mark_closure(value)
        elif type(value) == Continuation:
            mark_stack(value.stack)
        mark_stack(self.stack)
        # returning visited_values is for relocating their internal location values
        return (visited_locations, visited_values)

    def sweep_and_compact(self, visited_locations: set[int]) -> tuple[int, dict[int, int]]:
        removed = 0
        # old location -> new location
        relocation = {}
        n = len(self.store)
        i = 0
        j = 0
        while j < n:
            if j in visited_locations:
                self.store[i] = self.store[j]
                self.store[i].location = i
                relocation[j] = i
                i += 1
            else:
                removed += 1
            j += 1
        # adjust the next available location
        self.location = i
        return (removed, relocation)
    
    def relocate(self, visited_values: list[Value], relocation: dict[int, int]) -> None:
        # don't need to recursively update because all descendant objects are in visited_values
        for value in visited_values: 
            if type(value) == Closure:
                for i in range(len(value.env)):
                    value.env[i] = (value.env[i][0], relocation[value.env[i][1]])
            elif type(value) == list:
                for layer in value:
                    if layer.frame:
                        for i in range(len(layer.env)):
                            layer.env[i] = (layer.env[i][0], relocation[layer.env[i][1]])

    def gc(self, value: Value) -> int:
        ''' mark-and-sweep garbage collection '''
        visited_locations, visited_values = self.mark(value)
        removed, relocation = self.sweep_and_compact(visited_locations)
        self.relocate(visited_values, relocation)
        return removed

def check_args_error_exit(callee: ExprNode, args: list[Value], ts: list[type]) -> bool:
    ''' check whether arguments conform to types '''
    if len(args) != len(ts):
        sys.exit(f'[Runtime Error] wrong number of arguments given to {callee}')
    for i in range(len(args)):
        if not isinstance(args[i], ts[i]):
            sys.exit(f'[Runtime Error] wrong type of arguments given to {callee}')

def is_lexical_name(name: str) -> bool:
    return name[0].islower()

def is_dynamic_name(name: str) -> bool:
    return name[0].isupper()

def filter_lexical(env: list[tuple[str, int]]) -> list[tuple[str, int]]:
    ''' find out lexical variable-location pairs in an environment '''
    lex_env = []
    for v, l in env:
        if is_lexical_name(v):
            lex_env.append((v, l))
    return lex_env

def lookup_env(sl: SourceLocation, name: str, env: list[tuple[str, int]]) -> int:
    ''' lexically scoped variable lookup '''
    for i in range(len(env) - 1, -1, -1):
        if env[i][0] == name:
            return env[i][1]
    sys.exit(f'[Runtime Error] undefined variable {name} at {sl} (intrinsic functions cannot be treated as variables)')

def lookup_stack(sl: SourceLocation, name: str, stack: list[Layer]) -> int:
    ''' dynamically scoped variable lookup '''
    for i in range(len(stack) - 1, -1, -1):
        if stack[i].frame:
            for j in range(len(stack[i].env) - 1, -1, -1):
                if stack[i].env[j][0] == name:
                    return stack[i].env[j][1]
    sys.exit(f'[Runtime Error] undefined variable {name} at {sl} (intrinsic functions cannot be treated as variables)')

def query_env(name: str, env: list[tuple[str, int]]) -> bool:
    ''' lexically scoped variable query '''
    for i in range(len(env) - 1, -1, -1):
        if env[i][0] == name:
            return True
    return False

def query_stack(name: str, stack: list[Layer]) -> bool:
    ''' dynamically scoped variable query '''
    for i in range(len(stack) - 1, -1, -1):
        if stack[i].frame:
            for j in range(len(stack[i].env) - 1, -1, -1):
                if stack[i].env[j][0] == name:
                    return True
    return False

### interpreter

def interpret(tree: ExprNode, debug: bool) -> Value:
    if debug:
        sys.stderr.write('[Debug] *** starting interpreter ***\n')
    
    # state
    state = State(tree)
    # the evaluation result of the last stack layer
    value = None

    # used for GC control
    insufficient_capacity = -1

    # we just adjust "state.stack" and "value"
    # the evaluation will automatically continue along the while loop
    while True:
        
        # end of evaluation
        if len(state.stack) == 0:
            return value

        # GC control
        capacity = state.get_store_capacity()
        # insufficient_capacity is the last capacity where GC failed
        if capacity > insufficient_capacity:
            if state.location >= 0.8 * capacity:
                cnt = state.gc(value)
                if debug:
                    sys.stderr.write(f'[Debug] GC collected {cnt} store cells\n')
                # GC failed to release enough memory, meaning that the capacity needs to grow
                if state.location >= 0.8 * capacity:
                    insufficient_capacity = capacity
                # after GC the current capacity is enough so we keep the previous insufficient_capacity
                else:
                    pass
        # the capacity is insufficient, so we allow it to naturally grow and don't run GC before the growing
        else:
            pass

        # evaluating the current layer
        layer = state.stack[-1]
        if debug:
            sys.stderr.write(f'[Debug] evaluating AST node of type {type(layer.expr)} at {layer.expr.sl}\n')
        if type(layer.expr) == NumberNode:
            value = Number(layer.expr.n, layer.expr.d)
            state.stack.pop()
        elif type(layer.expr) == StringNode:
            value = String(layer.expr.value)
            state.stack.pop()
        elif type(layer.expr) == LambdaNode:
            value = Closure(filter_lexical(layer.env), layer.expr)
            state.stack.pop()
        elif type(layer.expr) == LetrecNode:
            # create locations and bind variables to them
            if layer.pc == 0:
                for v, e in layer.expr.var_expr_list:
                    layer.env.append((v.name, state.new(Void())))
                layer.pc += 1
            # evaluate binding expressions
            elif layer.pc <= len(layer.expr.var_expr_list):
                # update location content
                if layer.pc > 1:
                    var = layer.expr.var_expr_list[layer.pc - 2][0]
                    last_location = lookup_env(var.sl, var.name, layer.env)
                    state.store[last_location] = value
                state.stack.append(Layer(layer.env, layer.expr.var_expr_list[layer.pc - 1][1]))
                layer.pc += 1
            # evaluate body expression
            elif layer.pc == len(layer.expr.var_expr_list) + 1:
                # update location content
                if layer.pc > 1:
                    var = layer.expr.var_expr_list[layer.pc - 2][0]
                    last_location = lookup_env(var.sl, var.name, layer.env)
                    state.store[last_location] = value
                state.stack.append(Layer(layer.env, layer.expr.expr))
                layer.pc += 1
            # finish letrec
            else:
                # this is necessary because letrec layer's env is shared with its previous frame
                for i in range(len(layer.expr.var_expr_list)):
                    layer.env.pop()
                state.stack.pop()
        elif type(layer.expr) == IfNode:
            # evaluate the condition
            if layer.pc == 0:
                state.stack.append(Layer(layer.env, layer.expr.cond))
                layer.pc += 1
            # choose the branch to evaluate
            elif layer.pc == 1:
                if type(value) != Number:
                    sys.exit(f'[Runtime Error] the condition of {layer.expr} evaluated to a value ({value}) of wrong type')
                if value.n != 0:
                    state.stack.append(Layer(layer.env, layer.expr.branch1))
                else:
                    state.stack.append(Layer(layer.env, layer.expr.branch2))
                layer.pc += 1
            # finish if
            else:
                state.stack.pop()
        elif type(layer.expr) == VariableNode:
            if debug:
                sys.stderr.write(f'[Debug] looking up the variable {layer.expr}\n')
            # two types of variables
            if is_lexical_name(layer.expr.name):
                value = state.store[lookup_env(layer.expr.sl, layer.expr.name, layer.env)]
            else:
                value = state.store[lookup_stack(layer.expr.sl, layer.expr.name, state.stack)]
            state.stack.pop()
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
                        layer.local['args'].append(value)
                    state.stack.append(Layer(layer.env, layer.expr.arg_list[layer.pc - 1]))
                    layer.pc += 1
                # intrinsic call doesn't need to grow the stack, so this is the final step for this call
                else:
                    if layer.pc > 1:
                        layer.local['args'].append(value)
                    intrinsic = layer.expr.callee.name
                    args = layer.local['args']
                    # a gigantic series of if conditions, one for each intrinsic function
                    if intrinsic == '.void':
                        check_args_error_exit(layer.expr.callee, args, [])
                        value = Void()
                    elif intrinsic == '.+':
                        check_args_error_exit(layer.expr.callee, args, [Number, Number])
                        value = args[0].add(args[1])
                    elif intrinsic == '.-':
                        check_args_error_exit(layer.expr.callee, args, [Number, Number])
                        value = args[0].sub(args[1])
                    elif intrinsic == '.*':
                        check_args_error_exit(layer.expr.callee, args, [Number, Number])
                        value = args[0].mul(args[1])
                    elif intrinsic == './':
                        check_args_error_exit(layer.expr.callee, args, [Number, Number])
                        value = args[0].div(args[1], layer.expr)
                    elif intrinsic == '.%':
                        check_args_error_exit(layer.expr.callee, args, [Number, Number])
                        value = args[0].mod(args[1], layer.expr)
                    elif intrinsic == '.floor':
                        check_args_error_exit(layer.expr.callee, args, [Number])
                        value = args[0].floor()
                    elif intrinsic == '.ceil':
                        check_args_error_exit(layer.expr.callee, args, [Number])
                        value = args[0].ceil()
                    elif intrinsic == '.<':
                        check_args_error_exit(layer.expr.callee, args, [Number, Number])
                        value = Number(1) if args[0].lt(args[1]) else Number(0)
                    elif intrinsic == '.<=':
                        check_args_error_exit(layer.expr.callee, args, [Number, Number])
                        value = Number(1) if (not args[1].lt(args[0])) else Number(0)
                    elif intrinsic == '.>':
                        check_args_error_exit(layer.expr.callee, args, [Number, Number])
                        value = Number(1) if (args[1].lt(args[0])) else Number(0)
                    elif intrinsic == '.>=':
                        check_args_error_exit(layer.expr.callee, args, [Number, Number])
                        value = Number(1) if (not args[0].lt(args[1])) else Number(0)
                    elif intrinsic == '.==':
                        check_args_error_exit(layer.expr.callee, args, [Number, Number])
                        value = Number(1) if (not args[0].lt(args[1])) and (not args[1].lt(args[0])) else Number(0)
                    elif intrinsic == '.!=':
                        check_args_error_exit(layer.expr.callee, args, [Number, Number])
                        value = Number(1) if args[0].lt(args[1]) or args[1].lt(args[0]) else Number(0)
                    elif intrinsic == '.and':
                        check_args_error_exit(layer.expr.callee, args, [Number, Number])
                        value = Number(1) if args[0].n != 0 and args[1].n != 0 else Number(0)
                    elif intrinsic == '.or':
                        check_args_error_exit(layer.expr.callee, args, [Number, Number])
                        value = Number(1) if args[0].n != 0 or args[1].n != 0 else Number(0)
                    elif intrinsic == '.not':
                        check_args_error_exit(layer.expr.callee, args, [Number])
                        value = Number(1) if args[0].n == 0 else Number(0)
                    elif intrinsic == '.strlen':
                        check_args_error_exit(layer.expr.callee, args, [String])
                        value = Number(len(args[0].value))
                    elif intrinsic == '.strcut':
                        check_args_error_exit(layer.expr.callee, args, [String, Number, Number])
                        if args[1].d != 1 or args[2].d != 1:
                            sys.exit(f'[Runtime Error] .strcut is applied to non-integer(s) at {layer.expr}')
                        value = String(args[0].value[args[1].n : args[2].n])
                    elif intrinsic == '.str+':
                        check_args_error_exit(layer.expr.callee, args, [String, String])
                        value = String(args[0].value + args[1].value)
                    elif intrinsic == '.str<':
                        check_args_error_exit(layer.expr.callee, args, [String, String])
                        value = Number(1) if args[0].value < args[1].value else Number(0)
                    elif intrinsic == '.str<=':
                        check_args_error_exit(layer.expr.callee, args, [String, String])
                        value = Number(1) if args[0].value <= args[1].value else Number(0)
                    elif intrinsic == '.str>':
                        check_args_error_exit(layer.expr.callee, args, [String, String])
                        value = Number(1) if args[0].value > args[1].value else Number(0)
                    elif intrinsic == '.str>=':
                        check_args_error_exit(layer.expr.callee, args, [String, String])
                        value = Number(1) if args[0].value >= args[1].value else Number(0)
                    elif intrinsic == '.str==':
                        check_args_error_exit(layer.expr.callee, args, [String, String])
                        value = Number(1) if args[0].value == args[1].value else Number(0)
                    elif intrinsic == '.str!=':
                        check_args_error_exit(layer.expr.callee, args, [String, String])
                        value = Number(1) if args[0].value != args[1].value else Number(0)
                    elif intrinsic == '.strnum':
                        check_args_error_exit(layer.expr.callee, args, [String])
                        node = parse(deque([Token(layer.expr.sl, args[0].value)]), debug)
                        if not isinstance(node, NumberNode):
                            sys.exit(f'[Runtime Error] .strnum applied to non-number-string at {layer.expr}')
                        value = Number(node.n, node.d)
                    elif intrinsic == '.strquote':
                        check_args_error_exit(layer.expr.callee, args, [String])
                        value = String(quote(args[0].value))
                    elif intrinsic == '.getline':
                        check_args_error_exit(layer.expr.callee, args, [])
                        try:
                            value = String(input())
                        except EOFError:
                            value = Void()
                    elif intrinsic == '.put':
                        if not (len(args) >= 1 and all(map(lambda v : isinstance(v, Value), args))):
                            sys.exit(f'[Runtime Error] wrong number/type of arguments given to {layer.expr.callee}')
                        output = ''
                        # the printing format of "put" is simpler than that of the classes' "__str__" functions
                        for v in args:
                            output += v.pretty_print()
                        print(output, end = '', flush = True)
                        # the return value of put is void
                        value = Void()
                    elif intrinsic == '.call/cc':
                        check_args_error_exit(layer.expr.callee, args, [Closure])
                        state.stack.pop()
                        # obtain the continuation (this deepcopy will not copy the store)
                        cont = Continuation(deepcopy(state.stack))
                        if debug:
                            sys.stderr.write(f'[Debug] captured continuation {cont}\n')
                        closure = args[0]
                        # make a closure call layer and pass in the continuation
                        addr = cont.location if cont.location != None else state.new(cont)
                        state.stack.append(Layer(closure.env[:] + [(closure.fun.var_list[0].name, addr)], closure.fun.expr, frame = True))
                        # we already popped the stack in this case, so just continue the evaluation
                        continue
                    elif intrinsic == '.void?':
                        check_args_error_exit(layer.expr.callee, args, [Value])
                        value = Number(1 if isinstance(args[0], Void) else 0)
                    elif intrinsic == '.num?':
                        check_args_error_exit(layer.expr.callee, args, [Value])
                        value = Number(1 if isinstance(args[0], Number) else 0)
                    elif intrinsic == '.str?':
                        check_args_error_exit(layer.expr.callee, args, [Value])
                        value = Number(1 if isinstance(args[0], String) else 0)
                    elif intrinsic == '.clo?':
                        check_args_error_exit(layer.expr.callee, args, [Value])
                        value = Number(1 if isinstance(args[0], Closure) else 0)
                    elif intrinsic == '.cont?':
                        check_args_error_exit(layer.expr.callee, args, [Value])
                        value = Number(1 if isinstance(args[0], Continuation) else 0)
                    elif intrinsic == '.eval':
                        check_args_error_exit(layer.expr.callee, args, [String])
                        arg = args[0]
                        if debug:
                            sys.stderr.write(f'[Debug] eval started a new interpreter instance at {layer.expr}\n')
                            value = debug_run(arg.value)
                            sys.stderr.write(f'[Debug] eval stopped the new interpreter instance at {layer.expr}\n')
                        else:
                            value = normal_run(arg.value)
                    elif intrinsic == '.exit':
                        check_args_error_exit(layer.expr.callee, args, [])
                        if debug:
                            sys.stderr.write(f'[Debug] execution stopped by the intrinsic call {layer.expr}\n')
                        # the interpreter returns 0
                        sys.exit()
                    elif intrinsic == '.python':
                        check_args_error_exit(layer.expr.callee, args, [String, String])
                        if debug:
                            sys.stderr.write(f'[Debug] calling Python FFI {layer.expr}\n')
                        value = String(eval(args[0].value + '({!r})'.format(args[1].value)))
                    else:
                        sys.exit(f'[Runtime Error] unrecognized intrinsic function call at {layer.expr}')
                    state.stack.pop()
            # closure or continuation call
            else:
                # evaluate the callee
                if layer.pc == 0:
                    state.stack.append(Layer(layer.env, layer.expr.callee))
                    layer.pc += 1
                # initialize callee and args
                elif layer.pc == 1:
                    layer.local['callee'] = value
                    layer.local['args'] = []
                    layer.pc += 1
                # evaluate arguments
                elif layer.pc - 1 <= len(layer.expr.arg_list):
                    if layer.pc - 1 > 1:
                        layer.local['args'].append(value)
                    state.stack.append(Layer(layer.env, layer.expr.arg_list[layer.pc - 2]))
                    layer.pc += 1
                # evaluate the call
                elif layer.pc - 1 == len(layer.expr.arg_list) + 1:
                    if layer.pc - 1 > 1:
                        layer.local['args'].append(value)
                    callee = layer.local['callee']
                    args = layer.local['args']
                    if type(callee) == Closure:
                        closure = callee
                        # types will be checked inside the closure call
                        if len(args) != len(closure.fun.var_list):
                            sys.exit(f'[Runtime Error] wrong number/type of arguments given to {layer.expr.callee}')
                        new_env = closure.env[:]
                        for i, v in enumerate(closure.fun.var_list):
                            addr = args[i].location if args[i].location != None else state.new(args[i])
                            new_env.append((v.name, addr))
                        # evaluate the closure call
                        state.stack.append(Layer(new_env, closure.fun.expr, frame = True))
                        layer.pc += 1
                    elif type(callee) == Continuation:
                        cont = callee
                        # the "value" variable already contains the last evaluation result of the args, so we just continue
                        if len(args) != 1:
                            sys.exit(f'[Runtime Error] wrong number/type of arguments given to {layer.expr.callee}')
                        # replace the stack
                        state.stack = deepcopy(cont.stack)
                        if debug:
                            sys.stderr.write(f'[Debug] applied continuation {cont}, stack switched\n')
                        # the stack has been replaced, so we don't need to pop the previous stack's call layer
                        # the previous stack is simply discarded
                        continue
                    else:
                        sys.exit(f'[Runtime Error] {layer.expr.callee} (whose evaluation result is {callee}) is not callable')
                # finish the call
                else:
                    state.stack.pop()
        elif type(layer.expr) == SequenceNode:
            # evaluate the expressions, without the need of storing the results to local
            if layer.pc < len(layer.expr.expr_list):
                state.stack.append(Layer(layer.env, layer.expr.expr_list[layer.pc]))
                layer.pc += 1
            # finish the sequence
            else:
                state.stack.pop()
        elif type(layer.expr) == QueryNode:
            if debug:
                sys.stderr.write(f'[Debug] querying the variable {layer.expr.var}\n')
            if layer.expr.var.is_lex():
                # evaluate the closure
                if layer.pc == 0:
                    state.stack.append(Layer(layer.env, layer.expr.expr_box[0]))
                    layer.pc += 1
                else:
                    if type(value) != Closure:
                        sys.exit(f'[Runtime Error] lexical variable query applied to non-closure type at {layer.expr}')
                    # the closure's value is already in "value", so we just use it and then update "value"
                    value = Number(1) if query_env(layer.expr.var.name, value.env) else Number(0)
                    state.stack.pop()
            else:
                value = Number(1) if query_stack(layer.expr.var.name, state.stack) else Number(0)
                state.stack.pop()
        elif type(layer.expr) == AccessNode:
            if debug:
                sys.stderr.write(f'[Debug] accessing the variable {layer.expr.var}\n')
            # evaluate the closure
            if layer.pc == 0:
                state.stack.append(Layer(layer.env, layer.expr.expr))
                layer.pc += 1
            else:
                if type(value) != Closure:
                    sys.exit(f'[Runtime Error] lexical variable access applied to non-closure type at {layer.expr}')
                # again, "value" already contains the closure's evaluation result
                value = state.store[lookup_env(layer.expr.sl, layer.expr.var.name, value.env)]
                state.stack.pop()
        else:
            sys.exit(f'[Runtime Error] unrecognized AST node {layer.expr}')

### main

def normal_run(source: str) -> Value:
    tokens = lex(source, False)
    tree = parse(tokens, False)
    result = interpret(tree, False)
    return result

def debug_run(source: str) -> Value:
    tokens = lex(source, True)
    tree = parse(tokens, True)
    result = interpret(tree, True)
    return result

def main(option: str, source: str) -> None:
    if option == 'run':
        print(normal_run(source).pretty_print())
    elif option == 'time':
        start_time = time.time()
        print(normal_run(source).pretty_print())
        end_time = time.time()
        sys.stderr.write(f'Total time (seconds): {end_time - start_time}\n')
    elif option == 'space':
        tracemalloc.start() 
        print(normal_run(source).pretty_print())
        current_memory, peak_memory = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        sys.stderr.write(f'Peak memory (KiB): {peak_memory / 1024}\n')
    elif option == 'debug':
        print(debug_run(source).pretty_print())
    elif option == 'ast':
        tokens = lex(source, False)
        tree = parse(tokens, False)
        print(tree)
    elif option == 'print':
        tokens = lex(source, False)
        tree = parse(tokens, False)
        print(tree.pretty_print())

if __name__ == '__main__':
    if len(sys.argv) != 3 or sys.argv[1] not in ['run', 'time', 'space', 'debug', 'ast', 'print']:
        sys.exit(
            'Usage:\n'
            f'\tpython3 {sys.argv[0]} run <source-file>\n'
            f'\tpython3 {sys.argv[0]} time <source-file>\n'
            f'\tpython3 {sys.argv[0]} space <source-file>\n'
            f'\tpython3 {sys.argv[0]} debug <source-file>\n'
            f'\tpython3 {sys.argv[0]} ast <source-file>\n'
            f'\tpython3 {sys.argv[0]} print <source-file>'
        )
    with open(sys.argv[2], 'r', encoding = 'utf-8') as f:
        main(sys.argv[1], f.read())
