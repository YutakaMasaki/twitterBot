# -*- coding: utf-8 -*-
"""
Created on Sat Apr 11 12:49:52 2020
@author: Yu-ri
CommandsIF が操作するコマンドと、そのベーススレッドを用意してある。
ベーススレッド継承による拡張性、各機能がすべて個別にスレッド化できることによる並列性を重視。
"""

import time
import copy
import queue
import random
import logging
import datetime
import schedule
import threading


from BaseOrder import PostOrder as po
from BaseOrder import GetOrder as go
from BaseOrder import RWOrder as rwo
from Keyword import ReadKeyword
from Aggregate import ListUpdate
import Noid_Commands as noid_cmds
from NoidParameters import IDs as noid_ids
from NoidParameters import FileAndPath as noid_fap
from NoidParameters import CommandType as noid_ct



formatter = '%(levelname)s : %(asctime)s : %(lineno)d: %(message)s : %(pathname)s(%(lineno)s) : %(funcName)s'
logging.basicConfig(level=logging.INFO, format=formatter, filename="Noid.logdata") 
logger = logging.getLogger(__name__)


class BaseThread(threading.Thread):
    """全てのスレッドが継承する基本のスレッド機能"""
    time_status = None
    task_queue = None
    night_perception_running = False
    def __init__(self, api, name, lock, request_reception, *args, night_sleep=False):
        threading.Thread.__init__(self)
        self.api = api
        self.thread_name = name
        self.lock = lock
        self.request_reception = request_reception
        self.night_sleep=night_sleep
        if BaseThread.task_queue == None:
            q = {
            "DM_1st":queue.Queue(),
            "DM_2nd":queue.Queue(),
            "DM_3rd":queue.Queue()
            }
            BaseThread.task_queue = q
        
        self.cooltime = 60*10   #繰り返し関数のクールタイム。デフォルトは15分なので、各機能ごとに好き勝手に設定する。
        self.countdown = self.cooltime    #1sleepごとに1減っていき、0になったら指定関数を実行する。
        self.init_setting(args)
        
    #Threading.threadのrunをオーバーラップしている。start()で、以下が別スレッドで走る。
    def run(self):
        self.alive = True
        now_time_state = None
        print("thread "+str(self.thread_name)+" 開始")
        print("count down is :",self.countdown)
        
        while self.alive == True:
            time.sleep(1)
            
            """昼夜関係の処理"""
            before_time_state = now_time_state
            now_time_state = BaseThread.time_status
            #就寝機能がOFF、かつ現在が夜なら、メインループの処理を行わない。
            if self.night_sleep==True and now_time_state=="Night":
                time.sleep(10)
                continue
            #朝→夜、夜→朝の変化の瞬間を判定し、関数を実施する
            try:
                if before_time_state=="Night" and now_time_state=="Noon":
                    self.morning_loutine()
                elif before_time_state=="Noon" and now_time_state=="Night":
                    self.night_loutine()
            except:
                logging.error("morning_loutine, night_loutineが失敗しています(BaseThread)")
            
            """メインループと待機処理"""
            #カウントダウンが0になったら。
            if self.countdown <= 0:
                try:
                    self.loop_function()
                    self.countdown = self.cooltime
                    #クールタイムが20秒以下であれば、強制的に20秒になる。
                    if self.cooltime < 20:
                        self.cooltime = 20
                    
                except TypeError as te:
                    logging.error("type error が発生しました\n関数：run,\nthread:{},\nerror:{}".format(self.thread_name, te.args))
                    self.countdown = 15*60
                    continue
                except Exception as e:
                    logging.error("Exception が発生しました 'error:'{}".format(str(e.args)))
                    self.countdown = 15*60
                    continue
                
            self.countdown -= 1
            
    #各スレッドがオーバーラップして自由に使っていく
    def loop_function(self):
        print("This thread's loop function is not overlaped.\n kill this thread.")
        self.cooltime = 60*60*24
        
    #各クラスごとに、最初に実行してほしい処理を入れる。
    def init_setting(self, *args):
        pass
                
    #night_sleepがTrueの場合、朝の活動開始直前に実行される
    def morning_loutine(self):
        pass
    
    #night_sleepがTrueの場合、夜になった終了直後に実行される
    def night_loutine(self):
        pass
        
    def kill_self_thread(self):
        self.alive=False
        
    def save_status_for_restart(self, **args):
        #再開に必要な変数を返す
        return None
        
    def thread_restart(self, **args):
        #前回の設定を引き継いで再開する
        print("thread didn't restart")
        
    
        
