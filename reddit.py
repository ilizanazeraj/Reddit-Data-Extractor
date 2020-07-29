import praw 
import pandas as pd
import datetime as dt
import json
from pprint import pprint
import requests
from psaw import PushshiftAPI
import time
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import copy
from tqdm import tqdm
import argparse
import os

#api = PushshiftAPI(reddit)

parser = argparse.ArgumentParser(description='Enter the input subreddits and keywords text files for data extraction.')
parser.add_argument('-s', dest='subreddit_file', help='This is the input subreddit text file path.', required=True)
parser.add_argument('-k', dest='keyword_file', help='This is the input keyword text file path.', required=True)
args = parser.parse_args()


class specialComment():

	def __init__(self, praw_comment=None):
		self.praw_comment = praw_comment
		self.comment_dict = {}
		self.comment_dict['subcomments'] = []
		self.comment_dict['childSpecialComments'] = []
		self.comment_list = []

	def commentToDict(self):
		if self.praw_comment.author:
			self.comment_dict['author'] = self.praw_comment.author.name
		else:
			self.comment_dict['author'] = 'Deleted'
		self.comment_dict['created_utc'] = self.praw_comment.created_utc
		self.comment_dict['id'] = self.praw_comment.id
		self.comment_dict['link_id'] = self.praw_comment.link_id
		self.comment_dict['parent_id'] = self.praw_comment.parent_id
		self.comment_dict['replies'] = self.praw_comment.replies
		self.comment_dict['body'] = self.praw_comment.body
		self.comment_dict['distinguished'] = self.praw_comment.distinguished
		self.comment_dict['edited'] = self.praw_comment.edited
		self.comment_dict['is_submitter'] = self.praw_comment.is_submitter
		self.comment_dict['score'] = self.praw_comment.score
		self.comment_dict['stickied'] = self.praw_comment.stickied
		self.comment_dict['subreddit_id'] = self.praw_comment.subreddit_id

def recurseCommentTree(treeObject):

	# Create current object and take attributes from passed in argument
	currentObject = specialComment()
	currentObject.praw_comment = treeObject.praw_comment
	currentObject.commentToDict()

	# If there are children, then turn them into special comments for the 
	#recursive function to work
	if currentObject.comment_dict['replies']:
		list_of_child_special_comments = []
		for praw_comment_object in currentObject.comment_dict['replies']:
			child_object = specialComment(praw_comment=praw_comment_object)
			child_object.commentToDict()
			list_of_child_special_comments.append(child_object)
		currentObject.comment_dict['childSpecialComments'] = list_of_child_special_comments

		for child_object in currentObject.comment_dict['childSpecialComments']:
			currentChild = recurseCommentTree(child_object)
			currentObject.comment_dict['subcomments'].append(currentChild.comment_dict)

	del currentObject.comment_dict['childSpecialComments']
	currentObject.comment_dict['replies'] = [i.id for i in currentObject.comment_dict['replies'].list()]
	return currentObject


def get_keywords_and_subreddits():

	#try:
	with open(args.subreddit_file) as f:
		subreddits = f.read().splitlines()
	#except:
	#	print('Error reading subreddit input file ' + args.subreddit_file + '.')



	#try:
	with open(args.keyword_file) as f:
		keywords = f.read().splitlines()

	#except:
	#	print('Error reading keyword input file ' + args.keyword_file + '.')



	#keywords = ['Heroin','Safe Use Site', 'SUS', 'Safehouse', 'SIS', 
	#		'Safe Injection Site', 'Supervised Injection', 'Overdose on site', 
	#		'Safe-injection site', 'Drug treatment center', 'Treatment', 'Opioid', 
	#		'Opiates', 'Prescription Opioid Painkillers', 'POPs', 'Dealer', 'Smack', 
	#		'Dope', 'Drug Dealer', 'Overdose', 'Narcan', 'Naloxone', 'OD', 'crackhead', 
	#		'junkie', 'zombie', 'crack head']


	#subreddits = ['Philadelphia', 'New Jersey', 'South Jersey', 'Sixers', 'Phillylist',
	#				'Pennsylvania', 'Pennsylvania_Politics', 'UrbanHell'                     
	#				'CamdenCounty', 'OurOverUsedVeins', 'Delco', 'Montco',
	#				'BucksCountyPA', 'Chester County']
	#				# 'Opiates', 'Opioids', 'Heroin',

	return keywords, subreddits

