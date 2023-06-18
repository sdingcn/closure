# exprscript

[中文 README](README-CN.md)

![](https://github.com/sdingcn/expr/actions/workflows/auto-test.yml/badge.svg)

```
letrec (
  leaf = lambda () {
    lambda () { 0 }
  }
  node = lambda (value left right) {
    lambda () { 1 }
  }
  dfs = lambda (tree) {
    if (.not (tree)) then (.void)
    else [
      (dfs &left tree)
      (.put &value tree "\n")
      (dfs &right tree)
    ]
  }
) {
  # in-order traversal
  (dfs
    (node 4
      (node 2
        (node 1 (leaf) (leaf))
        (node 3 (leaf) (leaf)))
      (node 5 (leaf) (leaf))))
}
```

ExprScript is a dynamically typed functional programming language.
It has a small language core, but can implement/simulate many other features.

| Feature | Implementation |
| --- | --- |
| Object-oriented programming ([test/oop.expr](test/oop.expr)) | Closures and dynamically scoped variables |
| Coroutines ([test/coroutines.expr](test/coroutines.expr)) | Continuations |
| Lazy evaluation ([test/lazy-evaluation.expr](test/lazy-evaluation.expr)) | Zero-argument functions |
| Multi-stage evaluation ([test/multi-stage.expr](test/multi-stage.expr)) | `eval` |

## dependencies

Python >= 3.9

## syntax and semantics

```
<comment> := #.*?\n
<integer> := [+-]?0 | [+-]?[1-9][0-9]*
<string> := "( [^"\] | \" | \\ | \t | \n )*" // charset is English keyboard
<lexical-variable> := [a-z][a-zA-Z]*         // lexically scoped variable
<dynamic-variable> := [A-Z][a-zA-Z]*         // dynamically scoped variable
<variable> := <lexical-variable> | <dynamic-variable>
<intrinsic> := .void
             | .+ | .- | .* | ./ | .^ | .%
             | .< | .<= | .> | .>= | .== | .!=
             | .and | .or | .not             // for simplicity use integers as Booleans
             | .strlen | .strcut | .str+ | .strint | .strquote
             | .str< | .str<= | .str> | .str>= | .str== | .str!= 
             | .getline | .put
             | .void? | .int? | .str? | .clo? | .cont?
             | .call/cc | .eval | .exit
             | .python                       // Python FFI
<binding> := <variable> = <expr>
<callee> := <intrinsic> | <expr>
<query-body> := <dynamic-variable>           // Is it defined here?
              | <lexical-variable> <expr>    // Is it defined in the closure's environment?
<expr> := <integer> | <string> | <variable>
        | lambda ( <variable>* ) { <expr> }
        | letrec ( <binding>* ) { <expr> }
        | if <expr> then <expr> else <expr>
        | ( <callee> <expr>* )
        | [ <expr>+ ]                        // sequence evaluation
        | @ <query-body>                     // query whether a variable is defined
        | & <lexical-variable> <expr>        // access a variable in a closure's env
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
  - `ast` print (to `stdout`) the AST of code in `<file>`;
  - `print` print (to `stdout`) the formatted version of code in `<file>`.
+ `python3 test.py` runs all tests (see [test.py](test.py) for inputs/outputs for each test program).
