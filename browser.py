import tkinter
import socket
import ssl
import os
import time
import tkinter.font
CACHE = {}
FONTS = {}
VISITED_URLS = set()
Height, Width = 600,800
HSTEP, VSTEP = 8, 18
SELF_CLOSING_TAGS = ["area", "base", "br", "col", "embed", "hr", "img", "input",
                      "link", "meta", "param", "source", "track", "wbr"]
LINE_SPACING_MULTIPLIER = 1.25  # Extra spacing between lines


# Handles URL parsing, scheme detection, and HTTP/HTTPS requests with caching
class URL:
  
  def __init__(self, url):
    self.fragment = None
    
    # Add this new check FIRST
    if url.startswith("about:"):
      self.scheme = "about"
      self.path = url[6:]  # Remove "about:" prefix
      return

    if url == "bookmarks":
      self.scheme = "bookmarks"
      self.path = ""
      return
    
    self.view_source = False
    if url.startswith("view-source:"):
      self.view_source = True
      url = url[len("view-source:"):]
    
    # ... rest stays the same
    
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
      
      # Fragment is already initialized above, now parse it
      if "#" in self.path:
        self.path, self.fragment = self.path.split("#", 1)
      
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
    
  def __str__(self):
    if self.scheme == "about":
      return f"about:{self.path}"
    elif self.scheme == "bookmarks":
      return "bookmarks"
    
    port_part = ":" + str(self.port)
    if self.scheme == "https" and self.port == 443:
        port_part = ""
    if self.scheme == "http" and self.port == 80:
        port_part = ""
    return self.scheme + "://" + self.host + port_part + self.path

  def request(self, redirect_count=0):
    if self.scheme == "about" or self.scheme == "bookmarks":
      if self.path == "bookmarks" or self.scheme == "bookmarks":
        return BOOKMARK_MANAGER.generate_page_html()
      elif self.path == "":
        return ""
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
    # Don't resolve relative URLs for special schemes
    if self.scheme in ["about", "bookmarks"]:
      if "://" in url:
        return URL(url)
      return self  # Can't resolve relative URLs for special schemes
    
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


# Represents text content tokens from HTML parsing
class TextToken:
  def __init__(self, text):
    self.text = text

  def __repr__(self):
    return repr(self.text)


# Represents HTML tag tokens from lexing
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


def style(node, rules, url):
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

    if isinstance(node, Element) and node.tag == "a" and "href" in node.attributes:
        if str(url.resolve(node.attributes["href"])) in VISITED_URLS:
            node.style["color"] = "purple"
    # 5. RECURSE
    for child in node.children:
        style(child, rules, url)



def tree_to_list(tree, list):
  list.append(tree)
  for child in tree.children:
    tree_to_list(child, list)
  return list


# Represents text nodes in the DOM tree
class Text:
  def __init__(self, text, parent):
    self.text = text
    self.children = []
    self.parent = parent
  def __repr__(self):
    return repr(self.text) 


# Represents HTML element nodes with tags and attributes
class Element:
  def __init__(self, tag, attributes, parent):
    self.tag = tag
    self.attributes = attributes
    self.children = []
    self.parent = parent
  def __repr__(self):
    return "<" + self.tag + ">"


# Selects DOM elements by tag name or CSS class
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


# Selects elements based on ancestor-descendant relationships
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


# Parses CSS stylesheets into rules and properties
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


# Parses HTML strings into a DOM tree structure
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


# Command to draw text on the canvas
class DrawText:
  def __init__(self, x1, y1, text, font, color):
    self.top = y1
    self.left = x1
    self.text = text
    self.font = font
    self.color = color
    
    self.bottom = y1 + font.metrics("linespace")
  
  def execute(self, scroll, canvas):
    fill = "black"  # Default fallback
    
    if hasattr(self, "color"):
      if not self.color.startswith(("rgba", "rgb", "hsl")):
        fill = self.color
      else:
        fill = "black"  # Fallback for unsupported colors

    canvas.create_text(
      self.left, self.top - scroll,
      text=self.text,
      font=self.font,
      fill=fill,
      anchor='nw')


