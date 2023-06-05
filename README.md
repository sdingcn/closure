# expr

Expr is a simple, dynamically-typed, functional programming language.

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
<intrinsic> := void
             | add | sub | mul | div | mod | lt
             | strlen | strslice | strcat | strlt | strint
             | getline
             | put
             | callcc
             | type
             | exit
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
Other features and intrinsic functions should be intuitive.
The full semantic reference is the interpreter itself.

## usage

+ `python3 src/interpreter.py run <file>` runs code in `<file>`.

+ `python3 src/interpreter.py debug <file>` runs code in `<file>` and prints (to `stderr`) intermediate steps.

+ `python3 src/interpreter.py dump-ast <file>` dumps AST of code in `<file>`.

+ `python3 test.py` runs all tests (see `test.py` for inputs/outputs of each test program).
