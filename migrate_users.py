import params
import json
import requests
from requests.auth import HTTPDigestAuth
import pymongo
from pymongo import MongoClient

print("\nMigrating MongoDB Users\n")

# Establish connection to the source cluster
client = MongoClient(params.source_conn_string)
db = client[params.source_database]

userInfo = db.command('usersInfo')
users = userInfo['users']
print(str(len(users)) + " potential users to be migrated\n")

# Format the roles as required by the Atlas API
def getRoles(roles):
    result = []
    for role in roles:
        formattedRole = {"databaseName": role["db"], "roleName": role["role"]}
        result.append(formattedRole)
    print("Formatted roles:")
    print(result)
    return result

headers = {"content-type":"application/json"}

## Create users
for user in users:

  # Don't try to create agent users in Atlas
  if user["user"][:3] == "mms":
      print("<<<Skipping user " + user["user"] + ">>>\n")
      continue

  print(">>> Migrating user:")
  print(str(user) + "\n")

  userdata = {
    "databaseName" : "admin",
    "roles" : getRoles(user["roles"]),
    "username" : user["user"],
    "password" : "changeme123"
  }

  print("\nUser data sent to Atlas API:")
  print(userdata)
  print()
  
  url = "https://cloud.mongodb.com/api/atlas/v1.0/groups/" + params.target_project_id +"/databaseUsers"
  resp = requests.post(url=url, auth=HTTPDigestAuth(params.target_api_user, params.target_api_key), json=userdata, headers=headers)
  
  if resp.status_code == 201:
    print(user["user"] + " created.")
  elif resp.status_code == 409:
    print(user["user"] + " alredy exists.")
  else:
    print(user["user"] + " failed to be created.")
    print("Error - status code: " + str(resp.status_code))

  print(">>>\n")
  
