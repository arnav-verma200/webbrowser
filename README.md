# 🌐 I Built a Web Browser (And You Can Too!)

Ever wondered how Chrome, Firefox, or Safari actually *work* under the hood? Me too. So I built one from scratch in Python to find out.

This isn't just another "toy project" - it's a fully functional web browser that speaks HTTP, parses HTML, understands CSS, and renders actual web pages. All in ~1000 lines of Python. No magic libraries. Just sockets, strings, and a whole lot of parsing.

## 🚀 Why This Exists

Because reading about how browsers work is boring. Building one? That's where the fun begins.

This project answers questions like:
- What *actually* happens when you type a URL and hit Enter?
- How does CSS cascade and inheritance really work?
- Why do browsers cache things, and how do they know when to stop?
- What's the difference between layout and painting?

Spoiler: It's way cooler than it sounds.

## ✨ What It Can Do

### The Impressive Stuff
- **Raw Socket Networking**: No `requests` library here - we're talking directly to servers using Python sockets and SSL
- **Full CSS Engine**: Selector matching, specificity calculations, cascade resolution, and inheritance. Yes, even `!important` works
- **Smart Caching**: Respects `Cache-Control` headers and expires cached content automatically
- **Multi-Tab Browsing**: Because who uses just one tab anymore?
- **Real HTML Parsing**: Builds an actual DOM tree, handles malformed HTML gracefully, knows about self-closing tags
- **View Source Mode**: Ever wonder how `view-source:` works? Now you know

### The UI Features
- 🔗 **Clickable Links**: Click to navigate (mind-blowing, I know)
- ⬆️⬇️ **Smooth Scrolling**: Arrow keys and mouse wheel both work
- 📑 **Tab Management**: Open multiple pages, switch between them
- 🔙 **History Navigation**: Back button that actually remembers where you've been
- 🎨 **CSS Rendering**: Colors, fonts, backgrounds - the works

### The "Wait, You Built That?" Features
- Custom lexer that tokenizes HTML character by character
- CSS parser that handles shorthand properties (`margin: 10px 20px`)
- Layout engine with both block and inline layout modes
- Display list architecture for efficient rendering
- Redirect following (because the web loves redirects)

## 🎯 Quick Start

### Installation
```bash
git clone https://github.com/yourusername/python-web-browser.git
cd python-web-browser
```

That's it. No `pip install` needed (Tkinter comes with Python).

### Fire It Up

```bash
python browser.py https://browser.engineering/
```

Or browse local files:
```bash
python browser.py file:///path/to/your/file.html
```

Try this for fun:
```bash
python browser.py view-source:https://example.com
```

## 🏗️ How It Actually Works

### The Journey of a Web Page

**1. You type a URL**
```python
url = URL("https://example.com/page")
# Parses scheme, host, port, path
# Handles http, https, file, and even view-source:
```

**2. Browser makes a request**
```python
# Opens a socket, wraps it in SSL if needed
# Sends HTTP headers
# Reads response line by line
# Checks cache first (because network requests are expensive)
```

**3. HTML gets lexed and parsed**
```python
# Lexer: Splits "<p>Hello</p>" into tokens
# Parser: Builds a tree structure (the DOM)
# Handles broken HTML like a champ
```

**4. CSS gets parsed and applied**
```python
# Parses stylesheets into rules
# Matches selectors to DOM elements
# Calculates specificity (tag: 1, class: 10, inline: 1000)
# Resolves the cascade (!important wins all)
```

**5. Layout happens**
```python
# Walks the DOM tree
# Calculates x, y, width, height for everything
# Wraps text into lines
# Positions block elements vertically
```

**6. Paint time**
```python
# Generates display commands
# DrawText, DrawRect, DrawLine
# Canvas renders everything
```

### The Cool Technical Bits

**CSS Cascade That Actually Works**

Most tutorials skip this. Not here. The browser implements proper cascade resolution:
- Inherited properties flow down the tree
- Selector specificity is calculated correctly (tag selectors: 1 point, class selectors: 10 points)
- Inline styles beat stylesheet rules
- `!important` beats everything (as it should)

**Caching Done Right**

The browser respects `Cache-Control` headers:
```python
# Server says: "Cache-Control: max-age=3600"
# Browser: "Cool, I'll keep this for an hour"
# Next request within an hour: instant load
# After an hour: fresh request
```

**Layout Is Harder Than You Think**

Ever wonder why web layout is slow? Try implementing it:
- Calculate positions top to bottom
- Wrap text when lines get too long
- Handle both block (stacked) and inline (flowing) elements
- Recalculate everything when the window resizes

## 🎓 What I Learned Building This

1. **HTTP is chatty**: Every request is just formatted text sent over a socket
2. **HTML is forgiving**: Browsers have to handle terrible HTML (missing closing tags, nested incorrectly, you name it)
3. **CSS is complex**: The cascade rules are elegant but *dense*
4. **Layout is recursive**: Everything depends on its parent's size
5. **Caching is essential**: Network requests are slow, caching makes everything feel instant

## 🚧 Known Limitations (aka Features Not Bugs)

This is an educational browser, so some things are intentionally simplified:

- **No JavaScript**: Because life is complicated enough
- **Limited CSS properties**: We support the important ones (colors, fonts, display)
- **No images yet**: Text is more important anyway (kidding, PRs welcome)
- **Basic forms**: You can see them, can't submit them
- **Simple box model**: Margin and padding are parsed but not rendered yet

These aren't bugs - they're opportunities for you to contribute! 😉


## 🤝 Contributing

Found a bug? Want to add a feature? Think my code is terrible?

**Open an issue or PR!** This is a learning project, and I'm here to learn.

Ideas for contributions:
- Add image rendering
- Implement more CSS properties
- Better error handling
- Support for `<table>` layout
- Make it faster (always a good goal)

## 💡 Fun Facts

- The entire browser is ~1000 lines of Python
- It can render browser.engineering (meta!)
- The cache actually saves you from hitting GitHub servers every reload
- CSS specificity calculation was way harder than expected
- Layout is basically just recursive tree traversal with extra steps

## 📜 License

MIT - Do whatever you want with it. Build upon it. Learn from it. Break it and fix it again.

## 🙏 Thanks

- The Python community for making Tkinter surprisingly good
- Everyone who's ever struggled with CSS specificity (we're in this together)
- You, for reading this far

---

**Now go build something cool.** 🚀
