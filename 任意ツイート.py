# -*- coding: utf-8 -*-
"""
Created on Thu Oct 29 12:25:42 2020

@author: Yu-ri
"""

"""
"""
#標準ライブラリ
from os import path
#自作コード
import BaseOrder
from Keyword import OAuth
from NoidParameters import FileAndPath as noid_fap

#　↓　下のコードでKeyを取ると、テスト環境でツイートする！！！
api = OAuth.get_oauth(path.join("Database","TestNoid_api_keys.csv"))
#　↓　下のコードでKeyを取ると、本番環境でツイートする！！！
#api = OAuth.get_oauth(keys_file = path.join("Database","------_api_keys.csv"))


"""一言ツイートするだけの時(テスト)"""
text = "テスト"
api.update_status(text)


"""返信ツイートするだけの時(すぐに削除すること！)"""
#text = "replay"
#api.update_status(status=text, 
 #               in_reply_to_status_id=1324626613829464065, 
  #              auto_populate_reply_metadata=True)


"""一連のツイートをまとめてするとき"""
#BaseOrder.PostOrder.group_tweet(api, tweet_file=path.join("tweet_files","group_tweet.csv"))

""""""
#BaseOrder.PostOrder.random_tweet(api, noid_fap.PATH_AD_TWEET_FILE)
