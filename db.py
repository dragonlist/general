#!/usr/bin/python

import sys
import os

DIR_PATH = '/home/andy/XDev/appengine'

EXTRA_PATHS = [
  DIR_PATH,
  os.path.join(DIR_PATH, 'lib', 'antlr3'),
  os.path.join(DIR_PATH, 'lib', 'django'),
  os.path.join(DIR_PATH, 'lib', 'ipaddr'),
  os.path.join(DIR_PATH, 'lib', 'webob'),
  os.path.join(DIR_PATH, 'lib', 'yaml', 'lib'),
]

sys.path = EXTRA_PATHS + sys.path

from google.appengine.ext import db
from google.appengine.ext.remote_api import remote_api_stub

import MMA.lib 

APP_ID = 'imint'
REMOTE_API_PATH = '/remote_api'
SERVER = 'localhost:8800'

def auth_func():
  email_address = 'test@gmail.com' 
  password = '' 
  return email_address, password


def initialize_remote_api(app_id=APP_ID, 
                          path=REMOTE_API_PATH,
                          server=SERVER):
  remote_api_stub.ConfigureRemoteApi(app_id, path, auth_func, server)
  remote_api_stub.MaybeInvokeAuthentication()


def addSysUser():
  sysuser= MMA.lib.User(name = 'root',  password = 'ttt',  email = 'test@gmail.com') 
  sysuser.put()

def addProject():
  project = MMA.lib.Project(name = 'XYZ',  type = 'test',  author = None,  content = 'ZZZ',  midi = '') 
  ref = project.put()

def getSysUser():
  sysuser = MMA.lib.User.all().filter('name=', 'root').get()
  print sysuser

def getProject():
  sysuser = db.Query(MMA.lib.Project).filter('name=', 'XYZ').get()
  print sysuser


def addStyles():
  style = MMA.lib.StyleLib()
  style.put()

def main():
  initialize_remote_api()
  getProject()
 
if __name__ == '__main__':
  main()  
