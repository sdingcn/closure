#include <algorithm>
#include <cctype>
#include <concepts>
#include <cstddef>
#include <cstdlib>
#include <deque>
#include <filesystem>
#include <fstream>
#include <functional>
#include <iostream>
#include <memory>
#include <optional>
#include <stdexcept>
#include <string>
#include <type_traits>
#include <unordered_map>
#include <unordered_set>
#include <utility>
#include <variant>
#include <vector>

// ------------------------------
// global helper(s)
// ------------------------------

template <typename Type, typename Variant>
struct isAlternativeOfHelper {
    static constexpr bool value = false;
};

template <typename Type, typename... Alternative>
requires ((0 + ... + (std::same_as<Type, Alternative> ? 1 : 0)) == 1)
struct isAlternativeOfHelper<Type, std::variant<Alternative...>> {
    static constexpr bool value = true;
};

template <typename Type, typename Variant>
constexpr bool isAlternativeOf = isAlternativeOfHelper<Type, Variant>::value;

struct SourceLocation {
    SourceLocation(int l = 1, int c = 1): line(l), column(c) {}
    std::string toString() const {
        if (line <= 0 || column <= 0) {
            return "(SourceLocation N/A)";
        }
        return "(SourceLocation " + std::to_string(line) + " " + std::to_string(column) + ")";
    }
    void revert() {
        line = 1;
        column = 1;
    }
    void update(char c) {
        if (c == '\n') {
            line++;
            column = 1;
        } else {
            column++;
        }
    }

    int line;
    int column;
};

void panic(
    const std::string &type,
    const std::string &msg,
    const SourceLocation &sl = SourceLocation(0, 0)
) {
    throw std::runtime_error("[" + type + " error " + sl.toString() + "] " + msg);
}

// ------------------------------
// lexer
// ------------------------------

struct SourceStream {
    SourceStream(std::string s): source(std::move(s)) {
        std::string charstr =
            "_abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
            "+-0123456789.*/%<(){}@# \t\n";
        std::unordered_set<char> charset(charstr.begin(), charstr.end());
        for (char c : source) {
            if (!charset.contains(c)) {
                panic("lexer", "unsupported character", sl);
            }
            sl.update(c);
        }
        sl.revert();
        std::reverse(source.begin(), source.end());
    }
    bool hasNext() const {
        return source.size() > 0;
    }
    char peekNext() const {
        return source.back();
    }
    char popNext() {
        char c = source.back();
        source.pop_back();
        sl.update(c);
        return c;
    }
    SourceLocation getNextSourceLocation() const {
        return sl;
    }

    std::string source;
    SourceLocation sl;
};

struct Token {
    Token(SourceLocation s, std::string t) : sl(s), text(std::move(t)) {}

    SourceLocation sl;
    std::string text;
};

std::deque<Token> lex(std::string source) {
    SourceStream ss(std::move(source));

    std::function<std::optional<Token>()> nextToken =
        [&ss, &nextToken]() -> std::optional<Token> {
        // skip whitespaces
        while (ss.hasNext() && std::isspace(ss.peekNext())) {
            ss.popNext();
        }
        if (!ss.hasNext()) {
            return std::nullopt;
        }
        // read the next token
        auto startsl = ss.getNextSourceLocation();
        std::string text = "";
        // integer literal
        if (std::isdigit(ss.peekNext()) || ss.peekNext() == '-' || ss.peekNext() == '+') {
            if (ss.peekNext() == '-' || ss.peekNext() == '+') {
                text += ss.popNext();
            }
            while (ss.hasNext() && std::isdigit(ss.peekNext())) {
                text += ss.popNext();
            }
        // variable / keyword
        } else if (std::isalpha(ss.peekNext()) || ss.peekNext() == '_') {
            while (
                ss.hasNext() && (
                    std::isalpha(ss.peekNext()) ||
                    std::isdigit(ss.peekNext()) ||
                    ss.peekNext() == '_'
                )
            ) {
               text += ss.popNext();
            }
        // intrinsic
        } else if (ss.peekNext() == '.') {
            while (ss.hasNext() && !(std::isspace(ss.peekNext()) || ss.peekNext() == ')')) {
                text += ss.popNext();
            }
        // special symbol
        } else if (std::string("(){}@").find(ss.peekNext()) != std::string::npos) {
            text += ss.popNext();
        // comment
        } else if (ss.peekNext() == '#') {
            while (ss.hasNext() && ss.peekNext() != '\n') {
                ss.popNext();
            }
            // nextToken() will consume the \n and recursively continue
            return nextToken();
        } else {
            panic("lexer", "unsupported starting character", startsl);
        }
        return Token(startsl, std::move(text));
    };

    std::deque<Token> tokens;
    while (true) {
        auto ret = nextToken();
        if (ret.has_value()) {
            tokens.push_back(ret.value());
        } else {
            break;
        }
    }
    return tokens;
}

