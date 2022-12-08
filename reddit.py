import praw
import pandas as pd
import datetime as dt
import requests
from psaw import PushshiftAPI
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import copy
from tqdm import tqdm
import os
from flask import Flask, request, render_template, send_file
app = Flask(__name__)
# api = PushshiftAPI(reddit)

# parser = argparse.ArgumentParser(description='Enter the input subreddits and keywords text files for data extraction.')
# parser.add_argument('-s', dest='subreddit_file', help='This is the input subreddit text file path.', required=True)
# parser.add_argument('-k', dest='keyword_file', help='This is the input keyword text file path.', required=True)
# args = parser.parse_args()


'''
    RedditDataExtractor Class

    Contains all relevant methods and instance variables for processing. One RDE instance 
    is enough to pull all of the data from Reddit.

    client_id = 'KUv9fnWD9zXYiA'
    client_secret = 'K0g76ObWUHjR18GFXVXSU03Elag'


'''

#initial class
class RedditDataExtractor:

    def __init__(self, client_id, client_secret):
        self.subreddits = None
        self.keywords = None
        self.reddit = None
        self.initialize_Reddit(client_id, client_secret)
        self.api = PushshiftAPI()
        self.start_epoch = None
        self.end_epoch = None
        self.standardized_dict = {
            # these are the fields that both share
            'id': '',
            'author_id': '',
            'parent_id': '',
            'parent_author_id': '',
            'parent_author_name': '',
            'type': 'submission',
            'author': '',
            'body': '',
            'created_utc': '',
            'score': '',
            'stickied': None,
            'subreddit_id': '',
            # Now the fields for just submissions
            'title': '',
            'full_link': '',
            'media_only': None,
            'num_comments': 0,
            'over_18': None,
            'pinned': None,
            'retrieved_on': '',
            'score': None,
            'subreddit': '',
            'updated_utc': None,
            'date': '',
            'time': '',
            'url': '',
            # Now for the comment fields
            'distinguished': None,
            'edited': None,
            'is_submitter': None,
            'link_id': '',
            'relevance': 0
        }
        self.sub_cache = []
        self.comment_cache = []
        self.cache = {}
        self.total = 0
        self.list_of_data = []
        self.subcount = 0
        self.subtotal = 0

        # self.get_keywords_and_subreddits(args.subreddit_file, args.keyword_file)

    '''
        Purpose: This function reads in the input subreddits and keywords from text files provided by user.
        Input: the subreddit file path and the keyword file path
        Ouput: adds subreddits and keywords to instance attributes

    '''

    #to extract keywords and subreddits from text
    def get_keywords_and_subreddits(self, subreddit_file, keyword_file):

        with open(subreddit_file) as f:
            subreddits = f.read().splitlines()

        with open(keyword_file) as f:
            keywords = f.read().splitlines()

        self.keywords = keywords
        self.subreddits = subreddits

    #to extract keywords and subreddits from GUI
    def get_keywords_and_subreddits_from_form(self, subreddit_text, keyword_text):
        self.keywords = keyword_text.splitlines()
        self.subreddits = subreddit_text.splitlines()

    '''
        Purpose: Establish connection to Reddit API to extract data
        Input: arguments are two strings, client_id and client_secret, both configurable from Reddit
        Output: adds reddit instance connection to object instance attribute

    '''

    def initialize_Reddit(self, client_id, client_secret):
        session = requests.Session()
        session.verify = False

        self.reddit = praw.Reddit(client_id=client_id,
                                  client_secret=client_secret,
                                  user_agent='App',
                                  requestor_kwargs={'session': session})

    '''
        Purpose: conduct a throttled submission search using the PushShift API
        Input: arguments are two strings, the subreddit to search and the query parameter to search
        Output: Returns a list of submissions that contain the query in the particular subreddit

    '''

    def throttledSubmissionsSearch(self, subreddit, query):

        gen = self.api.search_submissions(after=self.start_epoch,
                                          before=self.end_epoch,
                                          subreddit=subreddit,
                                          # limit=1,
                                          # filter=['author', 'author_fullname', 'full_link',
                                          # 'id', 'num_comments', 'retrieved_on', 'title'],
                                          q=query)
        final = []
        list_of_subs = [i for i in list(gen)]
        for i in list_of_subs:
            new = copy.deepcopy(i.d_)
            try:
                new['author_id'] = i.author_fullname.split('_')[1]
            except:
                new['author_id'] = ''

            final.append(new)
        return final

    '''
        Purpose: conduct a throttled comment search using the PushShift API
        Input: arguments are two strings, the subreddit to search and the query parameter to search
        Output: Returns a list of submissions that contain the query in the particular subreddit

    '''

    def throttledCommentsSearch(self, subreddit, query):

        gen = self.api.search_comments(after=self.start_epoch,
                                       before=self.end_epoch,
                                       subreddit=subreddit,
                                       # limit=1,
                                       # filter=['submission'],
                                       q=query)

        return ([i.d_ for i in list(gen)])

    '''
    ################################################################################################################
        Here begins the standardization methods which take in a type of comment dictionary or object and 
        reduces it to be the same format as all of the other comments, or a standardized dict.
        This is because of the discrepencies of the different comment objects that are returned when
        making various Reddit API calls/Pushshift API calls
    ################################################################################################################
    '''

    '''
        Purpose: converts input comment into standardized format
        Input: comment dictionary to convert into standardized format
        Output: standard format comment

    '''

    def standardizeIndividualComment(self, comment):

        new_dict3 = copy.deepcopy(self.standardized_dict)
        new_dict3['type'] = 'comment'
        new_dict3['relevance'] = 1
        try:
            new_dict3['body'] = comment['body']
        except:
            pass
        try:
            new_dict3['author'] = comment['author']
        except:
            pass
        try:
            new_dict3['author_id'] = comment['author_id']
        except:
            pass
        try:
            new_dict3['created_utc'] = comment['created_utc']
        except:
            pass
        try:
            new_dict3['distinguished'] = comment['distinguished']
        except:
            pass
        try:
            new_dict3['edited'] = comment['edited']
        except:
            pass
        try:
            new_dict3['id'] = comment['id']
        except:
            pass
        try:
            new_dict3['is_submitter'] = comment['is_submitter']
        except:
            pass
        try:
            new_dict3['link_id'] = comment['link_id'].split('_')[1]
        except:
            pass
        try:
            new_dict3['parent_id'] = comment['parent_id'].split('_')[1]
        except:
            pass
        try:
            new_dict3['score'] = comment['score']
        except:
            pass
        try:
            new_dict3['stickied'] = comment['stickied']
        except:
            pass
        try:
            new_dict3['subreddit_id'] = comment['subreddit_id'].split('_')[1]
        except:
            pass

        return new_dict3

    '''
        Purpose: converts input comment object into standardized format. The input comment object for 
        this function is from traversing the comment subtree and is controlled by the while loop in 
        the extractData function.
        Input: comment dictionary to convert into standardized format
        Output: standard format comment

    '''

    def standardizeCurrentComment(self, currentComment):

        new_dict4 = copy.deepcopy(self.standardized_dict)
        new_dict4['type'] = 'comment'
        new_dict4['relevance'] = 1
        try:
            new_dict4['body'] = currentComment.body
        except:
            pass
        try:
            new_dict4['author'] = currentComment.author.author_fullname.split('_')[1]
        except:
            pass
        try:
            new_dict4['author_id'] = currentComment.author.id
        except:
            pass
        try:
            new_dict4['created_utc'] = currentComment.created_utc
        except:
            pass
        try:
            new_dict4['distinguished'] = currentComment.distinguished
        except:
            pass
        try:
            new_dict4['edited'] = currentComment.edited
        except:
            pass
        try:
            new_dict4['id'] = currentComment.id
        except:
            pass
        try:
            new_dict4['is_submitter'] = currentComment.is_submitter
        except:
            pass
        try:
            new_dict4['link_id'] = currentComment.link_id.split('_')[1]
        except:
            pass
        try:
            new_dict4['parent_id'] = currentComment.parent_id.split('_')[1]
        except:
            pass
        try:
            new_dict4['score'] = currentComment.score
        except:
            pass
        try:
            new_dict4['stickied'] = currentComment.stickied
        except:
            pass
        try:
            new_dict4['subreddit_id'] = currentComment.subreddit_id.split('_')[1]
        except:
            pass

        return new_dict4

    '''
        Purpose: helper function to determine whether comment's parent is submission or another comment, 
                 also hardcodes values that we know to be true
        Input: standardized comment dictionary
        Output: standardized comment dictionary with newly corrected fields

    '''

    def commentAuthorHelpAndFinalize(self, dictionary):
        if dictionary['parent_id'] == dictionary['link_id']:
            sub = self.reddit.submission(dictionary['link_id'])
            try:
                author = sub.author.author_fullname.split('_')[1]
            except:
                author = ''
            try:
                author_id = sub.author.id
            except:
                author_id = ''

        # It's a comment!
        else:
            parent_comment = self.reddit.comment(dictionary['parent_id'])
            try:
                author = parent_comment.author.name
            except:
                author = ''
            try:
                author_id = parent_comment.author.id
            except:
                author_id = ''

        dictionary['parent_author_name'] = author
        dictionary['parent_author_id'] = author_id
        dictionary['date'] = dt.datetime.fromtimestamp(dictionary['created_utc']).strftime('%d-%m-%Y')
        dictionary['time'] = dt.datetime.fromtimestamp(dictionary['created_utc']).strftime('%H:%M:%S')
        dictionary['relevance'] = 1

        return dictionary

    def set_timeSpan(self, start, end):
        if len(start) > 0:
            self.start_epoch = int(dt.datetime.strptime(start, '%Y-%m-%d').timestamp())
        else:
            self.start_epoch = int(dt.datetime(2005, 1, 1).timestamp())
        if len(end) > 0:
            self.end_epoch = int(dt.datetime.strptime(end, '%Y-%m-%d').timestamp())
        else:
            self.end_epoch = int(dt.datetime.strptime(dt.datetime.today().strftime('%Y-%m-%d'), '%Y-%m-%d').timestamp())


    def extractData(self):
        for subreddit in tqdm(self.subreddits):
            for keyword in self.keywords:
                submissions = self.throttledSubmissionsSearch(subreddit, keyword)
                for sub in submissions:
                    self.sub_cache.append(sub['id'])
                    self.subcount += 1
                    new_dict = copy.deepcopy(self.standardized_dict)
                    for key in sub.keys():
                        if key == 'selftext':
                            new_dict['body'] = sub['selftext']
                        if key == 'author':
                            try:
                                new_dict['author_id'] = sub['author'].id
                            except:
                                new_dict['author_id'] = ''
                        if key in ['parent_id', 'subreddit_id', 'link_id']:
                            new_dict[key] = sub[key].split('_')[1]
                        if key in new_dict.keys():
                            new_dict[key] = sub[key]
                        else:
                            pass
                    # Hard code parent ID values for submissions because there is no parent
                    new_dict['parent_author_id'] = ''
                    new_dict['parent_author_name'] = ''
                    new_dict['relevance'] = 1
                    new_dict['date'] = dt.datetime.fromtimestamp(new_dict['created_utc']).strftime('%d-%m-%Y')
                    new_dict['time'] = dt.datetime.fromtimestamp(new_dict['created_utc']).strftime('%H:%M:%S')
                    try:
                        self.cache[new_dict['id']] = [new_dict['author_id'], new_dict['author']]
                    except:
                        pass

                    self.list_of_data.append(new_dict)

                comments = self.throttledCommentsSearch(subreddit, keyword)

                for comment in comments:
                    if comment['id']:
                        if comment['link_id'] not in self.sub_cache and comment['id'] not in self.comment_cache:
                            new_dict3 = self.standardizeIndividualComment(comment)
                            currentComment = self.reddit.comment(comment['id'])
                            try:
                                # Conduct while loop to traverse up the tree of relevant parent comments to root
                                while currentComment.link_id != currentComment.parent_id:
                                    currentComment = self.reddit.comment(currentComment.parent_id)
                                    if currentComment.link_id not in self.sub_cache and currentComment.id not in self.comment_cache:
                                        new_dict4 = self.standardizeCurrentComment(currentComment)
                                        new_dict4 = self.commentAuthorHelpAndFinalize(new_dict4)
                                        self.comment_cache.append(currentComment.id)
                                        self.list_of_data.append(new_dict4)
                            except:
                                pass

                            # Add the submission of the Comment and also add it to the sub_cache

                            # Do logic to get ParentAuthorID and ParentAuthor
                            # It's a submission!

                            new_dict3 = self.commentAuthorHelpAndFinalize(new_dict3)
                            self.comment_cache.append(comment['id'])
                            self.list_of_data.append(new_dict3)

                self.createCSV(subreddit, keyword)
                self.list_of_data = []
            # print('Total for ' + subreddit + ' subreddit is ' + str(self.subtotal))
            self.subtotal = 0
        # print('Total number of entries: ' + str(self.total))


    #once the keywords are extracted, compile results into a downloadable CSV
    def createCSV(self, subreddit, keyword):
        data = pd.DataFrame(self.list_of_data)
        filename = subreddit + '_' + keyword + '.csv'
        # Get the directory of download folder
        current_dir = os.path.expanduser("~")+"/Downloads/"
        # Set the path
        abs_path = os.path.join(current_dir)
        if data.empty:
            # don't put it in a CSV file then!
            pass
        else:
           data.to_csv(abs_path + filename)
        self.total += len(data.index)
        self.subtotal += len(data.index)
        return send_file(path_or_file=abs_path+filename, as_attachment=True)
        #print('Just processed ' + filename + ' with a total of ' + str(len(data.index)) + ' entries')
        #time.sleep(5)


if __name__ == '__main__':
    app.run(debug=False,host='0.0.0.0')

@app.route('/', methods=['POST', 'GET'])
def start():
    return render_template('template.html')
@app.route('/run', methods=['GET', 'POST'])
def run():
    if request.method == 'POST':
        RDE = RedditDataExtractor(client_id='KUv9fnWD9zXYiA', client_secret='K0g76ObWUHjR18GFXVXSU03Elag')
        RDE.get_keywords_and_subreddits_from_form(request.form['subreddits'], request.form['keywords'])
        RDE.set_timeSpan(request.form['trip-start'], request.form['trip-end'])
        RDE.extractData()
        return render_template('downloaded.html')
