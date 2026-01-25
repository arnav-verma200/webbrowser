from config.constants import Height, VSTEP, SELF_CLOSING_TAGS
from dom.utils import tree_to_list
from dom.nodes import Element, Text
from network.url import URL, VISITED_URLS
from parser.html_parser import HTMLParser
from parser.css_parser import CSSParser
from style.style_engine import style
from layout.document_layout import DocumentLayout
from rendering.utils import paint_tree
from config.constants import *


class Tab:
    def __init__(self, tab_height):
        self.display_list = []
        self.scroll = 0
        self.scroll_step = 100
        self.url = None
        self.tab_height = tab_height
        self.history = []
        self.history_index = -1

    def get_title(self):
        title_nodes = [node for node in tree_to_list(self.nodes, [])
                    if isinstance(node, Element) and node.tag == "title"]
        
        if not title_nodes:
            return "Untitled"
        
        title_text = ""
        for child in title_nodes[0].children:
            if isinstance(child, Text):
                title_text += child.text
    
        return title_text.strip() if title_text.strip() else "Untitled"

    def click(self, x, y, middle_click=False):
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
                    elt_id = href[1:]
                    target_elt = [node for node in tree_to_list(self.nodes, [])
                                if isinstance(node, Element)
                                and node.attributes.get("id") == elt_id]
                    if target_elt:
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

    def scrollup(self):
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
        self.scroll -= event.delta
        max_y = self.display_list[-1].bottom
        max_scroll = max(0, max_y - Height)
        if self.scroll < 0:
            self.scroll = 0
        if self.scroll > max_scroll:
            self.scroll = max_scroll
    
    def on_resize(self, event):
        if not hasattr(self, "document"):
            return
        
        from config.constants import HSTEP
        
        # Update document width and re-layout
        self.document.width = event.width - 2 * HSTEP
        self.document.children = []
        self.document.layout()

        # Regenerate display list
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
            self.history = self.history[:self.history_index + 1]
            self.history.append(url)
            self.history_index = len(self.history) - 1
        
        self.url = url
        
        if url.scheme in ["http", "https"]:
            VISITED_URLS.add(str(url))
        
        body = url.request()
        
        if getattr(url, "view_source", False):
            print(body)
            # view-source needs to handle content display differently or just print?
            # Original code printed.
            return

        self.nodes = HTMLParser(body).parse()
        
        # DEFAULT_STYLE_SHEET needs to be loaded.
        # I'll import it or load it here.
        # It was global in browser.py
        try:
             with open("browser.css") as f:
                default_style_sheet = CSSParser(f.read()).parse()
        except FileNotFoundError:
             default_style_sheet = []
        
        rules = default_style_sheet.copy()
        
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

        style(self.nodes, rules, url)

        self.document = DocumentLayout(self.nodes, width=Width - 2 * HSTEP)
        self.document.layout()

        if url.fragment:
            elt = [node for node in tree_to_list(self.nodes, [])
                if isinstance(node, Element)
                and node.attributes.get("id") == url.fragment]
            if elt:
                obj = [obj for obj in tree_to_list(self.document, [])
                    if obj.node == elt[0]]
                if obj:
                    self.scroll = obj[0].y

        self.display_list = []
        paint_tree(self.document, self.display_list)
        
        if not url.fragment:
            self.scroll = 0
