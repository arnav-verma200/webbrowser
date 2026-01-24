from dom.nodes import Element

class TagSelector:
    def __init__(self, tag):
        self.tag = tag
        self.priority = 1
        self.class_name = None

        if tag.startswith("."):
            self.class_name = tag[1:]
            self.tag = None
            self.priority = 10

    def matches(self, node):
        if not isinstance(node, Element):
            return False

        if self.class_name:
            node_classes = node.attributes.get("class", "").split()
            return self.class_name in node_classes

        return self.tag == node.tag

class DescendantSelector:
    def __init__(self, ancestor, descendant):
        if isinstance(ancestor, DescendantSelector):
            self.selectors = ancestor.selectors + [descendant]
        else:
            self.selectors = [ancestor, descendant]

        self.priority = sum(sel.priority for sel in self.selectors)

    def matches(self, node):
        if not self.selectors[-1].matches(node):
            return False

        if len(self.selectors) == 1:
            return True

        selector_idx = len(self.selectors) - 2
        current = node.parent

        while current is not None and selector_idx >= 0:
            if self.selectors[selector_idx].matches(current):
                selector_idx -= 1
            current = current.parent

        return selector_idx < 0

def cascade_priority(rule):
    selector, body = rule
    return selector.priority
