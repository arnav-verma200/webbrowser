from dom.nodes import Text, Element
from config.constants import SELF_CLOSING_TAGS
from .lexer import lex, TextToken, TagToken

class HTMLParser:
    def __init__(self, body):
        self.body = body
        self.unfinished = []
    
    def add_text(self, text):
        if text.isspace():
            return
        if not self.unfinished:
            return
        
        parent = self.unfinished[-1]
        node = Text(text, parent)
        parent.children.append(node)
    
    def get_attributes(self, text):
        parts = []
        current = ""
        in_quotes = False
        quote_char = None
        
        for char in text:
            if char in ['"', "'"]:
                if not in_quotes:
                    in_quotes = True
                    quote_char = char
                elif char == quote_char:
                    in_quotes = False
                    quote_char = None
                current += char
            elif char.isspace() and not in_quotes:
                if current:
                    parts.append(current)
                    current = ""
            else:
                current += char
        
        if current:
            parts.append(current)
        
        if not parts:
            return "", {}
        
        tag = parts[0].casefold()
        attributes = {}
        
        for attrpair in parts[1:]:
            if "=" in attrpair:
                key, value = attrpair.split("=", 1)
                if len(value) > 2 and value[0] in ["'", "\""]:
                    value = value[1:-1]
                attributes[key.casefold()] = value
            else:
                attributes[attrpair.casefold()] = ""
        return tag, attributes
        
    def add_tag(self, tag):
        tag, attributes = self.get_attributes(tag)
        if tag.startswith("!"):
            return
        if tag.startswith("/"):
            if len(self.unfinished) == 1: return
            node = self.unfinished.pop()
            parent = self.unfinished[-1]
            parent.children.append(node)
        elif tag in SELF_CLOSING_TAGS:
            parent = self.unfinished[-1]
            node = Element(tag, attributes, parent)
            parent.children.append(node)
        else:
            parent = self.unfinished[-1] if self.unfinished else None
            node = Element(tag, attributes, parent)
            self.unfinished.append(node)
    
    def finish(self):
        while len(self.unfinished) > 1:
            node = self.unfinished.pop()
            parent = self.unfinished[-1]
            parent.children.append(node)
        return self.unfinished.pop()
    
    def parse(self):
        self.unfinished = [Element("html", {}, None)]
        tokens = lex(self.body)
        
        for token in tokens:
            if isinstance(token, TextToken):
                self.add_text(token.text)
            elif isinstance(token, TagToken):
                self.add_tag(token.tag)
        
        return self.finish()
