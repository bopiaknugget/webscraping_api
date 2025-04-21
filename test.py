import requests
import json
import os

# Create the request payload
request_data = {
    "url": "https://www.dia.co.th/articles/what-is-artificial-intelligence/",
    "selector": "article",  # Target the main article content
    "attributes": ["class"]  # Get class attributes and text content
}

# Send POST request to the scraper endpoint
response = requests.post("http://localhost:8000/scrape", json=request_data)

# Check if request was successful
if response.status_code == 200:
    # Get the results
    results = response.json()
    
   
    # Verify file exists and print absolute path
    
    file_path = os.path.abspath("result.txt")
    # Write results to file
    with open(file_path, 'w') as f:
        json.dump(results, f, indent=4)
    
    if os.path.exists(file_path):
        print(f"Results saved to: {file_path}")
    else:
        print("Warning: File was not created successfully")
else:
    print(f"Error: {response.status_code}")
    print(response.text)
