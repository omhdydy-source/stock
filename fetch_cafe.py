import time
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    user_data_dir = "C:/Users/omh/AppData/Local/Temp/PlaywrightNaverProfile"
    browser = p.chromium.launch_persistent_context(
        user_data_dir=user_data_dir,
        headless=False,
        args=["--start-maximized"]
    )
    page = browser.new_page()
    
    print("Navigating to Naver Login page...")
    page.goto("https://nid.naver.com/nidlogin.login")
    
    print("⏳ Please log in to Naver in the opened browser window.")
    print("Waiting up to 120 seconds for login completion...")
    
    logged_in = False
    for i in range(24):
        time.sleep(5)
        url = page.url
        print(f"Current URL: {url}")
        if "nidlogin" not in url and "naver.com" in url:
            print("Login detected!")
            logged_in = True
            break
            
    if logged_in:
        print("Navigating to target Naver Cafe post: 79251...")
        page.goto("https://cafe.naver.com/infinitebuying/79251")
        page.wait_for_timeout(5000)
        
        try:
            # Extract content from article
            content = page.evaluate("""() => {
                let body = document.querySelector('#cafe_main') ? document.querySelector('#cafe_main').contentDocument.body : (document.querySelector('.se-main-container') || document.body);
                return body.innerText;
            }""")
            print("--- EXTRACTED POST CONTENT START ---")
            print(content[:4000])
            print("--- EXTRACTED POST CONTENT END ---")
            
            with open("C:/Users/omh/Desktop/stock/cafe_post_79251_content.txt", "w", encoding="utf-8") as f:
                f.write(content)
            print("Successfully saved post content to cafe_post_79251_content.txt")
        except Exception as e:
            print(f"Extraction error: {e}")
            # Save outer HTML for debugging
            with open("C:/Users/omh/Desktop/stock/page_debug.html", "w", encoding="utf-8") as f:
                f.write(page.content())
    else:
        print("Login timed out.")

    print("Keeping browser open for 10 seconds...")
    time.sleep(10)
    browser.close()
