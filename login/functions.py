from login.models import *
from pathlib import Path
from telegram.tgfunctions import send_alert
from SmartApi.smartConnect import SmartConnect
from datetime import datetime
from kiteconnect import KiteConnect,KiteTicker
import time, pyotp,requests
import os
from order_functions.aliceblue import *



BASE_DIR = Path(__file__).resolve().parent.parent

def login_zerodha(api_key, api_sec, user_id, password, pin):
    # user_id = 'KZ8816'
    # password = 'Aaradhy@1412'
    # pin = 'M6A5D5O3MQGOIVUTLDQYWFRUWORG6BUC'
    # api_key = "qv851japie2u9mzi"
    # api_sec = "txfvxle0mtndvd2xra0pnt7szw1y68q1"
    from django.db import connection
    import datetime
    login = False
    attempt = 0
    while login == False and attempt < 40:
        try:
            session = requests.Session()
            request_id = session.post("https://kite.zerodha.com/api/login", {"user_id": user_id, "password": password}).json()["data"]["request_id"]
            session.post("https://kite.zerodha.com/api/twofa",
                            {"user_id": user_id, "request_id": request_id, "twofa_value": pyotp.TOTP(pin).now(), "twofa_type": "totp",
                            "skip_session": True})
            b = session.get(f'https://kite.trade/connect/login?api_key={api_key}&v=3')
            import time
            time.sleep(5)
            url = b.url
            print(url)
            request_token = url.split("request_token=")[1]
            from kiteconnect import KiteConnect
            from kiteconnect import KiteTicker
            kite = KiteConnect(api_key = api_key)
            data = kite.generate_session(request_token, api_secret=api_sec)
            kite.set_access_token(data['access_token'])
            kws = KiteTicker(api_key, data['access_token'])
            name = (kite.profile())['user_name']
            funds = (kite.margins())['equity']['available']['live_balance']


            AngelTable.objects.filter(UserID=user_id).update(AccessToken=data['access_token'])
            AngelTable.objects.filter(UserID=user_id).update(LastLoginStatus=True)
            AngelTable.objects.filter(UserID=user_id).update(LastLoginMessage="success")
            AngelTable.objects.filter(UserID=user_id).update(LastLoginTime=datetime.datetime.now())
            AngelTable.objects.filter(UserID=user_id).update(OpeningBalance=funds)
            AngelTable.objects.filter(UserID=user_id).update(ClientName=name)
            connection.close()
            

            login = True
            attempt += 1
        except:
            pass

    if login:
        send_alert(f"Login Successful for {user_id} ({name}), opening balance: {funds}")
    else:
        send_alert(f"Login Failed for Zerodha : {user_id}")

def login_angel(id, password, api_key, totp_key):
    from SmartApi.smartConnect import SmartConnect
    from datetime import datetime
    from django.db import connection
    import pyotp
    object = SmartConnect(api_key=api_key)
    try:
        data = object.generateSession(clientCode=str(id), password=str(password), totp=pyotp.TOTP(totp_key).now())
        bal = float(object.rmsLimit()['data']['availablecash'])
        prof = object.getProfile(refreshToken=object.refresh_token)
        name = prof['data']['name']

    except:
        try:
            data = object.generateSession(clientCode=str(id), password=str(password), totp=pyotp.TOTP(totp_key).now())
        except:
            data = {"status": False, "message": "Failed to login!"}
        bal = "Unavailable"
        name = "Unavailable"
    AngelTable.objects.filter(UserID=id).update(AccessToken=object.access_token)
    AngelTable.objects.filter(UserID=id).update(RefreshToken=object.refresh_token)
    AngelTable.objects.filter(UserID=id).update(FeedToken=object.feed_token)
    AngelTable.objects.filter(UserID=id).update(LastLoginStatus=data["status"])
    AngelTable.objects.filter(UserID=id).update(LastLoginMessage=data["message"])
    AngelTable.objects.filter(UserID=id).update(LastLoginTime=datetime.now())
    AngelTable.objects.filter(UserID=id).update(OpeningBalance=bal)
    AngelTable.objects.filter(UserID=id).update(ClientName=name.title())
    connection.close()