// ------------------------------
// AST and parser
// ------------------------------

#define COPY_CONTROL(CLASS)\
    virtual ~CLASS() {}\
    CLASS(const CLASS &) = delete;\
    CLASS &operator=(const CLASS &) = delete

struct ExprNode { COPY_CONTROL(ExprNode);
    ExprNode(SourceLocation s): sl(s) {}
    virtual std::string toString() const {
        return "<ExprNode>";
    }

    SourceLocation sl;
};

struct IntegerNode : public ExprNode { COPY_CONTROL(IntegerNode);
    IntegerNode(SourceLocation s, int v): ExprNode(s), val(v) {}
    virtual std::string toString() const override {
        return std::to_string(val);
    }

    int val;
};

struct VariableNode : public ExprNode { COPY_CONTROL(VariableNode);
    VariableNode(SourceLocation s, std::string n):
        ExprNode(s), name(std::move(n)) {}
    virtual std::string toString() const override {
        return name;
    }

    std::string name;
};

struct LambdaNode : public ExprNode { COPY_CONTROL(LambdaNode);
    LambdaNode(SourceLocation s,
        std::vector<std::unique_ptr<VariableNode>> v,
        std::unique_ptr<ExprNode> e
    ): ExprNode(s), varList(std::move(v)), expr(std::move(e)) {}
    virtual std::string toString() const override {
        std::string ret = "lambda (";
        for (const auto &v : varList) {
            ret += v->toString();
            ret += " ";
        }
        if (ret.back() == ' ') {
            ret.pop_back();
        }
        ret += ") ";
        ret += expr->toString();
        return ret;
    }

    std::vector<std::unique_ptr<VariableNode>> varList;
    std::unique_ptr<ExprNode> expr;
};

struct LetrecNode : public ExprNode { COPY_CONTROL(LetrecNode);
    LetrecNode(
        SourceLocation s,
        std::vector<std::pair<std::unique_ptr<VariableNode>, std::unique_ptr<ExprNode>>> v,
        std::unique_ptr<ExprNode> e
    ): ExprNode(s), varExprList(std::move(v)), expr(std::move(e)) {}
    virtual std::string toString() const override {
        std::string ret = "letrec (";
        for (const auto &p : varExprList) {
            ret += p.first->toString();
            ret += " ";
            ret += p.second->toString();
            ret += " ";
        }
        if (ret.back() == ' ') {
            ret.pop_back();
        }
        ret += ") ";
        ret += expr->toString();
        return ret;
    }
    
    std::vector<std::pair<std::unique_ptr<VariableNode>, std::unique_ptr<ExprNode>>> varExprList;
    std::unique_ptr<ExprNode> expr;
};

struct IfNode : public ExprNode { COPY_CONTROL(IfNode);
    IfNode(
        SourceLocation s,
        std::unique_ptr<ExprNode> c,
        std::unique_ptr<ExprNode> b1,
        std::unique_ptr<ExprNode> b2
    ): ExprNode(s), cond(std::move(c)), branch1(std::move(b1)), branch2(std::move(b2)) {}
    virtual std::string toString() const override {
        return "if " + cond->toString() + " " + branch1->toString() + " " + branch2->toString();
    }

    std::unique_ptr<ExprNode> cond;
    std::unique_ptr<ExprNode> branch1;
    std::unique_ptr<ExprNode> branch2;
};

struct SequenceNode : public ExprNode { COPY_CONTROL(SequenceNode);
    SequenceNode(
        SourceLocation s,
        std::vector<std::unique_ptr<ExprNode>> e
    ): ExprNode(s), exprList(std::move(e)) {}
    virtual std::string toString() const override {
        std::string ret = "{";
        for (const auto &e : exprList) {
            ret += e->toString();
            ret += " ";
        }
        if (ret.back() == ' ') {
            ret.pop_back();
        }
        ret += "}";
        return ret;
    }

    std::vector<std::unique_ptr<ExprNode>> exprList;
};

