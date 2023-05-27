# expr

## dependencies

Python >= 3.9

## syntax

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
Garbage collection removes store entries unreachable from the current call stack, and can only be triggered by `gc`.
Lambdas are lexically scoped and are thus evaluated to closures.
Common data structures (e.g. lists) can be implemented using closures (see `test/quicksort.expr`).
The evaluation order of `letrec` bindings, calls, and sequence, is left-to-right.
The full semantic reference is the interpreter itself.

## usage

`python3 interpreter.py <file>` runs code in `<file>`.
