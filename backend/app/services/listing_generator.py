"""eBay listing generation tools."""

from typing import Optional

import httpx

from ..config import get_settings

settings = get_settings()


# Common eBay category IDs for quick mapping
EBAY_CATEGORIES = {
    # Electronics
    "gpu": 27386,  # Computer Components > Graphics/Video Cards
    "laptop": 177,  # Computers/Tablets > Laptops
    "phone": 9355,  # Cell Phones & Accessories > Cell Phones
    "tablet": 171485,  # Computers/Tablets > Tablets
    "gaming_console": 139971,  # Video Games & Consoles > Consoles
    "monitor": 80053,  # Computers/Tablets > Monitors
    "tv": 11071,  # Consumer Electronics > TVs
    "headphones": 112529,  # Consumer Electronics > Portable Audio > Headphones
    "speaker": 14990,  # Consumer Electronics > Home Audio > Speakers
    "camera": 31388,  # Cameras & Photo > Digital Cameras
    "smartwatch": 178893,  # Cell Phones > Smart Watches
    "router": 44995,  # Computers/Tablets > Home Networking
    # Tools
    "power_tool": 631,  # Home & Garden > Tools > Power Tools
    "hand_tool": 3244,  # Home & Garden > Tools > Hand Tools
    # Vehicles
    "car": 6001,  # eBay Motors > Cars & Trucks
    "motorcycle": 6024,  # eBay Motors > Motorcycles
    # Furniture
    "furniture": 3197,  # Home & Garden > Furniture
    "couch": 38208,  # Furniture > Sofas
    "chair": 20490,  # Furniture > Chairs
    # Default
    "other": 99,  # Everything Else
}


def generate_listing_title(
    brand: Optional[str],
    model: Optional[str],
    subcategory: Optional[str],
    condition: Optional[str],
    variants: Optional[str] = None,
    part_numbers: Optional[list] = None,
    item_name: Optional[str] = None,
    max_length: int = 80,
) -> str:
    """
    Generate an optimized eBay listing title.

    eBay titles are max 80 characters. Prioritizes:
    1. Brand (searches rely on this)
    2. Model (specific identification)
    3. Key variant info (storage, color, edition)
    4. Condition indicator
    5. Part number (for searching)

    Returns:
        Optimized listing title under 80 chars.
    """
    parts = []

    # Brand is most important for search
    if brand:
        parts.append(brand)

    # Model
    if model:
        parts.append(model)
    elif subcategory:
        parts.append(subcategory.title())

    # Variant info
    if variants:
        parts.append(variants)

    # Condition - only add for non-obvious states
    if condition == "new":
        parts.append("NEW SEALED")
    elif condition == "needs_repair":
        parts.append("FOR PARTS")

    # Part number (helpful for exact matches)
    if part_numbers and len(part_numbers) > 0:
        parts.append(part_numbers[0])

    # Build title, truncate if needed
    title = " ".join(parts)

    # Fallback to item_name if no structured data available
    if not title.strip() and item_name:
        title = item_name

    if len(title) > max_length:
        # Truncate intelligently - don't cut words
        title = title[:max_length].rsplit(" ", 1)[0]

    return title


