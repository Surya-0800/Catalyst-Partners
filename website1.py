import requests,json
from bs4 import BeautifulSoup 
import re,os
import json
from concurrent.futures import ThreadPoolExecutor

class website1:

    '''
    This method is responsible for getting cookies and total number of bids that are present in website
    '''
    def get_cookies(self):
        response = requests.get('https://nevadaepro.com/bso/view/search/external/advancedSearchBid.xhtml?openBids=true')
        soup = BeautifulSoup(response.text,'lxml')
        pagination = soup.find('span',class_="ui-paginator-current")
        records = pagination.text.split(" ")[-1]
        self.cookies = response.cookies.get_dict()

        return records

    '''
    This method gets the URLS for each Bid and store it in a list
    '''

    def get_record_urls(self,records):

        data = {
            'javax.faces.partial.ajax': 'true',
            'javax.faces.source': 'bidSearchResultsForm:bidResultId',
            'javax.faces.partial.execute': 'bidSearchResultsForm:bidResultId',
            'javax.faces.partial.render': 'bidSearchResultsForm:bidResultId',
            'bidSearchResultsForm:bidResultId': 'bidSearchResultsForm:bidResultId',
            'bidSearchResultsForm:bidResultId_pagination': 'true',
            'bidSearchResultsForm:bidResultId_first': '0',
            'bidSearchResultsForm:bidResultId_rows': records,
            'bidSearchResultsForm:bidResultId_encodeFeature': 'true',
            'bidSearchResultsForm': 'bidSearchResultsForm',
            '_csrf': self.cookies['XSRF-TOKEN'],
            'openBids': 'true',
        }

        self.headers = {
            'authority': 'nevadaepro.com',
            'accept': 'application/xml, text/xml, */*; q=0.01',
            'accept-language': 'en-US,en;q=0.9',
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'faces-request': 'partial/ajax',
            'origin': 'https://nevadaepro.com',
            'referer': 'https://nevadaepro.com/bso/view/search/external/advancedSearchBid.xhtml?openBids=true',
            'sec-ch-ua': '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'x-requested-with': 'XMLHttpRequest',
        }

        response = requests.post(
            'https://nevadaepro.com/bso/view/search/external/advancedSearchBid.xhtml',
            cookies=self.cookies,
            headers=self.headers,
            data=data,
        )
        soup = BeautifulSoup(response.text,features="xml")
        html_data = soup.find('update').text
        html_soup = BeautifulSoup(html_data, 'html.parser')
        hrefs = html_soup.find_all('a')
        links = []
        for a in hrefs:
            href_value = a.get('href')
            if not "purchaseorder" in href_value and "parentUrl=close" in href_value:
                links.append(href_value)

        return links,self.headers['origin']


    '''
    This method downloads all the files that are present in each record and store it in a folder with the name Bid Number
    '''
    def download_file(self,url, data, bid_number, text, cookies, headers):
        response = requests.post(url, cookies=cookies, headers=headers, data=data)
        if response.status_code == 200:
            cwd = os.getcwd()
            directory_path = os.path.join(cwd, str(bid_number))
            os.makedirs(directory_path, exist_ok=True)
            file_path = os.path.join(directory_path, f"{text}.{'docx' if text.endswith('.docx') else 'pdf'}")
            with open(file_path, 'wb') as f:
                f.write(response.content)
            return file_path

    '''
    This method scrape the whole data regarding for the Bid and store it in dictionary 
    '''
    def get_bid_data(self, links, web_url):
        response_data = {}
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            for link in links:
                data_dict = {}
                updated_dict = {}
                file_data = []
                url = web_url + link
                res = requests.get(url)
                soup = BeautifulSoup(res.text, 'html.parser')
                table = soup.find('table', class_="table-01")
                table_data = table.find_all('td', class_='t-head-01')
                for td_head in table_data:
                    key = td_head.get_text(strip=True)
                    value_td = td_head.find_next_sibling('td')
                    if value_td:
                        value = value_td.get_text(strip=True)
                        data_dict[key] = value

                for key, values in data_dict.items():
                    updated_key = key.replace(":", " ").replace("\n", "").strip()
                    updated_value = values.strip()
                    updated_dict[updated_key] = updated_value
                    if updated_key == "Bill-to Address":
                        break
                
                response_data[updated_dict['Bid Number']] = updated_dict
                urls = table.find_all('a', class_="link-01")
                filtered_data = [(url['href'], url.text) for url in urls if 'javascript:downloadFile' in url['href']]
                pattern = r"javascript:downloadFile\('(\d+)'\)"
                for url, text in filtered_data:
                    match = re.search(pattern, url)
                    if match:
                        file_id = match.group(1)
                        data = {
                            '_csrf': self.cookies['XSRF-TOKEN'],
                            'mode': 'download',
                            'bidId': updated_dict['Bid Number'],
                            'docId': updated_dict['Bid Number'],
                            'currentPage': '1',
                            'querySql': '',
                            'downloadFileNbr': file_id,
                            'itemNbr': 'undefined',
                            'parentUrl': f'close/{file_id}',
                            'fromQuote': '',
                            'destination': '',
                        }
                        futures.append(executor.submit(self.download_file, 'https://nevadaepro.com/bso/external/bidDetail.sdo', data, updated_dict['Bid Number'], text, self.cookies, self.headers))

            for future in futures:
                future.result()

        with open("output.json", "w") as f:
            json.dump(response_data, f)

        

if __name__ == "__main__":
    class_obj = website1()
    records=class_obj.get_cookies()
    link,website = class_obj.get_record_urls(records)
    class_obj.get_bid_data(link,website)















     