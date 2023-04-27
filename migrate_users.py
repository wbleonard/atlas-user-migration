import params
import json
import requests
from requests.auth import HTTPDigestAuth
import pymongo
from pymongo import MongoClient
import random
import string

print("\nMigrating MongoDB Users\n")

# Establish connection to the source cluster
client = MongoClient(params.source_conn_string)
db = client[params.source_database]

userInfo = db.command("usersInfo")
users = userInfo["users"]
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

def generate_password(length):
    """
    Generate a random password of the given length.
    """
    # Define the set of characters to use in the password
    chars = string.ascii_letters + string.digits + string.punctuation

    # Use random.sample to get a list of `length` characters from the set
    password_chars = random.sample(chars, length)

    # Convert the list to a string and return it
    return ''.join(password_chars)

headers = {"content-type": "application/json"}

## Create users in Atlas
for user in users:
    # Don't try to create agent users in Atlas
    if user["user"][:3] == "mms":
        print("<<<Skipping user " + user["user"] + ">>>\n")
        continue

    print(">>> Migrating user:")
    print(str(user) + "\n")

    userdata = {
        "databaseName": "admin",
        "roles": getRoles(user["roles"]),
        "username": user["user"],
        "password": generate_password(12),
    }

    print("\nUser data sent to Atlas API:")
    print(userdata)
    print()

    url = (
        "https://cloud.mongodb.com/api/atlas/v1.0/groups/"
        + params.target_project_id
        + "/databaseUsers"
    )
    resp = requests.post(
        url=url,
        auth=HTTPDigestAuth(params.target_api_public_key, params.target_api_private_key),
        json=userdata,
        headers=headers,
    )

    if resp.status_code == 201:
        print("User " + user["user"] + " created.")

        # Record the generated user (so the passwords can be shared/changed)
        with open('users.txt', 'a') as f:
            f.write(user["user"] +':'+userdata["password"] + '\n')
     
    elif resp.status_code == 409:
        print(user["user"] + " alredy exists.")
    else:
        print(user["user"] + " failed to be created.")
        print("Error - status code: " + str(resp.status_code))

    print(">>>\n")
