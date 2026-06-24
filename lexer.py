from dataclasses import dataclass
from typing import Optional
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