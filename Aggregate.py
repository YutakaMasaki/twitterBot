# -*- coding: utf-8 -*-
"""
Created on Sat May 16 13:47:28 2020

@author: Yu-ri
"""

"""
コンテンツ関連ツイートを行った人を、アカウントのリストに登録する
"""

import logging#printではなくLoggingを使ってみよう
import datetime
import os
import time

from BaseOrder import PostOrder as po
from BaseOrder import RWOrder as rwo
from NoidParameters import IDs as noid_IDs
from NoidParameters import CommandType as noid_ct



class ListUpdate():

    def __init__(self, api, lock, request_reception):
        self.api = api
        self.lock = lock
        self.request_reception = request_reception
        self.user_list_ID = {"Lv1_list_id":noid_IDs.LIST_Lv1,
                          "Lv2_list_id":noid_IDs.LIST_Lv2,
                          "Lv3_list_id":noid_IDs.LIST_Lv3,
                          "Lv4_list_id":noid_IDs.LIST_Lv4}
        
        
    #キーワードを含むツイートを、過去一週間に何回行ったかを集計する
    def aggr_score(self, database_path, mainword_list, subword_list, rename_database_file=True):
        print("リスト更新開始")
        logging.info("リスト更新開始")
        if os.path.isfile(database_path)==False:
            logging.error("databeseファイルが見つからないため、リスト更新を中止しました。")
            raise FileNotFoundError("databaseファイルが見つかりません。リスト更新を中止しました。")
            
        #Managerへの許可申請
        command_type1 = noid_ct.LIST_MEMBERS#リスト参照
        command_type1["num_of_req"] = 4
        command_type2 = noid_ct.LIST_MEMBERS_CREATE_ALL#リストメンバーの削除
        command_type2["num_of_req"] = 4
        command_type3 = noid_ct.LIST_MEMBERS_DESTROY_ALL#リストメンバーの追加
        command_type3["num_of_req"] = 4
        command_type4 = noid_ct.STATUSES_UPDATE#リスト更新を知らせるツイート
        
        try:
            self.lock.acquire()
            self.request_reception(command_type1)
            self.request_reception(command_type2)
            self.request_reception(command_type3)
            self.request_reception(command_type4)
            self.lock.release()
        except:
            logging.worning("リソースの確保に失敗しました\nリスト更新を中断します")
            raise RuntimeError("リスト更新エラー。リストが更新されていません(point1)")              
        
        #ファイル名の変更し、ほかの関数からの変更が及ばないようにする。1週間分のデータを対比することが目的。
        try:
            if rename_database_file == True:
                database_path=self._attach_datetime2filename(database_path)
            #ため込んだツイートデータの読み込み
            tweets_data = rwo.read_database(database_path, True)
            print("read data complete.")
            
        except:
            logging.error("ファイル名の編集、もしくはデータの読み込みに失敗しました\nリスト更新を中断します")
            raise RuntimeError("リスト更新エラー。リストが更新されていません(point2)")
        
        """
        tweetの文章に'mainword','subword'がどれだけ含まれているかをカウントし、dictにして返す。
        this_week_user_eval={"user_id":評価値（0~4）}
        """
        try:
            this_week_user_eval = self._count_tweets_score(tweets_data, mainword_list, subword_list)
            
            #現在のリストを取得する
            #list_members={"Lv1_set":"Lv1のユーザーIDまとめ", "Lv2_set":"Lv2のユーザーIDまとめ"....}
            list_members = self._get_list_members()
            
            #今週のスコアと、先週までに登録されているユーザーを照合し、新しくリストを更新する
            self._list_update(this_week_user_eval, list_members)
            print("list is updated")
        except:
            raise
            
        self.create_report()
        """
        機能開放する前までは、このまま
        try:
            text = "【お知らせ】\n今週のリメンバーズリスト自動更新が完了したゾ！"
            po.tweet(self.api, text)
        except:
            raise RuntimeError("リスト更新は成功しましたが、完了報告ツイートに失敗しました。")
        """
          
        
    def _count_tweets_score(self, tweets_data, mainword_list, subword_list):
        try:
            #文字が含まれているかどうかのカウント。
            score_dict = {} #[mainword_num, subword_and_countword_num]
            for one_tweet in tweets_data:
                if one_tweet[1] == noid_IDs.MY_USER_ID:
                    #自分のツイートなら無視する
                    continue
                score = self._words_in_text(one_tweet[3], mainword_list, subword_list)
                #dictに突っ込んでいく
                userid_str = str(one_tweet[1])
                if score_dict.get(userid_str) == None:
                    score_dict[userid_str] = {"main_cnt":score[0], "sub_cnt":score[1]} 
                else:
                    score_dict[userid_str]["main_cnt"] += score[0]
                    score_dict[userid_str]["sub_cnt"] += score[1]
                    
            #文字数に応じて、評価値（Lv0~Lv4）を割りふる
                    users_eval = {}
            for u_id in score_dict.keys():
                if score_dict[u_id]["main_cnt"]>=6 and score_dict[u_id]["sub_cnt"]>=7:
                    users_eval[u_id] = 4
                elif score_dict[u_id]["main_cnt"]>=3 and score_dict[u_id]["sub_cnt"]>=4:
                    users_eval[u_id] = 3
                elif score_dict[u_id]["main_cnt"]>=2 and score_dict[u_id]["sub_cnt"]>=2:
                    users_eval[u_id] = 2
                elif score_dict[u_id]["main_cnt"]>=1 and score_dict[u_id]["sub_cnt"]>=1:
                    users_eval[u_id] = 1
                else:#それ以下ならカウントしない
                    continue
            return users_eval
                
        except Exception as e:
            logging.error("文字のカウントに失敗しました。\nリスト更新を中断します\nerror: {}".format(e.args))
            raise RuntimeError("リスト更新エラー。リストが更新されていません(point3)")


    def _get_list_members(self):
        try:
            Lv1_users = self.api.list_members(list_id = self.user_list_ID["Lv1_list_id"], include_entities=False, skip_status=True)
            Lv2_users = self.api.list_members(list_id = self.user_list_ID["Lv2_list_id"], include_entities=False, skip_status=True)
            Lv3_users = self.api.list_members(list_id = self.user_list_ID["Lv3_list_id"], include_entities=False, skip_status=True)
            Lv4_users = self.api.list_members(list_id = self.user_list_ID["Lv4_list_id"], include_entities=False, skip_status=True)
            self.remembers_num_before = [len(Lv1_users),len(Lv2_users),len(Lv3_users),len(Lv4_users)]
            
            list_members_id = {
                "Lv1_set":set(map(lambda l:l.id, Lv1_users)),
                "Lv2_set":set(map(lambda l:l.id, Lv2_users)),
                "Lv3_set":set(map(lambda l:l.id, Lv3_users)),
                "Lv4_set":set(map(lambda l:l.id, Lv4_users))
                }
        except Exception as e:
            logging.error("リスト取得コマンド、もしくはsetへの格納に失敗しました。\nリスト更新を中断します\nerror:{}".format(e.args))
            raise RuntimeError("リスト更新エラー。リストが更新されていません(point4)")
        
        return list_members_id
        
    
    #点数に基づいて、集合論理演算によってグループ分けをして、実際にリストの更新を行います。
    def _list_update(self, users_eval, list_members):
        #評価対象のユーザーIDをsetに入れる 
        new_users_id_str = set(users_eval.keys())
        new_users_id = set(map(int, new_users_id_str))
        #前回のリストに入っていた人をひとまとめにしてsetに入れる
        existing_users_id = list_members["Lv1_set"] | list_members["Lv2_set"] | list_members["Lv3_set"] | list_members["Lv4_set"]
        
        """
        今週のリスト、先週までのリスト、を論理演算し、
         1.先週いて、今週もいたグループ
         2.先週はいたけど、今週はいなかったグループ
         3.今週新しく見つけたグループ
        の3つに分ける。
        
        #1のグループは、レベルを比較して、上回っていれば1つ昇格、2Lv以上下回っている、かつLv.3以上なら降格
        #2のグループは、レベル3以上なら降格
        #3のグループは、Lv.1に追加
        """
        group_1 = {"Lv1_users_id": list_members["Lv1_set"] & new_users_id,
                   "Lv2_users_id": list_members["Lv2_set"] & new_users_id,
                   "Lv3_users_id": list_members["Lv3_set"] & new_users_id,
                   "Lv4_users_id": list_members["Lv4_set"] & new_users_id}
        group_2 = existing_users_id - new_users_id
        group_3 = new_users_id - existing_users_id
        
        #コマンド送信用に、空箱の用意
        move_list_id={
            "del":{
                "Lv1":list(),
                "Lv2":list(),
                "Lv3":list(),
                "Lv4":list()
                },
            "add":{
                "Lv1":list(),
                "Lv2":list(),
                "Lv3":list(),
                "Lv4":list()
                }
            }
        
        #配属グループごとに、グループの移動（del&addにより）を行う
        """グループ１　先週も今週も見たグループ"""
        for user_id in group_1["Lv1_users_id"]:
            if users_eval[str(user_id)] > 1:
                move_list_id["del"]["Lv1"].append(user_id)
                move_list_id["add"]["Lv2"].append(user_id)
            else:
                continue
        for user_id in group_1["Lv2_users_id"]:
            if users_eval[str(user_id)] > 2:
                move_list_id["del"]["Lv2"].append(user_id)
                move_list_id["add"]["Lv3"].append(user_id)
            else:
                continue
        for user_id in group_1["Lv3_users_id"]:
            if users_eval[str(user_id)] > 3:
                move_list_id["del"]["Lv3"].append(user_id)
                move_list_id["add"]["Lv4"].append(user_id)
            else:
                continue
        for user_id in group_1["Lv4_users_id"]:
            if users_eval[str(user_id)] == 4:
                pass
            elif users_eval[str(user_id)] < 3:
                move_list_id["del"]["Lv4"].append(user_id)
                move_list_id["add"]["Lv3"].append(user_id)
            else:
                continue
            
        """グループ2 リストにいたけど、今週は見なかったグループ"""
        for user_id in group_2:
            if user_id in list_members["Lv1_set"]:
                move_list_id["del"]["Lv1"].append(user_id)
            elif user_id in list_members["Lv3_set"]:
                move_list_id["del"]["Lv3"].append(user_id)
                move_list_id["add"]["Lv2"].append(user_id)
            elif user_id in list_members["Lv4_set"]:
                move_list_id["del"]["Lv4"].append(user_id)
                move_list_id["add"]["Lv3"].append(user_id)
            else:
                continue
            
        """グループ3 新たに加わるグループ"""
        for user_id in group_3:
            move_list_id["add"]["Lv1"].append(user_id)
        
        """レポート作成のための、増減リスト作成"""
        self.add_remembers_list = [len(move_list_id["add"]["Lv1"]),len(move_list_id["add"]["Lv2"]),len(move_list_id["add"]["Lv3"]),len(move_list_id["add"]["Lv4"])]
        self.del_remembers_list = [len(move_list_id["del"]["Lv1"]),len(move_list_id["del"]["Lv2"]),len(move_list_id["del"]["Lv3"]),len(move_list_id["del"]["Lv4"])]
        
        """リストの更新"""
        try:
            """リスト１から削除"""
            while len( move_list_id["del"]["Lv1"]) > 100:
                temp_list_id = move_list_id["del"]["Lv1"][:100]
                self.api.remove_list_members(list_id=self.user_list_ID["Lv1_list_id"], user_id=temp_list_id)
                del move_list_id["del"]["Lv1"][:100]
                time.sleep(60*30)#制限があるっぽいので、ひとまず30分待ってみる
            if move_list_id["del"]["Lv1"] != []:
                self.api.remove_list_members(list_id=self.user_list_ID["Lv1_list_id"], user_id=move_list_id["del"]["Lv1"])
            
            """リスト２から削除"""
            while len( move_list_id["del"]["Lv2"]) > 100:
                temp_list_id = move_list_id["del"]["Lv2"][:100]
                self.api.remove_list_members(list_id=self.user_list_ID["Lv2_list_id"], user_id=temp_list_id)
                del move_list_id["del"]["Lv2"][:100]
                time.sleep(60*30)    
            if move_list_id["del"]["Lv2"] != []:
                self.api.remove_list_members(list_id=self.user_list_ID["Lv2_list_id"], user_id=move_list_id["del"]["Lv2"])
            
            """リスト３から削除"""
            while len( move_list_id["del"]["Lv3"]) > 100:
                temp_list_id = move_list_id["del"]["Lv3"][:100]
                self.api.remove_list_members(list_id=self.user_list_ID["Lv3_list_id"], user_id=temp_list_id)
                del move_list_id["del"]["Lv3"][:100]
                time.sleep(60*30)
            if move_list_id["del"]["Lv3"] != []:
                self.api.remove_list_members(list_id=self.user_list_ID["Lv3_list_id"], user_id=move_list_id["del"]["Lv3"])
            
            """リスト４から削除"""
            while len( move_list_id["del"]["Lv4"]) > 100:
                temp_list_id = move_list_id["del"]["Lv4"][:100]
                self.api.remove_list_members(list_id=self.user_list_ID["Lv4_list_id"], user_id=temp_list_id)
                del move_list_id["del"]["Lv4"][:100]
                time.sleep(60*30)
            if move_list_id["del"]["Lv4"] != []:
                self.api.remove_list_members(list_id=self.user_list_ID["Lv4_list_id"], user_id=move_list_id["del"]["Lv4"])
              
            time.sleep(60*30)#待機時間
            
            """リスト１に追加"""
            while len( move_list_id["add"]["Lv1"]) > 100:
                temp_list_id = move_list_id["add"]["Lv1"][:100]
                self.api.add_list_members(list_id=self.user_list_ID["Lv1_list_id"], user_id=temp_list_id)
                del move_list_id["add"]["Lv1"][:100]
                time.sleep(60*30)
            if move_list_id["add"]["Lv1"] != []:
                self.api.add_list_members(list_id=self.user_list_ID["Lv1_list_id"], user_id=move_list_id["add"]["Lv1"])
            
            """リスト２に追加"""
            while len( move_list_id["add"]["Lv2"]) > 100:
                temp_list_id = move_list_id["add"]["Lv2"][:100]
                self.api.add_list_members(list_id=self.user_list_ID["Lv2_list_id"], user_id=temp_list_id)
                del move_list_id["add"]["Lv2"][:100]
                time.sleep(60*30)
            if move_list_id["add"]["Lv2"] != []:
                self.api.add_list_members(list_id=self.user_list_ID["Lv2_list_id"], user_id=move_list_id["add"]["Lv2"])
            
            """リスト３に追加"""
            while len( move_list_id["add"]["Lv3"]) > 100:
                temp_list_id = move_list_id["add"]["Lv3"][:100]
                self.api.add_list_members(list_id=self.user_list_ID["Lv3_list_id"], user_id=temp_list_id)
                del move_list_id["add"]["Lv3"][:100]
                time.sleep(60*30)
            if move_list_id["add"]["Lv3"] != []:
                self.api.add_list_members(list_id=self.user_list_ID["Lv3_list_id"], user_id=move_list_id["add"]["Lv3"])
            
            """リスト４に追加"""
            while len( move_list_id["add"]["Lv4"]) > 100:
                temp_list_id = move_list_id["add"]["Lv4"][:100]
                self.api.add_list_members(list_id=self.user_list_ID["Lv4_list_id"], user_id=temp_list_id)
                del move_list_id["add"]["Lv4"][:100]
                time.sleep(60*30)
            if move_list_id["add"]["Lv4"] != []:
                self.api.add_list_members(list_id=self.user_list_ID["Lv4_list_id"], user_id=move_list_id["add"]["Lv4"])
            
        except Exception as e:
            logging.error("リストの更新に失敗しました。更新リストを一時保存します。{}".format(e.args))
            try:
                self._save_dict(move_list_id) 
            except:
                raise
        else:
            logging.info("リストの更新が完了しました！")

            
    def _save_dict(w_dict, str1="", str2=""):
        import pickle
        try:
            time_info = datetime.datetime.today()
            now = time_info.strftime("%Y%m%d_%H%M%S")
            filepath = "false_dict_at"+now+".dat"
            with open(filepath, mode="wb") as ff:
                pickle.dump(w_dict, ff)
        except:
            print("リストの一時保存に失敗しました。")
            logging.error("更新リストの一時保存も失敗しました。")
            raise
    
    
    def _words_in_text(self, text, word_list1, word_list2):
        in_word_1 = False   
        in_word_2 = False
        for w1 in word_list1:
            if w1 in text:
                in_word_1 = True
                break
            
        for w2 in word_list2:
            if w2 in text:
                in_word_2 = True
                break   
        #print(text)
        #print(in_word_1, in_word_2)
        #print()  
        return [in_word_1, in_word_2]
        
    
    def _attach_datetime2filename(self, before_file_path):
        if os.path.isfile(before_file_path) == False:
            logging.error("'DATABASE.db'ファイルが見つかりません")
            raise FileExistsError()
        devided_name = before_file_path.rsplit(".",maxsplit=1)
        now = datetime.datetime.fromtimestamp(time.time())
        after_path = devided_name[0]+now.strftime('%Y%m%d_%H%M%S')+"."+devided_name[1]
        #ファイルアクセスが10回失敗したらあきらめる
        for i in range(0,10):
            try:
                os.rename(before_file_path, after_path)
            except:
                #ファイル名が書き換えられなかったら3秒待つ
                time.sleep(3)
                continue
            else:
                logging.info("ファイル名の変更が完了しました()")
                return after_path
        logging.error("ファイルの名前書き換えが10回失敗しました。エラーとして中断します")
        raise RuntimeError("ファイルの名前書き換えができません。")
  
    def create_report(self):
        logging.info("リスト増減レポート")
        logging.info("元のメンバーズ数（変更前）:{}".format(self.remembers_num_before))
        logging.info("メンバー増加数:{}".format(self.add_remembers_list))
        logging.info("メンバー減少数:{}".format(self.del_remembers_list))