from config.constants import HSTEP
from dom.nodes import Text, Element
from ui.fonts import get_font
from rendering.commands import DrawRect, DrawText
from layout.geometry import Rect
from layout.inline_layout import LineLayout, TextLayout

class BlockLayout:
    def __init__(self, node, parent=None, previous=None):
        self.node = node
        self.parent = parent
        self.previous = previous
        self.children = []
        
        self.x = None
        self.y = None
        self.width = None
        self.height = None
        
    def new_line(self):
        last_line = self.children[-1] if self.children else None
        new_line = LineLayout(self.node, self, last_line)
        self.children.append(new_line)

    def self_rect(self):
        return Rect(self.x, self.y,
                    self.x + self.width, self.y + self.height)

    def paint(self):
        cmds = []
        
        bgcolor = "transparent"
        
        if isinstance(self.node, Element):
            bgcolor = self.node.style.get("background-color", "transparent")
            if bgcolor.startswith("rgba") or bgcolor.startswith("rgb") or bgcolor.startswith("hsl"):
                bgcolor = "transparent"
            
            if bgcolor != "transparent":
                x2 = self.x + self.width
                y2 = self.y + self.height
                cmds.append(DrawRect(self.x, self.y, x2, y2, bgcolor))
        
        if isinstance(self.node, Element) and self.node.tag == "pre":
            x2 = self.x + self.width
            y2 = self.y + self.height
            cmds.append(DrawRect(self.x, self.y, x2, y2, "gray"))
        
        if isinstance(self.node, Element) and self.node.tag == "nav":
            if self.node.attributes.get("id") == "toc":
                header_height = 25
                header_y = self.y - 25
                cmds.append(DrawRect(self.x, header_y, 
                            self.x + self.width, 
                            header_y + header_height, 
                            "gray"))
                font = get_font(16, "bold", "roman")
                cmds.append(DrawText(
                        self.x + HSTEP, 
                        header_y + 5, 
                        "Table of Contents", 
                        font,
                        "black"
                        ))
        
        if isinstance(self.node, Element) and self.node.tag == "li":
            bullet_x = self.x - HSTEP
            bullet_y = self.y
            bullet_size = 4
            cmds.append(DrawRect(bullet_x, bullet_y, 
                                bullet_x + bullet_size, 
                                bullet_y + bullet_size, 
                                "black"))
        
        return cmds

    def layout_mode(self):
        if isinstance(self.node, Text):
            return "inline"
        elif self.node.children:
            if any(isinstance(child, Element) and child.style.get("display", "inline") == "block" 
                for child in self.node.children):
                return "block"
            else:
                return "inline"
        else:
            return "block"

    def layout(self):
        self.x = self.parent.x

        if isinstance(self.node, Element) and self.node.tag == "li":
            self.x += 2 * HSTEP

        if self.previous:
            self.y = self.previous.y + self.previous.height
        else:
            self.y = self.parent.y

        if isinstance(self.node, Element) and self.node.tag == "nav":
            if self.node.attributes.get("id") == "toc":
                self.y += 25

        if isinstance(self.node, Element):
            width_prop = self.node.style.get("width", "auto")
            if width_prop != "auto":
                try:
                    self.width = int(float(width_prop.replace("px", "")))
                except:
                    self.width = self.parent.width
            else:
                self.width = self.parent.width
        else:
            self.width = self.parent.width

        mode = self.layout_mode()

        if mode == "block":
            previous = None
            for child in self.node.children:
                if isinstance(child, Element) and child.tag == "head":
                    continue

                block = BlockLayout(child, self, previous)
                self.children.append(block)
                previous = block

            for child in self.children:
                child.layout()

        else:
            self.cursor_x = 0
            self.new_line()
            self.recurse(self.node)
            
            for line in self.children:
                line.layout()

        self.height = sum(child.height for child in self.children)

    def layout_intermediate(self):
        previous = None
        for child in self.node.children:
            next = BlockLayout(child, self, previous)
            self.children.append(next)
            previous = next

    def word(self, node, word):
        weight = node.style["font-weight"]
        style = node.style["font-style"]
        
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
        
        font_size = node.style.get("font-size") or "16px"
        
        if not font_size or font_size == "":
            font_size = "16px"
        
        if font_size in ["inherit", "initial", "unset"]:
            font_size = "16px"
        
        try:
            size = int(float(font_size[:-2]) * .75)
        except (ValueError, IndexError):
            size = 12
        
        font = get_font(size, weight, style)
        w = font.measure(word)

        if self.cursor_x + w > self.width:
            self.new_line()
            
        line = self.children[-1]
        previous_word = line.children[-1] if line.children else None
        text = TextLayout(node, word, line, previous_word)
        line.children.append(text)

        self.cursor_x += w + font.measure(" ")

    def recurse(self, node):
        if isinstance(node, Text):
            for word in node.text.split():
                self.word(node, word)
        else:
            for child in node.children:
                self.recurse(child)
