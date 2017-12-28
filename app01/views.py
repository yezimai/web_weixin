from django.shortcuts import render,HttpResponse
import requests
import time,re,json

# Create your views here.
def ticket(html):
    from bs4 import BeautifulSoup
    ret = {}
    soup = BeautifulSoup(html,'html.parser')
    for tag in soup.find(name='error').find_all():
        ret[tag.name] = tag.text
    return ret


def login(req):
    if req.method == "GET":
        uuid_time = int(time.time() * 1000)
        base_uuid_url = 'https://login.wx.qq.com/jslogin?appid=wx782c26e4c19acffb&redirect_uri=https%3A%2F%2Fwx.qq.com%2Fcgi-bin%2Fmmwebwx-bin%2Fwebwxnewloginpage&fun=new&lang=zh_CN&_={0}'
        uuid_url = base_uuid_url.format(uuid_time)
        r1 = requests.get(uuid_url)
        #print(r1.text) #window.QRLogin.code = 200; window.QRLogin.uuid = "AbURZO0Rhg==";
        result = re.findall('= "(.*)";', r1.text)
        uuid = result[0]
        req.session['UUID_TIME'] = uuid_time
        req.session['UUID'] = uuid
        return render(req,'login.html',{'uuid':uuid})

def check_login(req):
    response = {'code':408,'data':None}
    ctime = int(time.time()*1000)
    base_login_url = 'https://login.wx.qq.com/cgi-bin/mmwebwx-bin/login?loginicon=true&uuid={0}&tip=0&r=-1533908934&_={1}'
    login_url = base_login_url.format(req.session['UUID'],ctime)
    r1 = requests.get(login_url)
    if 'window.code=408' in r1.text:
        # 无人扫码
        response['code'] = 408
    elif 'window.code=201' in r1.text:
        # 扫码，返回头像
        response['code'] = 201
        response['data'] = re.findall("window.userAvatar = '(.*)';", r1.text)[0]
    elif 'window.code=200' in r1.text:
        # 扫码，并确认登录
        req.session['LOGIN_COOKIE'] = r1.cookies.get_dict() #扫码成功后将登陆的cookies保存，获取返回的一个url，在下次去调用
        base_redirect_url = re.findall('redirect_uri="(.*)";',r1.text)[0]
        redirect_url = base_redirect_url + '&fun=new&version=v2'

        # 获取凭证
        r2 = requests.get(redirect_url)
        ticket_dict = ticket(r2.text)
        req.session['TICKED_DICT'] = ticket_dict
        req.session['TICKED_COOKIE'] = r2.cookies.get_dict()


        # 初始化，获取最近联系人信息：工作号
        post_data = {
            "BaseRequest":{
                "DeviceID": "e384757757885382",
                'Sid': ticket_dict['wxsid'],
                'Uin': ticket_dict['wxuin'],
                'Skey': ticket_dict['skey'],
            }
        }

        # 用户初始化，讲最近联系人个人信息放在session中
        init_url = "https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxinit?r=-740036701&pass_ticket={0}".format(ticket_dict['pass_ticket'])
        r3 = requests.post(
            url=init_url,
            json=post_data
        )
        r3.encoding = 'utf-8'
        init_dict = json.loads(r3.text)
        req.session['INIT_DICT'] = init_dict
        response['code'] = 200
    return HttpResponse(json.dumps(response))


def index(req):
    """显示最近联系人"""
    # https://wx.qq.com
    #img_url = "https://wx.qq.com" + req.session['INIT_DICT']['User']['HeadImgUrl']
   # res = requests.get(img_url, headers={'Referer': 'https://wx.qq.com/?&lang=zh_CN'})

    # return render(req,'index.html',{'img': res.content})
    return render(req,'index.html')
def avatar(req):
    prev = req.GET.get('prev') # /cgi-bin/mmwebwx-bin/webwxgeticon?seq=602427528
    username = req.GET.get('username') # @fb736164312cbcdb9abe746d81e24835
    skey = req.GET.get('skey') # @crypt_2ccf8ab9_4414c9f723cbe6e9caca48b7deceff93
    img_url = "https://wx.qq.com{0}&username={1}&skey={2}".format(prev,username,skey)

    cookies= {}
    cookies.update(req.session['LOGIN_COOKIE'])
    cookies.update(req.session['TICKED_COOKIE'])
    print('----',img_url)
    res = requests.get(img_url,cookies=cookies,headers={'Content-Type': 'image/jpeg'})
    return HttpResponse(res.content)

def contact_list(req):
    """
    获取所有联系人
    :param req:
    :return:
    """
    ctime = int(time.time()*1000)
    base_url = "https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxgetcontact?lang=zh_CN&r={0}&seq=0&skey={1}"
    url = base_url.format(ctime,req.session['TICKED_DICT']['skey'])
    cookies = {}
    cookies.update(req.session['LOGIN_COOKIE'])
    cookies.update(req.session['TICKED_COOKIE'])

    r1 = requests.get(url,cookies=cookies)
    r1.encoding = 'utf-8'

    user_list = json.loads(r1.text)

    return render(req, 'contact_list.html',{'user_list':user_list})

def send_msg(req):
    """
    发送消息
    :param req:
    :return:
    """
    current_user = req.session['INIT_DICT']['User']['UserName'] # session初始化，User.UserName
    to = req.POST.get('to') # @dfb23e0da382f51746575a038323834a
    msg = req.POST.get('msg')# asdfasdfasdf

    # session Ticket
    # session Cookie
    ticket_dict = req.session['TICKED_DICT']
    ctime = int(time.time()*1000)

    post_data = {
	    "BaseRequest":{
            "DeviceID": "e384757757885382",
            'Sid': ticket_dict['wxsid'],
            'Uin': ticket_dict['wxuin'],
            'Skey': ticket_dict['skey'],
        },
        "Msg":{
            "ClientMsgId":ctime,
                "LocalID":ctime,
            "FromUserName": current_user,
            "ToUserName":to,
            "Content": msg,
            "Type": 1
        },
        "Scene": 0
    }

    url = "https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxsendmsg?pass_ticket={0}".format(ticket_dict['pass_ticket'])
    # res = requests.post(url=url,json=post_data) # application/json,json.dumps(post_data)
    # res = requests.post(url=url,data=json.dumps(post_data),headers={'Content-Type': "application/json"}) # application/json,json.dumps(post_data)

    res = requests.post(url=url,data=json.dumps(post_data,ensure_ascii=False).encode('utf-8'),headers={'Content-Type': "application/json"}) # application/json,json.dumps(post_data)
    print(res.text)
    return HttpResponse('...')