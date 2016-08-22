__copyright__ = "Copyright 2016, Leidos, Inc."
__license__ = "Apache 2.0"
__status__ = "Beta"
__year__ = "2016"
__note__ = "Based off of Dwayne V Campbell's news corpus builder"

from goose import Goose
import feedparser
from pprint import pprint
import sys
import os
import json
import io
from time import gmtime, strftime

from collections import defaultdict
# data bases
from pymongo import MongoClient
import sqlite3
import string
import urllib

class NewsCorpusGenerator(object):

    def __init__(self,corpus_dir,datastore_type='file',db_name='corpus.db', mongo_db_name='DomainModelCorpora', domain=None):
        '''
        Read links and associated categories for specified articles
        in text file seperated by a space

        Args:
            corpus_dir (str): The directory to save the generated corpus
            datastore_type (Optional[str]): Format to save generated corpus.
                                            Specify either 'file' or 'sqlite'.
            db_name (Optional[str]): Name of database if 'sqlite' is selected.
        '''

        self.g = Goose({'browser_user_agent': 'Mozilla','parser_class':'soup'})
        self.corpus_dir = corpus_dir
        self.datastore_type = datastore_type
        self.domain = domain
        # sqlite3 attributes
        self.db_name = db_name
        self.db = None
        # mongodb attributes
        self.mongo_db_name = mongo_db_name
        self.mongo_db = None
        self.mongo_client = None
        # self.mongo_db_collection_name = 'articles'
        if self.domain is None:
            self.mongo_db_collection_name = 'articles' # domain name
        else:
            self.mongo_db_collection_name = str(self.domain).replace(' ' , '_')
        self.mongo_db_collection =  None

        self.stats = defaultdict(int)

        self._create_corpus_dir(self.corpus_dir)

        if self.datastore_type == 'sqlite':
            self.db = self.corpus_dir + '/' + self.db_name
            self._set_up_db(self.db)
        if self.datastore_type == 'mongo':
            self.mongo_client = MongoClient('mongodb://mongo:27017/DomainModelCorpora')
            self._set_up_db_mongo()
    def _create_corpus_dir(self,directory):

        if not os.path.exists(directory):
            os.makedirs(directory)


    def read_links_file(self,file_path):
        '''
        Read links and associated categories for specified articles
        in text file seperated by a space

        Args:
            file_path (str): The path to text file with news article links
                             and domain

        Returns:
            articles: Array of tuples that contains article link & cateogory
                      ex. [('IPO','www.cs.columbia.edu')]
        '''

        articles = []
        with open(file_path) as f:
            for line in f:
                line = line.strip()
                #Ignore blank lines
                if len(line) != 0:
                    link,domain = line.split(' ')
                    articles.append((domain.rstrip(),link.strip()))

        return articles

    def uprint(self, *objects, sep=' ', end='\n', file=sys.stdout):
        enc = file.encoding
        if enc == 'UTF-8':
            print(*objects, sep=sep, end=end, file=file)
        else:
            f = lambda obj: str(obj).encode(enc, errors='backslashreplace').decode(enc)
            print(*map(f, objects), sep=sep, end=end, file=file)

    def asciiencode(self, *objects, sep=' ', end='\n'):
        enc = sys.stdout.encoding
        result = ''
        if enc == 'UTF-8':
            for object in objects:
                result += str(object)
        else:
            for object in objects:
                result += str(object).encode(enc, errors='backslashreplace').decode(enc)
        return result

    def generate_corpus(self,articles):

        # TODO parallelize extraction process
        print ( 'Extracting  content from links...')

        for article in articles:
            domain = self.asciiencode(article[0])
            link = article[1]
            print ("\n\nLINK:", link, " type(link) : ", type(link) )

            ex_article = None

            try:
                ex_article = self.g.extract(url=link)
            except Exception as e:
                print('failed to extract article.. (Exception :', e, ')')
                continue

            ex_title = self.asciiencode(ex_article.title)
            ex_body = self.asciiencode(ex_article.cleaned_text)
            print ("Article Title : ",  ex_title)
            print ("Article Body : ",  ex_body)

            if ex_body == '':
                self.stats['empty_body_articles'] += 1
                continue

            self._save_article({'title':ex_title, 'body': ex_body,
                                'timestamp' : strftime("%Y-%m-%d %H:%M:%S", gmtime()),
                                'domain':domain})

    def _save_article(self,clean_article):

        self.uprint ( "Saving article %s..." %(clean_article['title']) )

        if self.datastore_type == 'file':
            self._save_flat_file(clean_article)
        elif self.datastore_type == 'sqlite':
            self._save_to_db(clean_article)
        elif self.datastore_type == 'mongo':
            self._save_to_db_mongo(clean_article)
        else:
            raise Exception("Unsupported datastore type. Please specify file or sqlite")

    def _remove_punctuations(self,title):
        return "".join(char for char in title if char not in string.punctuation)

    def _save_flat_file(self,clean_article):

        directory = self.corpus_dir + '/' + clean_article['domain'].strip()

        # create domain directory
        if not os.path.exists(directory):
            os.makedirs(directory)
        filestem = self._remove_punctuations(clean_article['title']).replace(" ","_").strip()
        file_name = directory + '/' + filestem[0:64] + '.json'
        print ("File Name :", file_name)
        with io.open(file_name, 'w', encoding='utf-8') as f:
            f.write(str ( (json.dumps(clean_article, ensure_ascii=True)) ) )

    def _encode_query(self,query):
        return urllib.parse.quote(query)
    def google_news_search(self,query,domain_label,num=50):
        '''
        Searches Google News.
        NOTE: Official Google News API is deprecated https://developers.google.com/news-search/?hl=en
        NOTE: Google limits the maximum number of documents per query to 100.
              Use multiple related queries to get a bigger corpus.

        Args:
            query (str): The search term.
            domain_label (str): The domain to assign to the articles. These
                                  categories are the labels in the generated corpus

            num (Optional[int]): The numnber of results to return.

        Returns:
            articles: Array of tuples that contains article link & cateogory
                      ex. [('IPO','www.cs.columbia.edu')]
        '''

        url = 'https://news.google.com/news?hl=en&q='+self._encode_query(query) \
              +'&num='+str(num)+'&output=rss'
        rss = feedparser.parse(url)
        entries = rss['entries']
        articles = []

        for entry in entries:
            link = entry['link']
            articles.append((domain_label,link))
        return articles

