from PIL import Image
img = Image.open(r"默认头像.png")
print(type(img))
img.show()