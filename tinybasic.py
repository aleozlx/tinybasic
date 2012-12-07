import os
import io
import re
import sys
import pprint
import argparse
from peglet import *


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
            | clear_stmt
            | list_stmt
            | run_stmt
            | end_stmt
            | rem_stmt

print_stmt  = (PRINT\b) _ expr_list
let_stmt    = (LET\b) _ var _ (?:=) _ expr
input_stmt  = (INPUT\b) _ var_list
if_stmt     = (IF\b) _ expr _ (THEN\b) _ stmt
goto_stmt   = (GOTO\b) _ expr
clear_stmt  = (CLEAR\b)
list_stmt   = (LIST\b)
run_stmt    = (RUN\b)
end_stmt    = (END\b)
rem_stmt    = (REM\b) _ str

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
        self.ast = None
        self.curr = 0 
        self.symbols = {}
        self.memory = {}
    
    def repl(self):
        line = str(raw_input())
        if line == "QUIT":
            sys.exit(0)
        else:
            try:
                self.parse(line)
                self.eval()
                self.curr = 0
            except:
                pass
            self.repl()

    def parse(self, program):
        self.ast = self.parser(program)
    
    def store(self):
        for line in self.ast:
            if len(line) > 1:
                head, tail = line[0], line[1:]
                self.memory[head] = tail

    def eval(self):
        self.store()
        for line in self.ast:
            if len(line) == 1:
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
        elif head == "GOTO":
            self.goto_stmt(tail)
        elif head == "CLEAR":
            self.clear_stmt()
        elif head == "LIST":
            self.list_stmt()
        elif head == "RUN":
            self.run_stmt()
        elif head == "END":
            self.end_stmt()
        else:
            print "invalid statement"

    def print_stmt(self, xs):
        print " ".join(self.expr_list(xs))

    def let_stmt(self, xs):
        head, tail = xs[0], xs[1]
        self.symbols[head] = self.expr(tail)

    def input_stmt(self, xs):
        for x in xs:
            self.symbols[x] = str(raw_input("? "))
    
    def if_stmt(self, xs):
        head, tail = xs[0], xs[2:]
        if self.expr(head) == "True":
            self.stmt(tail)
    
    def goto_stmt(self, xs):
        n = self.expr(xs[0])
        self.curr = n
        self.run_stmt()
    
    def run_stmt(self):
        stmts = self.gen_stmt(self.memory)
        while (stmts):
            if self.curr >= 0:
                try:
                    self.curr, line = stmts.next()
                    self.stmt(line)
                except:
                    break
            else: 
                break

    def gen_stmt(self, memory):
        for k in sorted(self.memory):
            if k >= self.curr:
                yield (k, self.memory[k])

    def end_stmt(self):
        self.curr = -1

    def list_stmt(self):
        for k in sorted(self.memory):
            print " ".join(list(self.memory[k]))

    def clear_stmt(self):
        self.memory = {}

    def expr_list(self, xs):
        return [self.expr(x) for x in xs]

    def expr(self, x):
        if re.match("^\".*\"$", x):
            return x.replace("\"", "")
        else:
            vs = re.findall("[A-Z]", x)
            if vs:
                for v in vs:
                    x = x.replace(v, self.var(v))
            try:
                return str(eval(x))
            except:
                return x.replace("\"", "")
    
    def var(self, x):
        return self.symbols[x]
    

if __name__ == "__main__":

    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("path", nargs='?')
    arg_parser.add_argument("-p", "--parse", action="store_true")
    args = arg_parser.parse_args()

    tiny_basic = TinyBasic()

    if args.path:
        if os.path.isfile(args.path):
            with io.open(args.path) as f:
                program = "".join(f.readlines())
                program = program.encode("ascii", "ignore")
                tiny_basic.parse(program)
            if args.parse:
                pprint.pprint(tiny_basic.ast)
            else:
                tiny_basic.eval()
    else:
        tiny_basic.repl()
