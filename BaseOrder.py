# -*- coding: utf-8 -*-
"""
Created on Sat May 16 14:03:36 2020

@author: Yu-ri
ツイートしたり、取得したり、ファイルを操作したりなど。様々な関数から呼び出される基本的な動作をまとめている。
"""

import os
from os import path
import logging
import csv
import time
import random
import sqlite3
import shutil
from urllib import request as req

from NoidParameters import FileAndPath as noid_fap
from NoidParameters import csvKeys as noid_csv


formatter = '%(levelname)s : %(asctime)s : %(lineno)d: %(message)s : %(pathname)s(%(lineno)s) : %(funcName)s'
logging.basicConfig(level=logging.INFO, format=formatter, filename="Noid.logdata") 
logger = logging.getLogger(__name__)


class PostOrder():
    def tweet(api, text, media_ids=None, reply_id=None):
        try:
            if media_ids == None:
                tweet = api.update_status(text, in_reply_to_status_id=reply_id, auto_populate_reply_metadata=True)
                return tweet
            else:
                tweet = api.update_status(text, media_ids=media_ids, in_reply_to_status_id=reply_id, auto_populate_reply_metadata=True)
                return tweet
        except:
            logging.error("tweet が失敗しました。(po.tweet)")
            raise

    '''指定されたファイルから、ランダムにツイートを行う。'''
    def random_tweet(api, file):
        try:
            tweet_dict = PostOrder._take_random_tweet(file)
            tweet = api.update_status(tweet_dict["text"])
            return tweet
        except Exception as e:
            logging.error("Random tweet が失敗しました。\nエラー内容：{}".format(e.args))
            raise
            
    def reply(api, original_tweet, reply_text, media_path=None):
        user_name = original_tweet.user.name
        tweet_id = original_tweet.id
        try:
            if media_path!=None:
                media = api.upload_media(media_path)
                media_id = media.media_id
            else:
                media_id = None
            tweet = api.update_status(status=reply_text, 
                              in_reply_to_status_id=tweet_id, 
                              auto_populate_reply_metadata=True)
            return tweet
        except FileNotFoundError as fe:
            logging.error("ファイルパスが見つかりません（reply関数）")
            raise
        except Exception as e:
            logging.error("リプライに失敗しました.\nエラー内容：{}".format(e.args))
            raise            
            
        
        
    '''ｃｓｖファイルからツイートを取得して、ランダムに１列返します'''
    def _take_random_tweet(file, countup_sum_of_tweet=True):
        try:
            tweet_list = RWOrder.open_file(file)
            for i in range(0,30):
                random_line = random.randint(0,len(tweet_list)-1)
                if tweet_list[random_line]["TweetRightBefore"]=="1":
                    continue
                elif i >= 29:
                    logging.error("１つのファイルから同じツイートしかできない")
                    raise RuntimeError("１つのファイルからの同じツイートしかできない")
                else:
                    break
            taked_data = tweet_list[random_line]
            
            if countup_sum_of_tweet == True:
                #長いけど、文字列の数字を１カウントアップしてるだけ
                tweet_list[random_line]["SumOfTweet"]=str(int(tweet_list[random_line]["SumOfTweet"],10)+1)
            
            RWOrder.save_file(file, tweet_list, noid_csv.TWEET_CSV_KEYS)
        except:
            raise        
        return taked_data
    
    #起動時に、一連の流れをツイートしてくれる。起動時じゃなくても、呼び出せばツイートしてくれる。
    def group_tweet(api, tweet_file):
        tweet_list = RWOrder.open_file(tweet_file)
        i=0
        while i < len(tweet_list):
            media_ids = PostOrder.upload_and_get_ids(api, tweet_list[i]["media"])
            tweet1 = PostOrder.tweet(api, tweet_list[i]["text"], media_ids=media_ids)
            print("■"+tweet_list[i]["discription"]+"\n  user_id : "+tweet1.user.screen_name+"\n  tweet_id : "+str(tweet1.id))
            print("  url : https://twitter.com/"+tweet1.user.screen_name+"/status/"+str(tweet1.id))
            if tweet_list[i]["reply"] != "":
                num = int(tweet_list[i]["reply"])
                while i < num:
                    i += 1
                    media_ids = PostOrder.upload_and_get_ids(api, tweet_list[i]["media"])
                    PostOrder.tweet(api, tweet_list[i]["text"], media_ids=media_ids, reply_id=tweet1.id)
            i += 1
        return
                    
    def upload_and_get_ids(api, file_path):
        """以下、パスの正規化。OS差を吸収。"""
        list_path = file_path.split("/")
        folder_path = path.join(*list_path)
        
        """以下、画像のアップロード"""
        try:
            media_list = []
            media_ids = []
            for num in range(1,5):
                filepath = path.join(folder_path,(str(num) + ".jpg")) #Twitterからとってくる画像の形式って何？
                if path.isfile(filepath):
                    media_list.append(filepath)
                else:
                    break       
            media_ids = PostOrder.media_upload(api, media_list)
        except Exception as e:
            print("メディアアップデートに失敗しました。迷場面ツイートをキャンセルします。")
            logging.error("メディアアップデートに失敗しました。迷場面ツイートをキャンセルします。\n内容：{}".format(e.args))
            raise
        return media_ids
    
    def media_upload(api, media_path_list):
        media_ids = []
        for media_path in media_path_list:
            if media_path == "":
                continue
            else:
                join_path = path.join(media_path)
                upload_media = api.media_upload(join_path)
                media_ids.append(upload_media.media_id)
        
        return media_ids
                
        
   