# Command to draw filled rectangles on the canvas
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


# Lays out text content into horizontal lines
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


# Lays out individual words within a line
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


# Lays out block-level HTML elements
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

    def self_rect(self):
      return Rect(self.x, self.y,
                  self.x + self.width, self.y + self.height)

    def paint(self):
      cmds = []
      
      bgcolor = "transparent"
      
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
          # Draw gray background for header at the TOP of the nav element
          header_height = 25
          header_y = self.y - 25  # Position ABOVE the content
          cmds.append(DrawRect(self.x, header_y, 
                      self.x + self.width, 
                      header_y + header_height, 
                      "gray"))
          # Draw "Table of Contents" text
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


# Lays out the entire document structure
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


class BookmarkManager:
    def __init__(self, filename="bookmarks.txt"):
        self.filename = filename
        self.bookmarks = set()
        self.load()
    
    def load(self):
        """Load bookmarks from file"""
        if os.path.exists(self.filename):
            try:
                with open(self.filename, "r", encoding="utf-8") as f:
                    self.bookmarks = set(line.strip() for line in f if line.strip())
            except Exception as e:
                print(f"Error loading bookmarks: {e}")
                self.bookmarks = set()
    
    def save(self):
        """Save bookmarks to file"""
        try:
            with open(self.filename, "w", encoding="utf-8") as f:
                for bookmark in sorted(self.bookmarks):
                    f.write(bookmark + "\n")
        except Exception as e:
            print(f"Error saving bookmarks: {e}")
    
    def add(self, url):
        """Add a bookmark"""
        self.bookmarks.add(url)
        self.save()
    
    def remove(self, url):
        """Remove a bookmark"""
        if url in self.bookmarks:
            self.bookmarks.discard(url)
            self.save()
    
    def toggle(self, url):
        """Toggle bookmark status"""
        if url in self.bookmarks:
            self.remove(url)
        else:
            self.add(url)
    
    def contains(self, url):
        """Check if URL is bookmarked"""
        return url in self.bookmarks
    
    def generate_page_html(self):
        """Generate HTML for bookmarks page"""
        html = """
<!DOCTYPE html>
<html>
<head><title>Bookmarks</title></head>
<body>
<h1>Bookmarks</h1>
"""
        if not self.bookmarks:
            html += "<p>No bookmarks yet. Click the ★ button to bookmark a page.</p>"
        else:
            html += "<ul>"
            for bookmark in sorted(self.bookmarks):
                html += f'<li><a href="{bookmark}">{bookmark}</a></li>'
            html += "</ul>"
        
        html += "</body></html>"
        return html
# Create global bookmark manager
BOOKMARK_MANAGER = BookmarkManager()


try:
# Load default stylesheet
  DEFAULT_STYLE_SHEET = CSSParser(open("browser.css").read()).parse()
except FileNotFoundError:
  DEFAULT_STYLE_SHEET = []


# Command to draw rectangle outlines on the canvas
class DrawOutline:
  def __init__(self, rect, color, thickness):
    self.rect = rect
    self.color = color
    self.thickness = thickness

  def execute(self, scroll, canvas):
    canvas.create_rectangle(
            self.rect.left, self.rect.top - scroll,
            self.rect.right, self.rect.bottom - scroll,
            width=self.thickness,
            outline=self.color)


# Command to draw lines on the canvas
class DrawLine:
  def __init__(self, x1, y1, x2, y2, color, thickness):
    self.rect = Rect(x1, y1, x2, y2)
    self.color = color
    self.thickness = thickness

  def execute(self, scroll, canvas):
    canvas.create_line(
            self.rect.left, self.rect.top - scroll,
            self.rect.right, self.rect.bottom - scroll,
            fill=self.color, width=self.thickness)


