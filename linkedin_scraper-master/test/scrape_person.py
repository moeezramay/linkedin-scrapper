import os, time, random, csv
from datetime import datetime
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


CSV_PATH = "companies.csv"

# --- load company URLs ---
with open(CSV_PATH, newline="", encoding="utf-8") as f:
    COMPANIES = [row[0].strip().rstrip("/") for row in csv.reader(f) if row and row[0].strip()]
if not COMPANIES:
    raise RuntimeError(f"{CSV_PATH} is empty or malformed")

# --- browser setup ---
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
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
        time.sleep(random.uniform(0.5, 1.0))
        btn.click()
        return True
    except Exception:
        return False

def scrape_people_links(driver, company_url):
    people_url = company_url + "/people/"
    driver.get(people_url)
    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CSS_SELECTOR, "main")))

    seen, last, stagnant = set(), 0, 0
    while stagnant < 3:
        before = len(seen)
        collect_links(driver, seen)

        clicked = click_show_more_if_any(driver)
        if not clicked:
            driver.execute_script("window.scrollBy(0, document.body.scrollHeight);")
            time.sleep(random.uniform(1.0, 1.7))

        collect_links(driver, seen)
        print(f"[LOOP] {company_url} | links={len(seen)}")

        if len(seen) == last:
            stagnant += 1
        else:
            last, stagnant = len(seen), 0

    return sorted(seen)

ts = datetime.now().strftime("%Y%m%d_%H%M%S")
master_outfile = f"employees_all_{ts}.csv"

try:
    # --- login once ---
    driver.get("https://www.linkedin.com/login")
    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.NAME, "session_key")))
    driver.find_element(By.NAME, "session_key").send_keys(EMAIL)
    driver.find_element(By.NAME, "session_password").send_keys(PASSWORD)
    driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
    WebDriverWait(driver, 30).until(EC.any_of(
        EC.url_contains("/feed"),
        EC.presence_of_element_located((By.CSS_SELECTOR, 'img.global-nav__me-photo'))
    ))

    # --- write one CSV with grouped sections ---
    with open(master_outfile, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        # optional header (kept simple):
        w.writerow(["company_or_blank", "profile_url"])
        for idx, url in enumerate(COMPANIES, 1):
            print(f"\n[COMPANY {idx}/{len(COMPANIES)}] {url}")
            links = scrape_people_links(driver, url)

            # group: company URL row, then its profiles, then a blank separator
            w.writerow([url, ""])
            for href in links:
                w.writerow(["", href])
            w.writerow(["", ""])  # separator blank line

            print(f"[RESULT] {url} -> {len(links)} profiles")
            time.sleep(random.uniform(2.0, 3.5))

    print(f"\n[MASTER] Wrote grouped results to {master_outfile}")

except Exception as e:
    print("[ERROR]", repr(e))
finally:
    try:
        driver.quit()
    except Exception:
        pass




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
