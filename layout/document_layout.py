from config.constants import HSTEP, VSTEP, Width
from layout.block_layout import BlockLayout

class DocumentLayout:
    def __init__(self, node):
        self.node = node
        self.children = []
        
        self.parent = None

        self.x = HSTEP
        self.y = VSTEP
        self.width = Width - 2 * HSTEP
        self.height = 0

    def paint(self):
        return []
    
    def layout(self):
        child = BlockLayout(self.node, self, None)
        self.children.append(child)
        child.layout()
        self.height = child.height
