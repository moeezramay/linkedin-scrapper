import os, time, random, csv, sys
from datetime import datetime
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException



CSV_PATH = "companies.csv"
MASTER_OUTFILE = "companies_employees_scraped.csv"

DONE_PATH = "already_scrapped_companies.txt"


# function fix to properly handle "show more results" button

def try_click_show_more(driver, before_count, wait_s=12):

    meraButton = None
    for b in driver.find_elements(By.CSS_SELECTOR, 'button.scaffold-finite-scroll__load-button')[::-1]:
        try:
            if b.is_displayed() and b.is_enabled() and b.get_attribute("aria-disabled") != "true":
                meraButton = b; break
        except StaleElementReferenceException:
            continue
    if not meraButton:
        return False

    # bring into view and click (JS fallback is more reliable)
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", meraButton)
    time.sleep(random.uniform(0.4, 0.9))
    try:
        driver.execute_script("arguments[0].click()", meraButton)
    except Exception:
        try: meraButton.click()
        except Exception: return False

    # wait for new items OR the button to go away/disable
    try:
        WebDriverWait(driver, wait_s).until(
            lambda d: len(d.find_elements(By.CSS_SELECTOR, 'a[href*="/in/"]')) > before_count or
                      not any(bb.is_displayed() and bb.is_enabled()
                              for bb in d.find_elements(By.CSS_SELECTOR, 'button.scaffold-finite-scroll__load-button'))
        )
    except Exception:
        return False

    return len(driver.find_elements(By.CSS_SELECTOR, 'a[href*="/in/"]')) > before_count




# load already done companies
def load_done(path=DONE_PATH):
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return {line.strip().rstrip("/") for line in f if line.strip()}
    return set()

# load companies
with open(CSV_PATH, newline="", encoding="utf-8") as f:
    ALL_COMPANIES = [row[0].strip().rstrip("/") for row in csv.reader(f) if row and row[0].strip()]

# filtering out already done
DONE = load_done()
COMPANIES = [u for u in ALL_COMPANIES if u not in DONE]
print(f"[INIT] {len(COMPANIES)} pending, {len(DONE)} already done")

# exit if nothing to do
if not COMPANIES:
    print("[INIT] No pending companies. Exiting.")
    sys.exit(0)

options = uc.ChromeOptions()
options.add_argument("--lang=en-US")
driver = uc.Chrome(options=options)

def collect_links(driver, bag):
    for a in driver.find_elements(By.CSS_SELECTOR, 'a[href*="/in/"]'):
        href = (a.get_attribute("href") or "").split("?")[0]
        if "/in/" in href:
            bag.add(href)

def click_show_more_if_any(driver):
    try:
        btn = WebDriverWait(driver, 3).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.scaffold-finite-scroll__load-button:not([disabled])'))
        )
        driver.execute_script("arguments[0].scrollIntoView({block:""center""});", btn)
        time.sleep(random.uniform(0.5, 1.0))
        btn.click()
        return True
    except Exception:
        return False

def scrape_people_links(driver, company_url):
    
    #Incase of direct links for geographic location like getting people from USA
    if '/people/' in company_url:
        people_url = company_url
    else:
        people_url = company_url.rstrip("/") + "/people/"
    driver.get(people_url)
    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CSS_SELECTOR, "main")))

    seen, last, stagnant = set(), 0, 0

    while stagnant < 3:
        before = len(seen)  # save current count
        collect_links(driver, seen)  

        # Try to click "Show more results" if available
        grew = try_click_show_more(driver, before)

        if not grew:  # scroll manually if prev didnt grow
            driver.execute_script("window.scrollBy(0, document.body.scrollHeight);")
            time.sleep(random.uniform(1.0, 1.7))

        collect_links(driver, seen)  # collect after scroll

        print(f"[LOOP] {company_url} | links={len(seen)}")

        if len(seen) == last:
            stagnant += 1  # no change in links, increase stagnant 
        else:
            last, stagnant = len(seen), 0  # reset stagnant count on growth

    return sorted(seen)

try:
    # login once
    driver.get("https://www.linkedin.com/login")
    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.NAME, "session_key")))
    driver.find_element(By.NAME, "session_key").send_keys(EMAIL)
    driver.find_element(By.NAME, "session_password").send_keys(PASSWORD)
    driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
    WebDriverWait(driver, 30).until(EC.any_of(
        EC.url_contains("/feed"),
        EC.presence_of_element_located((By.CSS_SELECTOR, 'img.global-nav__me-photo'))
    ))

    # open (append) and write header only if file didn't exist
    file_exists = os.path.exists(MASTER_OUTFILE)
    with open(MASTER_OUTFILE, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if not file_exists:
            w.writerow(["company_or_blank", "profile_url"])

        for idx, url in enumerate(COMPANIES, 1):
            print(f"\n[COMPANY {idx}/{len(COMPANIES)}] {url}")
            links = scrape_people_links(driver, url)

            # section header (company URL), then its profiles, then a blank line
            w.writerow([url, ""])
            for href in links:
                w.writerow(["", href])
            w.writerow(["", ""])

            with open(DONE_PATH, "a", encoding="utf-8") as f_done:
                f_done.write(url.rstrip("/") + "\n")

            print(f"[RESULT] {url} -> {len(links)} profiles")
            time.sleep(random.uniform(2.0, 3.5))

            print(f"[RESULT] {url} -> {len(links)} profiles")
            time.sleep(random.uniform(2.0, 3.5))

    print(f"\n[MASTER] Updated {MASTER_OUTFILE}")

except Exception as e:
    print("[ERROR]", repr(e))
finally:
    try: driver.quit()
    except: pass




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
