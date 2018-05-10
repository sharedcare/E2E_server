from flask import Flask, request, json, jsonify, render_template
from flask_pymongo import PyMongo
import random
import os
import time
import string

CUSTOM_HEADER = {'Access-Control-Allow-Origin': '*'}
REQUEST = 'request'
CONFIRM = 'confirm'
DECLINE = 'decline'
SUCCESS_STAT = 'success'
FAIL_STAT = 'failed'

app = Flask(__name__)

if 'MONGODB_URI' in os.environ:
    app.config['MONGO_URI'] = os.environ['MONGODB_URI']

mongo = PyMongo(app)


@app.route('/')
def e2e_home_page():
    return render_template('index.html')


@app.route('/remove', methods=['POST'])
def remove():
    mongo.db.preKeyBundle.remove()
    mongo.db.idToken.remove()
    mongo.db.msg.remove()
    return 'Removed'


@app.route('/register', methods=['POST'])
def register():
    per_key_bundle = mongo.db.perKeyBundle
    id_token = mongo.db.idToken
    body = request.data
    id = random.randint(0, 999999)
    ids = per_key_bundle.distinct('id')
    while id in ids:
        id = random.randint(0, 999999)

    access_token = random_generator(size=32)

    pre_key_data = {"id": id, "preKeyBundle": body}
    id_token_data = {"id": id, "accessToken": access_token, "expireTime": time.time() + 60*60*3}
    per_key_bundle.insert(pre_key_data)
    id_token.insert(id_token_data)
    response = app.response_class(
        status=200,
        mimetype='application/json',
        headers=CUSTOM_HEADER,
        response=json.dumps({'id': id, "accessToken": access_token, 'status': SUCCESS_STAT})
    )
    return response


@app.route('/connect', methods=['GET', 'POST'])
def connect():
    id_token_table = mongo.db.idToken
    per_key_table = mongo.db.perKeyBundle
    msg_table = mongo.db.msg
    
    query_params = request.args
    access_token = query_params.get('accessToken')
    
    id = get_id_from_token(access_token)
    
    if not id:
        res_text = json.dumps({'status': FAIL_STAT, 'msg': 'access_token not found'})
        response = app.response_class(
            status=200,
            mimetype='application/json',
            headers=CUSTOM_HEADER,
            response=res_text
        )
        return response
    
    if request.method == 'GET':
        msg = msg_table.find_one({'receiverId': id, 'type': REQUEST})
        if msg:
            res_text = json.dumps({'senderId': msg['senderId'], 'status': SUCCESS_STAT})
        else:
            res_text = json.dumps({'status': SUCCESS_STAT, 'msg': 'no connect request'})
        
        response = app.response_class(
            status=200,
            mimetype='application/json',
            headers=CUSTOM_HEADER,
            response=res_text
        )
        
        return response

    if request.method == 'POST':
        body = request.get_json()
        receiver_id = int(body['receiverId'])
        
        sender_id = id
        
        receiver_id_token = id_token_table.find_one({'id': receiver_id})
        if receiver_id_token:
            receiver_id = receiver_id_token['id']
            
            per_key_bundle = per_key_table.find_one({'id': receiver_id})
            if per_key_bundle:
                msg_data = {'senderId': sender_id, 'receiverId': receiver_id, 'type': REQUEST}
                msg_table.insert(msg_data)
                
                res_text = json.dumps({'status': SUCCESS_STAT})
                
            else:
                res_text = json.dumps({'status': FAIL_STAT, 'msg': 'sender key has been used'})
                
        else:
            res_text = json.dumps({'status': FAIL_STAT, 'msg': 'receiver_id not found'})

        response = app.response_class(
            status=200,
            mimetype='application/json',
            headers=CUSTOM_HEADER,
            response=res_text
        )
        
        return response


@app.route('/confirm', methods=['GET', 'POST'])
def confirm():
    id_token_table = mongo.db.idToken
    per_key_table = mongo.db.perKeyBundle
    msg_table = mongo.db.msg
    
    query_params = request.args
    access_token = query_params.get('accessToken')
    
    id = get_id_from_token(access_token)
    
    if not id:
        res_text = json.dumps({'status': FAIL_STAT, 'msg': 'access_token not found'})
        response = app.response_class(
            status=200,
            mimetype='application/json',
            headers=CUSTOM_HEADER,
            response=res_text
        )
        return response
    
    if request.method == 'GET':
        msg = msg_table.find_one({'receiverId': id, 'type': CONFIRM})
        if msg:
            print(msg)
            msg_table.remove({"_id": msg["_id"]})
            res_text = json.dumps({'receiverId': msg['senderId'], 
                                   'isConfirm': True,
                                   'perKeyBundle': msg['data'],
                                   'status': SUCCESS_STAT})
        else:
            msg = msg_table.find_one({'receiverId': id, 'type': DECLINE})
            
            if msg:
                msg_table.remove({"_id": msg["_id"]})
                res_text = json.dumps({'receiverId': msg['senderId'], 
                                   'isConfirm': False,
                                   'status': SUCCESS_STAT})
                                   
            else:
                res_text = json.dumps({'status': SUCCESS_STAT, 'msg': 'no confirm'})
        
        response = app.response_class(
            status=200,
            mimetype='application/json',
            headers=CUSTOM_HEADER,
            response=res_text
        )
        
        return response
        
    if request.method == 'POST':
        body = request.get_json()
        
        receiver_id = id
        sender_id = int(body['senderId'])
        is_confirm = body['isConfirm']
        
        msg = msg_table.find_one({'receiverId': id, 'senderId': sender_id, 'type': REQUEST})
        if msg:
            msg_table.remove({"_id": msg["_id"]})
            
            if is_confirm == "True":
                receiver_preKeyBundle = per_key_table.find_one({'id': receiver_id})
                if receiver_preKeyBundle:
                    per_key_table.remove({"_id": receiver_preKeyBundle["_id"]})
                    
                    msg_data = {'senderId': receiver_id, 'receiverId': sender_id, 'type': CONFIRM, 'data': receiver_preKeyBundle['preKeyBundle']}
                    msg_table.insert(msg_data)
                    
                # TODO: Handle receiver_preKeyBundle not found
                
                sender_preKeyBundle = per_key_table.find_one({'id': sender_id})
                if sender_preKeyBundle:
                    per_key_table.remove({"_id": sender_preKeyBundle["_id"]})
                    
                    res_text = json.dumps({'status': SUCCESS_STAT, 'preKeyBundle': sender_preKeyBundle['preKeyBundle']})
                    
                    response = app.response_class(
                        status=200,
                        mimetype='application/json',
                        headers=CUSTOM_HEADER,
                        response=res_text
                    )
                    return response
                    
                # TODO: Handle receiver_preKeyBundle not found
                    
            else:
                msg_data = {'senderId': receiver_id, 'receiverId': sender_id, 'type': DECLINE}
                msg_table.insert(msg_data)
                
                res_text = json.dumps({'status': SUCCESS_STAT})
                
                response = app.response_class(
                    status=200,
                    mimetype='application/json',
                    headers=CUSTOM_HEADER,
                    response=res_text
                )
                return response
            
        else:
            res_text = json.dumps({'status': FAIL_STAT, 'msg': 'connection request not found'})
            
            response = app.response_class(
                status=200,
                mimetype='application/json',
                headers=CUSTOM_HEADER,
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


def random_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


def get_id_from_token(accessToken):
    id_token_table = mongo.db.idToken
    
    id_token = id_token_table.find_one({'accessToken': accessToken})
    
    if id_token:
        return id_token['id']
    else:
        return False


if __name__ == '__main__':
    app.run()