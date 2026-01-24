from core.browser import Browser
from network.url import URL
import tkinter

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python main.py <URL>")
        sys.exit(1)
    
    browser = Browser()
    browser.new_window(URL(sys.argv[1]))
    tkinter.mainloop()
