#include <deque>
#include <utility>
#include <string>
#include <stdexcept>
#include <unordered_set>
#include <unordered_map>
#include <algorithm>
#include <optional>
#include <cctype>
#include <functional>
#include <memory>
#include <vector>
#include <variant>
#include <concepts>
#include <type_traits>
#include <iostream>
#include <array>

// helper(s)

struct SourceLocation {
    SourceLocation(int l = 1, int c = 1): line(l), column(c) {}
    std::string toString() const {
        if (line <= 0 || column <= 0) {
            return "(SourceLocation N/A)";
        }
        return "(SourceLocation " +
            std::to_string(line) + " " + std::to_string(column) + ")";
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

void panic(const std::string &type, const SourceLocation &sl,
    const std::string &msg) {
    throw std::runtime_error(
        "[" + type + " error " + sl.toString() + "] " + msg
    );
}

// lexer

struct SourceStream {
    SourceStream(std::string s): source(std::move(s)) {
        std::string charstr =
            "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
            "0123456789`~!@#$%^&*()-_=+[{]}\\|;:'\",<.>/? \t\n";
        std::unordered_set<char> charset(charstr.begin(), charstr.end());
        for (auto c : source) {
            if (!charset.contains(c)) {
                panic("lexer", sl, "unsupported character");
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

    auto countTrailingEscape = [](const std::string &s) -> int {
        int cnt = 0;
        int pos = s.size() - 1;
        while (pos >= 0 && s[pos] == '\\') {
            cnt++;
            pos--;
        }
        return cnt;
    };

    std::function<std::optional<Token>()> nextToken =
        [&ss, &countTrailingEscape, &nextToken]()
            -> std::optional<Token> {
        // skip whitespaces
        while (ss.hasNext() && std::isspace(ss.peekNext())) {
            ss.popNext();
        }
        if (!ss.hasNext()) {
            return std::nullopt;
        }
        // read the next token
        auto start_sl = ss.getNextSourceLocation();
        std::string text = "";
        // integer literal
        if (
            std::isdigit(ss.peekNext()) ||
            ss.peekNext() == '-' ||
            ss.peekNext() == '+'
        ) {
            if (ss.peekNext() == '-' || ss.peekNext() == '+') {
                text += ss.popNext();
            }
            while (ss.hasNext() && std::isdigit(ss.peekNext())) {
                text += ss.popNext();
            }
        // variable / keyword
        } else if (std::isalpha(ss.peekNext())) {
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
            while (
                ss.hasNext() &&
                !(std::isspace(ss.peekNext()) || ss.peekNext() == ')')
            ) {
                text += ss.popNext();
            }
        // special symbol
        } else if (
            std::string("()[]=@&").find(ss.peekNext()) != std::string::npos
        ) {
            text += ss.popNext();
        // string literal
        } else if (ss.peekNext() == '"') {
            text += ss.popNext();
            while (
                ss.hasNext() && (
                    ss.peekNext() != '"' ||
                    (ss.peekNext() == '"' && countTrailingEscape(text) % 2 != 0)
                )
            ) {
                text += ss.popNext();
            }
            if (ss.hasNext() && ss.peekNext() == '"') {
                text += ss.popNext();
            } else {
                panic("lexer", start_sl, "incomplete string literal");
            }
        // comment
        } else if (ss.peekNext() == '#') {
            while (ss.hasNext() && ss.peekNext() != '\n') {
                ss.popNext();
            }
            // nextToken() will consume the \n and recursively continue
            return nextToken();
        } else {
            panic("lexer", start_sl, "unsupported starting character");
        }
        return Token(start_sl, std::move(text));
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

// parser

struct ExprNode {
    ExprNode(SourceLocation s): sl(s) {}
    ExprNode(const ExprNode &) = delete;
    ExprNode &operator=(const ExprNode &) = delete;
    virtual ~ExprNode() {}

    SourceLocation sl;
};

struct IntegerNode : public ExprNode {
    IntegerNode(SourceLocation s, int v): ExprNode(s), val(v) {}
    IntegerNode(const IntegerNode&) = delete;
    IntegerNode &operator=(const IntegerNode &) = delete;
    virtual ~IntegerNode() override {}

    int val;
};

struct StringNode : public ExprNode {
    StringNode(SourceLocation s, std::string v):
        ExprNode(s), val(std::move(v)) {}
    StringNode(const StringNode &) = delete;
    StringNode &operator=(const StringNode &) = delete;
    virtual ~StringNode() override {}

    std::string val;
};

struct IntrinsicNode : public ExprNode {
    IntrinsicNode(SourceLocation s, std::string n):
        ExprNode(s), name(std::move(n)) {}
    IntrinsicNode(const IntrinsicNode &) = delete;
    IntrinsicNode &operator=(const IntrinsicNode &) = delete;
    virtual ~IntrinsicNode() override {}

    std::string name;
};

struct VariableNode : public ExprNode {
    VariableNode(SourceLocation s, std::string n):
        ExprNode(s), name(std::move(n)) {}
    VariableNode(const VariableNode &) = delete;
    VariableNode &operator=(const VariableNode &) = delete;
    virtual ~VariableNode() override {}

    std::string name;
};

struct SetNode : public ExprNode {
    SetNode(
        SourceLocation s,
        std::unique_ptr<VariableNode> v,
        std::unique_ptr<ExprNode> e
    ): ExprNode(s), var(std::move(v)), expr(std::move(e)) {}
    SetNode(const SetNode &) = delete;
    SetNode &operator=(const SetNode &) = delete;
    virtual ~SetNode() override {}

    std::unique_ptr<VariableNode> var;
    std::unique_ptr<ExprNode> expr;
};

struct LambdaNode : public ExprNode {
    LambdaNode(SourceLocation s,
        std::vector<std::unique_ptr<VariableNode>> v,
        std::unique_ptr<ExprNode> e
    ): ExprNode(s), varList(std::move(v)), expr(std::move(e)) {}
    LambdaNode(const LambdaNode &) = delete;
    LambdaNode &operator=(const LambdaNode &) = delete;
    virtual ~LambdaNode() override {}

    std::vector<std::unique_ptr<VariableNode>> varList;
    std::unique_ptr<ExprNode> expr;
};

struct LetrecNode : public ExprNode {
    LetrecNode(
        SourceLocation s,
        std::vector<std::pair<
            std::unique_ptr<VariableNode>, std::unique_ptr<ExprNode>
        >> v,
        std::unique_ptr<ExprNode> e
    ): ExprNode(s), varExprList(std::move(v)), expr(std::move(e)) {}
    LetrecNode(const LetrecNode &) = delete;
    LetrecNode &operator=(const LetrecNode &) = delete;
    virtual ~LetrecNode() override {}
    
    std::vector<std::pair<
        std::unique_ptr<VariableNode>, std::unique_ptr<ExprNode>
    >> varExprList;
    std::unique_ptr<ExprNode> expr;
};

struct IfNode : public ExprNode {
    IfNode(
        SourceLocation s,
        std::unique_ptr<ExprNode> c,
        std::unique_ptr<ExprNode> b1,
        std::unique_ptr<ExprNode> b2
    ): 
        ExprNode(s), cond(std::move(c)),
        branch1(std::move(b1)), branch2(std::move(b2)) {}
    IfNode(const IfNode &) = delete;
    IfNode &operator=(const IfNode &) = delete;
    virtual ~IfNode() override {}

    std::unique_ptr<ExprNode> cond;
    std::unique_ptr<ExprNode> branch1;
    std::unique_ptr<ExprNode> branch2;
};

struct WhileNode : public ExprNode {
    WhileNode(
        SourceLocation s,
        std::unique_ptr<ExprNode> c,
        std::unique_ptr<ExprNode> b
    ): ExprNode(s), cond(std::move(c)), body(std::move(b)) {}
    WhileNode(const WhileNode &) = delete;
    WhileNode &operator=(const WhileNode &) = delete;
    virtual ~WhileNode() override {}

    std::unique_ptr<ExprNode> cond;
    std::unique_ptr<ExprNode> body;
};

struct CallNode : public ExprNode {
    CallNode(
        SourceLocation s,
        std::unique_ptr<ExprNode> c,
        std::vector<std::unique_ptr<ExprNode>> a
    ): ExprNode(s), callee(std::move(c)), argList(std::move(a)) {}
    CallNode(const CallNode &) = delete;
    CallNode &operator=(const CallNode &) = delete;
    virtual ~CallNode() override {}

    std::unique_ptr<ExprNode> callee;
    std::vector<std::unique_ptr<ExprNode>> argList;
};

struct SequenceNode : public ExprNode {
    SequenceNode(
        SourceLocation s,
        std::vector<std::unique_ptr<ExprNode>> e
    ): ExprNode(s), exprList(std::move(e)) {}
    SequenceNode(const SequenceNode &) = delete;
    SequenceNode &operator=(const SequenceNode &) = delete;
    virtual ~SequenceNode() override {}

    std::vector<std::unique_ptr<ExprNode>> exprList;
};

struct QueryNode : public ExprNode {
    QueryNode(
        SourceLocation s,
        std::unique_ptr<VariableNode> v,
        std::unique_ptr<ExprNode> e
    ): ExprNode(s), var(std::move(v)), expr(std::move(e)) {}
    QueryNode(const QueryNode &) = delete;
    QueryNode &operator=(const QueryNode &) = delete;
    virtual ~QueryNode() override {}

    std::unique_ptr<VariableNode> var;
    std::unique_ptr<ExprNode> expr;
};

struct AccessNode : public ExprNode {
    AccessNode(
        SourceLocation s,
        std::unique_ptr<VariableNode> v,
        std::unique_ptr<ExprNode> e
    ): ExprNode(s), var(std::move(v)), expr(std::move(e)) {}
    AccessNode(const AccessNode &) = delete;
    AccessNode &operator=(const AccessNode &) = delete;
    virtual ~AccessNode() override {}

    std::unique_ptr<VariableNode> var;
    std::unique_ptr<ExprNode> expr;
};

std::unique_ptr<ExprNode> parse(std::deque<Token> tokens) {
    auto isNumberToken = [](const Token &token) {
        return
            token.text.size() > 0 && (
                std::isdigit(token.text[0]) ||
                token.text[0] == '-' ||
                token.text[0] == '+'
            );
    };
    auto isStringToken = [](const Token &token) {
        return token.text.size() > 0 && token.text[0] == '"';
    };
    auto isIntrinsicToken = [](const Token &token) {
        return token.text.size() > 0 && token.text[0] == '.';
    };
    auto isVariableToken = [](const Token &token) {
        return token.text.size() > 0 && std::isalpha(token.text[0]);
    };
    auto isToken = [](const std::string &s) {
        return [s](const Token &token) {
            return token.text == s;
        };
    };

    auto consume =
        [&tokens]<typename Callable>(const Callable &predicate) -> Token {
        if (tokens.size() == 0) {
            panic(
                "parser", SourceLocation(-1, -1), "incomplete token stream"
            );
        }
        auto token = tokens.front();
        tokens.pop_front();
        if (!predicate(token)) {
            panic("parser", token.sl, "unexpected token");
        }
        return token;
    };

    std::function<std::unique_ptr<IntegerNode>()> parseNumber;
    std::function<std::unique_ptr<StringNode>()> parseString;
    std::function<std::unique_ptr<IntrinsicNode>()> parseIntrinsic;
    std::function<std::unique_ptr<SetNode>()> parseSet;
    std::function<std::unique_ptr<LambdaNode>()> parseLambda;
    std::function<std::unique_ptr<LetrecNode>()> parseLetrec;
    std::function<std::unique_ptr<IfNode>()> parseIf;
    std::function<std::unique_ptr<WhileNode>()> parseWhile;
    std::function<std::unique_ptr<VariableNode>()> parseVariable;
    std::function<std::unique_ptr<CallNode>()> parseCall;
    std::function<std::unique_ptr<SequenceNode>()> parseSequence;
    std::function<std::unique_ptr<QueryNode>()> parseQuery;
    std::function<std::unique_ptr<AccessNode>()> parseAccess;
    std::function<std::unique_ptr<ExprNode>()> parseExpr;

    parseNumber = [&]() -> std::unique_ptr<IntegerNode> {
        auto token = consume(isNumberToken);
        return std::make_unique<IntegerNode>(token.sl, std::stoi(token.text));
    };
    parseString = [&]() -> std::unique_ptr<StringNode> {
        auto token = consume(isStringToken);
        auto content = token.text;
        content.pop_back();
        std::reverse(content.begin(), content.end());
        content.pop_back();
        std::string s;
        while (content.size()) {
            auto c = content.back();
            content.pop_back();
            if (c == '\\') {
                if (content.size()) {
                    auto next = content.back();
                    content.pop_back();
                    if (next == '\\') {
                        s += '\\';
                    } else if (next == '"') {
                        s += '"';
                    } else if (next == 't') {
                        s += '\t';
                    } else if (next == 'n') {
                        s += '\n';
                    } else {
                        panic(
                            "parser", token.sl, "unsupported escape sequence"
                        );
                    }
                } else {
                    panic(
                        "parser", token.sl, "incomplete escape sequence"
                    );
                }
            } else {
                s += c;
            }
        }
        return std::make_unique<StringNode>(token.sl, std::move(s));
    };
    parseIntrinsic = [&]() -> std::unique_ptr<IntrinsicNode> {
        auto token = consume(isIntrinsicToken);
        return std::make_unique<IntrinsicNode>(token.sl, token.text);
    };
    parseSet = [&]() -> std::unique_ptr<SetNode> {
        auto start = consume(isToken("set"));
        auto var = parseVariable();
        auto expr = parseExpr();
        return std::make_unique<SetNode>(
            start.sl, std::move(var), std::move(expr)
        );
    };
    parseLambda = [&]() -> std::unique_ptr<LambdaNode> {
        auto start = consume(isToken("lambda"));
        consume(isToken("("));
        std::vector<std::unique_ptr<VariableNode>> varList;
        while (tokens.size() && isVariableToken(tokens[0])) {
            varList.push_back(parseVariable());
        }
        consume(isToken(")"));
        auto expr = parseExpr();
        return std::make_unique<LambdaNode>(
            start.sl, std::move(varList), std::move(expr)
        );
    };
    parseLetrec = [&]() -> std::unique_ptr<LetrecNode> {
        auto start = consume(isToken("letrec"));
        consume(isToken("("));
        std::vector<std::pair<
            std::unique_ptr<VariableNode>,
            std::unique_ptr<ExprNode>
        >> varExprList;
        while (tokens.size() && isVariableToken(tokens[0])) {
            auto v = parseVariable();
            consume(isToken("="));
            auto e = parseExpr();
            varExprList.emplace_back(std::move(v), std::move(e));
        }
        consume(isToken(")"));
        auto expr = parseExpr();
        return std::make_unique<LetrecNode>(
            start.sl, std::move(varExprList), std::move(expr)
        );
    };
    parseIf = [&]() -> std::unique_ptr<IfNode> {
        auto start = consume(isToken("if"));
        auto cond = parseExpr();
        auto branch1 = parseExpr();
        auto branch2 = parseExpr();
        return std::make_unique<IfNode>(
            start.sl, std::move(cond), std::move(branch1), std::move(branch2)
        );
    };
    parseWhile = [&]() -> std::unique_ptr<WhileNode> {
        auto start = consume(isToken("while"));
        auto cond = parseExpr();
        auto body = parseExpr();
        return std::make_unique<WhileNode>(
            start.sl, std::move(cond), std::move(body)
        );
    };
    parseVariable = [&]() -> std::unique_ptr<VariableNode> {
        auto token = consume(isVariableToken);
        return std::make_unique<VariableNode>(token.sl, std::move(token.text));
    };
    parseCall = [&]() -> std::unique_ptr<CallNode> {
        auto start = consume(isToken("("));
        if (!tokens.size()) {
            panic("parser", start.sl, "incomplete tokens stream");
        }
        std::unique_ptr<ExprNode> callee =
            isIntrinsicToken(tokens[0]) ? parseIntrinsic() : parseExpr();
        std::vector<std::unique_ptr<ExprNode>> argList;
        while (tokens.size() && tokens[0].text != ")") {
            argList.push_back(parseExpr());
        }
        consume(isToken(")"));
        return std::make_unique<CallNode>(
            start.sl, std::move(callee), std::move(argList)
        );
    };
    parseSequence = [&]() -> std::unique_ptr<SequenceNode> {
        auto start = consume(isToken("["));
        std::vector<std::unique_ptr<ExprNode>> exprList;
        while (tokens.size() && tokens[0].text != "]") {
            exprList.push_back(parseExpr());
        }
        if (!exprList.size()) {
            panic("parser", start.sl, "zero-length sequence");
        }
        consume(isToken("]"));
        return std::make_unique<SequenceNode>(start.sl, std::move(exprList));
    };
    parseQuery = [&]() -> std::unique_ptr<QueryNode> {
        auto start = consume(isToken("@"));
        auto var = parseVariable();
        auto expr = parseExpr();
        return std::make_unique<QueryNode>(
            start.sl, std::move(var), std::move(expr)
        );
    };
    parseAccess = [&]() -> std::unique_ptr<AccessNode> {
        auto start = consume(isToken("&"));
        auto var = parseVariable();
        auto expr = parseExpr();
        return std::make_unique<AccessNode>(
            start.sl, std::move(var), std::move(expr)
        );
    };
    parseExpr = [&]() -> std::unique_ptr<ExprNode> {
        if (!tokens.size()) {
            panic(
                "parser", SourceLocation(-1, -1), "incomplete token stream"
            );
            return nullptr;
        } else if (isNumberToken(tokens[0])) {
            return parseNumber();
        } else if (isStringToken(tokens[0])) {
            return parseString();
        } else if (tokens[0].text == "set") {
            return parseSet();
        } else if (tokens[0].text == "lambda") {
            return parseLambda();
        } else if (tokens[0].text == "letrec") {
            return parseLetrec();
        } else if (tokens[0].text == "if") {
            return parseIf();
        } else if (tokens[0].text == "while") {
            return parseWhile();
        // check keywords before var to avoid recognizing keywords as vars
        } else if (isVariableToken(tokens[0])) {
            return parseVariable();
        } else if (tokens[0].text == "(") {
            return parseCall();
        } else if (tokens[0].text == "[") {
            return parseSequence();
        } else if (tokens[0].text == "@") {
            return parseQuery();
        } else if (tokens[0].text == "&") {
            return parseAccess();
        } else {
            panic("parser", tokens[0].sl, "unrecognized token");
            return nullptr;
        }
    };

    auto expr = parseExpr();
    if (tokens.size()) {
        panic("parser", tokens[0].sl, "redundant token(s)");
    }
    return expr;
}

// runtime

// every value is accessed by reference, which is its location on the heap 
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

struct String {
    String(std::string v): value(std::move(v)) {}
    std::string toString() const {
        return value;
    }

    std::string value;
};

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
    Closure(Env e, LambdaNode *f):
        env(std::move(e)), fun(f) {}
    std::string toString() const {
        return "<closure evaluated at " + fun->sl.toString() + ">";
    }

    Env env;
    LambdaNode *fun;
};

using Value = std::variant<Void, Integer, String, Closure>;

std::string valueToString(const Value &v) {
    if (std::holds_alternative<Void>(v)) {
        return std::get<Void>(v).toString();
    } else if (std::holds_alternative<Integer>(v)) {
        return std::get<Integer>(v).toString();
    } else if (std::holds_alternative<String>(v)) {
        return std::get<String>(v).toString();
    } else {
        return std::get<Closure>(v).toString();
    }
}

template <typename Type, typename Variant>
struct isAlternativeOf {
    static constexpr bool value = false;
};

template <typename Type, typename... Alternative>
requires ((0 + ... + (std::same_as<Type, Alternative> ? 1 : 0)) == 1)
struct isAlternativeOf<Type, std::variant<Alternative...>> {
    static constexpr bool value = true;
};

template <typename... Alternative, typename... Variant>
requires (
    true && ... &&
    isAlternativeOf<Alternative, std::remove_cvref_t<Variant>>::value
)
bool holds(Variant&&... vars) {
    return (
        true && ... &&
        std::holds_alternative<Alternative>(std::forward<Variant>(vars))
    );
}

struct Layer {
    Layer(std::shared_ptr<Env> e, ExprNode *x, bool f = false):
      env(std::move(e)), expr(x), frame(f) {}
    bool isFrame() const {
        return frame;
    }

    std::shared_ptr<Env> env;
    ExprNode *expr;
    bool frame;
    // program counter
    int pc = 0;
    // local helpers for evaluation
    std::unordered_map<
        std::string, std::variant<Location, std::vector<Location>>
    > local;
};

using Stack = std::vector<Layer>;
using Heap = std::vector<Value>;

constexpr int GC_INTERVAL = 10000;

class State {
public:
    State(ExprNode *e) {
        // the main frame
        stack.push_back(Layer(std::make_shared<Env>(), nullptr, true));
        // the first expression
        stack.push_back(Layer(stack.back().env, e));
    }
    bool step() {
        // careful! this reference may be invalidated after modifying stack
        // so always keep the stack change operation as the last one
        auto &layer = stack.back();
        if (layer.expr == nullptr) {
            // end of evaluation
            return false;
        } else if (auto inode = dynamic_cast<IntegerNode*>(layer.expr)) {
            resultLoc = _new<Integer>(inode->val);
            stack.pop_back();
        } else if (auto snode = dynamic_cast<StringNode*>(layer.expr)) {
            resultLoc = _new<String>(snode->val);
            stack.pop_back();
        } else if (auto vnode = dynamic_cast<VariableNode*>(layer.expr)) {
            auto loc = lookup(vnode->name, *(layer.env));
            if (!loc.has_value()) {
                panic("runtime", layer.expr->sl, "undefined variable");
            }
            resultLoc = loc.value();
            stack.pop_back();
        } else if (auto snode = dynamic_cast<SetNode*>(layer.expr)) {
            if (layer.pc == 0) {
                layer.pc++;
                stack.push_back(Layer(
                    layer.env, snode->expr.get()
                ));
            } else {
                auto loc = lookup(snode->var->name, *(layer.env));
                if (!loc.has_value()) {
                    panic("runtime", layer.expr->sl, "undefined variable");
                }
                heap[loc.value()] = heap[resultLoc];
                resultLoc = _new<Void>();
                stack.pop_back();
            }
        } else if (auto lnode = dynamic_cast<LambdaNode*>(layer.expr)) {
            resultLoc = _new<Closure>(*(layer.env), lnode);
            stack.pop_back();
        } else if (auto lnode = dynamic_cast<LetrecNode*>(layer.expr)) {
            // unified argument copy
            if (layer.pc > 1 && layer.pc <= lnode->varExprList.size() + 1) {
                auto loc = lookup(
                    lnode->varExprList[layer.pc - 2].first->name,
                    *(layer.env)
                );
                if (!loc.has_value()) {
                    panic("runtime", layer.expr->sl, "undefined variable");
                }
                // copy
                heap[loc.value()] = heap[resultLoc];
            }
            // create new locations
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
                stack.push_back(
                    Layer(
                        layer.env,
                        lnode->varExprList[layer.pc - 2].second.get()
                    )
                );
            // evaluate body
            } else if (layer.pc == lnode->varExprList.size() + 1) {
                layer.pc++;
                stack.push_back(
                    Layer(
                        layer.env,
                        lnode->expr.get()
                    )
                );
            // finish letrec
            } else {
                int nParams = lnode->varExprList.size();
                for (int i = 0; i < nParams; i++) {
                    layer.env->pop_back();
                }
                // no need to update resultLoc: inherited
                stack.pop_back();
            }
        } else if (auto inode = dynamic_cast<IfNode*>(layer.expr)) {
            if (layer.pc == 0) {
                layer.pc++;
                stack.push_back(Layer(layer.env, inode->cond.get()));
            } else if (layer.pc == 1) {
                layer.pc++;
                if (!holds<Integer>(heap[resultLoc])) {
                    panic("runtime", layer.expr->sl, "wrong cond type");
                }
                if (std::get<Integer>(heap[resultLoc]).value) {
                    stack.push_back(
                        Layer(layer.env, inode->branch1.get())
                    );
                } else {
                    stack.push_back(
                        Layer(layer.env, inode->branch2.get())
                    );
                }
            } else {
                // no need to update resultLoc: inherited
                stack.pop_back();
            }
        } else if (auto wnode = dynamic_cast<WhileNode*>(layer.expr)) {
            if (layer.pc == 0) {
                layer.pc++;
                stack.push_back(Layer(layer.env, wnode->cond.get()));
            } else if (layer.pc == 1) {
                if (!holds<Integer>(heap[resultLoc])) {
                    panic("runtime", layer.expr->sl, "wrong cond type");
                }
                if (std::get<Integer>(heap[resultLoc]).value) {
                    // loop
                    layer.pc = 0;
                    stack.push_back(
                        Layer(layer.env, wnode->body.get())
                    );
                } else {
                    resultLoc = _new<Void>();
                    stack.pop_back();
                }
            }
        } else if (auto cnode = dynamic_cast<CallNode*>(layer.expr)) {
            if (
                auto callee = dynamic_cast<IntrinsicNode*>(cnode->callee.get())
            ) {
                // unified argument recording
                if (layer.pc > 1 && layer.pc <= cnode->argList.size() + 1) {
                    std::get<std::vector<Location>>(layer.local["args"])
                        .push_back(resultLoc);
                }
                // initialization
                if (layer.pc == 0) {
                    layer.pc++;
                    layer.local["args"] = std::vector<Location>();
                // evaluate arguments
                } else if (layer.pc <= cnode->argList.size()) {
                    layer.pc++;
                    stack.push_back(Layer(
                        layer.env,
                        cnode->argList[layer.pc - 2].get()
                    ));
                // intrinsic call doesn't grow the stack
                } else {
                    auto value = _callIntrinsic(
                        layer.expr->sl,
                        callee->name,
                        // intrinsic call is pass by reference
                        std::get<std::vector<Location>>(layer.local["args"])
                    );
                    resultLoc = _moveNew(value);
                    stack.pop_back();
                }
            } else {
                // unified argument recording
                if (layer.pc > 2 && layer.pc <= cnode->argList.size() + 2) {
                    std::get<std::vector<Location>>(layer.local["args"])
                        .push_back(resultLoc);
                }
                // evaluate the callee
                if (layer.pc == 0) {
                    layer.pc++;
                    stack.push_back(Layer(
                        layer.env,
                        cnode->callee.get()
                    ));
                // initialization
                } else if (layer.pc == 1) {
                    layer.pc++;
                    layer.local["callee"] = resultLoc;
                    layer.local["args"] = std::vector<Location>();
                // evaluate arguments
                } else if (layer.pc <= cnode->argList.size() + 1) {
                    layer.pc++;
                    stack.push_back(Layer(
                        layer.env,
                        cnode->argList[layer.pc - 3].get()
                    ));
                // call
                } else if (layer.pc == cnode->argList.size() + 2) {
                    layer.pc++;
                    auto calleeLoc = std::get<Location>(layer.local["callee"]);
                    auto argsLoc = std::get<std::vector<Location>>(
                        layer.local["args"]
                    );
                    if (!std::holds_alternative<Closure>(heap[calleeLoc])) {
                        panic("runtime", layer.expr->sl, "non-callable");
                    }
                    auto &callee = std::get<Closure>(heap[calleeLoc]);
                    // types will be checked inside the closure call
                    if (argsLoc.size() != callee.fun->varList.size()) {
                        panic("runtime", layer.expr->sl, "wrong N of args");
                    }
                    int nArgs = argsLoc.size();
                    auto newEnv = callee.env;
                    for (int i = 0; i < nArgs; i++) {
                        // closure call is pass by reference
                        newEnv.push_back(std::make_pair(
                            callee.fun->varList[i]->name,
                            argsLoc[i]
                        ));
                    }
                    // evaluation of the closure body
                    stack.push_back(Layer(
                        // new frame has new env
                        std::make_shared<Env>(std::move(newEnv)),
                        callee.fun->expr.get(),
                        true
                    ));
                // finish
                } else {
                    // no need to update resultLoc: inherited
                    stack.pop_back();
                }
            }
        } else if (auto snode = dynamic_cast<SequenceNode*>(layer.expr)) {
            if (layer.pc < snode->exprList.size()) {
                layer.pc++;
                stack.push_back(Layer(
                    layer.env,
                    snode->exprList[layer.pc - 1].get()
                ));
            } else {
                // no need to update resultLoc: inherited
                stack.pop_back();
            }
        } else if (auto qnode = dynamic_cast<QueryNode*>(layer.expr)) {
            if (layer.pc == 0) {
                layer.pc++;
                stack.push_back(Layer(layer.env, qnode->expr.get()));
            } else {
                if (!holds<Closure>(heap[resultLoc])) {
                    panic("runtime", layer.expr->sl, "@ wrong type");
                }
                resultLoc = _new<Integer>(
                    lookup(
                        qnode->var->name,
                        std::get<Closure>(heap[resultLoc]).env
                    ).has_value() ? 1 : 0
                );
                stack.pop_back();
            }
        } else if (auto anode = dynamic_cast<AccessNode*>(layer.expr)) {
            if (layer.pc == 0) {
                layer.pc++;
                stack.push_back(Layer(layer.env, anode->expr.get()));
            } else {
                if (!holds<Closure>(heap[resultLoc])) {
                    panic("runtime", layer.expr->sl, "& wrong type");
                }
                auto loc = lookup(
                    anode->var->name,
                    std::get<Closure>(heap[resultLoc]).env
                );
                if (!loc.has_value()) {
                    panic("runtime", layer.expr->sl, "undefined variable");
                }
                resultLoc = loc.value();
                stack.pop_back();
            }
        } else {
            panic("runtime", layer.expr->sl, "unrecognized AST node");
        }
        return true;
    }
    void execute() {
        int ctr = 0;
        while (step()) {
            ctr++;
            if (ctr && (ctr % GC_INTERVAL == 0)) {
                std::cerr << "[note] GC collected: " << _gc() << "\n";
            }
        }
    }
    Value getResult() {
        return heap[resultLoc];
    }
private:
    // intrinsic dispatch
    Value _callIntrinsic(
        SourceLocation sl,
        const std::string &name,
        const std::vector<Location> &args
    ) {
        if (name == ".void") {
            if (!(args.size() == 0)) {
                panic("runtime", sl, "type error on intrinsic call");
            }
            return Void();
        } else if (name == ".+") {
            if (
                !(args.size() == 2 &&
                holds<Integer, Integer>(heap[args[0]], heap[args[1]]))
            ) {
                panic("runtime", sl, "type error on intrinsic call");
            }
            return Integer(
                std::get<Integer>(heap[args[0]]).value +
                std::get<Integer>(heap[args[1]]).value
            );
        } else if (name == ".-") {
            if (
                !(args.size() == 2 &&
                holds<Integer, Integer>(heap[args[0]], heap[args[1]]))
            ) {
                panic("runtime", sl, "type error on intrinsic call");
            }
            return Integer(
                std::get<Integer>(heap[args[0]]).value -
                std::get<Integer>(heap[args[1]]).value
            );
        } else if (name == ".*") {
            if (
                !(args.size() == 2 &&
                holds<Integer, Integer>(heap[args[0]], heap[args[1]]))
            ) {
                panic("runtime", sl, "type error on intrinsic call");
            }
            return Integer(
                std::get<Integer>(heap[args[0]]).value *
                std::get<Integer>(heap[args[1]]).value
            );
        } else if (name == "./") {
            if (
                !(args.size() == 2 &&
                holds<Integer, Integer>(heap[args[0]], heap[args[1]]))
            ) {
                panic("runtime", sl, "type error on intrinsic call");
            }
            return Integer(
                std::get<Integer>(heap[args[0]]).value /
                std::get<Integer>(heap[args[1]]).value
            );
        } else if (name == ".%") {
            if (
                !(args.size() == 2 &&
                holds<Integer, Integer>(heap[args[0]], heap[args[1]]))
            ) {
                panic("runtime", sl, "type error on intrinsic call");
            }
            return Integer(
                std::get<Integer>(heap[args[0]]).value %
                std::get<Integer>(heap[args[1]]).value
            );
        } else if (name == ".<") {
            if (
                !(args.size() == 2 &&
                holds<Integer, Integer>(heap[args[0]], heap[args[1]]))
            ) {
                panic("runtime", sl, "type error on intrinsic call");
            }
            return Integer(
                std::get<Integer>(heap[args[0]]).value <
                std::get<Integer>(heap[args[1]]).value ? 1 : 0
            );
        } else if (name == ".slen") {
            if (!(args.size() == 1 && holds<String>(heap[args[0]]))) {
                panic("runtime", sl, "type error on intrinsic call");
            }
            return Integer(
                std::get<String>(heap[args[0]]).value.size()
            );
        } else if (name == ".ssub") {
            if (!(
                args.size() == 3 &&
                holds<String, Integer, Integer>(
                    heap[args[0]], heap[args[1]], heap[args[2]]
                )
            )) {
                panic("runtime", sl, "type error on intrinsic call");
            }
            return String(
                std::get<String>(heap[args[0]]).value.substr(
                    std::get<Integer>(heap[args[1]]).value,
                    std::get<Integer>(heap[args[2]]).value - 
                    std::get<Integer>(heap[args[1]]).value
                )
            );
        } else if (name == ".s+") {
            if (!(
                args.size() == 2 &&
                holds<String, String>(heap[args[0]], heap[args[1]])
            )) {
                panic("runtime", sl, "type error on intrinsic call");
            }
            return String(
                std::get<String>(heap[args[0]]).value +
                std::get<String>(heap[args[1]]).value
            );
        } else if (name == ".s<") {
            if (!(
                args.size() == 2 &&
                holds<String, String>(heap[args[0]], heap[args[1]])
            )) {
                panic("runtime", sl, "type error on intrinsic call");
            }
            return Integer(
                std::get<String>(heap[args[0]]).value <
                std::get<String>(heap[args[1]]).value ? 1 : 0
            );
        } else if (name == ".i->s") {
            if (!(
                args.size() == 1 && holds<Integer>(heap[args[0]])
            )) {
                panic("runtime", sl, "type error on intrinsic call");
            }
            return String(
                std::to_string(std::get<Integer>(heap[args[0]]).value)
            );
        } else if (name == ".s->i") {
            if (!(
                args.size() == 1 && holds<String>(heap[args[0]])
            )) {
                panic("runtime", sl, "type error on intrinsic call");
            }
            return Integer(
                std::stoi(std::get<String>(heap[args[0]]).value)
            );
        } else if (name == ".v?") {
            if (!(args.size() == 1)) {
                panic("runtime", sl, "type error on intrinsic call");
            }
            return Integer(
                holds<Void>(heap[args[0]]) ? 1 : 0
            );
        } else if (name == ".i?") {
            if (!(args.size() == 1)) {
                panic("runtime", sl, "type error on intrinsic call");
            }
            return Integer(
                holds<Integer>(heap[args[0]]) ? 1 : 0
            );
        } else if (name == ".s?") {
            if (!(args.size() == 1)) {
                panic("runtime", sl, "type error on intrinsic call");
            }
            return Integer(
                holds<String>(heap[args[0]]) ? 1 : 0
            );
        } else if (name == ".c?") {
            if (!(args.size() == 1)) {
                panic("runtime", sl, "type error on intrinsic call");
            }
            return Integer(
                holds<Closure>(heap[args[0]]) ? 1 : 0
            );
        } else {
            panic("runtime", sl, "unrecognized intrinsic call");
            return Void();
        }
    }
    // memory management
    template <typename V, typename... Args>
    requires isAlternativeOf<V, Value>::value
    Location _new(Args&&... args) {
        heap.push_back(V(std::forward<Args>(args)...));
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
            [this, &visited, &traverseLocation](Location loc) {
            if (!(visited.contains(loc))) {
                visited.insert(loc);
                if (std::holds_alternative<Closure>(heap[loc])) {
                    for (
                        const auto &[_, l] : std::get<Closure>(heap[loc]).env
                    ) {
                        traverseLocation(l);
                    }
                }
            }
        };
        // tarverse the stack
        for (const auto &layer : stack) {
            if (layer.isFrame()) {
                for (const auto &[_, loc] : (*(layer.env))) {
                    traverseLocation(loc);
                }
            }
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
        return std::make_pair(removed, relocation);
    }
    void _relocate(const std::unordered_map<Location, Location> &relocation) {
        for (auto &v : heap) {
            if (std::holds_alternative<Closure>(v)) {
                auto &c = std::get<Closure>(v);
                for (auto &[_, loc] : c.env) {
                    if (relocation.contains(loc)) {
                        loc = relocation.at(loc);
                    }
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
    // fields
    Stack stack;
    Heap heap;
    Location resultLoc;
};

const std::unordered_map<std::string, std::string> tests = {
{
R"(
letrec (
    leaf = lambda () lambda () 0
    node = lambda (value left right) lambda () 1
    # in-order DFS
    dfs = lambda (tree)
        if (.< (tree) 1)
        ""
        (.s+ (.s+ (dfs &left tree) &value tree) (dfs &right tree))
)
(dfs
    (node "4"
        (node "2"
            (node "1" (leaf) (leaf))
            (node "3" (leaf) (leaf)))
        (node "5" (leaf) (leaf))))
)"
,
"12345"
}
,
{
R"(
letrec (
  x = ""
  r = ""
  change = lambda (var val) set var val
)
[
  set x "a"
  set r (.s+ r x)
  (change x "b")
  set r (.s+ r x)
  letrec (z = x) set z "c"
  set r (.s+ r x)
  r
]
)"
,
"abb"
}
};

void test() {
    int i = 0;
    for (const auto &[source, result] : tests) {
        auto tokens = lex(source);
        auto expr = parse(std::move(tokens));
        State state(expr.get());
        state.execute();
        auto r = valueToString(state.getResult());
        if (r == result) {
            std::cout << "Passed test " << ++i << "\n";
        } else {
            std::cout << "Failed test " << ++i << "\n";
        }
    }
}

int main() {
    test();
}