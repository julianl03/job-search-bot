import unittest
from selenium import webdriver
from bs4 import BeautifulSoup
import chromedriver_autoinstaller
import time
from selenium.webdriver.common.by import By
from datetime import datetime

TEST_URL = "" #eluta url

class TestJobFinder(unittest.TestCase):
	def test_find_jobs(self):
		"""
		Test if find_jobs() works
		"""

		bot = job_finder([""], TEST_URL, 1)
		source = bot.driver.page_source
		self.assertTrue(len(bot.find_jobs(source))>=1)

	def test_check_keywords(self):
		"""
		Test if check_keywords() works
		"""

		bot = job_finder(["testkeyword1", "testkeyword2"], TEST_URL, 1)
		self.assertTrue(bot.check_keywords("testkeyword1 ABCde1"))
		self.assertFalse(bot.check_keywords("Abcad1"))
		self.assertTrue(bot.check_keywords("testkeyword2 atestkeyword1"))
		bot.set_min_keyword_limit(3)
		bot.set_keywords(["intern", "Co-Op", "sofTwAre"])
		self.assertTrue(bot.check_keywords("CO-op Intern soFtWAREasdf"))

	def test_check_job_title(self):
		"""
		Test if check_job_title() works
		"""

		bot = job_finder(["intern", "Co-Op"], TEST_URL, 1)
		self.assertTrue(bot.check_job_title("testkeyword1 intern"))
		self.assertTrue(bot.check_job_title("tesadsfaCo-Opasdfas"))
		self.assertFalse(bot.check_job_title("asdflknasdlfnk"))

	def test_check_job_description(self):
		"""
		Test if check_job_description() works
		"""

		bot = job_finder(["intern", "Co-Op"], TEST_URL, 1)
		self.assertTrue(bot.check_job_description("testkeyword1 intern"))
		self.assertTrue(bot.check_job_description("tesadsfaCo-Opasdfas"))
		self.assertFalse(bot.check_job_description("asdflknasdlfnk"))


