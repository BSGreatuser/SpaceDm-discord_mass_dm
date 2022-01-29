import discum, requests, websocket, random, json

tokens = []

def ready(token):
    ws = websocket.WebSocket()
    ws.connect("wss://gateway.discord.gg/?v=6&encoding=json")
    ws.send(json.dumps(
    {
    "op": 2,
    "d": {
        "token": token,
        "properties": {
            "$browser": "Yas",
            }
        }
    }
    ))

def pick(lenn):
    alpha = "abcdefghijklmnopqrstuvwxyz0123456789"
    text = ''
    for i in range(0, lenn):
        text += alpha[random.randint(0, len(alpha) - 1)]
    return text

def Header(token): 
    return {
        "authority": "discord.com",
        "method": "POST",
        "scheme": "https",
        "accept": "*/*",
        "accept-encoding": "gzip, deflate, br",
        "accept-language": "en-US",
        "Authorization": token,
        "content-length": "0",
        "cookie": f"__cfuid={pick(43)}; __dcfduid={pick(32)}; locale=en-US",
        "origin": "https://discord.com",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) discord/1.0.600 Chrome/91.0.4472.106 Electron/13.1.4 Safari/537.36",
        "x-context-properties": "eyJsb2NhdGlvbiI6Ikludml0ZSBCdXR0b24gRW1iZWQiLCJsb2NhdGlvbl9ndWlsZF9pZCI6Ijg3OTc4MjM4MDAxMTk0NjAyNCIsImxvY2F0aW9uX2NoYW5uZWxfaWQiOiI4ODExMDg4MDc5NjE0MTk3OTYiLCJsb2NhdGlvbl9jaGFubmVsX3R5cGUiOjAsImxvY2F0aW9uX21lc3NhZ2VfaWQiOiI4ODExOTkzOTI5MTExNTkzNTcifQ==",
        "x-debug-options": "bugReporterEnabled",
        "x-super-properties": "eyJvcyI6IldpbmRvd3MiLCJicm93c2VyIjoiRGlzY29yZCBDbGllbnQiLCJyZWxlYXNlX2NoYW5uZWwiOiJjYW5hcnkiLCJjbGllbnRfdmVyc2lvbiI6IjEuMC42MDAiLCJvc192ZXJzaW9uIjoiMTAuMC4yMjAwMCIsIm9zX2FyY2giOiJ4NjQiLCJzeXN0ZW1fbG9jYWxlIjoic2siLCJjbGllbnRfYnVpbGRfbnVtYmVyIjo5NTM1MywiY2xpZW50X2V2ZW50X3NvdXJjZSI6bnVsbH0="
    }

def check_channel(token, guild_id, channel_id):
    channels = requests.get(f"https://discord.com/api/v9/guilds/{guild_id}/channels", headers=Header(token)).json()
    for channel in channels:
        try:
            if channel["id"] == channel_id:
                if not "Missing" in str(requests.get(f"https://discord.com/api/v9/channels/{channel_id}/messages", headers=Header(token)).json()):
                    return True
        except:
            pass
    return False

def check_token(token):
    req = requests.get("https://discord.com/api/v9/users/@me/library", headers=Header(token))
    return req.status_code

def parse(token, guild_id, channel_id):
    bot = discum.Client(token=token, log=False)

    def close_after_fetching(resp, guild_id):
        if bot.gateway.finishedMemberFetching(guild_id):
            len(bot.gateway.session.guild(guild_id).members)
            bot.gateway.removeCommand({'function': close_after_fetching, 'params': {'guild_id': guild_id}})
            bot.gateway.close()

    def get_members(guild_id, channel_id):
        bot.gateway.fetchMembers(guild_id, channel_id, keep='all', wait=0)
        bot.gateway.command({'function': close_after_fetching, 'params': {'guild_id': guild_id}})
        bot.gateway.run()
        bot.gateway.resetSession()
        return bot.gateway.session.guild(guild_id).members

    try:
        members = get_members(guild_id=guild_id, channel_id=channel_id)
    except:
        return False
    return members

def join_server(token, invite):
    req = requests.post(f"https://discord.com/api/v9/invites/{invite}", headers=Header(token))
    return req.status_code, req.json()

def leave_server(token, server_id):
    while True:
        try:
            req = requests.delete(f"https://discord.com/api/v9/users/@me/guilds/{server_id}", headers=Header(token), json={
                "lurking": False
            })
            return req.status_code
        except:
            pass

def get_dm_channel_id(user_id, token):
    try:
        json = {
            "recipient_id" : user_id
        }
        headers = Header(token)
        res = requests.post(url="https://discordapp.com/api/v9/users/@me/channels", json=json, headers=headers)
        data = res.json()
        dm_channel_id = data['id']
        return dm_channel_id
    except:
        return False

def send_dm(token, user_id, content):
    dm_channel_id = get_dm_channel_id(user_id, token)
    req = requests.post(f"https://discordapp.com/api/v9/channels/{dm_channel_id}/messages", headers=Header(token), json={
        "content" : content.replace("[@tag]", f"<@{user_id}>"),
        "nonce" : f"81{random.randint(7006, 7310)}{random.randint(100000000, 999999999)}{random.randint(100, 999)}",
        "tts" : False
    })
    try:
        return req.status_code, req.json()
    except:
        return req.status_code, req.text()

def member_verification(token, guild_id, invite_code):
    try:
        req = requests.get(f"https://discord.com/api/v9/guilds/{guild_id}/member-verification?with_guild=false&invite_code={invite_code}", headers=Header(token))
        requests.put(f"https://discord.com/api/v9/guilds/{guild_id}/requests/@me", headers=Header(token), json=req.json())
    except:
        pass
    return