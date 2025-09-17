from linkedin_scraper import Person, actions
from selenium import webdriver
import csv
driver = webdriver.Chrome()

email = "moeez@codexon.pk"
password = "police15@SA"
actions.login(driver, email, password) # if email and password isnt given, it'll prompt in terminal
person = Person("https://www.linkedin.com/in/mattsnowden/", driver=driver)


with open('person.csv', 'w', newline='', encoding='utf-8') as csvfile:
    fieldnames = ['Name', 'About', 'Experiences', 'Educations', 'Interests', 'Accomplishments', 'Job Title']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

    writer.writeheader()
    writer.writerow({
        'Name': person.name,
        'About': person.about,
        'Experiences': person.experiences,
        'Educations': person.educations,
        'Interests': person.interests,
        'Accomplishments': person.accomplishments,
        'Job Title': person.job_title
    })

print("Data saved to person.csv")
