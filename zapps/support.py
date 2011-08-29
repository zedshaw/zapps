INDENT = " "*4
import re
import sys
from string import *

class Generator:
    def __init__(self, name, options, tokens, rules):
        self.change_count = 0
        self.name = name
        self.options = options
        self.preparser = ''
        self.postparser = None
        
        self.tokens = {} # Map from tokens to regexps
        self.ignore = [] # List of token names to ignore in parsing
        self.terminals = [] # List of token names (to maintain ordering)
        for n,t in tokens:
            if n == '#ignore':
                n = t
                self.ignore.append(n)

            if n in self.tokens.keys() and self.tokens[n] != t:
                print 'Warning: token', n, 'multiply defined.'
            self.tokens[n] = t
            self.terminals.append(n)
            
        self.rules = {} # Map from rule names to parser nodes
        self.params = {} # Map from rule names to parameters
        self.goals = [] # List of rule names (to maintain ordering)
        for n,p,r in rules:
            self.params[n] = p
            self.rules[n] = r
            self.goals.append(n)
            
        self.output = sys.stdout

    def __getitem__(self, name):
        # Get options
        return self.options.get(name, 0)
    
    def non_ignored_tokens(self):
        return filter(lambda x, i=self.ignore: x not in i, self.terminals)
    
    def changed(self):
        self.change_count = 1+self.change_count

    def subset(self, a, b):
        "See if all elements of a are inside b"
        for x in a:
            if x not in b: return 0
        return 1
    
    def equal_set(self, a, b):
        "See if a and b have the same elements"
        if len(a) != len(b): return 0
        if a == b: return 1
        return self.subset(a, b) and self.subset(b, a)
    
    def add_to(self, parent, additions):
        "Modify parent to include all elements in additions"
        for x in additions:
            if x not in parent:
                parent.append(x)
                self.changed()

    def equate(self, a, b):
        self.add_to(a, b)
        self.add_to(b, a)

    def write(self, *args):
        for a in args:
            self.output.write(a)

    def in_test(self, x, full, b):
        if not b: return '0'
        if len(b) == 1: return '%s == %s' % (x, repr(b[0]))
        if full and len(b) > len(full)/2:
            # Reverse the sense of the test.
            not_b = filter(lambda x, b=b: x not in b, full)
            return self.not_in_test(x, full, not_b)
        return '%s in %s' % (x, repr(b))
    
    def not_in_test(self, x, full, b):
        if not b: return '1'
        if len(b) == 1: return '%s != %s' % (x, repr(b[0]))
        return '%s not in %s' % (x, repr(b))

    def peek_call(self, a):
        a_set = (repr(a)[1:-1])
        if self.equal_set(a, self.non_ignored_tokens()): a_set = ''
        if self['context-insensitive-scanner']: a_set = ''
        return 'self._peek(%s)' % a_set
    
    def peek_test(self, a, b):
        if self.subset(a, b): return '1'
        if self['context-insensitive-scanner']: a = self.non_ignored_tokens()
        return self.in_test(self.peek_call(a), a, b)

    def not_peek_test(self, a, b):
        if self.subset(a, b): return '0'
        return self.not_in_test(self.peek_call(a), a, b)

    def calculate(self):
        while 1:
            for r in self.goals:
                self.rules[r].setup(self, r)
            if self.change_count == 0: break
            self.change_count = 0

        while 1:
            for r in self.goals:
                self.rules[r].update(self)
            if self.change_count == 0: break
            self.change_count = 0

    def dump_information(self):
        self.calculate()
        for r in self.goals:
            print '    _____' + '_'*len(r)
            print ('___/Rule '+r+'\\' + '_'*80)[:79]
            queue = [self.rules[r]]
            while queue:
                top = queue[0]
                del queue[0]

                print repr(top)
                top.first.sort()
                top.follow.sort()
                eps = []
                if top.accepts_epsilon: eps = ['(null)']
                print '     FIRST:', join(top.first+eps, ', ')
                print '    FOLLOW:', join(top.follow, ', ')
                for x in top.get_children(): queue.append(x)
                
    def generate_output(self):
        self.calculate()
        self.write(self.preparser)
        # TODO: remove "import *" construct
        self.write("from string import *\n")
        self.write("import re\n")
        self.write("from zapps.rt import *\n")
        self.write("\n")
        self.write("class ", self.name, "Scanner(Scanner):\n")
        self.write("    patterns = [\n")
        for p in self.terminals:
            self.write("        (%s, re.compile(%s)),\n" % (
                repr(p), repr(self.tokens[p])))
        self.write("    ]\n")
        self.write("    def __init__(self, str):\n")
        self.write("        Scanner.__init__(self,None,%s,str)\n" %
                   repr(self.ignore))
        self.write("\n")
        
        self.write("class ", self.name, "(Parser):\n")
        for r in self.goals:
            self.write(INDENT, "def ", r, "(self")
            if self.params[r]: self.write(", ", self.params[r])
            self.write("):\n")
            self.rules[r].output(self, INDENT+INDENT)
            self.write("\n")

        self.write("\n")
        self.write("def parse(rule, text):\n")
        self.write("    P = ", self.name, "(", self.name, "Scanner(text))\n")
        self.write("    return wrap_error_reporter(P, rule)\n")
        self.write("\n")
        if self.postparser is not None:
            self.write(self.postparser)
        else:
            self.write("if __name__ == '__main__':\n")
            self.write(INDENT, "from sys import argv, stdin\n")
            self.write(INDENT, "if len(argv) >= 2:\n")
            self.write(INDENT*2, "if len(argv) >= 3:\n")
            self.write(INDENT*3, "f = open(argv[2],'r')\n")
            self.write(INDENT*2, "else:\n")
            self.write(INDENT*3, "f = stdin\n")
            self.write(INDENT*2, "print parse(argv[1], f.read())\n")
            self.write(INDENT, "else: print 'Args:  <rule> [<filename>]'\n")

