# Reddit-Data-Extractor

![alt text](https://github.com/Sterner-Labs/Reddit-Data-Extractor/blob/master/rdetool.png)


This is the official page of the Reddit Data Extractor. The Reddit Data Extractor or RDE, is a command line tool that allows users to extract data from Reddit in the form of organized CSV files. By providing a list of subreddits to scrape and a list of keywords to look for, the RDE tool returns all submissions and comments in the comment tree that are relevant to the keywords at hand. 


## Features

* Output files are easy-to-read CSV files
* Easy command line interface
* Can get data from multiple subreddits and keywords
* Comes with a Python virtual environment for dependencies
* Requires no knowledge of coding or data scraping to use


## Dependencies

There are two main ways of using the RDE tool. One way is to install all of the Python library dependencies individually. The other is to use the virtual environment. The individual library dependencies are listed below:

`
pandas
psaw
datetime
pprint
requests
urllib3
tqdm
argparse
`

Then, you will need to either install `git` to pull the files directly to your local machine or download the files directly from this repository. If you are using a virtual environment to run the RDE, then run the following command once you have pulled the repository files to you local machine:

`source venv/bin/activate`

Now you are ready to run the RDE!

## Usage

Once you have all of the dependencies in order, it is time to run the RDE extractor. The usage can be seen below. There are two command line arguments to the tool: an input text file containing the subreddits to search and the input text file containing the keywords to search for.

`usage: reddit.py [-h] -s SUBREDDIT_FILE -k KEYWORD_FILE`


## Contribution

## Citation

## Contact
