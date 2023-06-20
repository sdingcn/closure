# exprscript

![](https://github.com/sdingcn/expr/actions/workflows/auto-test.yml/badge.svg)

ExprScript 是一个动态类型函数式语言.
此项目有以下三个主要目标.

+ 直接支持全精度有理数计算

```
$ cat test/average.expr
letrec (
  null = lambda () { lambda () { 0 } }
  cons = lambda (head tail) { lambda () { 1 } }
  len = lambda (list) {
    if (list) then (.+ 1 (len &tail list)) else 0
  }
  sum = lambda (list) {
    if (list) then (.+ &head list (sum &tail list)) else 0
  }
) {
  letrec (
    list = (cons 100/11 (cons 61 (cons +15/7 (cons 1.355 (cons -41.06 (null))))))
  ) {
    (./ (sum list) (len list))
  }
}
$ python3 src/interpreter.py run test/average.expr
500943/77000
```

+ 利用一个小语言核心实现很多语言特性

| 特性 | 实现 |
| --- | --- |
| 面向对象编程 ([test/oop.expr](test/oop.expr)) | 闭包和动态作用域变量 |
| 协程 ([test/coroutines.expr](test/coroutines.expr)) | 续延 |
| 惰性求值 ([test/lazy-evaluation.expr](test/lazy-evaluation.expr)) | 无参函数 |
| 多阶段求值 ([test/multi-stage.expr](test/multi-stage.expr)) | `eval` |

+ 展示解释器实现

参见 ([src/interpreter.py](src/interpreter.py)).

## 依赖

Python >= 3.9

## 语法和语义

```
<comment> := #.*?\n
<head-nonzero> := [1-9][0-9]*
<tail-nonzero> := [0-9]*[1-9]
<number> := [+-]?0
          | [+-]?<head-nonzero>
          | [+-]?0.<tail-nonzero>
          | [+-]?<head-nonzero>.<tail-nonzero>
          | [+-]?0/<head-nonzero>
          | [+-]?<head-nonzero>/<head-nonzero>
<string> := "( [^"\] | \" | \\ | \t | \n )*" // charset is English keyboard
<lexical-variable> := [a-z][a-zA-Z]*         // lexically scoped variable
<dynamic-variable> := [A-Z][a-zA-Z]*         // dynamically scoped variable
<variable> := <lexical-variable> | <dynamic-variable>
<intrinsic> := .void
             | .+ | .- | .* | ./ | .% | .floor | .ceil
             | .< | .<= | .> | .>= | .== | .!=
             | .and | .or | .not             // for simplicity use numbers as Booleans
             | .strlen | .strcut | .str+ | .strnum | .strquote
             | .str< | .str<= | .str> | .str>= | .str== | .str!= 
             | .getline | .put
             | .void? | .num? | .str? | .clo? | .cont?
             | .call/cc | .eval | .exit
             | .python                       // Python FFI
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
垃圾回收在预留堆空间占用率达到 80% 时自动运行,
且如果垃圾回收无法将占用率降低到 80% 以下, 则预留堆空间会增长.
整个程序的求值结果会被写到标准输出.
完整语义请参考解释器本身 ([src/interpreter.py](src/interpreter.py)).

## 用法

+ `python3 src/interpreter.py <option> <file>`, 此处 `<option>` 可以是
  - `run` 运行 `<file>` 中的代码;
  - `time` 运行 `<file>` 中的代码且将运行时间写入标准错误;
  - `space` 运行 `<file>` 中的代码且将内存峰值写入标准错误 (此选项可能拖慢解释器速度);
  - `debug` 运行 `<file>` 中的代码且将运行的中间过程写入标准错误;
  - `ast` 将 `<file>` 中代码的抽象语法树写入标准输出;
  - `print` 将 `<file>` 中的代码格式化后写入标准输出.
+ `python3 test.py` 运行所有测试 ([test.py](test.py) 包含每个测试程序的输入/输出).