struct IntrinsicCallNode : public ExprNode { COPY_CONTROL(IntrinsicCallNode);
    IntrinsicCallNode(
        SourceLocation s,
        std::string i,
        std::vector<std::unique_ptr<ExprNode>> a
    ): ExprNode(s), intrinsic(std::move(i)), argList(std::move(a)) {}
    virtual std::string toString() const override {
        std::string ret = "(" + intrinsic;
        for (const auto &a : argList) {
            ret += " ";
            ret += a->toString();
        }
        ret += ")";
        return ret;
    }

    std::string intrinsic;
    std::vector<std::unique_ptr<ExprNode>> argList;
};

struct ExprCallNode : public ExprNode { COPY_CONTROL(ExprCallNode);
    ExprCallNode(
        SourceLocation s,
        std::unique_ptr<ExprNode> e,
        std::vector<std::unique_ptr<ExprNode>> a
    ): ExprNode(s), expr(std::move(e)), argList(std::move(a)) {}
    virtual std::string toString() const override {
        std::string ret = "(" + expr->toString();
        for (const auto &a : argList) {
            ret += " ";
            ret += a->toString();
        }
        ret += ")";
        return ret;
    }

    std::unique_ptr<ExprNode> expr;
    std::vector<std::unique_ptr<ExprNode>> argList;
};

struct AtNode : public ExprNode { COPY_CONTROL(AtNode);
    AtNode(
        SourceLocation s,
        std::unique_ptr<VariableNode> v,
        std::unique_ptr<ExprNode> e
    ): ExprNode(s), var(std::move(v)), expr(std::move(e)) {}
    virtual std::string toString() const override {
        return "@ " + var->toString() + " " + expr->toString();
    }

    std::unique_ptr<VariableNode> var;
    std::unique_ptr<ExprNode> expr;
};

#undef COPY_CONTROL

