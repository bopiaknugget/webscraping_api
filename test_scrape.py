import requests
import json

url = "http://localhost:8000/scrape"
data = {
    "url": "https://www.dia.co.th/articles/what-is-artificial-intelligence/",
    "selector": "article",  # This will select the main article content
    "attributes": ["class", "id"]
}

response = requests.post(url, json=data)
print(json.dumps(response.json(), indent=2, ensure_ascii=False)) 