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
    """
    HTTP/1.1 keeps connections alive by default 
    Your response.read() may block or hang 
    Servers may wait forever
    so to fixx this we add: request += "Connection: close\r\n"
    """
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
    no_store = response_headers.get("no-store")
    max_age = response_headers.get("max-age")
    
    print("OO")
    print(cache_control)
    print(no_store)
    print(max_age)
    print("OO")
    
    content = response.read()
    s.close()
    
    if cache_control: #sees if cache control exist or not
      cache_control = cache_control.lower()

      if "no-store" not in cache_control and "max-age=" in cache_control:
        """
        Only cache if BOTH are true:
        "no-store" is NOT present
        "max-age=" IS present
        
        No max-age → no expiry → unsafe to cache (for your assignment rules)
        “DO NOT store this response anywhere.”
        This overrides everything.
        So if it exists → immediate rejection.
        """
        try:
          #gives the max time for which the thing can be in the cache
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

# getting the html from the page 
def show(self, body):
  in_tag = False
  i = 0
  while i < len(body):

    if body.startswith("&lt;", i):
      print("<", end="")
      i += 4
      continue

    if body.startswith("&gt;", i):
      print(">", end="")
      i += 4
      continue

    c = body[i]

    if c == "<":
        in_tag = True
    elif c == ">":
        in_tag = False
    elif not in_tag:
        print(c, end="")

    i += 1



#loading the page and getting html
def load(url):
  body = url.requests()
  if getattr(url, "view_source", False):
    print(body)
  else:
    show(url,body)


if __name__ == "__main__":
  import sys
  load(URL(sys.argv[1]))