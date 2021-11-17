# -*- coding: utf-8 -*-
"""
Created on Sat Apr 11 18:45:15 2020

@author: Yu-ri
検索キーワードのcsvファイル読み込み
"""

import csv
import tweepy
import logging
from NoidParameters import FileAndPath as noid_fap

class OAuth:
    #APIとの接続の準備
    def get_oauth(keys_file=noid_fap.API_KEYS):
        try:
            with open(keys_file, mode="r", encoding="utf-8") as f:
                k_dict = csv.DictReader(f)
                for line in k_dict:
                    CK = line["Consumer_Key"]
                    CS = line["Consumer_Secret"]
                    AT = line["Access_Token"]
                    ATS = line["Access_Token_Secret"]
                auth = tweepy.OAuthHandler(CK, CS)
                auth.set_access_token(AT, ATS)
        except:
            logging.error("key read process falsed")
            raise RuntimeError("api key can't read")
        else:
            return tweepy.API(auth)

class ReadKeyword():
    def __init__(self):
        self.cr_list = []
        self.sub_list = []
        self.cnt_list = []
        self.cr_str = ""
        self.sub_str = ""
        
    def csv2str_for_search(self):
        try:
            with open(noid_fap.RELATING_WORDS, mode="r", encoding="utf-8-sig") as f:
                r_list = list(csv.reader(f))
        except:
            raise
            
        try:
            first_line=True
            for line in r_list:
                #最初の行だけ特殊処理
                if first_line==True:
                    if line[0]!="Critical word" or line[1]!="Sub word" or line[2]!="Count word":
                        logging.error("キーワードファイルではありません。不正なファイルが読み込まれました。")
                        raise
                    else:
                        first_line=False
                        continue
        
                if line[0]=="":
                    pass
                else:
                    self.cr_list.append(line[0])
                    
                if line[1]=="":
                    pass
                else:
                    self.sub_list.append(line[1])
                if line[2]=="":
                    pass
                else:
                    self.cnt_list.append(line[2])
                    
        except Exception as e:
            logging.error("キーワードサーチのリスト確認で、その他のエラーが発生しました。\nエラー内容：{}".format(e.args))
            raise RuntimeError("キーワードサーチのリスト確認で、その他のエラーが発生しました\n内容：",e.args)
            
        try:
            for i_str in self.cr_list:
                if self.cr_str == "":
                    self.cr_str = i_str       
                elif " " in i_str:
                    self.cr_str += " OR "+ "(" + i_str+ ")"         
                else:
                    self.cr_str += " OR "+ i_str
                    
            for j_str in self.sub_list:
                if self.sub_str == "":
                    self.sub_str = j_str
                elif " " in j_str:
                    self.sub_str += " OR "+ "(" + j_str+ ")"   
                else:
                    self.sub_str += " OR "+ j_str
                            
            self.search_str = self.cr_str + " OR " + self.sub_str
    #        print(self.words)
    #        print(self.words)
        except:
            raise RuntimeError("キーワード読み込みで、リスト、文字列編集中にエラーが発生しました")
            
    def read_keyword(self, return_type):
        self.csv2str_for_search()
        if return_type=="str":
            return self.search_str
        elif return_type=="list":
            return self.cr_list, self.sub_list+self.cnt_list
        