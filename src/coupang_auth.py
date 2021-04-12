import datetime
import hashlib
import hmac


def get_header(url: str, data: dict, method: str = 'GET', query=''):
    dt = datetime.datetime.utcnow().strftime("%y%m%dT%H%M%SZ")
    message = dt + method + url + query

    signature = hmac.new(data.get('secret_key').encode('utf-8'), message.encode('utf-8'), hashlib.sha256).hexdigest()
    authorization = f"CEA algorithm=HmacSHA256, access-key={data.get('access_key')}, signed-date={dt}, signature={signature}"

    header = {
        "Content-type": "application/json;charset=UTF-8",
        "Authorization": authorization,
        "X-Requested-By": data.get('partner_no'),
        "X-EXTENDED-TIMEOUT": "60000"
    }
    return header
