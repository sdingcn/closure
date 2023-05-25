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

`python3 interpreter.py` reads code from `stdin` and writes the result to `stdout`.

### example (sorting)

```
letrec (
  eq = lambda (a b) {
    if (< (+ (< a b) (< b a)) 1) then 1 else 0
  }
  leq = lambda (a b) {
    if (< b a) then 0 else 1
  }
  gt = lambda (a b) {
    if (leq a b) then 0 else 1
  }
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
  len = lambda (list) {
    if (isnull list) then 0
    else (+ 1 (len (cdr list)))
  }
  getlist = lambda (n) {
    if (== n 0) then (null)
    else (cons (get) (getlist (- n 1)))
  }
  putlist = lambda (list) {
    if (isnull list) then (void)
    else [(put (car list)) (putlist (cdr list))]
  }
  filterleq = lambda (v list) {
    if (isnull list) then (null)
    else letrec (
      head = (car list)
      tail = (cdr list)
    ) {
      if (leq head v) then (cons head (filterleq v tail))
      else (filterleq v tail)
    }
  }
  filtergt = lambda (v list) {
    if (isnull list) then (null)
    else letrec (
      head = (car list)
      tail = (cdr list)
    ) {
      if (gt head v) then (cons head (filtergt v tail))
      else (filtergt v tail)
    }
  }
  concat = lambda (list1 list2) {
    if (isnull list1) then list2
    else letrec (
      head = (car list1)
      tail = (cdr list1)
    ) {
      (cons head (concat tail list2))
    }
  }
  quicksort = lambda (list) {
    if (isnull list) then (null)
    else letrec (
      head = (car list)
      tail = (cdr list)
      left = (filterleq head tail)
      right = (filtergt head tail)
    ) {
      (concat left (concat (cons head (null)) right))
    }
  }
) {
  letrec (
    n = (get)
  ) {
    (putlist (quicksort (getlist n)))
  }
}
```
