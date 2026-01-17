import tkinter
import socket
import ssl
import os
import time
import tkinter.font
CACHE = {}
FONTS = {}
Height, Width = 600,800
HSTEP, VSTEP = 8, 18
SELF_CLOSING_TAGS = ["area", "base", "br", "col", "embed", "hr", "img", "input",
                      "link", "meta", "param", "source", "track", "wbr"]
LINE_SPACING_MULTIPLIER = 1.25  # Extra spacing between lines

class URL:
  def __init__(self, url):
    if url == "about:blank":
      self.scheme = "about"
      self.path = ""
      return
    
    self.view_source = False
    if url.startswith("view-source:"):
      self.view_source = True
      url = url[len("view-source:"):]
    
    try:
    #cutting url into host, scheme and path
        self.scheme, url = url.split("://", 1)
    except ValueError:
        # Malformed URL → behave like about:blank
        self.scheme = "about"
        self.path = ""
        return
    
    # Unknown scheme → treat as about:blank
    if self.scheme not in ["http", "https", "file"]:
      self.scheme = "about"
      self.path = ""
      return
    
    if self.scheme in ["http", "https"]:  
      if "/" not in url :
        url = url + "/"
      
      self.host, url = url.split("/",1)
      self.path = "/" + url
      
      #saving port for http or https because both have diff ports 
      if self.scheme == "http":
        self.port = 80
      elif self.scheme == "https":
        self.port = 443
        
      if ":" in self.host:
        self.host, port = self.host.split(":", 1)
        self.port = int(port)
    
    
    elif self.scheme in ["file"]:
      # file:///C:/path/to/file.html
      if os.name == "nt" and url.startswith("/"):
        url = url[1:]   # remove leading '/'
      self.path = os.path.normpath(url)


  def request(self, redirect_count=0):
    if self.scheme == "about":
      return ""
    
    #A cache key is like a unique label or address for a specific piece of temporary stored data
    if self.scheme == "file":
      cache_key = f"{self.scheme}://{self.path}"
    else:
      cache_key = f"{self.scheme}://{self.host}{self.path}"

    
    if cache_key in CACHE:
      #checking if cache key exist or not
      entry = CACHE[cache_key]
      if time.time() < entry["expires"]:

        print("-----------------------------------")
        print("cache hit:", cache_key)
        print("-----------------------------------")
        
        return entry["body"]
        #time.time() gets the current "now" time.
        #entry["expires"] is a timestamp in the future when the data becomes invalid.
        #If the current time is less than the expiration time, the data is still fresh. The program
        #returns the stored body immediately, skipping the need for a slow network request.
      else:
        #if time expires it delets the cache
        del CACHE[cache_key]
    
    
    MAX_REDIRECTS = 5

    if redirect_count > MAX_REDIRECTS:
      raise Exception("Too many redirects")
    
    if self.scheme == "file":
      try:
        with open(self.path, "r", encoding="utf8") as f:
          return f.read()
      except FileNotFoundError:
        return "<h1>404 File Not Found</h1>"
      
    #using socket to estabilish the connection
    s = socket.socket(
      family= socket.AF_INET,
      type= socket.SOCK_STREAM,)
    
    s.connect((self.host, self.port)) #establishing the connection
    if self.scheme == "https":
      #used ssl to create a context ctx and use that context to wrap the socket s 
      #that wrap_socket returns a new socket
      ctx = ssl.create_default_context()
      s = ctx.wrap_socket(s, server_hostname=self.host)

    
    request = "GET {} HTTP/1.1\r\n".format(self.path)
    request += "HOST: {}\r\n".format(self.host)
    request += "Connection: close\r\n"  
    request += "\r\n"
    
    s.send(request.encode("utf8")) #sends requests to the server
    
    """
    Also note the encode call. When you send data, it’s important to remember that 
    you are sending raw bits and bytes; they could form text or an image or video. But a
    Python string is specifically for representing text. The encode method converts text 
    into bytes, and there’s a corresponding decode method that goes the other way.
    When you call encode and decode you need to tell the computer what character encoding you
    want it to use. This is a complicated topic. I’m using utf8 here, which is a common character
    encoding and will work on many pages, but in the real world you would need to be more careful.
    """
    
    response = s.makefile("r", encoding="utf8", newline="\r\n")
    statusline = response.readline()
    version, status, explanation = statusline.split(" ", 2)
    status = int(status)
    
    response_headers = {}
    while True:
      line = response.readline()
      if line == "\r\n":
        break
      header, value = line.split(":",1)
      response_headers[header.casefold()] = value.strip()
      
    # redirection handling
    if 300 <= status < 400:
      #if it is redirecting then we get the locations 
      location = response_headers.get("location")
      s.close()

      #if location empty basicly do nothing
      if not location:
        return ""

      #if it is hhts not hhtp
      if location.startswith("http://") or location.startswith("https://"):
        return URL(location).request(redirect_count + 1)
      
      #if nothing from above 
      else:
        new_url = "{}://{}{}".format(self.scheme, self.host, location)
        return URL(new_url).request(redirect_count + 1)
    
    cache_control = response_headers.get("cache-control")
    
    content = response.read()
    s.close()
    
    if cache_control:
      cache_control = cache_control.lower()

      if "no-store" not in cache_control and "max-age=" in cache_control:
        try:
          max_age = int(cache_control.split("max-age=")[1].split(",")[0])
          
          #this just stores the data in the cache
          CACHE[cache_key] = {
            "expires": time.time() + max_age,
            "body": content
          }
          
          print("-----------------------------------")
          print(" Cached:", cache_key, f"(max-age={max_age})")
          print("-----------------------------------")
      
        except:
          pass    
    
    return content
  
  def resolve(self, url):
    # Absolute URL
    if "://" in url:
        return URL(url)

    # Scheme-relative URL
    if url.startswith("//"):
        return URL(self.scheme + ":" + url)

    # FILE URLs (Windows-safe)
    if self.scheme == "file":
        base_dir = os.path.dirname(self.path)
        full_path = os.path.normpath(os.path.join(base_dir, url))
        return URL("file://" + full_path)

    # HTTP / HTTPS relative URLs
    if not url.startswith("/"):
        dir, _ = self.path.rsplit("/", 1)

        while url.startswith("../"):
            url = url[3:]
            if "/" in dir:
                dir, _ = dir.rsplit("/", 1)

        url = dir + "/" + url

    return URL(f"{self.scheme}://{self.host}:{self.port}{url}")


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

  #What this does
  #Collects text outside tags → Text
  #Collects tag contents → Tag
  #Drops unfinished tags (browser-correct behavior)
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


