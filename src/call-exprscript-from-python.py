import exprscript as es

if __name__ == '__main__':
    code = 'letrec (g = lambda (a b) { if (.not b) then a else (g b (.% a b)) }) { (.reg "gcd" g) }'
    state = es.State(es.parse(es.lex(code)))
    es.execute(state)
    print(es.call_expr_function(state, "gcd", [45, 60]))
