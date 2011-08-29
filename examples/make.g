# Copyright (C) Zed A. Shaw, licensed under the GPL 3 for the Utu project ( http://www.savingtheinternetwithhate.com )

%%
parser MakeParser:
    ignore: "[ \t\r]+"
    token NUMBER: "[0-9]+"
    token STRING: '\'([^\\n\'\\\\]|\\\\.)*\'|"([^\\n"\\\\]|\\\\.)*"'
    token ID: "[a-zA-Z][a-zA-Z\-_0-9]+"
    token IMPORT: "import"
    token EXPORT: "export"
    token DO: "do"
    token TEST_EXPR: "[^}]"
    token CODE_EXPR: "[^\\n][^\\n]\\n\\n"

    rule DO ID Type ":"
        STRING Depends Tests Code

    rule Type: "(" ID ")"
    rule Depends: "[" (ID)* "]"
    rule Tests: "{" TEST_EXPR "}"
    rule Code: ( CODE_EXPR )*

%%

if __name__=='__main__':
    import sys

    file = open(sys.argv[1])

    text = file.read() + "\n\n"
    file.close()

    doc = parse('Document', text)
    print doc
    print repr(text)
