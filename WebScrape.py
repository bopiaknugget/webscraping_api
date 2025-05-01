import aiohttp
from bs4 import BeautifulSoup
import json
from fastapi import FastAPI, HTTPException
from typing import Optional, List, Dict, Any
import logging
from pydantic import BaseModel
import asyncio
from aiohttp import ClientTimeout, ClientResponseError
from tenacity import retry, stop_after_attempt, wait_exponential

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
    attributes: Optional[List[str]] = None
    headers: Optional[Dict[str, str]] = None
    timeout: Optional[int] = 30
    follow_redirects: Optional[bool] = True

class ScrapingResponse(BaseModel):
    success: bool
    data: Dict[str, Any]
    error: Optional[str] = None
    status_code: Optional[int] = None
    message: Optional[str] = None

class Scraper:
    def __init__(self):
        self.default_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }
        self.timeout = ClientTimeout(total=30)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def scrape(self, request: ScrapingRequest) -> ScrapingResponse:
        try:
            headers = {**self.default_headers, **(request.headers or {})}
            timeout = ClientTimeout(total=request.timeout or 30)

            async with aiohttp.ClientSession(headers=headers, timeout=timeout) as session:
                async with session.get(
                    request.url,
                    allow_redirects=request.follow_redirects
                ) as response:
                    status_code = response.status
                    
                    if status_code != 200:
                        return ScrapingResponse(
                            success=False,
                            data={},
                            error=f"HTTP Error: {status_code}",
                            status_code=status_code,
                            message=f"Server returned status code {status_code}"
                        )

                    html = await response.text()
                    if not html.strip():
                        return ScrapingResponse(
                            success=False,
                            data={},
                            error="Empty response from server",
                            status_code=status_code,
                            message="Received empty HTML content"
                        )

            try:
                soup = BeautifulSoup(html, 'html.parser')
            except Exception as e:
                return ScrapingResponse(
                    success=False,
                    data={},
                    error="HTML parsing failed",
                    status_code=status_code,
                    message=f"Failed to parse HTML: {str(e)}"
                )

            if not request.selector:
                return ScrapingResponse(
                    success=True,
                    data={"html": str(soup)},
                    status_code=status_code
                )

            elements = soup.select(request.selector)
            if not elements:
                return ScrapingResponse(
                    success=True,
                    data={"results": []},
                    status_code=status_code,
                    message="No elements found matching the selector"
                )
            
            results = []
            for element in elements:
                try:
                    if request.attributes:
                        data = {attr: element.get(attr, '') for attr in request.attributes}
                        data['text'] = element.get_text(strip=True)
                        results.append(data)
                    else:
                        results.append(element.get_text(strip=True))
                except Exception as e:
                    logger.warning(f"Error processing element: {str(e)}")
                    continue

            if not results:
                return ScrapingResponse(
                    success=True,
                    data={"results": []},
                    status_code=status_code,
                    message="No valid data extracted from elements"
                )

            return ScrapingResponse(
                success=True,
                data={"results": results},
                status_code=status_code
            )

        except aiohttp.ClientError as e:
            logger.error(f"Request error: {str(e)}")
            return ScrapingResponse(
                success=False,
                data={},
                error=f"Request failed: {str(e)}",
                message="Network request failed"
            )
        except Exception as e:
            logger.error(f"Scraping error: {str(e)}")
            return ScrapingResponse(
                success=False,
                data={},
                error=f"Scraping failed: {str(e)}",
                message="Unexpected error during scraping"
            )

# Initialize scraper
scraper = Scraper()

@app.post("/scrape", response_model=ScrapingResponse)
async def scrape_endpoint(request: ScrapingRequest):
    """
    Endpoint to scrape websites based on provided configuration
    
    Parameters:
    - url: Target website URL
    - selector (optional): CSS selector to target specific elements
    - attributes (optional): List of HTML attributes to extract
    - headers (optional): Custom headers for the request
    - timeout (optional): Request timeout in seconds (default: 30)
    - follow_redirects (optional): Whether to follow redirects (default: True)
    """
    return await scraper.scrape(request)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
   
