from time import sleep
from os import getenv

from requests import post, get
from discord_webhook import DiscordWebhook, DiscordEmbed
from tinydb import TinyDB, Query

OPENSEA_URL = "https://api.opensea.io/api/v1/events"


def get_sales(collection: str) -> dict:
    """
    Get recent sales from opensea
    """

    response = get(
        OPENSEA_URL + f"?collection_slug={collection}&event_type=successful",
        headers={
            "Accept": "application/json",
            "X-API-KEY": getenv("OPENSEA_TOKEN")
        }
    )

    response.raise_for_status()

    return response.json().get("asset_events", [])


def get_listings(collection: str) -> dict:
    """
    Get recent listings from opensea
    """

    response = get(
        OPENSEA_URL + f"?collection_slug={collection}&event_type=created",
        headers={
            "Accept": "application/json",
            "X-API-KEY": getenv("OPENSEA_TOKEN")
        }
    )

    response.raise_for_status()

    return response.json().get("asset_events", [])


if __name__ == "__main__":

    if getenv("SALES_WEBHOOK_URL"):
        sales_db = TinyDB("sales.json")
        sales = Query()

        for sale in get_sales(getenv("COLLECTION")):

            if sales_db.search(sales.id == sale["id"]):
                print("already sent sale")
                continue

            for webhook_url in getenv("SALES_WEBHOOK_URL").split(';'):
                webhook = DiscordWebhook(url=webhook_url)

                coin = float(sale["total_price"])  / 1000000000000000000.0
                usd = float(sale["payment_token"]["usd_price"]) * coin
                kind = sale["asset"]['collection']["name"]
                description = sale['asset']['description'] or ""
                embed = DiscordEmbed(
                    title=sale["asset"]["name"],
                    url=sale["asset"]["permalink"],
                    description=f"{description}\n\n**A {kind} just got sold!**\n\n**Seller**: {sale['seller']['address']}\n**Buyer**: {sale['winner_account']['address']}\n**Price (BNB)**: {coin}{sale['payment_token']['symbol']}\n**Price (USD)**: ${usd}",
                    color="03b2f8",
                )

                embed.set_author(
                    name="NFT Sold",
                    url="https://opensea.io/",
                    icon_url="https://storage.googleapis.com/opensea-static/Logomark/Logomark-Blue.png",
                )

                embed.set_image(url=sale["asset"]["image_url"])

                webhook.add_embed(embed)

                response = webhook.execute()

                if response.status_code == 200:
                    sales_db.insert({"id": sale["id"]})
                    print(f"sent {sale['id']}")

            sleep(5)

    if getenv("LISTINGS_WEBHOOK_URL"):
        listings_db = TinyDB("listings.json")
        listings = Query()

        for listing in get_listings(getenv("COLLECTION")):

            if listings_db.search(listings.id == listing["id"]):
                print("already sent listing")
                continue

            for webhook_url in getenv("LISTINGS_WEBHOOK_URL").split(';'):
                webhook = DiscordWebhook(url=webhook_url)

                coin = float(listing["starting_price"])  / 1000000000000000000.0
                usd = float(listing["payment_token"]["usd_price"]) * coin
                kind = listing["asset"]['collection']["name"]
                description = listing['asset']['description'] or ""
                embed = DiscordEmbed(
                    title=listing["asset"]["name"],
                    url=listing["asset"]["permalink"],
                    description=f"{description}\n\n**A {kind} just got listed!**\n\n**Seller**: {listing['seller']['address']}\n**Price (BNB)**: {coin}{listing['payment_token']['symbol']}\n**Price (USD)**: ${usd}",
                    color="03b2f8",
                )

                embed.set_author(
                    name="NFT Listed",
                    url="https://opensea.io/",
                    icon_url="https://storage.googleapis.com/opensea-static/Logomark/Logomark-Blue.png",
                )

                embed.set_image(url=listing["asset"]["image_url"])

                webhook.add_embed(embed)

                response = webhook.execute()

                if response.status_code == 200:
                    listings_db.insert({"id": listing["id"]})
                    print(f"sent {listing['id']}")

            sleep(5)
