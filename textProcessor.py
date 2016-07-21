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
    def __init__(self, wikiiter, dictionary):
        self.wikiiter=wikiiter
        self.dictionary=dictionary
    def __iter__(self):
        for (rvid, time, doc) in self.wikiiter:
            yield self.dictionary.doc2bow(doc.split())


def saveDictionary(title):
    """
    """
    if not os.path.isdir('dictionaries'):
        os.mkdir('dictionaries')

    wiki = WikiIter()
    dictionary=gensim.corpora.Dictionary(content.lower().split() 
            for (rvid, timestamp, content) in wiki.__iter__(title, "0"))
    stoplist=set('for a of the and to in'.split())

    stop_ids=[dictionary.token2id[stopword] for stopword in stoplist 
                if stopword in dictionary.token2id]
    once_ids=[tokenid for tokenid, docfreq in dictionary.dfs.iteritems() if docfreq==1]
    dictionary.filter_tokens(stop_ids+once_ids)
    dictionary.compactify()

    title=title.replace(" ", "_")
    file='dictionaries/'+title+'.dict'
    dictionary.save(file)


def readDictionary(title):
    """
    """
    title=title.replace(" ", "_")
    file='dictionaries/'+title+'.dict'
    if not os.path.isdir('dictionaries') or not os.path.isfile(file):
        print "File does not exist"
        return
    return gensim.corpora.Dictionary.load(file)



def saveCorpus(title, dictionary):
    """
    """
    if not os.path.isdir('corpus'):
        os.mkdir('corpus')

    wiki = WikiIter()

    corpus=MyCorpus(wiki.__iter__(title, "0"), dictionary)
    file='corpus/' + title.replace(" ", "_")+'.mm'
    gensim.corpora.MmCorpus.serialize(file, corpus)

def readCorpus(title):
    """
    """
    file='corpus/' + title.replace(" ", "_")+'.mm'
    if not os.path.isdir('corpus') or not os.path.isfile(file):
        print "File does not exist."
        return
    return gensim.corpora.MmCorpus(file)


def saveTfidf(title, bow_corpus, normalize):
    """
    """
    tfidf_model=gensim.models.TfidfModel(bow_corpus, normalize)
    if not os.path.isdir('tfidf'):
        os.mkdir('tfidf')
    file='tfidf/' + title.replace(" ", "_")+'.tfidf'
    tfidf_model.save(file)

def loadTfidf(title):
    """
    """
    file='tfidf/' + title.replace(" ", "_")+'.tfidf'
    if not os.path.isdir('tfidf') or not os.path.isfile(file):
        print "File does not exist."
        return
    return gensim.models.TfidfModel.load(file)

def saveLsi(title, tfidf, corpus, id2word, num_topics):
    """
    """
    tfidf_model=gensim.models.LsiModel(tfidf[corpus], id2word=id2word, num_topics=num_topics)
    if not os.path.isdir('lsi'):
        os.mkdir('lsi')
    file='lsi/' + title.replace(" ", "_")+'.lsi'
    tfidf_model.save(file)

def loadLsi(title):
    """
    """
    file='lsi/' + title.replace(" ", "_")+'.lsi'
    if not os.path.isdir('lsi') or not os.path.isfile(file):
        print "File does not exist."
        return
    return gensim.models.LsiModel.load(file)


def scoreDoc(title, index, doc, dictionary, tfidf, lsi):
    """
    """
    title=title.replace(" ", "_")
    # use 200-500 topics for tfidf
    doc_bow=dictionary.doc2bow(doc.lower().split())
    index_bow=[dictionary.doc2bow(index.lower().split())]


    lsi_doc=lsi[tfidf[doc_bow]]
    lsi_index=lsi[tfidf[index_bow]]

    if not os.path.isdir('indexes'):
        os.mkdir('indexes')
    # index has to be a corpus, does not have to be the training corpus
    index=gensim.similarities.Similarity('indexes/'+title, lsi_index, 300)
    sims=index[lsi_doc]
    return(list(enumerate(sims)))

