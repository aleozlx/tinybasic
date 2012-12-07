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
if_stmt     = (IF\b) _ expr _ relop _ expr _ (THEN\b) _ stmt
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
            | term
term        = var
            | num
            | l_paren _ expr _ r_paren          join
var_list    = var _ , _ var_list
            | var
var         = ([A-Z])


str         = " chars " _                       join
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
relop       = (<|>|=)
binop       = (\+|\-|\*|\/)
l_paren     = (\()
r_paren     = (\)) 
_           = \s*
"""


class TinyBasic:

    def __init__(self):
        self.parser = Parser(grammar, 
                             hug=hug, 
                             join=join, 
                             escape=re.escape)

    def parse(self, program):
        self.ast = self.parser(program)

    def eval(self):
        pass


if __name__ == "__main__":

    program = r'''
        10 PRINT "HELLO", A + 1
        20 RETURN
        40 IF 1+2 < 3+4 THEN PRINT "YES"
        END
        RETURN
    '''

    tb = TinyBasic()
    tb.parse(program)
    pprint(tb.ast)
