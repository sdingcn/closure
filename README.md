# expr
Expr is a dynamically-typed, interpreted, functional, toy programming language with mark-and-sweep garbage collection.

## dependencies

The only dependency is Python. Any version of Python 3.x should work.

## syntax

```
<var> := [a-zA-Z]+ ; except for reserved keywords

<int> := [+-]?0 | [+-]?[1-9][0-9]*

<built-in> := + | - | * | / | % | == | < | get | put | error

<var-list> := epsilon | <var> <var-list>

<var-expr-list> := epsilon | <var> = <expr> <var-expr-list>

<expr-list> := epsilon | <expr> <expr-list>

<expr> := <int>
        | lambda ( <var-list> ) { <expr> }
        | letrec ( <var-expr-list> ) { <expr> }
        | if <expr> then <expr> else <expr>
        | [ <expr> <expr-list> ] ; function call
        | <built-in>
        | <var>
```

There are two types of objects: closure, integer.

All variables are pointers pointing to locations of objects in a globally-maintained resizable array. Garbage collection compress this array and is triggered for every 100 function returns.

All functions are closures (including built-in ones, which are closures with the empty environment).

The evaluation order of function arguemnts is left-to-right.

You can implement lists using closures (illustrated below in the example).

The full semantic reference is the interpreter itself.

## usage

`python3 interpreter.py` reads code from `stdin` and writes the result to `stdout`.

### example 1 (gcd)

### example 2 (sequence)

### example 3 (list and sorting)

```
letrec (
  null = lambda (x) {
    if [== x 0] then 1 else [error]
  }
  cons = lambda (head tail) {
    letrec (
      h = head
      t = tail
    ) {
      lambda (x) {
        if [== x 0] then 0
        else if [== x 1] then h
        else if [== x 2] then t
        else [error]
      }
    }
  }
  isnull = lambda (list) {
    [list 0]
  }
  car = lambda (list) {
    [list 1]
  }
  cdr = lambda (list) {
    [list 2]
  }
) {
}
```
