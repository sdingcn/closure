# expr
Expr is a dynamically-typed, interpreted, functional, toy programming language with mark-and-sweep garbage collection.

## dependencies

The only dependency is Python. Any version of Python 3.x should work.

## syntax

The design goal is to make the language core as small as possible, with most features implementable as functions.

```
<var> := [a-zA-Z]+ ; except for reserved keywords and built-in names

<int> := [+-]?0 | [+-]?[1-9][0-9]*

<built-in> := + | - | * | / | % | < | void | get | put | gc | error

<var-list> := epsilon | <var> <var-list>

<var-expr-list> := epsilon | <var> = <expr> <var-expr-list>

<expr-list> := epsilon | <expr> <expr-list>

<expr> := <int>
        | <built-in>
        | lambda ( <var-list> ) { <expr> }
        | letrec ( <var-expr-list> ) { <expr> }
        | if <expr> then <expr> else <expr>
        | ( <expr> <expr-list> ) ; function call
        | [ <expr> <expr-list> ] ; sequence
        | <var>
```

There are three types of objects: closure, integer, void (with only one value obtainable by calling `void`). All objects are immutable.

All variables are pointers pointing to locations of objects in a globally-maintained resizable array. Binding a variable to another variable only copies the address. Garbage collection compress the global array and can only be triggered by calling `gc`.

All functions are closures (including built-in ones, which are closures with the empty environment).

The evaluation order of `letrec` bindings, function calls, and sequence, is left-to-right.

The full semantic reference is the interpreter itself.

## usage

`python3 interpreter.py <source>` runs the Expr code in the file `<source>`.

### example (sorting)

[quicksort.expr](quicksort.expr)
