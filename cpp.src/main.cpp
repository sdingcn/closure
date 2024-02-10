#include <deque>
#include <utility>
#include <string>
#include <format>
#include <stdexcept>
#include <unordered_set>
#include <algorithm>
#include <optional>
#include <cctype>
#include <functional>
#include <memory>
#include <vector>

// helpers

struct SourceLocation {
    SourceLocation(int l = 1, int c = 1): line(l), column(c) {}
    std::string toString() const {
        if (line <= 0 || column <= 0) {
            return "(SourceLocation N/A)";
        }
        return std::format("(SourceLocation {} {})", line, column);
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

void throwError(const std::string &type, const SourceLocation &sl, const std::string &msg) {
    throw std::runtime_error(std::format("[{} error {}] {}", type, sl.toString(), msg));
}

// lexer

struct Token {
    Token(SourceLocation s, std::string t) : sl(s), text(std::move(t)) {}

    SourceLocation sl;
    std::string text;
};

std::deque<Token> lex(std::string source) {
    static std::string charstr = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789`~!@#$%^&*()-_=+[{]}\\|;:'\",<.>/? \t\n";
    static std::unordered_set<char> charset(charstr.begin(), charstr.end());
    SourceLocation sl;
    for (auto c : source) {
        if (!charset.contains(c)) {
            throwError("lexer", sl, "unsupported character");
        }
        sl.update(c);
    }
    sl.revert();

    auto countTrailingEscape = [](const std::string &s) -> int {
        int cnt = 0;
        int pos = s.size() - 1;
        while (pos >= 0 && s[pos] == '\\') {
            cnt++;
            pos--;
        }
        return cnt;
    };

    std::reverse(source.begin(), source.end());
    std::function<std::optional<Token>()> nextToken =
    [&source, &sl, &countTrailingEscape, &nextToken]() -> std::optional<Token> {
        // skip whitespaces
        while (source.size() && std::isspace(source.back())) {
            sl.update(source.back());
            source.pop_back();
        }
        if (!source.size()) {
            return std::nullopt;
        }
        // read the next token
        auto start_sl = sl;
        std::string text = "";
        // integer literal
        if (std::isdigit(source.back()) || source.back() == '-' || source.back() == '+') {
            if (source.back() == '-' || source.back() == '+') {
                text += source.back();
                source.pop_back();
                sl.update(text.back());
            }
            while (source.size() && std::isdigit(source.back())) {
                text += source.back();
                source.pop_back();
                sl.update(text.back());
            }
        // variable / keyword
        } else if (std::isalpha(source.back())) {
            while (source.size() && (std::isalpha(source.back()) || std::isdigit(source.back()) || source.back() == '_')) {
               text += source.back();
               source.pop_back();
               sl.update(text.back()); 
            }
        // intrinsic
        } else if (source.back() == '.') {
            while (source.size() && !(std::isspace(source.back()) || source.back() == ')')) {
                text += source.back();
                source.pop_back();
                sl.update(text.back());
            }
        // special symbol
        } else if (std::string("()[]=@&").find(source.back()) != std::string::npos) {
            text += source.back();
            source.pop_back();
            sl.update(text.back());
        // string literal
        } else if (source.back() == '"') {
            text += source.back();
            source.pop_back();
            sl.update(text.back());
            while (source.size() && (source.back() != '"' || (source.back() == '"' && countTrailingEscape(text) % 2 != 0))) {
                text += source.back();
                source.pop_back();
                sl.update(text.back());
            }
            if (source.size() && source.back() == '"') {
                text += source.back();
                source.pop_back();
                sl.update(text.back());
            } else {
                throwError("lexer", sl, "incomplete string literal");
            }
        // comment
        } else if (source.back() == '#') {
            sl.update(source.back());
            source.pop_back();
            while (source.size() && source.back() != '\n') {
                sl.update(source.back());
                source.pop_back();
            }
            // nextToken() will consume the \n and recursively continue
            return nextToken();
        } else {
            throwError("lexer", sl, "unsupported starting character");
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
    StringNode(SourceLocation s, std::string v): ExprNode(s), val(std::move(v)) {}
    StringNode(const StringNode &) = delete;
    StringNode &operator=(const StringNode &) = delete;
    virtual ~StringNode() override {}

    std::string val;
};

struct IntrinsicNode : public ExprNode {
    IntrinsicNode(SourceLocation s, std::string n): ExprNode(s), name(std::move(n)) {}
    IntrinsicNode(const IntrinsicNode &) = delete;
    IntrinsicNode &operator=(const IntrinsicNode &) = delete;
    virtual ~IntrinsicNode() override {}

    std::string name;
};

struct VariableNode : public ExprNode {
    VariableNode(SourceLocation s, std::string n): ExprNode(s), name(std::move(n)) {}
    VariableNode(const VariableNode &) = delete;
    VariableNode &operator=(const VariableNode &) = delete;
    virtual ~VariableNode() override {}

    std::string name;
};

struct SetNode : public ExprNode {
    SetNode(SourceLocation s, std::unique_ptr<VariableNode> v, std::unique_ptr<ExprNode> e):
        ExprNode(s), var(std::move(v)), expr(std::move(e)) {}
    SetNode(const SetNode &) = delete;
    SetNode &operator=(const SetNode &) = delete;
    virtual ~SetNode() override {}

    std::unique_ptr<VariableNode> var;
    std::unique_ptr<ExprNode> expr;
};

struct LambdaNode : public ExprNode {
    LambdaNode(SourceLocation s, std::vector<std::unique_ptr<VariableNode>> v, std::unique_ptr<ExprNode> e):
        ExprNode(s), varList(std::move(v)), expr(std::move(e)) {}
    LambdaNode(const LambdaNode &) = delete;
    LambdaNode &operator=(const LambdaNode &) = delete;
    virtual ~LambdaNode() override {}

    std::vector<std::unique_ptr<VariableNode>> varList;
    std::unique_ptr<ExprNode> expr;
};

struct LetrecNode : public ExprNode {
    LetrecNode(
        SourceLocation s,
        std::vector<std::pair<std::unique_ptr<VariableNode>, std::unique_ptr<ExprNode>>> v,
        std::unique_ptr<ExprNode> e
    ): ExprNode(s), varExprList(std::move(v)), expr(std::move(e)) {}
    LetrecNode(const LetrecNode &) = delete;
    LetrecNode &operator=(const LetrecNode &) = delete;
    virtual ~LetrecNode() override {}
    
    std::vector<std::pair<std::unique_ptr<VariableNode>, std::unique_ptr<ExprNode>>> varExprList;
    std::unique_ptr<ExprNode> expr;
};

struct IfNode : public ExprNode {
    IfNode(
        SourceLocation s,
        std::unique_ptr<ExprNode> c,
        std::unique_ptr<ExprNode> b1,
        std::unique_ptr<ExprNode> b2
    ): ExprNode(s), cond(std::move(c)), branch1(std::move(b1)), branch2(std::move(b2)) {}
    IfNode(const IfNode &) = delete;
    IfNode &operator=(const IfNode &) = delete;
    virtual ~IfNode() override {}

    std::unique_ptr<ExprNode> cond;
    std::unique_ptr<ExprNode> branch1;
    std::unique_ptr<ExprNode> branch2;
};

struct WhileNode : public ExprNode {
    WhileNode(SourceLocation s, std::unique_ptr<ExprNode> c, std::unique_ptr<ExprNode> b):
        ExprNode(s), cond(std::move(c)), body(std::move(b)) {}
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

std::unique_ptr<ExprNode> parse(std::deque<Token> &tokens) {
    auto isNumberToken = [](const Token &token) {
        return token.text.size() > 0 &&
            (std::isdigit(token.text[0]) || token.text[0] == '-' || token.text[0] == '+');
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

    auto consume = [&tokens]<typename Callable>(const Callable &predicate) -> Token {
        if (tokens.size() == 0) {
            throwError("parser", SourceLocation(-1, -1), "incomplete token stream");
        }
        auto token = tokens.front();
        tokens.pop_front();
        if (!predicate(token)) {
            throwError("parser", token.sl, "unexpected token");
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
                        throwError("parser", token.sl, "unsupported escape sequence");
                    }
                } else {
                    throwError("parser", token.sl, "incomplete escape sequence");
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
        return std::make_unique<SetNode>(start.sl, std::move(var), std::move(expr));
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
        return std::make_unique<LambdaNode>(start.sl, std::move(varList), std::move(expr));
    };
    parseLetrec = [&]() -> std::unique_ptr<LetrecNode> {
        auto start = consume(isToken("letrec"));
        consume(isToken("("));
        std::vector<std::pair<std::unique_ptr<VariableNode>, std::unique_ptr<ExprNode>>> varExprList;
        while (tokens.size() && isVariableToken(tokens[0])) {
            auto v = parseVariable();
            consume(isToken("="));
            auto e = parseExpr();
            varExprList.emplace_back(std::move(v), std::move(e));
        }
        consume(isToken(")"));
        auto expr = parseExpr();
        return std::make_unique<LetrecNode>(start.sl, std::move(varExprList), std::move(expr));
    };
    parseIf = [&]() -> std::unique_ptr<IfNode> {
        auto start = consume(isToken("if"));
        auto cond = parseExpr();
        auto branch1 = parseExpr();
        auto branch2 = parseExpr();
        return std::make_unique<IfNode>(start.sl, std::move(cond), std::move(branch1), std::move(branch2));
    };
    parseWhile = [&]() -> std::unique_ptr<WhileNode> {
        auto start = consume(isToken("while"));
        auto cond = parseExpr();
        auto body = parseExpr();
        return std::make_unique<WhileNode>(start.sl, std::move(cond), std::move(body));
    };
    parseVariable = [&]() -> std::unique_ptr<VariableNode> {
        auto token = consume(isVariableToken);
        return std::make_unique<VariableNode>(token.sl, std::move(token.text));
    };
    parseCall = [&]() -> std::unique_ptr<CallNode> {
        auto start = consume(isToken("("));
        if (!tokens.size()) {
            throwError("parser", start.sl, "incomplete tokens stream");
        }
        std::unique_ptr<ExprNode> callee = isIntrinsicToken(tokens[0]) ? parseIntrinsic() : parseExpr();
        std::vector<std::unique_ptr<ExprNode>> argList;
        while (tokens.size() && tokens[0].text != ")") {
            argList.push_back(parseExpr());
        }
        consume(isToken(")"));
        return std::make_unique<CallNode>(start.sl, std::move(callee), std::move(argList));
    };
    parseSequence = [&]() -> std::unique_ptr<SequenceNode> {
        auto start = consume(isToken("["));
        std::vector<std::unique_ptr<ExprNode>> exprList;
        while (tokens.size() && tokens[0].text != "]") {
            exprList.push_back(parseExpr());
        }
        if (!exprList.size()) {
            throwError("parser", start.sl, "zero-length sequence");
        }
        consume(isToken("]"));
        return std::make_unique<SequenceNode>(start.sl, std::move(exprList));
    };
    parseQuery = [&]() -> std::unique_ptr<QueryNode> {
        auto start = consume(isToken("@"));
        auto var = parseVariable();
        auto expr = parseExpr();
        return std::make_unique<QueryNode>(start.sl, std::move(var), std::move(expr));
    };
    parseAccess = [&]() -> std::unique_ptr<AccessNode> {
        auto start = consume(isToken("&"));
        auto var = parseVariable();
        auto expr = parseExpr();
        return std::make_unique<AccessNode>(start.sl, std::move(var), std::move(expr));
    };
    parseExpr = [&]() -> std::unique_ptr<ExprNode> {
        if (!tokens.size()) {
            throwError("parser", SourceLocation(-1, -1), "incomplete token stream");
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
            throwError("parser", tokens[0].sl, "unrecognized token");
            return nullptr;
        }
    };

    auto expr = parseExpr();
    if (tokens.size()) {
        throwError("parser", tokens[0].sl, "redundant token(s)");
    }
    return expr;
}

int main() {
}