#!/usr/bin/python

from app import app
app.secret_key = '?\xbf,\xb4\x8d\xa3"<\x9c\xb0@\x0f5\xab,w\xee\x8d$0\x13\x8b83'
app.run(debug=True)