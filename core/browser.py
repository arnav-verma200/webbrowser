import tkinter
import tkinter.font
from config.constants import Width, Height
from network.url import URL
from ui.chrome import Chrome
from .tab import Tab

class BrowserWindow:
    def __init__(self, browser, initial_url=None):
        self.browser = browser
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
        self.window.bind("<Key>", self.handle_key)
        self.window.bind("<Return>", self.handle_enter)
        self.window.bind("<BackSpace>", self.handle_backspace)
        self.window.bind("<Control-c>", self.handle_copy)
        self.window.bind("<Control-v>", self.handle_paste)
        self.window.bind("<Left>", self.handle_left)
        self.window.bind("<Right>", self.handle_right)
        self.window.bind("<Control-n>", self.handle_new_window)
        self.window.bind("<Control-t>", self.handle_new_tab)
        self.window.bind("<Control-w>", self.handle_close_tab)
        
        self.window.protocol("WM_DELETE_WINDOW", self.handle_window_close)
        
        self.chrome = Chrome(self)
        
        if initial_url:
            self.new_tab(initial_url)
        else:
            self.new_tab(URL("https://browser.engineering/"))
    
    def handle_new_window(self, e):
        self.browser.new_window()
    
    def handle_new_tab(self, e):
        self.new_tab(URL("https://browser.engineering/"))
    
    def handle_close_tab(self, e):
        if self.active_tab:
            self.close_tab(self.active_tab)
    
    def handle_window_close(self):
        self.browser.close_window(self)
    
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
        if self.active_tab:
            self.active_tab.scrolldown()
            self.draw()
    
    def handle_up(self, e):
        if self.active_tab:
            self.active_tab.scrollup()
            self.draw()
    
    def handle_mousewheel(self, e):
        if self.active_tab:
            self.active_tab.mousewheel(e)
            self.draw()
    
    def handle_click(self, e):
        if e.y < self.chrome.bottom:
            self.chrome.click(e.x, e.y)
        else:
            if self.active_tab:
                tab_y = e.y - self.chrome.bottom
                self.active_tab.click(e.x, tab_y)
        
        if len(self.tabs) > 0:
            self.draw()
    
    def handle_resize(self, e):
        if self.active_tab:
            self.active_tab.on_resize(e)
            self.draw()
    
    def draw(self):
        if not self.active_tab:
            return
        
        self.canvas.delete("all")
        self.active_tab.draw(self.canvas, self.chrome.bottom)
        for cmd in self.chrome.paint():
            cmd.execute(0, self.canvas)
        
        self.window.title(self.active_tab.get_title())
    
    def new_tab(self, url):
        # Calculate Height dynamically based on current window height if available, else default
        # Actually Height is constant initially, but handled in resize.
        # Tab needs height.
        new_tab = Tab(Height - self.chrome.bottom)
        new_tab.load(url)
        self.active_tab = new_tab
        self.tabs.append(new_tab)
        self.draw()
    
    def close_tab(self, tab):
        index = self.tabs.index(tab)
        self.tabs.remove(tab)
        
        if len(self.tabs) == 0:
            self.browser.close_window(self)
            return
        
        if tab == self.active_tab:
            if index > 0:
                self.active_tab = self.tabs[index - 1]
            else:
                self.active_tab = self.tabs[0]
        
        self.draw()

class Browser:
    def __init__(self):
        self.windows = []
    
    def new_window(self, url=None):
        window = BrowserWindow(self, url)
        self.windows.append(window)
        return window
    
    def close_window(self, window):
        if window in self.windows:
            self.windows.remove(window)
            window.window.destroy()
        
        if len(self.windows) == 0:
            import sys
            sys.exit(0)