class NightPerception(BaseThread):
    
    def thread_preparation(self, good_morning_tweet=True, good_night_tweet=True):
        self.now_state = None
        self.good_morning_tweet = good_morning_tweet
        self.good_night_tweet = good_night_tweet
        if self.night_sleep is True:
            logging.error("夜検知機能は、夜間OFFに設定できません。常時ONに設定します")
            self.night_sleep = False
        pass
    
    def loop_function(self):
        try:
            next_state = self._night_perception()#時間の監視。夜と日中の時間を定義し、当てはまっているほうを通知する
            if self.now_state=="Noon" and next_state=="Night" and self.good_night_tweet==True:
                logging.info("夜時間になりました")
                print("夜になりました。")
                if self._roll_dice()==6:#1/6の確率でツイート
                    po.random_tweet(self.api, noid_fap.PATH_GoodNight_TWEET_FILE)
                else:
                    pass
                    
            elif self.now_state=="Night" and next_state=="Noon" and self.good_morning_tweet==True:
                logging.info("朝時間になりました")
                print("朝になりました。")
                if self._roll_dice()==6:
                    po.random_tweet(self.api, noid_fap.PATH_GoodMorning_TWEET_FILE)
                else:
                    pass
        except RuntimeError as re:
            logging.error("おはようツイート、おやすみツイートに失敗しました。\n内容:{}".format(re.args))
            BaseThread.time_status = self.now_state
        except Exception as e:
            print("予期せぬエラーが発生しました:{}".format(e.args))
            logging.error("エラーが発生しました（night_perception_loop）:{}".format(e.args))
        else:
            self.now_state = next_state
            BaseThread.time_status = self.now_state
        finally:
            self.cooltime = 60*random.randint(5,60)
            #print("night check dome. Now state is ",self.now_state)

        
    def _night_perception(self, night_start_time=23, noon_start_time=6):
        try:
            time_info = datetime.datetime.now()
            now_hour = int(time_info.strftime("%H"))
            if now_hour >= night_start_time or now_hour < noon_start_time:
                now_state = "Night"
            elif now_hour < night_start_time and now_hour >= noon_start_time:
                now_state = "Noon"
            return now_state
        
        except Exception as e:
            logging.error("例外が発生しました： {}".format(e.args))
            raise RuntimeError(e.args) from e
    
    
    def _roll_dice(self):
        return random.randint(1,6)

    
class AutoTweet(BaseThread):
    """定期的に自動ツイートを行うクラス"""
    def thread_preparation(self, tweet_file, max_span=60*60*24, min_span=60*60*15):
        self.tweet_file=tweet_file
        self.min_update_span = min_span
        self.max_update_span = max_span
        self.countdown = random.randint(self.min_update_span, self.max_update_span)

        
    def loop_function(self):
        print("Auto Tweet 実行　（{}）".format(self.thread_name))
        logging.info("Auto tweet が実行されます。")
        command_type = noid_ct.STATUSES_UPDATE
        self.lock.acquire()
        try:
            self.request_reception(command_type)
            po.random_tweet(self.api, self.tweet_file)
            logging.info("Auto tweet が実行完了しました。")
        except:
            logging.error("例外発生 : 'AutoTweet'-'loop_function'内。ツイートできませんでした")
            print("ツイートできませんでした")
        finally:
            self.lock.release()
            self.cooltime = random.randint(self.min_update_span, self.max_update_span)
            

    def save_status_for_restart(self):
        return_dict = {
            self.thread_name:{
                "class_name":self.__class__.__name__,
                "countdown":self.countdown,
                "tweet_file":self.tweet_file,
                "min_update_span":self.min_update_span,
                "max_update_span":self.max_update_span
                }
            }
        return return_dict
        
    
    def thread_restart(self, thread_cache):
        
        self.tweet_file = thread_cache["tweet_file"]
        self.max_update_span = thread_cache["max_update_span"]
        self.min_update_span = thread_cache["min_update_span"]
        self.countdown= thread_cache["countdown"]
        self.start()



