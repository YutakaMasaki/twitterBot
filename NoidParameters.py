
from os import path

MODE = ("TEST") #TEST or LIVE

class FileAndPath(object):
    
    
    PATH_GoodMorning_TWEET_FILE = (path.join("tweet_files","Tweet_Texts_GoodMorning.csv"))
    PATH_GoodNight_TWEET_FILE = (path.join("tweet_files","Tweet_Texts_GoodNight.csv"))
    PATH_AUTO_TWEET_FILE = (path.join("tweet_files","Auto_Tweet_Texts.csv"))
    PATH_AD_TWEET_FILE = (path.join("tweet_files","Advertise_Tweet_Texts.csv"))
    PATH_MACHIKADO_TWEET_FILE = (path.join("tweet_files","Machikado_Tweet.csv"))
    PATH_MUSCLE_TWEET_FILE = (path.join("tweet_files","Muscle_Tweet.csv"))
    
    
    CACHE_FILE = (path.join("Database","Cache.dat"))
    TWITTER_UPDATE_LIST = (path.join("DATABASE","FALSE_LIST.dat"))
    TWEET_DATABASE = (path.join("Database","Noid_database.db"))
    ANNIVERSALY_DATABASE = (path.join("Database","anniversary.csv"))
    
    RELATING_WORDS=(path.join("Database","Relation_words.csv"))
    
    if MODE == "LIVE":
        API_KEYS=(path.join("Database","Noid_api_keys.csv"))
    elif MODE == "TEST":
        API_KEYS=(path.join("Database","TestNoid_api_keys.csv"))
        
        
class csvKeys(object):
    TWEET_CSV_KEYS = ["id","media","text", "SumOfTweet","TweetRightBefore"]
    MEI_SCENE_CSV_KEYS = ["id","type","name","title","section","source","sub_source","path","tweeted"]
    STARTUP_TWEET_KEYS = ["id","discription","text","media","reply","tweeted"]
    
class IDs(object):
    if MODE == "LIVE":
        LIST_Lv1 = ("******************")#rリスト１
        LIST_Lv2 = ("******************")#
        LIST_Lv3 = ("******************")#
        LIST_Lv4 = ("******************")#
        MY_USER_ID = ("******************")
        MY_SCREEN_NAME = "@Noid"
        MASTER_ID = ("******************")
    elif MODE == "TEST":
        LIST_Lv1 = ("******************")#
        LIST_Lv2 = ("******************")#
        LIST_Lv3 = ("******************")#
        LIST_Lv4 = ("******************")#
        MY_USER_ID = ("******************")
        MY_SCREEN_NAME = "@noid"
        MASTER_ID = ("******************")
    
    
class CommandType(object):
    STATUSES_UPDATE = ({"type":"POST",
                      "resource_family":"create content", 
                      "end_point":"/statuses/update",
                      "num_of_req":1})
    SEARCH_TWEETS = ({"type":"GET",
                     "resource_family":"search",
                     "end_point":"/search/tweets",
                     "num_of_req":1})
    MENTIONED_TIMELINE = ({"type":"GET",
                           "resource_family":"statuses", 
                           "end_point":"/statuses/mentions_timeline", 
                           "num_of_req":1})
    
    LIST_MEMBERS = ({
        "type":"GET",
        "resource_family":"lists", 
        "end_point":"/lists/members", 
        "num_of_req":1})
    LIST_MEMBERS_CREATE_ALL = ({
        "type":"POST",
        "resource_family":"lists", 
        "end_point":"/lists/members/create_all", 
        "num_of_req":1})
    LIST_MEMBERS_DESTROY_ALL = ({
        "type":"POST",
        "resource_family":"lists", 
        "end_point":"/lists/members/destroy_all", 
        "num_of_req":1})
    
class PastTweet(object):
    URL_MT_1 = ""
    
    