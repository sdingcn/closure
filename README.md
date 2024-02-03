# cvm

![](https://github.com/sdingcn/closure/actions/workflows/auto-test.yml/badge.svg)

Closure virtual machine: a programming language, a shell, and a virtual machine.

## Programming language

```
<lexical-variable> :=
    [a-z][a-zA-Z0-9_]*
<dynamic-variable> :=
    [A-Z][a-zA-Z0-9_]*
<variable> :=
    <lexical-variable>
  | <dynamic-variable>
<binding> :=
    <variable> = <expr>
<callee> :=
    <intrinsic>
  | <expr>
<expr> :=
    <number>
  | <string>
  | <variable>
  | lambda ( <variable>* ) { <expr> }
  | letrec ( <binding>* ) { <expr> }
  | if <expr> then <expr> else <expr>
  | ( <callee> <expr>* )
  | [ <expr>+ ]
  | @ <lexical-variable> <expr>
  | & <lexical-variable> <expr>
<def> :=
    letrec ( <binding>* )
<intrinsic> :=
    .+ | .- | .* | ./ | .% | .<
  | .slen | .ssub | .s+ | .squote | .s<
  | .n->s | .s->n
  | .n? | .s? | .c?
  | .get | .put
  | .eval
  | .exit
  | .send | .recv
```

## Shell

```
<def>          // foreground definition
/ls            // list all names defined by letrec
/co name       // examine the value of name
/dl name       // delete name
<expr>         // foreground evaluation
CTRL-D         // bring current process into background with pid = unused_rand()
/bg pid <expr> // background evaluation
/fg pid        // bring to foreground
/ki pid        // kill process
/ps            // list all background processes
/gc            // run garbage collection
/sd            // shutdown
```

## Dependency and usage

Python >= 3.9