std::unique_ptr<ExprNode> parse(std::deque<Token> tokens) {
    auto isIntegerToken = [](const Token &token) {
        return token.text.size() > 0 && (
            std::isdigit(token.text[0]) ||
            token.text[0] == '-' ||
            token.text[0] == '+'
        );
    };
    auto isIntrinsicToken = [](const Token &token) {
        return token.text.size() > 0 && token.text[0] == '.';
    };
    auto isVariableToken = [](const Token &token) {
        return token.text.size() > 0 && (std::isalpha(token.text[0]) || token.text[0] == '_');
    };
    auto isTheToken = [](const std::string &s) {
        return [s](const Token &token) {
            return token.text == s;
        };
    };
    auto consume = [&tokens]<typename Callable>(const Callable &predicate) -> Token {
        if (tokens.size() == 0) {
            panic("parser", "incomplete token stream");
        }
        auto token = tokens.front();
        tokens.pop_front();
        if (!predicate(token)) {
            panic("parser", "unexpected token", token.sl);
        }
        return token;
    };

    std::function<std::unique_ptr<IntegerNode>()> parseInteger;
    std::function<std::unique_ptr<VariableNode>()> parseVariable;
    std::function<std::unique_ptr<LambdaNode>()> parseLambda;
    std::function<std::unique_ptr<LetrecNode>()> parseLetrec;
    std::function<std::unique_ptr<IfNode>()> parseIf;
    std::function<std::unique_ptr<SequenceNode>()> parseSequence;
    std::function<std::unique_ptr<IntrinsicCallNode>()> parseIntrinsicCall;
    std::function<std::unique_ptr<ExprCallNode>()> parseExprCall;
    std::function<std::unique_ptr<AtNode>()> parseAt;
    std::function<std::unique_ptr<ExprNode>()> parseExpr;

    parseInteger = [&]() -> std::unique_ptr<IntegerNode> {
        auto token = consume(isIntegerToken);
        return std::make_unique<IntegerNode>(token.sl, std::stoi(token.text));
    };
    parseVariable = [&]() -> std::unique_ptr<VariableNode> {
        auto token = consume(isVariableToken);
        return std::make_unique<VariableNode>(token.sl, std::move(token.text));
    };
    parseLambda = [&]() -> std::unique_ptr<LambdaNode> {
        auto start = consume(isTheToken("lambda"));
        consume(isTheToken("("));
        std::vector<std::unique_ptr<VariableNode>> varList;
        while (tokens.size() && isVariableToken(tokens[0])) {
            varList.push_back(parseVariable());
        }
        consume(isTheToken(")"));
        auto expr = parseExpr();
        return std::make_unique<LambdaNode>(start.sl, std::move(varList), std::move(expr));
    };
    parseLetrec = [&]() -> std::unique_ptr<LetrecNode> {
        auto start = consume(isTheToken("letrec"));
        consume(isTheToken("("));
        std::vector<std::pair<
            std::unique_ptr<VariableNode>,
            std::unique_ptr<ExprNode>
        >> varExprList;
        while (tokens.size() && isVariableToken(tokens[0])) {
            auto v = parseVariable();
            auto e = parseExpr();
            varExprList.emplace_back(std::move(v), std::move(e));
        }
        consume(isTheToken(")"));
        auto expr = parseExpr();
        return std::make_unique<LetrecNode>(start.sl, std::move(varExprList), std::move(expr));
    };
    parseIf = [&]() -> std::unique_ptr<IfNode> {
        auto start = consume(isTheToken("if"));
        auto cond = parseExpr();
        auto branch1 = parseExpr();
        auto branch2 = parseExpr();
        return std::make_unique<IfNode>(
            start.sl, std::move(cond), std::move(branch1), std::move(branch2)
        );
    };
    parseSequence = [&]() -> std::unique_ptr<SequenceNode> {
        auto start = consume(isTheToken("{"));
        std::vector<std::unique_ptr<ExprNode>> exprList;
        while (tokens.size() && tokens[0].text != "}") {
            exprList.push_back(parseExpr());
        }
        if (!exprList.size()) {
            panic("parser", "zero-length sequence", start.sl);
        }
        consume(isTheToken("}"));
        return std::make_unique<SequenceNode>(start.sl, std::move(exprList));
    };
    parseIntrinsicCall = [&]() -> std::unique_ptr<IntrinsicCallNode> {
        auto start = consume(isTheToken("("));
        auto intrinsic = consume(isIntrinsicToken);
        std::vector<std::unique_ptr<ExprNode>> argList;
        while (tokens.size() && tokens[0].text != ")") {
            argList.push_back(parseExpr());
        }
        consume(isTheToken(")"));
        return std::make_unique<IntrinsicCallNode>(
            start.sl, std::move(intrinsic.text), std::move(argList)
        );
    };
    parseExprCall = [&]() -> std::unique_ptr<ExprCallNode> {
        auto start = consume(isTheToken("("));
        auto expr = parseExpr();
        std::vector<std::unique_ptr<ExprNode>> argList;
        while (tokens.size() && tokens[0].text != ")") {
            argList.push_back(parseExpr());
        }
        consume(isTheToken(")"));
        return std::make_unique<ExprCallNode>(start.sl, std::move(expr), std::move(argList));
    };
    parseAt = [&]() -> std::unique_ptr<AtNode> {
        auto start = consume(isTheToken("@"));
        auto var = parseVariable();
        auto expr = parseExpr();
        return std::make_unique<AtNode>(start.sl, std::move(var), std::move(expr));
    };
    parseExpr = [&]() -> std::unique_ptr<ExprNode> {
        if (!tokens.size()) {
            panic("parser", "incomplete token stream");
            return nullptr;
        } else if (isIntegerToken(tokens[0])) {
            return parseInteger();
        } else if (tokens[0].text == "lambda") {
            return parseLambda();
        } else if (tokens[0].text == "letrec") {
            return parseLetrec();
        } else if (tokens[0].text == "if") {
            return parseIf();
        // check keywords before var to avoid recognizing keywords as vars
        } else if (isVariableToken(tokens[0])) {
            return parseVariable();
        } else if (tokens[0].text == "{") {
            return parseSequence();
        } else if (tokens[0].text == "(") {
            if (tokens.size() < 2) {
                panic("parser", "incomplete token stream");
                return nullptr;
            }
            if (isIntrinsicToken(tokens[1])) {
                return parseIntrinsicCall();
            } else {
                return parseExprCall();
            }
        } else if (tokens[0].text == "@") {
            return parseAt();
        } else {
            panic("parser", "unrecognized token", tokens[0].sl);
            return nullptr;
        }
    };

    auto expr = parseExpr();
    if (tokens.size()) {
        panic("parser", "redundant token(s)", tokens[0].sl);
    }
    return expr;
}

// ------------------------------
// runtime
// ------------------------------

// every value is accessed by reference to its location on the heap 
using Location = int;

struct Void {
    Void() = default;
    std::string toString() const {
        return "<void>";
    }
};

struct Integer {
    Integer(int v): value(v) {}
    std::string toString() const {
        return std::to_string(value);
    }

    int value = 0;
};