# Manages the browser's user interface chrome (tabs, address bar, buttons)
class Chrome:
  def __init__(self, browser):
    self.browser = browser
    
    self.font = get_font(20, "normal", "roman")
    self.font_height = self.font.metrics("linespace")
    
    self.padding = 5
    self.tabbar_top = 0
    self.tabbar_bottom = self.font_height + 2*self.padding
    
    plus_width = self.font.measure("+") + 2*self.padding
    self.newtab_rect = Rect(
      self.padding, self.padding,
      self.padding + plus_width,
      self.padding + self.font_height)
    
    self.bottom = self.tabbar_bottom
    
    self.urlbar_top = self.tabbar_bottom
    self.urlbar_bottom = self.urlbar_top + \
      self.font_height + 2*self.padding
    self.bottom = self.urlbar_bottom
    
    back_width = self.font.measure("<") + 2*self.padding
    self.back_rect = Rect(
      self.padding,
      self.urlbar_top + self.padding,
      self.padding + back_width,
      self.urlbar_bottom - self.padding)
    
    forward_width = self.font.measure(">") + 2*self.padding
    self.forward_rect = Rect(
      self.back_rect.right + self.padding,
      self.urlbar_top + self.padding,
      self.back_rect.right + self.padding + forward_width,
      self.urlbar_bottom - self.padding)

    # Bookmark toggle button (star)
    bookmark_width = self.font.measure("★") + 2*self.padding
    self.bookmark_rect = Rect(
      self.forward_rect.right + self.padding,
      self.urlbar_top + self.padding,
      self.forward_rect.right + self.padding + bookmark_width,
      self.urlbar_bottom - self.padding)

    # ADD THIS: Bookmarks list button (folder icon)
    bookmarks_list_width = self.font.measure("☰") + 2*self.padding
    self.bookmarks_list_rect = Rect(
      self.bookmark_rect.right + self.padding,
      self.urlbar_top + self.padding,
      self.bookmark_rect.right + self.padding + bookmarks_list_width,
      self.urlbar_bottom - self.padding)

    # Update address bar to start after bookmarks list button
    self.address_rect = Rect(
      self.bookmarks_list_rect.right + self.padding,
      self.urlbar_top + self.padding,
      Width - self.padding,
      self.urlbar_bottom - self.padding)
    
    self.focus = None
    self.address_bar = ""
    self.cursor_position = 0
  
  def copy(self):
    if self.focus == "address bar":
      import tkinter as tk
      self.browser.window.clipboard_clear()
      self.browser.window.clipboard_append(self.address_bar)

  def paste(self):
    if self.focus == "address bar":
      import tkinter as tk
      try:
        clipboard_text = self.browser.window.clipboard_get()
        # Insert at cursor position
        self.address_bar = (self.address_bar[:self.cursor_position] + 
                          clipboard_text + 
                          self.address_bar[self.cursor_position:])
        self.cursor_position += len(clipboard_text)
      except:
        pass  # Clipboard empty or unavailable

  def tab_rect(self, i):
    tabs_start = self.newtab_rect.right + self.padding
    tab_width = self.font.measure("Tab X ") + self.font.measure("X") + 4*self.padding
    return Rect(
      tabs_start + tab_width * i, self.tabbar_top,
      tabs_start + tab_width * (i + 1), self.tabbar_bottom)

  def close_button_rect(self, i):
    tab_bounds = self.tab_rect(i)
    close_size = self.font.measure("X")
    return Rect(
      tab_bounds.right - close_size - 2*self.padding,
      tab_bounds.top + self.padding,
      tab_bounds.right - self.padding,
      tab_bounds.bottom - self.padding)

  def paint(self):
    cmds = []
    
    # Draw white background for entire tab bar FIRST
    cmds.append(DrawRect(
      0, 0,
      Width, self.bottom,
      "white"))
    
    # Draw all tabs
    for i, tab in enumerate(self.browser.tabs):
      bounds = self.tab_rect(i)
      
      # Highlight active tab with light background
      if tab == self.browser.active_tab:
        cmds.append(DrawRect(
          bounds.left, bounds.top,
          bounds.right, bounds.bottom,
          "lightgray"))
      
      # Draw tab vertical separators
      cmds.append(DrawLine(
      bounds.left, bounds.top, bounds.left, bounds.bottom,
      "black", 1))
      cmds.append(DrawLine(
      bounds.right, bounds.top, bounds.right, bounds.bottom,
      "black", 1))
      
      # Draw tab label
      cmds.append(DrawText(
        bounds.left + self.padding, bounds.top + self.padding,
        "Tab {}".format(i), self.font, "black"))

      # Draw vertical line before close button
      close_rect = self.close_button_rect(i)
      cmds.append(DrawLine(
        close_rect.left - self.padding, bounds.top,
        close_rect.left - self.padding, bounds.bottom,
        "black", 1))
      
      # Draw close button (X)
      close_rect = self.close_button_rect(i)
      cmds.append(DrawText(
        close_rect.left, close_rect.top,
        "X", self.font, "black"))
    
    # Draw back button (replace existing code)
    can_go_back = self.browser.active_tab.history_index > 0
    back_color = "black" if can_go_back else "gray"

    cmds.append(DrawOutline(self.back_rect, "black", 1))
    cmds.append(DrawText(
          self.back_rect.left + self.padding,
          self.back_rect.top,
          "<", self.font, back_color))
    
    # Draw forward button
    can_go_forward = (self.browser.active_tab.history_index < 
                      len(self.browser.active_tab.history) - 1)
    forward_color = "black" if can_go_forward else "gray"

    cmds.append(DrawOutline(self.forward_rect, "black", 1))
    cmds.append(DrawText(
      self.forward_rect.left + self.padding,
      self.forward_rect.top,
      ">", self.font, forward_color))
    
    # Draw bookmark button (optimized)
    current_url = str(self.browser.active_tab.url)
    is_bookmarked = BOOKMARK_MANAGER.contains(current_url)
    show_bookmark = self.browser.active_tab.url.scheme in ["http", "https"]

    if show_bookmark:
      bookmark_color = "gold" if is_bookmarked else "white"
        
      cmds.append(DrawRect(
          self.bookmark_rect.left, self.bookmark_rect.top,
          self.bookmark_rect.right, self.bookmark_rect.bottom,
          bookmark_color))
        
      cmds.append(DrawOutline(self.bookmark_rect, "black", 1))
      cmds.append(DrawText(
          self.bookmark_rect.left + self.padding,
          self.bookmark_rect.top,
          "★", self.font, "black"))

    # Draw bookmarks list button
    cmds.append(DrawOutline(self.bookmarks_list_rect, "black", 1))
    cmds.append(DrawText(
          self.bookmarks_list_rect.left + self.padding,
          self.bookmarks_list_rect.top,
          "☰", self.font, "black"))
    
    # Draw the "+" button
    cmds.append(DrawOutline(self.newtab_rect, "black", 1))
    cmds.append(DrawText(
      self.newtab_rect.left + self.padding,
      self.newtab_rect.top,
      "+", self.font, "black"))
    
    # Draw address bar outline
    cmds.append(DrawOutline(self.address_rect, "black", 1))
    if self.focus == "address bar":
      cmds.append(DrawText(
                self.address_rect.left + self.padding,
                self.address_rect.top,
                self.address_bar, self.font, "black"))
      
      # Draw cursor at cursor_position instead of at the end
      w = self.font.measure(self.address_bar[:self.cursor_position])
      cmds.append(DrawLine(
                self.address_rect.left + self.padding + w,
                self.address_rect.top,
                self.address_rect.left + self.padding + w,
                self.address_rect.bottom,
                "red", 1))
      
    else:
      url = str(self.browser.active_tab.url)
      cmds.append(DrawText(
                self.address_rect.left + self.padding,
                self.address_rect.top,
                url, self.font, "black"))
    
    # Draw bottom border of tab bar (separates tabs from content)
    cmds.append(DrawLine(
      0, self.bottom, Width, self.bottom, 
      "black", 1))
    
    
    return cmds

  def keypress(self, char):
    if self.focus == "address bar":
      # Insert character at cursor position
      self.address_bar = (self.address_bar[:self.cursor_position] + 
                        char + 
                        self.address_bar[self.cursor_position:])
      self.cursor_position += 1

  def backspace(self):
    if self.focus == "address bar":
      if self.cursor_position > 0:
        # Delete character before cursor
        self.address_bar = (self.address_bar[:self.cursor_position - 1] + 
                          self.address_bar[self.cursor_position:])
        self.cursor_position -= 1

  def enter(self):
    if self.focus == "address bar":
      self.browser.active_tab.load(URL(self.address_bar))
      self.focus = None
      self.cursor_position = 0

  def click(self, x, y):
      self.focus = None
      
      if self.newtab_rect.contains_point(x, y):
        self.browser.new_tab(URL("https://browser.engineering/"))
      else:
        for i, tab in enumerate(self.browser.tabs):
          # Check close button first
          if self.close_button_rect(i).contains_point(x, y):
            self.browser.close_tab(tab)
            return
          
          elif self.tab_rect(i).contains_point(x, y):
            self.browser.active_tab = tab
            self.browser.draw()
            return
        
        if self.back_rect.contains_point(x, y):
          self.browser.active_tab.go_back()

        elif self.forward_rect.contains_point(x, y):
          self.browser.active_tab.go_forward()

        elif self.bookmark_rect.contains_point(x, y):
          if self.browser.active_tab.url.scheme in ["http", "https"]:
              self.toggle_bookmark()
        
        # ADD THIS: Handle bookmarks list button click
        elif self.bookmarks_list_rect.contains_point(x, y):
          self.browser.active_tab.load(URL("about:bookmarks"))

        elif self.address_rect.contains_point(x, y):
          self.focus = "address bar"
          self.address_bar = ""
          self.cursor_position = 0

  def move_cursor_left(self):
    if self.focus == "address bar":
      if self.cursor_position > 0:
        self.cursor_position -= 1

  def move_cursor_right(self):
    if self.focus == "address bar":
      if self.cursor_position < len(self.address_bar):
        self.cursor_position += 1

  def toggle_bookmark(self):
    current_url = str(self.browser.active_tab.url)
    # Only allow bookmarking http/https URLs
    if self.browser.active_tab.url.scheme in ["http", "https"]:
        BOOKMARK_MANAGER.toggle(current_url)


