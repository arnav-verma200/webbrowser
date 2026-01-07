def layout(self):
  self.x = self.parent.x
  self.y = self.parent.y if not self.previous else \
  self.previous.y + self.previous.height
  self.width = self.parent.width

  mode = self.layout_mode()

  if mode == "block":
    previous = None
    for child in self.node.children:
      next = BlockLayout(child, self, previous)
      self.children.append(next)
      previous = next

    for child in self.children:
      child.layout()

    self.height = sum(child.height for child in self.children)

  else:
    self.cursor_x = HSTEP
    self.cursor_y = VSTEP
    self.weight = "normal"
    self.style = "roman"
    self.size = 12

    self.line = []
    self.recurse(self.node)
    self.flush()

    self.height = self.cursor_y