######################################################################
class Node:
    def __init__(self):
        self.first = []
        self.follow = []
        self.accepts_epsilon = 0
        self.rule = '?'
        
    def setup(self, gen, rule):
        # Setup will change accepts_epsilon,
        # sometimes from 0 to 1 but never 1 to 0.
        # It will take a finite number of steps to set things up
        self.rule = rule

    def used(self, vars):
        "Return two lists: one of vars used, and the other of vars assigned"
        return vars, []

    def get_children(self):
        "Return a list of sub-nodes"
        return []
    
    def __repr__(self):
        return str(self)
    
    def update(self, gen):
        if self.accepts_epsilon:
            gen.add_to(self.first, self.follow)

    def output(self, gen, indent):
        "Write out code to _gen_ with _indent_:string indentation"
        gen.write(indent, "assert 0 # Invalid parser node\n")
    
class Terminal(Node):
    def __init__(self, token):
        Node.__init__(self)
        self.token = token
        self.accepts_epsilon = 0

    def __str__(self):
        return self.token

    def update(self, gen):
        Node.update(self, gen)
        if self.first != [self.token]:
            self.first = [self.token]
            gen.changed()

    def output(self, gen, indent):
        gen.write(indent)
        if self.is_ident():
            gen.write(self.token, " = ")
        gen.write("self._scan(%s)\n" % repr(self.token))

    def is_ident(self):
        return re.match('[a-zA-Z_][a-zA-Z_0-9]*$', self.token)
        
class Eval(Node):
    def __init__(self, expr):
        Node.__init__(self)
        self.expr = expr

    def setup(self, gen, rule):
        Node.setup(self, gen, rule)
        if not self.accepts_epsilon:
            self.accepts_epsilon = 1
            gen.changed()

    def __str__(self):
        return '{{ %s }}' % strip(self.expr)

    def output(self, gen, indent):
        gen.write(indent, strip(self.expr), '\n')
        
class Pack(Eval):
    def __str__(self):
        return "//%s//" % strip(self.expr)

    def output(self, gen, indent):
        gen.write(indent, "return self._unpack(%s)\n" % repr(self.expr))

