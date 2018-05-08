#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue May  8 14:10:46 2018

@author: laurarocha
"""


import pandas as pd
from bs4 import BeautifulSoup
import urllib
from slackclient import SlackClient
import seaborn as sns


url= 'https://www.indeed.com/jobs?q=statistics&l=Seattle,+WA&jt=fulltime&explvl=entry_level&sort=date&start=0&limit=60'

web_page = urllib.request.urlopen(url)
soup = BeautifulSoup(web_page, 'html.parser')

all_jobs = soup.find_all('div', class_ = 'row')

companies = [span.get_text().strip()
             for div in all_jobs
             for span in div.find_all(name = 'span', class_ = 'company')]

jobs_title = [a.get_text()
           for div in all_jobs
           for a in div.find_all(name = 'a', attrs = {'data-tn-element':'jobTitle'})]

locations = [span.get_text()
            for div in all_jobs
            for span in div.find_all(name = 'span', class_ = 'location')]

date_posted = [span.get_text()
                for div in all_jobs
                for span in div.find_all(name = 'span', class_ = 'date')]      
            
hyperlinks = [a['href']
                for div in all_jobs
                for a in div.find_all(name = 'a',  attrs = {'data-tn-element':'jobTitle'})]
        
hyperlinks = pd.DataFrame(hyperlinks)
hyperlinks.columns = ['link']

hyperlinks = hyperlinks.replace({'/rc/clk':'https://www.indeed.com/viewjob'}, regex = True)
hyperlinks = hyperlinks.replace({'/company':'https://www.indeed.com/cmp'}, regex = True)
hyperlinks.loc[hyperlinks['link'].str.contains("/pagead"),'link'] = 'https://www.indeed.com' + hyperlinks['link']

col_names = ['title', 'company', 'location', 'link', 'date_posted']
data = pd.concat([pd.DataFrame(jobs_title), pd.DataFrame(companies), pd.DataFrame(locations), hyperlinks, pd.DataFrame(date_posted)], 1)
data.columns = col_names

recent_posts = data.loc[(data['date_posted'] == 'Just posted') | (data['date_posted'] == 'Today')]

message = pd.DataFrame(':robot_face: '+recent_posts['title']+', '+recent_posts['company']+', '+recent_posts['location']+', '+recent_posts['link'])
message.columns = ['job_posts']

BOT_TOKEN = 'insert_your_token'

slack_client = SlackClient(BOT_TOKEN)


def list_channels():
    channels_call = slack_client.api_call("channels.list")
    if channels_call['ok']:
            channels_call = slack_client.api_call("channels.list")
            channels = channels_call['channels']
            channels_name_id = [[x['name'], x['id']] for x in channels]
            return channels_name_id
    return None

channels_name_id = list_channels()

channels_id = [x[1] for x in channels_name_id]

def post_message():
# send message to python:
    for i in message['job_posts']:  
        if slack_client.rtm_connect():
            slack_client.api_call("chat.postMessage", channel = channels_id[4], text = i)

post_message()