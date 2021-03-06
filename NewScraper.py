#!/usr/bin/env python
# coding: utf-8

# In[1]:


from bs4 import BeautifulSoup
import requests
import datetime #as dt
from datetime import date 
from datetime import datetime
import pandas as pd 
import re 
import numpy as np
import sys
import warnings
from datetime import timedelta
if not sys.warnoptions:
    warnings.simplefilter("ignore")
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
import time 
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.action_chains import ActionChains
from sympy.solvers import solve
from sympy import Symbol
import mysql.connector
import sqlalchemy
from mysql.connector import Error


# In[2]:


def load_exists(driver):
    try:
        WebDriverWait(driver,10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "button.Button.SportsBoxAll.LoadMore")))
        return True
    except:
        return False

def cookies(driver):
    try:
        driver.find_element_by_xpath('//*[@id="app"]/div/span[2]/div/button')
        return True
    except:
        return False       
        
def click_through(x):
    if load_exists(x):
        if cookies(x):
            pisso= x.find_element_by_xpath('//*[@id="app"]/div/span[2]/div/button')
            ActionChains(x).move_to_element(pisso).click().perform()
            element= x.find_element_by_css_selector("button.Button.SportsBoxAll.LoadMore")
            ActionChains(x).move_to_element(element).click().perform()
            click_through(x)
        else:
            element= x.find_element_by_css_selector("button.Button.SportsBoxAll.LoadMore")
            ActionChains(x).move_to_element(element).click().perform()
            click_through(x)
    return x

def get_links(browse):
    rows= []
    for thing in BeautifulSoup(browse.page_source,'lxml').find_all('li',{'class':'Match'}):
        try:
            if thing.find('a',{'class':'MatchTitleLink'}): 
                dict1= {}
                match_link= 'https://www.betbrain.de' + thing.find('a', {'class':'MatchTitleLink'})['href']
                date= pd.to_datetime(thing.find('span', {'class':'DateTime'}).text) 
                dict1.update({'match_link':match_link,'date':date})
                rows.append(dict1)
        except:
            continue
    df= pd.DataFrame(rows)
    df=df[df['match_link'].str.contains("home-draw-away")& df['match_link'].str.contains("football")].reset_index(drop= True)
    return df

chrome_path= r'C:\Users\Iris\Documents\Nico\NicoUni\Practicum\Python\Projects\WebDrivers\chromedriver.exe'
chrome_options = Options()
chrome_options.add_argument('--headless')
browser = webdriver.Chrome(
executable_path=chrome_path, options=chrome_options)
browser.get('https://www.betbrain.de/next-matches/')

doc= click_through(browser)

links= get_links(doc)


# In[11]:


def xpath_exists(text,driver):
    try:
        WebDriverWait(driver,10).until(EC.presence_of_element_located((By.XPATH,text)))
        return True
    except:
        return False

def get_odds(URL,playtime):
    chrome_path= r'C:\Users\Iris\Documents\Nico\NicoUni\Practicum\Python\Projects\WebDrivers\chromedriver.exe'
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    browser = webdriver.Chrome(executable_path=chrome_path, options=chrome_options)
    browser.get(URL)
    if xpath_exists("//*[contains(text(), 'Pinnacle Sports')]",browser):
        if xpath_exists('//*[@id="app"]/div/span/div/button',browser):
            element= browser.find_element_by_xpath('//*[@id="app"]/div/span/div/button')
            ActionChains(browser).move_to_element(element).click().perform()
        
        country= browser.find_element_by_xpath('/html/body/div[1]/div/section/div/div/div/div[2]/div/div[1]/ul/li[4]/a/span[1]').text
        league= browser.find_element_by_xpath('/html/body/div[1]/div/section/div/div/div/div[2]/div/div[1]/ul/li[5]/a/span[1]').text
        html_page= browser.page_source
        browser.quit()
        soup= BeautifulSoup(html_page)
        date= playtime + timedelta(hours= 2)
        home_team= soup.find('p',{'class':'ScoresHome'}).findAll('span')[1].text
        away_team= soup.find('p',{'class':'ScoresAway'}).findAll('span')[1].text
        scrape_time= pd.to_datetime(datetime.now())
        bookie_list= []
        
        for thing in soup.findAll('div', {'class':'OTBookmakers'}):#
            for element in thing.findAll('span', {'class':'BookieLogo BL'}):
                bookie_list.append(element.find('span').text)
                
        outcome= ['H','D','A']   
        exclude= ['Betfair Exchange','Betfair']

        bookie_cols= [x.replace(' ','')+y for x in bookie_list for y in outcome if x not in exclude]
        odds= []
        
        for element in soup.findAll('a',{'class':['OTOddsLink', 'HasDeeplink']}):
            odds.append(element.next_element.text[:-2])
                        
        if any(x in exclude for x in bookie_list):
            exchange= True
        else:
            exchange= False
                    
        if exchange:
            values= [home_team, away_team, date,scrape_time,country,league]+odds[:-12]
        else:
            values= [home_team, away_team, date,scrape_time,country,league]+odds
        
        keys= ['home_team','away_team','date','scrape_time','country','league']+bookie_cols
            
        zipper= zip(keys, values)
        match_dict= dict(zipper)
    else:
        match_dict= {}
    
    return match_dict