###
# mongo
####
    def _set_up_db_mongo(self):
        self.mongo_db = self.mongo_client[self.mongo_db_name]
        self.mongo_db_collection = self.mongo_db[self.mongo_db_collection_name.replace(' ' , '_')]
        print ( 'Database [mongodb] ==> ' + self.mongo_db_name +'. Collection ==>' + str(self.mongo_db_collection) + ' Domain ==> ' + self.domain  )

    def _save_to_db_mongo(self,clean_article):
        self.mongo_db_collection.update(
            {'title' : clean_article['title']}
            ,clean_article
            ,upsert=True
        )

###
# sqlite
####
    def _set_up_db(self,db):
        if os.path.exists(db):
            print ( 'Database (' + str(db) +') exists, assume schema does, too.')
        else:
            print ( 'Need to create schema')
            print ( 'Creating schema...')
            conn = sqlite3.connect(db)
            cur = conn.cursor()
            cur.execute("create table articles (Id INTEGER PRIMARY KEY,domain, title,body)")
            cur.execute("CREATE UNIQUE INDEX uni_article on articles (domain,title)")
            conn.close()

    def _save_to_db(self,clean_article):
        conn = sqlite3.connect(self.db)
        with conn:
            cur = conn.cursor()
            try:
                cur.execute("INSERT INTO articles (Id,domain,title,body) VALUES(?, ?, ?,?)"
                    ,(None,clean_article['domain'],clean_article['title'],clean_article['body']))
            except sqlite3.IntegrityError:
                self.stats['not_insert_db'] += 1
                print ( 'Record already inserted with title %s ' %(clean_article['title']))

    def get_stats(self):
        return self.stats


if __name__ == '__main__':
    pass
