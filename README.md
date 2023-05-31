# expr

![](https://github.com/sdingcn/expr/actions/workflows/auto-test.yml/badge.svg)

## dependencies

Python >= 3.9

## syntax and semantics

```
<int> := [+-]?0 | [+-]?[1-9][0-9]*
<var> := [a-zA-Z]+ ; except for keywords and intrinsic function names
```

```
<intrinsic> := add | sub | mul | div | mod | lt | void | get | put | callcc | exit
<var-list> := epsilon | <var> <var-list>
<var-expr-list> := epsilon | <var> = <expr> <var-expr-list>
<expr-list> := epsilon | <expr> <expr-list>
<expr> := <int>
        | lambda ( <var-list> ) { <expr> }
        | letrec ( <var-expr-list> ) { <expr> }
        | if <expr> then <expr> else <expr>
        | <var> ; can hold void, ints, lambdas, continuations, but cannot hold intrinsics
        | ( <intrinsic> <expr-list> ) ; intrinsic / lambda / continuation call
        | [ <expr> <expr-list> ] ; sequence
```

| feature | status |
| --- | --- |
| first-class functions | complete |
| lexical scope and closures | complete |
| dynamic scope | not started |
| letrec and (mutual) recursion | complete |
| mark-and-sweep garbage collection | in progress |
| first-class continuations | not started |

The full semantic reference is the interpreter itself.

## interpreter usage

`python3 src/interpreter.py run <file>` runs the code in `<file>`.

`python3 src/interpreter.py dump-ast <file>` dumps the AST of the code in `<file>`.

`python3 test.py` runs all tests.
