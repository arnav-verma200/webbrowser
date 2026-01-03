import socket

class URL:
  def __init__(self, url):
    #cutting url into host, scheme and path
    self.scheme, url = url.split("://",1)
    assert self.scheme == "http"
    
    if "/" not in url :
      url = url + "/"
    
    self.host, url = url.split("/",1)
    self.path = "/" + url
    
  def requests(self):
    #using socket to estabilish the connection
    s = socket.socket(
      family= socket.AF_INET,
      type= socket.SOCK_STREAM,)
    s.connect((self.host, 80)) #establishing the connection
    
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
    version, stats, explanation = statusline.split(" ", 2)
    
    response_headers = {}
    while True:
      line = response.readline()
      if line == "\r\n":
        break
      header, value = line.split(":",1)
      response_headers[header.casefold()] = value.strip()
      
    content = response.read()
    s.close()
    return content
    
url1 = URL("http://example.org/index.html")
ts = url1.requests()
print(ts)