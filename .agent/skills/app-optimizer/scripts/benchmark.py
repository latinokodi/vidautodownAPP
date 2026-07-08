import asyncio
import sys
import argparse
from datetime import datetime

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("❌ Playwright is required. Run: pip install playwright && playwright install")
    sys.exit(1)

async def run_benchmark(url):
    print(f"--- ⏱️ Performance Delta Module: Benchmarking {url} ---")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Track payloads
        total_bytes = 0
        def handle_response(response):
            nonlocal total_bytes
            # Rough estimate of payload size via headers
            if 'content-length' in response.headers:
                total_bytes += int(response.headers['content-length'])
                
        page.on("response", handle_response)
        
        start_time = datetime.now()
        await page.goto(url, wait_until="networkidle")
        end_time = datetime.now()
        
        load_time = (end_time - start_time).total_seconds()
        
        # Get Performance API metrics
        timing = await page.evaluate("JSON.stringify(window.performance.timing)")
        
        print("\n📊 [EMPIRICAL PERFORMANCE REPORT]")
        print(f"URL: {url}")
        print(f"Network Idle Time: {load_time:.2f} seconds")
        print(f"Estimated Network Payload: {total_bytes / 1024:.2f} KB")
        print("\nNote: Run this before and after optimization to calculate the Delta.")
        
        await browser.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Benchmark web page performance")
    parser.add_argument("url", help="URL to benchmark (e.g., http://localhost:3000)")
    args = parser.parse_args()
    
    asyncio.run(run_benchmark(args.url))
