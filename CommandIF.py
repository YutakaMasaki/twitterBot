# -*- coding: utf-8 -*-
"""
Created on Sat Mar 28 12:59:06 2020
@author: Yu-ri
outline: CommandIFのメインクラスを作る。
"""

import tweepy
import threading
import time
import pickle
import logging
import csv
import os

#以下、自作ファイルより
import Commands as cmds
from Keyword import ReadKeyword
from Keyword import OAuth
from NoidParameters import FileAndPath as noid_fap
import NoidParameters

formatter = '%(levelname)s : %(asctime)s : %(lineno)d行 : %(message)s : %(pathname)s(%(lineno)s) : %(funcName)s'
logging.basicConfig(level=logging.INFO, format=formatter, filename="Noid.logdata")
logger = logging.getLogger(__name__)

class CommandIF():
    #すべてのCommandIFのインスタンス、スレッドで、リクエストマネージャーの関数や変数を共有する
    #また、リクエストマネージャーにアクセスする際はロックをかける。
    #よって、ロックされている間は他のすべての関数からのアクセスを停止するので、処理はなるべく短くする
    thread_dict = {}
    req_manager=None
    def __init__(self, api, night_sleep=True, manager_work=True):
        print("MODE is ",NoidParameters.MODE)
        self.api = api
        #最新のIDを取得しておく。
        try:
            pre_search = api.search(q = "ツイート", lang="ja", count="1", tweet_mode="extended")
            self.MAX_ID_WHEN_MAIN_START = pre_search[0].id
        except Exception as e:
            print("最初のツイート取得に失敗しました。機能を終了します。")
            print("エラー内容：",e.args)
            raise
        
        CommandIF.req_manager = RequestManagor(self.api, manager_work=manager_work)
        self.req_addr = CommandIF.req_manager
        time.sleep(3)#reqest_managerが起動してから、ほかのスレッドを起動したい
        if night_sleep==True:
            self.NP_thread = self._night_perception()
            
                  
    #昼夜を検知して、クラス変数を変更する。常駐スレッドで、1つしかインスタンス化されない。
    def _night_perception(self):
        thread_name = "NP"
        NP_thread = cmds.NightPerception(self.api, 
                                    thread_name, 
                                    self.req_addr.access_resource_lock, 
                                    self.req_addr.consume_requests)
        NP_thread.thread_preparation()
        NP_thread.start()
        print("'nigut perception' start working")
        return NP_thread
            
    
    #自動ツイートのクラスをインスタンスし、スレッド化
    def auto_tweet(self, file_path=noid_fap.PATH_AUTO_TWEET_FILE, thread_name="at1", min_span=60*60*30, max_span=60*60*48):
        self._name_check(thread_name)
        #スレッド共通の初期化（インスタンス化）
        at_thread = cmds.AutoTweet(self.api, 
                                    thread_name, 
                                    self.req_addr.access_resource_lock, 
                                    self.req_addr.consume_requests,
                                    night_sleep=True)
        at_thread.thread_preparation(file_path,
                                     max_span,
                                     min_span)
        at_thread.start()
        CommandIF.thread_dict.setdefault(thread_name,at_thread)#スレッドの辞書はCommandIFの大本でかんりしたほうがいいのでは？
    
    
    #ツイート検索＆保存をスレッド化
    def track_tweet(self, search_word=None, save_file=noid_fap.TWEET_DATABASE, thread_name="tt1", get_tweet_num=50):
        self._name_check(thread_name)
        if search_word is None:
            keyword = ReadKeyword()
            search_word = keyword.read_keyword("str") + "-filter:retweets"
            print(search_word)
        #スレッド共通の初期化（インスタンス化）
        tt_thread = cmds.TrackTweet(self.api, 
                                    thread_name, 
                                    self.req_addr.access_resource_lock, 
                                    self.req_addr.consume_requests)
        #スレッド固有のパラメータ設定
        tt_thread.thread_preparation(search_word,
                                     save_file,
                                     get_tweet_num,
                                     update_span=60*60)
        #スレッドスタート
        tt_thread.start()
        CommandIF.thread_dict.setdefault(thread_name, tt_thread)#スレッドの辞書はCommandIFの大本でかんりしたほうがいいのでは？
                
  
    #取得スレッドをもとにリストを更新する機能をスレッド化。
    #本質はスケジュール関数のスレッド化だけど、現状この機能しかないため、このネーミング。
    def scheduling(self):
        self._name_check("ST")
        #スレッド共通の初期化（インスタンス化）
        sd_thread = cmds.ScheduleThread(self.api, 
                                    "ST", 
                                    self.req_addr.access_resource_lock, 
                                    self.req_addr.consume_requests)
        """以下、スケジュールの登録"""
        sd_thread.scheduling_list_update()
        sd_thread.scheduling_anniv_tweet()
        sd_thread.scheduling_mei_scene_tweet()
        sd_thread.start()
        print("now duty schedule is ...\n\t",end="")
        sd_thread.view_duty_schedule()
        CommandIF.thread_dict.setdefault("ST", sd_thread)
  
        
    #自分に対するリプライを監視、特定のワードに反応してアクションを起こす。
    def react_mentioned(self, get_tweet_num=10, MODE="RELEASE"):
        self._name_check("RM")
        rm_thread = cmds.GetReply(self.api, 
                                  "RM", 
                                  self.req_addr.access_resource_lock, 
                                  self.req_addr.consume_requests,
                                  night_sleep=True)
        rm_thread.thread_preparation(max_id = self.MAX_ID_WHEN_MAIN_START)
        if MODE=="DEBUG":
            rm_thread.run()
        elif MODE=="RELEASE":
            rm_thread.start()
        else:
            print("unexpected mode is given")
        CommandIF.thread_dict.setdefault("RM", rm_thread)#スレッドの辞書はCommandIFの大本でかんりしたほうがいいのでは？

    def queue_work(self, MODE="RELEASE"):
        self._name_check("QT")
        qt_thread = cmds.QueueManage(self.api,
                                  "QT",
                                  self.req_addr.access_resource_lock, 
                                  self.req_addr.consume_requests,
                                  night_sleep=True)
        if MODE=="DEBUG":
            qt_thread.run()
        elif MODE=="RELEASE":
            qt_thread.start()
        else:
            print("unexpected mode is given")
        CommandIF.thread_dict.setdefault("QT", qt_thread)


    def _name_check(self, thread_name):
        if thread_name in CommandIF.thread_dict:
            raise RuntimeError("同じ名前のスレッドが存在しています。2つ以上作成できるスレッドであれば、スレッド名を変えてください。")
        
    
            
    def kill_resident_thread(self):
        self.req_addr.state["alive"]=False
        self.NP_thread.kill_self_thread()
        self.req_addr.manager_thread.join()
        self.NP_thread.join()
        
    #常駐スレッド以外を止める
    def kill_all_slave_thread(self, save_status=True):
        if save_status==True:
            self._save_now_status()
        for key in CommandIF.thread_dict.keys():
            CommandIF.thread_dict[key].kill_self_thread()
            CommandIF.thread_dict[key].join()
            print("'{}' thread is killed".format(key))
        CommandIF.thread_dict.clear()
            
    #中断機能のあるスレッド（thread_restart関数をオーバーロードしたクラスのスレッド）の、現在の情報を保存する
    def _save_now_status(self):
        import datetime as dt
        cache_dict = {"datetime":dt.datetime.today(), "data":{}}
            
        try:
            if os.path.isfile(noid_fap.CACHE_FILE) is True:
                os.remove(noid_fap.CACHE_FILE)
                logging.info("cache.dat ファイル一度削除しました") 
            for thread in CommandIF.thread_dict.values():
                state_data = thread.save_status_for_restart()
                if state_data is None:
                    continue
                cache_dict["data"].update(state_data)
            with open(noid_fap.CACHE_FILE, mode="wb") as cf:
                pickle.dump(cache_dict, cf)
                
        except Exception as e:
            raise RuntimeError(e.args) from e
    
    #中断した時の変数やパラメータを引き継いで、自動的に再開する。最大IDは更新する。
    def restart(self):
        if os.path.isfile(noid_fap.CACHE_FILE) is False:
            raise RuntimeError("CACHE_FILE doesn't exist")
        with open (noid_fap.CACHE_FILE, mode="rb") as cf:
            cache_dict = pickle.load(cf)
            
        for thread_name in cache_dict["data"].keys():
            try:
                cls = getattr(cmds, cache_dict["data"][thread_name]["class_name"])
                instance = cls(api = self.api,
                               name = thread_name,
                               lock = self.req_addr.access_resource_lock,
                               request_reception = self.req_addr.consume_requests)
                instance.thread_restart(cache_dict["data"][thread_name])
            except KeyError:
                print("'Key Error：予期しない要素で辞書を読み込まれました'")
                continue
            except:
                print("予期しないエラーです...関数：'restart'")
                continue
            else:
                #辞書に登録
                CommandIF.thread_dict.setdefault(thread_name, instance)
        
        try:
            os.remove(noid_fap.CACHE_FILE)
            print("リスタート完了。cache.dat ファイルを削除しました")
        except:
            print("ファイル操作のエラーです。...関数：'restart'")
            raise
    
    
    
