import json, discord, asyncio, random, sqlite3, functions, requests, threading, time, webbrowser

from discord import channel

client = discord.Client()

c = 0
c_ = 0
joined_token = []
invalid = []
config = json.loads(open("config.json", "r", encoding="utf-8").read())
ing = [

]
user_count = 0
use_tokens_ = []
member_verificationed_tokens = []

def userinfo(id):
    con = sqlite3.connect("db.db")
    cur = con.cursor()
    cur.execute(f"SELECT * FROM users WHERE id == ?;", (id,))
    userinfo = cur.fetchone()
    con.close()
    return userinfo

def gen_code(pick):
    code = ""
    for _ in range(pick):
        code += random.choice("QWERTYUIOPASDFGHJKLZXCVBNM1234567890")
    return code

async def mass_dm(tokens, user_id, invite, content, guild_id):
    while True:
        try:
            global c
            global c_
            global invalid
            global use_tokens_
            token = random.choice(tokens)
            try:
                token = token.split(":")[2]
            except:
                pass
            use_tokens_.append(token)
            if not token in invalid:
                token_status = functions.check_token(token)
                if token_status == 200:
                    functions.ready(token)
                    if not token in joined_token:
                        joined_token.append(token)
                        join = functions.join_server(token, invite)
                        if join != 200:
                            c_ += 1
                            break
                    if not token in member_verificationed_tokens:
                        member_verificationed_tokens.append(token)
                        functions.member_verification(token, guild_id, invite)
                    send = functions.send_dm(token, user_id, content)
                    token_status = functions.check_token(token)
                    if "content" in send[1]:
                        if functions.check_token(token) != 200:
                            invalid.append(token)
                        c += 1
                        c_ += 1
                        break
                    else:
                        if token_status == 401:
                            invalid.append(token)
                        elif token_status == 403:
                            invalid.append(token)
                        elif send[0] == 429:
                            pass
                        else:
                            c_ += 1
                            break
                elif token_status == 401:
                    invalid.append(token)
                elif token_status == 403:
                    invalid.append(token)
        except:
            pass

async def st(tokens, user_id, invite, content, guild_id):
    await asyncio.gather(mass_dm(tokens, user_id, invite, content, guild_id))

@client.event
async def on_ready():
    print(f"CLIENT ID : {client.user.id}")

