from PIL import Image, ImageDraw

# Create a simple test image
img = Image.new('RGB', (200, 200), color=(73, 109, 137))
d = ImageDraw.Draw(img)
d.text((10, 10), "Test Image", fill=(255, 255, 0))
img.save('examples/test_image.png')