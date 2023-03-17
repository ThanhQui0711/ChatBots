
# coding: utf-8

# In[1]:


import nltk
from nltk.stem.lancaster import LancasterStemmer
stemmer = LancasterStemmer()
from flask import Flask, render_template, request
import numpy as np
import tflearn
import tensorflow as tf
import random
app = Flask(__name__)

# In[2]:


import pickle
data = pickle.load( open( "models/training_data", "rb" ) )
words = data['words']
classes = data['classes']
train_x = data['train_x']
train_y = data['train_y']

import json
with open('data/intents.json',encoding='utf-8') as json_data:
    intents = json.load(json_data)


# In[3]:


net = tflearn.input_data(shape=[None, len(train_x[0])])
net = tflearn.fully_connected(net, 8)
net = tflearn.fully_connected(net, 8)
net = tflearn.fully_connected(net, len(train_y[0]), activation='softmax')
net = tflearn.regression(net, optimizer='adam', loss='categorical_crossentropy')

model = tflearn.DNN(net, tensorboard_dir='tflearn_logs')


# In[4]:
def clean_up_sentence(sentence):
    sentence_words = nltk.word_tokenize(sentence)

    sentence_words = [stemmer.stem(word.lower()) for word in sentence_words]
    return sentence_words

# bag of words
def bow(sentence, words, show_details=False):
    sentence_words = clean_up_sentence(sentence)
    # bag of words
    bag = [0]*len(words)  
    for s in sentence_words:
        for i,w in enumerate(words):
            if w == s: 
                bag[i] = 1
                if show_details:
                    print ("found in bag: %s" % w)
    return(np.array(bag))
# In[5]:
bow('demo', words)
# In[6]:
# load model
model.load('./models/model.tflearn')
# In[7]:
# data structure to hold user context
context = {}

ERROR_THRESHOLD = 0.25
def classify(sentence):
    results = model.predict([bow(sentence, words)])[0]
    results = [[i,r] for i,r in enumerate(results) if r>ERROR_THRESHOLD]
    results.sort(key=lambda x: x[1], reverse=True)
    return_list = []
    for r in results:
        return_list.append((classes[r[0]], r[1]))
    return return_list

def response(sentence, userID='1', show_details=False):
    results = classify(sentence)
    if results:
        while results:
            for i in intents['intents']:
                if i['tag'] == results[0][0]:
                    if 'context_set' in i:
                        if show_details: print ('context:', i['context_set'])
                        context[userID] = i['context_set']
                    if not 'context_filter' in i or (userID in context and 'context_filter' in i and i['context_filter'] == context[userID]):
                        if show_details: print ('tag:', i['tag'])
                        return random.choice(i['responses'])
            results.pop(0)
@app.route("/")
def home():
	return render_template("home.html")
@app.route("/get")
def get_bot_response():
	userText = request.args.get('msg')
	return str(response(userText))
if __name__ == "__main__":
	app.run()         
