# Quiet-Harvey
#### An expandable wordcloud and statistical analysis generator from live tweets

Quiet-Harvey is a big data analysis project using Mongo Atlas and Wordcloud.py to generate wordclouds from the twitter streaming API as well as provide analytical statistics data such as frequency distributions, retweet density, etc


## Installation

##### Note: You will need **python3.5** and **mongoDB** installed in order to sucessfully run Quiet-Harvey

1. Clone this repo 
    `git clone https://github.com/hdmifish/quiet-harvey.git quiet-harvey `

2. Install pip if you don't already have it
    i. `wget bootstrap.pypa.io/get-pip.py`
    ii. `sudo python3.5 get-pip.py`

3. Install requirements
    i. `sudo -H python3.5 -m pip install --upgrade -r requirements.txt`

4. Configure and retrieve tokens
    i. Go to https://apps.twitter.com/
    ii. Create an application and give it `read` permissions. You need to authenticate it to your own account.  Dont worry about the callback-uri or company name, this is going to run on your personal account

    iii. copy your tokens into example_config.json
    *   con_key = consumer key
    *   con_sec = consumer secret
    *   tok_key = oauth token key
    *   tok_sec = oauth secret
    *   remote_uri = Your mongoDB atlas uri (not covered in this tutorial and purely optional)
    *   use_local = True (set this to false if using atlas)
    

## Running
##### Default values can be changed by editing quietharvey.py


* `python3.5 quietharvey.py`
* CTRL+C (ONCE) to stop crawling tweets before the automatic cutoff





