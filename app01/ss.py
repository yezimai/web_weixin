# -*- coding:utf-8 -*-
#--author：yewei-Administrator on 2017/12/16

import requests
# url='https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxnewloginpage?ticket=Ae9-BgYt6lF_STC5-E3dnebv@qrticket_0&uuid=AdDbqHsOzw==&lang=zh_CN&scan=1513407299&fun=new&version=v2&lang=zh_CN'
# r1=requests.get(url)

html = '''
<error><ret>0</ret><message></message><skey>@crypt_3552ef50_cdb6335320f68afe42478977c9fa211b</skey><wxsid>QT93Hiiidk/iK9/j</wxsid><wxuin>315911535</wxuin><pass_ticket>F2XCFzE2nTHCSjAQQEhqLf0JQAcFJR8Go2r%2FhTz0JhloRcZTD74HmVMpPWsa5LLp</pass_ticket><isgrayscale>1</isgrayscale></error>
'''
from bs4 import BeautifulSoup
# print(r1.text)
ret={}
#soup = BeautifulSoup(r1.text,'html.parser')
soup = BeautifulSoup(html,'html.parser')
for tag in soup.find(name='error').find_all():
    ret[tag.name] = tag.text
print(soup.find(name='error').find_all())
print(ret)