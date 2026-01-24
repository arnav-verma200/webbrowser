import os
import socket
import ssl
import time
from .cache import CACHE
from core.bookmarks import BOOKMARK_MANAGER

VISITED_URLS = set()

class URL:
    def __init__(self, url):
        self.fragment = None
        
        if url.startswith("about:"):
            self.scheme = "about"
            self.path = url[6:]
            return

        if url == "bookmarks":
            self.scheme = "bookmarks"
            self.path = ""
            return
        
        self.view_source = False
        if url.startswith("view-source:"):
            self.view_source = True
            url = url[len("view-source:"):]
        
        try:
            self.scheme, url = url.split("://", 1)
        except ValueError:
            self.scheme = "about"
            self.path = ""
            return
        
        if self.scheme not in ["http", "https", "file"]:
            self.scheme = "about"
            self.path = ""
            return
        
        if self.scheme in ["http", "https"]:  
            if "/" not in url :
                url = url + "/"
            
            self.host, url = url.split("/",1)
            self.path = "/" + url
            
            if "#" in self.path:
                self.path, self.fragment = self.path.split("#", 1)
            
            if self.scheme == "http":
                self.port = 80
            elif self.scheme == "https":
                self.port = 443
            
            if ":" in self.host:
                self.host, port = self.host.split(":", 1)
                self.port = int(port)
        
        elif self.scheme in ["file"]:
            if os.name == "nt" and url.startswith("/"):
                url = url[1:]
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
        
        if self.scheme == "file":
            cache_key = f"{self.scheme}://{self.path}"
        else:
            cache_key = f"{self.scheme}://{self.host}{self.path}"

        if cache_key in CACHE:
            entry = CACHE[cache_key]
            if time.time() < entry["expires"]:
                print("-----------------------------------")
                print("cache hit:", cache_key)
                print("-----------------------------------")
                return entry["body"]
            else:
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
            
        s = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
        s.connect((self.host, self.port))
        
        if self.scheme == "https":
            ctx = ssl.create_default_context()
            s = ctx.wrap_socket(s, server_hostname=self.host)
        
        request = "GET {} HTTP/1.1\r\n".format(self.path)
        request += "HOST: {}\r\n".format(self.host)
        request += "Connection: close\r\n"  
        request += "\r\n"
        
        s.send(request.encode("utf8"))
        
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
            
        if 300 <= status < 400:
            location = response_headers.get("location")
            s.close()
            if not location:
                return ""
            if location.startswith("http://") or location.startswith("https://"):
                return URL(location).request(redirect_count + 1)
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
        if self.scheme in ["about", "bookmarks"]:
            if "://" in url:
                return URL(url)
            return self
        
        if "://" in url:
            return URL(url)
    
        if url.startswith("//"):
            return URL(self.scheme + ":" + url)

        if self.scheme == "file":
            base_dir = os.path.dirname(self.path)
            full_path = os.path.normpath(os.path.join(base_dir, url))
            return URL("file://" + full_path)

        if not url.startswith("/"):
            dir, _ = self.path.rsplit("/", 1)
            while url.startswith("../"):
                url = url[3:]
                if "/" in dir:
                    dir, _ = dir.rsplit("/", 1)
            url = dir + "/" + url

        return URL(f"{self.scheme}://{self.host}:{self.port}{url}")
