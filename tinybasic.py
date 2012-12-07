from peglet import *
from pprint import *
import re


grammar = r"""
lines       = _ line _ lines
            | _ line
line        = num _ stmt                        hug
            | stmt                              hug
stmt        = print_stmt
            | let_stmt
            | input_stmt
            | if_stmt
            | goto_stmt
            | gosub_stmt
            | return_stmt
            | clear_stmt
            | list_stmt
            | run_stmt
            | end_stmt

print_stmt  = (PRINT\b) _ expr_list
let_stmt    = (LET\b) _ var _ (?:=) _ expr
input_stmt  = (INPUT\b) _ var_list
if_stmt     = (IF\b) _ expr _ (THEN\b) _ stmt
goto_stmt   = (GOTO\b) _ expr
gosub_stmt  = (GOSUB\b) _ expr
return_stmt = (RETURN\b)
clear_stmt  = (CLEAR\b)
list_stmt   = (LIST\b)
run_stmt    = (RUN\b)
end_stmt    = (END\b)

expr_list   = expr _ , _ expr_list 
            | expr 
            | str _ , _ expr_list
            | str
expr        = term _ binop _ expr               join
            | term _ relop _ expr               join
            | term
term        = var
            | num
            | l_paren _ expr _ r_paren          join
var_list    = var _ , _ var_list
            | var
var         = ([A-Z])

str         = " chars " _                       join quote
            | ' sqchars ' _                     join
chars       = char chars 
            |
char        = ([^\x00-\x1f"\\]) 
            | esc_char
sqchars     = sqchar sqchars 
            |
sqchar      = ([^\x00-\x1f'\\]) 
            | esc_char
esc_char    = \\(['"/\\])
            | \\([bfnrt])                       escape
num         = (\-) num
            | (\d+)
relop       = (<>|><|<=|<|>=|>|=)               repop
binop       = (\+|\-|\*|\/)
l_paren     = (\()
r_paren     = (\)) 
_           = \s*
"""

def repop(s):
    if s == "<>" or s == "><":
        return "!="
    return s

def quote(s):
    return '"' + s + '"'

class TinyBasic:

    def __init__(self):
        self.parser = Parser(grammar, 
                             hug=hug,
                             join=join,
                             repop=repop,
                             quote=quote,
                             escape=re.escape)
        self.symbols = {}

    def parse(self, program):
        self.ast = self.parser(program)

    def eval(self):
        for line in self.ast:
            if len(line) != 1:
                line = line[1:]    
            self.stmt(line)
    
    def stmt(self, stmt):
        head, tail = stmt[0], stmt[1:]
        if head == "PRINT":
            self.print_stmt(tail)
        elif head == "LET":
            self.let_stmt(tail)
        elif head == "INPUT":
            self.input_stmt(tail)
        elif head == "IF":
            self.if_stmt(tail)

    def print_stmt(self, xs):
        print " ".join(self.expr_list(xs))

    def let_stmt(self, xs):
        head, tail = xs[0], xs[1]
        self.symbols[head] = tail

    def input_stmt(self, xs):
        for x in xs:
            self.symbols[x] = str(raw_input("?"))
    
    def if_stmt(self, xs):
        head, tail = xs[0], xs[2:]
        if self.expr(head) == "True":
            self.stmt(tail)

    def expr_list(self, xs):
        return [self.expr(x) for x in xs]

    def expr(self, x):
        if re.match("^\".*\"$", x):
            return x
        else:
            vs = re.findall("[A-Z]", x)
            if vs:
                for v in vs:
                    x = x.replace(v, self.var(v))
            return str(eval(x))
    
    def var(self, x):
        return self.symbols[x]

if __name__ == "__main__":

    program = r'''
        10 LET A = 10
        20 IF A < 2 THEN PRINT "A is less than 2"
    '''

    tiny_basic = TinyBasic()
    tiny_basic.parse(program)
    pprint(tiny_basic.ast)
    
    print "\n"

    tiny_basic.eval()
    #pprint(tiny_basic.symbols)
