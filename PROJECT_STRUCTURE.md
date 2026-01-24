# Project Structure Documentation

This document explains the purpose of each file and folder in the webbrowser project.

## Root Directory
- **main.py**: The entry point of the application. It initializes the `Browser` class and opens a new window with the provided URL.
- **browser.css**: The default user agent stylesheet defining base styles for HTML elements.
- **bookmarks.txt**: Stores user bookmarks.
- **requirements.txt**: Lists Python dependencies required for the project.
- **README.md**: General project information and instructions.

## `config/`
Configuration settings and constants.
- **constants.py**: Defines global constants such as window dimensions (`Width`, `Height`), layout steps (`HSTEP`, `VSTEP`), and self-closing tags.

## `core/`
Core browser logic and state management.
- **browser.py**: Contains `Browser` and `BrowserWindow` classes. Manages application-level state, window creation, and global event handling (keyboard, mouse).
- **tab.py**: Represents a single browser tab. Manages navigation history, page loading, and rendering pipeline coordination.
- **bookmarks.py**: Manages bookmark storage and operations (add, remove, check).

## `dom/`
Document Object Model (DOM) representation.
- **nodes.py**: Defines the classes for DOM nodes, including `Element` and `Text` nodes.
- **utils.py**: Utility functions for DOM manipulation (e.g., printing the tree).

## `layout/`
Layout engine responsible for calculating the position and size of elements.
- **document_layout.py**: Top-level layout manager for the document.
- **block_layout.py**: Handles layout for block-level elements (e.g., `<div>`, `<p>`).
- **inline_layout.py**: Handles layout for inline elements (e.g., `<span>`, text).
- **geometry.py**: Defines geometric primitives like `Rect` used for hit testing and drawing.

## `network/`
Networking and resource fetching.
- **url.py**: A `URL` class for parsing URLs, handling paths, schemes (http, file, data), and resolving relative links.
- **cache.py**: Implements caching mechanisms to store and retrieve network responses.

## `parser/`
Parsing logic for HTML and CSS.
- **html_parser.py**: A custom HTML parser that tokenizes HTML input and constructs a DOM tree.
- **css_parser.py**: Parses CSS stylesheets into rules and declarations.
- **lexer.py**: Lexical analyzer used by the parsers to break input into tokens.

## `rendering/`
Rendering primitives and instructions.
- **commands.py**: Defines drawing commands (`DrawRect`, `DrawText`, `DrawLine`) that abstract over the underlying graphics library (Tkinter).
- **utils.py**: Rendering utility functions.

## `style/`
CSS styling engine.
- **style_engine.py**: Matches CSS rules to DOM nodes and computes computed styles.
- **selectors.py**: Logic for parsing and matching CSS selectors (tags, classes, IDs).

## `ui/`
User Interface components for the browser window (chrome).
- **chrome.py**: Draws and manages the browser "chrome" layout (address bar, tab bar, back/forward buttons, bookmarks). Handles user interactions within these areas.
- **fonts.py**: Wrapper around Tkinter fonts to manage font loading and metrics.
