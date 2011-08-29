# A Yapps2 parser that handles your typical IRC style command/message input
# but includes arguments in the command parsing so.  Next step is to build the
# command system and have this create them on the fly.
#
# Copyright (C) Zed A. Shaw, licensed under the GPL 3 for the Utu project ( http://www.savingtheinternetwithhate.com )


from string import *
import re
from zapps.rt import *

class CommandParserScanner(Scanner):
    patterns = [
        ('"/"', re.compile('/')),
        ('[ \t]+', re.compile('[ \t]+')),
        ('NUMBER', re.compile('[0-9]+')),
        ('STRING', re.compile('".*"')),
        ('FLOAT', re.compile('[0-9]+\\.[0-9]+')),
        ('ID', re.compile('[a-zA-Z]+')),
        ('END', re.compile('\n')),
        ('START', re.compile('/')),
        ('MESSAGE', re.compile('[^/].*')),
        ('END', re.compile('\n')),
    ]
    def __init__(self, str):
        Scanner.__init__(self,None,['[ \t]+'],str)

class CommandParser(Parser):
    def arg(self):
        _token_ = self._peek('ID', 'NUMBER', 'FLOAT', 'STRING')
        if _token_ == 'ID':
            ID = self._scan('ID')
            return ID
        elif _token_ == 'NUMBER':
            NUMBER = self._scan('NUMBER')
            return atoi(NUMBER)
        elif _token_ == 'FLOAT':
            FLOAT = self._scan('FLOAT')
            return atof(FLOAT)
        else:# == 'STRING'
            STRING = self._scan('STRING')
            return STRING

    def parameters(self, PARAMS):
        while self._peek('ID', 'NUMBER', 'FLOAT', 'STRING', 'END') != 'END':
            arg = self.arg()
            PARAMS.append(arg)

    def command(self):
        self._scan('"/"')
        ID = self._scan('ID')
        cmd = [ID] ; params = []
        parameters = self.parameters(params)
        END = self._scan('END')
        cmd.append(params); return cmd

    def message(self):
        MESSAGE = self._scan('MESSAGE')
        END = self._scan('END')
        return MESSAGE

    def input(self):
        while 1:
            _token_ = self._peek('"/"', 'MESSAGE')
            if _token_ == '"/"':
                command = self.command()
                return command
            else:# == 'MESSAGE'
                message = self.message()
                return message
            if 0: break


def parse(rule, text):
    P = CommandParser(CommandParserScanner(text))
    return wrap_error_reporter(P, rule)




if __name__=='__main__':
    while 1:
        try: s = raw_input('>>> ')
	except EOFError: break
        if not s: break
        print parse('input', s + "\n")
    print 'Bye.'


