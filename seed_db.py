import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kitchen_kilowatt.settings')
django.setup()

from django.contrib.auth import get_user_model
from accounts.models import Address, CustomerProfile
from products.models import Category, Brand, Product, ProductVariant, ProductImage, Banner
from inventory.models import Stock, StockLog
from orders.models import Coupon
from reviews.models import Review
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

def seed_database():
    print("Seeding Kitchen & Kilowatt database...")

    # 1. Create Superuser & Customer
    if not User.objects.filter(username='admin').exists():
        admin_user = User.objects.create_superuser('admin', 'admin@kitchenandkilowatt.com', 'admin123')
        admin_user.first_name = "Master"
        admin_user.last_name = "Admin"
        admin_user.save()
        print("Created superuser: admin / admin123")
    else:
        admin_user = User.objects.get(username='admin')

    if not User.objects.filter(username='customer').exists():
        customer = User.objects.create_user('customer', 'customer@example.com', 'customer123')
        customer.first_name = "Eleanor"
        customer.last_name = "Vane"
        customer.phone_number = "+1 (555) 234-5678"
        customer.save()
        
        # Add Address
        Address.objects.create(
            user=customer,
            full_name="Eleanor Vane",
            phone="+1 (555) 234-5678",
            street_address="742 Copper Wire Avenue",
            apartment_suite="Suite 4B",
            city="San Francisco",
            state="CA",
            postal_code="94107",
            country="United States",
            address_type="SHIPPING",
            is_default=True
        )
        print("Created customer user: customer / customer123")
    else:
        customer = User.objects.get(username='customer')

    # 2. Categories
    cat_appliances, _ = Category.objects.get_or_create(
        name="Smart Appliances",
        defaults={"description": "High-powered electric countertop ovens, smart blenders, and induction tech.", "icon": "fa-bolt", "is_featured": True}
    )
    cat_cookware, _ = Category.objects.get_or_create(
        name="Precision Cookware",
        defaults={"description": "Heavy-duty copper, tri-ply stainless steel, and cast iron cookware.", "icon": "fa-fire", "is_featured": True}
    )
    cat_gadgets, _ = Category.objects.get_or_create(
        name="Kitchen Gadgets",
        defaults={"description": "Digital scales, precision sous-vide sticks, thermo probes, and smart timers.", "icon": "fa-microchip", "is_featured": True}
    )
    cat_lifestyle, _ = Category.objects.get_or_create(
        name="Lifestyle & Decor",
        defaults={"description": "Barware, electric carafes, coffee bar fixtures, and LED under-cabinet lights.", "icon": "fa-mug-hot", "is_featured": True}
    )

    # 3. Brands
    brand_kilowatt, _ = Brand.objects.get_or_create(name="Kilowatt Pro", defaults={"description": "Engineering culinary energy."})
    brand_artisan, _ = Brand.objects.get_or_create(name="Artisan Copper", defaults={"description": "Handcrafted metallic luxury."})
    brand_culinary, _ = Brand.objects.get_or_create(name="Culinary Tech", defaults={"description": "Digital smart kitchen sensors."})

    # 4. Products
    products_data = [
        {
            "name": "Kilowatt Smart Convection Air Oven 2000W",
            "sku": "KK-OVEN-2000W",
            "category": cat_appliances,
            "brand": brand_kilowatt,
            "price": 349.99,
            "discount_price": 299.99,
            "short_description": "2000W convection steam and air-fry oven with dual zone copper quartz heating.",
            "description": "Experience intense culinary energy with the Kilowatt Smart Convection Oven. Featuring 20-in-1 presets, dual-zone temperature control up to 500°F, crisp steam injection, and smart Wi-Fi recipe synchronization.",
            "features": [
                "2000 Watts dual copper-element rapid heating",
                "Full color HD touch interface with guided cooking presets",
                "Precision steam injection for bakery-grade crusts",
                "Graphite brushed steel housing with copper metallic controls"
            ],
            "specifications": {
                "Power": "2000 Watts",
                "Capacity": "26 Liters / 6 Slice Toast",
                "Voltage": "120V / 60Hz",
                "Dimensions": "17.5\" W x 16.2\" D x 14.8\" H",
                "Warranty": "3 Years Limited"
            },
            "is_featured": True,
            "is_best_seller": True,
            "image_filename": "hero_smart_oven.png",
            "stock": 18,
            "variants": [
                {"name": "Graphite Steel & Copper (Standard 120V)", "sku": "KK-OVEN-2000W-GC", "price_override": 299.99, "stock": 12},
                {"name": "Midnight Black Anodized (120V)", "sku": "KK-OVEN-2000W-MB", "price_override": 319.99, "stock": 6},
            ]
        },
        {
            "name": "Kilowatt Pro Espresso Machine 15-Bar",
            "sku": "KK-ESPRESSO-15B",
            "category": cat_appliances,
            "brand": brand_kilowatt,
            "price": 499.99,
            "discount_price": 449.99,
            "short_description": "Italian 15-bar pump espresso machine with PID thermo-coil and copper portafilter.",
            "description": "Brew cafe-quality espresso in seconds. The Kilowatt Pro Espresso Machine features precision PID temperature stability, an analog pressure gauge framed in copper, and a micro-foam commercial steam wand.",
            "features": [
                "Commercial 15-Bar Italian vibration pump",
                "PID precise temperature stability within ±1°C",
                "Heavyweight 58mm solid brass & copper portafilter",
                "Integrated cup warming plate"
            ],
            "specifications": {
                "Pump Pressure": "15 Bar",
                "Water Tank": "2.2 Liters Removable",
                "Heating System": "Thermo-Coil Copper Line",
                "Weight": "21 lbs"
            },
            "is_featured": True,
            "is_best_seller": True,
            "image_filename": "espresso_kilowatt.png",
            "stock": 8,
            "variants": [
                {"name": "Graphite & Brushed Copper", "sku": "KK-ESPRESSO-15B-GC", "price_override": 449.99, "stock": 5},
                {"name": "Full Metallic Copper Limited", "sku": "KK-ESPRESSO-15B-CO", "price_override": 499.99, "stock": 3},
            ]
        },
        {
            "name": "Turbine 1800W High-Velocity Blender",
            "sku": "KK-BLENDER-1800",
            "category": cat_appliances,
            "brand": brand_kilowatt,
            "price": 229.99,
            "discount_price": 189.99,
            "short_description": "Heavy-duty 1800W commercial blender with titanium-copper 6-leaf blade.",
            "description": "Pulverize frozen fruit, ice, and tough greens in seconds. The Turbine 1800W Blender uses military-grade titanium blades coated in copper alloy and a shatterproof BPA-free Tritan pitcher.",
            "features": [
                "1800W Peak Performance Commercial Motor",
                "2.5L Shatterproof Tritan Container",
                "Pulse and 8 Variable Speed Precision Dials",
                "Automated self-cleaning cycle in 30 seconds"
            ],
            "specifications": {
                "Motor Power": "1800W / 2.4 HP",
                "RPM": "32,000 RPM",
                "Pitcher Capacity": "2.5 Liters",
                "Blade Material": "Titanium Copper Alloy"
            },
            "is_featured": True,
            "is_best_seller": False,
            "image_filename": "pro_blender.png",
            "stock": 25,
            "variants": []
        },
        {
            "name": "Artisan Heritage 10-Piece Copper Cookware Set",
            "sku": "KK-COOKWARE-10P",
            "category": cat_cookware,
            "brand": brand_artisan,
            "price": 699.99,
            "discount_price": 599.99,
            "short_description": "Hand-hammered 2.5mm solid copper pots and pans with 18/10 stainless steel lining.",
            "description": "Unrivaled heat response and timeless beauty. The Artisan Heritage Cookware set combines a thick 2.5mm copper exterior with non-reactive stainless steel interior for unmatched temperature control.",
            "features": [
                "Thick 2.5mm solid copper body for instant thermal conductivity",
                "18/10 Stainless interior requiring no re-tinning",
                "Riveted cast iron handles with copper alloy rivets",
                "Compatible with gas, electric, and halogen cooktops"
            ],
            "specifications": {
                "Set Includes": "8\" Skillet, 10\" Skillet, 2Qt Saucepan, 3Qt Saucepan, 4Qt Saute Pan, 8Qt Stockpot + Lids",
                "Material": "Solid Copper + 18/10 Stainless Lining",
                "Oven Safe": "Up to 500°F"
            },
            "is_featured": True,
            "is_best_seller": True,
            "image_filename": "copper_cookware_set.png",
            "stock": 4, # Low stock demo!
            "variants": []
        },
        {
            "name": "Kilowatt Precision Gooseneck Electric Kettle 1200W",
            "sku": "KK-KETTLE-1200W",
            "category": cat_lifestyle,
            "brand": brand_culinary,
            "price": 119.99,
            "discount_price": 99.99,
            "short_description": "Pour-over electric gooseneck kettle with 1° degree digital temp control and hold mode.",
            "description": "Craft the ultimate pour-over coffee and delicate teas with exact temperature accuracy down to 1 degree Fahrenheit. Features a 60-minute heat hold and ergonomic copper handle.",
            "features": [
                "1200W Strix rapid boiling base",
                "1-Degree temperature adjustment from 104°F to 212°F",
                "Counterbalanced copper trim handle for smooth pour stream",
                "Built-in brew stopwatch timer"
            ],
            "specifications": {
                "Capacity": "1.0 Liter",
                "Power": "1200W",
                "Temperature Range": "104°F - 212°F",
                "Hold Time": "60 Minutes"
            },
            "is_featured": False,
            "is_best_seller": True,
            "image_filename": "electric_kettle.png",
            "stock": 30,
            "variants": [
                {"name": "Matte Charcoal with Copper Accents", "sku": "KK-KETTLE-1200W-MC", "price_override": 99.99, "stock": 20},
                {"name": "Polished Pure Copper Finish", "sku": "KK-KETTLE-1200W-PC", "price_override": 119.99, "stock": 10},
            ]
        }
    ]

    for p_data in products_data:
        prod, created = Product.objects.get_or_create(
            sku=p_data["sku"],
            defaults={
                "name": p_data["name"],
                "category": p_data["category"],
                "brand": p_data["brand"],
                "price": p_data["price"],
                "discount_price": p_data["discount_price"],
                "short_description": p_data["short_description"],
                "description": p_data["description"],
                "features": p_data["features"],
                "specifications": p_data["specifications"],
                "is_featured": p_data["is_featured"],
                "is_best_seller": p_data["is_best_seller"],
            }
        )

        # Image setup
        img_path = f"products/{p_data['image_filename']}"
        ProductImage.objects.get_or_create(
            product=prod,
            is_primary=True,
            defaults={"image": img_path, "alt_text": prod.name, "display_order": 1}
        )

        # Stock setup
        if not prod.variants.exists() and not p_data["variants"]:
            stock, _ = Stock.objects.get_or_create(
                product=prod,
                variant=None,
                defaults={"quantity": p_data["stock"], "low_stock_threshold": 5}
            )
            StockLog.objects.get_or_create(
                product=prod,
                variant=None,
                reason="INITIAL",
                defaults={"change_quantity": p_data["stock"], "resulting_quantity": p_data["stock"], "notes": "Initial seed stock"}
            )
        else:
            for v_data in p_data["variants"]:
                variant, _ = ProductVariant.objects.get_or_create(
                    sku=v_data["sku"],
                    defaults={
                        "product": prod,
                        "name": v_data["name"],
                        "price_override": v_data["price_override"],
                    }
                )
                stock, _ = Stock.objects.get_or_create(
                    product=prod,
                    variant=variant,
                    defaults={"quantity": v_data["stock"], "low_stock_threshold": 5}
                )
                StockLog.objects.get_or_create(
                    product=prod,
                    variant=variant,
                    reason="INITIAL",
                    defaults={"change_quantity": v_data["stock"], "resulting_quantity": v_data["stock"], "notes": f"Initial variant stock for {variant.name}"}
                )

        # Sample reviews
        Review.objects.get_or_create(
            product=prod,
            user=customer,
            defaults={
                "rating": 5,
                "title": "Outstanding build quality and stunning kitchen aesthetics!",
                "comment": f"Bought this {prod.name} two weeks ago. The performance is top tier and the copper finish looks incredible in my kitchen.",
                "is_verified_purchase": True,
                "is_approved": True
            }
        )

    # 5. Coupons
    now = timezone.now()
    Coupon.objects.get_or_create(
        code="KILOWATT10",
        defaults={
            "discount_type": "PERCENTAGE",
            "discount_value": 10.00,
            "min_purchase_amount": 50.00,
            "valid_from": now - timedelta(days=1),
            "valid_to": now + timedelta(days=365),
            "active": True
        }
    )
    Coupon.objects.get_or_create(
        code="POWER20",
        defaults={
            "discount_type": "FIXED",
            "discount_value": 20.00,
            "min_purchase_amount": 100.00,
            "valid_from": now - timedelta(days=1),
            "valid_to": now + timedelta(days=365),
            "active": True
        }
    )

    # 6. Hero Banners
    Banner.objects.get_or_create(
        title="Culinary Power Meets Metallic Elegance",
        defaults={
            "subtitle": "Discover our flagship 2000W Smart Convection Ovens & Artisanal Copper Cookware.",
            "badge": "NEW 2026 COLLECTION",
            "button_text": "Explore Appliances",
            "button_link": "/products/?category=smart-appliances",
            "display_order": 1,
            "is_active": True
        }
    )

    print("Database seeding completed successfully!")

if __name__ == '__main__':
    seed_database()
