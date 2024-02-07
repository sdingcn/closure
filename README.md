# cvm

![](https://github.com/sdingcn/closure/actions/workflows/auto-test.yml/badge.svg)

Closure virtual machine: an interpreter, a scheduler, and a memory manager.

## Language

```
// types: void, int, str, closure
<comment>   := #[^\n]*
<variable>  := [a-zA-Z][a-zA-Z0-9_]*
<binding>   := <variable> = <expr>
<callee>    := <intrinsic>
             | <expr>
<expr>      := <int>
             | <str>
             | <variable>
             | set <variable> <expr>
             | lambda ( <variable>* ) { <expr> }
             | letrec ( <binding>* ) { <expr> }           // pass by deepcopy
             | if <expr> then { <expr> } else { <expr> }
             | while <expr> { <expr> }
             | ( <callee> <expr>* )                       // pass by reference
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
             | .send                        // (int, int | str) -> void
             | .recv                        // (int) -> int | str | void
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
/sm <label> <expr> // send a message
/rm <label>        // receive a message
/sd                // shutdown
```

## Dependency

Python >= 3.9
