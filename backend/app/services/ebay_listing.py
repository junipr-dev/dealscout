"""eBay Listing creation via Inventory API."""

import uuid
from datetime import datetime
from typing import Optional
import httpx

from sqlalchemy.ext.asyncio import AsyncSession

from .ebay_seller import get_valid_access_token, EBAY_URLS
from ..config import get_settings

settings = get_settings()

# eBay API endpoints (dynamic based on sandbox setting)
EBAY_INVENTORY_API = EBAY_URLS["inventory"]
EBAY_MEDIA_API = "https://api.sandbox.ebay.com/commerce/media/v1_beta" if settings.ebay_sandbox else "https://api.ebay.com/commerce/media/v1_beta"
EBAY_VIEW_URL = "https://sandbox.ebay.com/itm" if settings.ebay_sandbox else "https://www.ebay.com/itm"

# Condition mappings for eBay
CONDITION_MAP = {
    "new": "NEW",
    "used": "USED_EXCELLENT",
    "needs_repair": "FOR_PARTS_OR_NOT_WORKING",
}


async def upload_image_to_ebay(
    db: AsyncSession,
    image_data: bytes,
    filename: str,
) -> Optional[str]:
    """
    Upload an image to eBay's media service.
    Returns the eBay image URL if successful.
    """
    access_token = await get_valid_access_token(db)
    if not access_token:
        raise ValueError("No valid eBay access token")

    async with httpx.AsyncClient() as client:
        # Step 1: Create upload task
        response = await client.post(
            f"{EBAY_MEDIA_API}/video",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
            json={
                "title": filename,
                "description": "Product image",
            },
            timeout=30.0,
        )

        # For images, we use a simpler approach - upload directly in offer
        # eBay accepts external URLs or base64 in the pictureDetails
        return None  # We'll handle images differently


async def create_ebay_listing(
    db: AsyncSession,
    flip_id: int,
    title: str,
    description: str,
    category_id: str,
    condition: str,
    price: float,
    quantity: int = 1,
    image_urls: list[str] = None,
    brand: str = None,
    model: str = None,
    aspects: dict = None,
) -> dict:
    """
    Create a listing on eBay using the Inventory API.

    Returns:
        dict with listing_id and status
    """
    access_token = await get_valid_access_token(db)
    if not access_token:
        raise ValueError("No valid eBay access token. Please re-link your eBay account.")

    # Generate a unique SKU for this item
    sku = f"DS-{flip_id}-{uuid.uuid4().hex[:8]}"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Content-Language": "en-US",
    }

    async with httpx.AsyncClient() as client:
        # Step 1: Create/update inventory item
        # Build aspects dict for item specifics
        item_aspects = aspects or {}
        if brand:
            item_aspects["Brand"] = [brand]
        if model:
            item_aspects["Model"] = [model]

        product_data = {
            "title": title[:80],  # eBay limit
            "description": description,
            "imageUrls": image_urls or [],
        }

        if item_aspects:
            product_data["aspects"] = item_aspects

        inventory_item = {
            "availability": {
                "shipToLocationAvailability": {
                    "quantity": quantity
                }
            },
            "condition": CONDITION_MAP.get(condition, "USED_EXCELLENT"),
            "product": product_data,
        }

        response = await client.put(
            f"{EBAY_INVENTORY_API}/inventory_item/{sku}",
            headers=headers,
            json=inventory_item,
            timeout=30.0,
        )

        if response.status_code not in (200, 201, 204):
            error_detail = response.text
            print(f"eBay inventory item error: {response.status_code} - {error_detail}")
            raise ValueError(f"Failed to create inventory item: {error_detail}")

        # Step 2: Ensure we have an inventory location
        location_key = "default-location"
        location_response = await client.get(
            f"{EBAY_INVENTORY_API}/location/{location_key}",
            headers=headers,
            timeout=30.0,
        )

        if location_response.status_code == 404:
            # Create default location
            location_data = {
                "location": {
                    "address": {
                        "city": "Cookeville",
                        "stateOrProvince": "TN",
                        "postalCode": "38501",
                        "country": "US"
                    }
                },
                "locationTypes": ["WAREHOUSE"],
                "name": "Default Location",
                "merchantLocationStatus": "ENABLED"
            }
            await client.post(
                f"{EBAY_INVENTORY_API}/location/{location_key}",
                headers=headers,
                json=location_data,
                timeout=30.0,
            )

        # Step 3: Ensure business policies exist
        policies = await ensure_business_policies(access_token)

        if not policies.get("fulfillmentPolicyId"):
            return {
                "success": False,
                "error": "Could not create or find fulfillment policy",
                "requires_manual_listing": True,
            }

        # Step 4: Create offer
        offer = {
            "sku": sku,
            "marketplaceId": "EBAY_US",
            "format": "FIXED_PRICE",
            "listingDescription": description,
            "availableQuantity": quantity,
            "categoryId": category_id,
            "merchantLocationKey": location_key,
            "pricingSummary": {
                "price": {
                    "currency": "USD",
                    "value": str(price)
                }
            },
            "listingPolicies": policies,
        }

        response = await client.post(
            f"{EBAY_INVENTORY_API}/offer",
            headers=headers,
            json=offer,
            timeout=30.0,
        )

        if response.status_code not in (200, 201):
            error_detail = response.text
            print(f"eBay offer error: {response.status_code} - {error_detail}")
            # Return partial success - item created but not listed
            return {
                "success": False,
                "sku": sku,
                "error": f"Item created but offer failed: {error_detail}",
                "requires_manual_listing": True,
            }

        offer_data = response.json()
        offer_id = offer_data.get("offerId")

        # Step 5: Publish the offer
        response = await client.post(
            f"{EBAY_INVENTORY_API}/offer/{offer_id}/publish",
            headers=headers,
            timeout=30.0,
        )

        if response.status_code not in (200, 201):
            error_detail = response.text
            print(f"eBay publish error: {response.status_code} - {error_detail}")
            return {
                "success": False,
                "sku": sku,
                "offer_id": offer_id,
                "error": f"Offer created but publish failed: {error_detail}",
                "requires_manual_listing": True,
            }

        publish_data = response.json()
        listing_id = publish_data.get("listingId")

        return {
            "success": True,
            "sku": sku,
            "offer_id": offer_id,
            "listing_id": listing_id,
            "ebay_url": f"{EBAY_VIEW_URL}/{listing_id}",
        }


