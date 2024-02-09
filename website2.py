import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
import csv

class website2:
    '''
    This is a constructor
    '''
    def __init__(self):
        self.url = "https://isd110.org"
        self.school_information = {}

    '''
    Main method to orchestrate the scraping process.
    It scrapes school data, constructs URLs for teacher pages,
    and then scrapes teacher information from those pages. 
    '''
    def main(self):
        school_data = self.scrape_schools_data()
        page_urls = {}
        with open('staff_info.csv', 'w') as file:
            file.truncate(0)
            csv_writer = csv.writer(file)
            csv_writer.writerow(['School Name','Address','State','Zip','First Name','Last Name', 'Title', 'Phone', 'Email'])
        for schoolName,schoolUrl in school_data.items():
            try:
                page_hrfs = self.scrape_adress_page_urls(schoolName,schoolUrl)
                page_urls[schoolName]=page_hrfs
            except Exception as ex:
                pass
        for self.school,urls in page_urls.items():
            teachers_data = self.scrape_teachers_data(urls)
            self.write_to_csv(teachers_data)

    """
    Scrapes school data from the website and returns it as a dictionary.
    Returns:
        dict: A dictionary containing school names as keys and their URLs as values.
    """

    def scrape_schools_data(self):
        school_data_dict ={}
        source = requests.get(self.url).text
        soup = BeautifulSoup(source,'lxml')
        navbar = soup.find('div',class_="bottom group")
        our_schools_section = navbar.find('a', string='Our Schools')
        if our_schools_section:
            our_schools_list = our_schools_section.find_next('ul', class_='menu level-1')
            if our_schools_list:
                for a in our_schools_list.find_all('a'):
                    school_data_dict[a.text.strip()]=a['href']
        return school_data_dict


    """
    Constructs URLs for teacher pages of a school and returns them as a list.
    Args:
        schoolName (str): The name of the school.
        school_url (str): The URL of the school's staff directory page.
    Returns:
        list: A list of URLs for teacher pages.
    """
    def scrape_adress_page_urls(self,schoolName,school_url):
        
        url = self.url+school_url+"/staff-directory"
        school_source = requests.get(url).text
        soup = BeautifulSoup(school_source,'lxml')
        address_paragraph = soup.find('p', class_='address').get_text(strip=True)
        address_lines = address_paragraph.split(' ')
        state, zip_code = address_lines[-2],(address_lines[-1]).split("D")[0]
        last_pagination_item = soup.find('li', class_='item last')
        last_href = last_pagination_item.find('a')['href']
        last_page_number = int(last_href.split('=')[-1])
        self.school_information[schoolName]={
            "adress":address_paragraph,
            "state":state,
            "zip":zip_code
        }
        page_hrefs = [f"{url}/?s=&page={i}" for i in range(0, last_page_number + 1)]
        return page_hrefs


    """
    Scrapes teacher information from a list of page URLs.
    Args:
        page_urls (list): A list of teachers data.
    Returns:
        list : A list of teachers information.
    """
    def scrape_teachers_data(self,page_urls):
        with ThreadPoolExecutor(max_workers=5) as executor:  # Adjust max_workers as needed
            results = executor.map(self.process_page, page_urls) 
        results = [result for sublist in results for result in sublist]

        return results


    '''
    This method writes the school data to CSV file
    '''
    def write_to_csv(self,results):
        with open('staff_info.csv', 'a', newline='') as csvfile:
            csv_writer = csv.writer(csvfile)
            for school, title, job_title, phone, email in results:
                first_name = title.split(",")[0].strip()
                last_name = title.split(",")[1].strip()
                csv_writer.writerow([school,self.school_information[school]['adress'],self.school_information[school]['state'],self.school_information[school]['zip'] ,first_name,last_name, job_title, phone, email])
    

    """
    Processes a page URL, scrapes teacher information from it, and returns the results.
    Args:
        page_url (str): The URL of the page to be processed.
    Returns:
        list: A list of tuples containing teacher information.
    """
    def process_page(self,page_url):
        try:
            html_code = requests.get(page_url).text
            soup = BeautifulSoup(html_code, 'html.parser')
            staff_teasers = soup.find_all(class_='node staff teaser')
            results = []
            for staff_teaser in staff_teasers:
                try:
                    title = staff_teaser.find(class_='title').text.strip()
                    job_title = staff_teaser.find(class_='field job-title').text.strip()
                    phone = staff_teaser.find(class_='field phone').find('a').text.strip()
                    email = staff_teaser.find(class_='field email').find('a').text.strip()
                    results.append((self.school,title, job_title, phone, email))
                except Exception as ex:
                    pass
            return results
        except Exception as ex:
            return []

if __name__ == "__main__":
    class_obj = website2()
    class_obj.main()


