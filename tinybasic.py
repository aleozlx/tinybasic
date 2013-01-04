import os
import io
import re
import sys
import pprint
import argparse
import peglet


class Parser(object):

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
                | (LET\b) _ var _ (?:=) _ str
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

    def __init__(self):
        kwargs = {"hug"     : peglet.hug,
                  "join"    : peglet.join,
                  "repop"   : self.repop,
                  "quote"   : self.quote,
                  "escape"  : re.escape}
        self.parser = peglet.Parser(self.grammar, **kwargs)
    
    def __call__(self, program):
        return self.parser(program)

    def repop(self, token):
        if token == "<>" or token == "><":
            return "!="
        return token

    def quote(self, token):
        return '"%s"' % token


class Interpreter(object):
    
    def __init__(self):
        self.curr = 0
        self.memory = {}
        self.symbols = {}
        self.parse_tree = None
        self.parser = Parser()
    
    def __call__(self, program):
        self.parse_tree = self.parser(program)
        for line in self.parse_tree:
            if len(line) > 1:
                head, tail = line[0], line[1:]
                self.memory[head] = tail
        for line in self.parse_tree:
            if len(line) == 1:
                self.stmt(line)
        self.curr = 0

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


class Compiler(object):
    
    def __init__(self):
        self.parser = Parser()
        self.parse_tree = None
        self.symbols = {}
        self.malloc_symbols = {}

    def __call__(self, program):
        self.parse_tree = self.parser(program)
        print "#include <stdio.h>"
        print "#include <stdlib.h>"
        print "#include <string.h>"
        print "int main (void) {"
        for line in self.parse_tree:
            if "LET" in line:
                id = line[2]
                if id not in self.symbols:
                    self.compile_stmt(line[1:])
            elif "INPUT" in line:
                id = line[2]
                if id not in self.symbols:
                    self.compile_var((id, '""'))
        for line in self.parse_tree:
            self.compile_stmt(line)
        print "}"
    
    def compile_stmt(self, stmt):
        head, tail = stmt[0], stmt[1:]
        if tail:
            if head == "IF":
                self.compile_if(tail)
            elif head == "LET":
                self.compile_var(tail)
            elif head == "REM":
                self.compile_comment(tail)
            elif head == "GOTO":
                self.compile_goto(tail)
            elif head == "PRINT":
                self.compile_printf(tail)
            elif head == "INPUT":
                self.compile_input(tail)
            else:
                self.compile_label(head)
                self.compile_stmt(tail)
        else:
            if head == "END":
                self.compile_return()
    
    def compile_input(self, xs):
        id, buffer = xs[0], 50
        self.malloc_symbols[id] = buffer
        print '''
        {0} = malloc(sizeof(char) * {1});
        fgets({0}, {1}, stdin);
        if ({0}[strlen({0}) - 1] == '\\n') {{
            {0}[strlen({0}) - 1] = '\\0';
        }}
        '''.format(id, buffer)

    def compile_if(self, xs):
        cond, stmt = xs[0], xs[2:]
        print "if (%s) {" % (cond)
        self.compile_stmt(stmt)
        print "}"

    def compile_goto(self, xs):
        print "goto label_%s;" % xs[0]

    def compile_var(self, xs):
        id = xs[0]
        if id in self.symbols:
            self.compile_var_set(xs)
        else:
            self.compile_var_dec(xs)
    
    def compile_var_dec(self, xs):
        t, id, v = None, xs[0], xs[1]
        if self.is_quoted(v):
            t = "char"
        else:
            t = "int"
        self.symbols[id] = (t, v)
        if t == "char":
            print "%s* %s;" % (t, id)
        elif t == "int":
            print "%s %s;" % (t, id)

    def compile_var_set(self, xs):
        id, nv = xs[0], xs[1]
        t, ov = self.symbols[id] 
        self.symbols[id] = (t, nv)
        print "%s = %s;" % (id, nv)

    def compile_comment(self, xs):
        print "// %s" % xs[0].replace('"', "")

    def compile_label(self, n):
        print "label_%s:" % n
    
    def compile_printf(self, xs):
        fmt, args = [], []
        for x in xs:
            if x in self.symbols:
                t, v = self.symbols[x]
                if t == "char":
                    fmt.append("%s")
                elif t == "int":
                    fmt.append("%d")
                args.append(x)
            else:
                try:
                    x = int(eval(x))
                    fmt.append("%d")
                    args.append(str(x))
                except:
                    fmt.append("%s")
                    args.append(x)
        if fmt and args:
            fmt = " ".join(fmt)
            args = ", ".join(args)
            print 'printf("{0}\\n", {1});'.format(fmt, args)

    def compile_return(self):
        for id in self.malloc_symbols:
            print "free(%s);" % id
        print "return 0;"

    def is_quoted(self, s):
        return re.match('^".*"$', s)


class TinyBasic(object):
    
    def __init__(self):
        self.parser = Parser()
        self.interpreter = Interpreter()
        self.compiler = Compiler()
    
    def parse(self, program):
        return self.parser(program)
    
    def interpret(self, program):
        self.interpreter(program)

    def compile(self, program):
        self.compiler(program)

    def repl(self):
        line = str(raw_input("> "))
        if line == "QUIT":
            sys.exit(0)
        try: 
            self.interpret(line)
        except: 
            if line:
                print "parse error"
        self.repl()


if __name__ == "__main__":

    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("path", nargs='?')
    arg_parser.add_argument("-p", "--parse", action="store_true")
    arg_parser.add_argument("-c", "--compile", action="store_true")
    args = arg_parser.parse_args()

    tiny_basic = TinyBasic()

    if args.path:
        if os.path.isfile(args.path):
            with io.open(args.path, "r") as f:
                program = "".join(f.readlines())
                program = program.encode("ascii", "ignore")
                if args.parse:
                    for line in tiny_basic.parse(program):
                        print line
                elif args.compile:
                    tiny_basic.compile(program)
                else:
                    tiny_basic.interpret(program)
    else:
        tiny_basic.repl()