class TrackTweet(BaseThread):
    """定期的に、コンテンツ関連ワードを含むツイートを収集する機能"""
    def thread_preparation(self, search_word, save_file, get_tweet_num=10, update_span=60*15):
        self.search_word = search_word
        self.save_file = save_file
        self.get_tweet_num = get_tweet_num
        self.update_span = update_span
        
        self.since_id=0
        
    
    def loop_function(self):
        #Try一つにまとめたい
        command_type = noid_ct.SEARCH_TWEETS
        self.lock.acquire()
        try:
            self.request_reception(command_type)
        except:
            logging.warning("リクエストリソースが確保できませんでした(Track tweet)。")
            self.cooltime = 15*60
            self.lock.release()
            return
        else:
            self.lock.release()
            
        #以下、ツイート取得＆保存＆更新
        try:
            tweets = go.search_tweets(
                                    self.api,
                                    self.search_word,
                                    self.get_tweet_num,
                                    self.since_id)
            rwo.save_tweets_database(tweets, self.save_file)
            for tweet in tweets:
                if self.since_id < tweet.id:
                    self.since_id = tweet.id+1
        except Exception as e:
            logging.error("ツイートの取得、もしくは保存に失敗しました。\n error: {}".format(e.args))
            self.cooltime = 15*60
    
    
    def save_status_for_restart(self):
        return_dict = {
            self.thread_name:{
                "class_name":   self.__class__.__name__,
                "countdown":    self.countdown,
                "search_word":  self.search_word,
                "save_file":    self.save_file,
                "since_id":     self.since_id,
                "get_tweet_num":self.get_tweet_num,
                "update_span":  self.update_span
                }
            }
        return return_dict
        
    
    #↓　__init__の亜種として運用するべき。
    def thread_restart(self, thread_cache):
        self.countdown = thread_cache["countdown"]
        self.search_word = thread_cache["search_word"]
        self.save_file = thread_cache["save_file"]
        self.get_tweet_num = thread_cache["get_tweet_num"]
        self.update_span = thread_cache["update_span"]
        self.since_id= thread_cache["since_id"]
        print("since_id is : ",self.since_id)
        
        self.start()



