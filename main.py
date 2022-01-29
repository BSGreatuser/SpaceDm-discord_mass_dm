import json, discord, asyncio, random, sqlite3, functions, requests, threading, time

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
        if message.content.startswith("!생성 "):
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
        
        if message.content.startswith("!충전 "):
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
                    await message.channel.send(f"{amount}원이 충전되었습니다.\n현재 잔액: {userinfo(message.author.id)[1]}")
                    await client.get_channel(config["log_channel_id"]).send(f"<@{message.author.id}> 님이 {amount}원을 충전하셨습니다.")
                else:
                    await message.channel.send(f"코드가 올바르지 않습니다.")
            else:
                await message.channel.send(f"가입이 되어있지 않습니다.\n!가입 명령어로 가입하실 수 있습니다.")

        if message.content == "!재고":
            highest_tokens = open("tokens.txt", "r").read()
            if highest_tokens == "":
                highest_tokens = 0
            else:
                highest_tokens = len(highest_tokens.split("\n"))
            await message.channel.send(f"{highest_tokens}개")

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
                            await message.author.send("토큰을 입력해주세요. (파싱할 서버에 들어가있는 토큰)")
                        except:
                            ing.remove({
                                "id": message.author.id,
                                "user_count": u
                            })
                            await message.channel.send("디엠을 막았는지 확인해주세요.")
                            return
                        await message.channel.send("디엠을 확인해주세요.")
                        try:
                            token = await client.wait_for("message", timeout=60, check=check)
                        except asyncio.TimeoutError:
                            ing.remove({
                                "id": message.author.id,
                                "user_count": u
                            })
                            try:
                                await message.author.send("시간 초과")
                            except:
                                pass
                            return
                        await message.author.send("서버 아이디를 입력해주세요.")
                        try:
                            guild_id = await client.wait_for("message", timeout=60, check=check)
                        except asyncio.TimeoutError:
                            ing.remove({
                                "id": message.author.id,
                                "user_count": u
                            })
                            try:
                                await message.author.send("시간 초과")
                            except:
                                pass
                            return
                        if not guild_id.content in open("white_list.txt", "r").read().split("\n"):
                            await message.author.send("채널 아이디를 입력해주세요.")
                            try:
                                channel_id = await client.wait_for("message", timeout=60, check=check)
                            except asyncio.TimeoutError:
                                ing.remove({
                                    "id": message.author.id,
                                    "user_count": u
                                })
                                try:
                                    await message.author.send("시간 초과")
                                except:
                                    pass
                                return
                            await message.author.send("서버 초대링크를 입력해주세요. (discord.gg/hackingtoken X hackingtoken O)")
                            try:
                                invite_code = await client.wait_for("message", timeout=60, check=check)
                            except asyncio.TimeoutError:
                                ing.remove({
                                    "id": message.author.id,
                                    "user_count": u
                                })
                                try:
                                    await message.author.send("시간 초과")
                                except:
                                    pass
                                return
                            await message.author.send("메시지 내용을 입력해주세요. ([@tag] = 유저맨션)")
                            try:
                                content = await client.wait_for("message", timeout=60, check=check)
                            except asyncio.TimeoutError:
                                ing.remove({
                                    "id": message.author.id,
                                    "user_count": u
                                })
                                try:
                                    await message.author.send("시간 초과")
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
                                                        await msg.edit(content=f"총 유저 수 : {len(members)}명/예상 차감 금액 : {z}원")

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
                                                                    await msg.edit(content=f"성공 : {c}/실패 : {len(members) - c}\n차감된 금액 : {cha}원/환불된 금액 : {hwan}원\n걸린 시간 : {end-start}")
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
                                                        await client.get_channel(config["log_channel_id"]).send(f"뒷메 로그\n\n`유저 카운트 : {u}\n\n아이디 : {message.author.id}\n이름#태그 : {message.author}\n성공 : {c}\n실패 : {len(members) - c}\n총 유저 : {len(members)}\n메시지 내용 : {content.content}\n차감 금액 : {cha}원\n환불 금액 : {hwan}원\n사용한 토큰 개수 : {token_amount}개\n\n서버 아이디 : {guild_id.content}\n채널 아이디 : {channel_id.content}\n초대링크 : {invite_code.content}\n\n걸린 시간 : {end-start}`")
                                                        c = 0
                                                        c_ = 0
                                                    except:
                                                        con = sqlite3.connect("db.db")
                                                        cur = con.cursor()
                                                        cur.execute("UPDATE users SET money = ? WHERE id == ?;", (userinfo(message.author.id)[1] + config["price"] * len(members), message.author.id))
                                                        con.commit()
                                                        con.close()
                                                        await msg.edit(content=f"뒷메 중 알수없는 오류가 발생했습니다.")
                                                else:
                                                    await msg.edit(content="잔액이 부족합니다.\n필요한 금액 : " + str(config["price"] * len(members)) + "원, 현재 잔액 : " + str(userinfo(message.author.id)[1]) + "원")
                                            else:
                                                await msg.edit(content="토큰이 부족합니다.")
                                        except:
                                            await msg.edit(content=f"뒷메 중 알수없는 오류가 발생했습니다.")
                                    else:
                                        await message.author.send("서버 초대링크가 올바르지 않습니다.")
                                else:
                                    await message.author.send("서버 아이디 또는 채널 아이디가 올바르지 않습니다.")
                            else:
                                await message.author.send("토큰이 올바르지 않습니다.")
                        else:
                            await message.author.send("보호되어있는 서버입니다.")
                    except:
                        await message.author.send(f"뒷메 중 알수없는 오류가 발생했습니다.")
                    ing.remove({
                        "id": message.author.id,
                        "user_count": u
                    })
                else:
                    await message.channel.send(f"이미 뒷메를 진행중인 사람이 있습니다.")
            else:
                await message.channel.send(f"가입이 되어있지 않습니다.\n!가입 명령어로 가입하실 수 있습니다.")

        if message.content == "!잔액":
            if userinfo(message.author.id) != None:
                await message.channel.send(str(userinfo(message.author.id)[1]) + "원")
            else:
                await message.channel.send(f"가입이 되어있지 않습니다.\n!가입 명령어로 가입하실 수 있습니다.")

        if message.content.startswith("!잔액 "):
            try:
                user_id = message.mentions[0].id
            except:
                return
            if userinfo(user_id) != None:
                await message.channel.send(str(userinfo(user_id)[1]) + "원")
            else:
                await message.channel.send(f"가입이 되어있지 않습니다.\n!가입 명령어로 가입하실 수 있습니다.")

        if message.content == "!가입":
            if userinfo(message.author.id) == None:
                con = sqlite3.connect("db.db")
                cur = con.cursor()
                cur.execute("INSERT INTO users Values(?, ?);", (message.author.id, 0))
                con.commit()
                await client.get_channel(config["log_channel_id"]).send(f"{message.author.id}님이 가입하셨습니다.")
                await message.channel.send("성공적으로 가입되었습니다.")
            else:
                await message.channel.send(f"이미 가입이 되어있습니다.")

        if message.content == "!쇼트 생성":
            def check(msg):
                return (isinstance(msg.channel, discord.channel.DMChannel) and (message.author.id == msg.author.id))
            try:
                await message.author.send("서버 아이디를 입력해주세요.")
            except:
                await message.channel.send("디엠을 막았는지 확인해주세요.")
                return
            await message.channel.send("디엠을 확인해주세요.")
            try:
                guild_id = await client.wait_for("message", timeout=60, check=check)
            except asyncio.TimeoutError:
                try:
                    await message.author.send("시간 초과")
                except:
                    pass
                return
            await message.author.send("채널 아이디를 입력해주세요.")
            try:
                channel_id = await client.wait_for("message", timeout=60, check=check)
            except asyncio.TimeoutError:
                try:
                    await message.author.send("시간 초과")
                except:
                    pass
                return
            await message.author.send("서버 초대링크를 입력해주세요.")
            try:
                invite_code = await client.wait_for("message", timeout=60, check=check)
            except asyncio.TimeoutError:
                try:
                    await message.author.send("시간 초과")
                except:
                    pass
                return

client.run(config["token"])
