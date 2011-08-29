# This parser tests the use of OR clauses with one of them being empty

parser Test:
    rule R: ( A | ) 'c'
    rule A: 'a'+
