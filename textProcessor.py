#!/usr/bin/python

import gensim
import os
import codecs


class WikiIter(object):

    def __iter__(self, title, offset):

        title=title.replace(" ", "_")

        getid = True # can read id from doc
        gettime = False # have id ready to use, can read time from doc 
        gettext= False   # have an id ready to use
        process = False  # ready to use content
        writeText= False  # adding to current content
        
        while os.path.isfile('full_histories/'+title+'/'+title+'|'+offset+'.xml'):
            historyFile=codecs.open('full_histories/'+title+'/'+title+'|'+offset+'.xml', "r", "utf-8")
        
            line = historyFile.readline().strip()
            while line[:4] != "<id>":
                line=historyFile.readline().strip()

            for line in historyFile:
                line=line.strip()

                # Gets the next revision id
                if getid:
                    if line[:4] == "<id>":
                        rvid = line[4:-5]
                        getid=False
                        gettime=True

                if gettime:
                    if line[:11] == "<timestamp>":
                        timestamp = line[11:-12]
                        offset=timestamp
                        gettime = False
                        gettext=True

                # Have an id ready to use, looking for start of content
                if gettext:
                    if line[:5] == "<text":
                        content= ""
                        line = line.split('">')
                        if len(line) == 1:
                            line += [""]
                        line = line[1]+"\n"
                        gettext=False
                        writeText=True
        
                # Have reached start if content, looking for end
                if writeText:
                    if line[-7:] == "</text>":
                        content+=line[:-7]
                        writeText=False
                        process=True
                    else:
                        content+=line+"\n"
                

                if process:
                    getid=True
                    process=False
                    content = gensim.corpora.wikicorpus.filter_wiki(content)
                    yield rvid, timestamp, content

        historyFile.close()

class MyCorpus(object):
    def __iter__(self, wikiiter, dictionary):
        for (rvid, time, doc) in wikiiter:
            yield dictionary.doc2bow(doc.split())

corpus=MyCorpus()
wiki = WikiIter()
dictionary=gensim.corpora.Dictionary(content.lower().split() 
            for (rvid, timestamp, content) in wiki.__iter__("Mesostigma", "0"))
stoplist=set('for a of the and to in'.split())

stop_ids=[dictionary.token2id[stopword] for stopword in stoplist 
                if stopword in dictionary.token2id]
once_ids=[tokenid for tokenid, docfreq in dictionary.dfs.iteritems() if docfreq==1]
dictionary.filter_tokens(stop_ids+once_ids)
dictionary.compactify()
print(dictionary)
for vector in corpus.__iter__(wiki.__iter__("Mesostigma", "0"), dictionary):
    print vector
