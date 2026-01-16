Element = "not in use"

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
      node_classes = node.attributes.get("class","").split()
      return self.class_name in node_classes

    return self.tag == node.tag


class DescendantSelector:
  def __init__(self, ancestor, descendant):
    # Flatten the selector chain into a list
    # Store from rightmost (most specific) to leftmost (least specific)
    if isinstance(ancestor, DescendantSelector):
      # ancestor is already a chain, extend it
      self.selectors = ancestor.selectors + [descendant]
    else:
      # ancestor is a base selector
      self.selectors = [ancestor, descendant]
    
    # Priority is sum of all selector priorities
    self.priority = sum(sel.priority for sel in self.selectors)
    
  def matches(self, node):
    """
    Fast matching algorithm - O(n + d) time complexity
    where n = number of selectors, d = depth of tree
    
    Strategy: Walk up the tree once, checking selectors right-to-left
    """
    # The rightmost selector must match the current node
    if not self.selectors[-1].matches(node):
      return False
    
    # If only one selector, we're done
    if len(self.selectors) == 1:
      return True
    
    # Walk up the tree, matching selectors from right to left
    # selector_idx points to the selector we're trying to match next
    selector_idx = len(self.selectors) - 2  # Start with second-to-last
    current = node.parent
    
    while current is not None and selector_idx >= 0:
      if self.selectors[selector_idx].matches(current):
        # Found a match! Move to the next selector (going left)
        selector_idx -= 1
      # Keep walking up regardless of match
      current = current.parent
    
    # Success if we matched all selectors
    return selector_idx < 0


# Example of how this improves performance:
# 
# OLD WAY (O(nd) - nested recursion):
# For selector "div div div div div" matching a node at depth 100:
# - Check if rightmost "div" matches node (1 check)
# - For each ancestor (up to 100):
#   - Recursively check "div div div div" against that ancestor
#   - Which itself walks up the tree for "div div div"
#   - And so on... exponential explosion!
# 
# NEW WAY (O(n + d) - single pass):
# For selector "div div div div div" matching a node at depth 100:
# - Check if rightmost "div" matches node (1 check)
# - Walk up the tree once (100 steps max)
# - At each step, check if current ancestor matches next selector (5 checks max)
# - Total: 1 + 100 steps = O(n + d) where n=5, d=100