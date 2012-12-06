from peglet import *
from pprint import *
import re
import operator as op


grammar = r"""
lines       = _ line _ lines
            | _ line
line        = number _ stmt                     hug
            | stmt                              hug

stmt        = STMT print_stmt                   hug
            | STMT if_stmt                      hug
            | STMT goto_stmt                    hug
            | STMT input_stmt                   hug
            | STMT let_stmt                     hug
            | STMT gosub_stmt                   hug
            | STMT simple_stmt                  hug

print_stmt  = (PRINT\b) _ expr_list
if_stmt     = (IF\b) _ relop_expr _ (THEN\b) _ stmt
goto_stmt   = (GOTO\b) _ expr
input_stmt  = (INPUT\b) _ var_list
let_stmt    = (LET\b) _ var_expr
gosub_stmt  = (GOSUB\b) _ expr
simple_stmt = (RETURN\b|CLEAR\b|LIST\b|RUN\b|END\b)

expr        = EXP term _ plus_minus _ expr      hug
            | EXP term                          hug

expr_list   = expr_or_str _ , _ expr_list
            | expr_or_str
expr_or_str = expr                              
            | STR string                        hug

term        = factor _ mult_div _ term          hug
            | factor

factor      = var 
            | NUM number                        hug
            | l_paren _ expr _ r_paren          hug

l_paren     = (?:\()
r_paren     = (?:\)) 

assop       = ASSOP (=)                         hug

plus_minus  = plus | minus
mult_div    = mult | div
plus        = BINOP (\+)                        hug
minus       = BINOP (\-)                        hug
mult        = BINOP (\*)                        hug
div         = BINOP (\/)                        hug

relop       = (<|>|=)
relop_expr  = expr _ relop _ expr


var_list    = var _ , _ var_list
            | var
var_expr    = var _ assop _ expr
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
            | (?:-) number

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
                             STMT=Tag("STMT"),
                             BINOP=Tag("BINOP"),
                             ASSOP=Tag("ASSOP"))
        self.operators = {"+": op.add,
                          "-": op.sub
                
                }
        self.symbols = {}

    def parse(self, program):
        self.ast = self.parser(program)

    def eval(self):
        for line in self.ast: 
            if len(line) == 1:
                pass
            else:
                line_number = line[0]
                stmt = line[1][1:]
                self.eval_stmt(stmt)

        print self.symbols
        
    def eval_stmt(self, stmt):
        keyword = stmt[0]
        body = stmt[1:]
        if keyword == "PRINT":
            self.eval_print_stmt(body)
        elif keyword == "LET":
            self.eval_let_stmt(body)
        elif keyword == "INPUT":
            self.eval_input_stmt(body)
        elif keyword == "IF":
            self.eval_if_stmt(body)

    def eval_if_stmt(self, body):

        expr1    = body[0]
        operator = body[1]
        expr2    = body[2]
        stmt     = body[4]
        

    def eval_input_stmt(self, var_list):
        for var in var_list:
            name = self.eval_var(var)
            self.symbols[name] = raw_input("?")
    
    def eval_let_stmt(self, body):
        self.eval_var_expr(body)
        
    def eval_print_stmt(self, expr_list):
        output = ""
        for expr in expr_list:
            output += str(self.eval_expr_or_str(expr))
        print output

    def eval_expr_or_str(self, expr):
        if expr[0] == "STR":
            return expr[1]
        else:
            return self.eval_expr(expr)
            
    def eval_expr(self, expr):
        expr = expr[1:]
        if len(expr) == 3:
            operator = expr[1][1]
            if operator == "+":
                return self.eval_term(expr[0]) + self.eval_expr(expr[2])
            elif operator == "-":
                return self.eval_term(expr[0]) - self.eval_expr(expr[2])
        elif len(expr) == 1:
            return self.eval_term(expr[0])

    def eval_term(self, term):
        if len(term) == 2:
            return self.eval_factor(term)
        elif len(term) == 3:
            operator = term[1][1]
            if operator == "*":
                return self.eval_factor(term[0]) * self.eval_term(term[2])
            elif operator == "/":
                return self.eval_factor(term[0]) / self.eval_term(term[2])
            eval("1+2*3")

    def eval_factor(self, factor):
        if factor[0] == "NUM":
            return self.eval_number(factor[1])
        elif factor[0] == "VAR":
            return self.symbols[factor[1]]

    def eval_number(self, number):
        return int(number)

    def eval_var_expr(self, var_expr):
        var = self.eval_var(var_expr[0])
        self.symbols[var] = self.eval_expr(var_expr[2])

    def eval_var(self, var):
        return var[1]

if __name__ == "__main__":

    program = r'''
        10 PRINT "What's your name"
        20 INPUT A
        30 PRINT "Hello ", A
    '''

    tb = TinyBasic()
    tb.parse(program)
    #pprint(tb.ast)
    tb.eval()
