import md5
import gbl
from   MMA.common import *
import MMA.api

from google.appengine.ext import db
from google.appengine.api import users

class User(db.Model):
  name = db.StringProperty()
  password = db.StringProperty()
  email = db.EmailProperty()
  date = db.DateTimeProperty(auto_now_add=True)

class Project(db.Model):
  name = db.StringProperty(required=True)
  type = db.StringProperty(required=True)
  author = db.ReferenceProperty(User)
  content = db.TextProperty(required=True)
  date = db.DateTimeProperty(auto_now_add=True)
  midi = db.BlobProperty()

class StyleLib(db.Model):
  name  = db.StringProperty(required=True)
  type = db.StringProperty(required=True)
  path  = db.StringProperty(required=False)
  author = db.ReferenceProperty(User)
  date = db.DateTimeProperty(auto_now_add=True)
  content = db.TextProperty(required=True)
  tags = db.ListProperty(str)

class StyleRating(db.Model):
  style = db.ReferenceProperty(StyleLib)
  author = db.ReferenceProperty(User)
  rate = db.IntegerProperty(required=True)
  date = db.DateTimeProperty(auto_now_add=True)

def getStyle(name, path):
  greetings = StyleLib.gql( "WHERE name = :1 ", name)
  if (greetings != None ):
    return greetings[0]
  return None

def parseStyle(content):
  pass

def saveStyle(name, path, content): 
  pass 
 
def getProject(id): 
  projects = StyleLib.gql( "WHERE id = :1 ", id) 
  if (projects != None ): 
    return projects[0] 
  return None 
 
def saveProject(content): 
  pass 
 
def parseProject(content): 
  pass 