class GetOrder():  
    def search_tweets(api, search_word, get_tweet_num, since_id=None, trim_user=False, include_entities=False):
        try:
            tweets = api.search(q = search_word, 
                                lang="ja", 
                                #result_type="recent",
                                trim_user=trim_user,
                                include_entities=include_entities,
                                count=str(get_tweet_num),
                                since_id=since_id#,
                                #tweet_mode="extended"
                                )
        except:
            logging.error("api.searchに失敗しました.。Noneを返しました。")
            return None#検索結果がなかった場合、どんな変数が返ってくるかによる

        return tweets
    
    def show_tweet(api, tweet_id):
        return api.get_status(tweet_id)
               
         
class RWOrder():
    
    def save_tweets_database(tweets, writefile):
        data=[]
        if tweets==[]:
            raise RuntimeError("取得ツイートゼロです")
            return
        for tw in tweets:
            data.append([tw.id, tw.user.id, tw.created_at, tw.text])
            
        #コネクションの確立
        conn = sqlite3.connect(writefile)
        #作業場の構築とデータの保存
        c = conn.cursor()
        try:
            c.execute('''CREATE TABLE IF NOT EXISTS tweets_data
                 (tweet_id int, user_id int, date text, text text)''')
            c.executemany("INSERT INTO tweets_data VALUES (?,?,?,?)",data)
            #c.execute('''CREATE TABLE IF NOT EXISTS infomation
            #     (start_day str, end_day str)''')
            #c.execute("INSERT INTO infomation VALUES (?,?)",time_info)
        except sqlite3.Error as e:
            print('sqlite3.Error occurred:', e.args[0])
        finally:
            #保存と接続の切断
            conn.commit()
            conn.close()
            
            
    def read_database(filename, ordered_by_userid=False):
        conn = sqlite3.connect(filename)
        cur = conn.cursor()
        try:
            if ordered_by_userid == True:
                cur.execute("""SELECT * FROM tweets_data ORDER BY user_id""")
            elif ordered_by_userid == False:
                cur.execute("""SELECT * FROM tweets_data""")
            database_list =  cur.fetchall()#全部のデータを取得している。メモリが足りなくなりそうなら、一部の列にするべき
            #print(database_list)
        except sqlite3.error as e:
            print("Catch SQLite error : ",e)
            database_list = None
        finally:
            conn.commit()
            conn.close()
        
        return database_list
    
    
    def open_file(file):
        for trying in range(0,4):
            try:
                with open(file, mode="r", encoding="utf-8-sig") as f:
                    return list(csv.DictReader(f))
            except Exception as e:
                logging.info("ファイル読み込み失敗（{}回目）n. : {} エラー内容:{}".format(trying, file, e.args))
                time.sleep(5)
                continue
        logging.error("ファイルの読み込みに5回十敗しました。読み込みを終了します。")
        raise RuntimeError("ファイルを読み込めません。ファイル名:{}".format(file))
                    
    
    '''ツイートした回数を更新して、保存します。'''
    def save_file(file, w_list, field_names):
        #最初にファイルのコピーを作成しておく
        tmp_file = file.rstrip(".csv") + "_buckup.csv"
        shutil.copy(file, tmp_file)
        for i in range(0,5):
            try:
                """以下、ファイル書き込み"""
                with open(file, mode="w", encoding="utf-8-sig", newline="") as f:
                    writer = csv.DictWriter(f, fieldnames = field_names)
                    writer.writeheader()
                    for w_line in w_list:
                        line_dict = {}
                        for key in field_names:
                            line_dict[key] = w_line[key]
                        writer.writerow(line_dict)
                os.remove(tmp_file)
                return True
            #正常ならここ↑で終了
            #異常の場合はこの下でエラー処理
            except Exception as e:
                text = "ファイルの書き込みに失敗しました({})。 file path:{}".format(i, file)
                text2 = "\nエラー内容:{}".format(e.args)
                logging.info(text+text2)
                time.sleep(10)
                continue
        logging.warning("ファイルオープンに5回失敗しました。書き込みを諦めます。")
        os.remove(file)
        os.rename(tmp_file, file)
        raise RuntimeError("ファイルを開けません。ファイル名:{}".format(file))
        
        
    """Twitter Json のentities["media"]のデータを引数とする"""
    def download_media(api, media_list, folder_path, filename_list=None):
        num = 1
        for img in media_list:
            img_url = img['media_url']
            if filename_list==None:
                filename = str(num)
            else:
                filename = filename_list[num-1]
            save_path = path.join(folder_path, filename+".jpg")
            #この関数で画像を保存できる
            req.urlretrieve(img_url, save_path)
            num += 1