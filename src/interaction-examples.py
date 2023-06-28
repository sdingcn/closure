import exprscript as es

if __name__ == '__main__':

    # call ExprScript function from Python
    code = '(.reg "plus1" lambda (x) { (.+ x 1) })'
    state = es.State(es.parse(es.lex(code)))
    print(state.execute().call_expr_function("plus1", [-6])) # -5

    # call Python function from ExprScript
    code = '(.py "rev" (.str+ "na" "me"))'
    state = es.State(es.parse(es.lex(code)))
    print(state.register_python_function("rev", lambda s: s[::-1]).execute().value.value) # "eman"