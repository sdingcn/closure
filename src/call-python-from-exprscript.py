import exprscript as es

if __name__ == '__main__':
    code = '(.py "upper_reverse" (.str+ "na" "me"))'
    state = es.State(es.parse(es.lex(code)))

    def upper_reverse(s: str) -> str:
        return s.upper()[::-1]

    state.register_py_function(upper_reverse)
    es.execute(state)
    print(state.value.value)