// variable environment; newer variables have larger indices
using Env = std::vector<std::pair<std::string, Location>>;

std::optional<Location> lookup(const std::string &name, const Env &env) {
    for (auto p = env.rbegin(); p != env.rend(); p++) {
        if (p->first == name) {
            return p->second;
        }
    }
    return std::nullopt;
}

struct Closure {
    // a closure should copy its environment
    Closure(Env e, const LambdaNode *f): env(std::move(e)), fun(f) {}
    std::string toString() const {
        return "<closure evaluated at " + fun->sl.toString() + ">";
    }

    Env env;
    const LambdaNode *fun;
};

using Value = std::variant<Void, Integer, Closure>;

std::string valueToString(const Value &v) {
    if (std::holds_alternative<Void>(v)) {
        return std::get<Void>(v).toString();
    } else if (std::holds_alternative<Integer>(v)) {
        return std::get<Integer>(v).toString();
    } else {
        return std::get<Closure>(v).toString();
    }
}

// stack layer

struct Layer {
    Layer(std::shared_ptr<Env> e, const ExprNode *x, bool f = false):
        env(std::move(e)), expr(x), frame(f) {}
    bool isFrame() const {
        return frame;
    }

    // one env per frame (closure call layer)
    std::shared_ptr<Env> env;
    const ExprNode *expr;
    // whether this is a frame
    bool frame;
    // program counter inside this expr
    int pc = 0;
    // temporary local information for evaluation
    std::unordered_map<std::string, std::variant<Location, std::vector<Location>>> local;
};

