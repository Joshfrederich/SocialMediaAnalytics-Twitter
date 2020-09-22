from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
import sqlite3
import tweepy
import re
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta


class twitterforcovid:

    def __init__(self):
        pass

    def verif(self, consumer_key, consumer_secret, access_token, access_token_secret):
        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_token, access_token_secret)
        self.api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)

    def update_data(self):
        search_words = "vaksin covid"
        date_until = datetime.today().strftime("%Y:%m:%d").replace(':', '-')
        date_since = (datetime.today() - timedelta(days=2)).strftime("%Y:%m:%d").replace(':', '-')

        new_search = search_words + " -filter:retweets"

        tweets = tweepy.Cursor(self.api.search,
                               q=new_search,
                               lang="id",
                               until=date_until,
                               since=date_since,
                               tweet_mode="extended").items()

        tweeps = []
        tweetid = []
        tweettime = []
        tweetuser = []
        Pre = []

        factory = StemmerFactory()
        stemmer = factory.create_stemmer()

        for tweet in tweets:
            tweettime.append(tweet.created_at.strftime("%Y:%m:%d").replace(':', '-'))
            tweetuser.append('@' + tweet.user.screen_name)
            tweetid.append(tweet.id)
            twi = ' '.join(re.sub("(@[A-Za-z0-9]+)|([^0-9A-Za-z \t])|(\w+:\/\/\S+)", " ", tweet.full_text).split())
            tweeps.append(twi)
            Pre.append(stemmer.stem(twi))

        dict = {'tweet': tweeps, 'tweettime': tweettime, 'tweetuser': tweetuser, 'pre': Pre, 'tweetid': tweetid}
        hasil = pd.DataFrame(dict)

        connection = sqlite3.connect('twitter.db')
        query = '''CREATE TABLE IF NOT EXISTS Tweets(
                                     tweet_time DATE NOT NULL,
                                     tweetusername TEXT NOT NULL,
                                     tweet TEXT NOT NULL,
                                     tweetid INT NOT NULL,
                                     PRIMARY KEY  (`tweetid`)
                                     );'''
        cursor = connection.cursor()
        cursor.execute(query)
        cursor.close()

        query = '''CREATE TABLE IF NOT EXISTS TweetsPre(
                                             tweets TEXT NOT NULL,
                                             sentiment INT,
                                             tweet_time DATE NOT NULL,
                                             tweetid INT NOT NULL UNIQUE 
                                             );'''
        cursor = connection.cursor()
        cursor.execute(query)
        cursor.close()

        for i in range(0, len(hasil)):
            query = '''INSERT OR IGNORE INTO TweetsPre(tweets, tweetid,tweet_time) values (?,?,?)'''
            cursor = connection.cursor()
            cursor.execute(query, (hasil.pre[i], int(hasil.tweetid[i]), hasil.tweettime[i]))
            cursor.close()

        for i in range(0, len(hasil)):
            query = '''INSERT OR IGNORE INTO Tweets(tweet_time, tweetusername, tweet, tweetid) values (?,?,?,?)'''
            cursor = connection.cursor()
            cursor.execute(query, (hasil.tweettime[i], hasil.tweetuser[i], hasil.tweet[i], int(hasil.tweetid[i])))
            cursor.close()
        connection.commit()
        connection.close()

    def updateSentiment(self):
        av = sqlite3.connect('Twitter.db')
        df = pd.read_sql_query("SELECT * FROM TweetsPre WHERE sentiment IS NULL ", av)

        pos_list = open("./kata_positif.txt", "r")
        pos_kata = pos_list.readlines()
        neg_list = open("./kata_negatif.txt", "r")
        neg_kata = neg_list.readlines()
        S = []
        for item in df['tweets']:
            count_p = 0
            count_n = 0
            for kata_pos in pos_kata:
                if kata_pos.strip() in item:
                    count_p += 1
            for kata_neg in neg_kata:
                if kata_neg.strip() in item:
                    count_n += 1
            # print("positif: " + str(count_p))
            # print("negatif: " + str(count_n))
            S.append(count_p - count_n)
            # print ("-----------------------------------------------------")

        for i in range(0, len(df)):
            df.at[i, 'sentiment'] = S[i]

        connection = sqlite3.connect('twitter.db')
        for i in range(0, len(df)):
            query = '''UPDATE TweetsPre SET sentiment = ? WHERE sentiment IS NULL AND tweets = ? '''
            cursor = connection.cursor()
            cursor.execute(query, (df.sentiment[i], df.tweets[i]))
            cursor.close()
        connection.commit()
        connection.close()

        # print("Nilai rata-rata: " + str(np.mean(df["sentiment"])))
        # print("Nilai median: " + str(np.median(df["sentiment"])))
        # print("Nilai STD: " + str(np.std(df["sentiment"])))

    def lihatdata(self, timestart, timestop):

        av = sqlite3.connect('Twitter.db')
        df = pd.read_sql_query("SELECT * FROM Tweets WHERE tweet_time BETWEEN ? AND ?", av,
                               params=(timestart, timestop))
        dict = {}
        for i in range(0, len(df)):
            dict = {'Akun': df.tweetusername[i], 'Tanggal': df.tweet_time[i], 'Tweet': df.tweet[i]}
            print(dict)

    def visualisasi(self, timestart, timestop):

        av = sqlite3.connect('Twitter.db')
        df = pd.read_sql_query("SELECT * FROM TweetsPre WHERE tweet_time BETWEEN ? AND ?", av,
                               params=(timestart, timestop))
        print(df.head())

        print("Nilai rata-rata: " + str(np.mean(df["sentiment"])))
        print("Nilai median: " + str(np.median(df["sentiment"])))
        print("Nilai STD: " + str(np.std(df["sentiment"])))

        self.labels, self.counts = np.unique(df["sentiment"], return_counts=True)

        plt.bar(self.labels, self.counts, align='center')
        plt.gca().set_xticks(self.labels)
        plt.show()


consumer_key = "XXXXXXXXXXXXXXXXXXXXXXXX"
consumer_secret = "XXXXXXXXXXXXXXXXXXXXXXXX"
access_token = "XXXXXXXXXXXXXXXXXXXXXXXX"
access_token_secret = "XXXXXXXXXXXXXXXXXXXXXXXX"

while True:
    print("Apa yang ingin anda lakukan?")
    print("\t 1. Update Data")
    print("\t 2. Update Nilai Sentimen")
    print("\t 3. Lihat Data")
    print("\t 4. Visualisasi Data")
    print("\t 5. Keluar")
    choice = input("\tInput anda : ")

    if choice == '1':
        twitter = twitterforcovid()
        twitter.verif(consumer_key, consumer_secret, access_token, access_token_secret)
        twitter.update_data()

    elif choice == '2':
        twitter = twitterforcovid()
        twitter.updateSentiment()

    elif choice == '3':
        twitter = twitterforcovid()
        startdate = input("tanggal awal (format: 2020-04-24): ")
        enddate = input("tanggal akhir (format: 2020-04-24): ")
        twitter.lihatdata(startdate, enddate)

    elif choice == '4':
        twitter = twitterforcovid()
        startdate = input("tanggal awal (format: 2020-04-24): ")
        enddate = input("tanggal akhir (format: 2020-04-24): ")
        twitter.visualisasi(startdate, enddate)

    elif choice == '5':
        break

    else:
        pass
