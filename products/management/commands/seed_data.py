from decimal import Decimal

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from products.models import Brand, Category, Product, Review


class Command(BaseCommand):
    help = 'Seeds initial headphone categories, brands, products, and technical specs into SoundSphere'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("Seeding SoundSphere database..."))

        # Superuser creation if not exists
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@soundsphere.com',
                'is_staff': True,
                'is_superuser': True
            }
        )
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            self.stdout.write(self.style.SUCCESS("Created admin user (Username: admin, Password: admin123)"))

        # Categories
        cat_data = [
            ("Wireless Headphones", "Over-ear and on-ear wireless Bluetooth headphones with ultra long battery life.", False),
            ("Gaming Headsets", "Immersive 7.1 surround sound headsets with noise-cancelling microphone.", False),
            ("Bluetooth Earbuds", "True Wireless Stereo (TWS) in-ear earbuds with compact charging case.", False),
            ("Studio Headphones", "Flat frequency response audiophile monitoring headphones.", False),
            ("Noise-Cancelling Headphones", "Industry-leading Active Noise Cancellation (ANC) for silence on the go.", False),
            ("Charging Cables", "Braided USB-C & fast charging audio adapter cables.", True),
            ("Headphone Stands", "RGB & premium aluminum acoustic desktop headphone stands.", True),
            ("Ear Cushions", "Memory foam and cooling gel replacement ear pads.", True),
            ("Carrying Cases", "Hard-shell shockproof travel cases for premium headphones.", True),
        ]

        categories = {}
        for name, desc, is_acc in cat_data:
            cat, _ = Category.objects.get_or_create(
                name=name,
                defaults={'description': desc, 'is_accessory': is_acc}
            )
            categories[name] = cat

        # Brands
        brand_names = ["Sony", "Bose", "Sennheiser", "Audio-Technica", "JBL", "SoundSphere Signature"]
        brands = {}
        for bname in brand_names:
            b, _ = Brand.objects.get_or_create(name=bname)
            brands[bname] = b

        # Products Seed List
        products_seed = [
            {
                "name": "SoundSphere Apex ANC Wireless",
                "brand": "SoundSphere Signature",
                "category": "Noise-Cancelling Headphones",
                "price": Decimal("349.99"),
                "discount_price": Decimal("299.99"),
                "description": "Experience peak acoustic performance with SoundSphere Apex. Featuring custom 45mm beryllium drivers, hybrid active noise cancellation, ambient passthrough, and up to 40 hours of continuous playback.",
                "stock": 25,
                "is_featured": True,
                "specs": {
                    "driver_size": "45mm Custom Beryllium",
                    "battery_life": "40 Hours (ANC On)",
                    "connectivity": "Bluetooth 5.3 + LDAC + 3.5mm",
                    "noise_cancellation": "Hybrid Adaptive ANC (-42dB)",
                    "frequency_response": "10 Hz - 40,000 Hz",
                    "impedance": "32 Ohms",
                    "weight": "265g",
                    "warranty": "2 Years International"
                }
            },
            {
                "name": "Sony WH-1000XM5 Wireless",
                "brand": "Sony",
                "category": "Noise-Cancelling Headphones",
                "price": Decimal("399.99"),
                "discount_price": Decimal("348.00"),
                "description": "Industry-leading noise cancelling with two processors and 8 microphones for unprecedented sound quality and crystal-clear call quality.",
                "stock": 18,
                "is_featured": True,
                "specs": {
                    "driver_size": "30mm Precision Carbon",
                    "battery_life": "30 Hours",
                    "connectivity": "Bluetooth 5.2 / AAC / LDAC",
                    "noise_cancellation": "Integrated Processor V1 ANC",
                    "frequency_response": "4 Hz - 40,000 Hz",
                    "impedance": "48 Ohms",
                    "weight": "250g",
                    "warranty": "1 Year Manufacturer"
                }
            },
            {
                "name": "Bose QuietComfort Ultra",
                "brand": "Bose",
                "category": "Wireless Headphones",
                "price": Decimal("429.00"),
                "discount_price": Decimal("379.00"),
                "description": "World-class noise cancellation, quieter than ever before. Breakthrough spatialized audio for more immersive listening.",
                "stock": 15,
                "is_featured": True,
                "specs": {
                    "driver_size": "Custom Bose Acoustic",
                    "battery_life": "24 Hours (Immersive Audio On)",
                    "connectivity": "Bluetooth 5.3 / Multipoint",
                    "noise_cancellation": "Quiet, Aware, and Custom ANC",
                    "frequency_response": "15 Hz - 22,000 Hz",
                    "impedance": "32 Ohms",
                    "weight": "254g",
                    "warranty": "1 Year Manufacturer"
                }
            },
            {
                "name": "Sennheiser HD 660S2 Open-Back",
                "brand": "Sennheiser",
                "category": "Studio Headphones",
                "price": Decimal("499.95"),
                "discount_price": None,
                "description": "Revel in intimate sound with sub-bass extension. Audiophile-grade transducers delivering lush, natural vocals and immaculate clarity.",
                "stock": 10,
                "is_featured": True,
                "specs": {
                    "driver_size": "38mm Audiophile Transducer",
                    "battery_life": "N/A (Wired)",
                    "connectivity": "6.35mm Stereo & 4.4mm Balanced",
                    "noise_cancellation": "Open-Back Acoustic Design",
                    "frequency_response": "8 Hz - 41,500 Hz",
                    "impedance": "300 Ohms",
                    "weight": "260g",
                    "warranty": "2 Years Sennheiser"
                }
            },
            {
                "name": "Audio-Technica ATH-M50xBT2",
                "brand": "Audio-Technica",
                "category": "Studio Headphones",
                "price": Decimal("199.00"),
                "discount_price": Decimal("179.00"),
                "description": "The legendary M50x studio sound, now with wireless capability. Exceptional clarity throughout an extended frequency range with deep, accurate bass.",
                "stock": 30,
                "is_featured": False,
                "specs": {
                    "driver_size": "45mm Large-Aperture",
                    "battery_life": "50 Hours",
                    "connectivity": "Bluetooth 5.0 / AAC / LDAC",
                    "noise_cancellation": "Passive Acoustic Isolation",
                    "frequency_response": "15 Hz - 28,000 Hz",
                    "impedance": "38 Ohms",
                    "weight": "307g",
                    "warranty": "1 Year Manufacturer"
                }
            },
            {
                "name": "SoundSphere CyberPulse 7.1 Gaming Headset",
                "brand": "SoundSphere Signature",
                "category": "Gaming Headsets",
                "price": Decimal("149.99"),
                "discount_price": Decimal("119.99"),
                "description": "Tactical 7.1 spatial surround sound headset featuring ultra-low latency 2.4GHz wireless transmission, detachable broadcast-grade cardioid mic, and customizable RGB pulse illumination.",
                "stock": 40,
                "is_featured": True,
                "specs": {
                    "driver_size": "50mm Titanium Mesh",
                    "battery_life": "35 Hours (RGB Off)",
                    "connectivity": "2.4GHz Wireless USB Dongle + 3.5mm",
                    "noise_cancellation": "Environmental Noise Cancellation Mic",
                    "frequency_response": "20 Hz - 22,000 Hz",
                    "impedance": "32 Ohms",
                    "weight": "290g",
                    "warranty": "2 Years International"
                }
            },
            {
                "name": "JBL Tour Pro 2 TWS Earbuds",
                "brand": "JBL",
                "category": "Bluetooth Earbuds",
                "price": Decimal("249.95"),
                "discount_price": Decimal("199.95"),
                "description": "True wireless noise cancelling earbuds featuring the world's first Smart Charging Case with interactive touch display.",
                "stock": 20,
                "is_featured": False,
                "specs": {
                    "driver_size": "10mm Dynamic",
                    "battery_life": "40 Hours (10h Earbuds + 30h Case)",
                    "connectivity": "Bluetooth 5.3 LE Audio",
                    "noise_cancellation": "True Adaptive Noise Cancelling",
                    "frequency_response": "20 Hz - 20,000 Hz",
                    "impedance": "16 Ohms",
                    "weight": "85g Total",
                    "warranty": "1 Year JBL"
                }
            },
            {
                "name": "SoundSphere Minimalist Aluminum Stand",
                "brand": "SoundSphere Signature",
                "category": "Headphone Stands",
                "price": Decimal("49.99"),
                "discount_price": Decimal("39.99"),
                "description": "Precision CNC milled aircraft-grade aluminum headphone stand with silicone weighted base and non-scratch leather arch rest.",
                "stock": 50,
                "is_featured": False,
                "specs": {
                    "driver_size": "N/A",
                    "battery_life": "N/A",
                    "connectivity": "N/A",
                    "noise_cancellation": "N/A",
                    "frequency_response": "N/A",
                    "impedance": "N/A",
                    "weight": "420g Solid Base",
                    "warranty": "Lifetime Limited"
                }
            },
            {
                "name": "SoundSphere Armor Shield Travel Case",
                "brand": "SoundSphere Signature",
                "category": "Carrying Cases",
                "price": Decimal("34.99"),
                "discount_price": Decimal("29.99"),
                "description": "Shockproof, water-resistant ballistic nylon hard shell case with custom cable organizer pouch.",
                "stock": 60,
                "is_featured": False,
                "specs": {
                    "driver_size": "N/A",
                    "battery_life": "N/A",
                    "connectivity": "N/A",
                    "noise_cancellation": "N/A",
                    "frequency_response": "N/A",
                    "impedance": "N/A",
                    "weight": "180g",
                    "warranty": "1 Year"
                }
            },
            {
                "name": "SoundSphere Pro-Series Braided Cable (1.5m)",
                "brand": "SoundSphere Signature",
                "category": "Charging Cables",
                "price": Decimal("24.99"),
                "discount_price": Decimal("19.99"),
                "description": "High-purity oxygen-free copper (OFC) braided audio cable with 24k gold-plated 3.5mm connectors.",
                "stock": 100,
                "is_featured": False,
                "specs": {
                    "driver_size": "N/A",
                    "battery_life": "N/A",
                    "connectivity": "3.5mm Male to 3.5mm Male",
                    "noise_cancellation": "N/A",
                    "frequency_response": "N/A",
                    "impedance": "Ultra Low Resistance",
                    "weight": "45g",
                    "warranty": "3 Years"
                }
            },
            {
                "name": "Velour & Memory Foam Ear Cushions",
                "brand": "SoundSphere Signature",
                "category": "Ear Cushions",
                "price": Decimal("29.99"),
                "discount_price": None,
                "description": "Ultra-breathable velour ear pads filled with high-density memory foam for extended studio listening comfort.",
                "stock": 45,
                "is_featured": False,
                "specs": {
                    "driver_size": "Universal 90mm Oval",
                    "battery_life": "N/A",
                    "connectivity": "N/A",
                    "noise_cancellation": "Enhanced Passive Seal",
                    "frequency_response": "N/A",
                    "impedance": "N/A",
                    "weight": "30g",
                    "warranty": "1 Year"
                }
            }
        ]

        for item in products_seed:
            sdata = item["specs"]
            prod, pcreated = Product.objects.get_or_create(
                name=item["name"],
                defaults={
                    "brand": brands[item["brand"]],
                    "category": categories[item["category"]],
                    "price": item["price"],
                    "discount_price": item["discount_price"],
                    "description": item["description"],
                    "stock": item["stock"],
                    "is_featured": item["is_featured"],
                    "driver_size": sdata["driver_size"],
                    "battery_life": sdata["battery_life"],
                    "connectivity": sdata["connectivity"],
                    "noise_cancellation": sdata["noise_cancellation"],
                    "frequency_response": sdata["frequency_response"],
                    "impedance": sdata["impedance"],
                    "weight": sdata["weight"],
                    "warranty": sdata["warranty"],
                }
            )

            # Sample Review
            if pcreated:
                Review.objects.create(
                    product=prod,
                    user=admin_user,
                    rating=5,
                    headline="Exceptional Sound & Design!",
                    comment=f"I was blown away by the acoustic quality and build of the {prod.name}. Highly recommended audio gear!"
                )

        self.stdout.write(self.style.SUCCESS(f"Successfully seeded {len(products_seed)} products, categories, and brands into SoundSphere!"))
