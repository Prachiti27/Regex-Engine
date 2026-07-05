from lexer import Lexer
from matcher import Matcher
from parser import Parser


lexer = Lexer(r"hello$")
tokens = lexer.tokenize()
parser = Parser(tokens)
ast = parser.parse()
matcher = Matcher(ast)
print(matcher.match("world hello"))
print(matcher.search("world hello"))
print(matcher.findall("world hello"))