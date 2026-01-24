from ui.fonts import get_font
from rendering.commands import DrawText

class LineLayout:
    def __init__(self, node, parent, previous):
        self.node = node
        self.parent = parent
        self.previous = previous
        self.children = []
  
    def layout(self):
        self.width = self.parent.width
        self.x = self.parent.x
        
        if self.previous:
            self.y = self.previous.y + self.previous.height
        else:
            self.y = self.parent.y
        
        for word in self.children:
            word.layout()
        
        if not self.children:
            self.height = 0
            return
        
        max_ascent = max([word.font.metrics("ascent") for word in self.children])
        baseline = self.y + 1.25 * max_ascent
        
        for word in self.children:
            word.y = baseline - word.font.metrics("ascent")
        
        max_descent = max([word.font.metrics("descent") for word in self.children])
        self.height = 1.25 * (max_ascent + max_descent)

    def paint(self):
        return []

class TextLayout:
    def __init__(self, node, word, parent, previous):
        self.node = node
        self.word = word
        self.children = []
        self.parent = parent
        self.previous = previous
  
    def layout(self):
        weight = self.node.style["font-weight"]
        style = self.node.style["font-style"]
        
        if not style or style == "":
            style = "normal"
        if style == "normal": 
            style = "roman"
        
        if not weight or weight == "":
            weight = "normal"
        
        if weight.isdigit():
            weight_num = int(weight)
            if weight_num >= 600:
                weight = "bold"
            else:
                weight = "normal"
        elif weight not in ["normal", "bold"]:
            weight = "normal"
        
        font_size = self.node.style.get("font-size") or "16px"
        
        if not font_size or font_size == "":
            font_size = "16px"
        
        if font_size in ["inherit", "initial", "unset"]:
            font_size = "16px"
        
        try:
            size = int(float(font_size[:-2]) * .75)
        except (ValueError, IndexError):
            size = 12
        
        self.font = get_font(size, weight, style)
        
        self.width = self.font.measure(self.word)

        if self.previous:
            space = self.previous.font.measure(" ")
            self.x = self.previous.x + space + self.previous.width
        else:
            self.x = self.parent.x
        
        self.height = self.font.metrics("linespace")

    def paint(self):
        color = self.node.style["color"]
        return [DrawText(self.x, self.y, self.word, self.font, color)]
