from linkedin_scraper import Person, actions, Company
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import os

# Set up Chrome options to use your specific Profile 4
chrome_options = Options()
chrome_options.add_argument("--user-data-dir=C:\\Users\\moeez\\AppData\\Local\\Google\\Chrome\\User Data")
chrome_options.add_argument("--profile-directory=Profile 4")

# Optional: Add these to make the browser less detectable as automation
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
chrome_options.add_experimental_option('useAutomationExtension', False)

driver = webdriver.Chrome(options=chrome_options)

email = os.getenv("LINKEDIN_USER")
password = os.getenv("LINKEDIN_PASSWORD")
actions.login(driver, email, password) 

company = Company("https://ca.linkedin.com/company/google")
print(company.employees)



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
