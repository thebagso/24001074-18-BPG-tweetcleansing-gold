from flask import Flask, jsonify
import re
import pandas as pd
import sqlite3

from flask import request
from flasgger import Swagger, LazyString, LazyJSONEncoder
from flasgger import swag_from

app = Flask(__name__)

kamusalaydf = pd.read_csv('/Users/0011-21-pt.lbb/binar-dsc/binar-dsc/binar-dsc/coding_binar/Asset Challenge/new_kamusalay.csv', encoding='ISO-8859-1', header=None)
kamusalay_dict = dict(zip(kamusalaydf[0], kamusalaydf[1]))
def koreksi_alay(text):
    return ' '.join([kamusalay_dict[word] if word in kamusalay_dict else word for word in text.split(' ')])

def proper_case(sentence):
    words = sentence.split()
    if len(words) > 0:
        words[0] = words[0].capitalize()
    for i in range(1, len(words)):
        words[i] = words[i].lower()
    return ' '.join(words)

def proper_casing_paragraph(paragraph):
    sentences = paragraph.split('.')
    proper_cased_sentences = []
    for sentence in sentences:
        if sentence.strip() != "":
            proper_cased_sentence = proper_case(sentence.strip())
            proper_cased_sentences.append(proper_cased_sentence)
    return '. '.join(proper_cased_sentences)

def clean_text(text):
    text = re.sub(r'\\x[0-9a-fA-F]{2}', '', text)
    text = re.sub('http\S+', '', text)
    text = re.sub(r'[^a-zA-Z.,]', ' ', text)
    text = re.sub('\s+', ' ', text)
    text = re.sub(r'\b(USER|RT|URL)\b', '', text)
    text = text.strip()
    text = proper_casing_paragraph(text)
    text = koreksi_alay(text)

    return text

app.json_encoder = LazyJSONEncoder
swagger_template = dict(
info = {
    'title': LazyString(lambda: 'Challenge Gold DSC 18 - Bagus Prakoso'),
    },
    host = LazyString(lambda: request.host)
)
swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": 'docs',
            "route": '/docs.json',
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/docs/"
}
swagger = Swagger(app, template=swagger_template,
                  config=swagger_config)

@swag_from("docs/text_processing.yml", methods=['POST'])
@app.route('/input_text', methods=['POST'])
def input_teks():
    data = request.form.get('text')
    json_response = {
        'output': clean_text(data),
    }
    return jsonify(json_response)

import re

@swag_from("docs/text_processing_file.yml", methods=['POST'])
@app.route('/docs/text_processing_from_csv', methods=['POST'])
def text_processing_file():
    file = request.files.getlist('file')[0]
    
    df = pd.read_csv(file, encoding='latin-1')
    df['Tweet'] = df['Tweet'].replace(r'\\n',' ', regex=True)
    texts = df['Tweet'].to_list()
   
    def clean_tweet(tweet):
        tweet = re.sub(r'\\x[0-9a-fA-F]{2}', '', tweet)
        tweet = re.sub('http\S+', '', tweet)
        tweet = re.sub(r'[^a-zA-Z0-9]', ' ', tweet)
        tweet = re.sub('\s+', ' ', tweet)
        tweet = re.sub(r'\b(USER|RT|URL)\b', '', tweet)
        tweet = tweet.strip()
        tweet = proper_casing_paragraph(tweet)

        return tweet
    
    df_db = pd.DataFrame()
    df_db['Before_Cleaned'] = df['Tweet']
    df_db['After_Cleaned'] = df['Tweet'].apply(clean_tweet)
    cleaned_text = df_db['After_Cleaned'].values.tolist()

    conn = sqlite3.connect('tweet_cleansing.db')
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tweet_table (
        Before_Cleaned TEXT,
        After_Cleaned TEXT
    )
    ''')
    for index, text in df_db.iterrows():
        cursor.execute('''
            INSERT INTO tweet_table VALUES (?,?)
        ''', tuple(text))

    conn.commit()
    conn.close()
    
    json_response = {
        'status_code': 200,
        'description': "Teks yang sudah diproses",
        'data': cleaned_text,
    }
    response_data = jsonify(json_response)
    return response_data

if __name__ == '__main__':
   app.run()