INHERITED_PROPERTIES = {
    "font-size": "16px",
    "font-style": "normal",
    "font-weight": "normal",
    "color": "black",
    "display": "inline",
}


def style(node, rules):
    node.style = {}

    # 1. INHERIT FROM PARENT (or defaults)
    for prop, default in INHERITED_PROPERTIES.items():
        if node.parent:
            node.style[prop] = node.parent.style[prop]
        else:
            node.style[prop] = default

    # 2. COLLECT ALL MATCHING RULES WITH PRIORITIES
    all_properties = {}  # prop -> [(priority, value), ...]
    
    for selector, body in rules:
      if selector.matches(node):
        base_priority = selector.priority
        for prop, (val, important) in body.items():
          priority = base_priority + (10000 if important else 0)
          
          if prop not in all_properties:
            all_properties[prop] = []
          all_properties[prop].append((priority, val))
    
    # Apply highest priority value for each property
    for prop, values in all_properties.items():
      values.sort(key=lambda x: x[0], reverse=True)
      node.style[prop] = values[0][1]

    # 3. APPLY INLINE STYLE
    if isinstance(node, Element) and "style" in node.attributes:
        parser = CSSParser(node.attributes["style"] + ";")
        pairs = parser.body()
        
        for prop, (val, important) in pairs.items():
            inline_priority = 1000 + (10000 if important else 0)
            
            # Check if stylesheet has higher priority !important
            if prop in all_properties:
              max_stylesheet_priority = max(v[0] for v in all_properties[prop])
              if inline_priority > max_stylesheet_priority:
                node.style[prop] = val
            else:
              node.style[prop] = val

    # 4. COMPUTE FONT-SIZE (percent → px)
    if node.style.get("font-size", "").endswith("%"):
        pct = float(node.style["font-size"][:-1]) / 100
        if node.parent:
            parent_font = node.parent.style.get("font-size", "16px")
            if parent_font and parent_font.endswith("px"):
                parent_px = int(parent_font[:-2])
            else:
                parent_px = 16
        else:
            parent_px = int(INHERITED_PROPERTIES["font-size"][:-2])
        node.style["font-size"] = str(int(parent_px * pct)) + "px"

    # 5. RECURSE
    for child in node.children:
        style(child, rules)


def tree_to_list(tree, list):
  list.append(tree)
  for child in tree.children:
    tree_to_list(child, list)
  return list


class Text:
  def __init__(self, text, parent):
    self.text = text
    self.children = []
    self.parent = parent
  def __repr__(self):
    return repr(self.text) 


