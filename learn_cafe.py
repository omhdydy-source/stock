import time
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    try:
        browser = p.chromium.connect_over_cdp("http://localhost:9222")
        contexts = browser.contexts
        if contexts:
            context = contexts[0]
            pages = context.pages
            if pages:
                page = pages[0]
            else:
                page = context.new_page()
            
            print("Navigating to https://cafe.naver.com/infinitebuying/79251 ...")
            page.goto("https://cafe.naver.com/infinitebuying/79251")
            page.wait_for_timeout(4000)
            
            print(f"Current URL: {page.url} - Title: {page.title()}")
            
            # Extract content from article
            content = page.evaluate("""() => {
                let iframe = document.querySelector('#cafe_main');
                if (iframe) {
                    try {
                        return iframe.contentDocument.body.innerText;
                    } catch(e) {
                        return iframe.src;
                    }
                }
                let main = document.querySelector('.se-main-container') || document.querySelector('.article_viewer') || document.body;
                return main.innerText;
            }""")
            
            print("--- CAFE POST CONTENT START ---")
            print(content[:3000])
            print("--- CAFE POST CONTENT END ---")
            
            with open("C:/Users/omh/Desktop/stock/learned_cafe_post.txt", "w", encoding="utf-8") as f:
                f.write(content)
            print("Successfully saved post content to learned_cafe_post.txt")
        else:
            print("No browser contexts found via CDP.")
    except Exception as e:
        print(f"CDP connection error: {e}")