async def ensure_business_policies(access_token: str) -> dict:
    """Create default business policies if they don't exist."""
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    account_api = EBAY_URLS["account"]
    policies = {}

    async with httpx.AsyncClient() as client:
        # Check/create fulfillment policy
        print(f"Checking fulfillment policies at: {account_api}/fulfillment_policy")
        response = await client.get(
            f"{account_api}/fulfillment_policy?marketplace_id=EBAY_US",
            headers=headers,
            timeout=30.0,
        )
        print(f"Fulfillment policy GET response: {response.status_code} - {response.text[:500] if response.text else 'empty'}")

        if response.status_code == 200:
            data = response.json()
            policy_list = data.get("fulfillmentPolicies", [])
            if policy_list:
                policies["fulfillmentPolicyId"] = policy_list[0].get("fulfillmentPolicyId")

        if "fulfillmentPolicyId" not in policies:
            # Create a default fulfillment policy
            print("Creating new fulfillment policy...")
            policy_data = {
                "name": "DealScout Default Shipping",
                "marketplaceId": "EBAY_US",
                "categoryTypes": [{"name": "ALL_EXCLUDING_MOTORS_VEHICLES"}],
                "handlingTime": {"value": 1, "unit": "DAY"},
                "shippingOptions": [{
                    "optionType": "DOMESTIC",
                    "costType": "FLAT_RATE",
                    "shippingServices": [{
                        "sortOrder": 1,
                        "shippingCarrierCode": "USPS",
                        "shippingServiceCode": "USPSPriority",
                        "shippingCost": {"value": "0.00", "currency": "USD"},
                        "freeShipping": True
                    }]
                }]
            }
            response = await client.post(
                f"{account_api}/fulfillment_policy",
                headers=headers,
                json=policy_data,
                timeout=30.0,
            )
            print(f"Fulfillment policy POST response: {response.status_code} - {response.text[:500] if response.text else 'empty'}")
            if response.status_code in (200, 201):
                policies["fulfillmentPolicyId"] = response.json().get("fulfillmentPolicyId")

        # Check/create payment policy
        response = await client.get(
            f"{account_api}/payment_policy?marketplace_id=EBAY_US",
            headers=headers,
            timeout=30.0,
        )

        if response.status_code == 200:
            data = response.json()
            policy_list = data.get("paymentPolicies", [])
            if policy_list:
                policies["paymentPolicyId"] = policy_list[0].get("paymentPolicyId")

        if "paymentPolicyId" not in policies:
            policy_data = {
                "name": "DealScout Default Payment",
                "marketplaceId": "EBAY_US",
                "categoryTypes": [{"name": "ALL_EXCLUDING_MOTORS_VEHICLES"}],
                "paymentMethods": [{"paymentMethodType": "PERSONAL_CHECK"}]
            }
            response = await client.post(
                f"{account_api}/payment_policy",
                headers=headers,
                json=policy_data,
                timeout=30.0,
            )
            if response.status_code in (200, 201):
                policies["paymentPolicyId"] = response.json().get("paymentPolicyId")

        # Check/create return policy
        response = await client.get(
            f"{account_api}/return_policy?marketplace_id=EBAY_US",
            headers=headers,
            timeout=30.0,
        )

        if response.status_code == 200:
            data = response.json()
            policy_list = data.get("returnPolicies", [])
            if policy_list:
                policies["returnPolicyId"] = policy_list[0].get("returnPolicyId")

        if "returnPolicyId" not in policies:
            policy_data = {
                "name": "DealScout Default Returns",
                "marketplaceId": "EBAY_US",
                "categoryTypes": [{"name": "ALL_EXCLUDING_MOTORS_VEHICLES"}],
                "returnsAccepted": True,
                "returnPeriod": {"value": 30, "unit": "DAY"},
                "refundMethod": "MONEY_BACK",
                "returnShippingCostPayer": "BUYER"
            }
            response = await client.post(
                f"{account_api}/return_policy",
                headers=headers,
                json=policy_data,
                timeout=30.0,
            )
            if response.status_code in (200, 201):
                policies["returnPolicyId"] = response.json().get("returnPolicyId")

    return policies


async def get_listing_policies(db: AsyncSession) -> dict:
    """Get the seller's listing policies (payment, return, fulfillment)."""
    access_token = await get_valid_access_token(db)
    if not access_token:
        return {}

    async with httpx.AsyncClient() as client:
        policies = {}

        for policy_type in ["payment_policy", "return_policy", "fulfillment_policy"]:
            response = await client.get(
                f"{EBAY_INVENTORY_API.replace('/inventory/v1', '/account/v1')}/{policy_type}?marketplace_id=EBAY_US",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                },
                timeout=30.0,
            )

            if response.status_code == 200:
                data = response.json()
                policy_list = data.get(f"{policy_type.replace('_', '')}s", [])
                if policy_list:
                    # Get the first/default policy
                    policies[policy_type] = policy_list[0].get(f"{policy_type.replace('_', '')}Id")

        return policies