def initialize_Reddit():
	session = requests.Session()
	session.verify = False

	reddit = praw.Reddit(client_id='KUv9fnWD9zXYiA',
						client_secret='K0g76ObWUHjR18GFXVXSU03Elag',
						user_agent='App',
						requestor_kwargs={'session':session})
	return reddit


def timestamp_to_datetime(timestamp):
	'''
	'''

	return datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')


def throttledSubmissionsSearch(api, start_epoch, subreddit, query):

	gen = api.search_submissions(after=start_epoch,
								subreddit=subreddit,
								#limit=1,
								#filter=['author', 'author_fullname', 'full_link',
										#'id', 'num_comments', 'retrieved_on', 'title'],
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

def throttledCommentsSearch(api, start_epoch, subreddit, query):

	gen = api.search_comments(after=start_epoch,
								subreddit=subreddit,
								#limit=1,
								#filter=['submission'],
								q=query)

	return([i.d_ for i in list(gen)])


def getComments(submissionID, r):

	submission = r.submission(submissionID)

	#pprint(type(submission))
	#pprint(submission._d)
	#pprint(vars(vars(submission)['_reddit']['']))
	commentsFromSub = []
	#submission.comments.replace_more(limit=0)
	comment_dict = {}

	for comment in submission.comments:

		# If there are any subcomments to make up a tree of comments...
		if comment.replies:
			commentObj = specialComment(comment)
			commentObj.commentToDict()
			tree = recurseCommentTree(commentObj)

			# We need to do this for each nested node in the tree
			#del tree.comment_dict['childSpecialComments']
			#pprint(tree.comment_dict)
			#return tree.comment_dict
			#print(type(tree))
			commentsFromSub.append(tree.comment_dict)
			continue

		# Else there are no subcomments on this comment
		else:
			comment_dict = {}
			if comment.author:
				comment_dict['author'] = comment.author.name
			else:
				comment_dict['author'] = 'Deleted'
			comment_dict['created_utc'] = comment.created_utc
			comment_dict['id'] = comment.id
			comment_dict['link_id'] = comment.link_id
			comment_dict['parent_id'] = comment.parent_id
			comment_dict['replies'] = comment.replies.list()
			comment_dict['body'] = comment.body
			comment_dict['distinguished'] = comment.distinguished
			comment_dict['edited'] = comment.edited
			comment_dict['is_submitter'] = comment.is_submitter
			comment_dict['score'] = comment.score
			comment_dict['stickied'] = comment.stickied
			comment_dict['subreddit_id'] = comment.subreddit_id

			commentsFromSub.append(comment_dict)
			continue
		
	return commentsFromSub

def commentToDict(comment):
	comment_dict = {}
	comment_dict['author'] = comment.author
	comment_dict['created_utc'] = comment.created_utc
	comment_dict['id'] = comment.id
	comment_dict['link_id'] = comment.link_id
	comment_dict['parent_id'] = comment.parent_id
	comment_dict['replies'] = comment.replies.list()
	return comment_dict

def get_submissionID_from_comment(reddit, commentID):
	'''
	'''
	comment = reddit.comment(id=commentID)
	return(comment.link_id)


def getPushshiftData(submissionID, subreddit):
	url = 'https://api.pushshift.io/reddit/search/submission/?ids=' + submissionID
	print(url)
	r = requests.get(url)
	try:
		data = json.loads(r.text)
		return data['data']
	except:
		return None


def buildSubmissionCommentTree(submissionID, api):

	# Takes in a submission ID and builds a full document with all submission data and comments data
	results = list(api.search_submissions(ids=submissionID))



# Here begins the standardization methods which take in a type of comment dictionary or object and 
# reduces it to be the same format as all of the other comments, or a standardized dict.
# This is because of the discrepencies of the different comment objects that are returned when
# making various Reddit API calls





# The input of this function is a commentList that is retreived directly from the submission
def standardizeCommentList(commentList, standardized_dict):

	new_dict2 = copy.deepcopy(standardized_dict)
	for comment in commentList:

		
		new_dict2['type'] = 'comment'
		try:
			new_dict2['body'] = comment.body
		except:
			pass
		try:
			new_dict2['author'] = comment.author
		except:
			pass
		try:
			new_dict2['author_id'] = comment.author.id
		except:
			pass
		try:
			new_dict2['created_utc'] = comment.created_utc
		except:
			pass
		try:
			new_dict2['distinguished'] = comment.distinguished
		except:
			pass
		try:
			new_dict2['edited'] = comment.edited
		except:
			pass
		try:
			new_dict2['id'] = comment.id
		except:
			pass
		try:
			new_dict2['is_submitter'] = comment.is_submitter
		except:
			pass
		try:
			new_dict2['link_id'] = comment.link_id.split('_')[1]
		except:
			pass
		try:
			new_dict2['parent_id'] = comment.parent_id.split('_')[1]
		except:
			pass
		try:
			new_dict2['score'] = comment.score
		except:
			pass
		try:
			new_dict2['stickied'] = comment.stickied
		except:
			pass
		try:
			new_dict2['subreddit_id'] = comment.subreddit_id.split('_')[1]
		except:
			pass

	return new_dict2



# This function standardizes an individual comment dictionary retrevied from the comment specific API
def standardizeIndividualComment(comment, standardized_dict):

	new_dict3 = copy.deepcopy(standardized_dict)
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



# The input comment object for this function is from traversing the comment subtree and is controlled
# by the while loop in the main function
def standardizeCurrentComment(currentComment, standardized_dict):

	new_dict4 = copy.deepcopy(standardized_dict)
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

if __name__ == '__main__':
	#print(search_comments('opiates', 'philadelphia'))

	total = 0

	r = initialize_Reddit()

	# Declare a PushShiftAPI object so that we can make API calls
	api = PushshiftAPI()	

	# Declare a Reddit object in order to lookup submission IDs from comments
	reddit = initialize_Reddit()
	#print('hi')
	#results = getPushshiftData('t3_h9dkw', 'Philadelphia')

	#pprint(results)

	# Make a start epoch which represents how far back the scraping should go
	start_epoch=int(dt.datetime(2005, 1, 1).timestamp())

	# Start the loops for subreddit and keywords here

	# Cache the already processed submissions
	#processed_submissions = []

	'''
	shared mappings:

	submission  comment

	author -> author
	created_utc -> created_utc
	selftext -> body
	id -> id
	score -> score
	stickied -> stickied
	subreddit_id -> subreddit_id


	'''
	standardized_dict = {
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



	keywords, subreddits = get_keywords_and_subreddits()


	#submissions = throttledSubmissionsSearch(api, start_epoch, 'Philadelphia', 'Safe Use Site')

	# Syntax for cache is id: [parent_author_id, parent_author_name]
	cache = {}

	# Build simple record of all submissionIDs so we can reference later
	sub_cache = []
	comment_cache = []

	for subreddit in tqdm(subreddits):
		subtotal = 0
		for keyword in keywords:
			submissions = throttledSubmissionsSearch(api, start_epoch, subreddit, keyword)
			list_of_data = []

			subcount = 0
			for sub in submissions:
				sub_cache.append(sub['id'])
				subcount += 1
				new_dict = copy.deepcopy(standardized_dict)
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
					cache[new_dict['id']] = [new_dict['author_id'], new_dict['author']]
				except:
					pass

				# Also time to add the author info from the submission to our cache

				list_of_data.append(new_dict)
				subObj = r.submission(sub['id'])
				subObj.comments.replace_more(limit=0)
				new_dict2 = standardizeCommentList(subObj.comments.list(), standardized_dict)
				

				# Now do the parentID logic/lookup 
				try:
					cache[new_dict2['id']] = [new_dict2['author_id'], new_dict2['author']]
				except:
					pass

				if new_dict2['parent_id'] in cache.keys():
					new_dict2['parent_author_name'] = cache[new_dict2['parent_id']][1]
					new_dict2['parent_author_id'] = cache[new_dict2['parent_id']][0]
		

				if new_dict2['created_utc'] != '':
					new_dict2['date'] = dt.datetime.fromtimestamp(new_dict2['created_utc']).strftime('%d-%m-%Y')
					new_dict2['time'] = dt.datetime.fromtimestamp(new_dict2['created_utc']).strftime('%H:%M:%S')
					new_dict2['relevance'] = 1
					list_of_data.append(new_dict2)

				else:
					pass




			comments = throttledCommentsSearch(api, start_epoch, subreddit, keyword)


			for comment in comments:
				if comment['link_id'] not in sub_cache and comment['id'] not in comment_cache:
					new_dict3 = standardizeIndividualComment(comment, standardized_dict)

					currentComment = r.comment(comment['id'])

					try:
						# Conduct while loop to traverse up the tree of relevant parent comments to root
						while currentComment.link_id != currentComment.parent_id:

							currentComment = r.comment(currentComment.parent_id)
						
							if currentComment.link_id not in sub_cache and currentComment.id not in comment_cache:
								
								new_dict4 = standardizeCurrentComment(currentComment, standardized_dict)

								if new_dict4['parent_id'] == new_dict4['link_id']:
									sub = r.submission(new_dict4['link_id'])
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
									parent_comment = r.comment(new_dict4['parent_id'])
									try:
										author = parent_comment.author.name
									except:
										author = ''
									try:
										author_id = parent_comment.author.id
									except:
										author_id = ''

								new_dict4['parent_author_name'] = author
								new_dict4['parent_author_id'] = author_id
								new_dict4['date'] = dt.datetime.fromtimestamp(new_dict4['created_utc']).strftime('%d-%m-%Y')
								new_dict4['time'] = dt.datetime.fromtimestamp(new_dict4['created_utc']).strftime('%H:%M:%S')
								new_dict4['relevance'] = 1
								comment_cache.append(currentComment.id)

								list_of_data.append(new_dict4)

					except:
						pass


					# Add the submission of the Comment and also add it to the sub_cache

					# Do logic to get ParentAuthorID and ParentAuthor
					# It's a submission!
					if new_dict3['parent_id'] == new_dict3['link_id']:
						sub = r.submission(new_dict3['link_id'])
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
						parent_comment = r.comment(new_dict3['parent_id'])
						try:
							author = parent_comment.author.name
						except:
							author = ''
						try:
							author_id = parent_comment.author.id
						except:
							author_id = ''

					new_dict3['parent_author_name'] = author
					new_dict3['parent_author_id'] = author_id
					new_dict3['date'] = dt.datetime.fromtimestamp(new_dict3['created_utc']).strftime('%d-%m-%Y')
					new_dict3['time'] = dt.datetime.fromtimestamp(new_dict3['created_utc']).strftime('%H:%M:%S')
					new_dict3['relevance'] = 1
					comment_cache.append(comment['id'])

					list_of_data.append(new_dict3)


					# Conduct comment search and be strategic about which comments are being selected
					# Search all comments for keyword on subreddit
					# Take list of comments
					# For each comment, check and see if the submission it is from is already taken from above analysis, not here
					# If so, ignore
					# If a unique subcomment, take this comment and all comments above it in the comment tree



			data = pd.DataFrame(list_of_data)


			filename = subreddit + '_' + keyword + '.csv'

			current_dir = os.path.dirname(__file__) 
			rel_path = 'data/'
			abs_path = os.path.join(current_dir, rel_path)

			if data.empty:
				# don't put it in a CSV file then!
				pass
			else:
				data.to_csv(abs_path + filename)

			total += len(data.index)
			subtotal += len(data.index)

			print('Just processed ' + filename + ' with a total of ' + str(len(data.index)) + ' entries')
			time.sleep(5)
		print('Total for ' + subreddit + ' subreddit is ' + str(subtotal))

	print('Total number of entries: ' + str(total))

	#comments = getPushshiftData('3dr4vo', 'Philadelphia')

	#pprint(comments)
	#pprint(submissions)
	#print(len(submissions))
	'''
	counter = 0
	for submission in submissions:
		sub_id = submission['id']
		comments = getPushshiftData(sub_id, 'Philadelphia')
		print('###########SUB Below##############')
		pprint(submission)
		if not comments:
			comments = []

		counter += (1 + len(comments))

	print(counter)

	'''
	'''
	#Get all initial submissions which contain the keyword in the given subreddit
	submissions = throttledSubmissionsSearch(api, start_epoch, 'Philadelphia', 'heroin')

	with open('submissions.pkl', 'wb') as f:
		pickle.dump(submissions, f)
	print('dumped')
	# Build list of unique submissionIDs to eventually make a set
	original_sub_IDs = [i['id'] for i in submissions]

	#delete submissions from memory because we will have to get them again anyway

	#Now search for comments pertaining to the keyword and subreddit
	independent_comments = throttledCommentsSearch(api, start_epoch, 'Philadelphia', 'heroin')

	submissionIDs_from_independent_comments = []

	# Now retrieve the submissionIDs for all the comments
	print('total number of comments are: ' + str(len(independent_comments)))
	counter = 0
	for comment in independent_comments:
		submissionIDs_from_independent_comments.append(get_submissionID_from_comment(reddit, comment['id']))
		
		if counter % 20 == 0:
			print('Went through ' + str(counter) + ' comments thus far.')

		counter += 1

	# Make a list of the total submissionIDs from comments and regular submission search
	all_ids = original_sub_IDs + submissionIDs_from_independent_comments

	# Make a unique set of the total submissionIDs from comments and regular submissions
	unique_ids = list(set(all_ids))
	print('There are '+ str(len(unique_ids)) + ' unique submissions with this keyword and subreddit')
	# Initialize the empty list of submissions with their comments


	with open('unique_ids.pkl', 'wb') as f:
		pickle.dump(unique_ids, f)
	'''
		
	#with open('unique_ids.pkl', 'rb') as f:
		#unique_ids = pickle.load(f)

	#documents = []
	#for uniq in unique_ids:
		#temp_dict = {}
		#temp_dict = getPushshiftData(uniq, 'Philadelphia')
		#temp_dict['comments'] = getComments(uniq, reddit)
		#documents.append(getPushshiftData(uniq, 'Philadelphia'))

	#data = {'data': documents}

	#with open('TESTOUTPUT.json', 'w') as f:
		#json.dump(data, f)

	#keywords, subreddits = get_keywords_and_subreddits()
	

	#tree = build_tree(keywords, subreddits)

	#pprint(tree)
	# For reddit in subreddits:
		# data = {submissionID: [commentIDs, commentIDs], }
		# search specific subreddit for submissions containing query
			# Add relevant positive search results
			# Grab all comment IDs from positive submissions
		#search all comments in subreddit for query
			# Check if submissionID of comment already exists
				#If so, skip it
				# If not, add it
		#Continue to iterate through each subreddit, adding more data to the data dict
'''
 Schema of final tree:
		{data:
				{philadelphia: 
						{opiates: 
								{submissionID: [commentIDs, commentIDs, commentIDs],
								submissionID: [commentIDs, commentIDs, commentIDs],
								},
						 heroin: 
						 		{submissionID: [commentIDs, commentIDs, commentIDs],
								submissionID: [commentIDs, commentIDs, commentIDs],
								},
						},


				new Jersey: 
						{opiates: 
								{submissionID: [commentIDs, commentIDs, commentIDs],
								submissionID: [commentIDs, commentIDs, commentIDs],
								},
						 heroin: 
						 		{submissionID: [commentIDs, commentIDs, commentIDs],
								submissionID: [commentIDs, commentIDs, commentIDs],
								},
						}
				}
		 }

'''

	#Eventually, sweep through the dictionary and populate the data with text and author data
	# Output JSON files or CSV files or to a Database






############################################### OLD CODE ##################################################################



# def search_submissions(query, subreddit, size=1000):
# 	'''
# 		Summary: performs a search based on a query and a subreddit in order to 
# 				 return a list of all submissionID

# 		Input: query (string), subreddit (string)

# 		Output: list_of_submissions (list)

# 	'''

# 	url = 'https://api.pushshift.io/reddit/search/submission/'
# 	params = {'q': query, 
# 			  'size': str(size),
# 			  'subreddit': subreddit}
# 	response = requests.get(url, params=params)
# 	data = json.loads(response.text)
# 	pprint(data)
# 	list_of_submission_ids = [dictionary['id'] for dictionary in data['data']]
# 	return list_of_submission_ids



# def search_comments(query, subreddit, size=100000):
# 	'''
# 	'''
# 	url = 'https://api.pushshift.io/reddit/search/comment/'
# 	params = {'q': query,
# 			  'size': str(size),
# 			  'subreddit': subreddit}
# 	response = requests.get(url, params=params)
# 	data = json.loads(response.text)
# 	list_of_comment_ids = [dictionary['id'] for dictionary in data['data']]
# 	return list_of_comment_ids



# def check_for_dups(submission_dict):
# 	'''
# 	'''
# 	pass

# def extract_author_data():
# 	'''
# 	'''
# 	pass


# def build_tree(keywords, subreddits):
# 	'''
# 		Summary: Builds a tree holding all the results of the keyword search on
# 				 each of the different subreddits.

# 		Input:

# 		Output:

# 	'''
# 	reddit = initialize_Reddit()
# 	data = {}
# 	for subreddit in subreddits:
# 		data[subreddit] = {}
# 		for keyword  in keywords:
# 			data[subreddit][keyword] = {}
# 			submissionIds = search_submissions(keyword, subreddit)
# 			commentIds = search_comments(keyword, subreddit)
# 			other_submission_ids = [get_submissionID_from_comment(reddit, commentId) for commentId in commentIds]
# 			all_sub_ids = submissionIds + other_submission_ids
# 			all_sub_ids = set(all_sub_ids)
# 			for sub_id in all_sub_ids:
# 				data[subreddit][keyword][sub_id] = get_comments_from_submission(sub_id)
# 	return data

'''

start_epoch = int(dt.datetime(2017,1,1).timestamp())

#example = list(api.search_submissions(after=start_epoch,
							#subreddit='philadelphia',
							#filter=['url', 'body', 'author', 'title', 'subreddit'],
							#limit=1000))


example = api.search_comments(q='safe use site', subreddit='philadelphia')
example_submission = api.search_submissions(q='safe use site', subreddit='philadelphia')

count = 0
for i in example_submission:
	print(i)
	#date = dt.datetime.fromtimestamp(i.created_utc)
	#print(date)
	print()
	print()
	count += 1

print(count)

'''


# def get_comments_from_submission(submissionID):
# 	'''
# 	'''
# 	url = 'https://api/pushshift.io/reddit/submission/comment_ids/' + submissionID
# 	response = requests.get(url)
# 	data = json.loads(response.text)
# 	list_of_comment_ids = data['data']
# 	return list_of_comment_ids




# def getNestedComments(comment):
# 	currentObject = recursiveComment(comment)
	
# 	#comment_dict['replies'] = comment.replies.list()
# 	if currentObject.comment_dict['replies']:
# 		for child in currentObject.comment_dict['replies']:
# 			currentChild = getNestedComments(child)
# 			currentObject.comment_dict['replies'] = currentChild.comment_dict
	
# 	return currentObject.comment


# def nestedComments(obj):

# 	rcomment = recursiveComment()
# 	rcomment.comment = obj.comment
# 	rcomment.commentToDict()
# 	if rcomment.comment_dict['replies']:
# 		for children in obj.comment_dict['replies']:
# 			rcomment.comment_dict['subcomments'].append()

