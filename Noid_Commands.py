# -*- coding: utf-8 -*-
"""
Created on Sat Jun  6 23:30:49 2020
@author: Yu-ri
noidアカウントのみで使えそうな特殊コマンド。
業界ネタがソースコード内に入っている
"""

import os
import time
import random
import logging
import datetime
from os import path
from html import unescape

from NoidParameters import IDs as noid_ids
from NoidParameters import csvKeys as noid_csv
from NoidParameters import FileAndPath as noid_fap
from BaseOrder import PostOrder as po
from BaseOrder import GetOrder as go
from BaseOrder import RWOrder as rwo


formatter = '%(levelname)s : %(asctime)s : %(message)s : %(pathname)s(%(lineno)s) : %(funcName)s'
logging.basicConfig(level=logging.INFO, format=formatter, filename="Noid.logdata") 
logger = logging.getLogger(__name__)
        



class IPP():
    def __init__(self, api):
        self.api = api
        
    def _tell_IPP(self, tweet, replyed_dict, random_value):
        try:
            user_id = tweet.user.id
            tweet_id = tweet.id
            user_name = tweet.user.name
            if "@" in user_name:
                user_name = user_name[:user_name.find("@")]
            
            #日に2回目以降は回答しないように。
            if "IPP" not in replyed_dict.keys():
                replyed_dict["IPP"][user_id] = 1
            else:
                today_reply_id = replyed_dict["IPP"].get(user_id)
            if today_reply_id==None:
                replyed_dict["IPP"][user_id]=1
            elif today_reply_id==1:
                text = "".format(user_name)
                replyed_dict["IPP"][user_id] = 2
                self.api.update_status(status=text,
                                       in_reply_to_status_id = tweet_id,
                                       auto_populate_reply_metadata=True)
            else:
                #"3回以降のコマンドのため無視"
                return
        except:
            raise
        
        IPP = int((user_id*(random_value+1))%1001)

        if IPP==1000:
            text_3 = "pattern1"
        elif IPP > 989:
            text_3 = "pattern2"
        elif IPP > 939:
            text_3 = "pattern3"
        elif IPP > 879:
            text_3 = "pattern4"
        elif IPP > 799:
            text_3 = "pattern5"
        elif IPP > 709:
            text_3 = "pattern6"
        elif IPP > 579:
            text_3 = "pattern7"
        elif IPP > 419:
            text_3 = "pattern8"
        elif IPP > 369:
            text_3 = "pattern9"
        elif IPP > 289:
            text_3 = "pattern10"
        elif IPP > 199:
            text_3 = "pattern11"
        elif IPP > 99:
            text_3 = "pattern12"
        elif IPP > 29:
            text_3 = "pattern13"
        elif IPP > 0:
            text_3 = "pattern14"
        elif IPP == 0:
            text_3 = "pattern15"
        else:
            text_3 = "pattern0"
        
        if IPP == 0:
            pass
        else:
            IPP = IPP/10 +1
        
        text_1 = user_name+" です"
        text_2 = "『"+str(int(IPP))+"』！\n\n"
        
        text = text_1 + text_2 + "\n" + text_3
        try:
            self.api.update_status(status=text,
                              in_reply_to_status_id = tweet_id,
                              auto_populate_reply_metadata=True)
        except:
            raise
        
        
class Anniversary():
    """記念日に登録された内容をツイートできる"""
    def __init__(self, api):
        self.api = api
    
    def confirm_today_anniversary(self):
        #記念日リストの取得
        try:
            anniv_list = rwo.open_file(noid_fap.ANNIVERSALY_DATABASE)
            today = datetime.date.today()
            for anniv in anniv_list:
                if not anniv["month"]==str(today.month):
                    continue
                if not anniv["day"]==str(today.day):
                    continue
                text_1 = anniv["text"]
                text_2 = anniv["additional text"]
                text = text_1 + "\n" + text_2
                folder_path = path.join("Database","media_anniv")
                media_list = []
                if anniv["media1"]!="":
                    media_list.append(path.join(folder_path, anniv["media1"]))
                if anniv["media2"]!="":
                    media_list.append(path.join(folder_path, anniv["media2"]))
                if anniv["media3"]!="":
                    media_list.append(path.join(folder_path, anniv["media3"]))
                if anniv["media4"]!="":
                    media_list.append(path.join(folder_path, anniv["media4"]))
                
                media_ids = po.media_upload(self.api,[anniv["media1"],anniv["media2"],anniv["media3"],anniv["media4"]])
                po.tweet(self.api, text, media_ids)
                break
            
        except Exception as e:
            logging.error("エラー内容：{}".format(e.args))
            print("エラー内容：{}".format(e.args))


    
