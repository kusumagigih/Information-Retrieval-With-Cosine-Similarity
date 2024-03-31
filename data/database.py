import mysql.connector
import csv
import re
from preprocess import preprocess
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfTransformer

mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    passwd="",
    database="skripsi"
)

mycursor = mydb.cursor()
mycursor.execute("TRUNCATE dok_kata;")
mycursor.execute("TRUNCATE kata;")
mycursor.execute("TRUNCATE dokumen;")
with open('outpust.csv', 'r', encoding='utf8') as i:
    reader = csv.reader(i)
    next(reader, None) # skip header
    corpus = [[], [], [], []]
    for i, line in enumerate(reader):
        Buku,Bab,Bagian,Paragraf,Pasal,Ayat = line
        corpus[0].append(preprocess(Bab))
        corpus[1].append(preprocess(Bagian))
        corpus[2].append(preprocess(Paragraf))
        corpus[3].append(preprocess(Ayat))
        mycursor.execute(
            "INSERT INTO dokumen (id,buku,bab,bagian,paragraf,pasal,ayat) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (i + 1, Buku,Bab,Bagian,Paragraf,Pasal,Ayat))
    word_id_map = {}
    for ctg_i, ctg_name in enumerate("Bab,Bagian,Paragraf,Ayat".split(",")):
        vectorizer = CountVectorizer()
        X = vectorizer.fit_transform(corpus[ctg_i])
        wordlist = list(vectorizer.get_feature_names_out())
        for i, word in enumerate(wordlist):
            # kalau sudah ada, skip
            if word in word_id_map:
                continue
            mycursor.execute(
                "INSERT INTO kata (id,teks) VALUES (%s)",
                (len(word_id_map) + 1, word))
            word_id_map[word] = len(word_id_map) + 1
        
        tfidf = TfidfTransformer()
        Y = tfidf.fit_transform(X)
        tfidf = {}
        for i, x in enumerate(list(Y)):
            for y, z in dict(x.todok()).items():
                tfidf[i + 1, word_id_map[wordlist[y[1]]], ctg_name] = float(z)

        for (x, y, z), w in tfidf.items():
            sql = "INSERT INTO dok_kata VALUES(%s, %s, %s, %s)"
            mycursor.execute(sql, [x, y, z, w])
    mydb.commit()
