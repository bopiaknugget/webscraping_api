import requests
from bs4 import BeautifulSoup
import json
from fastapi import FastAPI, HTTPException
from typing import Optional
import logging
from pydantic import BaseModel
import asyncio

# Initialize FastAPI app
app = FastAPI(
    title="Web Scraping API",
    description="API for scraping websites with flexible configuration"
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ScrapingRequest(BaseModel):
    url: str
    selector: Optional[str] = None
    attributes: Optional[list] = None
    headers: Optional[dict] = None

class Scraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    async def scrape(self, request: ScrapingRequest):
        try:
            # Make the request
            response = self.session.get(
                request.url,
                headers=request.headers if request.headers else {}
            )
            response.raise_for_status()

            # Parse the HTML
            soup = BeautifulSoup(response.text, 'html.parser')

            # If no selector is provided, return the full HTML
            if not request.selector:
                return {"html": str(soup)}

            # Find elements matching the selector
            elements = soup.select(request.selector)
            
            result = []
            for element in elements:
                if request.attributes:
                    # Extract specified attributes
                    data = {attr: element.get(attr, '') for attr in request.attributes}
                    data['text'] = element.get_text(strip=True)
                    result.append(data)
                else:
                    # Return text content if no attributes specified
                    result.append(element.get_text(strip=True))

            return {"results": result}

        except requests.RequestException as e:
            logger.error(f"Request error: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"Scraping error: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

# Initialize scraper
scraper = Scraper()

@app.post("/scrape")
async def scrape_endpoint(request: ScrapingRequest):
    """
    Endpoint to scrape websites based on provided configuration
    
    Parameters:
    - url: Target website URL
    - selector (optional): CSS selector to target specific elements
    - attributes (optional): List of HTML attributes to extract
    - headers (optional): Custom headers for the request
    """
    return await scraper.scrape(request)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
   