class MeiScene():
    """クラス変数(定数で使う)を記載"""
    q = 0
    reply_options = [
            {"label": "承認",  "description": "登録します","metadata": "external_id_1"},
            {"label": "却下１", "description": "攻撃的・差別的な発言が含まれている","metadata": "external_id_2"},
            {"label": "却下２", "description": "画像、文章がリステと関係ない", "metadata": "external_id_3"},
            {"label": "却下３", "description": "中の人、外部コンテンツネタ", "metadata": "external_id_4"},
            {"label": "却下４", "description": "酷い下ネタなどが含まれる", "metadata": "external_id_5"},
            {"label": "却下５", "description": "スパム認定", "metadata": "external_id_6"},
            {"label": "却下６", "description": "同じ内容がすでに登録されている", "metadata": "external_id_7"},
            {"label": "却下７", "description": "その他の理由", "metadata": "external_id_8"}
         ]
    Restage_Charactors = ("天使","悪魔","先生","メイド長")
    Section_List = ("メインストーリー","原作ストーリー","キャラストーリー","イベントストーリー")
    ZENKAKU_SUJI = ("０","１","２","３","４","５","６","７","８","9")
    HANKAKU_SUJI = ("0","1","2","3","4","5","6","7","8","9")
    SUJI_ZEN2HAN = {"０":"0","１":"1","２":"2","３":"3","４":"4","５":"5","６":"6","７":"7","８":"8","9":"9"}
    NUM2ORDER    = {"1":"st","2":"nd","3":"rd","4":"th","5":"th","6":"th","7":"th","8":"th","9":"th","10":"th","11":"th","12":"th","13":"th","14":"th","15":"th","16":"th","17":"th"}

    def __init__(self, api):
        self.api = api
    
    def mei_scene_tweet(self, file=path.join("media_scene","Re_Scene.csv")):
        
        scene_list = rwo.open_file(file)
        scene_line_num = self._select_random_line_num(scene_list)
        text = self._make_text("main", selected_scene=scene_list[scene_line_num])
        re_text = self._make_text("reply")
        media_ids = self._upload_medias(scene_list[scene_line_num])
        
        try:
            tweet1 = po.tweet(self.api, text=text, media_ids = media_ids)
            #事後処理
            scene_list[scene_line_num]["tweeted"] = "1"
            rwo.save_file(file, scene_list, noid_csv.MEI_SCENE_CSV_KEYS)
            if random.randint(1,6)==6:
                po.tweet(self.api, text=re_text, reply_id=tweet1.id)
        except Exception as e:
            logging.error("ツイートに失敗しました。\n原因：{}".format(e.args))
        
        return


    def _select_random_line_num(self, scene_list):
        """まだつぶやいたことのないツイートの選出可能性を上げ、その後選出を行う"""
        try:
            #全体の持ち点算出ループ
            _sum=0
            for lis in scene_list:
                _sum += 1 + 9*(int(lis["tweeted"])==0)
            random_num = random.randint(1,_sum)
            
            #選出ループ
            _sum=0
            _id=0
            for lis in scene_list:
                _sum += 1 + 9*(int(lis["tweeted"])==0)
                if _sum <= random_num:
                    _id += 1
                    continue
                selected_num = _id
                break
        except Exception as e:
            logging.error("迷シーンツイート選択でエラーが発生しました。内容：{}".format(e.args))
            print("迷シーンツイート選択でエラーが発生しました。内容：{}".format(e.args))
            raise
        return selected_num


    def _upload_medias(self, selected_scene):
        """以下、パスの正規化。OS差を吸収。"""
        _path = selected_scene["path"]
        list_path = _path.split("/")#linux
        list_path = _path.split("\\")#windows
        folder_path = path.join(*list_path)
        
        """以下、画像のアップロード"""
        try:
            media_list = []
            media_ids = []
            for num in range(1,5):
                filepath = path.join(folder_path,(str(num) + ".jpg"))
                if path.isfile(filepath):
                    media_list.append(filepath)
                else:
                    break       
            media_ids = po.media_upload(self.api, media_list)
        except Exception as e:
            print("メディアアップデートに失敗しました。迷場面ツイートをキャンセルします。")
            logging.error("メディアアップデートに失敗しました。迷場面ツイートをキャンセルします。\n内容：{}".format(e.args))
            raise
        return media_ids
        
    
    def _make_text(self, text_type, selected_scene=None):
        if text_type=="main":
            resister_type   = selected_scene["type"]
            if resister_type == "A":
                charactor       = selected_scene["name"]
                title           = selected_scene["title"]
                section         = selected_scene["section"]
                source          = selected_scene["source"]
                sub_source      = selected_scene["sub_source"]
                #以下、ツイート文章作成
    #ココから下、タイトルだけツイートして、ほかはコマンドで聞けるようにする
                text0 = "#リ名言・迷シーン\n"
                if charactor != "":
                    text1 = "【発言者】 "+charactor+"\n"
                else:
                    text1=""
                if title != "":
                    text2 = "【タイトル】 "+title+"\n"
                else:
                    text2 = ""
                if section != "":
                    text3 = "【ソース】 "+section
                    if source != "":
                        text3 += (" -> "+source)
                        if sub_source != "":
                            text3 += (" -> "+sub_source)
                    text3 += "\n"
                else:
                    text3=""
                mei_text = text0+text1+text2+text3
            elif resister_type == "B":
              mei_text = "#名言・迷シーン\n" + selected_scene["title"]
            #mei_text = selected_scene["title"]#両方タイトルしかツイートしないなら、上をすべてコメントにしてこれだけにする。
            return mei_text

        elif text_type=="reply":
            text_list = list()
            text_list.append("test1")
            text_list.append("test2")
            text_list.append("test3")
            text_list.append("test4")
            text = text_list[random.randint(0,len(text_list)-1)]
            return text
        
        else:
            print("迷シーンのテキスト作成で謎のエラー")
            logging.error("迷シーンのテキスト作成で謎のエラー")
            raise
    
    
    
    """以下、登録申請を受けた時の処理"""
    
    def proccess_register_tweet(api, tweet, replyed_dict, dm_q):
        """ツイートの中身の取り出し"""
        tweet_dict = {
            "created" : tweet.created_at,
            "user_name" : tweet.user.name,
            "screen_name" : "@"+tweet.user.screen_name,
            "user_id" : tweet.user.id,
            "tweet_id" : tweet.id,
            "text" : unescape(tweet.text)#ココでHTML独特のエスケープシーケンスっぽい何かを元に戻している
            }
        print("迷シーンツイートの申請が来たよ！")
        print(tweet_dict["text"])
        
        try:
            #メディアの取り出し方だけ少し特殊
            tweet_dict["media_list"] = MeiScene._check_media(tweet)
            if tweet_dict["media_list"]==[]:
                raise RuntimeError("画像が張られてない")
            #コマンド受信の回数が超過していれば、返信を止める
            acception = MeiScene._check_today_reception(api, replyed_dict, tweet_dict)
            if acception == False:
                return
            
            if "#名言・迷シーン登録申請" in tweet_dict["text"]:
                register_type = "A"
            #1.要素のリスト化（返り値......[0]:【発言者】、[1]：【タイトル】、[2]：【ソース】）
                elements_list = MeiScene._pick_register_elements(tweet_dict["text"])
            #2.ソースのリストから、保存するメディアのパスを作成する。
                media_path = MeiScene._create_media_path(elements_list[2], tweet_dict["screen_name"])
            #RuntimeErrorは、警告文を出す時に使う
                
            elif "#名言・迷シーンそのまま申請" in tweet_dict["text"]:
                register_type = "B"
                #URLの削除
                url_start = tweet_dict["text"].find("https://")
                if url_start != -1:
                    _str = tweet_dict["text"][:url_start]
                    tweet_dict["text"] = _str
                #ハッシュタグの削除。
                strip_start_num = tweet_dict["text"].find("#名言・迷シーンそのまま申請")
                strip_end_num   = len("#名言・迷シーンそのまま申請")
                first_half_str  = tweet_dict["text"][:strip_start_num]
                latter_half_str = tweet_dict["text"][strip_end_num:]
                
                if len(latter_half_str)!=0:
                    latter_half_str = latter_half_str[1:]
                elements_list = [None, first_half_str+latter_half_str, [None]]
                media_path =  MeiScene._create_media_path(["その他"], tweet_dict["screen_name"])
      
            #キュースレッドに投げる
            MeiScene._increase_reception(replyed_dict, tweet_dict["user_id"], 5)
            url = "https://twitter.com/"+tweet.user.screen_name+"/status/"+str(tweet.id)
            DM_params = {
                "text"          :   "新しい応募が来てる\n"+url,
                "user_id"       :   noid_ids.MASTER_ID,
                "type"          :   "options",
                "options"       :   MeiScene.reply_options,
                "callback_func" :   MeiScene.note_conclusion
                }
            reply_params = {
                "tweet_dict":tweet_dict,
                "media_path":media_path,
                "elements_list":elements_list,
                "register_type":register_type
                }
            master_request_args = {
                "DM_params"     :DM_params,
                "reply_params"  :reply_params
                }
            print("acception! put data to 2nd queue.")
            dm_q["DM_2nd"].put(master_request_args)
                
            
        except RuntimeError as e:
            text = "エラー！\n内容："+e.args[0]
            po.tweet(api, text, reply_id=tweet_dict["tweet_id"])
            MeiScene._increase_reception(replyed_dict, tweet_dict["user_id"], 2)
        #その他のエラーが出た場合は即終了する
        except Exception as e:
            print("その他のエラーが発生しました")
            logging.error("ツイート取得でエラー！\n内容：{}".format(e.args))
            text = "内部処理エラーが発生"
            po.tweet(api, text, reply_id=tweet_dict["tweet_id"])
            return
    
        
        
    def _check_media(tweet):
        try:
            if "extended_entities" in str(tweet):
                return tweet.extended_entities["media"]
            else:
                return tweet.entities["media"]
        except:
            return []
            
    
    def _pick_register_elements(txt):
        """
        文字列処理の関数。
        もらったテキストを、一部整形やチェックして、要素ごとにリストにして返す。
        [0]:【発言者】
        [1]：【タイトル】
        [2]：【ソース】
        """
        """要素ごとの文章を取り出す"""
        try:
            speaker      = MeiScene._pick_text(txt,"【発言者】")
            title        = MeiScene._pick_text(txt,"【タイトル】")
            source_list  = MeiScene._pick_text(txt,"【ソース】")#ソースだけリストで帰ってくるよ！！
            #ソースの中身がない場合、即リターン。
            if source_list == None:
                return [speaker, title, source_list]
                
            """以下、セクションごとの処理"""
            """キャラストーリーの場合の処理"""
            if source_list[0] == "キャラストーリー":
                #スペースだけは削除しているよ
                striped_source = source_list[1].strip(" 　")#見えないけど、半角全角の空白を消している
                source_list[1] = striped_source
                if source_list[1] not in MeiScene.Charactors:
                    raise RuntimeError("『キャラストーリー』にキャラが指定されてない")
                    
                """メインストーリー、もしくは原作ストーリーの場合の処理"""
            elif source_list[0]=="メインストーリー" or source_list[0]=="原作ストーリー":
                #文字列の数値を取り出す
                tmp_str =""
                #全角英数字を直して、仮
                for _str in source_list[1]:
                    if _str in MeiScene.ZENKAKU_SUJI:
                        tmp_str += MeiScene.SUJI_ZEN2HAN[_str]
                    elif _str in MeiScene.HANKAKU_SUJI:
                        tmp_str += _str
                    else:
                        break
                if tmp_str == "" or int(tmp_str)>50:
                    raise RuntimeError("【ソース】の章番号が無効な数字")
                source_list[1] = tmp_str
                
                """イベントストーリーの場合の処理"""
            elif source_list[0] == "イベントストーリー":
                a = source_list[1]#KeyErrorだけ確認してスルー
                
                """どれでもなかった場合"""
            else:
                raise RuntimeError("【ソース】の第一セクションが無効")
                
        except KeyError as ke:
            #"サブセクションが書かれてない。警告後、このまま登録する"
            logging.error("key error?? 内容：{}".format(ke.args))
            raise RuntimeError("【ソース】の第二セクションが無効")
        except RuntimeError:
            raise
        except:
            #予期せぬエラーはそのまま上げる
            raise
        return [speaker, title, source_list]
    
    
    """メディア保存用のパスを作成する"""
    def _create_media_path(source_list, screen_name):
        #現在時刻の取得
        t3 = time.localtime(time.time())
        now_time = str(t3.tm_year)+str(t3.tm_mon)+str(t3.tm_mday)+"_"+str(t3.tm_hour)+str(t3.tm_min)+str(t3.tm_sec)
        #数字が埋まってるところまで埋める
        media_path = "media_scene"
        try:
            media_path = path.join(media_path, source_list[0])
            media_path = path.join(media_path, source_list[1])
            media_path = path.join(media_path, source_list[2])
            #類似度でのパスの検索等は、また問題があったら考える
        #あるところまで追加する。keyerrorが出たら抜ける、くらいのイメージ
        except IndexError:
            pass
        except Exception:
            raise
        finally:
            media_path = path.join(media_path, now_time+"_"+screen_name)
        return media_path
            
    
    """もらったデータをもとに、csvファイルに追記する"""
    def _save_csv(elements_list, media_path, register_type="A", file=path.join("media_scene","Re_Scene.csv")):
        #現在のファイルを読み込み
        scene_list = rwo.open_file(file)
        #保存用のコンテナを用意
        new_line={}
        #いったん空で登録。ディクショナリを完成させる
        for key in noid_csv.MEI_SCENE_CSV_KEYS:
            new_line[key] = ""
        #最下層のidに1足した数
        new_line["id"]          = int(scene_list[-1]["id"])+1
        new_line["type"]        = register_type
        new_line["section"]     = "その他" #Bグループの場合はこうなるので、あらかじめそのように入れておく
        new_line["title"]       = elements_list[1]
        new_line["path"]        = media_path
        new_line["tweeted"]     = 0
        try:
            if register_type=="A":#Bタイプの申請の場合は以下は記載しない
                new_line["name"]        = elements_list[0]
                new_line["section"]     = elements_list[2][0]
                new_line["source"]      = elements_list[2][1]
                new_line["sub_source"]  = elements_list[2][2]
        except IndexError:#インデックス違反をフラグに入力を終了する
            pass
        except Exception:
            raise
        scene_list.append(new_line)
        rwo.save_file(file, scene_list, noid_csv.MEI_SCENE_CSV_KEYS)
        pass
    
            
    def _pick_text(txt, element):
        if not element in txt:
            #発言者がいない→その他登録
            return ""
        
        try:
            start_place             = txt.index(element)
            expected_quote_place    = start_place+len(element)
            quote_place             = txt.index("『",start_place)
            unquote_place           = txt.index("』",quote_place)
            contents_text       = txt[quote_place:unquote_place+1]
        except:
            raise RuntimeError(element+"の項目が正しくない")
        if expected_quote_place != quote_place:
            raise RuntimeError(element+"の 『 がなんか違う")
        #『』に囲まれた文字列が0文字だった場合
        if unquote_place - quote_place == 1:
            raise RuntimeError(element+" に文字が入力されてない")
        """途中に改行を発見したらエラー"""
        if "\n" in contents_text:
            raise RuntimeError(element+" の文章中に改行が含まれてるか、』 がない")
    
        
        """以下、要素ごとの特殊処理"""
        if element == "【発言者】":
            contents = contents_text.strip("『』 ")#『』と空白を削除
            if contents not in MeiScene.Charactors:
                raise RuntimeError("【発言者】のキャラが知らない人")
        elif element=="【タイトル】":
            contents = contents_text.strip("『』")
            #pass
        elif element=="【ソース】":
            contents = MeiScene._devide_source(contents_text)
            #文字列の左右から空白を削除
            length = len(contents)
            for i in range(0,length):
                tmp = contents[i].strip()
                contents[i] = tmp
        return contents
    
    
    """【ソース】の要素は、セクションごとに区切られている。その区切りをリストに変換させる"""
    def _devide_source(contents_text):
        s_text = contents_text.strip("『』,")
        unquote_place = -2 #最初の文字の前に">>"がついていた場合、丁度-2になるため。後で足している。
        source_list = []
        try:
            #区切り文字で区切られた文字で分割。最後の』に着くまで繰り返す。
            while(5):
                quote_place = unquote_place+2
                unquote_place = s_text.find(">>",quote_place)#ここは見つからない可能性が多分にあるからfindを使ってる
                if unquote_place == -1:
                    source_list.append(s_text[quote_place:])#最後の文字列取得
                    break
                source_list.append(s_text[quote_place:unquote_place])
        except:
            raise
        return source_list
    
    """1日の登録数に制限を付ける。"""
    def _check_today_reception(api, replyed_dict, tweet_dict):
        tw_id = tweet_dict["tweet_id"]
        user_id = tweet_dict["user_id"]
        today_reply_id = replyed_dict["MeiScene"].get(user_id)
        if today_reply_id==None:
            replyed_dict["MeiScene"][user_id] = 0
        elif replyed_dict["MeiScene"][user_id]<15:
            return True
        elif replyed_dict["MeiScene"][user_id]<20:
            po.tweet(api, "今日はもう登録申請できないよ。",reply_id=tw_id)
            replyed_dict["MeiScene"][user_id] = 31
            return False
        elif replyed_dict["MeiScene"][user_id]>30:
            return False
        
    def _increase_reception(replyed_dict, user_id, add):
        replyed_dict["MeiScene"][user_id] += add
        
        
    """承認、もしくは却下された後の処理"""
    def note_conclusion(api, decision, reply_params, DM_params):
        print("note start!")
        for choice in MeiScene.reply_options:
            if choice["label"] != decision:
                continue
            if choice["label"] != "承認":
                text1 = "申請が却下されたヨ。\n"
                text2 = "【理由】 "+choice["description"]+"\n"
                text3 = "……ゴメンネ？"
                text = text1+text2+text3
            elif choice["label"] == "承認":
                t = [
                    "承認コメント１",
                    "承認コメント２",
                    "承認コメント３",
                    "承認コメント４"
                    ]
                text = t[random.randint(0,3)]
                #メディアのダウンロードを行う                
                os.makedirs(reply_params["media_path"])#パスを作成する。
                rwo.download_media(
                    api, 
                    reply_params["tweet_dict"]["media_list"], 
                    folder_path = reply_params["media_path"]
                    )
                #csvファイルにツイートの内容を保存する
                MeiScene._save_csv(
                    reply_params["elements_list"], 
                    reply_params["media_path"], 
                    register_type=reply_params["register_type"]
                    )
            else:
                logging.error("エラー0142")
                return
            
            logging.info("全行程完了！！")
            """最後に、「申請を受理したよ」のコメントと、replyed_dictの更新を行う"""
            po.tweet(api, text, reply_id = reply_params["tweet_dict"]["tweet_id"])