class Element:
  def __init__(self, tag, attributes, parent):
    self.tag = tag
    self.attributes = attributes
    self.children = []
    self.parent = parent
  def __repr__(self):
    return "<" + self.tag + ">"


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
    if isinstance(ancestor, DescendantSelector):
      self.selectors = ancestor.selectors + [descendant]
    else:
      self.selectors = [ancestor, descendant]
    
    self.priority = sum(sel.priority for sel in self.selectors)
    
  def matches(self, node):
    # The rightmost selector must match the current node
    if not self.selectors[-1].matches(node):
      return False
    
    if len(self.selectors) == 1:
      return True
    
    # Walk up the tree once, matching selectors right to left
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
    
    # Read value until semicolon or closing brace
    val_start = self.i
    while self.i < len(self.s) and self.s[self.i] not in [";", "}"]:
      self.i += 1
    val = self.s[val_start:self.i].strip()
    
    # Check for !important flag
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
    """Expand shorthand properties into individual properties"""
    expanded = {}
    
    if prop == "font":
      # font: [style] [weight] size [family]
      # Examples: "italic bold 100% Times", "bold 16px Arial"
      parts = val.split()
      
      # Defaults
      style = "normal"
      weight = "normal"
      size = None
      
      for part in parts:
        # Check for font-style
        if part in ["italic", "oblique", "normal"]:
          style = part
        # Check for font-weight
        elif part in ["bold", "bolder", "lighter", "normal"] or part.isdigit():
          weight = part
        # Check for font-size (contains px, %, em, or is a number followed by unit)
        elif any(unit in part for unit in ["px", "%", "em", "pt", "rem"]):
          size = part
        # Anything else is treated as font-family (we'll ignore for now)
        
      # Only set properties if we found a valid size
      if size:
        expanded["font-style"] = style
        expanded["font-weight"] = weight
        expanded["font-size"] = size

      else:
        #invalid font shorthand, dont expand
        pass
      
    elif prop == "margin":
      # margin: top [right] [bottom] [left]
      parts = val.split()
      if len(parts) == 1:
        # All sides
        expanded["margin-top"] = parts[0]
        expanded["margin-right"] = parts[0]
        expanded["margin-bottom"] = parts[0]
        expanded["margin-left"] = parts[0]
      elif len(parts) == 2:
        # top/bottom, left/right
        expanded["margin-top"] = parts[0]
        expanded["margin-bottom"] = parts[0]
        expanded["margin-right"] = parts[1]
        expanded["margin-left"] = parts[1]
      elif len(parts) == 3:
        # top, left/right, bottom
        expanded["margin-top"] = parts[0]
        expanded["margin-right"] = parts[1]
        expanded["margin-left"] = parts[1]
        expanded["margin-bottom"] = parts[2]
      elif len(parts) == 4:
        # top, right, bottom, left (clockwise)
        expanded["margin-top"] = parts[0]
        expanded["margin-right"] = parts[1]
        expanded["margin-bottom"] = parts[2]
        expanded["margin-left"] = parts[3]
    
    elif prop == "padding":
      # padding: same logic as margin
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
      # Not a shorthand property, return as-is
      expanded[prop] = val
    
    return expanded
  
  
  def ignore_until(self, chars):
    while self.i < len(self.s):
      if self.s[self.i] in chars:
        return self.s[self.i]
      else:
        self.i += 1
    return None


class HTMLParser:
    def __init__(self, body):
      self.body = body
      self.unfinished = []
    
    def add_text(self, text):
      if text.isspace():
        return
      if not self.unfinished:
        return  # safety: no open tags yet
      
      parent = self.unfinished[-1]
      node = Text(text, parent)
      parent.children.append(node)
    
    def get_attributes(self, text):
      # Don't split on all whitespace - need to handle quoted attributes
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
      
      # Safety check: ignore empty tags
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
        tokens = lex(self.body)  # Use the lex function!
        
        for token in tokens:
            if isinstance(token, TextToken):
                self.add_text(token.text)
            elif isinstance(token, TagToken):
                self.add_tag(token.tag)
        
        return self.finish()


def get_font(size, weight, style):
    key = (size, weight, style)
    if key not in FONTS:
        font = tkinter.font.Font(size=size, weight=weight,
            slant=style)
        label = tkinter.Label(font=font)
        FONTS[key] = (font, label)
    return FONTS[key][0]


def paint_tree(layout_object, display_list):
    display_list.extend(layout_object.paint())

    for child in layout_object.children:
        paint_tree(child, display_list)


