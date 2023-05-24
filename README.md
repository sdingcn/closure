# expr
Expr is a dynamically-typed, interpreted, functional, toy programming language written in Python. The main purpose of this project is to illustrate the basic implementation of interpreters.

## dependencies

The only dependency is Python. Any version of Python 3.x should work.

## syntax

```
<var> := [a-zA-Z]+ ; except for reserved keywords

<int> := [+-]?0 | [+-]?[1-9][0-9]* ;

<op> := + | - | * | / | = | < ;

<expr> := <var> | <int> | <op>
        | ( lambda ( <var> ) <expr> )
        | ( letrec ( <var> <expr> ) <expr> )
        | ( if <expr> <expr> <expr> )
        | ( call <expr> <expr> ) ;
```

The semantics should be intuitive, and the full semantic reference is the interpreter itself.

## usage

`python3 interpreter.py` reads code from `stdin` and writes the result to `stdout`.

### example

```
```
