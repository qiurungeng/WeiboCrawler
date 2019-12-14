import sqlite3
import time
import base64
import rsa
import binascii
import requests
import re
import random
from Weibo.DbUtil import FollowedListTable

try:
    from PIL import Image
except:
    pass
try:
    from urllib.parse import quote_plus
except:
    from urllib import quote_plus, request


class WeiboUtil():

    def __init__(self):
        requests.adapters.DEFAULT_RETRIES = 5
        self.session=requests.session()
        # self.agent = 'Mozilla/5.0 (Windows NT 6.3; WOW64; rv:41.0) Gecko/20100101 Firefox/41.0'
        self.agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.79 Safari/537.36'
        self.headers = {
            'User-Agent': self.agent
        }
        self.uid=0
        self.db=FollowedListTable()

    def create_db(self):
        con = sqlite3.connect('weibo.db')
        cur = con.cursor()
        cur.execute(
            'create table if not exists followlist(id int(10) primary key,followed boolean)')


    def get_su(self,username):
        """
        对 email 地址和手机号码 先 javascript 中 encodeURIComponent
        对应 Python 3 中的是 urllib.parse.quote_plus
        然后在 base64 加密后decode
        """
        username_quote = quote_plus(username)
        username_base64 = base64.b64encode(username_quote.encode("utf-8"))
        return username_base64.decode("utf-8")


    def get_server_data(self,su):
        """
        预登陆获得 servertime, nonce, pubkey, rsakv
        """
        pre_url = "http://login.sina.com.cn/sso/prelogin.php?entry=weibo&callback=sinaSSOController.preloginCallBack&su="
        pre_url = pre_url + su + "&rsakt=mod&checkpin=1&client=ssologin.js(v1.4.18)&_="
        pre_url = pre_url + str(int(time.time() * 1000))
        pre_data_res = self.session.get(pre_url, headers=self.headers)
        sever_data = eval(pre_data_res.content.decode("utf-8").replace("sinaSSOController.preloginCallBack", ''))

        return sever_data


    def get_password(self,password, servertime, nonce, pubkey):
        rsaPublickey = int(pubkey, 16)
        key = rsa.PublicKey(rsaPublickey, 65537)  # 创建公钥
        message = str(servertime) + '\t' + str(nonce) + '\n' + str(password)  # 拼接明文js加密文件中得到
        message = message.encode("utf-8")
        passwd = rsa.encrypt(message, key)  # 加密
        passwd = binascii.b2a_hex(passwd)  # 将加密信息转换为16进制。
        return passwd

    def get_cha(self,pcid):
        """
        获取验证码
        :param pcid:
        :return:
        """
        cha_url = "http://login.sina.com.cn/cgi/pin.php?r="
        cha_url = cha_url + str(int(random.random() * 100000000)) + "&s=0&p="
        cha_url = cha_url + pcid
        cha_page = self.session.get(cha_url, headers=self.headers)
        with open("cha.jpg", 'wb') as f:
            f.write(cha_page.content)
            f.close()
        try:
            im = Image.open("cha.jpg")
            im.show()
            im.close()
        except:
            print("请到当前目录下，找到验证码后输入")

    def openurl(self, url):
        """
        返回网页数据
        :param url:
        :return:
        """
        data = self.session.get(url=url,headers=self.headers,timeout=3).content.decode('utf-8')
        return data

    def get_follow_list(self,uid):
        """
        打开关注页面爬取关注者的uid，从第一页开始爬取到最后一页
        :param uid:
        :return:
        """
        print('打开关注列表')
        follow_url = 'https://weibo.com/{}/follow'.format(uid)
        next_page_pat = 'next.S_txt1.S_line1.".href=."(.+?.)".+?.下一页'
        uid_list=[]
        page = self.openurl(follow_url)
        while True:
            follow_pat = 'class=."W_face_radius.".+?."id=(.+?.)."'
            follow_list = re.compile(follow_pat).findall(page)
            print('爬取当前页的用户id')
            for item in follow_list:
                uid_list.append(item)
            next_page = re.compile(next_page_pat).findall(page)
            if len(next_page)==0:
                print('搜集关注用户id完毕,目前搜集了：' + str(len(uid_list))+'人')
                break
            else:
                next_page_url = 'https://weibo.com' + next_page[0].replace('\\', '')
                # print(next_page_url)
                page = self.session.get(next_page_url).text
                time.sleep(random.randint(1, 5))
                continue
        return uid_list

    # 关注用户
    def follow(self,uid_list):
        """
        先获取登录用户关注列表，然后遍历uid_list，若其中uid不在登录用户已关注列表中，则发送POST请求为登录用户关注该uid用户
        :param uid_list:
        :return:
        """
        my_follow_list=self.get_follow_list(self.uid)
        num = 0
        for uid in uid_list:
            if my_follow_list.__contains__(uid):
                print('我的关注列表中已存在用户:'+uid+',跳过此用户')
                continue
            # 仿照关注页面的POST请求头的数据
            headers = {'Host': 'weibo.com',
                       'Connection': 'keep-alive',
                       'Content-Length': '307',
                       'Origin': 'https://weibo.com',
                       'X-Requested-With': 'XMLHttpRequest',
                       'User-Agent':'Mozilla/5.0 (Windows NT 6.3; WOW64; rv:41.0) Gecko/20100101 Firefox/41.0',
                       'Content-Type': 'application/x-www-form-urlencoded',
                       'Accept': '*/*',
                       'Referer': "https://weibo.com/u/"+str(uid)+"?is_hot=1",
                       'Accept-Encoding': 'gzip, deflate, br',
                       'Accept-Language': 'zh-CN,zh;q=0.9',
                       }
            time.sleep(random.randint(1, 5))
            try:
                data = 'uid={}&objectid=&f=1&extra=&refer_sort=fanslist&refer_flag=1005050008_&location=hisfans_v6&oid=1875333245&wforce=1&nogroup=1&refer_from=relate_fans&special_focus=1&template=8&isrecommend=1&is_special=0&redirect_url=%252Fp%252F1005056980219805%252Fmyfollow%253Fgid%253D4334480753977676%2523place&_t=0'.format(
                    uid)
                r = self.session.post(
                    'https://weibo.com/aj/f/followed?ajwvr=6&__rnd={}'.format(int(time.time() * 1000)),
                    headers=headers,
                    data=data,
                    cookies=self.session.cookies)
                if '"code":"100000"' not in r.text:
                    print(uid, '关注失败，关注过于频繁')
                    print('共关注{}个'.format(num))
                    return
                else:
                    print('已关注', uid, r)
                    self.db.updateFollow(uid)
                    num += 1
            except Exception as e:
                print(e)
        print('批量关注完毕，共关注{}人'.format(num))


    def login(self, username, password):
        """
        登录
        :param username:
        :param password:
        :return:
        """
        print('正在登录，登录用户名为:'+username)
        # su 是加密后的用户名
        su = self.get_su(username)
        sever_data = self.get_server_data(su)
        servertime = sever_data["servertime"]
        nonce = sever_data['nonce']
        rsakv = sever_data["rsakv"]
        pubkey = sever_data["pubkey"]
        showpin = sever_data["showpin"]
        password_secret = self.get_password(password, servertime, nonce, pubkey)

        postdata = {
            'entry': 'weibo',
            'gateway': '1',
            'from': '',
            'savestate': '7',
            'useticket': '1',
            'pagerefer': "http://login.sina.com.cn/sso/logout.php?entry=miniblog&r=http%3A%2F%2Fweibo.com%2Flogout.php%3Fbackurl",
            'vsnf': '1',
            'su': su,
            'service': 'miniblog',
            'servertime': servertime,
            'nonce': nonce,
            'pwencode': 'rsa2',
            'rsakv': rsakv,
            'sp': password_secret,
            'sr': '1366*768',
            'encoding': 'UTF-8',
            'prelt': '115',
            'url': 'http://weibo.com/ajaxlogin.php?framelogin=1&callback=parent.sinaSSOController.feedBackUrlCallBack',
            'returntype': 'META'
        }
        login_url = 'http://login.sina.com.cn/sso/login.php?client=ssologin.js(v1.4.18)'
        if showpin == 0:
            login_page = self.session.post(login_url, data=postdata, headers=self.headers)
        else:
            pcid = sever_data["pcid"]
            self.get_cha(pcid)
            postdata['door'] = input(u"请输入验证码")
            login_page = self.session.post(login_url, data=postdata, headers=self.headers)
        login_loop = (login_page.content.decode("GBK"))
        # print(login_loop)
        pa = r'location\.replace\([\'"](.*?)[\'"]\)'
        loop_url = re.findall(pa, login_loop)[0]
        # print(loop_url)
        # 此出还可以加上一个是否登录成功的判断，下次改进的时候写上
        login_index = self.session.get(loop_url, headers=self.headers)
        uuid = login_index.text
        uuid_pa = r'"uniqueid":"(.*?)"'
        uuid_res = re.findall(uuid_pa, uuid, re.S)[0]   #   新浪微博用户unique id
        self.uid=uuid_res
        # 返回已登录的uid
        return uuid_res

if __name__ == '__main__':
    username = '你的账号'  # 微博账号
    password = '你的密码' # 微博密码
    weibo_old = WeiboUtil()
    id_old = weibo_old.login(username,password)
    print('账号uid:'+id_old+'已登录')
    weibo_old.get_follow_list(id_old)

    # # 将关注列表保存到数据库
    # weibo_old.db.addFollowFromList(uid_list)

    # weibo_new=WeiboUtil()
    # id_new=weibo_new.login('00601123581465','asdasdasd')
    # print('账号:' + id_new + '已登录')
    # follow_list=weibo_new.db.getUnfollowList()
    # weibo_new.follow(follow_list)
