# Slackbot to send notifications about new job postings

This project was designed to develop web scraping and bot knowledge. From 'www.indeed.com' website, 'Statistics' jobs data get extracted using web scraping in Python. The goal of this example is to build a bot in Slack that will send me new job postings everyday based on examples of  job interests. Also basic exploratory analysis is performed on the data to help visualize and understand information about the posted jobs.

Requirements:

- Have a Slack account
- Python 3.6.4 :: Anaconda, Inc.

### Extract the data and build the dataset

Fetch the html content from the web page URL. For this case, the URL is from Indeed's website link with the filters: statistics, seattle, 50miles radius, full-time and entry-level position, sorted by date, and limit search to 60 (to make sure all new postings get extracted).

```
from bs4 import BeautifulSoup
import urllib

url = 'https://www.indeed.com/jobs?q=statistics&l=Seattle,+WA&radius=50&jt=fulltime&explvl=entry_level&sort=date&start=0&limit=60'

web_page = urllib.request.urlopen(url)
soup = BeautifulSoup(web_page, 'html.parser')
```
The following code perform the scraping from the parsed html stored in the 'soup' variable. Five main information that interests me to be notified gets extracted: company name, job title (position), job location, job posting date and link to the job post.

```
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
```

When scraping the hyperlinks, the entire URL path is not returned. Using RegEx, the code fixes this issue.

```
import pandas as pd

hyperlinks = pd.DataFrame(hyperlinks)
hyperlinks.columns = ['link']

hyperlinks = hyperlinks.replace({'/rc/clk':'https://www.indeed.com/viewjob'}, regex = True)
hyperlinks = hyperlinks.replace({'/company':'https://www.indeed.com/cmp'}, regex = True)
hyperlinks.loc[hyperlinks['link'].str.contains("/pagead"),'link'] = 'https://www.indeed.com' + hyperlinks['link']
```

The next step is to store the extracted information into a Dataframe with 'pandas' package.

```
col_names = ['title', 'company', 'location', 'link', 'date_posted']
data = pd.concat([pd.DataFrame(jobs_title), pd.DataFrame(companies), pd.DataFrame(locations), hyperlinks, pd.DataFrame(date_posted)], 1)
data.columns = col_names
```
The information gets filtered based on the 'date_posted' column. Since I get notified once a day, the rows (job postings) that I want to be notified about are the ones labeled as 'Just posted' and 'Today'.

```
recent_posts = data.loc[(data['date_posted'] == 'Just posted') | (data['date_posted'] == 'Today')]
```

The message that will get sent through Slack is formatted including 4 information about the job post ('date_posted' is not included since we use that only to filter the data).

```
message = pd.DataFrame(':robot_face: '+recent_posts['title']+', '+recent_posts['company']+', '+recent_posts['location']+', '+recent_posts['link'])
message.columns = ['job_posts']
```

### Slack connection/send message

The next step is to send the messages to Slack. A Slack account is needed for this step and an Application has to be created (bot application). Detailed information on how to do that can be found here: https://github.com/ltdarocha/slackbot.

After following the steps from the provided link, you will now have a Token for your Bot Application. The following code connects Python with your Bot.

```
from slackclient import SlackClient

# bot token will start with 'xoxb'
BOT_TOKEN = 'insert-your-bot-token'

slack_client = SlackClient(BOT_TOKEN)
```

To send data to the channel, the channel's id has to be stored. The following function will give the name and id for all the channels in your Slack account.

```
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
```

The following function will activate your bot (make bot online) and send the message to the desired channel.

```
def post_message():
# send message to python:
    for i in message['job_posts']:  
        if slack_client.rtm_connect():
            slack_client.api_call("chat.postMessage", channel = channels_id[4], text = i)

# channels_id[4] is the id of the channel I want the message to be sent to.

post_message()
```

I setup a cronjob on my computer for this code to run everyday at 9am. You can also deploy your bot with hosting services websites such as 'Heroku'.

This is how the final Slackbot messages look like.

![image](https://imgur.com/483du5L.png)

### Data analysis

Some basic analysis is performed to explore the data and understand all the job postings that gets extracted (including old job postings).

The positions of interest in this example are the ones that has 'Data Scientist' or 'Analyst' in the job title, and the locations 'Seattle' and 'Bellevue'.

The data gets cleaned and renamed by matching the key words of interest to the job postings extracted data to run the analysis.

<p align="center">
<img src="https://imgur.com/belJy2q.png" width="300" align="center">     <img src="https://imgur.com/02Vvh8i.png" width="280" align="center">
</p>

The chart above draws the conclusion that the majority of 66% of the returned job postings are not of interest in this case, defined as 'Other position'. Hence, only 34% of the search returned data is valuable.

<p align="center">
<img src="https://imgur.com/BA6f1ri.png" width="300" align="center">     <img src="https://imgur.com/yfa8fXF.png" width="300" align="center">
</p>

From the chart presented it is possible to observe that, approximately, 50% of the job postings searched are based in Seattle. The second highest location is 'Other location', representing 34% of the total of the job postings search. Concluding the 'Seattle' filter is not 100% accurate.

![image](https://imgur.com/u1C8cTU.png)

From the chart presented it is possible to observe that the job title 'Other position' is the most frequent for all the listed locations, being a total of, approximately, 66% of the total job postings. As pointed previously, only 34% of the job postings have the desired job title, and only 19% of the job postings match the ideal position based on title and location.

It is possible to conclude a high percentage of the job postings for the filtered criteria (statistics, seattle, entry-level, etc) does not match the desired job title (Data Scientist or Analyst) and location (Seattle and Bellevue), representing 19% of the total returned data.

### Issues/Next steps:

- Date posted not found for some job postings
- Hyperlinks paths are not fully complete, so some arrangements had to be done. Current code might not work for hyperlinks that has a different format than the ones encountered so far.