# Represents rectangular areas for layout calculations
class Rect:
  def __init__(self, left, top, right, bottom):
    self.left = left
    self.top = top
    self.right = right
    self.bottom = bottom
  
  def contains_point(self, x, y):
    return x >= self.left and x < self.right \
      and y >= self.top and y < self.bottom


# Represents a browser tab containing a web page
class Tab:
  def __init__(self, tab_height):
    self.display_list = []
    self.scroll = 0 #how much we scrolled     
    self.scroll_step = 100 #how much it should scroll in one tap of button
    self.url = None
    self.tab_height = tab_height
    self.history = []
    self.history_index = -1

  def get_title(self):
    # Find the <title> element in the document
    title_nodes = [node for node in tree_to_list(self.nodes, [])
                  if isinstance(node, Element) and node.tag == "title"]
    
    if not title_nodes:
      return "Untitled"
    
    # Get text content from the title element
    title_text = ""
    for child in title_nodes[0].children:
      if isinstance(child, Text):
        title_text += child.text
  
    return title_text.strip() if title_text.strip() else "Untitled"

  def on_url_submit(self, event):
    url_text = self.url_entry.get()
    try:
      new_url = URL(url_text)
      self.load(new_url)
    except:
      pass

  def click(self, x, y, middle_click = False):
    y += self.scroll
    
    objs = [obj for obj in tree_to_list(self.document, [])
            if obj.x <= x < obj.x + obj.width
            and obj.y <= y < obj.y + obj.height]
    
    if not objs : return
    elt = objs[-1].node
    
    while elt:
      if isinstance(elt, Text):
        pass
      elif elt.tag == "a" and "href" in elt.attributes:
        href = elt.attributes["href"]
        if href.startswith("#"):
            # Find the element with that id
            elt_id = href[1:]
            target_elt = [node for node in tree_to_list(self.nodes, [])
                          if isinstance(node, Element)
                          and node.attributes.get("id") == elt_id]
            if target_elt:
                # Find the layout object for the element
                obj = [obj for obj in tree_to_list(self.document, [])
                      if obj.node == target_elt[0]]
                if obj:
                    self.scroll = obj[0].y
            return
        
        url = self.url.resolve(elt.attributes["href"])
        if middle_click:
          return url
        else:
          return self.load(url)
      elt = elt.parent
  
  def draw(self, canvas, offset):
    for cmd in self.display_list:
      if cmd.top > self.scroll + Height: continue
      if cmd.bottom < self.scroll: continue
      cmd.execute(self.scroll - offset, canvas)

  def scrollup(self): #scroll up function
    self.scroll -= self.scroll_step
    if self.scroll < 0:
      self.scroll = 0
    
  def scrolldown(self):
    if not self.display_list:
      return
    max_y = max(
      self.document.height + 2*VSTEP - self.tab_height, 0)
    self.scroll = min(self.scroll + self.scroll_step, max_y)
    max_scroll = max(0, max_y - Height)
    if self.scroll > max_scroll:
      self.scroll = max_scroll
    
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
  
  def on_scrollbar(self, action, value, units=None):
    if not self.display_list:
      return

    if action == "moveto":
      fraction = float(value)
      max_y = self.display_list[-1].bottom
      max_scroll = max(0, max_y - Height)
      self.scroll = int(fraction * max_scroll)

    elif action == "scroll":
      amount = int(value)
      if units == "units":
        self.scroll += amount * 20
      elif units == "pages":
        self.scroll += amount * Height

      self.scroll = max(0, self.scroll)

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

  def go_back(self):
    if self.history_index > 0:
      self.history_index -= 1
      self.load(self.history[self.history_index], from_history=True)

  def go_forward(self):
    if self.history_index < len(self.history) - 1:
      self.history_index += 1
      self.load(self.history[self.history_index], from_history=True)

  def load(self, url, from_history=False):
      if not from_history:
        # Remove forward history when navigating normally
        self.history = self.history[:self.history_index + 1]
        self.history.append(url)
        self.history_index = len(self.history) - 1
      
      self.url = url
      
      # Only track normal URLs, not special schemes
      if url.scheme in ["http", "https"]:
        VISITED_URLS.add(str(url))
      
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
      style(self.nodes, rules, url)

      # DOM → layout tree
      self.document = DocumentLayout(self.nodes)
      self.document.layout()

      if url.fragment:
        elt = [node for node in tree_to_list(self.nodes, [])
               if isinstance(node, Element)
               and node.attributes.get("id") == url.fragment]
        if elt:
            # Find the layout object for the element
            obj = [obj for obj in tree_to_list(self.document, [])
                   if obj.node == elt[0]]
            if obj:
                self.scroll = obj[0].y

      # layout → display list
      self.display_list = []
      paint_tree(self.document, self.display_list)
      
      if not url.fragment:
          self.scroll = 0


