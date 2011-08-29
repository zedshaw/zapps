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


from string import *
import re
from zapps.rt import *

class StackishParserScanner(Scanner):
    patterns = [
        ('":"', re.compile(':')),
        ('"\'"', re.compile("'")),
        ('[ \t\r]+', re.compile('[ \t\r]+')),
        ('NUMBER', re.compile('[0-9]+')),
        ('FLOAT', re.compile('[\\-+]([0-9]+)?\\.[0-9]+')),
        ('STRING', re.compile('"[^"]*"')),
        ('START', re.compile('\\[')),
        ('WORD', re.compile('[a-zA-Z]+[a-zA-Z0-9\\-_.:]*')),
        ('ATTRIB', re.compile('@[a-zA-Z]+[a-zA-Z0-9\\-_.:]*')),
        ('GROUP', re.compile('\\]')),
        ('END', re.compile('\\n')),
        ('PACK', re.compile('[xcbBhHiIlLqQfdspP0-9]+')),
    ]
    def __init__(self, str):
        Scanner.__init__(self,None,['[ \t\r]+'],str)

class StackishParser(Parser):
    def blob(self):
        self._scan('"\'"')
        _token_ = self._peek('NUMBER', 'PACK')
        if _token_ == 'NUMBER':
            NUMBER = self._scan('NUMBER')
            pack = None; count = atoi(NUMBER)
        else:# == 'PACK'
            PACK = self._scan('PACK')
            pack = PACK; count = struct.calcsize(PACK)
        self._scan('":"')
        chunk = self._eat(count)
        self._scan('"\'"')
        x = BLOB(chunk) ; x.pack = pack; return x

    def data(self, results):
        _token_ = self._peek('FLOAT', 'NUMBER', 'STRING', '"\'"', 'ATTRIB')
        if _token_ == 'FLOAT':
            FLOAT = self._scan('FLOAT')
            results.append(atof(FLOAT))
        elif _token_ == 'NUMBER':
            NUMBER = self._scan('NUMBER')
            results.append(atoi(NUMBER))
        elif _token_ == 'STRING':
            STRING = self._scan('STRING')
            results.append(STRING[1:-1])
        elif _token_ == '"\'"':
            blob = self.blob()
            results.append(blob)
        else:# == 'ATTRIB'
            ATTRIB = self._scan('ATTRIB')
            value = results.pop(); value.reverse(); results.append({ATTRIB: value})

    def structure(self, results,current):
        _token_ = self._peek('WORD', 'GROUP')
        if _token_ == 'WORD':
            WORD = self._scan('WORD')
            current.reverse(); results.append({WORD: current})
        else:# == 'GROUP'
            GROUP = self._scan('GROUP')
            results.append(current)

    def header(self):
        return self._unpack('H')

    def node(self, results):
        START = self._scan('START')
        current = []
        while self._peek('FLOAT', 'NUMBER', 'STRING', '"\'"', 'ATTRIB', 'WORD', 'GROUP', 'START', 'END') not in ['WORD', 'GROUP', 'END']:
            _token_ = self._peek('FLOAT', 'NUMBER', 'STRING', '"\'"', 'ATTRIB', 'START')
            if _token_ != 'START':
                data = self.data(current)
            else:# == 'START'
                node = self.node(current)
        structure = self.structure(results,current)

    def stackish(self):
        header = self.header()
        print "%s long" % repr(header) ; results = []
        while 1:
            node = self.node(results)
            if self._peek('START', 'END', 'FLOAT', 'NUMBER', 'STRING', '"\'"', 'ATTRIB', 'WORD', 'GROUP') != 'START': break
        END = self._scan('END')
        return results


def parse(rule, text):
    P = StackishParser(StackishParserScanner(text))
    return wrap_error_reporter(P, rule)




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
