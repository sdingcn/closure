# exprscript

[中文 README](README-CN.md)

![](https://github.com/sdingcn/expr/actions/workflows/auto-test.yml/badge.svg)

ExprScript is a dynamically typed functional programming language.

+ Directly support full-precision rational number computations

```
$ cat test/average.expr
letrec (
  # It's easy to implement your own data structures.
  null = lambda () { lambda () { 0 } }
  cons = lambda (head tail) { lambda () { 1 } }
  len = lambda (list) { if (list) then (.+ 1 (len &tail list)) else 0 }
  sum = lambda (list) { if (list) then (.+ &head list (sum &tail list)) else 0 }
) {
  letrec (
    list = (cons 100/11 (cons 61 (cons +15/7 (cons 1.355 (cons -41.06 (null))))))
  ) {
    (./ (sum list) (len list))
  }
}
$ python3 src/interpreter.py run test/average.expr
500943/77000
```

+ Use a small language core to implement many language features

| Feature | Implementation |
| --- | --- |
| Object-oriented programming ([test/oop.expr](test/oop.expr)) | Closures and dynamically scoped variables |
| Coroutines ([test/coroutines.expr](test/coroutines.expr)) | Continuations |
| Lazy evaluation ([test/lazy-evaluation.expr](test/lazy-evaluation.expr)) | Zero-argument functions |
| Multi-stage evaluation ([test/multi-stage.expr](test/multi-stage.expr)) | `eval` |

+ Demonstrate the implementation of a simple interpreter

See ([src/interpreter.py](src/interpreter.py)).

## dependencies

Python >= 3.9

## syntax and semantics

```
<comment> := #.*?\n
<head-nonzero> := [1-9][0-9]*
<tail-nonzero> := [0-9]*[1-9]
<number> := [+-]?0
          | [+-]?<head-nonzero>
          | [+-]?0.<tail-nonzero>
          | [+-]?<head-nonzero>.<tail-nonzero>
          | [+-]?0/<head-nonzero>
          | [+-]?<head-nonzero>/<head-nonzero>
<string> := "( [^"\] | \" | \\ | \t | \n )*" // charset is English keyboard
<lexical-variable> := [a-z][a-zA-Z0-9_]*         // lexically scoped variable
<dynamic-variable> := [A-Z][a-zA-Z0-9_]*         // dynamically scoped variable
<variable> := <lexical-variable> | <dynamic-variable>
<intrinsic> := .void
             | .+ | .- | .* | ./ | .% | .floor | .ceil
             | .< | .<= | .> | .>= | .== | .!=
             | .and | .or | .not             // for simplicity use numbers as Booleans
             | .strlen | .strcut | .str+ | .strnum | .strquote
             | .str< | .str<= | .str> | .str>= | .str== | .str!= 
             | .getline | .put
             | .void? | .num? | .str? | .clo? | .cont?
             | .call/cc | .eval | .exit
             | .py                           // Python FFI
<binding> := <variable> = <expr>
<callee> := <intrinsic> | <expr>
<query-body> := <dynamic-variable>           // Is it defined here?
              | <lexical-variable> <expr>    // Is it defined in the closure's environment?
<expr> := <number> | <string> | <variable>
        | lambda ( <variable>* ) { <expr> }
        | letrec ( <binding>* ) { <expr> }
        | if <expr> then <expr> else <expr>
        | ( <callee> <expr>* )
        | [ <expr>+ ]                        // sequence evaluation
        | @ <query-body>                     // query whether a variable is defined
        | & <lexical-variable> <expr>        // access a variable in a closure's env
```

Supported object types: Void, Number, String, Closure, Continuation.
Functions are not curried by default.
Objects are immutable.
Variables are references to objects and are immutable once bound.
Garbage collection (GC) runs when 80% of the reserved heap space is occupied,
and if GC cannot reduce the occupancy to be < 80%, the reserved heap space will grow.
The evaluation result of the entire program is printed to `stdout`.

## usage

+ `python3 src/interpreter.py <file>` runs code in `<file>`.
+ `python3 test.py` runs all tests (see [test.py](test.py) for inputs/outputs for each test program).