class DrawText:
  def __init__(self, x1, y1, text, font, color):
    self.top = y1
    self.left = x1
    self.text = text
    self.font = font
    self.color = color
    
    self.bottom = y1 + font.metrics("linespace")
  
  def execute(self, scroll, canvas):
    if hasattr(self, "color"):
        if not self.color.startswith(("rgba", "rgb", "hsl")):
            fill = self.color

    canvas.create_text(
        self.left, self.top - scroll,
        text=self.text,
        font=self.font,
        fill=self.color,
        anchor='nw')


class DrawRect:
  def __init__(self, x1, y1, x2, y2, color):
    self.top = y1
    self.left = x1
    self.bottom = y2
    self.right = x2
    self.color = color
    
  def execute(self, scroll, canvas):
    canvas.create_rectangle(
      self.left, self.top - scroll,
      self.right, self.bottom - scroll,
      width=0,
      fill=self.color)


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
      
      # Safety check: ensure style is valid
      if not style or style == "":
        style = "normal"
      if style == "normal": 
        style = "roman"
      
      # Safety check: ensure weight is valid
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
      
      # Safety check: ensure font-size is valid
      if not font_size or font_size == "":
        font_size = "16px"
        
      if font_size in ["inherit", "initial", "unset"]:
        font_size = "16px"
      
      try:
        size = int(float(font_size[:-2]) * .75)
      except (ValueError, IndexError):
        size = 12  # default size after .75 multiplier
      
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


