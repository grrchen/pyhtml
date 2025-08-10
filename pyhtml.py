# Standard library imports.
import sys
from enum import Enum
from pathlib import Path
import argparse
import logging

logger = logging.getLogger(__name__)

handler = logging.StreamHandler(sys.stdout)
#handler.setLevel(logging.DEBUG)
#formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
formatter = logging.Formatter("%(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

# Related third party imports.

# Local application/library specific imports.


class BlockTyp(Enum):
    TEXT_BLOCK = 1
    HTML_ELEMENT = 2


class TokenType(Enum):
    HTML_ELEMENT = 1
    ATTRIBUTE = 2
    ASSIGMENT = 3
    COLON = 4
    INDENT = 5
    UNINDENT = 6
    NEWLINE = 7
    VALUE = 8
    TEXT_BLOCK = 9
    STRING = 10
    ADD_TEXT = 11


class SyntaxError(Exception):
    def __init__(self, token):
        self.token = token.token
        self.line = token.line
        self.row = token.row - len(self.token)
        Exception.__init__(self, f"Syntax error in line {self.line} and position {self.row}. Did not expect: {self.token} (╹-╹)?")


class Token:
    def __init__(self, token, line, row, token_type=None):
        self.line = line
        self.row = row
        self.token = token
        self.token_type = token_type

    def __repr__(self):
        return f"Token('{self.token}', {self.line}, {self.row}, {self.token_type})"


class BaseElement:
    pass


class HTMLElement(BaseElement):
    def __init__(self, indent: str, tag: str):
        self._indent = indent
        self._tag = tag
        self._childs: list = []

    def append(self, child):
        self._childs.append(child)

    def __repr__(self):
        return f"{self.__class__.__name__}({self._tag}, {repr(self._childs)})"


class Block(BaseElement):
    def __init__(self, childs: list):
        self._childs = [childs]

    def append(self, child):
        self._childs.append(child)

    def __repr__(self):
        return f"Block({repr(self._childs)})"

    def render(self):
        for child in self._childs:
            pass


class AddText(BaseElement):
    def __init__(self, value: str):
        self._value: str = value

    def render(self):
        return value

    def __repr__(self):
        return f"{self.__class__.__name__}({self._value})"

    def __str__(self):
        return self._value


class Attribute(BaseElement):
    def __init__(self, name: str, value: str):
        self._value: str = value
        self._name: str = name

    def render(self):
        return f"{self._name} = '{value}'"

    def __repr__(self):
        return f"{self.__class__.__name__}({self._name} = {self._value})"

    def __str__(self):
        return f"{self._name}='{self._value}'"


class Tokenizer:

    #delimiters: list = [" ", "=", ":", "(", ")", "[", "]", "\n", '"', "<"]
    delimiters: list = [" ", "=", ":", "\n", '"', "<"]

    def __init__(self, src):
        self._last_indent = ""
        self.tokens = tokens = []
        token: str = ""
        last_char: str = ""
        is_indendation: bool = False
        colon: bool = False
        text_block: bool = True
        string: bool = False
        line: int = 1
        row: int = 0
        for char in src:
            row += 1
            if is_indendation:
                if char != " ":
                    if self._last_indent is not None:
                        pass
                    if self._last_indent is not None and len(self._last_indent) <= len(token):
                        tokens.append(Token(token, line, row, TokenType.INDENT))
                    else:
                        tokens.append(Token(token, line, row, TokenType.UNINDENT))
                    self._last_indent = token
                    token = char
                    is_indendation = False
                    last_char = char
                    continue
                else:
                    token += char
                    continue
            elif is_indendation and last_char == " ":
                token += " "
            elif string:
                if char == '"' and last_char != "\\":
                    string = False
                    #tokens.append(Token(token, line, row, TokenType.STRING))
                    tokens.append(Token(token, line, row, TokenType.VALUE))
                    token = ""
                    last_char = char
                    continue
            elif char in self.delimiters and not string:
                if token and char != "<":
                    tokens.append(Token(token, line, row))
                    token = ""
                if char == "\n":
                    line += 1
                    row = 0
                    is_indendation = True
                    tokens.append(Token(char, line, row, TokenType.NEWLINE))
                    if colon:
                        current_block = BlockTyp.HTML_ELEMENT
                        token = ""
                        last_char = char
                        continue
                    else:
                        current_block = BlockTyp.TEXT_BLOCK
                        continue
                elif char == "<":
                    if last_char == "<":
                        tokens.append(Token("<<", line, row, TokenType.ADD_TEXT))
                        token = ""
                    last_char = char
                    continue
                elif char == "=":
                    tokens.append(Token(char, line, row, TokenType.ASSIGMENT))
                    continue
                elif char == ":":
                    tokens.append(Token(char, line, row, TokenType.COLON))
                    colon = True
                    continue
                elif char == " ":
                    continue
                elif char == '"':
                    string = True
                    continue
            token += char
            last_char = char

    def parse(self):
        first_element = None
        newline = True
        for i, token in enumerate(self.tokens):
            if token.token_type == TokenType.COLON:
                first_element.token_type = TokenType.HTML_ELEMENT
            #elif i == 0:
            #    token.token_type = TokenType.HTML_ELEMENT
            elif token.token_type in (TokenType.INDENT, TokenType.UNINDENT):
                newline = True
            elif newline:
                first_element = token
                newline = False
            elif token.token == "=":
                self.tokens[i-1].token_type = TokenType.ATTRIBUTE
                self.tokens[i+1].token_type = TokenType.VALUE


class UnknownRuleToken(Exception):
    pass


class Parser:
    def __init__(self, tokens):
        self._tokens: list = tokens
        self._last_correct_token = None
        self._block_stack: list = []
        self._current_indent: int = 0
        self._current_block: list = []
        #self._block_stack.append(self._current_block)
        self._parent_block: list = []

    def get_fncs(self, fnc_name, skip_first=False, current_pos=0):
        fncs: list = []
        rule_fnc = getattr(self, fnc_name, None)
        if rule_fnc is None:
            return fncs
        fncs.append(rule_fnc)
        j: int = 1
        while True:
            rule_fnc = getattr(self, fnc_name + str(j), None)
            if rule_fnc is None:
                return fncs
            else:
                rule_length: int = len(rule_fnc.__doc__)
                for i, fnc in enumerate(fncs):
                    if len(fnc.__doc__) < rule_length:
                        fncs.insert(i, rule_fnc)
                        break
                else:
                    fncs.append(rule_fnc)
            j += 1

    def match(self, fnc_name: str, pos:int=0) -> list | None:
        logger.debug(f"fnc_name: {fnc_name} pos: {pos}")
        rule_fncs: list =  self.get_fncs(fnc_name)
        logger.debug("rule functions: " + str(rule_fncs))
        tokens = self._tokens
        for rule_fnc in rule_fncs:
            logger.debug(f"rule_fnc: {rule_fnc.__name__}")
            rule_tokens = rule_fnc.__doc__.split(" ")
            matched_tokens = []
            return_tokens: list = [(rule_fnc, matched_tokens)]
            logger.debug("rule_tokens: " + str(rule_tokens))
            current_pos: int = pos
            for i, rule_token_name in enumerate(rule_tokens):
                logger.debug(f"rule_token_name: {rule_token_name}")
                if current_pos + i + 1 > len(tokens):
                    logger.debug("no more tokens left (ó﹏ò｡)")
                    break
                token = tokens[current_pos + i]
                logger.debug(f"token: {token}")
                token.pos = current_pos + i
                rule_token = getattr(TokenType, rule_token_name, None)
                logger.debug(f"rule_token: {token.token_type} {rule_token}")
                if rule_token is not None:
                    if token.token_type is rule_token:
                        logger.debug(f"machted token: {token}")
                        matched_tokens.append(token)
                        self._last_correct_token = token
                        continue
                    break
                else:
                    print(f"{rule_token_name} could be another ruleset (ㅅ´ ˘ `)")
                    matches = self.match(rule_token_name, current_pos + i)
                    logger.debug("matches: " + str(matches))
                    if matches is not None:
                        token_count: int = self.count_tokens(matches)
                        #rule_fnc(matched_tokens)
                        logger.debug(f"current_pos: {current_pos}")
                        current_pos += token_count - 1
                        logger.debug(f"new current_pos: {current_pos}")
                        return_tokens += matches
                    else:
                        break
            else:
                #rule_fnc(matched_tokens)
                return return_tokens
        else:
            logger.debug("no function does match (╥﹏╥)")
            return None

    def count_tokens(self, matches: list) -> int:
        """Counts the tokens in each match.
        A match is a tuple that contains the rule function in the first position and a list of all found tokens in the second position.
        matches stucture:
            matches = [(match_fnc1, [token1, token2]), (match_fnc2, [token3, token4, token5])]
        """
        token_count: int = 0
        for match in matches:
            logger.debug(f"match: {match}")
            token_count += len(match[1])
        return token_count

    def parse(self):
        self._current_pos: int = 0
        returned_tokens = self.match("r_html_element", 0)
        if returned_tokens is None:
            print(f"last corret token: {self._last_correct_token}")
        else:
            #print(returned_tokens)
            for rule_fnc, tokens in returned_tokens:
                rule_fnc(tokens)
            logger.info("parsed correctly")

        logger.debug(f"last_correct_token is last_token: {self._tokens[-1] is self._last_correct_token}")
        if not self._tokens[-1] is self._last_correct_token:
            for token in self._tokens[self._last_correct_token.pos + 1:]:
                if token.token_type not in (TokenType.INDENT, TokenType.UNINDENT):
                    raise SyntaxError(token)

    def indent(self, indent, t):

        if isinstance(t, HTMLElement):
            new_block = t
            self._current_block.append(new_block)
            self._parent_block.append(self._current_block)
            self._current_block = new_block
            self._current_indent = len(indent)
        else:
            self._current_block.append(t)

    def unindent(self, indent, t):
        #print("new unindent:", t)
        if self._parent_block:
            self._current_block = self._parent_block.pop()
        if isinstance(t, HTMLElement):
            new_block = t
            self._current_block.append(new_block)
            self._current_block = new_block
        else:
            self._current_block.append(t)
        self._current_indent = len(indent)

    def r_html_element(self, t):
        "HTML_ELEMENT COLON NEWLINE r_html_element"
        self._current_block = HTMLElement("", t[0].token)
        self._block_stack.append(self._current_block)

    def r_html_element1(self, t):
        "INDENT HTML_ELEMENT COLON NEWLINE r_html_element"
        self.indent(t[0].token, HTMLElement(t[0].token, t[1].token))

    def r_html_element12(self, t):
        "HTML_ELEMENT r_html_element_attribute COLON NEWLINE r_html_element"
        self._current_block = HTMLElement("", t[0].token)
        self._block_stack.append(self._current_block)

    def r_html_element13(self, t):
        "HTML_ELEMENT r_html_element_attribute COLON NEWLINE"
        self._current_block = HTMLElement("", t[0].token)
        self._block_stack.append(self._current_block)

    def r_html_element14(self, t):
        "HTML_ELEMENT r_html_element_attribute COLON"
        self._current_block = HTMLElement("", t[0].token)
        self._block_stack.append(self._current_block)

    def r_html_element15(self, t):
        "INDENT HTML_ELEMENT r_html_element_attribute COLON NEWLINE r_html_element"
        self.indent(t[0].token, HTMLElement(t[0].token, t[1].token))

    def r_html_element16(self, t):
        "UNINDENT HTML_ELEMENT r_html_element_attribute COLON NEWLINE r_html_element"
        self.unindent(t[0].token, HTMLElement(t[0].token, t[1].token))

    def r_html_element17(self, t):
        "INDENT HTML_ELEMENT r_html_element_attribute COLON NEWLINE"
        self.indent(t[0].token, HTMLElement(t[0].token, t[1].token))

    def r_html_element18(self, t):
        "UNINDENT HTML_ELEMENT r_html_element_attribute COLON NEWLINE"
        self.unindent(t[0].token, HTMLElement(t[0].token, t[1].token))

    def r_html_element8(self, t):
        "HTML_ELEMENT COLON NEWLINE"
        self._current_block = HTMLElement("", t[0].token)
        self._block_stack.append(self._current_block)

    def r_html_element9(self, t):
        "HTML_ELEMENT COLON"
        self._current_block = HTMLElement("", t[0].token)
        self._block_stack.append(self._current_block)

    def r_html_element2(self, t):
        "UNINDENT HTML_ELEMENT COLON NEWLINE r_html_element"
        self.unindent(t[0].token, HTMLElement(t[0].token, t[1].token))

    def r_html_element3(self, t):
        "HTML_ELEMENT COLON NEWLINE r_html_element_body"
        self._current_block = HTMLElement("", t[0].token)
        self._block_stack.append(self._current_block)

    def r_html_element4(self, t):
        "INDENT HTML_ELEMENT COLON NEWLINE r_html_element_body"
        self.indent(t[0].token, HTMLElement(t[0].token, t[1].token))

    def r_html_element10(self, t):
        "INDENT HTML_ELEMENT r_html_element_attribute COLON NEWLINE r_html_element_body"
        self.indent(t[0].token, HTMLElement(t[0].token, t[1].token))

    def r_html_element11(self, t):
        "UNINDENT HTML_ELEMENT r_html_element_attribute COLON NEWLINE r_html_element_body"
        self.indent(t[0].token, HTMLElement(t[0].token, t[1].token))

    def r_html_element_attribute1(self, t):
        "ATTRIBUTE ASSIGMENT VALUE r_html_element_attribute"
        self._current_block.append(Attribute(t[0].token, t[2].token))

    def r_html_element_attribute(self, t):
        "ATTRIBUTE ASSIGMENT VALUE"
        self._current_block.append(Attribute(t[0].token, t[2].token))

    def r_html_element5(self, t):
        "UNINDENT HTML_ELEMENT COLON NEWLINE r_html_element_body"
        self.unindent(t[0].token, HTMLElement(t[0].token, t[1].token))

    def r_html_element6(self, t):
        "INDENT HTML_ELEMENT COLON NEWLINE"
        self.unindent(t[0].token, HTMLElement(t[0].token, t[1].token))

    def r_html_element7(self, t):
        "UNINDENT HTML_ELEMENT COLON NEWLINE"
        self.unindent(t[0].token, HTMLElement(t[0].token, t[1].token))

    def r_html_element_body(self, t):
        "INDENT ATTRIBUTE ASSIGMENT VALUE NEWLINE r_html_element_body"
        self.indent(t[0].token, Attribute(t[1].token, t[3].token))

    def r_html_element_body1(self, t):
        "UNINDENT ATTRIBUTE ASSIGMENT VALUE NEWLINE r_html_element_body"
        self.unindent(t[0].token, Attribute(t[1].token, t[3].token))

    def r_html_element_body2(self, t):
        "INDENT ATTRIBUTE ASSIGMENT VALUE NEWLINE r_html_element"
        self.indent(t[0].token, Attribute(t[1].token, t[3].token))

    def r_html_element_body3(self, t):
        "UNINDENT ATTRIBUTE ASSIGMENT VALUE NEWLINE r_html_element"
        self.unindent(t[0].token, Attribute(t[1].token, t[3].token))

    def r_html_element_body4(self, t):
        "INDENT ATTRIBUTE ASSIGMENT VALUE NEWLINE"
        self.indent(t[0].token, Attribute(t[1].token, t[3].token))

    def r_html_element_body5(self, t):
        "UNINDENT ATTRIBUTE ASSIGMENT VALUE NEWLINE"
        self.unindent(t[0].token, Attribute(t[1].token, t[3].token))

    def r_html_element_body6(self, t):
        "INDENT ATTRIBUTE ASSIGMENT VALUE"
        self.indent(t[0].token, Attribute(t[1].token, t[3].token))

    def r_html_element_body7(self, t):
        "UNINDENT ATTRIBUTE ASSIGMENT VALUE"
        self.unindent(t[0].token, Attribute(t[1].token, t[3].token))

    def r_html_element_body8(self, t):
        "INDENT ADD_TEXT VALUE NEWLINE r_html_element_body"
        self.indent(t[0].token, AddText(t[2].token))

    def r_html_element_body9(self, t):
        "UNINDENT ADD_TEXT VALUE NEWLINE r_html_element_body"
        self.unindent(t[0].token, AddText(t[2].token))

    def r_html_element_body10(self, t):
        "INDENT ADD_TEXT VALUE NEWLINE r_html_element"
        self.indent(t[0].token, AddText(t[2].token))

    def r_html_element_body11(self, t):
        "UNINDENT ADD_TEXT VALUE NEWLINE r_html_element"
        self.unindent(t[0].token, AddText(t[2].token))

    def r_html_element_body12(self, t):
        "INDENT ADD_TEXT VALUE NEWLINE"
        self.indent(t[0].token, AddText(t[2].token))

    def r_html_element_body13(self, t):
        "UNINDENT ADD_TEXT VALUE NEWLINE"
        self.unindent(t[0].token, AddText(t[2].token))

    def r_html_element_body14(self, t):
        "INDENT ADD_TEXT VALUE"
        self.indent(t[0].token, AddText(t[2].token))

    def r_html_element_body15(self, t):
        "UNINDENT ADD_TEXT VALUE"
        self.unindent(t[0].token, AddText(t[2].token))

    """
    def r_html_element_body8(self, t):
        "INDENT ATTRIBUTE ASSIGMENT STRING r_newline"
        pass

    def r_html_element_body9(self, t):
        "UNINDENT ATTRIBUTE ASSIGMENT STRING r_newline"
        pass

    def r_html_element_body10(self, t):
        "INDENT ATTRIBUTE ASSIGMENT STRING"
        pass

    def r_html_element_body11(self, t):
        "UNINDENT ATTRIBUTE ASSIGMENT STRING"
        pass
    """

    def r_newline(self, t):
        "INDENT NEWLINE r_newline"
        self.indent(t[0].token, t)

    def r_newline1(self, t):
        "UNINDENT NEWLINE r_newline"
        self.unindent(t[0].token, t)

    def r_newline2(self, t):
        "INDENT NEWLINE"
        self.indent(t[0].token, t)

    def r_newline3(self, t):
        "UNINDENT NEWLINE"
        self.unindent(t[0].token, t)

    def r_newline4(self, t):
        "NEWLINE r_newline"

    def r_newline5(self, t):
        "NEWLINE"

    start = r_html_element


class Compiler:

    _print = False
    lines: list = None

    def write(self, src):
        if self._print:
            print(src)
        self.lines.append(src)

    @property
    def src(self) -> str:
        src: str = "\n".join(self.lines)
        return src

    def __init__(self, element):
        self._element = element
        self.lines = []
        self.visit(element)

    def visit(self, element):
        element_name = element.__class__.__name__
        fnc = getattr(self, f"visit_{element_name}")
        fnc(element)

    def visit_Attribute(self, element):
        if element._name == "text":
            self.write(element._value)

    def visit_AddText(self, element):
        self.write(element._value)

    def visit_HTMLElement(self, element):
        tag_name: str = element._tag
        indent: str = element._indent
        attributes: list = []
        html_elements: list = []
        for child_element in element._childs:
            if isinstance(child_element, Attribute):
                attributes.append(str(child_element))
            else:
                html_elements.append(child_element)
        attributes_str: str = " ".join(attributes)
        if attributes_str:
            attributes_str = " " + attributes_str
        self.write(f"{indent}<{tag_name}{attributes_str}>")
        for child_element in html_elements:
            self.visit(child_element)
        self.write(f"{indent}</{tag_name}>")


def main():
    parser = argparse.ArgumentParser(
                    prog='pyhtml',
                    description='pyhtml to html compiler')
    parser.add_argument('pyhtml_file') # positional argument
    parser.add_argument('html_file', nargs="?", default=None) # positional argument
    parser.add_argument('-d', '--debug', action='store_true')
    args = parser.parse_args(sys.argv[1:])

    if args.debug:
        logger.setLevel(logging.DEBUG)

    with open(args.pyhtml_file, "r") as fh:
        src = fh.read()
    print(src)
    html_src: str = compile_pyhtml(src)

    if args.html_file is None:
        html_file: str = str(Path(args.pyhtml_file).with_suffix(''))+".html"
    else:
        html_file: str = args.html_file
    with open(html_file, "w") as fh:
        fh.write(html_src)

    print("Done! (˶ᵔ ᵕ ᵔ˶)")


def compile_pyhtml(src: str) -> str:
    tokenizer: Tokenizer = Tokenizer(src)
    tokenizer.parse()
    print(tokenizer.tokens)
    parser = Parser(tokenizer.tokens)
    parser.parse()
    #print("block stack:", parser._block_stack)
    compiler = Compiler(parser._block_stack[0])
    return compiler.src


if __name__ == "__main__":
    main()
