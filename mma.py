#!/usr/bin/env python
import cgi
import datetime
import wsgiref.handlers
import MMA.api
import md5

from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.ext import webapp

class Project(db.Model):
  id = db.StringProperty(multiline=False)
  author = db.UserProperty()
  content = db.StringProperty(multiline=True)
  date = db.DateTimeProperty(auto_now_add=True)
  translate = db.StringProperty(multiline=True)

class MMA2Midi(webapp.RequestHandler):
  def mma2midi(self, content):
    return MMA.api.parseMMA(content) 

  def post(self):
    content = self.request.get('content')
    self.response.out.write( self.mma2midi(content) )


class SaveMMA(webapp.RequestHandler):
  def post(self):
    project = Project()

    if users.get_current_user():
      project.author = users.get_current_user()

    project.id = self.request.get('id')
    project.content = self.request.get('content')
    project.put()
    self.redirect('/mma/')


class MainPage(webapp.RequestHandler):
  def get(self):
    self.response.out.write('<html><body>')

    greetings = db.GqlQuery("SELECT * "
                            "FROM Project "
                            "ORDER BY date DESC LIMIT 10")

    for greeting in greetings:
      if greeting.author:
        self.response.out.write('<b>%s</b> wrote:' % greeting.author.nickname())
      else:
        self.response.out.write('An anonymous person wrote:')
      self.response.out.write('<blockquote>%s</blockquote>' %
                              cgi.escape(greeting.content))

    self.response.out.write("""
          <form action="/mma/2midi" method="post">
            <div><textarea name="content" rows="3" cols="60"></textarea></div>
            <div><input type="submit" value="Sign Guestbook"></div>
          </form>
        </body>
      </html>""")


def main():
  application = webapp.WSGIApplication([
    ('/mma/', MainPage),
    ('/mma/2midi', MMA2Midi),
    ('/mma/save', SaveMMA)
  ], debug=True)

  wsgiref.handlers.CGIHandler().run(application)


if __name__ == '__main__':
  main()
