from enum import Enum

class TokenType(Enum):
    LITERAL = 0
    ARGUMENT = 1
    OPERATOR = 2
    PARENTHESIS = 3
    START = 4
    END = 5
    UNARY_OPERATOR = 6
    BINARY_OPERATOR = 7

class Token:
    def __init__(self, _type: TokenType, value: str, idx: int):
        self.type = _type
        self.value = value
        self.idx = idx

    def is_literal(self):
        return self.type == TokenType.LITERAL

    def is_argument(self):
        return self.type == TokenType.ARGUMENT

    def is_operator(self):
        return self.type == TokenType.OPERATOR or self.type == TokenType.UNARY_OPERATOR or\
            self.type == TokenType.BINARY_OPERATOR

    def is_opening_parenthesis(self):
        return self.value == '('

    def is_closing_parenthesis(self):
        return self.value == ')'

    def is_binary_operator(self):
        return self.type == TokenType.BINARY_OPERATOR or self.value in ['**', '+', '/', '*', '^']

    def is_unary_operator(self):
        return self.type == TokenType.UNARY_OPERATOR

    def is_start(self):
        return self.type == TokenType.START

    def is_end(self):
        return self.type == TokenType.END

    def is_right_associative(self):
        return self.value in ["**", '^'] or self.type == TokenType.UNARY_OPERATOR

    def is_left_associative(self):
        return (self.value in ['+', '-', '/', '*']) and self.type != TokenType.UNARY_OPERATOR

    def __str__(self):
        return f"Token({self.type}, \"{self.value}\", {self.idx})"