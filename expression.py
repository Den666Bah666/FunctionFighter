from token import Token, TokenType


class Expression:
    def __init__(self, raw: str):
        tokenized = Expression._tokenize(raw)
        Expression._validate(tokenized)
        self._postfix_expr = Expression._parse(tokenized)

    @staticmethod
    def _tokenize(expr: str) -> list[Token]:
        i = 0
        tokens: list[Token] = [Token(TokenType.START, "", -1)]

        while i < len(expr):
            if expr[i].isspace():
                i += 1

            elif expr[i] == 'x':
                tokens.append(Token(TokenType.ARGUMENT, "x", i))
                i += 1

            elif expr[i] in '123456789' or (expr[i] == '0' and _peek(expr, i + 1) == '.'):
                lit = str(expr[i])
                start = i
                while _peek(expr, i + 1).isdigit() or _peek(expr, i + 1) == '.':
                    i += 1
                    lit += expr[i]
                tokens.append(Token(TokenType.LITERAL, lit, start))
                i += 1

            elif expr[i] == '+':
                tokens.append(Token(TokenType.BINARY_OPERATOR, "+", i))
                i += 1

            elif expr[i] == '-':
                tokens.append(Token(TokenType.OPERATOR, "-", i))
                i += 1

            elif expr[i] == '*':
                if _peek(expr, i + 1) == '*':
                    tokens.append(Token(TokenType.BINARY_OPERATOR, "**", i))
                    i += 1
                else:
                    tokens.append(Token(TokenType.BINARY_OPERATOR, "*", i))
                i += 1

            elif expr[i] == '/':
                tokens.append(Token(TokenType.BINARY_OPERATOR, "/", i))
                i += 1

            elif expr[i] == '^':
                tokens.append(Token(TokenType.BINARY_OPERATOR, "^", i))
                i += 1

            elif expr[i] == "(":
                tokens.append(Token(TokenType.PARENTHESIS, "(", i))
                i += 1

            elif expr[i] == ")":
                tokens.append(Token(TokenType.PARENTHESIS, ")", i))
                i += 1

            else:
                raise TokenizationError(expr[i], i)

        tokens.append(Token(TokenType.END, "EOF", -1))
        return tokens

    @staticmethod
    def _validate(tokens: list[Token]) -> bool:
        last: Token | None = None

        parentheses_balance = 0
        first_opening_parenthesis: Token | None = None
        last_closing_parenthesis: Token | None = None

        for it in tokens:
            if last is not None:
                if (last.is_start() or last.is_opening_parenthesis()) and it.value == '-':
                    it.type = TokenType.UNARY_OPERATOR

                if last.is_operator() and (it.is_operator() or it.is_closing_parenthesis() or it.is_end()):
                    raise ParserSyntaxError(it)
                elif (last.is_opening_parenthesis() or last.is_start()) and \
                        (it.is_binary_operator() or it.is_closing_parenthesis() or it.is_end()):
                    raise ParserSyntaxError(it)
                elif (last.is_literal() or last.is_argument() or last.is_closing_parenthesis()) and it.is_literal():
                    raise ParserSyntaxError(it)
                elif last.is_argument() and it.is_argument() or last.is_literal() and it.is_opening_parenthesis():
                    raise ParserSyntaxError(it)

            if it.is_opening_parenthesis():
                parentheses_balance += 1
                first_opening_parenthesis = it if first_opening_parenthesis is None else first_opening_parenthesis

            elif it.is_closing_parenthesis():
                parentheses_balance -= 1
                if parentheses_balance < 0:
                    raise ParserSyntaxError(it)
                last_closing_parenthesis = it

            last = it

        if parentheses_balance < 0:
            raise ParserSyntaxError(last_closing_parenthesis)
        elif parentheses_balance > 0:
            raise ParserSyntaxError(first_opening_parenthesis)

        return True

    @staticmethod
    def _parse(tokens: list[Token]) -> list[Token]:
        last: Token | None = None
        listed_tokens: list[Token] = []
        for it in tokens:
            if last is not None:
                if ((last.is_literal() or last.is_closing_parenthesis()) and
                        it.is_argument() or (last.is_argument() or last.is_closing_parenthesis()) and it.is_opening_parenthesis()
                ):
                    listed_tokens.append(Token(TokenType.BINARY_OPERATOR, "*", it.idx))

            last = it
            listed_tokens.append(last)

        stack: list[Token] = []
        out: list[Token] = []

        for it in listed_tokens:
            if it.is_literal() or it.is_argument():
                out.append(it)

            elif it.is_opening_parenthesis():
                stack.append(it)

            elif it.is_closing_parenthesis():
                while stack and not stack[-1].is_opening_parenthesis():
                    out.append(stack.pop())
                stack.pop()

            elif it.is_left_associative():
                while stack and stack[-1].is_operator() and _pr(it) <= _pr(stack[-1]):
                    out.append(stack.pop())
                stack.append(it)

            elif it.is_right_associative():
                while stack and stack[-1].is_operator() and _pr(it) < _pr(stack[-1]):
                    out.append(stack.pop())
                stack.append(it)

            elif it.is_end():
                while stack:
                    out.append(stack.pop())

        return out

    def eval(self, x: float) -> float:
        stack = [0.0] * len(self._postfix_expr)
        top = 0

        for it in self._postfix_expr:
            if it.is_argument():
                stack[top] = x
                top += 1
            elif it.is_literal():
                stack[top] = float(it.value)
                top += 1
            elif it.is_unary_operator():
                stack[top - 1] = -stack[top - 1]
            elif it.value == "+":
                top -= 1
                stack[top - 1] += stack[top]
            elif it.value == "-":
                top -= 1
                stack[top - 1] -= stack[top]
            elif it.value == "*":
                top -= 1
                stack[top - 1] *= stack[top]
            elif it.value == "/":
                top -= 1
                stack[top - 1] /= stack[top]
            elif it.value in ("^", "**"):
                top -= 1
                stack[top - 1] **= stack[top]

        return stack[0]

class TokenizationError(Exception):
    def __init__(self, char: str, idx: int):
        self.char = char
        self.idx = idx
        super().__init__(f"Unexpected character '{char}' at position {idx}")


class ParserSyntaxError(Exception):
    def __init__(self, token: Token):
        self.token = token
        super().__init__(f"Unexpected token '{token.value}' at position {token.idx}")


def _peek(s: str, idx: int) -> str:
    return s[idx] if idx < len(s) else '\0'

_PRECEDENCE = {
    "+": 1,
    "-": 1,
    "*": 2,
    "/": 2,
    "^": 4,
    "**": 4,
}

def _pr(t: Token) -> int:
    if t.type == TokenType.UNARY_OPERATOR:
        return 3
    return _PRECEDENCE.get(t.value, 0)