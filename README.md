# expr

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

Expr is a simple, dynamically typed, functional programming language with first class continuations.
It also features lexically / dynamically scoped variables, mark-and-sweep garbage collection, and a built-in code evaluator `eval`.
The goals of this project are to experiment with language features and to demonstrate the implementation of interpreters.

Object-oriented programming ([test/oop.expr](test/oop.expr))
can be implemented using closures and dynamically scoped variables.
Coroutines ([test/coroutines.expr](test/coroutines.expr)) and exceptions ([test/exception.expr](test/exception.expr))
can be implemented using continuations.
Data structures such as lists ([test/quicksort.expr](test/quicksort.expr)) and binary trees ([test/binary-tree.expr](test/binary-tree.expr))
can be implemented using closures.
See [test/](test/) for more examples.

## dependencies

Python >= 3.9

## syntax and semantics

```
<one-line-comment> := #.*?\n
<int> := [+-]?0 | [+-]?[1-9][0-9]*
<str> := <Python-double-quote-str-literal>
<var> := [a-z][a-zA-Z]* // lexically scoped variable
       | [A-Z][a-zA-Z]* // dynamically scoped variable
<intrinsic> := void     // () -> Void; returns void (the only value of type Void)
             | add | sub | mul | div | mod  // (Integer, Integer) -> Integer; arithmetic
             | lt       // (Integer, Integer) -> Integer; (a < b) ? 1 : 0
             | strlen   // (String) -> Integer
             | strslice // (String, Integer, Integer) -> String; s[a ... b - 1]
             | strcat   // (String, String) -> String; concatenation
             | strlt    // (String, String) -> Integer; (s1 lexicograhically < s2) ? 1 : 0
             | strint   // (String) -> Integer; conversion
             | getline  // () -> String; read a line from stdin (discard '\n')
             | put      // ((Integer | String)+) -> Void; write to stdout, no separator, no '\n' end
             | callcc   // (Closure) -> Any
             | type     // (Any) -> Integer; Void:0 Integer:1 String:2 Closure:3 Continuation:4
             | eval     // (String) -> Any; evaluate code in a new interpreter instance
             | exit     // () ->; stop the interpreter (the interpreter's return value is 0)
<binding> := <var> = <expr>
<callee> := <intrinsic> | <expr>
<expr> := <int> | <str> | <var>
        | lambda ( <var>* ) { <expr> }
        | letrec ( <binding>* ) { <expr> }  // mutually recursive variable bindings (left-to-right evaluation)
        | if <expr> then <expr> else <expr> // condition must be an integer; 0 is false, others are true
        | ( <callee> <expr>* )              // intrinsic / closure / continuation call
        | [ <expr>+ ]                       // left-to-right evaluation, return the last result
```

Supported object types: Void, Integer, String, Closure, Continuation.
Lambdas are not curried.
Objects are immutable.
Variables are references to objects and are immutable once bound.
Garbage collection (GC) runs when 80% of the reserved heap space is occupied,
and if GC cannot reduce the occupancy to be < 80%, the reserved heap space will grow.
The evaluation result of the entire program is printed to `stdout`.

## usage

+ `python3 src/interpreter.py <option> <file>`, where `<option>` can be
  - `run` run code in `<file>`;
  - `time` run code in `<file>` and print (to `stderr`) execution time;
  - `space` run code in `<file>` and print (to `stderr`) peak memory use (this could slow down the interpreter);
  - `debug` run code in `<file>` and print (to `stderr`) intermediate evaluation steps;
  - `dump-ast` print (to `stdout`) the AST of code in `<file>`.
+ `python3 test.py` runs all tests (see `test.py` for inputs/outputs for each test program).
