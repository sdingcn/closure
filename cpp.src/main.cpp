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

    SourceLocation sl;
};

struct IntegerNode : public ExprNode {
    IntegerNode(SourceLocation s, int v): ExprNode(s), val(v) {}

    int val;
};

struct StringNode : public ExprNode {
    StringNode(SourceLocation s, std::string v): ExprNode(s), val(std::move(v)) {}

    std::string val;
};

struct IntrinsicNode : public ExprNode {
    IntrinsicNode(SourceLocation s, std::string n): ExprNode(s), name(std::move(n)) {}

    std::string name;
};

struct VariableNode : public ExprNode {
    VariableNode(SourceLocation s, std::string n): ExprNode(s), name(std::move(n)) {}

    std::string name;
};

struct SetNode : public ExprNode {
    SetNode(SourceLocation s, std::unique_ptr<VariableNode> v, std::unique_ptr<ExprNode> e):
        ExprNode(s), var(std::move(v)), expr(std::move(e)) {}

    std::unique_ptr<VariableNode> var;
    std::unique_ptr<ExprNode> expr;
};

struct LambdaNode : public ExprNode {
    LambdaNode(SourceLocation s, std::vector<std::unique_ptr<VariableNode>> v, std::unique_ptr<ExprNode> e):
        ExprNode(s), varList(std::move(v)), expr(std::move(e)) {}

    std::vector<std::unique_ptr<VariableNode>> varList;
    std::unique_ptr<ExprNode> expr;
};

struct LetrecNode : public ExprNode {
    LetrecNode(
        SourceLocation s,
        std::vector<std::pair<std::unique_ptr<VariableNode>, std::unique_ptr<ExprNode>>> v,
        std::unique_ptr<ExprNode> e
    ): ExprNode(s), varExprList(std::move(v)), expr(std::move(e)) {}
    
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

    std::unique_ptr<ExprNode> cond;
    std::unique_ptr<ExprNode> branch1;
    std::unique_ptr<ExprNode> branch2;
};

struct WhileNode : public ExprNode {
    WhileNode(SourceLocation s, std::unique_ptr<ExprNode> c, std::unique_ptr<ExprNode> b):
        ExprNode(s), cond(std::move(c)), body(std::move(b)) {}

    std::unique_ptr<ExprNode> cond;
    std::unique_ptr<ExprNode> body;
};

struct CallNode : public ExprNode {
    CallNode(
        SourceLocation s,
        std::unique_ptr<ExprNode> c,
        std::vector<std::unique_ptr<ExprNode>> a
    ): ExprNode(s), callee(std::move(c)), argList(std::move(a)) {}

    std::unique_ptr<ExprNode> callee;
    std::vector<std::unique_ptr<ExprNode>> argList;
};

struct SequenceNode : public ExprNode {
    SequenceNode(
        SourceLocation s,
        std::vector<std::unique_ptr<ExprNode>> e
    ): ExprNode(s), exprList(std::move(e)) {}

    std::vector<std::unique_ptr<ExprNode>> exprList;
};

struct QueryNode : public ExprNode {
    QueryNode(
        SourceLocation s,
        std::unique_ptr<VariableNode> v,
        std::unique_ptr<ExprNode> e
    ): ExprNode(s), var(std::move(v)), expr(std::move(e)) {}

    std::unique_ptr<VariableNode> var;
    std::unique_ptr<ExprNode> expr;
};

struct AccessNode : public ExprNode {
    AccessNode(
        SourceLocation s,
        std::unique_ptr<VariableNode> v,
        std::unique_ptr<ExprNode> e
    ): ExprNode(s), var(std::move(v)), expr(std::move(e)) {}

    std::unique_ptr<VariableNode> var;
    std::unique_ptr<ExprNode> expr;
};

int main() {
}