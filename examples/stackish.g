# Zapps (yapps2 plus my mods) parser for the Stackish XML alternative data language.
#
# Copyright (C) Zed A. Shaw, licensed under the GPL 3 for the Utu project ( http://www.savingtheinternetwithhate.com )

import struct

class BLOB(str):
    def __repr__(self):
        if self.pack:
            return repr(self.unpack())
        else:
            return str.__repr__(self)

    def unpack(self):
        if self.pack:
            return struct.unpack(self.pack, self)
        else:
            raise "You can't unpack this BLOB"

%%
parser StackishParser:
    ignore: "[ \t\r]+"
    token NUMBER: "[0-9]+"
    token FLOAT:  "[\\-+]([0-9]+)?\\.[0-9]+"
    token STRING: "\"[^\"]*\""
    token START: "\\["
    token WORD:  "[a-zA-Z]+[a-zA-Z0-9\\-_.:]*"
    token ATTRIB:  "@[a-zA-Z]+[a-zA-Z0-9\\-_.:]*"
    token GROUP:  "\\]"
    token END: "\\n"
    token PACK: '[xcbBhHiIlLqQfdspP0-9]+'

    rule blob: "'" ( NUMBER {{ pack = None; count = atoi(NUMBER) }} | PACK {{ pack = PACK; count = struct.calcsize(PACK) }} )
        ":" {{ chunk = self._eat(count) }} "'" {{ x = BLOB(chunk) ; x.pack = pack; return x }}

    rule data<<results>>:
        FLOAT    {{ results.append(atof(FLOAT)) }}
        | NUMBER {{ results.append(atoi(NUMBER)) }}
        | STRING {{ results.append(STRING[1:-1]) }}
        | blob   {{ results.append(blob) }}
        | ATTRIB {{ value = results.pop(); value.reverse(); results.append({ATTRIB: value}) }}

    rule structure<<results,current>>:
        WORD 
        {{ current.reverse(); results.append({WORD: current}) }}
        | 
        GROUP  
        {{ results.append(current) }}

    rule header: //H//

    rule node<<results>>: 
       START {{ current = [] }} ( data<<current>> | node<<current>> )* structure<<results,current>> 

    rule stackish: 
        header {{ print "%s long" % repr(header) ; results = [] }} 
        ( node<<results>> )+ 
        END {{ return results }}
%%

if __name__=='__main__':
    while 1:
        try: 
            s = raw_input('>>> ')
        except EOFError: 
            break
        if not s: break

        # make it have the header tooa
        s += "\n"
        s = struct.pack('H', len(s)) + s
        print "Parsing: %s" % repr(s)
        print parse('stackish', s)

    print 'Bye.'
