# exprscript

![](https://github.com/sdingcn/expr/actions/workflows/auto-test.yml/badge.svg)

```
letrec (
  # greatest common divisor of nonnegative integers
  gcd = lambda (a b) {
    if (lt b 1) then a
    else (gcd b (mod a b))
  }
) {
  (put (gcd (strint (getline)) (strint (getline))) "\n")
}
```

ExprScript 是一个动态类型函数式语言, 支持一等续延.
其它特性包括词法/动态作用域变量, 标记-扫描式垃圾回收,
和内置代码执行器 `eval`.
本项目的目标是试验语言特性和示意解释器的实现.

ExprScript 的一个设计目标是用一个小语言核心
来实现/模拟很多语言特性.
面向对象编程 ([test/oop.expr](test/oop.expr))
可以用闭包和动态作用域变量模拟.
协程 ([test/coroutines.expr](test/coroutines.expr))
和异常 ([test/exception.expr](test/exception.expr))
可以用续延模拟.
数据结构如链表 ([test/quicksort.expr](test/quicksort.expr))
和二叉树 ([test/binary-tree.expr](test/binary-tree.expr))
可以用闭包模拟.
自定义求值顺序/惰性求值 ([test/lazy-evaluation.expr](test/lazy-evaluation.expr))
和 Y 组合子 ([test/y-combinator.expr](test/y-combinator.expr))
可以用 lambda 函数模拟.
[test/](test/) 包含更多例子.

## 依赖

Python >= 3.9

## 语法和语义

```
<comment> := #.*?\n
<int> := [+-]?0 | [+-]?[1-9][0-9]*
<str> := <Python-double-quote-str-literal>
<lex-var> := [a-z][a-zA-Z]*
<dyn-var> := [A-Z][a-zA-Z]*
<var> := <lex-var> | <dyn-var>
<intrinsic> := void
             | add | sub | mul | div | mod | lt
             | strlen | strslice | strcat | strlt | strint
             | getline | put
             | callcc | type | eval | exit
<binding> := <var> = <expr>
<callee> := <intrinsic> | <expr>
<expr> := <int> | <str> | <var>
        | lambda ( <var>* ) { <expr> }
        | letrec ( <binding>* ) { <expr> }
        | if <expr> then <expr> else <expr>
        | ( <callee> <expr>* )
        | [ <expr>+ ]
```

支持的对象类型: Void, Integer, String, Closure, Continuation.
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
  - `dump-ast` 将 `<file>` 中代码的抽象语法树写入标准输出.
+ `python3 test.py` 运行所有测试 ([test.py](test.py) 包含每个测试程序的输入/输出).