# In[44]:


matches= []

def append_matches(URLS):
    global matches
    for i in range(0,len(URLS)):
        try:
            matches.append(get_odds(URLS['match_link'][i], URLS['date'][i]))
        except:
            continue
            
now= pd.to_datetime(datetime.now()+timedelta(hours= 6.5))

links['date']= pd.to_datetime(links['date'].dt.strftime("%Y-%d-%m %H:%M:%S"), format= "%Y-%m-%d %H:%M:%S")

links= links.query("date <=@now").reset_index(drop= True)
append_matches(links)


# In[46]:


def is_number(x):
    try:
        float(x)
        return True
    except ValueError:
        return False
    
data= pd.DataFrame(matches)

data['time_lag']= np.round((data['date']-data['scrape_time']).dt.total_seconds()/60,2)

time_lag= data.pop('time_lag')
data.insert(4, 'time_lag', time_lag)

bookies= data.iloc[:,7:].columns
homes= [x for x in bookies if x.endswith('H')]
draws= [x for x in bookies if x.endswith('D')]
aways= [x for x in bookies if x.endswith('A')]

for names,col in data[homes+draws+aways].iteritems():
    if any(is_number(x)== False for x in col):
        data[names]= [x if is_number(x) else None for x in col]

data[homes+draws+aways]= data[homes+draws+aways].astype('float16')

data['maxOddsH']= data[homes].max(axis=1)
data['maxOddsD']= data[draws].max(axis=1)
data['maxOddsA']= data[aways].max(axis=1)

data['maxBookieH']= data[homes].idxmax(axis=1)
data['maxBookieD']= data[draws].idxmax(axis=1)
data['maxBookieA']= data[aways].idxmax(axis=1)


# In[47]:


def add_margins(probability, max_odds):
    x= probability*(max_odds-1)-(1-probability)
    return(x)

#This is for Pinnacle 

cols= list(data.iloc[:,:7].columns)+['PinnacleSportsH','PinnacleSportsD','PinnacleSportsA','maxOddsH','maxOddsD','maxOddsA','maxBookieH', 'maxBookieD','maxBookieA']
# equal margins 
try:
    pinnacle= data[cols]
    
    test1= pinnacle.dropna(subset= ['PinnacleSportsH'])
    test1['overround']= (1/test1['PinnacleSportsH']+1/test1['PinnacleSportsD']+1/test1['PinnacleSportsA'])-1
    test1['ProbsPinnacleH-1']= 1/test1['PinnacleSportsH']/(1+test1['overround'])
    test1['ProbsPinnacleD-1']= 1/test1['PinnacleSportsD']/(1+test1['overround'])
    test1['ProbsPinnacleA-1']= 1/test1['PinnacleSportsA']/(1+test1['overround'])

    test1['marginH-1']= test1['ProbsPinnacleH-1']*(test1['maxOddsH']-1)-(1-test1['ProbsPinnacleH-1'])
    test1['marginD-1']= test1['ProbsPinnacleD-1']*(test1['maxOddsD']-1)-(1-test1['ProbsPinnacleD-1'])
    test1['marginA-1']= test1['ProbsPinnacleA-1']*(test1['maxOddsA']-1)-(1-test1['ProbsPinnacleA-1'])

#margins proportional to odds 

    test2= pinnacle.dropna(subset= ['PinnacleSportsH']) 
    test2['overround']= (1/test1['PinnacleSportsH']+1/test1['PinnacleSportsD']+1/test1['PinnacleSportsA'])-1
    test2['ProbsPinnacleH-2']= 1/((3*test2['PinnacleSportsH'])/(3-(test2['overround']*test2['PinnacleSportsH'])))
    test2['ProbsPinnacleD-2']= 1/((3*test2['PinnacleSportsD'])/(3-(test2['overround']*test2['PinnacleSportsD'])))
    test2['ProbsPinnacleA-2']= 1/((3*test2['PinnacleSportsA'])/(3-(test2['overround']*test2['PinnacleSportsA'])))
    
    test2['marginH-2']= test2['ProbsPinnacleH-2']*(test2['maxOddsH']-1)-(1-test2['ProbsPinnacleH-2'])
    test2['marginD-2']= test2['ProbsPinnacleD-2']*(test2['maxOddsD']-1)-(1-test2['ProbsPinnacleD-2'])
    test2['marginA-2']= test2['ProbsPinnacleA-2']*(test2['maxOddsA']-1)-(1-test2['ProbsPinnacleA-2'])
    
    #test3= 
