# expr
Expr is a dynamically-typed, interpreted, functional, toy programming language with mark-and-sweep garbage collection.

## dependencies

The only dependency is Python. Any version of Python 3.x should work.

## syntax

```
<var> := [a-zA-Z]+ ; except for reserved keywords

<int> := [+-]?0 | [+-]?[1-9][0-9]*

<built-in> := + | - | * | / | % | == | < | void | get | put | gc | error

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

There are two types of objects: closure, integer. All objects are immutable.

All variables are pointers pointing to locations of objects in a globally-maintained resizable array. Binding a variable to another variable only copies the address. Garbage collection compress this array and can only be triggered by the call to `gc`.

All functions are closures (including built-in ones, which are closures with the empty environment).

The evaluation order of `letrec` bindings, function calls, and sequence, is left-to-right.

You can implement lists using closures (illustrated below in the example).

The full semantic reference is the interpreter itself.

## usage

`python3 interpreter.py` reads code from `stdin` and writes the result to `stdout`.

### example (sorting)

```
letrec (
  null = lambda () {
    lambda (x) {
      if (== x 0) then 1 else (error)
    }
  }
  cons = lambda (head tail) {
    letrec (
      h = head
      t = tail
    ) {
      lambda (x) {
        if (== x 0) then 0
        else if (== x 1) then h
        else if (== x 2) then t
        else (error)
      }
    }
  }
  isnull = lambda (list) {
    (list 0)
  }
  car = lambda (list) {
    (list 1)
  }
  cdr = lambda (list) {
    (list 2)
  }
  getlist = lambda (n) {
    if (== n 0) then (null)
    else (cons (get) (getlist (- n 1)))
  }
  putlist = lambda (list) {
    if (isnull list) then (void)
    else [(put (car list)) (putlist (cdr list))]
  }
) {
}
```
