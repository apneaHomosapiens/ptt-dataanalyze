# ptt-dataanalyze
Get content from ptt.cc, store it, look at it.

# What is this?
This is a mini-dedicated-singlefunction web crawler. It's sole purpose is to 
1. Get web page content from https://ptt.cc/bbs
2. Catagorize and store the content in json format.

# What are those content from ptt.cc?
ptt.cc is an forum basically. There are hundres of board each has different interest of topic, e.g. politics, baseball, gossipping, NBA, ...etc. The ones I'm interest of for now are AllTogether, marriage, Boy-Girl, stock and WomenTalk.

# How does this thing work?
Each board has its [boardname]/index.html. Each article of the board has its unique url. The way this script does is start from the index, traverse all articles in this index, then go to previous page, traverse all articles in this index, then go to previous page...so on and so forth until reaches bookmark.

Bookmark is updated and stored in a file after each iteration, it's a epoch time which is conveniently got from article key index.

The reason to keep a bookmark is because I want to continuously get new articles over time. Put this python script on Linux and use cronjob to run it every several minutes that'll do.

All articles of each board is stored in its json file for later use.

# Something kind of important
To run this you need python3.6, BeautifulSoup4 and urllib. Some others are default python module.

# How does the json look like?
[to do]

# What can you do with these data?
[to do]
