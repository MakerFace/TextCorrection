# -*- coding:utf-8 -*-
from datetime import datetime
from wsgiref.handlers import format_date_time
from time import mktime
import hashlib
import base64
import hmac
from urllib.parse import urlencode
import json
import requests
from flask import Flask
app = Flask(__name__)


class AssembleHeaderException(Exception):
    def __init__(self, msg):
        self.message = msg


class Url:
    def __init__(this, host, path, schema):
        this.host = host
        this.path = path
        this.schema = schema
        pass


class WebsocketDemo:
    def __init__(self,APPId,APISecret,APIKey,Text):
        self.appid = APPId
        self.apisecret = APISecret
        self.apikey = APIKey
        self.text = Text
        self.url = '''https://api.xf-yun.com/v1/private/s9a87e3ec'''

    # calculate sha256 and encode to base64
    def sha256base64(self,data):
        sha256 = hashlib.sha256()
        sha256.update(data)
        digest = base64.b64encode(sha256.digest()).decode(encoding='utf-8')
        return digest


    def parse_url(self,requset_url):
        stidx = requset_url.index("://")
        host = requset_url[stidx + 3:]
        schema = requset_url[:stidx + 3]
        edidx = host.index("/")
        if edidx <= 0:
            raise AssembleHeaderException("invalid request url:" + requset_url)
        path = host[edidx:]
        host = host[:edidx]
        u = Url(host, path, schema)
        return u


    # build websocket auth request url
    def assemble_ws_auth_url(self,requset_url, method="POST", api_key="", api_secret=""):
        u = self.parse_url(requset_url)
        host = u.host
        path = u.path
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))
        #print(date)
        # date = "Thu, 12 Dec 2019 01:57:27 GMT"
        signature_origin = "host: {}\ndate: {}\n{} {} HTTP/1.1".format(host, date, method, path)
        #print(signature_origin)
        signature_sha = hmac.new(api_secret.encode('utf-8'), signature_origin.encode('utf-8'),
                                 digestmod=hashlib.sha256).digest()
        signature_sha = base64.b64encode(signature_sha).decode(encoding='utf-8')
        authorization_origin = "api_key=\"%s\", algorithm=\"%s\", headers=\"%s\", signature=\"%s\"" % (
            api_key, "hmac-sha256", "host date request-line", signature_sha)
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')
        #print(authorization_origin)
        values = {
            "host": host,
            "date": date,
            "authorization": authorization
        }

        return requset_url + "?" + urlencode(values)


    def get_body(self):
        body =  {
            "header": {
                "app_id": self.appid,
                "status": 3,
                #"uid":"your_uid"
            },
            "parameter": {
                "s9a87e3ec": {
                    #"res_id":"your_res_id",
                    "result": {
                        "encoding": "utf8",
                        "compress": "raw",
                        "format": "json"
                    }
                }
            },
            "payload": {
                "input": {
                    "encoding": "utf8",
                    "compress": "raw",
                    "format": "plain",
                    "status": 3,
                    "text": base64.b64encode(self.text.encode("utf-8")).decode('utf-8')
                }
            }
        }
        return body

    def get_result(self):
        request_url = self.assemble_ws_auth_url(self.url, "POST", self.apikey, self.apisecret)
        headers = {'content-type': "application/json", 'host':'api.xf-yun.com', 'app_id':self.appid}
        body = self.get_body()
        response = requests.post(request_url, data = json.dumps(body), headers = headers)
        # print('onMessage：\n' + response.content.decode())
        tempResult = json.loads(response.content.decode())
        # print('text字段解析：\n' + base64.b64decode(tempResult['payload']['result']['text']).decode())
        return base64.b64decode(tempResult['payload']['result']['text']).decode()

from flask import request as freq
@app.route('/submit', methods=["POST", "GET"])
def submit():
    #控制台获取
    APPId = "97e7fa7b"
    APISecret = "ODc5M2RmMjZjZDI3MjE0NWQ5MTdjYjcx"
    APIKey = "20df0c359a2099340e7842cdbadc2fe2"

    #需纠错文本
    Text = freq.args.get("Text")
    print(Text)
    demo = WebsocketDemo(APPId,APISecret,APIKey,Text)
    result = demo.get_result()
    result = json.loads(result)
    keyword = ['word', 'char']
    # print(result)
    # print(result['word'])
    modify = []
    for key in keyword:
        for word in result[key]:
            begin = word[0]
            end = begin+10
            begin -= 10
            modify.append('原文：{}\n'.format(Text[max(0,begin):min(len(Text), end)]))
            change = Text[max(0,begin):word[0]] + word[2] + Text[word[0]+len(word[2]):end]
            modify.append('改正：{}\n'.format(change))
            # print('原文：{}'.format(Text[begin:end]))
            # print('改正：{}'.format(Text[begin:end].replace(word[1], word[2])))
    if len(modify) == 0:
        modify.append('无需修改')
    modify = json.dumps(modify)
    # print(modify)
    return modify 


@app.route('/')
def main():
    return """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>MakerFace论文错别字检查</title>
</head>
<script src="//ajax.googleapis.com/ajax/libs/jquery/1.9.1/jquery.min.js"></script>
<script type=text/javascript>
        $(function() {
          $('a#test').bind('click', function() {
            $.getJSON('/submit',
                {"Text":$("textarea#textfield3").val()},
                function(data) {
                    let x = '';
                    for (i in data){
                        x += data[i]
                    }
                    $("textarea#modify").val(x)
            });
            return false;
          });
        });
</script>
<body>
    <form id="form2" action="mailto:fyy0528@sina.com" method="post" enctype="text/plain" >
        <table width="50%" border="1" bordercolorlight="#000000" bordercolordark="#FFFFFF" bgcolor="#FFFFFF" cellpadding="4" align="left">
                <td colspan="2"> 
                    <div align="center">正文<br> 
                        <textarea id="textfield3" cols="100" rows="50"></textarea>
                    </div>
                </td>
            </tr>
            <tr> 
                <td> 
                    <div align="right">
                        <a href=# id=test><button class='btn btn-default'>提 交</button></a>
                    </div> 
                </td>
                <td> 
                    <input type="reset" name="Submit2" value="重 写"> 
                </td>
            </tr>
        </table>
    </form>
    <div>
        <div align="center">修改<br>
            <textarea id="modify" cols="50" rows="30"></textarea>
        </div>
    </div>
</body>
</html>"""
