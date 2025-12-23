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
    Generate a structured eBay listing description.

    Follows eBay best practices:
    - Clear condition statement
    - Detailed specifications
    - What's included
    - Known issues (for repair items)
    - No contact info or external links

    Returns:
        Formatted description string.
    """
    sections = []

    # Header
    sections.append(f"# {title}\n")

    # Condition section (critical for buyer trust)
    if condition:
        condition_text = {
            "new": "Brand new, factory sealed. Never opened or used.",
            "used": "Pre-owned and in good working condition. Tested and functional.",
            "needs_repair": "**SOLD AS-IS FOR PARTS OR REPAIR.** Item is not working - see details below.",
            "unknown": "Condition not tested. Sold as-is.",
        }.get(condition, "Condition unknown. Please ask questions before purchasing.")

        sections.append(f"## Condition\n{condition_text}\n")

    # Specifications
    if item_details or brand or model:
        sections.append("## Specifications\n")
        specs = []
        if brand:
            specs.append(f"- **Brand:** {brand}")
        if model:
            specs.append(f"- **Model:** {model}")
        if item_details:
            for key, value in item_details.items():
                if value:
                    specs.append(f"- **{key.replace('_', ' ').title()}:** {value}")
        sections.append("\n".join(specs) + "\n")

    # Repair notes (for needs_repair items)
    if repair_notes and condition == "needs_repair":
        sections.append(f"## Known Issues\n{repair_notes}\n")

    # What's included
    sections.append("## What's Included\n")
    if bundle_items:
        for item in bundle_items:
            sections.append(f"- {item}")
    elif accessory_completeness:
        if accessory_completeness.lower() == "complete":
            sections.append("- Item with all original accessories")
        else:
            sections.append(f"- Item only ({accessory_completeness})")
    else:
        sections.append("- Item as shown in photos")

    sections.append("\n")

    # Shipping note
    sections.append("## Shipping\nItem will be carefully packaged and shipped within 1-2 business days.\n")

    # Returns policy note
    sections.append("## Returns\nPlease review all photos and description carefully. Feel free to ask questions before purchasing.\n")

    return "\n".join(sections)


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
