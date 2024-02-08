#include <deque>
#include <utility>
#include <string>
#include <format>
#include <stdexcept>

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

struct Token {
    Token(SourceLocation l, std::string r) : sl(l), src(std::move(r)) {}

    SourceLocation sl;
    std::string src;
};

std::deque<Token> lex(std::string source) {
    std::deque<Token> tokens;
    return tokens;
}

int main() {
}