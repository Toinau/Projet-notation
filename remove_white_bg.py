from PIL import Image

# Ouvre l'image
img = Image.open("static/logo_moyon_percy.png").convert("RGBA")
datas = img.getdata()

newData = []
for item in datas:
    # Si le pixel est blanc (ou presque), on le rend transparent
    if item[0] > 240 and item[1] > 240 and item[2] > 240:
        newData.append((255, 255, 255, 0))
    else:
        newData.append(item)

img.putdata(newData)
img.save("static/logo_moyon_percy_transparent.png", "PNG")
print("Image sauvegardée sous static/logo_moyon_percy_transparent.png") 