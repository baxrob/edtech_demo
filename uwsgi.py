import logging

#import frontis

from course_dev import create_app

app = create_app()

from flask_sslify import SSLify

sslify = SSLify(app)

cwd = os.getcwd()
logfilename = os.path.join(cwd, 'passenger_wsgi.log')

handler = logging.FileHandler(logfilename)
app.logger.setLevel(logging.DEBUG)
app.logger.addHandler(handler)

