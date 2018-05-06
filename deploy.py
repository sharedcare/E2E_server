from flask import Flask, request, json, jsonify, render_template
from flask_pymongo import PyMongo
import random
import os

app = Flask(__name__)
mongo = PyMongo(app)

if 'MONGO_URI' in os.environ:
    app.config['MONGO_URI'] = os.environ['MONGO_URI']


@app.route('/')
def e2e_home_page():
    online_users = mongo.db.users.find({'online': True})
    return render_template('index.html',
                           online_users=online_users)

@app.route('/insert')
def insert():
    query_params = request.args
    id = query_params.get('id')
    mongo.db.test.insert({"id": id})
    return "Success"

@app.route('/get')
def get():
    query_params = request.args
    id = query_params.get('id')
    result = mongo.db.test.distinct('id')
    return jsonify({'result': result})

@app.route('/remove')
def remove():
    mongo.db.test.remove()
    return 'Removed'


@app.route('/register', methods=['POST'])
def register():
    pre_key_bundle = mongo.db.preKeyBundle
    body = request.data
    id = random.randint(0, 999999)
    ids = pre_key_bundle.distinct('id')
    while id in ids:
        id = random.randint(0, 999999)

    data = {"id": id, "preKeyBundle": body}
    pre_key_bundle.insert(data)
    response = app.response_class(
        status=200,
        mimetype='application/json',
        response=json.dumps({'id': id})
    )
    return response

@app.route('/requestKey')
def request_key():
    query_params = request.args
    id = int(query_params.get('id'))
    preKeyBundle = mongo.db.preKeyBundle.find_one({'id': id})
    print(preKeyBundle)
    if preKeyBundle:
        res_text = json.dumps({'id': preKeyBundle['id'], 'preKeyBundle': preKeyBundle['preKeyBundle'].decode(), 'status': 'success'})
    else:
        res_text = json.dumps({'status': 'failed', 'msg': 'no such id'})

    response = app.response_class(
        status=200,
        mimetype='application/json',
        response=res_text
    )
    return response

@app.route('/send', methods=['POST'])
def send():
    return 'Send'

@app.route('/receive')
def receive():
    data = {'key': 'value'}
    response = app.response_class(
        status=200,
        mimetype='application/json',
        response=json.dumps(data)
    )
    return response

if __name__ == '__main__':
    app.run()