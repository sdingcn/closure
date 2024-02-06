# cvm

![](https://github.com/sdingcn/closure/actions/workflows/auto-test.yml/badge.svg)

Closure virtual machine: a programming language, a scheduler, and a memory manager.

## Programming language

```
// types: void, int, str, closure
<variable>  := [a-zA-Z][a-zA-Z0-9_]*
<binding>   := <variable> = <expr>
<update>    := <variable> <- <expr>
<callee>    := <intrinsic>
             | <expr>
<expr>      := <int>
             | <str>
             | <variable>
             | <update>
             | lambda ( <variable>* ) { <expr> }
             | letrec ( <binding>* ) { <expr> }
             | if <expr> then <expr> else <expr>
             | while <expr> { <expr> }
             | ( <callee> <expr>* )
             | [ <expr>+ ]
             | @ <variable> <expr>
             | & <variable> <expr>
<intrinsic> := .void                        // () -> void
             | .+ | .- | .* | ./ | .% | .<  // (int, int) -> int {no currying}
             | .slen                        // (str) -> int
             | .ssub                        // (str, int, int) -> str
             | .s+                          // (str, str) -> str
             | .s<                          // (str, str) -> int
             | .i->s                        // (int) -> str
             | .s->i                        // (str) -> int
             | .v? | .i? | .s? | .c?        // (any) -> int
             | .time                        // () -> int
             | .sleep                       // (int) -> void
             | .exit                        // () -> void
             | .send                        // (label, int | str) -> void
             | .recv                        // (label) -> int | str | void
```

## Commands

```
/cn <name> <expr>  // create a new (global) name (no duplicate)
/ln                // list all defined names
/pn <name>         // examine the value of a defined name
/dn <name>         // delete a defined name
/sp <pid> <expr>   // start a (background) process
/kp <pid>          // kill a process
/lp                // list all processes (including terminated, need to be explicitly killed)
/sm <label> <expr> // send message
/rm <label>        // receive message
/sd                // shutdown
```

## Dependency and usage

Python >= 3.9
