import exprscript as es

if __name__ == '__main__':

    # call ExprScript function from Python
    state = es.State(es.parse(es.lex('(.reg "plus1" lambda (x) { (.+ x 1) })')))
    print(state.execute().call_expr_function("plus1", [-6])) # -5

    # call Python function from ExprScript
    state = es.State(es.parse(es.lex('(.py "rev" (.str+ "na" "me"))')))
    print(state.register_python_function("rev", lambda s: s[::-1]).execute().value.value) # "eman"
