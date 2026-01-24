from config.constants import Width, Height, HSTEP
from rendering.commands import DrawRect, DrawLine, DrawText, DrawOutline
from ui.fonts import get_font
from layout.geometry import Rect
from network.url import URL
from core.bookmarks import BOOKMARK_MANAGER

class Chrome:
    def __init__(self, window):
        self.window = window
        
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

        bookmark_width = self.font.measure("★") + 2*self.padding
        self.bookmark_rect = Rect(
            self.forward_rect.right + self.padding,
            self.urlbar_top + self.padding,
            self.forward_rect.right + self.padding + bookmark_width,
            self.urlbar_bottom - self.padding)

        bookmarks_list_width = self.font.measure("☰") + 2*self.padding
        self.bookmarks_list_rect = Rect(
            self.bookmark_rect.right + self.padding,
            self.urlbar_top + self.padding,
            self.bookmark_rect.right + self.padding + bookmarks_list_width,
            self.urlbar_bottom - self.padding)

        self.address_rect = Rect(
            self.bookmarks_list_rect.right + self.padding,
            self.urlbar_top + self.padding,
            Width - self.padding,
            self.urlbar_bottom - self.padding)
        
        self.focus = None
        self.address_bar = ""
        self.cursor_position = 0
    
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
        
        cmds.append(DrawRect(
            0, 0,
            Width, self.bottom,
            "white"))
        
        for i, tab in enumerate(self.window.tabs):
            bounds = self.tab_rect(i)
            
            if tab == self.window.active_tab:
                cmds.append(DrawRect(
                    bounds.left, bounds.top,
                    bounds.right, bounds.bottom,
                    "lightgray"))
            
            cmds.append(DrawLine(
                bounds.left, bounds.top, bounds.left, bounds.bottom,
                "black", 1))
            cmds.append(DrawLine(
                bounds.right, bounds.top, bounds.right, bounds.bottom,
                "black", 1))
            
            cmds.append(DrawText(
                bounds.left + self.padding, bounds.top + self.padding,
                "Tab {}".format(i), self.font, "black"))

            close_rect = self.close_button_rect(i)
            cmds.append(DrawLine(
                close_rect.left - self.padding, bounds.top,
                close_rect.left - self.padding, bounds.bottom,
                "black", 1))
            
            cmds.append(DrawText(
                close_rect.left, close_rect.top,
                "X", self.font, "black"))
        
        can_go_back = self.window.active_tab.history_index > 0
        back_color = "black" if can_go_back else "gray"

        cmds.append(DrawOutline(self.back_rect, "black", 1))
        cmds.append(DrawText(
            self.back_rect.left + self.padding,
            self.back_rect.top,
            "<", self.font, back_color))
        
        can_go_forward = (self.window.active_tab.history_index < 
                        len(self.window.active_tab.history) - 1)
        forward_color = "black" if can_go_forward else "gray"

        cmds.append(DrawOutline(self.forward_rect, "black", 1))
        cmds.append(DrawText(
            self.forward_rect.left + self.padding,
            self.forward_rect.top,
            ">", self.font, forward_color))
        
        current_url = str(self.window.active_tab.url)
        is_bookmarked = BOOKMARK_MANAGER.contains(current_url)
        show_bookmark = self.window.active_tab.url.scheme in ["http", "https"]

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

        cmds.append(DrawOutline(self.bookmarks_list_rect, "black", 1))
        cmds.append(DrawText(
            self.bookmarks_list_rect.left + self.padding,
            self.bookmarks_list_rect.top,
            "☰", self.font, "black"))
        
        cmds.append(DrawOutline(self.newtab_rect, "black", 1))
        cmds.append(DrawText(
            self.newtab_rect.left + self.padding,
            self.newtab_rect.top,
            "+", self.font, "black"))
        
        cmds.append(DrawOutline(self.address_rect, "black", 1))
        if self.focus == "address bar":
            cmds.append(DrawText(
                self.address_rect.left + self.padding,
                self.address_rect.top,
                self.address_bar, self.font, "black"))
            
            w = self.font.measure(self.address_bar[:self.cursor_position])
            cmds.append(DrawLine(
                self.address_rect.left + self.padding + w,
                self.address_rect.top,
                self.address_rect.left + self.padding + w,
                self.address_rect.bottom,
                "red", 1))
            
        else:
            url = str(self.window.active_tab.url)
            cmds.append(DrawText(
                self.address_rect.left + self.padding,
                self.address_rect.top,
                url, self.font, "black"))
        
        cmds.append(DrawLine(
            0, self.bottom, Width, self.bottom, 
            "black", 1))
        
        return cmds

    def keypress(self, char):
        if self.focus == "address bar":
            self.address_bar = (self.address_bar[:self.cursor_position] + 
                                char + 
                                self.address_bar[self.cursor_position:])
            self.cursor_position += 1

    def backspace(self):
        if self.focus == "address bar":
            if self.cursor_position > 0:
                self.address_bar = (self.address_bar[:self.cursor_position - 1] + 
                                self.address_bar[self.cursor_position:])
                self.cursor_position -= 1

    def move_cursor_left(self):
        if self.focus == "address bar":
            if self.cursor_position > 0:
                self.cursor_position -= 1

    def move_cursor_right(self):
        if self.focus == "address bar":
            if self.cursor_position < len(self.address_bar):
                self.cursor_position += 1

    def click(self, x, y):
        self.focus = None
        
        if self.newtab_rect.contains_point(x, y):
            self.window.new_tab(URL("https://browser.engineering/"))
        else:
            for i, tab in enumerate(self.window.tabs):
                if self.close_button_rect(i).contains_point(x, y):
                    self.window.close_tab(tab)
                    return
                
                elif self.tab_rect(i).contains_point(x, y):
                    self.window.active_tab = tab
                    self.window.draw()
                    return
            
            if self.back_rect.contains_point(x, y):
                self.window.active_tab.go_back()

            elif self.forward_rect.contains_point(x, y):
                self.window.active_tab.go_forward()

            elif self.bookmark_rect.contains_point(x, y):
                if self.window.active_tab.url.scheme in ["http", "https"]:
                    self.toggle_bookmark()
            
            elif self.bookmarks_list_rect.contains_point(x, y):
                self.window.active_tab.load(URL("about:bookmarks"))

            elif self.address_rect.contains_point(x, y):
                self.focus = "address bar"
                self.address_bar = ""
                self.cursor_position = 0

    def enter(self):
        if self.focus == "address bar":
            if self.is_url(self.address_bar):
                self.window.active_tab.load(URL(self.address_bar))
            else:
                query = self.address_bar.replace(" ", "+")
                search_url = f"https://google.com/search?q={query}"
                self.window.active_tab.load(URL(search_url))
            
            self.focus = None
            self.cursor_position = 0

    def is_url(self, text):
        if "://" in text:
            return True
        if text.startswith("http://") or text.startswith("https://"):
            return True
        if text.startswith("file://") or text.startswith("about:"):
            return True
        if "." in text and " " not in text:
            parts = text.split(".")
            if len(parts) >= 2 and all(part for part in parts):
                return True
        return False
    
    def toggle_bookmark(self):
        current_url = str(self.window.active_tab.url)
        if self.window.active_tab.url.scheme in ["http", "https"]:
            BOOKMARK_MANAGER.toggle(current_url)

    def copy(self):
        if self.focus == "address bar":
            self.window.window.clipboard_clear()
            self.window.window.clipboard_append(self.address_bar)

    def paste(self):
        if self.focus == "address bar":
            try:
                clipboard_text = self.window.window.clipboard_get()
                self.address_bar = (self.address_bar[:self.cursor_position] + 
                                clipboard_text + 
                                self.address_bar[self.cursor_position:])
                self.cursor_position += len(clipboard_text)
            except:
                pass
