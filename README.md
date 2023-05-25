# expr
Expr is a dynamically-typed, interpreted, functional, toy programming language with mark-and-sweep garbage collection. The main purpose of this project is to illustrate the implementation of interpreters.

## dependencies

The only dependency is Python. Any version of Python 3.x should work.

## syntax

```
<var> := [a-zA-Z]+ ; except for reserved keywords

<int> := [+-]?0 | [+-]?[1-9][0-9]* ;

<binop> := + | - | * | / | % | = | < ;

<expr> := <int>
        | <binop>
        | lambda <var> <expr>
        | letrec <var> <expr> <expr>
        | if <expr> <expr> <expr>
        | call <expr> <expr>
        | seq <expr> <expr>
        | <var> ;
```

All functions are curried one-parameter functions. The full semantic reference is the interpreter itself.

## usage

`python3 interpreter.py` reads code from `stdin` and writes the result to `stdout`.

### example

```
letrec
  gcd
    lambda a
      lambda b
        if = b 0
          a
          call call gcd b % a b
  call call gcd 8 12
```
