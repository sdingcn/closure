# expr

Expr is a simple, dynamically-typed, functional programming language with first-class continuations.
The main purpose of this project is to demonstrate the implementation of interpreters.

![](https://github.com/sdingcn/expr/actions/workflows/auto-test.yml/badge.svg)

## dependencies

Python >= 3.9

## example

```
letrec (
  f = lambda (x) {
    if (lt x 0) then (void)
    else [(put x "\n") (g (sub x 1))]
  }
  g = lambda (x) {
    if (lt x 0) then (void)
    else [(put x "\n") (f (sub x 1))]
  }
) {
  (f 10)
}
```

For more examples, see `test/`.

## feature summary

| feature | status |
| --- | --- |
| first-class functions | complete |
| lexically scoped variables and closures | complete |
| dynamically scoped variables | complete |
| letrec and (mutual) recursion | complete |
| first-class continuations | complete |
| dynamic type check | complete |
| mark-and-sweep garbage collection | complete |

## syntax and semantics

```
<int> := [+-]?0 | [+-]?[1-9][0-9]*
<str> := <Python-double-quote-str-literal>
<lex-var> := [a-z][a-zA-Z]*                     ; lexically scoped variable
<dyn-var> := [A-Z][a-zA-Z]*                     ; dynamically scoped variable
<var> := <lex-var> | <dyn-var>
<intrinsic> := void                             ; zero-argument function returning void
  | add | sub | mul | div | mod | lt            ; integer arithmetic and comparison
  | strlen | strslice | strcat | strlt | strint ; string length, slice, concatenation, comparison, conversion to integer
  | getline                                     ; read a line from stdin and discard newline character(s)
  | put                                         ; write at least one value to stdout (no separator, no automatic newline)
  | callcc                                      ; call with current continuation
  | type                                        ; type tester (Void->0, Integer->1, String->2, Closure->3, Continuation->4)
  | exit                                        ; stop the interpreter (the interpreter's return value is 0)
<binding> := <var> = <expr>
<callee> := <intrinsic> | <expr>
<expr> := <int>                                 ; integer literal
  | <str>                                       ; string literal
  | lambda ( <var>* ) { <expr> }                ; lambda function
  | letrec ( <binding>* ) { <expr> }            ; letrec binding (left-to-right evaluation)
  | if <expr> then <expr> else <expr>           ; if expression (condition must be an integer, 0 is false and others are true)
  | <var>                                       ; variable dereference
  | ( <callee> <expr>* )                        ; intrinsic / closure / continuation call
  | [ <expr>+ ]                                 ; sequence (left-to-right evaluation, return the last evaluation result)
```

Supported types: Void, Integer, String, Closure, Continuation.
Data structures (e.g. lists, trees) can be implemented using closures (see `test/`).
Objects are immutable.
Variables are references to objects and are immutable once bound.
Garbage collection (GC) runs when 80% of the reserved heap space is occupied,
and if GC cannot reduce the occupancy to be smaller than 80%, the reserved heap space will grow.
The full semantic reference is the interpreter code.

## usage

+ `python3 src/interpreter.py run <file>` runs code in `<file>`.

+ `python3 src/interpreter.py time <file>` runs code in `<file>` and prints (to `stderr`) execution time.

+ `python3 src/interpreter.py space <file>` runs code in `<file>` and prints (to `stderr`) peak memory usage (may slow down the interpreter).

+ `python3 src/interpreter.py debug <file>` runs code in `<file>` and prints (to `stderr`) the interpreter's intermediate steps.

+ `python3 src/interpreter.py dump-ast <file>` dumps AST of code in `<file>`.

+ `python3 test.py` runs all tests (see `test.py` for inputs/outputs for each test program).