class GetReply(BaseThread):
    """Botのツイートがリプライされたとき、それにリアクションする機能"""
    search_word = noid_ids.MY_SCREEN_NAME
    replyed_init_dict = {"default":{}, "IPP":{}, "Muscle":{}, "MeiScene":{}, "Opinion":{}}
    def init_setting(self, args):
        self.countdown = 5
        self.used_ids=list()
    
    def thread_preparation(self, max_id, get_tweet_num=10, update_span=30):
        self.max_id_mentioned=max_id
        self.max_id_commands=max_id
        self.get_tweet_num = get_tweet_num
        self.update_span = update_span
        self.cooltime = self.update_span
        self.countdown = self.cooltime
        self.before_is_night = None
        
        self.q = BaseThread.task_queue
        self.replyed_dict=copy.copy(GetReply.replyed_init_dict)
        self.IPP = noid_cmds.IPP(self.api)
        self.muscle = noid_cmds.Muscle(self.api)
        #self.mei_scene = noid_cmds.MeiScene(self.api)
        self.opinion = noid_cmds.CatchOpinion(self.api, self.q)
        self.today_random_value = random.random()
        self.so_mi_ne_flag=0
        
    def loop_function(self):
        command_type = noid_ct.MENTIONED_TIMELINE
        self.lock.acquire()
        try:
            self.request_reception(command_type)
        except:
            logging.error("リクエストリソースが枯渇しています")
            self.cooltime = 120
            self.lock.release()
            return
        else:
            self.lock.release()
        """以下はツイートの取得と処理"""
        try:
            """メンションに対するリアクション"""
            tweets = self.api.mentions_timeline(since_id=self.max_id_mentioned, include_rts=False)#←このinclude_rtsって、mentions_timelineのメソッドになくない？
            for tweet in tweets:
                if self.max_id_mentioned < tweet.id:
                    self.max_id_mentioned = tweet.id
                #自分のIDには反応しない
                if tweet.user.id==noid_ids.MY_USER_ID:
                    continue
                self._allocate(tweet, tweet.text)
        except Exception as e:
            logging.error("リプライ取得、もしくはリプライに失敗しました\n内容：{}".format(e.args))
            return
        """コマンドの探索"""
        try:
            tweets = go.search_tweets(
                                    self.api,
                                    GetReply.search_word,
                                    self.get_tweet_num,
                                    since_id=self.max_id_commands)
            for tweet in tweets:
                if self.max_id_commands < tweet.id:
                    self.max_id_commands = tweet.id
                if not tweet.user.id==noid_ids.MY_USER_ID:
                    self._allocate(tweet, tweet.text)
        except Exception as e:
            logging.error("コマンド取得、もしくはコマンド応答に失敗しました\n内容：{}".format(e.args))
            return
        self.cooltime=self.update_span


    def _allocate(self, tweet, text):
        try:
            if ("ハッシュタグ機能1" in text) or ("ハッシュタグ機能2" in text):
                if tweet.id in self.used_ids:
                    return
                self.IPP._tell_IPP(tweet, self.replyed_dict, self.today_random_value)
            elif "ハッシュタグ機能3" in text:
                if tweet.id in self.used_ids:
                    return
                self.muscle.tweet_today_training(tweet, self.replyed_dict)
            elif ("ハッシュタグ機能4" in text) or ("ハッシュタグ機能5" in text):
                if tweet.id in self.used_ids:
                    return
                noid_cmds.MeiScene.proccess_register_tweet(self.api, tweet, self.replyed_dict, self.q)
            elif ("ッシュタグ機能6" in text) or ("ッシュタグ機能7" in text):
                if tweet.id in self.used_ids:
                    return
                self.opinion.catch_opinion(tweet, self.replyed_dict)
                
            else:
                if tweet.id in self.used_ids:
                    return
                self._default_reply(tweet)
            self.used_ids.append(tweet.id)
            
        except Exception as e:
            self.used_ids.append(tweet.id)
            logging.error("エラーの起きたテキスト: "+text+"\n内容："+str(e.args))
            return
            
    
    def _default_reply(self, tweet):
        text_1=["デフォルト応答分(リストにする)"]
        text_2=["デフォルト応答分(リストにする)"]
        text_3=["デフォルト応答分(リストにする)"]

        user_id = tweet.user.id
        tweet_id = tweet.id
        
        today_reply_id = self.replyed_dict["default"].get(user_id)
        if today_reply_id==None:
            self.replyed_dict["default"][user_id]=1
            text=text_1[random.randint(0,3)]
        elif today_reply_id == 1:
            self.replyed_dict["default"][user_id]=2
            text=text_2[random.randint(0,4)]
        elif today_reply_id == 2:
            self.replyed_dict["default"][user_id]=3
            text=text_3[random.randint(0,4)]
        else:
            return
        
        try:
            tweet = self.api.update_status(status=text,
                              in_reply_to_status_id = tweet_id,
                              auto_populate_reply_metadata=True)
        except:
            return
        
    def morning_loutine(self):
        #朝いちばんに、リプライした人のリスト（辞書）をリセットする。
        self.replyed_dict.clear()
        self.replyed_dict=copy.copy(GetReply.replyed_init_dict)
        #処理したツイートIDのリストをクリア。
        self.used_ids.clear()
        self.used_ids=list()
        #そうみぃねぇフラグをリセット
        self.so_mi_ne_flag=0
        #今日の乱数を決める。
        self.today_random_value = random.random()
        
        
    def save_status_for_restart(self):
        return_dict = {
            self.thread_name:{"class_name":self.__class__.__name__,
                              "max_id":self.max_id}
            }
        return return_dict
        
    def thread_restart(self, thread_cache):
        pre_search = self.api.search(q = "ツイート", lang="ja", count="1", tweet_mode="extended")
        max_id = pre_search.max_id
        self.countdown= 30
        self.thread_preparation(max_id)
        self.start()
    
    
    
