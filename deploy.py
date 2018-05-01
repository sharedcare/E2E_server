from flask import Flask, request, json, jsonify, render_template
from flask_pymongo import PyMongo

app = Flask(__name__)
mongo = PyMongo(app)

@app.route('/')
def e2e_home_page():
    online_users = mongo.db.users.find({'online': True})
    return render_template('index.html',
                           online_users=online_users)

@app.route('/insert')
def insert():
    query_params = request.args
    id = query_params.get('id')
    mongo.db.test.insert_one({"id": id})
    return "Success"

@app.route('/get')
def get():
    query_params = request.args
    id = query_params.get('id')
    return mongo.db.test.find_one({"id": id})

@app.route('/register', methods=['POST'])
def register():
    body = request.get_json()
    number = int(body['Number'])
    id = int(body['ID'])
    key_bundle = body['KeyBundle']
    data = {}
    return '''<p>The number is {}</p>
    <p>The id is {}</p>
    <p>The key bundle is {}</p>'''.format(number, id, key_bundle)

@app.route('/requestKey')
def request_key():
    query_params = request.args
    id = query_params.get('id')
    return '''<h1>The id is: {}</h1>'''.format(id)

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