def get_session_id_alice(user_id, encKey, api_secret):
    import requests
    import json
    import hashlib
    url = 'https://ant.aliceblueonline.com/rest/AliceBlueAPIService/sso/getUserDetails'
    payload = json.dumps({
              "checkSum":hashlib.sha256((str(user_id)+encKey+api_secret).encode('utf-8')).hexdigest()
          })
    headers = {
      'Content-Type': 'application/json'
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    session_id = json.loads(response.text)["userSession"]
    return session_id


# user_id, password, yob, totp_key, api_key, api_secret = '1136697','Suraj1993@',"1991","JXEILVSGFFEXVVCKZOGLNEODSIWYUJZF","rmLd4Q7J4RSi58y","6SXtlX3u7Ep4LBpBM0MGyh2CHsvEdQ31Mo66PiZsytM6mzdRmphXIcp4W532BuzzOfADE3lkOAX09VV4nOH2cVCsuPuirxZSAovW"


def single_login_alice_v2(user_id, password, yob, totp_key, api_key, api_secret):
    from django.db import connection
    import requests
    import json
    import pyotp
    from datetime import datetime
    def pad(data):
        BLOCK_SIZE = 16
        length = BLOCK_SIZE - (len(data) % BLOCK_SIZE)
        return data + (chr(length) * length).encode()

    def bytes_to_key(data, salt, output=48):
        from hashlib import md5
        # extended from https://gist.github.com/gsakkis/4546068
        assert len(salt) == 8, len(salt)
        data += salt
        key = md5(data).digest()
        final_key = key
        while len(final_key) < output:
            key = md5(key + data).digest()
            final_key += key
        return final_key[:output]

    def encrypt(message, passphrase):
        import base64
        from Crypto.Cipher import AES
        from Crypto import Random
        salt = Random.new().read(8)
        key_iv = bytes_to_key(passphrase, salt, 32 + 16)
        key = key_iv[:32]
        iv = key_iv[32:]
        aes = AES.new(key, AES.MODE_CBC, iv)
        return base64.b64encode(b"Salted__" + salt + aes.encrypt(pad(message)))
    s = requests.Session()
    err_stat = "BLANK"
    r1 = s.get(f"https://ant.aliceblueonline.com/?appcode={api_key}")
    r2 = s.post('https://ant.aliceblueonline.com/omk/auth/access/client/verify', json={"userId": user_id})
    if r2.json()['status'].upper()!="OK":
        err_stat = r2.json()['message']
        print(err_stat)
        bal = "Unavailable"
        name = "Unavailable"
        AngelTable.objects.filter(UserID=user_id).update(LastLoginStatus=False)
        AngelTable.objects.filter(UserID=user_id).update(AccessToken="")
        AngelTable.objects.filter(UserID=user_id).update(LastLoginMessage="Failed")
        AngelTable.objects.filter(UserID=user_id).update(LastLoginTime=datetime.now())
        AngelTable.objects.filter(UserID=user_id).update(OpeningBalance=bal)
        AngelTable.objects.filter(UserID=user_id).update(ClientName=name.title())
        AngelTable.objects.filter(UserID=user_id).update(LastLoginMessage=err_stat)
        connection.close()
        return datetime.now()
    om = r2.json()['result'][0]['base'].lower()
    if om=="omt":
        r3 = s.post(f"https://ant.aliceblueonline.com/{om}/auth/access/client/enckey", json={"userId": user_id})
        key = r3.json()['result'][0]['encKey']
        enc = encrypt(password.encode(), key.encode()).decode()
        r4 = s.post(url=f'https://ant.aliceblueonline.com/{om}/auth/access/v1/pwd/validate', json={"userId": user_id, "userData": enc})
        if r4.json()["status"].upper() != "OK":
            err_stat = "Wrong Password"
            print(err_stat)
            bal = "Unavailable"
            name = "Unavailable"
            AngelTable.objects.filter(UserID=user_id).update(LastLoginStatus=False)
            AngelTable.objects.filter(UserID=user_id).update(AccessToken="")
            AngelTable.objects.filter(UserID=user_id).update(LastLoginMessage="Failed")
            AngelTable.objects.filter(UserID=user_id).update(LastLoginTime=datetime.now())
            AngelTable.objects.filter(UserID=user_id).update(OpeningBalance=bal)
            AngelTable.objects.filter(UserID=user_id).update(ClientName=name.title())
            AngelTable.objects.filter(UserID=user_id).update(LastLoginMessage=err_stat)
            connection.close()
            return datetime.now()
        r5 = s.post(f'https://ant.aliceblueonline.com/{om}/auth/access/valid2fa', json={'answer1': yob, 'userId': user_id, 'scount': "1", 'sindex': "1"})
        if r5.json()["status"].upper() != "OK":
            err_stat = "Wrong Year of Birth"
            print(err_stat)
            bal = "Unavailable"
            name = "Unavailable"
            AngelTable.objects.filter(UserID=user_id).update(LastLoginStatus=False)
            AngelTable.objects.filter(UserID=user_id).update(AccessToken="")
            AngelTable.objects.filter(UserID=user_id).update(LastLoginMessage="Failed")
            AngelTable.objects.filter(UserID=user_id).update(LastLoginTime=datetime.now())
            AngelTable.objects.filter(UserID=user_id).update(OpeningBalance=bal)
            AngelTable.objects.filter(UserID=user_id).update(ClientName=name.title())
            AngelTable.objects.filter(UserID=user_id).update(LastLoginMessage=err_stat)
            connection.close()
            return datetime.now()
        if r5.json()['result'][0]['loPreference'].upper()=="TOTP":
            r_totp = s.post(url=f'https://ant.aliceblueonline.com/{om}/auth/access/topt/verify', json={"userId":user_id,"totp":str(pyotp.TOTP(totp_key).now()),"source":"WEB","vendor":api_key})
            if r_totp.json()['status'].upper()!="OK":
                err_stat = "Invalid TOTP Key"
                bal = "Unavailable"
                name = "Unavailable"
                AngelTable.objects.filter(UserID=user_id).update(LastLoginStatus=False)
                AngelTable.objects.filter(UserID=user_id).update(AccessToken="")
                AngelTable.objects.filter(UserID=user_id).update(LastLoginMessage="Failed")
                AngelTable.objects.filter(UserID=user_id).update(LastLoginTime=datetime.now())
                AngelTable.objects.filter(UserID=user_id).update(OpeningBalance=bal)
                AngelTable.objects.filter(UserID=user_id).update(ClientName=name.title())
                AngelTable.objects.filter(UserID=user_id).update(LastLoginMessage=err_stat)
                connection.close()
                return datetime.now()
            r56 = s.post('https://ant.aliceblueonline.com/omk/auth/sso/vendor/authorize/check', json={"userId": user_id, "vendor": api_key})
            if not r56.json()['result'][0]['authorized']:
                r6 = s.post('https://ant.aliceblueonline.com/omk/auth/sso/vendor/authorize',
                            json={"userId": user_id, "vendor": api_key})
                urll = r6.json()['result'][0]['redirectUrl']
            else:
                urll = r56.json()['result'][0]['redirectUrl']
            try:
                encKey = urll.split('?authCode=')[-1].split('&')[0]
                user_id = urll.split('&userId=')[-1].split('&')[0]
                session_id = get_session_id_alice(user_id=user_id, encKey=encKey, api_secret=api_secret)
                print("Token generated")
            except:
                err_stat = "Invalid TOTP Key"
                session_id = ""
        else:
            err_stat = "TOTP Not set up"
            bal = "Unavailable"
            name = "Unavailable"
            AngelTable.objects.filter(UserID=user_id).update(LastLoginStatus=False)
            AngelTable.objects.filter(UserID=user_id).update(AccessToken="")
            AngelTable.objects.filter(UserID=user_id).update(LastLoginMessage="Failed")
            AngelTable.objects.filter(UserID=user_id).update(LastLoginTime=datetime.now())
            AngelTable.objects.filter(UserID=user_id).update(OpeningBalance=bal)
            AngelTable.objects.filter(UserID=user_id).update(ClientName=name.title())
            AngelTable.objects.filter(UserID=user_id).update(LastLoginMessage=err_stat)
            connection.close()
            return datetime.now()
        print(err_stat)
        if err_stat == "BLANK":
            prof = get_profile_alice(user_id=user_id, session_id=session_id)
            bb = get_balance_alice(user_id=user_id, session_id=session_id)
            name = prof['accountName']
            print("Balance found")
            try:
                bal = f"Cash/FNO = {str(bb[0]['net'])}, Commodity = {str(bb[1]['net'])}"
            except:
                try:
                    bal = f"Cash/FNO = {str(bb[0]['net'])}"
                except:
                    bal = "Unable to fetch"
            AngelTable.objects.filter(UserID=user_id).update(LastLoginStatus=True)
            AngelTable.objects.filter(UserID=user_id).update(AccessToken=session_id)
            AngelTable.objects.filter(UserID=user_id).update(LastLoginMessage="Success")
            AngelTable.objects.filter(UserID=user_id).update(LastLoginTime=datetime.now())
            AngelTable.objects.filter(UserID=user_id).update(OpeningBalance=bal)
            AngelTable.objects.filter(UserID=user_id).update(ClientName=name.title())
            AngelTable.objects.filter(UserID=user_id).update(LastLoginMessage=err_stat)

        else:
            bal = "Unavailable"
            name = "Unavailable"
            AngelTable.objects.filter(UserID=user_id).update(LastLoginStatus=False)
            AngelTable.objects.filter(UserID=user_id).update(AccessToken="")
            AngelTable.objects.filter(UserID=user_id).update(LastLoginMessage="Failed")
            AngelTable.objects.filter(UserID=user_id).update(LastLoginTime=datetime.now())
            AngelTable.objects.filter(UserID=user_id).update(OpeningBalance=bal)
            AngelTable.objects.filter(UserID=user_id).update(ClientName=name.title())
            AngelTable.objects.filter(UserID=user_id).update(LastLoginMessage=err_stat)
        connection.close()
        return datetime.now()
    else:
        r3 = s.post("https://ant.aliceblueonline.com/omk/auth/access/client/enckey", json={"userId": user_id})
        key = r3.json()['result'][0]['encKey']
        enc = encrypt(password.encode(), key.encode()).decode()
        r4 = s.post('https://ant.aliceblueonline.com/omk/auth/access/v1/pwd/validate', json={"userId": user_id, "userData": enc, "source":"WEB"})
        if r4.json()["status"].upper() != "OK":
            err_stat = "Wrong Password"
            print(err_stat)
            bal = "Unavailable"
            name = "Unavailable"
            AngelTable.objects.filter(UserID=user_id).update(LastLoginStatus=False)
            AngelTable.objects.filter(UserID=user_id).update(AccessToken="")
            AngelTable.objects.filter(UserID=user_id).update(LastLoginMessage="Failed")
            AngelTable.objects.filter(UserID=user_id).update(LastLoginTime=datetime.now())
            AngelTable.objects.filter(UserID=user_id).update(OpeningBalance=bal)
            AngelTable.objects.filter(UserID=user_id).update(ClientName=name.title())
            AngelTable.objects.filter(UserID=user_id).update(LastLoginMessage=err_stat)
            connection.close()
            return datetime.now()
        if r4.json()['result'][0]['totpAvailable']:
            r_totp = s.post('https://ant.aliceblueonline.com/omk/auth/access/topt/verify', headers={'Authorization': 'Bearer ' + str(user_id) + " WEB " + r4.json()['result'][0]['token']}, json={"userId": user_id, "totp": str(pyotp.TOTP(totp_key).now()), "source": "WEB", "vendor": api_key})
            if r_totp.json()['status'].upper() != "OK":
                err_stat = "Invalid TOTP Key"
                bal = "Unavailable"
                name = "Unavailable"
                AngelTable.objects.filter(UserID=user_id).update(LastLoginStatus=False)
                AngelTable.objects.filter(UserID=user_id).update(AccessToken="")
                AngelTable.objects.filter(UserID=user_id).update(LastLoginMessage="Failed")
                AngelTable.objects.filter(UserID=user_id).update(LastLoginTime=datetime.now())
                AngelTable.objects.filter(UserID=user_id).update(OpeningBalance=bal)
                AngelTable.objects.filter(UserID=user_id).update(ClientName=name.title())
                AngelTable.objects.filter(UserID=user_id).update(LastLoginMessage=err_stat)
                connection.close()
                return datetime.now()
            response = s.get('https://ant.aliceblueonline.com/omk/client-rest/profile/getUser', headers={
                'Authorization': 'Bearer ' + r_totp.json()['result'][0]['accessToken']
            }, data="")
            print(f"getUser status - {response.json()['status']}")
            r56 = s.post('https://ant.aliceblueonline.com/omk/auth/sso/vendor/authorize/check',
                         json={"userId": user_id, "vendor": api_key})
            if not r56.json()['result'][0]['authorized']:
                r6 = s.post('https://ant.aliceblueonline.com/omk/auth/sso/vendor/authorize',
                            json={"userId": user_id, "vendor": api_key})
                urll = r6.json()['result'][0]['redirectUrl']
            else:
                urll = r56.json()['result'][0]['redirectUrl']
            try:
                encKey = urll.split('?authCode=')[-1].split('&')[0]
                user_id = urll.split('&userId=')[-1].split('&')[0]
                session_id = get_session_id_alice(user_id=user_id, encKey=encKey, api_secret=api_secret)
                print("Token generated")
            except:
                err_stat = "Invalid TOTP Key"
                session_id = ""
        else:
            err_stat = "TOTP Not set up"
            bal = "Unavailable"
            name = "Unavailable"
            AngelTable.objects.filter(UserID=user_id).update(LastLoginStatus=False)
            AngelTable.objects.filter(UserID=user_id).update(AccessToken="")
            AngelTable.objects.filter(UserID=user_id).update(LastLoginMessage="Failed")
            AngelTable.objects.filter(UserID=user_id).update(LastLoginTime=datetime.now())
            AngelTable.objects.filter(UserID=user_id).update(OpeningBalance=bal)
            AngelTable.objects.filter(UserID=user_id).update(ClientName=name.title())
            AngelTable.objects.filter(UserID=user_id).update(LastLoginMessage=err_stat)
            connection.close()
            return datetime.now()
        print(err_stat)
        if err_stat == "BLANK":
            prof = get_profile_alice(user_id=user_id, session_id=session_id)
            bb = get_balance_alice(user_id=user_id, session_id=session_id)
            name = prof['accountName']
            print("Balance found")
            try:
                bal = f"Cash/FNO = {str(bb[0]['net'])}, Commodity = {str(bb[1]['net'])}"
            except:
                bal = f"Cash/FNO = {str(bb[0]['net'])}"
            AngelTable.objects.filter(UserID=user_id).update(LastLoginStatus=True)
            AngelTable.objects.filter(UserID=user_id).update(AccessToken=session_id)
            AngelTable.objects.filter(UserID=user_id).update(LastLoginMessage="Success")
            AngelTable.objects.filter(UserID=user_id).update(LastLoginTime=datetime.now())
            AngelTable.objects.filter(UserID=user_id).update(OpeningBalance=bal)
            AngelTable.objects.filter(UserID=user_id).update(ClientName=name.title())
            AngelTable.objects.filter(UserID=user_id).update(LastLoginMessage=err_stat)
        else:
            bal = "Unavailable"
            name = "Unavailable"
            AngelTable.objects.filter(UserID=user_id).update(LastLoginStatus=False)
            AngelTable.objects.filter(UserID=user_id).update(AccessToken="")
            AngelTable.objects.filter(UserID=user_id).update(LastLoginMessage="Failed")
            AngelTable.objects.filter(UserID=user_id).update(LastLoginTime=datetime.now())
            AngelTable.objects.filter(UserID=user_id).update(OpeningBalance=bal)
            AngelTable.objects.filter(UserID=user_id).update(ClientName=name.title())
            AngelTable.objects.filter(UserID=user_id).update(LastLoginMessage=err_stat)
        connection.close()
        return datetime.now()
