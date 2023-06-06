# expr

Expr is a simple, dynamically-typed, functional programming language with first-class continuations and mark-and-sweep garbage collection.
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
<int>       := [+-]?0 | [+-]?[1-9][0-9]*
<str>       := <Python-double-quote-string-literal>
<lex-var>   := [a-z][a-zA-Z]*
<dyn-var>   := [A-Z][a-zA-Z]*
<var>       := <lex-var> | <dyn-var>
<intrinsic> := void                                        ; zero-argument function returning a void value
             | add | sub | mul | div | mod | lt            ; integer arithmetic and comparison
             | strlen | strslice | strcat | strlt | strint ; string length / slicing / concatenation / comparison / conversion to integer
             | getline                                     ; reading a line from stdin and discarding the trailing newline character(s)
             | put                                         ; writing arbitrarily many values to stdout (not separated by anything, no automatic newline)
             | callcc                                      ; calling with current continuation
             | type                                        ; type tester (Void: 0, Int: 1, String: 2, Closure: 3, Continuation: 4)
             | exit                                        ; immediately stopping the interpreter (the interpreter's return value is still 0)
<binding>   := <var> = <expr>
<callee>    := <intrinsic> | <expr>
<expr>      := <int>                             ; integer literal
             | <str>                             ; string literal
             | lambda ( <var>* ) { <expr> }      ; lambda function
             | letrec ( <binding>* ) { <expr> }  ; letrec binding
             | if <expr> then <expr> else <expr> ; if expression
             | <var>                             ; variable dereference
             | ( <callee> <expr>* )              ; intrinsic / closure / continuation call
             | [ <expr>+ ]                       ; sequence evaluation
```

Supported types of objects: Void, Integer, String, Closure, Continuation.
Common data structures (e.g. lists, binary trees) can be implemented using closures (see `test/` for examples).
All objects are immutable.
All variables are references to objects and are immutable once bound.
Variables starting with lower-case letters are lexically scoped;
variables starting with upper-case letters are dynamically scoped.
Garbage collection (GC) automatically runs when 80% of the reserved heap space is occupied,
and if GC cannot reduce the occupancy to be smaller than 80% then the reserved space will grow.
Other features and intrinsic functions should be intuitive.
The full semantic reference is the interpreter itself.

## usage

+ `python3 src/interpreter.py run <file>` runs code in `<file>`.

+ `python3 src/interpreter.py time <file>` runs code in `<file>` and prints (to `stderr`) the time usage.

+ `python3 src/interpreter.py space <file>` runs code in `<file>` and prints (to `stderr`) the peak memory usage (this option can cause more time usage).

+ `python3 src/interpreter.py debug <file>` runs code in `<file>` and prints (to `stderr`) the interpreter's intermediate steps.

+ `python3 src/interpreter.py dump-ast <file>` dumps AST of code in `<file>`.

+ `python3 test.py` runs all tests (see `test.py` for inputs/outputs of each test program).
