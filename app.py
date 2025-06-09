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
session = sa.login('Dev-Server', session_ps)
cloud1 = session.connect_cloud(1186198180)
client1 = cloud1.requests()

# --- Shared logic for get_pfp and gif ---

def handle_get_pfp(username):
    try:
        data = requests.get(f"https://api.scratch.mit.edu/users/{username}").json()
        user_id = data["id"]
    except:
        return "User Not Found"

    img_url = f"https://uploads.scratch.mit.edu/get_image/user/{user_id}_1000x1000.png"
    image_name = f"pfp{convertToNumber(username)}.png"
    image_path = f"/tmp/{image_name}"

    try:
        urllib.request.urlretrieve(img_url, image_path)
        img = Image.open(image_path)
        if getattr(img, "is_animated", False) and getattr(img, "n_frames", 1) > 1:
            log("Animated GIF detected inside PNG for", username)
            os.remove(image_path)
            return "GIF"
    except Exception as e:
        log("Failed to process profile picture:", e)
        return "Error processing image"

    log(f"Image stored in {image_path}")
    return image_name

def handle_gif(username, quality):
    try:
        data = requests.get(f"https://api.scratch.mit.edu/users/{username}").json()
        user_id = data["id"]
    except:
        return "User Not Found"

    img_url = f"https://uploads.scratch.mit.edu/get_image/user/{user_id}_1000x1000.png"
    image_name = f"pfp{convertToNumber(username)}.png"
    path = f"/tmp/{image_name}"

    try:
        urllib.request.urlretrieve(img_url, path)
    except:
        return "Failed to download profile picture"

    try:
        img = Image.open(path)
        if not (getattr(img, "is_animated", False) and getattr(img, "n_frames", 1) > 1):
            return "Not a GIF"
        img.seek(0)  # First frame
        frame = img.convert("RGBA")
    except:
        return "Failed to open image"

    try:
        size = int(quality)
        frame = frame.resize((size, size))
    except:
        return "Invalid quality"

    pixels = frame.load()
    width, height = frame.size
    colors = []

    for y in range(height):
        for x in range(width):
            r, g, b, a = pixels[x, y]
            color = a * 16777216 + r * 65536 + g * 256 + b
            colors.append(color)

    log(f"Returning {len(colors)} colors from GIF for", username)
    return colors

# --- Shared get_image_piece and done ---
def handle_image_piece(img_id, y_offset, img_size, username):
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

def handle_done(img_id):
    try:
        os.remove(f'/tmp/{str(img_id)}')
        log("Removing file", img_id)
        return "Done"
    except:
        return "Error deleting file"

# === CLIENT 1 ===

@client1.request
def ping(username):
    log("Ping request received")
    return "pong"

@client1.request
def get_pfp(username):
    return handle_get_pfp(username)

@client1.request
def gif(username, quality):
    return handle_gif(username, quality)

@client1.request
def get_image_piece(img_id, y_offset, img_size, username):
    return handle_image_piece(img_id, y_offset, img_size, username)

@client1.request
def done(img_id):
    return handle_done(img_id)

@client1.event
def on_ready():
    log("Request handler is running for client1")

# === CLIENT 2 ===

cloud2 = sa.get_tw_cloud(1186198180)
client2 = cloud2.requests()

@client2.request
def ping(username):
    log("Ping request received")
    return "pong"

@client2.request
def get_pfp(username):
    return handle_get_pfp(username)

@client2.request
def gif(username, quality):
    return handle_gif(username, quality)

@client2.request
def get_image_piece(img_id, y_offset, img_size, username):
    return handle_image_piece(img_id, y_offset, img_size, username)

@client2.request
def done(img_id):
    return handle_done(img_id)

@client2.event
def on_ready():
    log("Request handler is running for client2")

# === Start Everything ===

keep_alive()
client1.start()
client2.start()
log("Started both clients")