class BlockLayout:
    # BlockLayout of characters, walking the node tree
    def __init__(self, node, parent= None, previous= None):
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
        
    def paint(self):
      cmds = []
      
      if isinstance(self.node, Element):
              bgcolor = self.node.style.get("background-color", "transparent")

              # Ignore unsupported CSS colors (rgba, rgb, hsl, etc.)
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
          # Draw gray background for header
          header_height = 25  # height for the header
          cmds.append(DrawRect(self.x, self.y, 
                      self.x + self.width, 
                      self.y + header_height, 
                      "gray"))
          # Draw "Table of Contents" text
          font = get_font(16, "bold", "roman")
          cmds.append(DrawText(
                    self.x + HSTEP, 
                    self.y + 5, 
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
      # -------- position --------
      self.x = self.parent.x

      if isinstance(self.node, Element) and self.node.tag == "li":
        self.x += 2 * HSTEP  # indent list items

      if self.previous:
        self.y = self.previous.y + self.previous.height
      else:
        self.y = self.parent.y

      if isinstance(self.node, Element) and self.node.tag == "nav":
        if self.node.attributes.get("id") == "toc":
          self.y += 25  # space for header

      # -------- width --------
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

      # -------- layout mode --------
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
        # inline layout
        self.cursor_x = 0
        self.new_line()
        self.recurse(self.node)
        
        for line in self.children:
          line.layout()

      # -------- height --------
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
        
        # Safety check: ensure style is valid
        if not style or style == "":
          style = "normal"
        if style == "normal":
          style = "roman"
        
        # Safety check: ensure weight is valid
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
        
        # Safety check: ensure font-size is valid
        if not font_size or font_size == "":
          font_size = "16px"
          
        if font_size in ["inherit", "initial", "unset"]:
          font_size = "16px"
        
        try:
          size = int(float(font_size[:-2]) * .75)
        except (ValueError, IndexError):
          size = 12  # default size after .75 multiplier
        
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
        # recursive function to walk the node tree
        if isinstance(node, Text):
            for word in node.text.split():
                self.word(node, word)
        else:
            for child in node.children:
              self.recurse(child)


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


try:
# Load default stylesheet
  DEFAULT_STYLE_SHEET = CSSParser(open("browser.css").read()).parse()
except FileNotFoundError:
  DEFAULT_STYLE_SHEET = []


class Browser:
  def __init__(self):
    self.window = tkinter.Tk()
    
    self.window.title("Web Browser")

    # Create URL bar at the top
    self.url_frame = tkinter.Frame(self.window)
    self.url_frame.pack(side="top", fill="x", padx=5, pady=5)

    url_label = tkinter.Label(self.url_frame, text="URL:")
    url_label.pack(side="left")

    self.url_entry = tkinter.Entry(self.url_frame, width=80)
    self.url_entry.pack(side="left", fill="x", expand=True, padx=5)
    
    self.scrollbar = tkinter.Scrollbar(self.window, orient="vertical") #creating the window scrollbar
    self.scrollbar.pack(side="right", fill="y") #same as above
    self.scrollbar.config(command=self.on_scrollbar) #connect scrollbar to scroll logic
    
    self.display_list = []

        
    self.window.bind("<Configure>", self.on_resize) #<Configure> fires whenever: window resizes, window moves, BlockLayout changes
    self.canvas = tkinter.Canvas(
      self.window,
      width=Width,
      height=Height,
      bg="white"
    )
    
    #pack() tells: “Put this widget inside its parent window”
    #fill="both" tells: "Stretch this widget to fill available space"
    #expand=True tells: “If there is extra space, give it to THIS widget”
    self.canvas.pack(fill="both", expand=True)
    self.scroll = 0 #how much we scrolled 
    self.window.bind("<Down>", self.scrolldown) #binding the buttons to scroll down
    self.window.bind("<Up>", self.scrollup) #binding the buttons to scroll up
    
    self.window.bind("<MouseWheel>", self.mousewheel)  # using mouse wheel to scroll
    self.scroll_step = 100 #how much it should scroll in one tap of button

  def draw(self):
    self.canvas.delete("all")
    for cmd in self.display_list:
      if cmd.top > self.scroll + Height: continue
      if cmd.bottom < self.scroll: continue
      cmd.execute(self.scroll, self.canvas)

  def scrollup(self, e): #scroll up function
    self.scroll -= self.scroll_step
    if self.scroll < 0:
      self.scroll = 0
    self.draw()
    
  def scrolldown(self, e): #scroll down function
    if not self.display_list:
      return
    self.scroll += self.scroll_step
    max_y = self.display_list[-1].bottom
    max_scroll = max(0, max_y - Height)
    if self.scroll > max_scroll:
      self.scroll = max_scroll
    self.draw()
    
  def mousewheel(self, event):
    if not self.display_list:
      return
    self.scroll -= event.delta  # wheel up = positive delta
    """Why event.delta works
        On Windows:
        Scroll up → event.delta = +120
        Scroll down → event.delta = -120"""
    max_y = self.display_list[-1].bottom
    max_scroll = max(0, max_y - Height)
    if self.scroll < 0:
        self.scroll = 0
    if self.scroll > max_scroll:
        self.scroll = max_scroll
    self.draw()
  
  def on_scrollbar(self, action, value, units=None):
    if not self.display_list:
      return

    if action == "moveto":
      fraction = float(value)
      max_y = self.display_list[-1].bottom
      max_scroll = max(0, max_y - Height)
      self.scroll = int(fraction * max_scroll)
      self.draw()

    elif action == "scroll":
      amount = int(value)
      if units == "units":
        self.scroll += amount * 20
      elif units == "pages":
        self.scroll += amount * Height

      self.scroll = max(0, self.scroll)
      self.draw()

  def on_resize(self, event):
      #resizing of a window
      global Width, Height

      if event.width < 100 or event.height < 100:
          return

      Width = event.width
      Height = event.height

      if not hasattr(self, "document"):
          return

      self.document.width = Width - 2 * HSTEP
      self.document.children = []
      self.document.layout()

      self.display_list = []
      paint_tree(self.document, self.display_list)
      self.draw()

  def load(self, url):
      # Store and display the URL
      self.current_url = url
      if url.scheme == "file":
        display_url = f"file://{url.path}"
      elif url.scheme == "about":
        display_url = "about:blank"
      else:
        display_url = f"{url.scheme}://{url.host}{url.path}"
      
      self.url_entry.delete(0, tkinter.END)
      self.url_entry.insert(0, display_url)
      
      body = url.request()

      if getattr(url, "view_source", False):
        print(body)
        return

      # parse HTML → DOM
      self.nodes = HTMLParser(body).parse()
      # Start with default styles
      rules = DEFAULT_STYLE_SHEET.copy()
      
      # Load external stylesheets from <link> tags
      links = [node.attributes["href"]
              for node in tree_to_list(self.nodes, [])
              if isinstance(node, Element)
              and node.tag == "link"
              and node.attributes.get("rel") == "stylesheet"
              and "href" in node.attributes]
      
      for link in links:
        style_url = url.resolve(link)
        try:
          body = style_url.request()
        except:
          continue
        rules.extend(CSSParser(body).parse())

      # APPLY CSS STYLES (including inline styles)
      style(self.nodes, rules)

      # DOM → layout tree
      self.document = DocumentLayout(self.nodes)
      self.document.layout()

      # layout → display list
      self.display_list = []
      paint_tree(self.document, self.display_list)

      self.scroll = 0
      self.draw()


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python browser.py <URL>")
        sys.exit(1)
    url = URL(sys.argv[1])
    browser = Browser()
    browser.load(url)
    tkinter.mainloop()
