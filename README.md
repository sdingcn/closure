# closure

![](https://github.com/sdingcn/closure/actions/workflows/auto-test.yml/badge.svg)

This is a small functional programming language with first-class functions,
recursions, and mark-and-sweep garbage collection with memory compaction.

## code example

```
letrec (
    leaf lambda () lambda () 0
    node lambda (value left right) lambda () 1
    # in-order DFS
    dfs lambda (tree)
        if (.< (tree) 1)
        (.void)
        {
            (dfs @left tree)
            (.put @value tree)
            (dfs @right tree)
        }
)
(dfs
    (node 4
        (node 2
            (node 1 (leaf) (leaf))
            (node 3 (leaf) (leaf)))
        (node 5 (leaf) (leaf))))
```

## syntax

```
<comment>   := #[^\n]*\n
<integer>   := [+-]?[0-9]+
<variable>  := [a-zA-Z_][a-zA-Z0-9_]*
<intrinsic> := .void
             | .+ | .- | .* | ./ | .% | .<
             | .type  // returns an integer representation (see below) of the object's type
                      // an object's type never changes during its lifetime
             | .get | .put  // gets an integer / puts an integer with a newline
<vepair>    := <variable> <expr>

<expr> := <integer>
        | <variable>
        | lambda ( <variable>* ) <expr>
        | letrec ( <vepair>* ) <expr>
        | if <expr> <expr> <expr>
        | { <expr>+ }  // sequenced evaluation
        | ( <intrinsic> <expr>* )
        | ( <expr> <expr>* )
        | @ <variable> <expr>  // access a closure's environment variable
```

## semantics and implementation details

+ Reference semantics (unobservable):
  variables are references to objects;
  expressions evaluate to references of objects;
  both `letrec` and `( <callee> <expr>* )` use pass-by-reference.
+ Three object types, all immutable: Void (0), Int (1), Closure (2).
  Closures can be used as records / structs as shown in the above example.
+ Variables cannot be re-bound.
+ The evaluation order of `lambda` and `letrec` is left-to-right.
+ Simple periodic garbage collection with memory compaction.
+ No tail-call optimization.
+ The language's stacks and heaps are explicit in the implementation,
  so it should be easy to support debugging, exceptions, continuations, threads, coroutines, etc.

## dependencies

+ `cmake` >= 3.28.1
+ a reasonable version of `make`
+ `clang++` with support of C++20
+ `python3`

## build (on Linux/macOS)

```
mkdir build
cmake -DCMAKE_BUILD_TYPE:STRING=Debug \
      -DCMAKE_CXX_COMPILER:FILEPATH=$(which clang++) \
      -S src -B build \
      -G "Unix Makefiles"
cd build
make
```

## run

```
build/closure <source-path>
```

To run all tests, do `python3 run_test.py`.