#API制限に備え、各コマンドの残りリクエスト回数を1分ごとにアップデートして、
#各スレッドから要請があればリクエスト可能かどうかを調べて答える。そのたびに、リクエスト回数を消費する。
class RequestManagor(threading.Thread):
    
    def __init__(self, api, update_span=60*3, manager_work=True):
        threading.Thread.__init__(self)
        self.api = api
        self.update_span = update_span
        self.POST_resource=60
        self.manager_work=manager_work
        self.state={"alive":True}
        
#        resource_families = ()
#        self._fam_csv = ','.join(resource_families)        
        self.access_resource_lock = threading.Lock()
        if self.manager_work==True:
            self.access_resource_lock.acquire()
            self.remain_resource = self.api.rate_limit_status()
            self.access_resource_lock.release()
        
            self.manager_thread = threading.Thread(target=self._update_requests_remain, args=(self.state,))
            self.manager_thread.start()
            print("Manager start working")
        else:
            print("Manager doesn't work")
        
    def _update_requests_remain(self, state):
        logging.info("Request manager work on")
        countdown=0
        if self.update_span<30:
            self.update_span=30
            print("コマンド'api.rate_limit_status()'の更新時間が30秒以下だったため、30秒に変更されました。")
        #ここから処理ループ開始
        while state["alive"]==True:
            time.sleep(1)
            if countdown<=0:
                try:
                    now_resource = self.api.rate_limit_status()
                    self.access_resource_lock.acquire()
                    self.remain_resource = now_resource
                    self.access_resource_lock.release()
                except Exception as e:
                    logging.error("関数:'_update_requests_remain'でエラーが起きました。")
                    print("Error : ",e.args)
                finally:
                    countdown=self.update_span
            else:
                countdown -= 1
        print("manager gone home...")     
        return
    
    #外部からコマンド使用の申請が行われる。
    def consume_requests(self, command_type):
        #機能がOFFなら全部OK出す
        if self.manager_work==False:
            return True
        
        #メソッドが実行可能か調べる
        try:
            #POSTメソッドなら、ここで実行可能か調べる
            if command_type["type"] == "POST":
                if self._check_POST_resource(command_type) is False:
                    return False
            #GETメソッドなら、ここで実行可能か調べる
            elif command_type["type"] == "GET":
                if self.remain_resource["resources"][command_type["resource_family"]][command_type["end_point"]]["remaining"] <= 1+command_type["num_of_req"]:
                    logging.worning("リクエストのリソースがありません（コマンド内容:{}）".format(command_type))
                    raise RuntimeError ("例外発生　関数'consume_request 内容'リクエストリソースの枯渇'")
            
            #実行可能なら、リソースを消費して実行可能であることを伝える
            if command_type["type"] == "POST":
                self._consume_POST_resource(command_type)
                return True
            elif command_type["type"] == "GET":
                self.remain_resource["resources"][command_type["resource_family"]][command_type["end_point"]]["remaining"] -= command_type["num_of_req"]
                #print("remain commands is ",self.remain_resource["resources"][command_type["resource_family"]][command_type["end_point"]])
                return True        
        except:
            logging.error("リソースの確保に失敗しました")
            raise
        
            
    #現状、POSTメソッドへの制限は設けていない。
    def _check_POST_resource(self, one_command_type):
        #if self.POST_resource > 1:
        #    self.POST_resource -= 1
        return True
        #return False
    
    def _consume_POST_resource(self, one_command_type):
        return True
    
    