def generate_listing_description(
    title: str,
    brand: Optional[str] = None,
    model: Optional[str] = None,
    condition: Optional[str] = None,
    item_details: Optional[dict] = None,
    repair_notes: Optional[str] = None,
    accessory_completeness: Optional[str] = None,
    bundle_items: Optional[list] = None,
) -> str:
    """
    Generate a professional branded HTML eBay listing description.

    Creates a mobile-responsive, visually appealing template that:
    - Uses clean, modern styling
    - Highlights key product information
    - Builds buyer trust with clear policies
    - Works on all devices

    Returns:
        HTML formatted description string.
    """
    # Condition info
    condition_config = {
        "new": {
            "text": "Brand New - Factory Sealed",
            "detail": "Never opened or used. Includes all original accessories and packaging.",
            "color": "#4ecca3",
            "icon": "✓"
        },
        "used": {
            "text": "Pre-Owned - Excellent Condition",
            "detail": "Fully tested and working. Shows minimal signs of use.",
            "color": "#4ecca3",
            "icon": "✓"
        },
        "needs_repair": {
            "text": "For Parts or Repair",
            "detail": "SOLD AS-IS. Not working - please read details below.",
            "color": "#ff6b6b",
            "icon": "⚠"
        },
        "unknown": {
            "text": "Condition Unknown",
            "detail": "Not tested. Sold as-is - please ask questions.",
            "color": "#ff9800",
            "icon": "?"
        }
    }

    cond = condition_config.get(condition, condition_config["unknown"])

    # Build specs rows
    specs_rows = ""
    if brand:
        specs_rows += f'<tr><td style="padding:8px 12px;border-bottom:1px solid #333;color:#888;">Brand</td><td style="padding:8px 12px;border-bottom:1px solid #333;color:#fff;font-weight:500;">{brand}</td></tr>'
    if model:
        specs_rows += f'<tr><td style="padding:8px 12px;border-bottom:1px solid #333;color:#888;">Model</td><td style="padding:8px 12px;border-bottom:1px solid #333;color:#fff;font-weight:500;">{model}</td></tr>'
    if item_details:
        for key, value in item_details.items():
            if value:
                label = key.replace('_', ' ').title()
                specs_rows += f'<tr><td style="padding:8px 12px;border-bottom:1px solid #333;color:#888;">{label}</td><td style="padding:8px 12px;border-bottom:1px solid #333;color:#fff;font-weight:500;">{value}</td></tr>'

    # Build includes list
    includes_html = ""
    if bundle_items:
        for item in bundle_items:
            includes_html += f'<li style="padding:4px 0;color:#ddd;">{item}</li>'
    elif accessory_completeness:
        if accessory_completeness.lower() == "complete":
            includes_html = '<li style="padding:4px 0;color:#ddd;">Item with all original accessories</li>'
        else:
            includes_html = f'<li style="padding:4px 0;color:#ddd;">Item only ({accessory_completeness})</li>'
    else:
        includes_html = '<li style="padding:4px 0;color:#ddd;">Item as shown in photos</li>'

    # Known issues section (for repair items)
    issues_section = ""
    if repair_notes and condition == "needs_repair":
        issues_section = f'''
        <div style="background:#2a1a1a;border-left:4px solid #ff6b6b;padding:16px;margin:20px 0;border-radius:0 8px 8px 0;">
            <h3 style="color:#ff6b6b;margin:0 0 8px 0;font-size:16px;">⚠ Known Issues</h3>
            <p style="color:#ddd;margin:0;line-height:1.6;">{repair_notes}</p>
        </div>
        '''

    # Full HTML template
    html = f'''
<div style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;max-width:800px;margin:0 auto;background:#0f0f1a;color:#fff;padding:0;">

    <!-- Header -->
    <div style="background:linear-gradient(135deg,#1a1a2e 0%,#16213e 100%);padding:24px;text-align:center;border-radius:8px 8px 0 0;">
        <h1 style="margin:0;font-size:22px;font-weight:600;color:#fff;line-height:1.4;">{title}</h1>
    </div>

    <!-- Condition Badge -->
    <div style="background:#1a1a2e;padding:16px 24px;border-bottom:1px solid #333;">
        <div style="display:inline-block;background:{cond['color']}22;border:1px solid {cond['color']};border-radius:6px;padding:12px 20px;">
            <span style="color:{cond['color']};font-size:18px;margin-right:8px;">{cond['icon']}</span>
            <span style="color:{cond['color']};font-weight:600;">{cond['text']}</span>
        </div>
        <p style="color:#aaa;margin:12px 0 0 0;font-size:14px;">{cond['detail']}</p>
    </div>

    {issues_section}

    <!-- Specifications -->
    <div style="padding:20px 24px;">
        <h2 style="color:#4ecca3;font-size:16px;margin:0 0 16px 0;text-transform:uppercase;letter-spacing:1px;">Specifications</h2>
        <table style="width:100%;border-collapse:collapse;background:#1a1a2e;border-radius:8px;overflow:hidden;">
            {specs_rows if specs_rows else '<tr><td style="padding:12px;color:#888;">See photos for details</td></tr>'}
        </table>
    </div>

    <!-- What's Included -->
    <div style="padding:20px 24px;background:#1a1a2e;">
        <h2 style="color:#4ecca3;font-size:16px;margin:0 0 16px 0;text-transform:uppercase;letter-spacing:1px;">What's Included</h2>
        <ul style="margin:0;padding-left:20px;list-style-type:disc;">
            {includes_html}
        </ul>
    </div>

    <!-- Shipping & Policies -->
    <div style="padding:20px 24px;">
        <div style="display:flex;flex-wrap:wrap;gap:16px;">
            <div style="flex:1;min-width:200px;background:#1a1a2e;padding:16px;border-radius:8px;">
                <h3 style="color:#fff;font-size:14px;margin:0 0 8px 0;">📦 Fast Shipping</h3>
                <p style="color:#888;margin:0;font-size:13px;">Ships within 1-2 business days. Carefully packaged for safe delivery.</p>
            </div>
            <div style="flex:1;min-width:200px;background:#1a1a2e;padding:16px;border-radius:8px;">
                <h3 style="color:#fff;font-size:14px;margin:0 0 8px 0;">💬 Questions?</h3>
                <p style="color:#888;margin:0;font-size:13px;">Feel free to message us before purchasing. We respond quickly!</p>
            </div>
        </div>
    </div>

    <!-- Footer -->
    <div style="background:#1a1a2e;padding:16px 24px;text-align:center;border-radius:0 0 8px 8px;border-top:1px solid #333;">
        <p style="color:#666;margin:0;font-size:12px;">Thank you for shopping with us!</p>
    </div>

</div>
'''

    return html.strip()


