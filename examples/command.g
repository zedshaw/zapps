# A Yapps2 parser that handles your typical IRC style command/message input
# but includes arguments in the command parsing so.  Next step is to build the
# command system and have this create them on the fly.
#
# Copyright (C) Zed A. Shaw, licensed under the GPL 3 for the Utu project ( http://www.savingtheinternetwithhate.com )

%%
parser CommandParser:
    ignore: "[ \t]+"
    token NUMBER: "[0-9]+"
    token STRING: "\".*\""
    token FLOAT: "[0-9]+\.[0-9]+"
    token ID: "[a-zA-Z]+"
    token END: "\n"
    token START: "/"
    token MESSAGE: "[^/].*"
    token END: "\n"

    rule arg: ID {{ return ID }} 
       | NUMBER {{ return atoi(NUMBER) }} 
       | FLOAT {{ return atof(FLOAT) }} 
       | STRING {{ return STRING }} 

    rule parameters<<PARAMS>>: (arg {{ PARAMS.append(arg) }} )* 
    rule command: "/" ID {{ cmd = [ID] ; params = [] }} parameters<<params>> END {{ cmd.append(params); return cmd }}
    rule message: MESSAGE END {{ return MESSAGE }}

    rule input: ( command {{ return command }} | message {{ return message }})+ 
%%

if __name__=='__main__':
    while 1:
        try: s = raw_input('>>> ')
	except EOFError: break
        if not s: break
        print parse('input', s + "\n")
    print 'Bye.'


