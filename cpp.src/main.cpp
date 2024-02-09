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

// helpers

struct SourceLocation {
    SourceLocation(int l = 1, int c = 1) : line(l), column(c) {
    }
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
    Token(SourceLocation l, std::string r) : sl(l), src(std::move(r)) {}

    SourceLocation sl;
    std::string src;
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
        std::string src = "";
        // integer literal
        if (std::isdigit(source.back()) || source.back() == '-' || source.back() == '+') {
            if (source.back() == '-' || source.back() == '+') {
                src += source.back();
                source.pop_back();
                sl.update(src.back());
            }
            while (source.size() && std::isdigit(source.back())) {
                src += source.back();
                source.pop_back();
                sl.update(src.back());
            }
        // variable / keyword
        } else if (std::isalpha(source.back())) {
            while (source.size() && (std::isalpha(source.back()) || std::isdigit(source.back()) || source.back() == '_')) {
               src += source.back();
               source.pop_back();
               sl.update(src.back()); 
            }
        // intrinsic
        } else if (source.back() == '.') {
            while (source.size() && !(std::isspace(source.back()) || source.back() == ')')) {
                src += source.back();
                source.pop_back();
                sl.update(src.back());
            }
        // special symbol
        } else if (std::string("()[]=@&").find(source.back()) != std::string::npos) {
            src += source.back();
            source.pop_back();
            sl.update(src.back());
        // string literal
        } else if (source.back() == '"') {
            src += source.back();
            source.pop_back();
            sl.update(src.back());
            while (source.size() && (source.back() != '"' || (source.back() == '"' && countTrailingEscape(src) % 2 != 0))) {
                src += source.back();
                source.pop_back();
                sl.update(src.back());
            }
            if (source.size() && source.back() == '"') {
                src += source.back();
                source.pop_back();
                sl.update(src.back());
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
        return Token(start_sl, std::move(src));
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

int main() {
}