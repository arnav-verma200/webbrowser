from browser import URL, load

u = URL("https://httpbin.org/cache/60")
load(u)
print("\n--- second request ---\n")
load(u)
