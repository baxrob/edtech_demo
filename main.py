import os

from werkzeug.utils import secure_filename
from flask import Flask, redirect, url_for, session, request, jsonify, \
    render_template
from flask_oauthlib.client import OAuth
from flask_mail import Mail, Message

app = Flask(__name__, template_folder='.')

#app.debug = True
#app.secret_key = 'development'

app.config.from_object('local_config')
#print app.config['LINKEDIN_KEY']

oauth = OAuth(app)

'''
app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'customerjoe6@gmail.com'
app.config['MAIL_PASSWORD'] = 'pa55ad3na'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_DEFAULT_SENDER'] = '"edtech demo" <baxrob@gmail.com>'
'''
mail = Mail(app)

#import ipdb; ipdb.set_trace()

linkedin = oauth.remote_app(
    'linkedin',
    #consumer_key='863rzse5mrubtb',
    #consumer_secret='Ju9kwzCg2cIcBugP',
    consumer_key=app.config['LINKEDIN_CONSUMER_KEY'],
    consumer_secret=app.config['LINKEDIN_CONSUMER_SECRET'],
    request_token_params={
        'scope': 'r_basicprofile r_emailaddress',
        'state': 'aIEj8PmU6j2l9w',
    },
    base_url='https://api.linkedin.com/v1/',
    request_token_url=None,
    access_token_method='POST',
    access_token_url='https://www.linkedin.com/uas/oauth2/accessToken',
    authorize_url='https://www.linkedin.com/uas/oauth2/authorization',
)


@app.route('/')
def index():
    if 'linkedin_token' in session:
        me = linkedin.get('people/~')
        #return jsonify(me.data)
        me = linkedin.get('people/~:(id,email-address)?format=json')
        me = linkedin.get('people/~:(id,email-address)')
        if me.data.has_key('id'):
            return render_template('main.html', user=me.data)
    if app.config['FAKE_LOGIN']:
        return render_template(
            'main.html', 
            user={
                'id': '0000',
                'emailAddress': 'baxrob+edtech@gmail.com'
            }
        )
    return redirect(url_for('login'))


@app.route('/public')
def public():
    return render_template(
        'main.html', 
        user = {
            'id': '0000',
            'emailAddress': 'baxrob+edtech@gmail.com'
        }
    )


@app.route('/share/<string:file_ident>', methods=['POST'])
def share(file_ident):
    '''
    '''
    if app.config['FAKE_LOGIN'] or 'linkedin_token' in session:
        #me = linkedin.get('people/~')
        if 'linkedin_token' in session:
            me = linkedin.get('people/~:(id,email-address)?format=json')
            me = linkedin.get('people/~:(id,email-address)?format=json')
            user_data = me.data
            if not user_data.has_key('id'):
                return redirect(url_for('login'))
            #return jsonify(me.data)
            #return render_template('main.html', user=me.data)
        else:
            user_data = {'id': '0000', 'emailAddress': 'baxrob+edtech@gmail.com'}

        file_user = file_ident.split('_')[0]
        if user_data['id'] != file_user:
            return jsonify({
                'error': 'user mismatch'
            })

        # XXX: 512MB limit
        file_path = os.path.join(
            app.root_path,
            app.config['AUDIO_PATH'],
            secure_filename(''.join([str(file_ident), '.wav']))
        )
        #fd = open('audio/' + str(file_ident) + '.wav', 'wb+')
        fd = open(file_path, 'wb+')
        fd.write(request.data)
        fd.close()

        msg = Message(
            #recipients=['baxrob+edtech@gmail.com', 'rlb@blandhand.net'],
            recipients=[user_data['emailAddress']],
            body='https://baxrob.pythonanywhere.com/play/' + file_ident,
            subject='Edtech demo recording'
        )
        mail.send(msg)

        return jsonify({'file_ident': file_ident})
        return "written %s" % (file_ident)
        return jsonify({
            'cwd': os.getcwd(),
            'file_id': file_id
        })

    return redirect(url_for('login'))


@app.route('/play/<string:file_ident>')
def play(file_ident):
    #file_path = path.join(config.audio_path, file_ident)

    #1.wav
    #a_1549404899790.wav  
    #file_ident = 'a_1549406520161'
    #a_1.wav
    if app.config['FAKE_LOGIN'] or 'linkedin_token' in session:
        #me = linkedin.get('people/~')
        if 'linkedin_token' in session:
            me = linkedin.get('people/~:(id,email-address)?format=json')
            user_data = me.data
            #return jsonify(me.data)
            #return render_template('main.html', user=me.data)
        else:
            user_data = {'id': '0000', 'emailAddress': 'baxrob+edtech@gmail.com'}

        file_user = file_ident.split('_')[0]
        if user_data['id'] != file_user:
            return jsonify({
                'error': 'user mismatch'
            })
         
        file_path = os.path.join(
            '/',
            app.config['AUDIO_PATH'], 
            ''.join([file_ident, '.wav'])
        ) 
        return render_template('play.html', audio_path=file_path) 

    return redirect(url_for('login'))


@app.route('/login')
def login():
    return linkedin.authorize(callback=url_for('authorized', _external=True))


@app.route('/logout')
def logout():
    session.pop('linkedin_token', None)
    return redirect(url_for('index'))


@app.route('/login/authorized')
def authorized():
    resp = linkedin.authorized_response()
    if resp is None:
        return 'Access denied: reason=%s error=%s state=%s' % (
            request.args['error'],
            request.args['error_description'],
            request.args['state'] 
        )
    session['linkedin_token'] = (resp['access_token'], '')
    me = linkedin.get('people/~')
    me = linkedin.get('people/~:(id,num-connections,picture-url)?format=json')
    me = linkedin.get('people/~:(id,email-address)?format=json')
    return redirect(url_for('index'))
    return jsonify(me.data)


@linkedin.tokengetter
def get_linkedin_oauth_token():
    return session.get('linkedin_token')


def change_linkedin_query(uri, headers, body):
    auth = headers.pop('Authorization')
    headers['x-li-format'] = 'json'
    if auth:
        auth = auth.replace('Bearer', '').strip()
        if '?' in uri:
            uri += '&oauth2_access_token=' + auth
        else:
            uri += '?oauth2_access_token=' + auth
    return uri, headers, body

linkedin.pre_request = change_linkedin_query


if __name__ == '__main__':
    app.run(host='0.0.0.0')
