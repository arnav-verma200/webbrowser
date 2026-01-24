class TextToken:
    def __init__(self, text):
        self.text = text
    def __repr__(self):
        return repr(self.text)

class TagToken:
    def __init__(self, tag):
        self.tag = tag.strip().casefold()
    def __repr__(self):
        return "<" + self.tag + ">"

def lex(body):
    out = []
    buffer = ""
    in_tag = False
    for c in body:
        if c == "<":
            if buffer: 
                out.append(TextToken(buffer))
                buffer = ""
            in_tag = True
        elif c == ">":
            out.append(TagToken(buffer))
            buffer = ""
            in_tag = False
        else:
            buffer += c
            
    if buffer and not in_tag:
        out.append(TextToken(buffer))
    
    return out