@client.event
async def on_message(message):
    global invalid
    global c
    global c_
    global ing
    global joined_token
    global user_count
    global use_tokens_
    if not isinstance(message.channel, discord.channel.DMChannel):
        if message.content.startswith("!?????? "):
            if message.author.id in config["admin_ids"]:
                try:
                    gen_amount = int(message.content.split(" ")[1])
                    gen_money_amount = int(message.content.split(" ")[2])
                except:
                    return
                codes = []
                con = sqlite3.connect("db.db")
                cur = con.cursor()
                for _ in range(gen_amount):
                    code = gen_code(15)
                    codes.append(code)
                    cur.execute("INSERT INTO codes Values(?, ?);", (code, gen_money_amount))
                    con.commit()
                con.close()
                if len("\n".join(codes)) < 2000:
                    await message.channel.send("\n".join(codes))
        
        if message.content.startswith("!?????? "):
            if userinfo(message.author.id) != None:
                code = message.content.split(" ")[1]
                con = sqlite3.connect("db.db")
                cur = con.cursor()
                cur.execute(f"SELECT * FROM codes WHERE code == ?;", (code,))
                codeinfo = cur.fetchone()
                con.close()
                if codeinfo != None:
                    amount = codeinfo[1]
                    con = sqlite3.connect("db.db")
                    cur = con.cursor()
                    cur.execute("UPDATE users SET money = ? WHERE id == ?;", (amount + userinfo(message.author.id)[1], message.author.id))
                    con.commit()
                    cur.execute("DELETE FROM codes WHERE code == ?;", (code,))
                    con.commit()
                    con.close()
                    await message.channel.send(f"{amount}?????? ?????????????????????.\n?????? ??????: {userinfo(message.author.id)[1]}")
                    await client.get_channel(config["log_channel_id"]).send(f"<@{message.author.id}> ?????? {amount}?????? ?????????????????????.")
                else:
                    await message.channel.send(f"????????? ???????????? ????????????.")
            else:
                await message.channel.send(f"????????? ???????????? ????????????.\n!?????? ???????????? ???????????? ??? ????????????.")

        if message.content == "!??????":
            highest_tokens = open("tokens.txt", "r").read()
            if highest_tokens == "":
                highest_tokens = 0
            else:
                highest_tokens = len(highest_tokens.split("\n"))
            await message.channel.send(f"{highest_tokens}???")

        if message.content == "!dm":
            def check(msg):
                return (isinstance(msg.channel, discord.channel.DMChannel) and (message.author.id == msg.author.id))
            if userinfo(message.author.id) != None:
                if ing == []:
                    user_count += 1
                    ing.append({
                        "id": message.author.id,
                        "user_count": user_count
                    })
                    u = user_count
                    try:
                        try:
                            await message.author.send("????????? ??????????????????. (????????? ????????? ??????????????? ??????)")
                        except:
                            ing.remove({
                                "id": message.author.id,
                                "user_count": u
                            })
                            await message.channel.send("????????? ???????????? ??????????????????.")
                            return
                        await message.channel.send("????????? ??????????????????.")
                        try:
                            token = await client.wait_for("message", timeout=60, check=check)
                        except asyncio.TimeoutError:
                            ing.remove({
                                "id": message.author.id,
                                "user_count": u
                            })
                            try:
                                await message.author.send("?????? ??????")
                            except:
                                pass
                            return
                        await message.author.send("?????? ???????????? ??????????????????.")
                        try:
                            guild_id = await client.wait_for("message", timeout=60, check=check)
                        except asyncio.TimeoutError:
                            ing.remove({
                                "id": message.author.id,
                                "user_count": u
                            })
                            try:
                                await message.author.send("?????? ??????")
                            except:
                                pass
                            return
                        if not guild_id.content in open("white_list.txt", "r").read().split("\n"):
                            await message.author.send("?????? ???????????? ??????????????????.")
                            try:
                                channel_id = await client.wait_for("message", timeout=60, check=check)
                            except asyncio.TimeoutError:
                                ing.remove({
                                    "id": message.author.id,
                                    "user_count": u
                                })
                                try:
                                    await message.author.send("?????? ??????")
                                except:
                                    pass
                                return
                            await message.author.send("?????? ??????????????? ??????????????????. (discord.gg/hackingtoken X hackingtoken O)")
                            try:
                                invite_code = await client.wait_for("message", timeout=60, check=check)
                            except asyncio.TimeoutError:
                                ing.remove({
                                    "id": message.author.id,
                                    "user_count": u
                                })
                                try:
                                    await message.author.send("?????? ??????")
                                except:
                                    pass
                                return
                            await message.author.send("????????? ????????? ??????????????????. ([@tag] = ????????????)")
                            try:
                                content = await client.wait_for("message", timeout=60, check=check)
                            except asyncio.TimeoutError:
                                ing.remove({
                                    "id": message.author.id,
                                    "user_count": u
                                })
                                try:
                                    await message.author.send("?????? ??????")
                                except:
                                    pass
                                return
                            if functions.check_token(token.content) == 200:
                                if functions.check_channel(token.content, guild_id.content, channel_id.content):
                                    invite_status = functions.join_server(token.content, invite_code.content)
                                    if invite_status[0] == 200 and invite_status[1]["guild"]["id"] == guild_id.content:
                                        req = requests.get("https://discord.com/api/v9/users/@me", headers=functions.Header(token.content))
                                        username = req.json()["username"]
                                        discriminator = req.json()["discriminator"]
                                        msg = await message.author.send(f"Parsing....../{username}#{discriminator}")
                                        try:
                                            members = functions.parse(token.content, guild_id.content, channel_id.content)
                                            token_amount = int(str(len(members) / config["send_amount"]).split(".")[0]) + 1
                                            if token_amount <= len(open("tokens.txt", "r").read().split("\n")):
                                                if userinfo(message.author.id)[1] >= config["price"] * len(members):
                                                    con = sqlite3.connect("db.db")
                                                    cur = con.cursor()
                                                    cur.execute("UPDATE users SET money = ? WHERE id == ?;", (userinfo(message.author.id)[1] - config["price"] * len(members), message.author.id))
                                                    con.commit()
                                                    con.close()
                                                    try:
                                                        z = config["price"] * len(members)
                                                        await msg.edit(content=f"??? ?????? ??? : {len(members)}???/?????? ?????? ?????? : {z}???")

                                                        tokens = []

                                                        use_token_amount = token_amount

                                                        for _ in range(use_token_amount):
                                                            token = random.choice(open("tokens.txt", "r", encoding="utf-8").read().split("\n"))
                                                            tokens.append(token)
                                                        else:
                                                            start = time.time()
                                                            don_not_send_ids = open("don't send ids.txt", "r").read()
                                                            for user_id in members:
                                                                if not user_id in don_not_send_ids:
                                                                    threading.Thread(target=asyncio.run, args=(st(tokens, user_id, invite_code.content, content.content, guild_id.content),)).start()
                                                                    await asyncio.sleep(config["delay"])
                                                                else:
                                                                    c += 1
                                                                    c_ += 1
                                                            while True:
                                                                if c_ == len(members):
                                                                    for token in joined_token:
                                                                        threading.Thread(target=functions.leave_server, args=(token, guild_id.content,)).start()
                                                                    cha = config["price"] * c
                                                                    hwan = config["price"] * len(members) - config["price"] * c
                                                                    con = sqlite3.connect("db.db")
                                                                    cur = con.cursor()
                                                                    cur.execute("UPDATE users SET money = ? WHERE id == ?;", (userinfo(message.author.id)[1] + hwan, message.author.id))
                                                                    con.commit()
                                                                    con.close()
                                                                    end = time.time()
                                                                    await msg.edit(content=f"?????? : {c}/?????? : {len(members) - c}\n????????? ?????? : {cha}???/????????? ?????? : {hwan}???\n?????? ?????? : {end-start}")
                                                                    break
                                                        valid = []
                                                        ut = []
                                                        for token in open("tokens.txt", "r", encoding="utf-8").read().split("\n"):
                                                            try:
                                                                t = token.split(":")[2]
                                                            except:
                                                                t = token
                                                            if not t in use_tokens_:
                                                                valid.append(token)
                                                            else:
                                                                ut.append(token)
                                                        open("used_tokens.txt", "a").write("\n".join(ut) + "\n")
                                                        open("tokens.txt", "w").write("\n".join(valid))
                                                        invalid = []
                                                        valid = []
                                                        joined_token = []
                                                        await client.get_channel(config["log_channel_id"]).send(f"?????? ??????\n\n`?????? ????????? : {u}\n\n????????? : {message.author.id}\n??????#?????? : {message.author}\n?????? : {c}\n?????? : {len(members) - c}\n??? ?????? : {len(members)}\n????????? ?????? : {content.content}\n?????? ?????? : {cha}???\n?????? ?????? : {hwan}???\n????????? ?????? ?????? : {token_amount}???\n\n?????? ????????? : {guild_id.content}\n?????? ????????? : {channel_id.content}\n???????????? : {invite_code.content}\n\n?????? ?????? : {end-start}`")
                                                        c = 0
                                                        c_ = 0
                                                    except:
                                                        con = sqlite3.connect("db.db")
                                                        cur = con.cursor()
                                                        cur.execute("UPDATE users SET money = ? WHERE id == ?;", (userinfo(message.author.id)[1] + config["price"] * len(members), message.author.id))
                                                        con.commit()
                                                        con.close()
                                                        await msg.edit(content=f"?????? ??? ???????????? ????????? ??????????????????.")
                                                else:
                                                    await msg.edit(content="????????? ???????????????.\n????????? ?????? : " + str(config["price"] * len(members)) + "???, ?????? ?????? : " + str(userinfo(message.author.id)[1]) + "???")
                                            else:
                                                await msg.edit(content="????????? ???????????????.")
                                        except:
                                            await msg.edit(content=f"?????? ??? ???????????? ????????? ??????????????????.")
                                    else:
                                        await message.author.send("?????? ??????????????? ???????????? ????????????.")
                                else:
                                    await message.author.send("?????? ????????? ?????? ?????? ???????????? ???????????? ????????????.")
                            else:
                                await message.author.send("????????? ???????????? ????????????.")
                        else:
                            await message.author.send("?????????????????? ???????????????.")
                    except:
                        await message.author.send(f"?????? ??? ???????????? ????????? ??????????????????.")
                    ing.remove({
                        "id": message.author.id,
                        "user_count": u
                    })
                else:
                    await message.channel.send(f"?????? ????????? ???????????? ????????? ????????????.")
            else:
                await message.channel.send(f"????????? ???????????? ????????????.\n!?????? ???????????? ???????????? ??? ????????????.")

        if message.content == "!??????":
            if userinfo(message.author.id) != None:
                await message.channel.send(str(userinfo(message.author.id)[1]) + "???")
            else:
                await message.channel.send(f"????????? ???????????? ????????????.\n!?????? ???????????? ???????????? ??? ????????????.")

        if message.content.startswith("!?????? "):
            try:
                user_id = message.mentions[0].id
            except:
                return
            if userinfo(user_id) != None:
                await message.channel.send(str(userinfo(user_id)[1]) + "???")
            else:
                await message.channel.send(f"????????? ???????????? ????????????.\n!?????? ???????????? ???????????? ??? ????????????.")

        if message.content == "!??????":
            if userinfo(message.author.id) == None:
                con = sqlite3.connect("db.db")
                cur = con.cursor()
                cur.execute("INSERT INTO users Values(?, ?);", (message.author.id, 0))
                con.commit()
                await client.get_channel(config["log_channel_id"]).send(f"{message.author.id}?????? ?????????????????????.")
                await message.channel.send("??????????????? ?????????????????????.")
            else:
                await message.channel.send(f"?????? ????????? ??????????????????.")

        if message.content == "!?????? ??????":
            def check(msg):
                return (isinstance(msg.channel, discord.channel.DMChannel) and (message.author.id == msg.author.id))
            try:
                await message.author.send("?????? ???????????? ??????????????????.")
            except:
                await message.channel.send("????????? ???????????? ??????????????????.")
                return
            await message.channel.send("????????? ??????????????????.")
            try:
                guild_id = await client.wait_for("message", timeout=60, check=check)
            except asyncio.TimeoutError:
                try:
                    await message.author.send("?????? ??????")
                except:
                    pass
                return
            await message.author.send("?????? ???????????? ??????????????????.")
            try:
                channel_id = await client.wait_for("message", timeout=60, check=check)
            except asyncio.TimeoutError:
                try:
                    await message.author.send("?????? ??????")
                except:
                    pass
                return
            await message.author.send("?????? ??????????????? ??????????????????.")
            try:
                invite_code = await client.wait_for("message", timeout=60, check=check)
            except asyncio.TimeoutError:
                try:
                    await message.author.send("?????? ??????")
                except:
                    pass
                return
webbrowser.open("https://discord.gg/AFqvvdAdkY")
client.run(config["token"])
