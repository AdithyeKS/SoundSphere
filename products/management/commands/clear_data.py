from django.core.management.base import BaseCommand

from cart.models import CartItem
from orders.models import OrderItem
from products.models import Product, Review


class Command(BaseCommand):
    help = 'Clears all product demo data from the database'

    def handle(self, *args, **options):
        CartItem.objects.all().delete()
        OrderItem.objects.all().delete()
        Review.objects.all().delete()

        count, _ = Product.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f"Successfully cleared {count} demo products from the database! Catalog is now clean."))