def generate_testing_checklist(
    category: Optional[str],
    subcategory: Optional[str],
    brand: Optional[str] = None,
    model: Optional[str] = None,
) -> list[str]:
    """
    Generate a testing checklist based on item type.

    Helps ensure items are properly tested before listing.

    Returns:
        List of testing steps for this item type.
    """
    checklist = ["Visual inspection for damage/wear"]

    # Electronics general
    if category == "electronics":
        checklist.extend([
            "Powers on successfully",
            "Check for overheating",
            "All ports functional",
        ])

    # Specific subcategories
    subcategory_lower = (subcategory or "").lower()

    if subcategory_lower in ["gpu", "graphics card"]:
        checklist.extend([
            "Install in test system",
            "Check device manager recognition",
            "Run GPU-Z for specs",
            "Run 3DMark or FurMark stress test",
            "Check fan operation and temps",
            "Test all display outputs (HDMI, DP)",
            "Check for artifacts in games/benchmarks",
        ])

    elif subcategory_lower in ["laptop", "notebook"]:
        checklist.extend([
            "Boot to BIOS/OS",
            "Check battery health (cycles, capacity)",
            "Test keyboard (all keys)",
            "Test trackpad (click, scroll)",
            "Test display (dead pixels, backlight bleed)",
            "Test webcam and microphone",
            "Test WiFi and Bluetooth",
            "Test all USB/ports",
            "Run disk health check",
        ])

    elif subcategory_lower in ["phone", "smartphone"]:
        checklist.extend([
            "Power on and boot",
            "Check for iCloud/Google lock",
            "Test touchscreen (all areas)",
            "Test Face ID / fingerprint",
            "Test cameras (front and back)",
            "Test speakers and microphone",
            "Test cellular signal",
            "Test WiFi and Bluetooth",
            "Check battery health percentage",
            "Test charging (wired and wireless)",
        ])

    elif subcategory_lower in ["tablet"]:
        checklist.extend([
            "Power on and boot",
            "Check for activation lock",
            "Test touchscreen responsiveness",
            "Test cameras",
            "Test speakers",
            "Test WiFi and Bluetooth",
            "Check battery health",
        ])

    elif subcategory_lower in ["gaming console", "console", "playstation", "xbox", "switch"]:
        checklist.extend([
            "Power on to home screen",
            "Check for account locks",
            "Test disc drive (if applicable)",
            "Test controller connectivity",
            "Test WiFi connection",
            "Run a game to test performance",
            "Test HDMI output",
            "Check for overheating/loud fans",
        ])

    elif subcategory_lower in ["tv", "television"]:
        checklist.extend([
            "Power on and display image",
            "Check for dead pixels/lines",
            "Test all HDMI ports",
            "Test speakers",
            "Test remote control",
            "Check for backlight bleed",
            "Test smart TV features",
        ])

    elif subcategory_lower in ["power tool"]:
        checklist.extend([
            "Powers on/runs",
            "Check for smooth operation",
            "Test battery charge (if cordless)",
            "Check safety features",
            "Test speed settings",
            "Check for excessive vibration",
        ])

    # Add final steps
    checklist.extend([
        "Take clear photos from all angles",
        "Document serial number if visible",
        "Note any cosmetic imperfections",
    ])

    return checklist


