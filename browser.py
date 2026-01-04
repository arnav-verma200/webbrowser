import tkinter
import socket
import ssl
import os
import time

CACHE = {}

class URL:
  def __init__(self, url):
    
    self.view_source = False
    if url.startswith("view-source:"):
      self.view_source = True
      url = url[len("view-source:"):]
    
    #cutting url into host, scheme and path
    self.scheme, url = url.split("://",1)
    
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


    
      
  def requests(self, redirect_count=0):
    
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
        """time.time() gets the current "now" time.
        entry["expires"] is a timestamp in the future when the data becomes invalid.
        If the current time is less than the expiration time, the data is still fresh. The program
        returns the stored body immediately, skipping the need for a slow network request."""
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
        return URL(location).requests(redirect_count + 1)
      
      #if nothing from above 
      else:
        new_url = "{}://{}{}".format(self.scheme, self.host, location)
        return URL(new_url).requests(redirect_count + 1)
    
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


def lex(body):
  text = ""
  in_tag = False
  i = 0
  while i < len(body):
    if body.startswith("&lt;", i):
      text += "<"
      i += 4
      continue

    if body.startswith("&gt;", i):
      text += ">"
      i += 4
      continue

    c = body[i]

    if c == "<":
      in_tag = True
    elif c == ">":
      in_tag = False
    elif not in_tag:
      text += c

    i += 1

  return text


Height, Width = 600,800
HSTEP, VSTEP = 8, 18

#layout of characters like how they are layedout
def layout(text):
  display_list = []
  cursor_x, cursor_y = HSTEP, VSTEP

  for c in text:
    if c == "\n":
      cursor_y += VSTEP * 2
      cursor_x = HSTEP
      continue
    
    display_list.append((cursor_x, cursor_y, c))
    cursor_x += HSTEP

    if cursor_x >= Width - HSTEP:
      cursor_y += VSTEP
      cursor_x = HSTEP
  return display_list

class Browser:
  def __init__(self):
    self.window = tkinter.Tk()
    self.scrollbar = tkinter.Scrollbar(self.window, orient="vertical") #creating the window scrollbar
    self.scrollbar.pack(side="right", fill="y") #same as above
    self.scrollbar.config(command=self.on_scrollbar) #connect scrollbar to scroll logic

    self.canvas = tkinter.Canvas(
      self.window,
      width=Width,
      height=Height
    )
    self.canvas.pack()
    self.scroll = 0 #how much we scrolled 
    self.window.bind("<Down>", self.scrolldown) #binding the buttons to scroll down
    self.window.bind("<Up>", self.scrollup) #binding the buttons to scroll up
    
    self.window.bind("<MouseWheel>", self.mousewheel)  # using mouse wheel to scroll
    self.scroll_step = 100 #how much it should scroll in one tap of button

  def scrollup(self, e): #scroll up function
    self.scroll -= self.scroll_step
    if self.scroll < 0:
      self.scroll = 0
    self.draw()
    
  def scrolldown(self, e): #scroll down function
    self.scroll += self.scroll_step
    max_y = self.display_list[-1][1]
    max_scroll = max(0, max_y - Height)
    if self.scroll > max_scroll:
      self.scroll = max_scroll
    self.draw()
    
  def mousewheel(self, event):
    self.scroll -= event.delta  # wheel up = positive delta
    """Why event.delta works
        On Windows:
        Scroll up → event.delta = +120
        Scroll down → event.delta = -120"""
    max_y = self.display_list[-1][1]
    max_scroll = max(0, max_y - Height)
    if self.scroll < 0:
        self.scroll = 0
    if self.scroll > max_scroll:
        self.scroll = max_scroll
    self.draw()
  
  def on_scrollbar(self, action, value, units=None):
    if action == "moveto":
      fraction = float(value)
      max_y = self.display_list[-1][1]
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


    
  # drawing of characters
  def draw(self):
    self.canvas.delete("all")
    for x, y, c in self.display_list :
      if y > self.scroll + Height: continue
      if y + VSTEP < self.scroll: continue
      self.canvas.create_text(x, y - self.scroll, text=c)
      
    #This keeps scrollbar thumb in sync.
    max_y = self.display_list[-1][1]
    max_scroll = max(0, max_y - Height)
    if max_scroll > 0:
      self.scrollbar.set(self.scroll / max_scroll,
                        (self.scroll + Height) / max_scroll)
    else:
      self.scrollbar.set(0, 1)
      
      
      
  def load(self, url):
    
    body = url.requests()
    if getattr(url, "view_source", False):
      print(body)
    else:
      text = lex(body)
      self.display_list = layout(text)
      self.draw()


if __name__ == "__main__":
  import sys
  Browser().load(URL(sys.argv[1]))
  tkinter.mainloop()