except:
    test1= pd.DataFrame()
    test2= pd.DataFrame()


# #### Consensus group 

# In[48]:


probs_homes= ['Probs'+x for x in bookies if x.endswith('H')]
probs_draws= ['Probs'+x for x in bookies if x.endswith('D')]
probs_aways= ['Probs'+x for x in bookies if x.endswith('A')]

cons_test1= data 
# equal margins

for odds in range(0, len(bookies),3):
    overround= 1/cons_test1[bookies[odds]]+1/cons_test1[bookies[odds+1]]+1/cons_test1[bookies[odds+2]]
    cons_test1['Probs'+bookies[odds]]= (1/cons_test1[bookies[odds]]/overround)
    cons_test1['Probs'+bookies[odds+1]]= (1/cons_test1[bookies[odds+1]]/overround)
    cons_test1['Probs'+bookies[odds+2]]= (1/cons_test1[bookies[odds+2]]/overround)
    
cons_test1['consProbsH-3']= cons_test1[probs_homes].mean(axis= 1)
cons_test1['consProbsD-3']= cons_test1[probs_draws].mean(axis= 1)
cons_test1['consProbsA-3']= cons_test1[probs_aways].mean(axis= 1)
       
cons_test1['marginH-3']= add_margins(cons_test1['consProbsH-3'],cons_test1['maxOddsH'])
cons_test1['marginD-3']= add_margins(cons_test1['consProbsD-3'],cons_test1['maxOddsD'])
cons_test1['marginA-3']= add_margins(cons_test1['consProbsA-3'],cons_test1['maxOddsA'])

#proportional margins 

cons_test2= data 

for odd in range(0, len(bookies),3):
    overround= (1/cons_test2[bookies[odd]]+1/cons_test2[bookies[odd+1]]+1/cons_test2[bookies[odd+2]])-1   
    cons_test2['Probs'+bookies[odd]]= 1/((3*cons_test2[bookies[odd]])/(3-(overround*cons_test2[bookies[odd]])))
    cons_test2['Probs'+bookies[odd+1]]= 1/((3*cons_test2[bookies[odd+1]])/(3-overround*cons_test2[bookies[odd+1]]))
    cons_test2['Probs'+bookies[odd+2]]= 1/((3*cons_test2[bookies[odd+2]])/(3-(overround*cons_test2[bookies[odd+2]])))
        
                                                         
cons_test2['consProbsH-4']= cons_test2[probs_homes].mean(axis= 1)
cons_test2['consProbsD-4']= cons_test2[probs_draws].mean(axis= 1)
cons_test2['consProbsA-4']= cons_test2[probs_aways].mean(axis= 1)

cons_test2['marginH-4']= add_margins(cons_test2['consProbsH-4'],cons_test2['maxOddsH'])
cons_test2['marginD-4']= add_margins(cons_test2['consProbsD-4'],cons_test2['maxOddsD'])
cons_test2['marginA-4']= add_margins(cons_test2['consProbsA-4'],cons_test2['maxOddsA']) 

test3= cons_test1[['home_team','away_team','date','scrape_time','time_lag','country','league','maxOddsH','maxOddsD','maxOddsA','maxBookieH','maxBookieD','maxBookieA','consProbsH-3','consProbsD-3','consProbsA-3',
'marginH-3','marginD-3', 'marginA-3']]

test4= cons_test2[['home_team','away_team','date','scrape_time','time_lag','country','league','maxOddsH','maxOddsD','maxOddsA','maxBookieH','maxBookieD','maxBookieA','consProbsH-4','consProbsD-4','consProbsA-4',
'marginH-4','marginD-4', 'marginA-4']]


# In[49]:


def save_it(df,tablename, dbname):
    db_username= "root"
    db_password= '4kS8GdBm!'
    db_ip= "localhost"
    db_name= dbname
    
    db_connection = sqlalchemy.create_engine('mysql+mysqlconnector://{0}:{1}@{2}/{3}'.
                                               format(db_username, db_password, 
                                                      db_ip, db_name))    
    try:
        
        df.to_sql(tablename,db_connection,if_exists= 'append', index= False)
        print('successfully appended table')
        
    except:
        
        data = pd.read_sql('SELECT * FROM {sql_table}'.format(sql_table= tablename), db_connection)
        print('failed to add column')
        df2 = pd.concat([data,df])
        df2.to_sql(tablename,db_connection,if_exists= 'replace', index= False)
        print('successfully replaced table')
        
        
save_it(data, 'fixtures', 'betbrain')
save_it(test1, 'test_group1', 'betbrain')
save_it(test2, 'test_group2', 'betbrain')
save_it(test3, 'test_group3', 'betbrain')
save_it(test4, 'test_group4', 'betbrain')


# In[ ]:




