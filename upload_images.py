import os
import django
from pathlib import Path

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from products.models import Product
from django.conf import settings
from django.core.files import File

media_products = Path(settings.MEDIA_ROOT) / "products"

products = Product.objects.exclude(image="")

for product in products:
    image_name = os.path.basename(product.image.name)
    image_path = media_products / image_name

    if image_path.exists():
        print(f"Uploading: {product.name}")

        with open(image_path, "rb") as image_file:
            product.image.save(
                image_name,
                File(image_file),
                save=True
            )

        print(f"Done: {product.name}")
    else:
        print(f"File not found: {image_path}")

print("All images processed.")