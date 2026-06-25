# Web Browser Features

This is a summary of the features implemented in this custom Python Tkinter web browser:

## Tab & Window Management
*   **Multi-Tab Browsing**: Open, switch, and close multiple tabs in the same window.
*   **Multi-Window Support**: Open and close separate browser windows.
*   **Keyboard Shortcuts**:
    *   `Ctrl + T`: Open a new tab
    *   `Ctrl + W`: Close the active tab
    *   `Ctrl + N`: Open a new browser window

## Navigation & History
*   **Back and Forward Navigation**: Clickable `<` (back) and `>` (forward) buttons to navigate page history.
*   **History Stack**: Maintains page history for each tab separately.
*   **Clickable Links**: Click on HTML hyperlinks to navigate to other pages, or middle-click a link to open it in a new tab.

## Bookmarks System
*   **Bookmark Toggle**: Bookmark or remove the current page by clicking the Star (`★`) button.
*   **Bookmarks Menu**: Click the Menu (`☰`) button to view all bookmarked pages.
*   **Local Storage**: Saves bookmarked URLs to a local file (`bookmarks.txt`) in your user directory.
*   **Bookmarks Page**: Dynamically generates a native HTML page list of your bookmarks under `about:bookmarks`.

## Custom Rendering & Layout Engine
*   **Custom Graphics**: Paints page graphics (text, boxes, lines) directly onto a Tkinter canvas.
*   **Block & Inline Layouts**: Arranges blocks vertically and wraps inline text based on the window's width.
*   **Baseline Text Alignment**: Aligns text elements on font baselines for clean rendering.
*   **Page Scrolling**: Scroll through web pages using the `Up`/`Down` arrow keys or mouse wheel.
*   **Responsive Resizing**: Automatically updates layout and wraps text when you resize the browser window.

## Custom HTML & CSS Parsers
*   **HTML Parser**: A custom lexer and stack-based parser that converts raw HTML text into a structured Document Object Model (DOM) tree.
*   **CSS Parser**: Compiles stylesheets and processes nested rules, class selectors, and tag selectors.
*   **Cascade & Styling Engine**: Computes visual styles for DOM elements based on:
    *   User Agent defaults (`browser.css`)
    *   Inline styles (`style="..."` attributes)
    *   Priority overrides (`!important`)
    *   Inherited values (colors, fonts)
    *   Percentage font sizes (e.g. `120%`)

## Protocols & Network Stack
*   **Supported Schemes**:
    *   `http://` and `https://` for web pages
    *   `file://` for local file system browsing
    *   `about:` for local browser pages (e.g. `about:blank`, `about:bookmarks`)
*   **Secure Connection Wrapper**: Uses Python's standard `ssl` library to perform secure handshakes for HTTPS.
*   **Redirection Support**: Automatically follows HTTP redirect responses (up to 5 redirects).
*   **In-Memory Cache**: Caches fetched pages to speed up load times for visited pages.

## Interactive Browser UI (Chrome)
*   **Canvas-Drawn Interface**: Renders the complete browser UI (tab headers, address bar, navigation keys, buttons) directly on the Tkinter canvas.
*   **Address Bar Input**:
    *   Focus, type, and edit URLs/search queries in the URL bar.
    *   Keyboard controls to move the input cursor.
    *   Clipboard support (`Ctrl + C` to copy, `Ctrl + V` to paste) within the address bar.
*   **Dynamic Tab Titles**: Displays the active page's HTML `<title>` as the window title.

## View Source Mode
*   **View Source Page**: Prefix any URL with `view-source:` (e.g. `view-source:https://example.com`) to print its raw HTML to the terminal console.
