# exprscript

[中文 README](README-CN.md)

![](https://github.com/sdingcn/expr/actions/workflows/auto-test.yml/badge.svg)

```
letrec (
  # greatest common divisor of nonnegative integers
  gcd = lambda (a b) {
    if (lt b 1) then a
    else (gcd b (mod a b))
  }
) {
  (put (gcd (strint (getline)) (strint (getline))) "\n")
}
```

ExprScript is a dynamically typed functional programming language with first class continuations,
lexically / dynamically scoped variables, mark-and-sweep garbage collection,
and a built-in code evaluator `eval`.
The goals of this project are to experiment with language features
and to demonstrate the implementation of interpreters.

One design goal of ExprScript is to use a small language core
to implement/simulate other language features.

| Feature | Underlying implementation |
| --- | --- |
| Object-oriented programming ([test/oop.expr](test/oop.expr)) | Closures and dynamically scoped variables |
| Coroutines ([test/coroutines.expr](test/coroutines.expr)) | Continuations |
| Exceptions ([test/exception.expr](test/exception.expr)) | Continuations |
| Compound data types ([test/quicksort.expr](test/quicksort.expr), [test/binary-tree.expr](test/binary-tree.expr)) | Closures |
| User-defined evaluation order / lazy evaluation ([test/lazy-evaluation.expr](test/lazy-evaluation.expr), [test/y-combinator.expr](test/y-combinator.expr)) | Zero-argument functions |
| Multi-stage evaluation ([test/multi-stage.expr](test/multi-stage.expr)) | `eval` |

## dependencies

Python >= 3.9

## syntax and semantics

```
<comment> := #.*?\n
<int> := [+-]?0 | [+-]?[1-9][0-9]*
<str> := "( [-"\] | \" | \\ | \t | \n )*"
<lex-var> := [a-z][a-zA-Z]*
<dyn-var> := [A-Z][a-zA-Z]*
<var> := <lex-var> | <dyn-var>
<intrinsic> := void
             | add | sub | mul | div | mod | lt
             | strlen | strslice | strcat | strlt | strint | strquote
             | getline | put
             | callcc | type | eval | exit
<binding> := <var> = <expr>
<callee> := <intrinsic> | <expr>
<expr> := <int> | <str> | <var>
        | lambda ( <var>* ) { <expr> }
        | letrec ( <binding>* ) { <expr> }
        | if <expr> then <expr> else <expr>
        | ( <callee> <expr>* )
        | [ <expr>+ ]
```

Supported object types: Void, Integer, String, Closure, Continuation.
Functions are not curried by default.
Objects are immutable.
Variables are references to objects and are immutable once bound.
Garbage collection (GC) runs when 80% of the reserved heap space is occupied,
and if GC cannot reduce the occupancy to be < 80%, the reserved heap space will grow.
The evaluation result of the entire program is printed to `stdout`.
The full semantic reference is the interpreter ([src/interpreter.py](src/interpreter.py)).

## usage

+ `python3 src/interpreter.py <option> <file>`, where `<option>` can be
  - `run` run code in `<file>`;
  - `time` run code in `<file>` and print (to `stderr`) the execution time;
  - `space` run code in `<file>` and print (to `stderr`) the peak memory use (this option could slow down the interpreter);
  - `debug` run code in `<file>` and print (to `stderr`) the intermediate execution steps;
  - `dump-ast` print (to `stdout`) the AST of code in `<file>`;
  - `pretty-print` print (to `stdout`) the formatted version of code in `<file>`.
+ `python3 test.py` runs all tests (see [test.py](test.py) for inputs/outputs for each test program).