class ScheduleThread(BaseThread):
    """特定の時間に処理を行うスレッド"""
    def init_setting(self, args):
        self.tag_set = set()
        self.schedule = schedule.Scheduler()
        self.countdown = 20
    
    def loop_function(self):
        self.schedule.run_pending()
        self.cooltime = 20
        
    def scheduling_list_update(self):
        database_path = noid_fap.TWEET_DATABASE
        keyword = ReadKeyword()
        mainword_list, subword_list = keyword.read_keyword("list")
        self.lu = ListUpdate(self.api, self.lock, self.request_reception)
        self.schedule.\
            every().sunday.at("01:30").\
            do(self._job_list_update, database_path, mainword_list, subword_list).\
            tag("list_update")
        print("Schedule 'list_update'!!")
        self.tag_set.add("list_update")
    def _job_list_update(self, database_path, mainword_list, subword_list):
        try:
            lu_thread = threading.Thread(target=self.lu.aggr_score(self.database_path, self.lu_mainword_list, self.lu_subword_list))
            lu_thread.start()
        except Exception as e:
            logging.error("リストアップデートで例外発生：{}".format(e.args))
            return


    def scheduling_mei_scene_tweet(self):
        self.mst = noid_cmds.MeiScene(self.api)
        self.schedule.every().day.at("12:00").do(self._job_mei_scene_tweet).tag("mei_scene")
        self.schedule.every().day.at("18:30").do(self._job_mei_scene_tweet).tag("mei_scene")
        self.tag_set.add("mei_scene")
        print("Schedule 'mei_scene_tweet'!!")
    def _job_mei_scene_tweet(self):
        try:
            lu_thread = threading.Thread(target=self.mst.mei_scene_tweet())
            lu_thread.start()
        except Exception as e:
            logging.error("迷シーンツイートjob関数で例外発生：{}".format(e.args))
            return
    def _mst_debug(self):
        self.mst.mei_scene_tweet()
        
    def scheduling_anniv_tweet(self):
        self.anniv_tweet = noid_cmds.Anniversary(self.api)
        self.schedule.every().day.at("07:30").do(self.job_anniv_tweet).tag("anniv")
        self.tag_set.add("anniv")
        print("Schedule 'confirm_today_anniversary'!!")
    def job_anniv_tweet(self):
        self.anniv_tweet.confirm_today_anniversary()

    
    
    def close_schedule(self, tag=""):
        if tag == "":
            print("tagを入力しないコマンドは無効です。")
            return
        if tag == "all":
            self.schedule.alear()
        else:
            self.schedule.clear(tag)
            self.tag_set.remove(tag)
            
    def view_duty_schedule(self):
        print(self.tag_set)
    
    def kill_self_thread(self):
        self.schedule.clear()
        self.alive=False
        
    def save_status_for_restart(self):
        return_dict = {
            self.thread_name:{
                "class_name":   self.__class__.__name__,
                "tag_set":  self.tag_set
                }
            }
        return return_dict
    
    def thread_restart(self, thread_cache):
        self.tag_set = thread_cache["tag_set"]
        if "list_update" in self.tag_set:
            self.scheduling_list_update()
        if "anniv" in self.tag_set:
            self.scheduling_anniv_tweet()
        if "muscle" in self.tag_set:
            self.scheduling_muscle()
        self.start()
  
    

