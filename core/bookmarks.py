import os
from config.paths import BOOKMARKS_PATH

class BookmarkManager:
    def __init__(self, filename=None):
        # Use default path if none provided
        self.filename = str(filename) if filename else str(BOOKMARKS_PATH)
        self.bookmarks = set()
        self.load()
    
    def load(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, "r", encoding="utf-8") as f:
                    self.bookmarks = set(line.strip() for line in f if line.strip())
            except Exception as e:
                print(f"Error loading bookmarks: {e}")
                self.bookmarks = set()
    
    def save(self):
        try:
            with open(self.filename, "w", encoding="utf-8") as f:
                for bookmark in sorted(self.bookmarks):
                    f.write(bookmark + "\n")
        except Exception as e:
            print(f"Error saving bookmarks: {e}")
    
    def add(self, url):
        self.bookmarks.add(url)
        self.save()
    
    def remove(self, url):
        if url in self.bookmarks:
            self.bookmarks.discard(url)
            self.save()
    
    def toggle(self, url):
        if url in self.bookmarks:
            self.remove(url)
        else:
            self.add(url)
    
    def contains(self, url):
        return url in self.bookmarks
    
    def generate_page_html(self):
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

BOOKMARK_MANAGER = BookmarkManager()
