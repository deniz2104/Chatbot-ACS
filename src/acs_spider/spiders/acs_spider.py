import scrapy
from src.acs_spider.items import AcsPageItem


class AcsSpider(scrapy.Spider):
    name = "acs"
    allowed_domains = ["acs.pub.ro"]
    start_urls = ["https://acs.pub.ro"]

    def parse(self, response):
        print(f"\n[5. SPIDER] Got response: {response.status} from {response.url}")
        print(f"[5. SPIDER]   Response size: {len(response.body)} bytes")

        item = AcsPageItem()
        item["url"] = response.url
        item["title"] = response.css("title::text").get()
        item["headings"] = response.css("h1::text, h2::text, h3::text").getall()
        item["links"] = []

        for link in response.css("a[href]"):
            href = link.attrib.get("href", "")
            text = link.css("::text").get() or ""
            if href and not href.startswith("#"):
                item["links"].append({
                    "text": text.strip(),
                    "href": response.urljoin(href),
                })

        print(f"[5. SPIDER]   Title: {item['title']}")
        print(f"[5. SPIDER]   Headings found: {len(item['headings'])}")
        print(f"[5. SPIDER]   Links found: {len(item['links'])}")
        print(f"\n[6. YIELD] Yielding AcsPageItem -> sent to Item Pipeline")

        yield item
