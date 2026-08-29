import time
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    try:
        browser = p.chromium.connect_over_cdp("http://localhost:9222")
        for ctx in browser.contexts:
            for page in ctx.pages:
                if "79263" in page.url or "일반모드" in page.title():
                    print(f"Found target page: {page.url} - {page.title()}")
                    content = page.evaluate("""() => {
                        let iframe = document.querySelector('#cafe_main');
                        if (iframe) {
                            try { return iframe.contentDocument.body.innerText; } catch(e) {}
                        }
                        let main = document.querySelector('.se-main-container') || document.querySelector('.article_viewer') || document.body;
                        return main.innerText;
                    }""")
                    print("--- POST 79263 CONTENT START ---")
                    print(content[:4000])
                    print("--- POST 79263 CONTENT END ---")
                    
                    with open("C:/Users/omh/Desktop/stock/cafe_post_79263.txt", "w", encoding="utf-8") as f:
                        f.write(content)
                    break
    except Exception as e:
        print(f"Error: {e}")