class State {
public:
    State(const ExprNode *e) {
        // the main frame
        stack.emplace_back(std::make_shared<Env>(), nullptr, true);
        // the first expression (using the env of the main frame)
        stack.emplace_back(stack.back().env, e);
    }
    bool isTerminated() const {
        return stack.back().expr == nullptr;
    }
    // returns true iff the step is completed without reaching the end of evaluation
    bool step() {
        // be careful! this reference may be invalidated after modifying the stack
        // so always keep stack change as the last operation
        auto &layer = stack.back();
        // main frame; end of evaluation
        if (layer.expr == nullptr) {
            return false;
        }
        // evaluations for every case
        if (auto inode = dynamic_cast<const IntegerNode*>(layer.expr)) {
            resultLoc = _new<Integer>(inode->val);
            stack.pop_back();
        } else if (auto vnode = dynamic_cast<const VariableNode*>(layer.expr)) {
            auto loc = lookup(vnode->name, *(layer.env));
            if (!loc.has_value()) {
                panic("runtime", "undefined variable", layer.expr->sl);
            }
            resultLoc = loc.value();
            stack.pop_back();
        } else if (auto lnode = dynamic_cast<const LambdaNode*>(layer.expr)) {
            // copy the env into the closure
            resultLoc = _new<Closure>(*(layer.env), lnode);
            stack.pop_back();
        } else if (auto lnode = dynamic_cast<const LetrecNode*>(layer.expr)) {
            // unified argument recording
            if (layer.pc > 1 && layer.pc <= lnode->varExprList.size() + 1) {
                auto loc = lookup(
                    lnode->varExprList[layer.pc - 2].first->name,
                    *(layer.env)
                );
                // this shouldn't happen since those variables are newly introduced by letrec
                if (!loc.has_value()) {
                    panic("runtime", "undefined variable", layer.expr->sl);
                }
                // copy (inherited resultLoc)
                heap[loc.value()] = heap[resultLoc];
            }
            // create all new locations
            if (layer.pc == 0) {
                layer.pc++;
                for (const auto &[var, _] : lnode->varExprList) {
                    layer.env->push_back(std::make_pair(
                        var->name,
                        _new<Void>()
                    ));
                }
            // evaluate bindings
            } else if (layer.pc <= lnode->varExprList.size()) {
                layer.pc++;
                // note: growing the stack might invalidate the reference "layer"
                //       but this is fine since next time "layer" will be re-bound
                stack.emplace_back(
                    layer.env,
                    lnode->varExprList[layer.pc - 2].second.get()
                );
            // evaluate body
            } else if (layer.pc == lnode->varExprList.size() + 1) {
                layer.pc++;
                stack.emplace_back(
                    layer.env,
                    lnode->expr.get()
                );
            // finish letrec
            } else {
                int nParams = lnode->varExprList.size();
                for (int i = 0; i < nParams; i++) {
                    layer.env->pop_back();
                }
                // no need to update resultLoc: inherited from body evaluation
                stack.pop_back();
            }
        } else if (auto inode = dynamic_cast<const IfNode*>(layer.expr)) {
            // evaluate condition
            if (layer.pc == 0) {
                layer.pc++;
                stack.emplace_back(layer.env, inode->cond.get());
            // evaluate one branch
            } else if (layer.pc == 1) {
                layer.pc++;
                // inherited condition value
                if (!std::holds_alternative<Integer>(heap[resultLoc])) {
                    panic("runtime", "wrong cond type", layer.expr->sl);
                }
                if (std::get<Integer>(heap[resultLoc]).value) {
                    stack.emplace_back(layer.env, inode->branch1.get());
                } else {
                    stack.emplace_back(layer.env, inode->branch2.get());
                }
            // finish if
            } else {
                // no need to update resultLoc: inherited
                stack.pop_back();
            }
        } else if (auto snode = dynamic_cast<const SequenceNode*>(layer.expr)) {
            // evaluate one-by-one
            if (layer.pc < snode->exprList.size()) {
                layer.pc++;
                stack.emplace_back(
                    layer.env,
                    snode->exprList[layer.pc - 1].get()
                );
            // finish
            } else {
                // sequence's value is the last expression's value
                // no need to update resultLoc: inherited
                stack.pop_back();
            }
        } else if (auto cnode = dynamic_cast<const IntrinsicCallNode*>(layer.expr)) {
            // unified argument recording
            if (layer.pc > 1 && layer.pc <= cnode->argList.size() + 1) {
                // it's guaranteed to contain the vector alternative
                std::get<std::vector<Location>>(layer.local["args"]).push_back(resultLoc);
            }
            // initialization
            if (layer.pc == 0) {
                layer.pc++;
                layer.local["args"] = std::vector<Location>();
            // evaluate arguments
            } else if (layer.pc <= cnode->argList.size()) {
                layer.pc++;
                stack.emplace_back(
                    layer.env,
                    cnode->argList[layer.pc - 2].get()
                );
            // intrinsic call doesn't grow the stack
            } else {
                auto value = _callIntrinsic(
                    layer.expr->sl,
                    cnode->intrinsic,
                    // intrinsic call is pass by reference
                    std::get<std::vector<Location>>(layer.local["args"])
                );
                resultLoc = _moveNew(std::move(value));
                stack.pop_back();
            }
        } else if (auto cnode = dynamic_cast<const ExprCallNode*>(layer.expr)) {
            // unified argument recording
            if (layer.pc > 2 && layer.pc <= cnode->argList.size() + 2) {
                std::get<std::vector<Location>>(layer.local["args"]).push_back(resultLoc);
            }
            // evaluate the callee
            if (layer.pc == 0) {
                layer.pc++;
                stack.emplace_back(
                    layer.env,
                    cnode->expr.get()
                );
            // initialization
            } else if (layer.pc == 1) {
                layer.pc++;
                // inherited callee location
                layer.local["expr"] = resultLoc;
                layer.local["args"] = std::vector<Location>();
            // evaluate arguments
            } else if (layer.pc <= cnode->argList.size() + 1) {
                layer.pc++;
                stack.emplace_back(
                    layer.env,
                    cnode->argList[layer.pc - 3].get()
                );
            // call
            } else if (layer.pc == cnode->argList.size() + 2) {
                layer.pc++;
                auto &exprLoc = std::get<Location>(layer.local["expr"]);
                auto &argsLoc = std::get<std::vector<Location>>(layer.local["args"]);
                if (!std::holds_alternative<Closure>(heap[exprLoc])) {
                    panic("runtime", "calling a non-callable", layer.expr->sl);
                }
                auto &closure = std::get<Closure>(heap[exprLoc]);
                // types will be checked inside the closure call
                if (argsLoc.size() != closure.fun->varList.size()) {
                    panic("runtime", "wrong number of arguments", layer.expr->sl);
                }
                int nArgs = argsLoc.size();
                // lexical scope: copy the env from the closure definition place
                auto newEnv = closure.env;
                for (int i = 0; i < nArgs; i++) {
                    // closure call is pass by reference
                    newEnv.push_back(std::make_pair(
                        closure.fun->varList[i]->name,
                        argsLoc[i]
                    ));
                }
                // evaluation of the closure body
                stack.emplace_back(
                    // new frame has new env
                    std::make_shared<Env>(std::move(newEnv)),
                    closure.fun->expr.get(),
                    true
                );
            // finish
            } else {
                // no need to update resultLoc: inherited
                stack.pop_back();
            }
        } else if (auto anode = dynamic_cast<const AtNode*>(layer.expr)) {
            // evaluate the expr
            if (layer.pc == 0) {
                layer.pc++;
                stack.emplace_back(layer.env, anode->expr.get());
            } else {
                // inherited resultLoc
                if (!std::holds_alternative<Closure>(heap[resultLoc])) {
                    panic("runtime", "@ wrong type", layer.expr->sl);
                }
                auto loc = lookup(
                    anode->var->name,
                    std::get<Closure>(heap[resultLoc]).env
                );
                if (!loc.has_value()) {
                    panic("runtime", "undefined variable", layer.expr->sl);
                }
                // "access by reference"
                resultLoc = loc.value();
                stack.pop_back();
            }
        } else {
            panic("runtime", "unrecognized AST node", layer.expr->sl);
        }
        return true;
    }
    void execute() {
        static constexpr int GC_INTERVAL = 1000;
        int ctr = 0;
        while (step()) {
            ctr++;
            if (ctr && (ctr % GC_INTERVAL == 0)) {
                _gc();
            }
        }
    }
    const Value &getResult() const {
        return heap[resultLoc];
    }
private:
    template <typename... Alt>
    requires (true && ... && (std::same_as<Alt, Value> || isAlternativeOf<Alt, Value>))
    void _typecheck(SourceLocation sl, const std::vector<Location> &args) {
        bool ok = args.size() == sizeof...(Alt);
        int i = -1;
        ok = ok && (true && ... && (
            i++,
            [&] {
                if constexpr (std::same_as<Alt, Value>) {
                    return true;
                } else {
                    return std::holds_alternative<Alt>(heap[args[i]]);
                }
            } ()
        ));
        if (!ok) {
            panic("runtime", "type error on intrinsic call", sl);
        }
    }
    // intrinsic dispatch
    Value _callIntrinsic(
        SourceLocation sl, const std::string &name, const std::vector<Location> &args
    ) {
        if (name == ".void") {
            _typecheck<>(sl, args);
            return Void();
        } else if (name == ".+") {
            _typecheck<Integer, Integer>(sl, args);
            return Integer(
                std::get<Integer>(heap[args[0]]).value +
                std::get<Integer>(heap[args[1]]).value
            );
        } else if (name == ".-") {
            _typecheck<Integer, Integer>(sl, args);
            return Integer(
                std::get<Integer>(heap[args[0]]).value -
                std::get<Integer>(heap[args[1]]).value
            );
        } else if (name == ".*") {
            _typecheck<Integer, Integer>(sl, args);
            return Integer(
                std::get<Integer>(heap[args[0]]).value *
                std::get<Integer>(heap[args[1]]).value
            );
        } else if (name == "./") {
            _typecheck<Integer, Integer>(sl, args);
            return Integer(
                std::get<Integer>(heap[args[0]]).value /
                std::get<Integer>(heap[args[1]]).value
            );
        } else if (name == ".%") {
            _typecheck<Integer, Integer>(sl, args);
            return Integer(
                std::get<Integer>(heap[args[0]]).value %
                std::get<Integer>(heap[args[1]]).value
            );
        } else if (name == ".<") {
            _typecheck<Integer, Integer>(sl, args);
            return Integer(
                std::get<Integer>(heap[args[0]]).value <
                std::get<Integer>(heap[args[1]]).value ? 1 : 0
            );
        } else if (name == ".type") {
            _typecheck<Value>(sl, args);
            int label = -1;
            if (std::holds_alternative<Void>(heap[args[0]])) {
                label = 0;
            } else if (std::holds_alternative<Integer>(heap[args[0]])) {
                label = 1;
            } else {
                label = 2;
            }
            return Integer(label);
        } else if (name == ".get") {
            _typecheck<>(sl, args);
            int v;
            std::cin >> v;
            return Integer(v);
        } else if (name == ".put") {
            _typecheck<Integer>(sl, args);
            std::cout << std::get<Integer>(heap[args[0]]).value << std::endl;
            return Void();
        } else {
            panic("runtime", "unrecognized intrinsic call", sl);
            return Void();
        }
    }
    // memory management
    template <typename V, typename... Args>
    requires isAlternativeOf<V, Value>
    Location _new(Args&&... args) {
        heap.push_back(std::move(V(std::forward<Args>(args)...)));
        return heap.size() - 1;
    }
    Location _moveNew(Value v) {
        heap.push_back(std::move(v));
        return heap.size() - 1;
    }
    std::unordered_set<Location> _mark() {
        std::unordered_set<Location> visited;
        // for each traversed location, specifically handle the closure case
        std::function<void(Location)> traverseLocation =
            // "this" captures the current object by reference
            [this, &visited, &traverseLocation](Location loc) {
            if (!(visited.contains(loc))) {
                visited.insert(loc);
                if (std::holds_alternative<Closure>(heap[loc])) {
                    for (const auto &[_, l] : std::get<Closure>(heap[loc]).env) {
                        traverseLocation(l);
                    }
                }
            }
        };
        // traverse the stack
        for (const auto &layer : stack) {
            // only frames "own" the environments
            if (layer.isFrame()) {
                for (const auto &[_, loc] : (*(layer.env))) {
                    traverseLocation(loc);
                }
            }
            // but each layer can still have locals
            for (const auto &[_, v] : layer.local) {
                if (std::holds_alternative<Location>(v)) {
                    traverseLocation(std::get<Location>(v));
                } else {
                    const auto &vec = std::get<std::vector<Location>>(v);
                    for (const auto &loc : vec) {
                        traverseLocation(loc);
                    }
                }
            }
        }
        // traverse the resultLoc
        traverseLocation(resultLoc);
        return visited;
    }
    std::pair<int, std::unordered_map<Location, Location>>
        _sweepAndCompact(const std::unordered_set<Location> &visited) {
        int removed = 0;
        std::unordered_map<Location, Location> relocation;
        Location n = heap.size();
        Location i{0}, j{0};
        while (j < n) {
            if (visited.contains(j)) {
                if (i < j) {
                    heap[i] = std::move(heap[j]);
                    relocation[j] = i;
                    i++;
                    j++;
                } else {
                    i++;
                    j++;
                }
            } else {
                removed++;
                j++;
            }
        }
        heap.resize(i);
        return std::make_pair(removed, std::move(relocation));
    }
    void _relocate(const std::unordered_map<Location, Location> &relocation) {
        auto reloc = [&relocation](Location &loc) -> void {
            if (relocation.contains(loc)) {
                loc = relocation.at(loc);
            }
        };
        // traverse the stack
        for (auto &layer : stack) {
            // only frames "own" the environments
            if (layer.isFrame()) {
                for (auto &[_, loc] : (*(layer.env))) {
                    reloc(loc);
                }
            }
            // but each layer can still have locals
            for (auto &[_, v] : layer.local) {
                if (std::holds_alternative<Location>(v)) {
                    reloc(std::get<Location>(v));
                } else {
                    auto &vec = std::get<std::vector<Location>>(v);
                    for (auto &loc : vec) {
                        reloc(loc);
                    }
                }
            }
        }
        // traverse the resultLoc
        reloc(resultLoc);
        // traverse the closure values
        for (auto &v : heap) {
            if (std::holds_alternative<Closure>(v)) {
                auto &c = std::get<Closure>(v);
                for (auto &[_, loc] : c.env) {
                    reloc(loc);
                }
            }
        }
    }
    int _gc() {
        auto visited = _mark();
        const auto &[removed, relocation] = _sweepAndCompact(visited);
        _relocate(relocation);
        return removed;
    }
    // states
    std::vector<Layer> stack;
    std::vector<Value> heap;
    Location resultLoc;
};

// ------------------------------
// main
// ------------------------------

std::string readSource(const std::string &spath) {
    if (!std::filesystem::exists(spath)) {
        throw std::runtime_error(spath + " does not exist.");
    }
    static constexpr std::size_t BLOCK = 4096;
    std::ifstream in(spath);
    in.exceptions(std::ios_base::badbit);
    std::string source;
    char buf[BLOCK];
    while (in.read(buf, BLOCK)) {
        source.append(buf, 0, in.gcount());
    }
    source.append(buf, 0, in.gcount());
    return source;
}

int main(int argc, char **argv) {
    if (argc != 2) {
        std::cerr << "Usage: " << argv[0] << " <source-path>\n";
        return 1;
    }
    std::string source = readSource(argv[1]);
    try {
        auto expr = parse(lex(source));
        State state(expr.get());
        state.execute();
        std::cout << valueToString(state.getResult()) << std::endl;
    } catch (const std::runtime_error &e) {
        std::cerr << e.what() << std::endl;
        std::exit(EXIT_FAILURE);
    }
}
