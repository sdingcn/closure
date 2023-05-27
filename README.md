# expr

## dependencies

Python >= 3.9

## syntax and semantics

```
<int> := [+-]?0 | [+-]?[1-9][0-9]*

<intrinsic> := + | - | * | / | % | < | void | get | put | gc | exit

<var> := [a-zA-Z]+ ; except for keywords and intrinsic function names

<expr> := <int>
        | lambda ( <var> *) { <expr> }
        | letrec ( <var> = <expr> *) { <expr> }
        | if <expr> then <expr> else <expr>
        | <var>
        | ( <intrinsic> <expr>* ) ; intrinsic call
        | ( <expr> <expr>* ) ; function call
        | [ <expr> <expr>* ] ; sequence

```

Support 3 types of objects: integer, closure, void (with only one value obtainable by calling `void`).
Objects are immutable.
Variables are bound to locations in a global store, which maps locations to objects.
Binding a variable generally creates a new location, except for binding to another variable.
Variables are immutable once bound.
Garbage collection removes store entries unreachable from the current call stack, and can only be triggered by `gc`, which returns the number of locations retrieved.
Lambdas are lexically scoped and are thus evaluated to closures.
Common data structures (e.g. lists) can be implemented using closures (see [test/quicksort.expr](test/quicksort.expr)).
The evaluation order of `letrec` bindings, calls, and sequence, is left-to-right.
`get`/`put` reads/writes one line each time where each line contains one integer.
`exit` stops the execution immediately.
The full semantic reference is the interpreter itself.

## interpreter usage

`python3 src/interpreter.py run <file>` runs the code in `<file>`.

`python3 src/interpreter.py dump-ast <file>` dumps the AST of the code in `<file>`.