# Main browser application managing tabs and UI
class Browser:
  def __init__(self):
    self.tabs = []
    self.active_tab = None
    
    self.window = tkinter.Tk()
    self.window.title("Web Browser")
    
    self.canvas = tkinter.Canvas(
      self.window,
      width=Width,
      height=Height,
      bg="white"
    )
    self.canvas.pack(fill="both", expand=True)
    
    self.window.bind("<Down>", self.handle_down)
    self.window.bind("<Up>", self.handle_up)
    self.window.bind("<MouseWheel>", self.handle_mousewheel)
    self.window.bind("<Button-1>", self.handle_click)
    self.window.bind("<Button-2>", self.handle_middle_click)
    self.window.bind("<Configure>", self.handle_resize)

    self.chrome = Chrome(self)
    self.window.bind("<Key>", self.handle_key)
    self.window.bind("<Return>", self.handle_enter)
    self.window.bind("<BackSpace>", self.handle_backspace)
    self.window.bind("<Control-c>", self.handle_copy)
    self.window.bind("<Control-v>", self.handle_paste)
    self.window.bind("<Left>", self.handle_left)
    self.window.bind("<Right>", self.handle_right)
  
  
  def handle_left(self, e):
    self.chrome.move_cursor_left()
    self.draw()

  def handle_right(self, e):
    self.chrome.move_cursor_right()
    self.draw()

  def handle_middle_click(self, e):
    if e.y < self.chrome.bottom:
      pass
    else:
      tab_y = e.y - self.chrome.bottom
      url = self.active_tab.click(e.x, tab_y, middle_click=True)
      if url:
        self.new_tab(url)

  def handle_copy(self, e):
    self.chrome.copy()

  def handle_paste(self, e):
    self.chrome.paste()
    self.draw()
  
  def handle_backspace(self, e):
    self.chrome.backspace()
    self.draw()
  
  def handle_key(self, e):
    if len(e.char) == 0: return
    if not (0x20 <= ord(e.char) < 0x7f): return
    self.chrome.keypress(e.char)
    self.draw()
  
  def handle_enter(self, e):
    self.chrome.enter()
    self.draw()
  
  def handle_down(self, e):
    self.active_tab.scrolldown()
    self.draw()
  
  def handle_up(self, e):
    self.active_tab.scrollup()
    self.draw()
  
  def handle_mousewheel(self, e):
    self.active_tab.mousewheel(e)
    self.draw()
  
  def handle_click(self, e):
    if e.y < self.chrome.bottom:
      self.chrome.click(e.x, e.y)
    else:
      tab_y = e.y - self.chrome.bottom
      self.active_tab.click(e.x, tab_y)
    
    # Only draw if we still have tabs (window wasn't destroyed)
    if len(self.tabs) > 0:
      self.draw()
  
  def handle_resize(self, e):
    self.active_tab.on_resize(e)
    self.draw()
  
  def draw(self):
    self.canvas.delete("all")
    self.active_tab.draw(self.canvas, self.chrome.bottom)
    for cmd in self.chrome.paint():
      cmd.execute(0, self.canvas)
    
    self.window.title(self.active_tab.get_title())
  
  def new_tab(self, url):
      new_tab = Tab(Height - self.chrome.bottom)
      new_tab.load(url)
      self.active_tab = new_tab
      self.tabs.append(new_tab)
      self.draw()
  
  def close_tab(self, tab):
    # Find the index of the tab being closed
    index = self.tabs.index(tab)
    
    # Remove the tab
    self.tabs.remove(tab)
    
    # If this was the last tab, close the browser
    if len(self.tabs) == 0:
      self.window.destroy()
      return  # DON'T call draw() after this!
    
    # If we closed the active tab, switch to another tab
    if tab == self.active_tab:
      # Switch to the tab before it, or the first tab if it was the first tab
      if index > 0:
        self.active_tab = self.tabs[index - 1]
      else:
        self.active_tab = self.tabs[0]

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python browser.py <URL>")
        sys.exit(1)
    Browser().new_tab(URL(sys.argv[1]))
    tkinter.mainloop()