class CatchOpinion:
    """ハッシュタグで意見をもらった時に、反応する"""
    def __init__(self, api, q):
        self.api=api
        self.q = q
        
    def catch_opinion(self, tweet, replyed_dict):
        if self._check_today_opinion(tweet, replyed_dict)==False:
            return
        
        t=["お礼パターン１",
           "お礼パターン２"]
        text = t[random.randint(0,1)]
        try:
            self.api.create_favorite(tweet.id)
            po.tweet(self.api, text, reply_id=tweet.id)
        except:
            pass
        
        url = "https://twitter.com/"+tweet.user.screen_name+"/status/"+str(tweet.id)
        text = "提案が来てる\n"+url
        #"\nhttps://twitter.com/YURIKApqp/status/"+str(tweet_dict["tweet_id"]),
               
        
        self.q["DM_3rd"].put(text)
        print("acception! put data to 3rd queue.")
        
        
    
    def _check_today_opinion(self, tweet, replyed_dict):
        today_reply_id = replyed_dict["Opinion"].get(tweet.user.id)
        if today_reply_id==None:
            replyed_dict["Opinion"][tweet.id] = 1
            return True
        elif replyed_dict["Opinion"][tweet.user.id]<=3:
            replyed_dict["Opinion"][tweet.id] += 1
            return True
        elif replyed_dict["Opinion"][tweet.user.id]==4:
            po.tweet(self.api, "回数超過")
        elif replyed_dict["Opinion"][tweet.user.id]>=5:
            return False
        else:
            return False


