import nltk, string, re, math
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
factory = StemmerFactory()
stemmer = factory.create_stemmer()
from nltk.corpus import stopwords
listStopword = set(stopwords.words('indonesian'))
from flask import Flask, render_template, request, session
from flask_mysqldb import MySQL
# import mysql.connector

app = Flask(__name__)
app.config["SECRET_KEY"] = "kepo"
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'skripsi'

mysql = MySQL(app)

@app.route("/")
def index():
    return render_template("main_layout.html")

def processdoc(tanya):
    tanya2 = tanya.lower()
    tanya3 = tanya2.translate(str.maketrans("", "", string.punctuation))
    tanya4 = re.sub(r"\d+", "", tanya3)
    tanya5 = stemmer.stem(tanya4)
    tokens = nltk.tokenize.word_tokenize(tanya5)
    tokens = nltk.FreqDist(tokens)
    return dict(tokens)

def loadtfidf(tokens, ctg):
    cur = mysql.connection.cursor()
    cur.execute('''
    SELECT dok_kata.id_dok, kata.teks, tf_idf, dok_kata.category
    FROM dok_kata, kata WHERE dok_kata.kata = kata.id 
    AND dok_kata.category = %s
    AND kata.teks IN (''' 
    + ', '.join(['%s'] * len(tokens)) +
    ''')''', (ctg, *tokens))
    return list(cur.fetchall())


def cosine_similarity(a, b):
    dot_product = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    cos_sim = dot_product / (norm_a * norm_b)
    return cos_sim

def cossim(data, tokens, musthaveall):
    wordlist = tuple(tokens)
    dflist = [0] * len(tokens)
    docvectors = {}
    # cari nilai DF dan vektor dokumen terhadap query
    for [dok_id, word, tf_idf, ktg] in data:
        wordindex = wordlist.index(word)
        dflist[wordindex] += 1
        if dok_id not in docvectors:
            docvectors[dok_id] = [0] * len(tokens)
        docvectors[dok_id][wordindex] = tf_idf
    # cari vektor query
    tokenvector = []
    for i, word in enumerate(wordlist):
        tf = tokens[word]
        idf = len(docvectors) / dflist[i] if dflist[i] > 0 else 0
        tokenvector.append(tf * idf)
    doccossim = {}
    for dok_id, doc_vector in docvectors.items():
        # must have all?
        if musthaveall and 0 in doc_vector:
            continue
        doccossim[dok_id] = cosine_similarity(tokenvector, doc_vector)
    return doccossim    

def loaddocuments(docids, scores):
    cur = mysql.connection.cursor()
    cur.execute('''
    SELECT id,buku,bab,bagian,paragraf,pasal,ayat 
    FROM dokumen WHERE id IN (''' 
    + ', '.join(['%s'] * len(docids)) +
    ''')''', tuple(docids))
    results = []
    docs = list(cur.fetchall())
    for docid in docids:
        for doc in docs:
            if docid == doc[0]:
                results.append({
                    'id': doc[0],
                    'buku': doc[1],
                    'bab': doc[2],
                    'bagian': doc[3],
                    'paragraf': doc[4],
                    'pasal': doc[5],
                    'ayat': doc[6],
                    'score': scores[docid]
                })
                break
    jumlah_dokumen = len(results)
    print("Jumlah dokumen terpanggil:", jumlah_dokumen)
    return results


@app.route("/result")
def result():
    tanya = (request.args['query'])
    tokens = processdoc(tanya)
    scores_all = {}
    for ctg_i, ctg_name in enumerate("Bab,Bagian,Paragraf,Ayat".split(",")):
        doks = loadtfidf(set(tokens), ctg_name)
        scores = cossim(doks, tokens, True)
        for docid, score in scores.items():
            if docid not in scores_all:
                scores_all[docid] = [0] * 4
            scores_all[docid][ctg_i] = score
    for docid, s in scores_all.items():
        scores_all[docid] = s[3]
    docids = sorted(scores_all, key=scores_all.get, reverse=True)
    results = loaddocuments(docids, scores_all) if len(docids) > 0 else []
    return render_template("result.html", takok = tanya, results = results )

# @app.route("/about")
# def about():
#     return render_template("about.html")

# @app.route("/contact")
# def contact():
#     return render_template("contact.html")

if __name__ == "__main__":
    app.run(debug=True)