class QueueManage(BaseThread):        
    """TwitterのDM機能は新着上書き式なので、キューで調整する"""
    def init_setting(self, args):
        self.countdown = 90
        self.cooltime = 90
        self.q = BaseThread.task_queue
    #キューの中を確認し続ける
    def loop_function(self):
        try:
            #エラーなど、優先的に伝えたい項目
            if self.q["DM_1st"].empty() is False:
                self._send_dm("DM_1st")
                return
            #承認関連。これをいったん行わないと、次のメッセージが届かない
            elif self.q["DM_2nd"].empty() is False:
                self._send_meiscene_dm()
                return
            #特に急がない情報。２が全部なくなるまで通知されない。
            elif self.q["DM_3rd"].empty() is False:
                self._send_normal_dm()
                return
            else:
                pass
        except Exception as e:
            logging.error("QueueManagerでエラーが発生しました。\n内容：",e.args)
        
    def _send_normal_dm(self):
        text = self.q["DM_3rd"].get()
        self.api.send_direct_message(
            noid_ids.MASTER_ID, 
            text)
        
    #DMを送信する
    def _send_meiscene_dm(self):
        request_args =  self.q["DM_2nd"].get()
        #DM送信に必要なパラメータの取り出し
        reply_params = request_args["reply_params"]
        DM_params  = request_args["DM_params"]
        text                = DM_params["text"]
        user_id             = DM_params["user_id"]
        quick_reply_type    = DM_params["type"]
        quick_reply_options = DM_params["options"]
        callback_function   = DM_params["callback_func"]#次に実行してほしい関数
        #DMの送信
        sent_dm = self.api.send_direct_message(
            user_id, 
            text+"\n残り"+str(self.q["DM_2nd"].qsize()), 
            quick_reply_type = quick_reply_type, 
            quick_reply_options = quick_reply_options)
        #受付が完了したことをハートで通知する。
        self.api.create_favorite(reply_params["tweet_dict"]["tweet_id"])
        
        #マスターアカウントの返信を待つ
        while True:#回答をもらうまで回り続ける             
            #idを取得して、それ以降の返信を受け取るようにする。
            Since_id = sent_dm.id
            decision = self._pick_conclusion(Since_id)
            if decision==None:
                time.sleep(90)
                continue
            else:
                callback_function(self.api, decision, reply_params, DM_params)
                break
        """
        ↑
        今回は、この部分でしかDMを受け取らないためここで受信処理をしていたが、
        他のコマンドの処理などをするのであれば、もっと複雑な処理が必要となる。
        """
    
    def _pick_conclusion(self, since_id):
        try:
            ls = self.api.list_direct_messages(count=20)
            non_read_list=[]
            for i in ls:
                print("・",end="")#デバッグ用
                time.sleep(0.3)#デバッグ用
                if int(i.id) > int(since_id):
                    non_read_list.append(i)
                else:
                    break
        except Exception as e:
            logging.error("error! 内容："+e.args)
        #since_idを最新のIDにする。
        
        for l in range(len(non_read_list)-1, -1, -1):
            if int(ls[l].message_create["sender_id"]) != noid_ids.MASTER_ID:
                continue
            decision = ls[l].message_create["message_data"]["text"]
            if decision in ("承認","却下１","却下２","却下３","却下４","却下５"):
                return decision
        
        return None
        """次に、特定パターンの返信でなければ、無視して再び同じDMを送信するようにする"""
     
            