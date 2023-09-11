import qrcode
import qrcode.image.svg

qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_L)
qr.add_data('https://aft-services.ru')

# закругленные углы
img = qrcode.make('https://aft-services.ru', image_factory=qrcode.image.svg.SvgImage)
# встроенное изображение `/path/to/image.png`
# img_3 = qr.make_image(image_factory=StyledPilImage, embeded_image_path="/path/to/image.png")

img.save("img_1.svg")
# img_2.save("img_2.png")
# img_3.save("img_3.png")
