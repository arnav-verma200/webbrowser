from style.selectors import TagSelector, DescendantSelector

class CSSParser:
    def __init__(self, s):
        self.s = s
        self.i = 0
    
    def whitespace(self):
        while self.i < len(self.s) and self.s[self.i].isspace():
            self.i += 1
    
    def selector(self):
        out = TagSelector(self.word().casefold())
        self.whitespace()
        while self.i < len(self.s) and self.s[self.i] != "{":
            tag = self.word()
            descendant = TagSelector(tag.casefold())
            out = DescendantSelector(out, descendant)
            self.whitespace()
        return out
    
    def word(self):
        start = self.i
        while self.i < len(self.s):
            if self.s[self.i].isalnum() or self.s[self.i] in "#-.%":
                self.i += 1
            else:
                break
        if self.i == start:
            raise Exception("Parsing error")
        return self.s[start:self.i]
    
    def literal(self, literal):
        if not (self.i < len(self.s) and self.s[self.i] == literal):
            raise Exception("Parsing error")
        self.i += 1
        
    def parse(self):
        rules = []
        while self.i < len(self.s):
            try:
                self.whitespace()
                selector = self.selector()
                self.literal("{")
                self.whitespace()
                body = self.body()
                self.literal("}")
                rules.append((selector, body))
            except Exception:
                why = self.ignore_until(["}"])
                if why == "}":
                    self.literal("}")
                    self.whitespace()
                else:
                    break
        return rules

    def pair(self):
        prop = self.word()
        self.whitespace()
        self.literal(":")
        self.whitespace()
        
        val_start = self.i
        while self.i < len(self.s) and self.s[self.i] not in [";", "}"]:
            self.i += 1
        val = self.s[val_start:self.i].strip()
        
        important = False
        if "!important" in val:
            important = True
            val = val.replace("!important", "").strip()
        
        return prop.casefold(), val, important
    
    def body(self):
        pairs = {}
        while self.i < len(self.s) and self.s[self.i] != "}":
            try:
                prop, val, important = self.pair()
                expanded = self.expand_shorthand(prop, val)
                for key, value in expanded.items():
                    pairs[key] = (value, important)
                self.whitespace()
                self.literal(";")
                self.whitespace()
            except Exception:
                why = self.ignore_until([";", "}"])
                if why == ";":
                    self.literal(";")
                    self.whitespace()
                else:
                    break
        return pairs
    
    def expand_shorthand(self, prop, val):
        expanded = {}
        if prop == "font":
            parts = val.split()
            style = "normal"
            weight = "normal"
            size = None
            for part in parts:
                if part in ["italic", "oblique", "normal"]:
                    style = part
                elif part in ["bold", "bolder", "lighter", "normal"] or part.isdigit():
                    weight = part
                elif any(unit in part for unit in ["px", "%", "em", "pt", "rem"]):
                    size = part
            if size:
                expanded["font-style"] = style
                expanded["font-weight"] = weight
                expanded["font-size"] = size
        elif prop == "margin":
            parts = val.split()
            if len(parts) == 1:
                expanded["margin-top"] = parts[0]
                expanded["margin-right"] = parts[0]
                expanded["margin-bottom"] = parts[0]
                expanded["margin-left"] = parts[0]
            elif len(parts) == 2:
                expanded["margin-top"] = parts[0]
                expanded["margin-bottom"] = parts[0]
                expanded["margin-right"] = parts[1]
                expanded["margin-left"] = parts[1]
            elif len(parts) == 3:
                expanded["margin-top"] = parts[0]
                expanded["margin-right"] = parts[1]
                expanded["margin-left"] = parts[1]
                expanded["margin-bottom"] = parts[2]
            elif len(parts) == 4:
                expanded["margin-top"] = parts[0]
                expanded["margin-right"] = parts[1]
                expanded["margin-bottom"] = parts[2]
                expanded["margin-left"] = parts[3]
        elif prop == "padding":
            parts = val.split()
            if len(parts) == 1:
                expanded["padding-top"] = parts[0]
                expanded["padding-right"] = parts[0]
                expanded["padding-bottom"] = parts[0]
                expanded["padding-left"] = parts[0]
            elif len(parts) == 2:
                expanded["padding-top"] = parts[0]
                expanded["padding-bottom"] = parts[0]
                expanded["padding-right"] = parts[1]
                expanded["padding-left"] = parts[1]
            elif len(parts) == 3:
                expanded["padding-top"] = parts[0]
                expanded["padding-right"] = parts[1]
                expanded["padding-left"] = parts[1]
                expanded["padding-bottom"] = parts[2]
            elif len(parts) == 4:
                expanded["padding-top"] = parts[0]
                expanded["padding-right"] = parts[1]
                expanded["padding-bottom"] = parts[2]
                expanded["padding-left"] = parts[3]
        else:
            expanded[prop] = val
        return expanded
    
    def ignore_until(self, chars):
        while self.i < len(self.s):
            if self.s[self.i] in chars:
                return self.s[self.i]
            else:
                self.i += 1
        return None
