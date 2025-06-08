import scratchattach as sa
import requests
import urllib.request
from PIL import Image
import json, os, random, math, time
from keep_alive import keep_alive

def log(*args):
    print(f"[{round(time.time())}]", *args)

def convertToNumber(s):
    return int.from_bytes(s.encode(), 'little')

def convertFromNumber(n):
    return n.to_bytes(math.ceil(n.bit_length() / 8), 'little').decode()

session_ps = os.environ.get("SCRATCH_PS")
session = sa.login('Dev-Server', session_ps)  # replace with your session_id and username
cloud1 = session.connect_cloud(1186198180)  # replace with your project id
client1 = cloud1.requests()

@client1.request
def ping(username):  # called when client receives request
    log("Ping request received")
    return "pong"

@client1.request
def get_pfp(username):
    try:
        data = requests.get(f"https://api.scratch.mit.edu/users/{username}").json()
        user_id = data["id"]
    except:
        return "User Not Found"
    img_url = f"https://uploads.scratch.mit.edu/get_image/user/{user_id}_1000x1000.png"
    log(f"Image url: {img_url}")
    image_name = f"pfp{convertToNumber(username)}.png"
    urllib.request.urlretrieve(img_url, f"/tmp/{image_name}")
    log(f"Image stored in /tmp/{image_name}")
    return image_name

@client1.request
def get_image_piece(img_id, y_offset, img_size, username):
    img_id = img_id.replace("/", "").replace("\\", "")
    try:
        img = Image.open(f"/tmp/{img_id}").convert("RGBA")
    except:
        log("Failed to get image data from", img_id, "by", username)
        return "Error getting image data"
    img = img.resize((int(img_size), int(img_size)))
    width, height = img.size
    pixels = img.load()

    amount = 10
    colors = []
    for y in range(int(y_offset), int(y_offset) + int(amount)):
        for x in range(width):
            r, g, b, a = pixels[x, y]
            color = a * 16777216 + r * 65536 + g * 256 + b
            colors.append(color)
    log(username, 'requested image piece for image "' + img_id + '" with y offset', y_offset)
    return colors

@client1.request
def done(img_id):
    try:
        os.remove(f'/tmp/{str(img_id)}')
        log("Removing file", img_id)
        return "Done"
    except:
        return "Error deleting file"

@client1.event
def on_ready():
    log("Request handler is running")

cloud2 = sa.get_tw_cloud(1186198180)
client2 = cloud2.requests() 

@client2.request
def ping(username):  # called when client receives request
    log("Ping request received")
    return "pong"

@client2.request
def get_pfp(username):
    try:
        data = requests.get(f"https://api.scratch.mit.edu/users/{username}").json()
        user_id = data["id"]
    except:
        return "User Not Found"
    img_url = f"https://uploads.scratch.mit.edu/get_image/user/{user_id}_1000x1000.png"
    log(f"Image url: {img_url}")
    image_name = f"pfp{convertToNumber(username)}.png"
    urllib.request.urlretrieve(img_url, f"/tmp/{image_name}")
    log(f"Image stored in /tmp/{image_name}")
    return image_name

@client2.request
def get_image_piece(img_id, y_offset, img_size, username):
    img_id = img_id.replace("/", "").replace("\\", "")
    try:
        img = Image.open(f"/tmp/{img_id}").convert("RGBA")
    except:
        log("Failed to get image data from", img_id, "by", username)
        return "Error getting image data"
    img = img.resize((int(img_size), int(img_size)))
    width, height = img.size
    pixels = img.load()

    amount = 10
    colors = []
    for y in range(int(y_offset), int(y_offset) + int(amount)):
        for x in range(width):
            r, g, b, a = pixels[x, y]
            color = a * 16777216 + r * 65536 + g * 256 + b
            colors.append(color)
    log(username, 'requested image piece for image "' + img_id + '" with y offset', y_offset)
    return colors

@client2.request
def done(img_id):
    try:
        os.remove(f'/tmp/{str(img_id)}')
        log("Removing file", img_id)
        return "Done"
    except:
        return "Error deleting file"

@client2.event
def on_ready():
    log("Request handler is running")


keep_alive()
client1.start()
client2.start()
log("Started stuff")

