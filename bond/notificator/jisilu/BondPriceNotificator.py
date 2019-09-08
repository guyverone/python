import urllib.request
import time
import json
from win10toast import ToastNotifier
from apscheduler.schedulers.blocking import BlockingScheduler
import datetime
import cgitb
cgitb.enable(format='text')

url = 'https://www.jisilu.cn/data/cbnew/cb_list/?___jsl=LST___t='


percent = 0
openingPriceDict = {}


def send_http(timestamp):
    return get_http_response(url + timestamp)


def get_http_response(url):
    resp = urllib.request.urlopen(url)
    return str(resp.read(), 'utf8')


def get_bond_price():
    now = str(round(time.time() * 1000))
    print("Getting bond price at " + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    resp_data = send_http(now)
    parsed_json_data = json.loads(resp_data)
    rows_data = parsed_json_data.get('rows')
    filtered_data = []
    for row in rows_data:
        cell = row.get('cell')
        issuer_rating_cd = cell.get('issuer_rating_cd')
        rating_cd = cell.get('rating_cd')
        guarantor = cell.get('guarantor')
        bond_id = cell.get('bond_id')
        bond_nm = cell.get('bond_nm')
        price = cell.get('price')
        premium_rt = cell.get('premium_rt')
        ytm_rt_tax = cell.get('ytm_rt_tax')
        volume = cell.get('volume')
        if ("A" in rating_cd) and (float(price) < 100) and (float(premium_rt[0:-1]) <= 30) and (float(ytm_rt_tax[0:-1]) >= 3) and (float(volume) >= 100):
            if bond_nm is not None:
                show_content(bond_nm, issuer_rating_cd, rating_cd, guarantor, price, premium_rt, ytm_rt_tax, volume)
            sleep(0, 0, 8)
            data = {
                'issuer_rating_cd': issuer_rating_cd,
                'rating_cd': rating_cd,
                'guarantor': guarantor,
                'bond_id': bond_id,
                'bond_nm': bond_nm,
                'price' : price,
                'premium_rt': premium_rt,
                'ytm_rt_tax': ytm_rt_tax,
                'volume': volume
            }
            filtered_data.append(data)
    print(filtered_data)


def show_content(key, issuer_rating_cd, rating_cd, guarantor, price, premium_rt, ytm_rt_tax, volume):
    str_content = '担保人评级: ' + str(issuer_rating_cd) +  ' 评级: ' + str(rating_cd) + ' 担保情况: ' + str(guarantor) + ' \n价格: ' + str(price) + ' 溢价率: ' + str(premium_rt) + ' \n到期收益: ' + str(ytm_rt_tax) + ' 成交额: ' + str(volume) + '（万元）'
    print(key + " " + str_content + '\n')
    invoke_windows_notifier(key, str_content)


def invoke_windows_notifier(title, message):
    toaster = ToastNotifier()
    toaster.show_toast(title, message)


def sleep(hour, min, sec):
    time.sleep(hour*3600 + min*60 + sec)


if __name__ == '__main__':
    sched = BlockingScheduler()
    sched.add_job(get_bond_price,'cron', day_of_week='*', hour='*', minute='*', second="0")
    sched.start()