class job_finder(unittest.TestCase):

	def __init__(self, keywords, baseurl, keyword_min_limit=1, date=datetime.now()):
		"""
		Initialize the bot.
		"""

		chromedriver_autoinstaller.install()
		self.driver = webdriver.Chrome()
		self.driver.get(baseurl)
		self.jobs = []
		self.KEYWORDS = keywords
		self.KEYWORD_MIN_LIMIT = keyword_min_limit
		self.DATE = date

	def get_jobs_loop(self, page_count):
		"""
		Go through [page_count] number of pages to find listings matching the keywords being looked for.

		-page_count: # of pages to go through, type int
		"""

		for i in range(page_count):
			source = self.driver.page_source
			self.add_found_jobs(self.find_matching_jobs(source))
			time.sleep(5)
			
			try:
				next_button = self.driver.find_element(By.ID, "pager-next")
				self.driver.execute_script("arguments[0].scrollIntoView();", next_button)
			except Exception as e:
				print("ERROR FINDING NEXT PAGE")

				break
			time.sleep(2)

			self.driver.execute_script("arguments[0].click();", next_button)
			time.sleep(2)

		self.report_results()

	def find_matching_jobs(self, source_item):
		"""
		Find jobs on page(source_item), get job info, and filter out jobs that do not match the keywords.

		returns a list of lists containing the information of the jobs that match. [[JOB_TITLE, COMPANY_NAME, DESCRIPTION], ...]
		"""

		matching = self.filter_jobs(self.get_job_info(self.find_jobs(source_item)))

		return matching

	def find_jobs(self, source_item):
		"""
		Find the job postings on the current page(source_item).

		returns the jobs found
		"""

		source = source_item
		job_div = BeautifulSoup(source).find("div", {"id":"organic-jobs"})
		jobs = job_div.find_all("div", {"class":"organic-job"})

		return jobs

	def get_job_info(self, jobs):
		"""
		Gets information for all jobs found and returns it
		"""

		job_information = []

		for job in jobs:
			job_information.append(self.get_info(job))

		return job_information

	def filter_jobs(self, job_info):
		"""
		Filter out jobs not matching keywords.

		returns the jobs that matched.
		"""

		filtered_job_list = []

		for job in job_info:

			job_matches_keyword = False

			if self.check_job_title(job[0]):
				job_matches_keyword = True
			if self.check_job_description(job[2]):
				job_matches_keyword = True

			if job_matches_keyword:
				filtered_job_list.append(job)

		return filtered_job_list

	def check_job_title(self, title):
		"""
		Check if job title matches at least a single keyword.

		-returns a boolean
		"""

		return self.check_keywords(title, self.get_min_keyword_limit())

	def check_job_description(self, description):		
		"""
		Check if job description matches at least a single keyword.

		-returns a boolean
		"""

		return self.check_keywords(description, self.get_min_keyword_limit())

	def check_keywords(self, job_info, min_limit=1):
		"""
		Perform the keyword check. For every keyword found, increases a counter of matched keywords.

		If the counter is greater or equal to the minimum # of keywords needed (min_limit), returns True

		if less matched, returns False.

		-returns a boolean
		"""

		keywords_matching = 0

		for keyword in self.get_keywords():
			if keyword.lower() in job_info.lower():
				keywords_matching+=1

		if keywords_matching >= min_limit:
			return True

		return False

	def report_results(self):
		report_file = open(self.DATE.strftime("%Y-%m-%d")+" JOB REPORT.txt", "w+")

		for job in self.get_all_matching_jobs():
			job_info = """"""
			job_info+="JOB TITLE: "+job[0]+" AT "+job[1]+"\n\n" #JOB_TITLE AT COMPANY_NAME
			job_info+="DESCRIPTION: "+job[2]+"\n\n"
			report_file.write(job_info)

		report_file.close()

		print("WROTE REPORT TO FILE")


	def add_found_jobs(self, job_list):
		"""
		Add list of job info to self.jobs
		"""

		self.jobs = self.jobs+job_list

	def get_info(self, job):
		"""
		Get information about the job posting.
		The information being looked for is the job title, company name, and the job description.

		returns a list with string elements in form: [JOB_TITLE, COMPANY_NAME, JOB_DESCRIPTION]
		"""

		job_title = job.find("a", {"class":"lk-job-title"}).get("title")
		company = job.find("a", {"class":"employer"}).text
		description = job.find("span", {"class":"description"}).text
		print("TITLE: "+str(job_title),end="\n\n")
		print("COMPANY: "+str(company))
		print("DESCRIPTION: "+str(description))
		print("\n\n")
		return [job_title, company, description]

	def set_min_keyword_limit(self, new_limit):
		"""
		set new minimum keyword limit.
		"""

		self.KEYWORD_MIN_LIMIT = new_limit

	def get_min_keyword_limit(self):
		"""
		get minimum keyword limit
		
		-returns an int (the minimum keyword limit)
		"""

		return self.KEYWORD_MIN_LIMIT

	def set_keywords(self, new_keyword_list):
		"""
		set list of keywords being looked for.
		"""

		self.KEYWORDS = new_keyword_list

	def get_keywords(self):
		"""
		get list of keywords being looked for.

		-returns a list
		"""

		return self.KEYWORDS

	def get_all_matching_jobs(self):
		"""
		returns all jobs found that match.
		"""

		return self.jobs

def run_bot(config_file):
	config = open(config_file, "r")
	information = config.read().split(",")
	for item in information:
		item = item.strip()
	print("URL: "+information[0])
	print("MIN KEYWORD MATCH: "+information[1])
	print("LOOKING THROUGH "+information[2]+" PAGES.")
	print("KEYWORDS: ", end="")
	print(information[3:])
	bot = job_finder(information[3:], information[0], int(information[1]))
	bot.get_jobs_loop(int(information[2]))



run_bot("bot_config.txt") #config file information order: url, min keyword match, # of pages to look through, ... (keywords)

#call program in form: python jobsearchbot.py [url] [min keyword match #] [# of pages to search through] [any keywords to look for (seperate with a space)]
#bot = job_finder(["intern", "Co-Op", "software", "developer", "web-developer", "back-end", "front-end"], "eluta_url", 2)

#unittest.main()

	