class Muscle():
    """筋トレサポートツイート機能"""
    def __init__(self, api):
        self.api = api
    
    def tweet_today_training(self, tweet, replyed_dict):
        if self._check_today_muscle(tweet, replyed_dict)==False:
            return
        menu = self._select_training()          #トレーニング内容をkeyに入れたディクショナリを返している
        menu = self._decide_training_set_num(menu)
        text = self._make_text(menu)
        auto_re_text = self._select_reply_text(menu)
        try:
            post_tweet = po.tweet(self.api, text, reply_id=tweet.id)
            po.reply(self.api, post_tweet, auto_re_text)
        except Exception as e:
            logging.error("筋肉ツイート、もしくは筋肉自動リプライに失敗しました。\nerror内容：{}".format(e.args))
            raise
        
    def _check_today_muscle(self, tweet, replyed_dict):
        today_reply_id = replyed_dict["Muscle"].get(tweet.user.id)
        if today_reply_id==None:
            replyed_dict["Muscle"][tweet.id] = 1
            return True
        elif replyed_dict["Muscle"][tweet.user.id]==1:
            po.tweet(self.api, "筋トレコマンドは1日1回まで")
            replyed_dict["Muscle"][tweet.id] = 2
            return False
        elif replyed_dict["Muscle"][tweet.user.id]==2:
            return False
        else:
            return False
        
    def _select_training(self):
        #メニューは4つ以上に設定すること！（1～4のランダムな筋トレが選ばれるため。）
        max_train_num=3
        min_train_num=2
        menu_list = ["腹筋 20回","ﾊﾞｯｸｴｸｽﾃﾝｼｮﾝ 15回","腕立て伏せ","スクワット 15回","プランク 30秒","ダンベルカール 片手20回ずつ", "デッドバグ 15秒", "ランジ 片足15回ずつ"]
        if len(menu_list)<max_train_num:
            raise RuntimeError("筋トレメニュー数が最大メニュー数以下です。関数を終了します")
    #今日の筋トレ数を入力
        train_varietise = random.randint(min_train_num, max_train_num)
    #提示する筋トレの番号を、ランダムにかぶりなしで取得
        index_array = []
        while len(index_array) < train_varietise:
            index_num = random.randint(1, len(menu_list))
            if index_num in index_array:
                continue
            else:
                index_array.append(index_num)
    #番号→筋トレ名に変更
        train_name_dict={}
        for n in index_array:
            train_name_dict[menu_list[n-1]] = ""
            
        return train_name_dict
        
    
    def _decide_training_set_num(self, menu):
        #
        for train in menu.keys():
            train_set_num = random.randint(2,3)
            menu[train] = train_set_num
        return menu
        
        
    def _make_text(self, menu):
        text1 = "今日の筋トレはこれダヨ！\n\n"
        text2 = ""
        for train in menu.keys():
            text2 += train+"×"+str(menu[train])+"セット\n"
        
        text3 = self._select_comment(menu)

        
        return text1 + text2 + text3        
        
        
    def _select_comment(self, menu):
        train_sum = 0
        for set_num in menu.values():
            train_sum += set_num
            
        if train_sum == 4:
            text = "\nコメント１"
        elif train_sum == 5:
            text = "\nコメント2"
        elif train_sum == 6:
            text = "\nコメント3"
        elif train_sum == 7:
            text = "\nコメント１4"
        elif train_sum == 8:
            text = "\nコメント5"
        elif train_sum <= 9:
            text = "\nコメント6"
        else:
            text = "コメント0"
        return text
    
    def _select_reply_text(self, menu):
        
        text_list = [
            "ランダム再生のコメントをリスト形式で入れる"
            ]
        for name in menu.keys():
            if "腕立て伏せ" in name:
                additional_text = [
                    "ランダム再生のコメントをリスト形式で入れる
                    ]
                text_list.extend(additional_text)
            if "ダンベルカール" in name:
                additional_text = [
                    "ランダム再生のコメントをリスト形式で入れる
                    ]
                text_list.extend(additional_text)
            if "プランク" in name:
                additional_text = [
                    "ランダム再生のコメントをリスト形式で入れる
                    ]
                text_list.extend(additional_text)
            if "背筋" in name:
                additional_text = [
                    "ランダム再生のコメントをリスト形式で入れる
                    ]
                text_list.extend(additional_text)
            if "スクワット" in name:
                additional_text = [
                    "ランダム再生のコメントをリスト形式で入れる
                    ]
                text_list.extend(additional_text)
                
        re_text = text_list[random.randint(0,len(text_list)-1)]
        
        return re_text
            
            
    
    def favorite(self, tweet, replyed_dict):
        t1=time.strptime('18:00:00','%H:%M:%S')
        t2=time.strptime('23:00:00','%H:%M:%S')
        nn=time.strptime(time.strftime('%H:%M:%S'),'%H:%M:%S')
        if not (nn >= t1 and nn <= t2):
            return
        
        if "muscle" not in replyed_dict.keys():
            replyed_dict["muscle"]={tweet.user.id:1}
        else:
            today_reply_id = replyed_dict["muscle"].get(tweet.user.id)
            if today_reply_id==1:
                return
        try:
            re_tw = self.api.get_status(tweet.in_reply_to_status_id)
            if not ("#筋トレ支援ツイート" in re_tw.text) or ("このツイートに「筋トレしたよ」ってリプライしてね！" in re_tw.text):
                logging.info("筋トレしたよ、の報告が違うツイートにリプライされたため、無視した")
                return
            if not re_tw.created_at.day == datetime.date.today().day:
                logging.info("筋トレしたよ、の報告が過去のツイートにされたため、無視した")
                return
            #以下で実際の動作
            self.api.create_favorite(tweet.id)
            replyed_dict["muscle"][tweet.user.id]=1
        except Exception as e:
            logging.error("筋トレの元ツイートとふぁぼに失敗しました。error内容: ",e.args)




if __name__ == "__main__":
    #テストコード
    import tweepy
    CK = "********************"
    CS = "****************************************"
    AT = "****************************************"
    ATS = "****************************************"
    auth = tweepy.OAuthHandler(CK, CS)
    auth.set_access_token(AT, ATS)
    api = tweepy.API(auth)
    file_path = path.join("media_scene","Re_Scene.csv")
    
    app = MeiScene(api)
    app.mei_scene_tweet(file_path)