from flask import Flask
from flask import request
app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello World'

@app.route('/register', methods=['POST'])
def register():
    body = request.get_json()
    number = body['Number']
    id = body['ID']
    key_bundle = body['KeyBundle']
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
    return 'Receive'

if __name__ == '__main__':
    app.run()