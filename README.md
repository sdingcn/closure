# exprscript

![](https://github.com/sdingcn/expr/actions/workflows/auto-test.yml/badge.svg)

ExprScript 是一个动态类型函数式语言.
(ExprScript is a dynamically typed functional programming language.)

#### 小核心, 丰富表达力 (Small core, rich expressiveness)

| Feature | Implementation |
| --- | --- |
| Structures / Records ([test/binary-tree.expr](test/binary-tree.expr)) | Closures |
| Object-oriented programming ([test/oop.expr](test/oop.expr)) | Closures and dynamically scoped variables |
| Coroutines ([test/coroutines.expr](test/coroutines.expr)) | Continuations |
| Lazy evaluation ([test/lazy-evaluation.expr](test/lazy-evaluation.expr)) | Zero-argument functions |
| Multi-stage evaluation ([test/multi-stage.expr](test/multi-stage.expr)) | `eval` |

#### 支持全精度有理数 (Support full-precision rational numbers)

[test/average.expr](test/average.expr)

#### 与 Python 的交互 (Interactions with Python)

[src/interaction-examples.py](src/interaction-examples.py)

## 依赖 (dependencies)

Python >= 3.9

## 语法和语义 (syntax and semantics)

```
<comment> := #.*\n
<number> := [+-]?0 | [+-]?[1-9][0-9]*
          | [+-]?0\.[0-9]*[1-9] | [+-]?[1-9][0-9]*\.[0-9]*[1-9]
          | [+-]?0/[1-9][0-9]* | [+-]?[1-9][0-9]*/[1-9][0-9]*
<string> := "( [^"\] | \" | \\ | \t | \n )*"     // charset is English keyboard
<lexical-variable> := [a-z][a-zA-Z0-9_]*         // lexically scoped variable
<dynamic-variable> := [A-Z][a-zA-Z0-9_]*         // dynamically scoped variable
<variable> := <lexical-variable> | <dynamic-variable>
<intrinsic> := .void
             | .+ | .- | .* | ./ | .% | .floor | .ceil
             | .< | .<= | .> | .>= | .== | .!=
             | .and | .or | .not             // for simplicity use numbers as Booleans
             | .strlen | .strcut | .str+ | .strnum | .strquote
             | .str< | .str<= | .str> | .str>= | .str== | .str!= 
             | .void? | .num? | .str? | .clo? | .cont?
             | .getline | .put | .call/cc | .eval | .exit | .py | .reg
<binding> := <variable> = <expr>
<callee> := <intrinsic> | <expr>
<query-body> := <dynamic-variable>           // Is it defined here?
              | <lexical-variable> <expr>    // Is it defined in the closure's environment?
<expr> := <number> | <string> | <variable>
        | lambda ( <variable>* ) { <expr> }
        | letrec ( <binding>* ) { <expr> }
        | if <expr> then <expr> else <expr>
        | ( <callee> <expr>* )
        | [ <expr>+ ]                        // sequence evaluation
        | @ <query-body>                     // query whether a variable is defined
        | & <lexical-variable> <expr>        // access a variable in a closure's env
```

支持的对象类型: Void, Number, String, Closure, Continuation.
函数默认不柯里化.
对象不可变.
变量是指向对象的引用且一旦绑定就不可变.
支持尾调用优化和垃圾回收.
一些运行时信息会被写到标准错误.
(Supported object types: Void, Number, String, Closure, Continuation.
Functions are not curried by default.
Objects are immutable.
Variables are references to objects and are immutable once bound.
Tail call optimization and garbage collection are supported.
Some runtime information will be written to `stderr`.)

## 用法 (usage)

```
python3 src/exprscript.py <file>
python3 test.py
```
