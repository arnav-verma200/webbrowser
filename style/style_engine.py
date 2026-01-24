from dom.nodes import Element


INHERITED_PROPERTIES = {
    "font-size": "16px",
    "font-style": "normal",
    "font-weight": "normal",
    "color": "black",
    "display": "inline",
}

def style(node, rules, url):
    node.style = {}

    for prop, default in INHERITED_PROPERTIES.items():
        if node.parent:
            node.style[prop] = node.parent.style[prop]
        else:
            node.style[prop] = default

    all_properties = {}
    
    for selector, body in rules:
        if selector.matches(node):
            base_priority = selector.priority
            for prop, (val, important) in body.items():
                priority = base_priority + (10000 if important else 0)
                
                if prop not in all_properties:
                    all_properties[prop] = []
                all_properties[prop].append((priority, val))
    
    for prop, values in all_properties.items():
        values.sort(key=lambda x: x[0], reverse=True)
        node.style[prop] = values[0][1]

    if isinstance(node, Element) and "style" in node.attributes:
        from parser.css_parser import CSSParser
        parser = CSSParser(node.attributes["style"] + ";")
        pairs = parser.body()
        
        for prop, (val, important) in pairs.items():
            inline_priority = 1000 + (10000 if important else 0)
            
            if prop in all_properties:
                max_stylesheet_priority = max(v[0] for v in all_properties[prop])
                if inline_priority > max_stylesheet_priority:
                    node.style[prop] = val
            else:
                node.style[prop] = val

    if node.style.get("font-size", "").endswith("%"):
        pct = float(node.style["font-size"][:-1]) / 100
        if node.parent:
            parent_font = node.parent.style.get("font-size", "16px")
            if parent_font and parent_font.endswith("px"):
                parent_px = int(parent_font[:-2])
            else:
                parent_px = 16
        else:
            from config.constants import INHERITED_PROPERTIES as DEFAULTS 
            # Actually INHERITED_PROPERTIES is local here, but let's use the local one
            parent_px = int(INHERITED_PROPERTIES["font-size"][:-2])
        node.style["font-size"] = str(int(parent_px * pct)) + "px"

    # Moving visited link logic to browser/tab because it requires VISITED_URLS
    # Or passing VISITED_URLS in. The original code used global VISITED_URLS.
    # We will need to handle this. For now keeping simplified or injecting dependency?
    # Original: if str(url.resolve(node.attributes["href"])) in VISITED_URLS:
    # I'll rely on passing visited_urls separately or make it a global in constants/core?
    # Let's import it from a central place or handle it later.
    # ideally style() shouldn't depend on global state. 
    # For now, I'll stub it or assume visited_urls logic is handled in Tab or we pass it.
    # Re-reading browser.py: start calls style(self.nodes, rules, url). VISITED_URLS is global.
    # I'll skip the visited link color for now or import it from core later if I move it to core.
    # Better: style function signature doesn't include visited_urls.
    # I'll check if I can import VISITED_URLS from core.browser (circular?) or core.
    # Let's import from a state module if possible.
    # Decided: I will skip the visited check here to avoid circular dependencies for now
    # and re-add it if I create a clean way (e.g. passing it in).
    
    for child in node.children:
        style(child, rules, url)
