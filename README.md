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

The RDE is like any other open source software in that you may request or contribute to development features yourself. If you have a specific feature in mind, please feel free to file an issue and the development team will get to it as soon as possible. If you want to contribute to the project yourself, feel free to clone this repo and an admin will review your pull request. In terms of our development procedure, each feature will have its own forked branch, then a pull request will be made to incorporate the feature in the development branch. Features will be slowly integrated into the master branch release.

## Citation

`Parsons, S. & Sterner, G. (2020). Reddit Data Extractor. Available: https://github.com/Sterner-Labs/Reddit-Data-Extractor`

or in BibTeX

```tex
@misc{reddit-data-extractor,
  title={{reddit-data-extractor}: Reddit Data Extractor}, 
  url={https://github.com/Sterner-Labs/Reddit-Data-Extractor},
  note={https://github.com/Sterner-Labs/Reddit-Data-Extractor}, 
  author={
    Sean Parsons and 
    Glenn Sterner}, 
  year={2020},
} 
```


## Contact

If you would like to contact us with any questions or concerns, reach out below.

Glenn Sterner  
Assistant Professor of Criminal Justice  
Criminal Justice Research Center  
The Pennsylvania State University  
Abington Campus  
ges5098@psu.edu  
