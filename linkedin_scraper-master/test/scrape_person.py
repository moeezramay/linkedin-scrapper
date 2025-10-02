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

def load_done(path=DONE_PATH):
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return {line.strip().rstrip("/") for line in f if line.strip()}
    return set()

with open(CSV_PATH, newline="", encoding="utf-8") as f:
    ALL_COMPANIES = [row[0].strip().rstrip("/") for row in csv.reader(f) if row and row[0].strip()]

DONE = load_done()
COMPANIES = [u for u in ALL_COMPANIES if u not in DONE]
if not COMPANIES:
    sys.exit(0)

options = uc.ChromeOptions()
options.add_argument("--lang=en-US")
driver = uc.Chrome(options=options)

def _safe_write(writer, f, row):
    writer.writerow(row)
    f.flush(); os.fsync(f.fileno())

def try_click_show_more(driver, before_count, wait_s=12):
    btn = None
    for b in driver.find_elements(By.CSS_SELECTOR, 'button.scaffold-finite-scroll__load-button')[::-1]:
        try:
            if b.is_displayed() and b.is_enabled() and b.get_attribute("aria-disabled") != "true":
                btn = b; break
        except StaleElementReferenceException:
            continue
    if not btn:
        return False
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
    time.sleep(random.uniform(0.4, 0.9))
    try:
        driver.execute_script("arguments[0].click()", btn)
    except Exception:
        try: btn.click()
        except Exception: return False
    try:
        WebDriverWait(driver, wait_s).until(
            lambda d: len(d.find_elements(By.CSS_SELECTOR, 'a[href*="/in/"]')) > before_count or
                      not any(bb.is_displayed() and bb.is_enabled()
                              for bb in d.find_elements(By.CSS_SELECTOR, 'button.scaffold-finite-scroll__load-button'))
        )
    except Exception:
        return False
    return len(driver.find_elements(By.CSS_SELECTOR, 'a[href*="/in/"]')) > before_count

def scrape_and_stream(driver, company_url, writer, f_csv): 
    people_url = company_url if '/people/' in company_url else company_url.rstrip('/') + '/people/'
    driver.get(people_url)
    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CSS_SELECTOR, "main")))
    wrote_header = False
    seen, last, stagnant = set(), 0, 0
    while stagnant < 3:
        before = len(seen)
        for a in driver.find_elements(By.CSS_SELECTOR, 'a[href*="/in/"]'):
            href = (a.get_attribute("href") or "").split("?")[0]
            if "/in/" in href and href not in seen:
                seen.add(href)
                if not wrote_header:
                    _safe_write(writer, f_csv, [company_url, ""])
                    wrote_header = True
                _safe_write(writer, f_csv, ["", href])
        grew = try_click_show_more(driver, before)
        if not grew:
            driver.execute_script("window.scrollBy(0, document.body.scrollHeight);")
            time.sleep(random.uniform(1.0, 1.7))
        stagnant = stagnant + 1 if len(seen) == last else 0
        last = len(seen)
    if wrote_header:
        _safe_write(writer, f_csv, ["", ""])  # section separator

try:
    driver.get("https://www.linkedin.com/login")
    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.NAME, "session_key")))
    driver.find_element(By.NAME, "session_key").send_keys(EMAIL)
    driver.find_element(By.NAME, "session_password").send_keys(PASSWORD)
    driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
    WebDriverWait(driver, 30).until(EC.any_of(
        EC.url_contains("/feed"),
        EC.presence_of_element_located((By.CSS_SELECTOR, 'img.global-nav__me-photo'))
    ))
    file_exists = os.path.exists(MASTER_OUTFILE)
    with open(MASTER_OUTFILE, "a", newline="", encoding="utf-8") as f_csv:
        w = csv.writer(f_csv)
        if not file_exists:
            _safe_write(w, f_csv, ["company_or_blank", "profile_url"])
        for url in COMPANIES:
            scrape_and_stream(driver, url, w, f_csv)
            with open(DONE_PATH, "a", encoding="utf-8") as f_done:
                f_done.write(url.rstrip("/") + "\n")
                f_done.flush(); os.fsync(f_done.fileno())
except Exception as e:
    pass
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