def suggest_ebay_category(
    category: Optional[str],
    subcategory: Optional[str],
) -> dict:
    """
    Suggest the best eBay category for an item.

    Returns:
        Dict with category_id and category_name.
    """
    # Try subcategory first (more specific)
    subcategory_lower = (subcategory or "").lower()
    category_lower = (category or "").lower()

    # Direct subcategory matches
    subcategory_map = {
        "gpu": ("gpu", "Graphics/Video Cards"),
        "graphics card": ("gpu", "Graphics/Video Cards"),
        "laptop": ("laptop", "Laptops & Netbooks"),
        "notebook": ("laptop", "Laptops & Netbooks"),
        "phone": ("phone", "Cell Phones & Smartphones"),
        "smartphone": ("phone", "Cell Phones & Smartphones"),
        "iphone": ("phone", "Cell Phones & Smartphones"),
        "tablet": ("tablet", "Tablets & eReaders"),
        "ipad": ("tablet", "Tablets & eReaders"),
        "playstation": ("gaming_console", "Video Game Consoles"),
        "xbox": ("gaming_console", "Video Game Consoles"),
        "switch": ("gaming_console", "Video Game Consoles"),
        "console": ("gaming_console", "Video Game Consoles"),
        "monitor": ("monitor", "Monitors, Projectors & Accs"),
        "tv": ("tv", "Televisions"),
        "television": ("tv", "Televisions"),
        "headphones": ("headphones", "Headphones"),
        "earbuds": ("headphones", "Headphones"),
        "airpods": ("headphones", "Headphones"),
        "speaker": ("speaker", "Speakers & Subwoofers"),
        "camera": ("camera", "Digital Cameras"),
        "smartwatch": ("smartwatch", "Smart Watches"),
        "apple watch": ("smartwatch", "Smart Watches"),
        "router": ("router", "Home Networking & Connectivity"),
        "drill": ("power_tool", "Power Tools"),
        "saw": ("power_tool", "Power Tools"),
        "couch": ("couch", "Sofas & Couches"),
        "sofa": ("couch", "Sofas & Couches"),
        "chair": ("chair", "Chairs"),
    }

    for key, (cat_key, cat_name) in subcategory_map.items():
        if key in subcategory_lower:
            return {
                "category_id": EBAY_CATEGORIES.get(cat_key, 99),
                "category_name": cat_name,
                "category_key": cat_key,
            }

    # Fallback to category
    category_map = {
        "electronics": ("other", "Consumer Electronics"),
        "tools": ("power_tool", "Tools & Equipment"),
        "furniture": ("furniture", "Furniture"),
        "vehicles": ("car", "Cars & Trucks"),
    }

    for key, (cat_key, cat_name) in category_map.items():
        if key in category_lower:
            return {
                "category_id": EBAY_CATEGORIES.get(cat_key, 99),
                "category_name": cat_name,
                "category_key": cat_key,
            }

    return {
        "category_id": 99,
        "category_name": "Everything Else",
        "category_key": "other",
    }


def generate_listing_suggestion(
    title: str,
    brand: Optional[str] = None,
    model: Optional[str] = None,
    category: Optional[str] = None,
    subcategory: Optional[str] = None,
    condition: Optional[str] = None,
    item_details: Optional[dict] = None,
    repair_notes: Optional[str] = None,
    accessory_completeness: Optional[str] = None,
    bundle_items: Optional[list] = None,
    variants: Optional[str] = None,
    part_numbers: Optional[list] = None,
) -> dict:
    """
    Generate a complete listing suggestion with all components.

    Returns:
        Dict with title, description, category, and testing_checklist.
    """
    listing_title = generate_listing_title(
        brand=brand,
        model=model,
        subcategory=subcategory,
        condition=condition,
        variants=variants,
        part_numbers=part_numbers,
        item_name=title,  # Fallback to original title/item_name
    )

    description = generate_listing_description(
        title=listing_title,
        brand=brand,
        model=model,
        condition=condition,
        item_details=item_details,
        repair_notes=repair_notes,
        accessory_completeness=accessory_completeness,
        bundle_items=bundle_items,
    )

    ebay_category = suggest_ebay_category(category, subcategory)

    testing_checklist = generate_testing_checklist(
        category=category,
        subcategory=subcategory,
        brand=brand,
        model=model,
    )

    return {
        "suggested_title": listing_title,
        "description": description,
        "ebay_category": ebay_category,
        "testing_checklist": testing_checklist,
    }
