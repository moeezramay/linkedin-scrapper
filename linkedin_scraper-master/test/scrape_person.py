import os, time, random, sys
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import csv
from datetime import datetime  # <-- added

URL = "https://www.linkedin.com/company/codexon-edu/"

def ping(driver, label):
    try:
        driver.execute_script("return 1")
        svc_alive = getattr(driver, "service", None)
        svc_ok = (hasattr(svc_alive, "is_connectable") and svc_alive.is_connectable())
        print(f"[PING] {label} | session={driver.session_id} | svc_connectable={svc_ok} | url={driver.current_url}")
    except Exception as e:
        print(f"[PING-FAIL] {label}: {repr(e)}")

options = uc.ChromeOptions()
options.add_argument("--lang=en-US")
driver = uc.Chrome(options=options)

try:
    print("[STEP] open login")
    driver.get("https://www.linkedin.com/login")
    ping(driver, "login page loaded")

    print("[STEP] submit creds")
    driver.find_element(By.NAME, "session_key").send_keys("")
    driver.find_element(By.NAME, "session_password").send_keys("")
    driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
    WebDriverWait(driver, 30).until(EC.any_of(
        EC.url_contains("/feed"),
        EC.presence_of_element_located((By.CSS_SELECTOR, 'img.global-nav__me-photo'))
    ))
    ping(driver, "post-login")

    print("[STEP] go company people")
    people_url = URL.rstrip("/") + "/people/"
    driver.get(people_url)
    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CSS_SELECTOR, "main")))
    ping(driver, "people main present")

    print("[STEP] collect links")
    seen = set()
    last = 0
    stagnant = 0

    def collect():
        anchors = driver.find_elements(By.CSS_SELECTOR, 'a[href*="/in/"]')
        for a in anchors:
            href = (a.get_attribute("href") or "").split("?")[0]
            if "/in/" in href:
                seen.add(href)

    while stagnant < 3:
        before = len(seen)
        collect()

        # Try clicking "Show more results" if available
        clicked = False
        try:
            btn = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, 'button.scaffold-finite-scroll__load-button:not([disabled])')
                )
            )
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
            time.sleep(random.uniform(0.5, 1.0))
            btn.click()
            clicked = True
            # wait for new items to load (count must increase)
            WebDriverWait(driver, 10).until(
                lambda d: len(d.find_elements(By.CSS_SELECTOR, 'a[href*="/in/"]')) > before
            )
        except Exception:
            pass # ignore, will scroll instead

        if not clicked:
            driver.execute_script("window.scrollBy(0, document.body.scrollHeight);")
            time.sleep(random.uniform(1.0, 1.7))

        collect()
        print(f"[LOOP] links={len(seen)}")

        if len(seen) == last:
            stagnant += 1
        else:
            last = len(seen)
            stagnant = 0

    # save in csv
    links = sorted(seen) 
    slug = URL.strip("/").split("/")[-1] or "company"
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    outfile = f"employees_{slug}_{ts}.csv"

    with open(outfile, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["profile_url"])
        for href in links:
            w.writerow([href])

    print(f"[RESULT] wrote {len(links)} rows to {outfile}")

except Exception as e:
    print("[ERROR] raised:", repr(e))
finally:
    print("[STEP] quitting driver explicitly")
    try:
        driver.quit()
        print("[OK] quit done")
    except Exception as e:
        print("[QUIT-ERROR]", repr(e))




#person = Person("https://www.linkedin.com/in/mattsnowden/", driver=driver)


#with open('person.csv', 'w', newline='', encoding='utf-8') as csvfile:
#    fieldnames = ['Name', 'About', 'Experiences', 'Educations', 'Interests', 'Accomplishments', 'Job Title']
#    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
#
#    writer.writeheader()
#    writer.writerow({
#        'Name': person.name,
#        'About': person.about,
#        'Experiences': person.experiences,
#        'Educations': person.educations,
#       'Interests': person.interests,
#        'Accomplishments': person.accomplishments,
#        'Job Title': person.job_title
#    })

#print("Data saved to person.csv")
