from dataclasses import dataclass
from typing import Optional, List
from enum import Enum, auto

class TokenType(Enum):
    CHAR = auto()
    STAR = (
        auto()
    )                     # zero or more
    PLUS = (
        auto()
    )                     # one or more
    QUESTION = (
        auto()
    )                     # zero or one
    LBARCE = auto()       # {
    RBRACE = auto()       # }
    COMMA = auto()
    PIPE = auto()         # or
    LPAREN = auto()       # (
    RPAREN = auto()       # )
    LBRACKET = auto()     #[
    RBRACKET = auto()     #]
    CARET = auto()        # ^
    DASH = auto()         # -
    DOT = auto()          # wildcard like a fill in the blank
    DOLLAR = auto()       # end of str $
    BACKSLASH = auto()    # escape or seq \
    DIGIT = auto()        # \d
    NON_DIGIT = auto()    # ^ at beginning of digit
    WORD = (
        auto()            # word [a-zA-Z0-9]
    )
    NON_WORD = (
        auto()            # ^ at beginning of word
    )
    WHITESPACE = (
        auto()          
    )
    NON_WHITESPACE = (
        auto()
    )
    WORD_BOUNDARY = auto() # \b \b
    NON_WORD_BOUNDARY = auto() 
    BACKREF = auto()       # \1 \2, etc
    LOOKAHEAD_POS = (
        auto()             # (?=
    )
    LOOKAHEAD_NEG = (
        auto()             # (?!
    )
    LOOKBEHIND_POS = (
        auto()             # (?<=
    ) 
    LOOKBEHIND_NEG = (
        auto()             # (?<!
    )
    NON_CAPTURING = (
        auto()             # (?:s
    )
    EOF = auto()
    

@dataclass
class Token:
    type: TokenType
    value: Optional[str] = None
    position: int = 0
    
class Lexer:
    def __init__(self, pattern: str):
        self.pattern = pattern
        self.pos = 0
        self.length = len(pattern)
        
    def current_char(self) -> Optional[str]:
        if self.pos < self.length:
            return self.pattern[self.pos]
        return None
    
    def advance(self) -> Optional[str]:
        char = self.current_char()
        self.pos += 1
        return char
        
    def tokenize(self) -> List[Token]:
        tokens = []
        
        while self.pos < self.length:
            start_pos = self.pos
            char = self.current_char()
            
            if char == "\\":
                token = self._handle_escape()
                if token:
                    tokens.append(token)
                continue
            elif char == "*":
                tokens.append(Token(TokenType.STAR, char, start_pos))
                self.advance()
            elif char == "+":
                tokens.append(Token(TokenType.PLUS, char, start_pos))
                self.advance()
            elif char == "?":
                tokens.append(Token(TokenType.QUESTION, char, start_pos))
                self.advance()
            elif char == "{":
                tokens.append(Token(TokenType.LBARCE, char, start_pos))
                self.advance()
            elif char == "}":
                tokens.append(Token(TokenType.RBRACE, char, start_pos))
                self.advance()
            elif char == ",":
                tokens.append(Token(TokenType.COMMA, char, start_pos))
                self.advance()
            elif char == "|":
                tokens.append(Token(TokenType.PIPE, char, start_pos))
                self.advance()
            elif char == "(":
                token = self._handle_group_start()
                tokens.append(token)
            elif char == ")":
                tokens.append(Token(TokenType.RPAREN, char, start_pos))
                self.advance()
            elif char == "[":
                tokens.append(Token(TokenType.LBRACKET, char, start_pos))
                self.advance()
            elif char == "]":
                tokens.append(Token(TokenType.RBRACKET, char, start_pos))
                self.advance()
            elif char == "^":
                tokens.append(Token(TokenType.CARET, char, start_pos))
                self.advance()
            elif char == "$":
                tokens.append(Token(TokenType.DOLLAR, char, start_pos))
                self.advance()
            elif char == ".":
                tokens.append(Token(TokenType.DOT, char, start_pos))
                self.advance()
            elif char == "-":
                tokens.append(Token(TokenType.DASH, char, start_pos))
                self.advance()
            else:
                tokens.append(Token(TokenType.CHAR, char, start_pos))
                self.advance()

        tokens.append(Token(TokenType.EOF, None, self.pos))
        return tokens
                
    def _handle_escape(self) -> Optional[Token]:
        start_pos = self.pos
        self.advance() 
        
        next_char = self.current_char()
        
        if next_char is None:
            raise ValueError(
                f"Pattern cannot end with backslash at position {start_pos}"
            )
            
        if next_char == "d":
            self.advance()
            return Token(TokenType.DIGIT, r"\d", start_pos)
        elif next_char == "D":
            self.advance()
            return Token(TokenType.NON_DIGIT, r"\D", start_pos)
        elif next_char == "w":
            self.advance()
            return Token(TokenType.WORD, r"\w", start_pos)
        elif next_char == "W":
            self.advance()
            return Token(TokenType.NON_WORD, r"\W", start_pos)
        elif next_char == "s":
            self.advance()
            return Token(TokenType.WHITESPACE, r"\s", start_pos)
        elif next_char == "S":
            self.advance()
            return Token(TokenType.NON_WHITESPACE, r"\S", start_pos)
        elif next_char == "b":
            self.advance()
            return Token(TokenType.WORD_BOUNDARY, r"\b", start_pos)
        elif next_char == "B":
            self.advance()
            return Token(TokenType.NON_WORD_BOUNDARY, r"\B", start_pos)
        elif next_char.isdigit():
            num = ""
            while self.current_char() and self.current_char().isdigit():
                num += self.advance()
            return Token(TokenType.BACKREF, num, start_pos)
        elif next_char == "n":
            self.advance()
            return Token(TokenType.CHAR, "\n", start_pos)
        elif next_char == "t":
            self.advance()
            return Token(TokenType.CHAR, "\r", start_pos)
        elif next_char == "r":
            self.advance()
            return Token(TokenType.CHAR, "\r", start_pos)
        else:
            self.advance()
            return Token(TokenType.CHAR, next_char, start_pos)
            
            
    def _handle_group_start(self) -> Token:
        start_pos = self.pos
        self.advance()
        
        if self.current_char() == "?":
            self.advance()
            
            next_char = self.current_char()
            
            if next_char == ":":
                self.advance()
                return Token(TokenType.NON_CAPTURING, "(?:", start_pos)
            elif next_char == "=":
                self.advance()
                return Token(TokenType.LOOKAHEAD_POS, "(?=", start_pos)
            elif next_char == "!":
                self.advance()
                return Token(TokenType.LOOKAHEAD_NEG, "(?!", start_pos)
            elif next_char == "<":
                self.advance()
                look_char = self.current_char()
                if look_char == "=":
                    self.advance()
                    return Token(TokenType.LOOKBEHIND_POS, "(?<=", start_pos)
                elif look_char == "!":
                    self.advance()
                    return Token(TokenType.LOOKBEHIND_NEG, "(?<!", start_pos)
                else:
                    raise ValueError(f"Invalid group syntax at position {start_pos}")
            else:
                raise ValueError(
                    f"Unknown group modifier '?{next_char}' at position {start_pos}"
                )
        return Token(TokenType.LPAREN, "(", start_pos)
    
# lexer = Lexer(r"a\d{1}(?:foo|bar)?")
# print(lexer.tokenize())