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

def get_follower_count(username):
    url = f"https://api.scratch.mit.edu/users/{username}/followers"
    offset = 0
    limit = 40
    count = 0

    while True:
        res = requests.get(f"{url}?offset={offset}&limit={limit}")
        data = res.json()
        if not data:
            break
        count += len(data)
        offset += limit

    return count
    
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
def count(user):
    return sa.get_user(user.replace(" ", "")).follower_count()
    
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
def count(user):
    return sa.get_user(user.replace(" ", "")).follower_count()
    
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

cloud3 = session.connect_cloud(1186838073) 
client3 = cloud3.requests()

@client3.request
def count(user, something):
    return sa.get_user(user.replace(" ", "")).follower_count()

@client3.request
def pfp(user):
    try:
        data = requests.get(f"https://api.scratch.mit.edu/users/{user}").json()
        user_id = data["id"]
    except:
        return "User Not Found"

    img_url = f"https://uploads.scratch.mit.edu/get_image/user/{user_id}_1000x1000.png"
    image_path = f"/tmp/pfp_{user}.png"

    try:
        urllib.request.urlretrieve(img_url, image_path)
        img = Image.open(image_path).convert("RGBA")
        img = img.resize((100, 100))
    except Exception as e:
        log("Error downloading or processing image:", e)
        return "Error"

    pixels = img.load()
    colors = []
    for y in range(100):
        for x in range(100):
            r, g, b, a = pixels[x, y]
            color = a * 16777216 + r * 65536 + g * 256 + b
            colors.append(color)

    log(f"Returning {len(colors)} colors for", user)
    return colors

@client3.request
def ping():
    return "pong" 

cloud4 = session.connect_cloud(1191148134)
client4 = cloud4.requests()

@client4.request
def ping(username):
    log("Ping request received")
    return "pong"

@client4.request
def get_pfp(username):
    return handle_get_pfp(username)

@client4.request
def gif(username, quality):
    return handle_gif(username, quality)

@client4.request
def count(user):
    return sa.get_user(user.replace(" ", "")).message_count()
    
@client4.request
def get_image_piece(img_id, y_offset, img_size, username):
    return handle_image_piece(img_id, y_offset, img_size, username)

@client4.request
def done(img_id):
    return handle_done(img_id)

@client4.event
def on_ready():
    log("Request handler is running for client1")

cloud5 = session.connect_cloud(1192979296)
client5 = cloud5.requests()

# Directory to store chat histories per user
CHAT_DIR = "chat_histories"
os.makedirs(CHAT_DIR, exist_ok=True)

CHAT_LIMIT = 15


def load_chat_history(user, chat_name):
    filepath = os.path.join(CHAT_DIR, f"{user}_{chat_name}.json")
    if os.path.exists(filepath):
        with open(filepath, "r") as file:
            return json.load(file)
    return []


def save_chat_history(user, chat_name, history):
    filepath = os.path.join(CHAT_DIR, f"{user}_{chat_name}.json")
    with open(filepath, "w") as file:
        json.dump(history, file, indent=2)


def get_available_chat_name(user, base_name="chat"):
    for i in range(1, 100):
        name = f"{base_name}_{i}"
        filepath = os.path.join(CHAT_DIR, f"{user}_{name}.json")
        if not os.path.exists(filepath):
            return name
        with open(filepath, "r") as file:
            history = json.load(file)
            if len(history) < CHAT_LIMIT:
                return name
    return f"{base_name}_overflow"


def askAI(prompt, user, chat_name=None):
    API_KEY = os.getenv("APIKEY")
    API_URL = os.getenv("APIURL") + API_KEY

    # Determine or create chat
    if not chat_name:
        chat_name = get_available_chat_name(user)

    chat_history = load_chat_history(user, chat_name)

    # Build full history with new prompt
    chat_history.append({
        "role": "user",
        "parts": [{
            "text": f"You are an AI for scratch.If you are asked who made you reply with, i was made by The ScratchGPT team and that you were mostly made by kRxZy_kRxZy You can only write 100 words max, cannot say anything inappropriate for children under 12, cannot use markdown, images, or canvas code. Only return plain text. You can do math or any logical question but mostly about scratch. Question: '{prompt}'"
        }]
    })

    payload = {"contents": chat_history[-CHAT_LIMIT:]}

    # Make request
    try:
        response = requests.post(API_URL, json=payload)
        response.raise_for_status()
        data = response.json()

        # Parse reply
        reply = data.get("candidates", [])[0].get("content", {}).get("parts", [])[0].get("text", "")

        chat_history.append({
            "role": "model",
            "parts": [{"text": reply}]
        })
        save_chat_history(user, chat_name, chat_history)

        return reply
    except Exception as e:
        return "Failed To Get Response!"

@client5.request
def ping():
    return "AI: Welcome To ScratchGPT, Ask Any Question You Want!"

@client5.request
def ask(prompt, user):
    return f"AI: {askAI(prompt, user)}"

# === Start Everything ===

keep_alive()
client1.start()
client2.start()
client3.start()
client4.start()
client5.start()
log("Started all clients")
