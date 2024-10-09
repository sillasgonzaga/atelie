from parsel import Selector
from typing import Dict
import httpx
import math
import json

def extract_search(response) -> Dict:
    """extract json data from search page"""
    sel = Selector(response.text)
    # find script with result.pagectore data in it.
    script_with_data = sel.xpath('//script[contains(.,"_init_data_=")]')
    print(script_with_data)
    # select page data from javascript variable in script tag using regex
    data = json.loads(script_with_data.re(r'_init_data_\s*=\s*{\s*data:\s*({.+}) }')[0])
    return data['data']['root']['fields']

def parse_search(response):
    """Parse search page response for product preview results"""
    data = extract_search(response)
    parsed = []
    for result in data["mods"]["itemList"]["content"]:
        parsed.append(
            {
                "id": result["productId"],
                "url": f"https://www.aliexpress.com/item/{result['productId']}.html",
                "type": result["productType"],  # can be either natural or ad
                "title": result["title"]["displayTitle"],
                "price": result["prices"]["salePrice"]["minPrice"],
                "currency": result["prices"]["salePrice"]["currencyCode"],
                "trade": result.get("trade", {}).get("tradeDesc"),  # trade line is not always present
                "thumbnail": result["image"]["imgUrl"].lstrip("/"),
                "store": {
                    "url": result["store"]["storeUrl"],
                    "name": result["store"]["storeName"],
                    "id": result["store"]["storeId"],
                    "ali_id": result["store"]["aliMemberId"],
                },
            }
        )
    return parsed

def scrape_search_page(query: str, page: int, sort_type="default"):
    """Scrape a single aliexpress search page and return all embedded JSON search data"""
    print(f"scraping search query {query}:{page} sorted by {sort_type}")
    url = (
        "https://www.aliexpress.com/wholesale?trafficChannel=main"
        f"&d=y&CatId=0&SearchText={query}&ltype=wholesale&SortType={sort_type}&page={page}"
    )
    response = httpx.get(url)
    return response

def scrape_search(query: str, sort_type="default", max_pages: int = None):
    """Scrape all search results and return parsed search result data"""
    query = query.replace(" ", "+")

    # scrape first search page and find total result count
    first_page = scrape_search_page(query, 1, sort_type)
    first_page_data = extract_search(first_page)
    page_size = first_page_data["pageInfo"]["pageSize"]
    total_pages = int(math.ceil(first_page_data["pageInfo"]["totalResults"] / page_size))
    if total_pages > 60:
        print(f"query has {total_pages}; lowering to max allowed 60 pages")
        total_pages = 60

    # get the number of total pages to scrape
    if max_pages and max_pages < total_pages:
        total_pages = max_pages

    # scrape remaining pages
    print(f'scraping search "{query}" of total {total_pages} sorted by {sort_type}')

    product_previews = []
    for i in range(1, total_pages + 1):
        response = scrape_search_page(query, i, sort_type)
        product_previews.extend(parse_search(response))

    return product_previews


def main():
    # Create an HTTPX asynchronous client
    query = 'laptop'
    # Call the scrape_search function with the query and client
    results = scrape_search(query=query, sort_type="default", max_pages=2)
    # Print the results
    for result in results:
        print(result)

# Run the main function
if __name__ == "__main__":
    main()
