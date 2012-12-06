from peglet import *
from pprint import *
import re


grammar = r"""
lines       = _ line _ lines
            | _ line
line        = number _ stmt                     hug
            | simple_stmt                       hug

stmt        = print_stmt                        hug
            | if_stmt                           hug
            | goto_stmt                         hug
            | input_stmt                        hug
            | let_stmt                          hug
            | gosub_stmt                        hug
            | simple_stmt                       hug

print_stmt  = (PRINT) _ expr_list
if_stmt     = (IF) _ relop_expr _ (THEN) _ stmt
goto_stmt   = (GOTO) _ expr
input_stmt  = (INPUT) _ var_list
let_stmt    = (LET) _ var_expr
gosub_stmt  = (GOSUB) _ expr
simple_stmt = (RETURN|CLEAR|LIST|RUN|END)

term        = var
            | NUM unop                          hug
            | NUM number                        hug

eq          = EQOP (=)                          hug
relop       = (<|>|=)
relop_expr  = expr _ relop _ expr               hug


binop       = BINOP (\+|\-|\*|\/)               hug
unop        = (\+|\-) number                    join

expr_list   = expr_or_str _ , _ expr_list
            | expr_or_str
expr        = term _ binop _ expr               hug
            | term
expr_or_str = EXP expr                          hug
            | STR string                        hug

var_list    = var _ , _ var_list
            | var
var_expr    = var _ eq _ expr
var         = VAR ([A-Z])                       hug

string      = " chars " _                       join
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

number      = (\d+)

_           = \s*
"""

def Tag(label):
    return lambda *parts: (label)

class TinyBasic:
    def __init__(self):
        self.ast = None
        self.parser = Parser(grammar, 
                             hug=hug, 
                             join=join, 
                             escape=re.escape,
                             EXP=Tag("EXP"),
                             STR=Tag("STR"),
                             NUM=Tag("NUM"),
                             VAR=Tag("VAR"),
                             BINOP=Tag("BINOP"),
                             EQOP=Tag("EQOP"))
        self.memory = {}
        self.symbols = {}
    def parse(self, program):
        self.ast = self.parser(program)
    def eval(self):
        for line in self.ast:
            n, i = int(line[0]), line[1]
            self.memory[n] = i
        for n in sorted(self.memory):
            i = self.memory[n]
            stmt = i[0]
            args = i[1:]
            if stmt == "PRINT": self.print_stmt(args)
            elif stmt == "LET": self.let_stmt(args)
        #pprint(self.ast)

    def print_stmt(self, args):
        result = []
        for arg in args:
            head, tail = arg[0], arg[1]
            if head == "STR":
                result.append(tail)
            elif head == "EXP":
                expr = []
                if tail[0] == "VAR":
                    expr.append(tail[1])
                else:
                    for t in tail:
                        if t[0] == "NUM" or t[0] == "BINOP":
                            expr.append(t[1])
                        elif t[0] == "VAR":
                            expr.append(self.symbols[t[1]])

                result.append(str(eval("".join(expr))))
        print " ".join(result)

    def let_stmt(self, args):
        k = args[0][1]
        n = args[2][1]
        self.symbols[k] = n

if __name__ == "__main__":

    program = r'''
        10 LET A = 0
        20 PRINT A + 1, A+2, A+3
    '''

    tb = TinyBasic()
    tb.parse(program)
    tb.eval()
