# expr

Expr is a simple, dynamically typed, functional programming language with first class continuations.
It also features lexically scoped variables and dynamically scoped variables, dynamic type checking, as well as automatic mark-and-sweep garbage collection.
The main purpose of this project is to demonstrates the implementation of simple interpreters.

![](https://github.com/sdingcn/expr/actions/workflows/auto-test.yml/badge.svg)

## dependencies

Python >= 3.9

## example (GCD for nonnegative integers)

```
letrec (
  gcd = lambda (a b) {
    if (lt b 1) then a
    else (gcd b (mod a b))
  }
) {
  (put
    (gcd (strint (getline)) (strint (getline)))
    "\n"
  )
}
```

For more examples, see `test/`.

## syntax and semantics

```
<int> := [+-]?0 | [+-]?[1-9][0-9]*
<str> := <Python-double-quote-str-literal>
<var> := [a-z][a-zA-Z]* // lexically scoped variable
       | [A-Z][a-zA-Z]* // dynamically scoped variable
<intrinsic> := void     // () -> Void; returns void (the only value of type Void)
             | add      // (Integer, Integer) -> Integer
             | sub      // (Integer, Integer) -> Integer
             | mul      // (Integer, Integer) -> Integer
             | div      // (Integer, Integer) -> Integer
             | mod      // (Integer, Integer) -> Integer
             | lt       // (Integer, Integer) -> Integer; (a < b) ? 1 : 0
             | strlen   // (String) -> Integer
             | strslice // (String, Integer, Integer) -> String; s[a ... b - 1]
             | strcat   // (String, String) -> String; string concatenation
             | strlt    // (String, String) -> Integer; (s1 lexicograhically < s2) ? 1 : 0
             | strint   // (String) -> Integer; string to integer
             | getline  // () -> String; read a line from stdin (discard '\n')
             | put      // ((Integer | String)+) -> Void; write to stdout, no separator, no auto '\n'
             | callcc   // (Closure) -> Any
             | type     // (Any) -> Integer; Void -> 0 Integer -> 1 String -> 2 Closure -> 3 Continuation -> 4
             | exit     // () ->; stop the interpreter (the interpreter's return value is 0)
<binding> := <var> = <expr>
<callee> := <intrinsic> | <expr>
<expr> := <int>
       | <str>
       | lambda ( <var>* ) { <expr> }
       | letrec ( <binding>* ) { <expr> }  // left-to-right evaluation
       | if <expr> then <expr> else <expr> // condition must be an integer; 0 is false, others are true
       | <var>                             // cannot hold intrinsic functions
       | ( <callee> <expr>* )              // intrinsic / closure / continuation call
       | [ <expr>+ ]                       // left-to-right evaluation, return the last result
```

Supported types: Void, Integer, String, Closure, Continuation.
Lambdas are not curried.
Data structures (e.g. lists) can be implemented using closures (see `test/`).
Objects are immutable.
Variables are references to objects and are immutable once bound.
Garbage collection (GC) runs when 80% of the reserved heap space is occupied,
and if GC cannot reduce the occupancy to be smaller than 80%, the reserved heap space will grow.

## usage

+ `python3 src/interpreter.py <option> <file>`, where `<option>` can be one of the following choices.
  - `run`: Run code in `<file>`.
  - `time`: Run code in `<file>` and print (to `stderr`) execution time.
  - `space`: Run code in `<file>` and print (to `stderr`) peak memory use (may slow down the interpreter).
  - `debug`: Run code in `<file>` and print (to `stderr`) the interpreter's intermediate steps.
  - `dump-ast`: Dump AST of code in `<file>`.
+ `python3 test.py` runs all tests (see `test.py` for inputs/outputs for each test program).
