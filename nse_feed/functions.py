import requests
from bs4 import BeautifulSoup
import pandas as pd
import threading
from datetime import datetime

class NSE:
    def __init__(self):
        # Initialize any required attributes

        # LEVERAGE==============================
        url = "https://zerodha.com/margin-calculator/Equity/"
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")
        table = soup.find("table", {"id": "table"})
        headers = ['Scrip', 'MIS Margin %', 'MIS Leverage', 'CO Margin %', 'CO Leverage']
        data = []
        for row in table.find_all("tr"):
            row_data = [td.text.strip() for td in row.find_all("td")]
            if row_data:
                data.append(row_data)
        self.leverage_df = pd.DataFrame(data, columns=headers)

        # Send Alert
        self.TOKEN = "6960290902:AAEb28bQe-z-4L8ajfe0n7rOtjfkSUmqM34"
        self.chat_id = "-1001698980944"
    
    def send_alert(self,msg):
        url = f"https://api.telegram.org/bot{self.TOKEN}/sendMessage?chat_id={self.chat_id}&text={msg}&parse_mode=Markdown"
        threading.Thread(target = requests.get(url))

    def get_symbols_list(self):
        # getting symbol list
        session = requests.Session()
        headers = {'User-Agent': 'Mozilla/5.0 (Linux; Android) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.109 Safari/537.36 CrKey/1.54.248666'}
        session.headers.update(headers)
        website_url = "https://www.nseindia.com/market-data/live-equity-market"
        response = session.get(website_url, timeout=30)

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            cookies = response.cookies.get_dict()
            
            # Use the access token and cookies in subsequent requests
            api_url = "https://www.nseindia.com/api/equity-stockIndices?index=NIFTY%20TOTAL%20MARKET"
            headers = {
                # 'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36',
                'User-Agent': 'Mozilla/5.0 (Linux; Android) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.109 Safari/537.36 CrKey/1.54.248666',
                'Referer': website_url,
            }
            session.headers.update(headers)
            session.cookies.update(cookies)
            
            # Make a GET request to the API endpoint with the saved access token and cookies
            response = session.get(api_url, timeout=5)

            # Check if the request was successful (status code 200)
            if response.status_code == 200:
                # Access the JSON response
                symbols = ((pd.DataFrame((response.json())['data'][1:]))['symbol'].tolist())
                # print(data['data'])
                return symbols
            else:
                self.send_alert(f"Failed to fetch data. Status code: { response.status_code}")
        else:
            print(f"Failed to access the website. Status code: {response.status_code}")

        # symbol List accessed----------------------------------------------------------------------------

    def get_leverage(self,tradingsymbol:str,order_type:str="MIS"):
        leverage = self.leverage_df[self.leverage_df["Scrip"]==tradingsymbol][f'{order_type} Leverage'].iloc[0]
        return leverage

    def get_equity_historical_expiry(symbol,start_year=2015,end_year = datetime.now().year):

        all_exp = []
        # Create a session object
        session = requests.Session()
        # Set headers required for accessing the website
        headers = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.109 Safari/537.36 CrKey/1.54.248666'
        }
        session.headers.update(headers)
        # Make a GET request to the website URL to obtain access tokens and cookies
        website_url = "https://www.nseindia.com/report-detail/fo_eq_security"
        response = session.get(website_url, timeout=5)
        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Extract the necessary access tokens and cookies from the response
            # access_token = response.cookies.get('access_token')
            cookies = response.cookies.get_dict()

            for year in range(start_year, end_year + 1):
                # Use the access token and cookies in subsequent requests
                api_url = f"https://www.nseindia.com/api/historical/foCPV/expireDts?instrument=OPTSTK&symbol={symbol}&year={year}"
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Linux; Android) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.109 Safari/537.36 CrKey/1.54.248666',
                    'Referer': website_url,
                }
                session.headers.update(headers)
                session.cookies.update(cookies)

                # Make a GET request to the API endpoint with the saved access token and cookies
                response = session.get(api_url, timeout=5)

                # Check if the request was successful (status code 200)
                if response.status_code == 200:
                    # Access the JSON response
                    data = response.json()
                    exp = data['expiresDts']
                    all_exp = all_exp + exp
                    # print(data['expiresDts'])
                else:
                    print(f"Failed to fetch data for {year}. Status code:", response.status_code)
        else:
            print("Failed to access the website. Status code:", response.status_code)
        
        return all_exp

    def get_index_historical_expiry(symbol,start_year = 2027,end_year = datetime.now().year,opt_or_fut = 'O'):
        all_exp = []
        # Create a session object
        session = requests.Session()
        # Set headers required for accessing the website
        headers = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.109 Safari/537.36 CrKey/1.54.248666'
        }
        session.headers.update(headers)
        # Make a GET request to the website URL to obtain access tokens and cookies
        website_url = "https://www.nseindia.com/report-detail/fo_eq_security"
        response = session.get(website_url, timeout=5)

        
        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Extract the necessary access tokens and cookies from the response
            # access_token = response.cookies.get('access_token')
            cookies = response.cookies.get_dict()

            for year in range(start_year, end_year + 1):
                # Use the access token and cookies in subsequent requests
                if opt_or_fut == 'O':
                    api_url = f"https://www.nseindia.com/api/historical/foCPV/expireDts?instrument=OPTIDX&symbol={symbol}&year={year}"
                else:
                    api_url = f"https://www.nseindia.com/api/historical/foCPV/expireDts?instrument=FUTIDX&symbol={symbol}&year={year}"
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Linux; Android) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.109 Safari/537.36 CrKey/1.54.248666',
                    'Referer': website_url,
                }
                session.headers.update(headers)
                session.cookies.update(cookies)

                # Make a GET request to the API endpoint with the saved access token and cookies
                response = session.get(api_url, timeout=5)

                # Check if the request was successful (status code 200)
                if response.status_code == 200:
                    # Access the JSON response
                    data = response.json()
                    exp = data['expiresDts']
                    all_exp = all_exp + exp
                    # print(data['expiresDts'])
                    
                else:
                    print(f"Failed to fetch data for {year}. Status code:", response.status_code)
            return all_exp
        else:
            print("Failed to access the website. Status code:", response.status_code)
        
    def update_preopen(self):
        # Create a session object
        session = requests.Session()

        # Set headers required for accessing the website
        headers = {'User-Agent': 'Mozilla/5.0 (Linux; Android) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.109 Safari/537.36 CrKey/1.54.248666'}
        # headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36'}
        session.headers.update(headers)

        # Make a GET request to the website URL to obtain access tokens and cookies
        website_url = "https://www.nseindia.com/market-data/pre-open-market-cm-and-emerge-market"
        
        response = session.get(website_url, timeout=30)
        

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Extract the necessary access tokens and cookies from the response
            # access_token = response.cookies.get('access_token')
            cookies = response.cookies.get_dict()
            
            # Use the access token and cookies in subsequent requests
            api_url = "https://www.nseindia.com/api/market-data-pre-open?key=ALL"
            headers = {
                # 'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36',
                'User-Agent': 'Mozilla/5.0 (Linux; Android) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.109 Safari/537.36 CrKey/1.54.248666',
                'Referer': website_url,
            }
            session.headers.update(headers)
            session.cookies.update(cookies)
            
            # Make a GET request to the API endpoint with the saved access token and cookies
            response = session.get(api_url, timeout=5)

            # Check if the request was successful (status code 200)
            if response.status_code == 200:
                # Access the JSON response
                data = response.json()
                # print(data['data'])
            else:
                self.send_alert(f"Failed to fetch data. Status code: { response.status_code}")
        else:
            print(f"Failed to access the website. Status code: {response.status_code}")


        try:
            # data processing
            from pprint import pprint as p
            import pandas as pd

            preopen = [item['detail']['preOpenMarket'] for item in data['data']]
            # preopen

            preopen_df = pd.DataFrame(preopen)
            # preopen_df

            metadata = [item['metadata'] for item in data['data']]
            # metadata

            metadata_df = pd.DataFrame(metadata)
            # metadata_df

            df_concat = (pd.concat([metadata_df, preopen_df], axis=1))
            df_concat = df_concat.loc[:,~df_concat.columns.duplicated()].copy()
            df_concat['date'] = (pd.to_datetime(df_concat['lastUpdateTime']))
            df_concat['date'] = df_concat['date'].dt.date
            # (df_concat.columns)
            df_concat = df_concat.drop(['chartTodayPath','identifier','IEP'],axis = 1)
            return df_concat

        except:
            self.send_alert('Preopen update failed...')
            return None

    def market_status(self):
        # Create a session object
        session = requests.Session()

        # Set headers required for accessing the website
        headers = {'User-Agent': 'Mozilla/5.0 (Linux; Android) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.109 Safari/537.36 CrKey/1.54.248666'}
        # headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36'}
        session.headers.update(headers)

        # NIFTY 500 -------------------------------------------------------------------------------NIFTY 500
        # Make a GET request to the website URL to obtain access tokens and cookies
        website_url = "https://www.nseindia.com/market-data/live-equity-market"
        response = session.get(website_url, timeout=30)
        
        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Extract the necessary access tokens and cookies from the response
            # access_token = response.cookies.get('access_token')
            cookies = response.cookies.get_dict()
            
            # Use the access token and cookies in subsequent requests
            api_url = "https://www.nseindia.com/api/equity-stockIndices?index=NIFTY500%20MULTICAP%2050%3A25%3A25"
            headers = {
                # 'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36',
                'User-Agent': 'Mozilla/5.0 (Linux; Android) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.109 Safari/537.36 CrKey/1.54.248666',
                'Referer': website_url,
            }
            session.headers.update(headers)
            session.cookies.update(cookies)
            
            # Make a GET request to the API endpoint with the saved access token and cookies
            response = session.get(api_url, timeout=5)

            # Check if the request was successful (status code 200)
            if response.status_code == 200:
                # Access the JSON response
                data = response.json()
                print(data['data'])
            else:
                self.send_alert(f"Failed to fetch data. Status code: { response.status_code}")
        else:
            print(f"Failed to access the website. Status code: {response.status_code}")

        # -------------------------------------------------------------------------------------------MICROCAP 250
        # Make a GET request to the website URL to obtain access tokens and cookies
        website_url = "https://www.nseindia.com/market-data/live-equity-market"
        response = session.get(website_url, timeout=30)
        
        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Extract the necessary access tokens and cookies from the response
            # access_token = response.cookies.get('access_token')
            cookies = response.cookies.get_dict()
            # Use the access token and cookies in subsequent requests
            api_url = "https://www.nseindia.com/api/equity-stockIndices?index=NIFTY%20MICROCAP%20250"
            headers = {
                # 'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36',
                'User-Agent': 'Mozilla/5.0 (Linux; Android) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.109 Safari/537.36 CrKey/1.54.248666',
                'Referer': website_url,
            }
            session.headers.update(headers)
            session.cookies.update(cookies)
            # Make a GET request to the API endpoint with the saved access token and cookies
            response = session.get(api_url, timeout=5)
            # Check if the request was successful (status code 200)
            if response.status_code == 200:
                # Access the JSON response
                data_microcap = response.json()
                # print(data['data'])
            else:
                self.send_alert(f"Failed to fetch data. Status code: { response.status_code}")
        else:
            print(f"Failed to access the website. Status code: {response.status_code}")



        try:
            # data processing
            from pprint import pprint as p
            import pandas as pd
            p(data)

            (data['data'][0:1])

            nifty500_meta = [item['meta'] for item in data['data'][1:]]
            nifty500_ffmc = (pd.DataFrame(data['data'][1:]))[['symbol','ffmc']]
            nifty250_microcap_meta = [item['meta'] for item in data_microcap['data'][1:]]


            nifty500_details = (pd.DataFrame(nifty500_meta))
            nifty500_details =nifty500_details[['symbol','companyName','industry','activeSeries','isFNOSec']]
            nifty500_details['Index'] = 'NIFTY 500'

            # Merge the two DataFrames on the 'symbol' column
            nifty500_details = pd.merge(nifty500_details, nifty500_ffmc, on='symbol', how='inner')

            niftymicrocap_details = (pd.DataFrame(nifty250_microcap_meta))[['symbol','companyName','industry','activeSeries','isFNOSec']]
            niftymicrocap_details['Index'] = "NIFTY MICROCAP 250"
            niftymicrocap_details_ffmc = (pd.DataFrame(data_microcap['data'][1:]))[['symbol','ffmc']]

            # Merge the two DataFrames on the 'symbol' column
            niftymicrocap_details = pd.merge(niftymicrocap_details, niftymicrocap_details_ffmc, on='symbol', how='inner')

            niftyTotal = (pd.concat([nifty500_details, niftymicrocap_details], axis=0))
            niftyTotal.industry.unique()
            return niftyTotal

        except:
            self.send_alert('Preopen update failed...')

    def delivery_vol_historical(self,start_year):
        symbols = self.get_symbols_list()

        # Create a session object
        session = requests.Session()
        headers = {'User-Agent': 'Mozilla/5.0 (Linux; Android) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.109 Safari/537.36 CrKey/1.54.248666'}
        session.headers.update(headers)

        # Make a GET request to the website URL to obtain access tokens and cookies
        website_url = "https://www.nseindia.com/report-detail/eq_security"
        response = session.get(website_url, timeout=30)

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Extract the necessary access tokens and cookies from the response
            # access_token = response.cookies.get('access_token')
            cookies = response.cookies.get_dict()
            # Use the access token and cookies in subsequent requests
            
            headers = {
                # 'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36',
                'User-Agent': 'Mozilla/5.0 (Linux; Android) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.109 Safari/537.36 CrKey/1.54.248666',
                'Referer': website_url,
            }
            session.headers.update(headers)
            session.cookies.update(cookies)

            start_year = 2015
            current_year = datetime.now().year
            
            symbol_data_dict = {}
            for symbol in symbols:
                symbol_data =[]
                # Loop through each year from start_year to the current year
                for year in range(start_year, current_year + 1):
                    # Get the current date
                    end_date = datetime(year, 12, 31).strftime("%d-%m-%Y")
                    start_date = datetime(year, 1, 1).strftime("%d-%m-%Y")

                    # Make a GET request to the API endpoint with the saved access token and cookies
                    api_url = f"https://www.nseindia.com/api/historical/securityArchives?from={start_date}&to={end_date}&symbol={symbol}&dataType=priceVolumeDeliverable&series=ALL"
                    response = session.get(api_url, timeout=5)
                    # Check if the request was successful (status code 200)
                    if response.status_code == 200:
                        # Access the JSON response
                        data = (response.json())['data']
                        symbol_data.append(data)
                    else:
                        self.send_alert(f"Failed to fetch data. Status code: { response.status_code}")
                symbol_data_dict[symbol] = symbol_data
                
                print(symbol, ' - ', len(symbol_data_dict[symbol]))

                
        else:
            print(f"Failed to access the website. Status code: {response.status_code}")

    def fpi_details(self):
        session = requests.Session()
        headers = {'User-Agent': 'Mozilla/5.0 (Linux; Android) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.109 Safari/537.36 CrKey/1.54.248666'}
        session.headers.update(headers)
        website_url = "https://www.fpi.nsdl.co.in/web/Reports/RegisteredFIISAFPI.aspx?srch=A&ty=1#"
        response = session.get(website_url, timeout=30)

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            cookies = response.cookies.get_dict()
            
            # Use the access token and cookies in subsequent requests
            api_url = "https://www.fpi.nsdl.co.in/web/Reports/RegisteredFIISAFPI.aspx?action=getregdata"
            headers = {
                # 'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36',
                'User-Agent': 'Mozilla/5.0 (Linux; Android) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.109 Safari/537.36 CrKey/1.54.248666',
                'Referer': website_url,
            }
            session.headers.update(headers)
            session.cookies.update(cookies)
            
            # Make a GET request to the API endpoint with the saved access token and cookies
            response = session.get(api_url, data = {'Search':"%",'Type':0}, timeout=5)

            # Check if the request was successful (status code 200)
            if response.status_code == 200:
                # Access the JSON response.text
                symbols = pd.DataFrame((response.json())['Table'])
                # print(data['data'])
                return symbols
            else:
                self.send_alert(f"Failed to fetch data. Status code: { response.status_code}")
        else:
            print(f"Failed to access the website. Status code: {response.status_code}")

    def get_abbreviation_from_full_month_name(full_month_name):
        date_object = datetime.strptime(full_month_name, "%B")
        abbreviation = date_object.strftime("%b")
        return abbreviation

    def fortnightly_data_historical(self):
        final_data_dict = {}
        import calendar
        import numpy as np
        from bs4 import BeautifulSoup
        import time

        for year in range(2022, 2025):  # Adjust the end year as needed
            for month in range(1, 13):
                if year == 2022 and month < 6:
                    pass
                else:
                    # Get the number of days in the month
                    month_name = calendar.month_name[month]
                    num_days = calendar.monthrange(year, month)[1]
                    for date_ in [15,num_days]:
                        # URL of the website
                        url = f'https://www.cdslindia.com/publications/FII/FortnightlySecWisePages/{month_name}%20{date_},%20{year}.htm'
                        url2 = f'https://www.cdslindia.com/publications/FII/FortnightlySecWisePages/{month_name}%20{date_},{year}.htm'
                        url3 = f'https://www.fpi.nsdl.co.in/web/StaticReports/Fortnightly_Sector_wise_FII_Investment_Data/FIIInvestSector_{self.get_abbreviation_from_full_month_name(month_name)}{date_}{year}.html'
                        response = requests.get(url)
                        # response.text
                        if response.status_code != 200:
                            url = url2
                            response = requests.get(url)

                        if response.status_code == 200:
                            soup = BeautifulSoup(response.content)
                            # time.sleep(1)
                            table = soup.find('table')
                            row_data_list = []

                            a = 0
                            while a < 3:
                                if table:
                                    print('Table fetched...')
                                    break
                                else:
                                    print('retying to fetch table...')
                                    response = requests.get(url)
                                    soup = BeautifulSoup(response.text,'html.parser')
                                    # time.sleep(1)
                                    table = soup.find('table')
                                    a+=1

                            rows = []
                            if table:
                                rows = table.find_all('tr')
                                for row in rows:
                                    # Extract cell data from each row
                                    cells = row.find_all(['td', 'th'])
                                    row_data = [cell.text.strip() for cell in cells]
                                    row_data_list.append(row_data)

                                # Creating a DataFrame
                                row_data_df = pd.DataFrame(row_data_list[3:], columns=row_data_list[2])
                                # Find all occurrences of "Total" in the columns
                                total_columns = ['Total']
                                # Get the indices of "Total" columns
                                total_indices = [row_data_df.columns.get_loc(col) for col in total_columns]
                                total_indices_array = total_indices[0]
                                true_indices = np.where(total_indices_array)[0]
                                min_distance = min(np.diff(true_indices))
                                # row_data_df.columns
                                l1 = [item.replace('\r\n','').replace('\n',"").replace('    ','') for item in row_data_list[0] if item != ""]
                                l2 = list(set([item for item in row_data_list[1] if item != ""]))
                                i = 0
                                for l1_ in l1:
                                    final_data_dict[l1_] = {}  # Initialize an empty dictionary for each l1_

                                    for l2_ in l2:
                                        # Extracting the desired columns
                                        selected_columns = row_data_df.iloc[:, [1] + list(range(2+i, 2+i+min_distance))]
                                        # Creating a new DataFrame with the selected columns
                                        new_df = pd.DataFrame(selected_columns)
                                        final_data_dict[l1_][l2_] = new_df
                                        i += min_distance
                                # Print the month number and the number of days
                                print(f"{year}-{month_name}: {date_}")
                                
                            else:
                                print("Table not found on the webpage." ,f"{year}-{month_name}: {date_}")
                        else:
                            print(f"Failed to retrieve the webpage. Status code: {response.status_code}:  ", f"{year}-{month_name}: {date_}")

        final_df = pd.DataFrame()

        for key in final_data_dict.keys():
            df = final_data_dict[key]['IN INR Cr.']
            df['Date'] = key
            df_pivoted = df.pivot(index='Date', columns='Sectors', values='Total')
            df_pivoted.reset_index(inplace=True)

            final_df = pd.concat([final_df, df_pivoted], axis=0)

        final_df.to_csv('final_data.csv')


        # Filter rows containing AUC information
        auc_df = final_df[final_df['Date'].str.contains('AUC')]

        # Filter rows containing Net Investment information
        net_investment_df = final_df[final_df['Date'].str.contains('Net Investment')]

        return auc_df,net_investment_df

    def extract_data(self,html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        data = {}

        # Extracting data for FII/FPI investments
        investments_table = soup.find('h4', text='Daily Trends in FII / FPI Investments').find_next('table')
        investments_data = {}
        for row in investments_table.find_all('tr')[1:]:
            columns = row.find_all('td')
            if len(columns) > 1:
                date = columns[0].text.strip()
                investments_data[date] = {
                    'Equity': {
                        'Stock Exchange': {
                            'Gross Purchases (Rs Crore)': columns[3].text.strip(),
                            'Gross Sales (Rs Crore)': columns[4].text.strip(),
                            'Net Investment (Rs Crore)': columns[5].text.strip(),
                            'Net Investment (US$ million)': columns[6].text.strip()
                        },
                        'Primary market & others': {
                            'Gross Purchases (Rs Crore)': columns[7].text.strip(),
                            'Gross Sales (Rs Crore)': columns[8].text.strip(),
                            'Net Investment (Rs Crore)': columns[9].text.strip(),
                            'Net Investment (US$ million)': columns[10].text.strip()
                        }
                    },
                    'Debt': {
                        'Stock Exchange': {
                            'Gross Purchases (Rs Crore)': columns[12].text.strip(),
                            'Gross Sales (Rs Crore)': columns[13].text.strip(),
                            'Net Investment (Rs Crore)': columns[14].text.strip(),
                            'Net Investment (US$ million)': columns[15].text.strip()
                        },
                        'Primary market & others': {
                            'Gross Purchases (Rs Crore)': columns[16].text.strip(),
                            'Gross Sales (Rs Crore)': columns[17].text.strip(),
                            'Net Investment (Rs Crore)': columns[18].text.strip(),
                            'Net Investment (US$ million)': columns[19].text.strip()
                        }
                    },
                    'Debt-VRR': {
                        'Stock Exchange': {
                            'Gross Purchases (Rs Crore)': columns[21].text.strip(),
                            'Gross Sales (Rs Crore)': columns[22].text.strip(),
                            'Net Investment (Rs Crore)': columns[23].text.strip(),
                            'Net Investment (US$ million)': columns[24].text.strip()
                        },
                        'Primary market & others': {
                            'Gross Purchases (Rs Crore)': columns[25].text.strip(),
                            'Gross Sales (Rs Crore)': columns[26].text.strip(),
                            'Net Investment (Rs Crore)': columns[27].text.strip(),
                            'Net Investment (US$ million)': columns[28].text.strip()
                        }
                    },
                    'Hybrid': {
                        'Stock Exchange': {
                            'Gross Purchases (Rs Crore)': columns[30].text.strip(),
                            'Gross Sales (Rs Crore)': columns[31].text.strip(),
                            'Net Investment (Rs Crore)': columns[32].text.strip(),
                            'Net Investment (US$ million)': columns[33].text.strip()
                        },
                        'Primary market & others': {
                            'Gross Purchases (Rs Crore)': columns[34].text.strip(),
                            'Gross Sales (Rs Crore)': columns[35].text.strip(),
                            'Net Investment (Rs Crore)': columns[36].text.strip(),
                            'Net Investment (US$ million)': columns[37].text.strip()
                        }
                    },
                    'Total': {
                        'Gross Purchases (Rs Crore)': columns[39].text.strip(),
                        'Gross Sales (Rs Crore)': columns[40].text.strip(),
                        'Net Investment (Rs Crore)': columns[41].text.strip(),
                        'Net Investment (US$ million)': columns[42].text.strip()
                    }
                }

        data['FII_FPI_Investments'] = investments_data

        # Extracting data for FII/FPI derivative trades
        derivatives_table = soup.find('h4', text='Daily Trends in FII / FPI Derivative Trades').find_next('table')
        derivatives_data = {}
        for row in derivatives_table.find_all('tr')[2:]:
            columns = row.find_all('td')
            if len(columns) > 1:
                date = columns[0].text.strip()
                derivatives_data[date] = {
                    'INDEX_FUTURES': {
                        'Buy': {
                            'No. of Contracts': columns[2].text.strip(),
                            'Amount in Crore': columns[3].text.strip()
                        },
                        'Sell': {
                            'No. of Contracts': columns[4].text.strip(),
                            'Amount in Crore': columns[5].text.strip()
                        },
                        'Open Interest at the end of the date': {
                            'No. of Contracts': columns[6].text.strip(),
                            'Amount in Crore': columns[7].text.strip()
                        }
                    },
                    'INDEX_OPTIONS': {
                        'Buy': {
                            'No. of Contracts': columns[9].text.strip(),
                            'Amount in Crore': columns[10].text.strip()
                        },
                        'Sell': {
                            'No. of Contracts': columns[11].text.strip(),
                            'Amount in Crore': columns[12].text.strip()
                        },
                        'Open Interest at the end of the date': {
                            'No. of Contracts': columns[13].text.strip(),
                            'Amount in Crore': columns[14].text.strip()
                        }
                    },
                    'STOCK_FUTURES': {
                        'Buy': {
                            'No. of Contracts': columns[16].text.strip(),
                            'Amount in Crore': columns[17].text.strip()
                        },
                        'Sell': {
                            'No. of Contracts': columns[18].text.strip(),
                            'Amount in Crore': columns[19].text.strip()
                        },
                        'Open Interest at the end of the date': {
                            'No. of Contracts': columns[20].text.strip(),
                            'Amount in Crore': columns[21].text.strip()
                        }
                    },
                    'STOCK_OPTIONS': {
                        'Buy': {
                            'No. of Contracts': columns[23].text.strip(),
                            'Amount in Crore': columns[24].text.strip()
                        },
                        'Sell': {
                            'No. of Contracts': columns[25].text.strip(),
                            'Amount in Crore': columns[26].text.strip()
                        },
                        'Open Interest at the end of the date': {
                            'No. of Contracts': columns[27].text.strip(),
                            'Amount in Crore': columns[28].text.strip()
                        }
                    },
                    'INTEREST_RATE_FUTURES': {
                        'Buy': {
                            'No. of Contracts': columns[30].text.strip(),
                            'Amount in Crore': columns[31].text.strip()
                        },
                        'Sell': {
                            'No. of Contracts': columns[32].text.strip(),
                            'Amount in Crore': columns[33].text.strip()
                        },
                        'Open Interest at the end of the date': {
                            'No. of Contracts': columns[34].text.strip(),
                            'Amount in Crore': columns[35].text.strip()
                        }
                    }
                }

        data['FII_FPI_Derivative_Trades'] = derivatives_data

        return data

    def fii_dii_data_latest(self):
        url = 'https://www.cdslindia.com/Publications/FIIDailyData.aspx'

        # Sending a GET request to the URL
        response = requests.get(url)

        # Checking if the request was successful (status code 200)
        if response.status_code == 200:
            # Extracting data and structuring it into a nested dictionary
            extracted_data = self.extract_data(response.content)
            print(extracted_data)
        else:
            print('Failed to retrieve data. Status code:', response.status_code)

      