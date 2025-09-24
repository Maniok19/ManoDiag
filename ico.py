from PIL import Image
img = Image.open("logo_ManoDiag.png").convert("RGBA")
sizes = [16, 24, 32, 48, 64, 128, 256]
img.save("assets/app.ico", sizes=[(s, s) for s in sizes])
print("assets/app.ico créé")