def get_running_thread():
    try:
        print("name\tclass")
        for key in CommandIF.thread_dict.keys():
            print("{}\t{}".format(key, CommandIF.thread_dict[key].__class__))
    except:
        print("No threads running")
    
def EXIT(save_status=True):
    app.kill_all_slave_thread(save_status)
    app.kill_resident_thread()
    print("killed all threads.")
    
def kill_thread(save_status=True):
    app.kill_all_slave_thread(save_status)
    
def helper():
    print("auto_tweet(thread_name='at1')\
              ...自動ツイートを行うスレッドを立ち上げます。")
    print("track_tweet(thread_name='tt1', get_tweet_num=100)\
              ...ツイートの自動取得を15分おきに行います。search_wordの初期値は、'keyword.csv'を編集すること")
    print("update_twitter_list()\
              ...毎週土曜日にリストの更新を行う。上に同じく、search_wordの初期値は、'keyword.csv'を編集すること")
    print("EXIT('save_status=True')...全スレッドを閉じます。'save_status=True'で、現在のスレッドステータスを次回に引き継ぎます。")
    print("restart()...前回の状態を引き継いで、前回動いていたスレッド（scheduler除く）を再開します。")


def all_set():
    #app.auto_tweet()
    #app.track_tweet()
    #app.scheduling()
    app.react_mentioned(MODE="DEBUG")
    #app.queue_work()
    #app.auto_tweet(file_path=noid_fap.PATH_AD_TWEET_FILE, 
    #               thread_name="ad_tweet",
    #               max_span=60*60*34,
    #               min_span=60*60*25)
    #app.auto_tweet(file_path=noid_fap.PATH_MUSCLE_TWEET_FILE, 
    #               thread_name="muscle_tweet",
    #               max_span=60*60*45,
    #               min_span=60*60*60)


#ココからメインルーチンスタート！
try:
    api = OAuth.get_oauth()
    app = CommandIF(api)
except:
    print("起動シーケンスでエラーが発生しました")
    exit()

print("API key 取得完了！\nコマンドインターフェース準備完了！\n'app.helper()'でコマンドを参照できます。")

if os.path.isfile(noid_fap.CACHE_FILE):
    print("前回実行していたスレッドのステータスが残っています。\n<インスタンス>.restart()で再開することを勧めます。")

all_set()
CommandIF.thread_dict["ST"]._mst_debug()