class NonTerminal(Node):
    def __init__(self, name, args):
        Node.__init__(self)
        self.name = name
        self.args = args

    def setup(self, gen, rule):
        Node.setup(self, gen, rule)
        try:
            self.target = gen.rules[self.name]
            if self.accepts_epsilon != self.target.accepts_epsilon:
                self.accepts_epsilon = self.target.accepts_epsilon
                gen.changed()
        except KeyError: # Oops, it's nonexistent
            print 'Error: no rule <%s>' % self.name
            self.target = self
            
    def __str__(self):
        return '<%s>' % self.name

    def update(self, gen):
        Node.update(self, gen)
        gen.equate(self.first, self.target.first)
        gen.equate(self.follow, self.target.follow)

    def output(self, gen, indent):
        gen.write(indent)
        gen.write(self.name, " = ")
        gen.write("self.", self.name, "(", self.args, ")\n")
        
class Sequence(Node):
    def __init__(self, *children):
        Node.__init__(self)
        self.children = children

    def setup(self, gen, rule):
        Node.setup(self, gen, rule)
        for c in self.children: c.setup(gen, rule)
        
        if not self.accepts_epsilon:
            # If it's not already accepting epsilon, it might now do so.
            for c in self.children:
                # any non-epsilon means all is non-epsilon
                if not c.accepts_epsilon: break
            else:
                self.accepts_epsilon = 1
                gen.changed()

    def get_children(self):
        return self.children
    
    def __str__(self):
        return '( %s )' % join(map(lambda x: str(x), self.children))

    def update(self, gen):
        Node.update(self, gen)
        for g in self.children:
            g.update(gen)

        empty = 1
        for g_i in range(len(self.children)):
            g = self.children[g_i]
            
            if empty:  gen.add_to(self.first, g.first)
            if not g.accepts_epsilon: empty = 0
            
            if g_i == len(self.children)-1:
                next = self.follow
            else:
                next = self.children[1+g_i].first
            gen.add_to(g.follow, next)

        if self.children:
            gen.add_to(self.follow, self.children[-1].follow)

    def output(self, gen, indent):
        if self.children:
            for c in self.children:
                c.output(gen, indent)
        else:
            # Placeholder for empty sequences, just in case
            gen.write(indent, 'pass\n')
            
class Choice(Node):
    def __init__(self, *children):
        Node.__init__(self)
        self.children = children

    def setup(self, gen, rule):
        Node.setup(self, gen, rule)
        for c in self.children: c.setup(gen, rule)
            
        if not self.accepts_epsilon:
            for c in self.children:
                if c.accepts_epsilon:
                    self.accepts_epsilon = 1
                    gen.changed()

    def get_children(self):
        return self.children
    
    def __str__(self):
        return '( %s )' % join(map(lambda x: str(x), self.children), ' | ')

    def update(self, gen):
        Node.update(self, gen)
        for g in self.children:
            g.update(gen)

        for g in self.children:
            gen.add_to(self.first, g.first)
            gen.add_to(self.follow, g.follow)
        for g in self.children:
            gen.add_to(g.follow, self.follow)
        if self.accepts_epsilon:
            gen.add_to(self.first, self.follow)

    def output(self, gen, indent):
        test = "if"
        gen.write(indent, "_token_ = ", gen.peek_call(self.first), "\n")
        tokens_seen = []
        tokens_unseen = self.first[:]
        if gen['context-insensitive-scanner']:
            # Context insensitive scanners can return ANY token,
            # not only the ones in first.
            tokens_unseen = gen.non_ignored_tokens()
        for c in self.children:
            testset = c.first[:]
            removed = []
            for x in testset:
                if x in tokens_seen:
                    testset.remove(x)
                    removed.append(x)
                if x in tokens_unseen: tokens_unseen.remove(x)
            tokens_seen = tokens_seen + testset
            if removed:
                if not testset:
                    print 'Error in rule', self.rule+':', c, 'never matches.'
                else:
                    print 'Warning:', self
                print ' * These tokens are being ignored:', join(removed, ', ')
                print '   due to previous choices using them.'
                
            if testset:
                if not tokens_unseen: # context sensitive scanners only!
                    if test == 'if':
                        # if it's the first AND last test, then
                        # we can simply put the code without an if/else
                        c.output(gen, indent)
                    else:
                        gen.write(indent, "else:")
                        t = gen.in_test('', [], testset)
                        if len(t) < 70-len(indent):
                            gen.write("#", t)
                        gen.write("\n")
                        c.output(gen, indent+INDENT)
                else:
                    gen.write(indent, test, " ",
                              gen.in_test('_token_', tokens_unseen, testset),
                              ":\n")
                    c.output(gen, indent+INDENT)
                test = "elif"

        if gen['context-insensitive-scanner'] and tokens_unseen:
            gen.write(indent, "else:\n")
            gen.write(indent, INDENT, "raise SyntaxError(self._pos, ")
            gen.write("'Could not match ", self.rule, "')\n")

