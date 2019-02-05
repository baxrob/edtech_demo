from flask import Flask, redirect, url_for, session, request, jsonify, \
    render_template
from flask_oauthlib.client import OAuth
from flask_mail import Mail, Message

app = Flask(__name__, template_folder='.')
app.debug = True
app.secret_key = 'development'
oauth = OAuth(app)

linkedin = oauth.remote_app(
    'linkedin',
    #consumer_key='k8fhkgkkqzub',
    #consumer_secret='ZZtLETQOQYNDjMrz',
    consumer_key='863rzse5mrubtb',
    consumer_secret='Ju9kwzCg2cIcBugP',
    request_token_params={
        'scope': 'r_basicprofile r_emailaddress',
        'state': 'RandomString',
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
        return jsonify(me.data)
        return render_template('main.html', {
            'user': me.data
        })
    return redirect(url_for('login'))


@app.route('/public')
def public():
    return render_template(
        'main.html', 
        user = {
            'email-address': 'baxrob+edtech@gmail.com'
        }
    )


@app.route('/share/<string:file_ident>', methods=['POST'])
def share(file_ident):
    if 'linkedin_token' in session:
        me = linkedin.get('people/~')
        return jsonify(me.data)
        return render_template('main.html', {
            'user': me.data
        })
    #return redirect(url_for('login'))

    #import ipdb; ipdb.set_trace()
    #print file_id, request.form, request.data
    from werkzeug.utils import secure_filename
    # XXX: 512MB limit
    fd = open('audio/' + str(file_ident) + '.wav', 'wb+')
    fd.write(request.data)
    fd.close()
    return jsonify({'file_ident': file_ident})
    return "written %s" % (file_ident)


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
