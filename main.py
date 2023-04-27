import requests
from bs4 import BeautifulSoup
import logging



ma_login = '5134011266'
ma_pass = 'UTlw$9M4'

class DataParser:
    def __init__(self, login, password):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 YaBrowser/23.3.2.806 Yowser/2.5 Safari/537.36',
            'Upgrade-Insecure-Requests': '1'})
        self.auth = {
            'main_login2': login,
            'main_password2': password
        }
        self.relogin()

    def relogin(self, func=None, retry=3, pass_try=3, **kwargs):
        self.login_status = False
        try:
            req_login = self.session.post('https://edu.tatar.ru/logon', data=self.auth,
                                          headers=dict(referer='https://edu.tatar.ru/logon'))
            if req_login.url == 'https://edu.tatar.ru/user/anketa':
                self.login_status = True
                if func:
                    if kwargs:
                        return func(**kwargs)
                    else:
                        return func()
            else:
                if pass_try:
                    logging.warning(f'пароль не подошел, try={4-pass_try}')
                    return self.relogin(func=func, retry=retry, pass_try=(pass_try-1), kwargs=kwargs)
                else:
                    return False
        except Exception as ex:
            if retry:
                print(f'[error] retry={retry}')
                return self.relogin(func=func, retry=(retry-1), kwargs=kwargs)
            else:
                logging.warning('Сервер не отвечает')

    def logout(self):
        logoff = self.session.get('https://edu.tatar.ru/logoff')
        self.login_status=False

    def get_day_marks(self, day='', retry=3):
        try:
            if day:
                req_day_marks = self.session.get('https://edu.tatar.ru/user/diary/day', params={'for':str(day)})
            else:
                req_day_marks = self.session.get('https://edu.tatar.ru/user/diary/day')
            if req_day_marks.url == 'https://edu.tatar.ru/message':
                return self.relogin(self.get_day_marks, day=day, retry=retry)
            timetable = []
            soup = BeautifulSoup(req_day_marks.content, 'lxml')
            table = soup.find('div', class_='d-table')
            thead = table.find('thead').find('tr').findAll('td', )
            timetable.append(list(map(lambda x: x.text, thead)))
            tbody = table.find('tbody').findAll('tr', style="text-align: center;")

            for tr in tbody:
                line = []
                content = tr.contents
                times='\n-\n'.join(content[1].text.strip().split('—'))
                line.append(times)
                line.append(content[3].text.strip())
                line.append(content[5].text.strip())
                line.append(content[7].text.strip())
                markslist = []
                marks = content[9].find('table', class_='marks')
                if marks:
                    marks = marks.findAll('tr')
                    for mark in marks:
                        mark = mark.find('td')
                        if mark:
                            work = mark.attrs['title']
                            point = mark.find('div').text
                            markslist.append(work.split('-')[1][1:]+': '+point)
                    line.append(markslist)

                else:
                    line.append([])

                timetable.append(line)
        except Exception as ex:
            if retry:
                print(f'[error] retry={retry}')
                return self.get_day_marks(day=day, retry=(retry - 1))
            else:
                logging.warning('Сервер не отвечает')
        else:
            return timetable

    def schcedule(self, retry=3, period=''):
        try:
            if period:
                req_sch = self.session.get('https://edu.tatar.ru/user/diary/term', params={'term': str(period)})
            else:
                req_sch = self.session.get('https://edu.tatar.ru/user/diary/term')
        except Exception as ex:
            if retry:
                print(f'[error] retry={retry}')
                return self.schcedule(period=period, retry=(retry - 1))
            else:
                logging.warning('Сервер не отвечает')










a = DataParser(ma_login, ma_pass)
b = a.get_day_marks('1682370000')
print(b)