class Wrapper(Node):
    def __init__(self, child):
        Node.__init__(self)
        self.child = child

    def setup(self, gen, rule):
        Node.setup(self, gen, rule)
        self.child.setup(gen, rule)

    def get_children(self):
        return [self.child]
    
    def update(self, gen):
        Node.update(self, gen)
        self.child.update(gen)
        gen.add_to(self.first, self.child.first)
        gen.equate(self.follow, self.child.follow)

class Option(Wrapper):
    def setup(self, gen, rule):
        Wrapper.setup(self, gen, rule)
        if not self.accepts_epsilon:
            self.accepts_epsilon = 1
            gen.changed()

    def __str__(self):
        return '[ %s ]' % str(self.child)

    def output(self, gen, indent):
        if self.child.accepts_epsilon:
            print 'Warning in rule', self.rule+': contents may be empty.'
        gen.write(indent, "if %s:\n" %
                  gen.peek_test(self.first, self.child.first))
        self.child.output(gen, indent+INDENT)
        
class Question(Wrapper):
    def setup(self, gen, rule):
        Wrapper.setup(self, gen, rule)
        if not self.accepts_epsilon:
            self.accepts_epsilon = 1
            gen.changed()

    def __str__(self):
        return '( %s )?' % str(self.child)

    def output(self, gen, indent):
        if self.child.accepts_epsilon:
            print 'Warning in rule', self.rule+': contents may be empty.'
        gen.write(indent, "if %s:\n" %
                  gen.peek_test(self.first, self.child.first))
        self.child.output(gen, indent+INDENT)
        gen.write(indent, "else:\n", indent+INDENT, 
                "%s = None\n\n" % self.child.name)

class Plus(Wrapper):
    def setup(self, gen, rule):
        Wrapper.setup(self, gen, rule)
        if self.accepts_epsilon != self.child.accepts_epsilon:
            self.accepts_epsilon = self.child.accepts_epsilon
            gen.changed()

    def __str__(self):
        return '%s+' % str(self.child)

    def update(self, gen):
        Wrapper.update(self, gen)
        gen.add_to(self.follow, self.first)

    def output(self, gen, indent):
        if self.child.accepts_epsilon:
            print 'Warning in rule', self.rule+':'
            print ' * The repeated pattern could be empty.  The resulting'
            print '   parser may not work properly.'
        gen.write(indent, "while 1:\n")
        self.child.output(gen, indent+INDENT)
        union = self.first[:]
        gen.add_to(union, self.follow)
        gen.write(indent+INDENT, "if %s: break\n" %
                  gen.not_peek_test(union, self.child.first))

class Star(Plus):
    def setup(self, gen, rule):
        Wrapper.setup(self, gen, rule)
        if not self.accepts_epsilon:
            self.accepts_epsilon = 1
            gen.changed()

    def __str__(self):
        return '%s*' % str(self.child)

    def output(self, gen, indent):
        if self.child.accepts_epsilon:
            print 'Warning in rule', self.rule+':'
            print ' * The repeated pattern could be empty.  The resulting'
            print '   parser probably will not work properly.'
        gen.write(indent, "while %s:\n" %
                  gen.peek_test(self.follow, self.child.first))
        self.child.output(gen, indent+INDENT)
