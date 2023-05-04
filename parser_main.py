import requests
from bs4 import BeautifulSoup
import logging

# ma_login = '5185004386'
# ma_pass = 'aC!pYG7W'
# ma_login = '5134011266'
# ma_pass = 'UTlw$9M4'
# ma_login = '5153122086'
# ma_pass = '57FC'


class DataParser:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 YaBrowser/23.3.2.806 Yowser/2.5 Safari/537.36',
            'Upgrade-Insecure-Requests': '1'})

    def login(self, login, password):
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
                    logging.warning(f'пароль не подошел, try={4 - pass_try}')
                    return self.relogin(func=func, retry=retry, pass_try=(pass_try - 1), kwargs=kwargs)
                else:
                    return False
        except Exception as ex:
            if retry:
                print(f'[error] retry={retry}')
                return self.relogin(func=func, retry=(retry - 1), kwargs=kwargs)
            else:
                logging.warning('Сервер не отвечает')

    def logout(self):
        logoff = self.session.get('https://edu.tatar.ru/logoff')
        self.login_status = False

    def get_day_marks(self, day='', retry=3):
        try:
            if day:
                req_day_marks = self.session.get('https://edu.tatar.ru/user/diary/day', params={'for': str(day)})
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
                times = '\n-\n'.join(content[1].text.strip().split('—'))
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
                            markslist.append(work.split('-')[1][1:] + ': ' + point)
                    line.append('\n'.join(markslist))

                else:
                    line.append('')

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
            if req_sch.url == 'https://edu.tatar.ru/message':
                return self.relogin(self.schcedule, period=period, retry=retry)
            table = []
            soup = BeautifulSoup(req_sch.content, 'lxml')
            periods_tags = soup.find('form').find('select').findAll('option')
            periods = dict()
            for tag in periods_tags:
                periods[' '.join(tag.text.strip().split())] = tag.attrs['value']
            table_tag = soup.find('table')
            thead = table_tag.find('thead').find('tr').findAll('td')
            head = list(map(lambda x: x.text, thead))
            extra = False
            if head[-2]== 'Экзамен' or head[-2] == 'График':
                a = head.pop(-2)
                extra = True
            table.append(head)
            tbody = table_tag.find('tbody').findAll('tr')
            for tr_tag in tbody:
                line = []
                marks = []
                td_tags = tr_tag.findAll('td')
                if extra:
                    a = td_tags.pop(-2)
                if period == 'year':
                    line = [x.text for x in td_tags]
                    table.append(line)
                else:
                    line = [x.text.strip() for x in td_tags]
                    marks = []
                    for x in line[1:-2]:
                        if x:
                            marks.append(x)
                    line = [line[0]]+[' '.join(marks)]+line[-2:]
                    table.append(line)

        except Exception as ex:
            if retry:
                print(f'[error] retry={retry}')
                return self.schcedule(period=period, retry=(retry - 1))
            else:
                logging.warning('Сервер не отвечает')
        else:
            return periods, table

    def get_name(self, retry=3):
        try:
            req = self.session.get('https://edu.tatar.ru/user/anketa')
            if req.url == 'https://edu.tatar.ru/message':
                return self.relogin(self.get_name, retry=retry)
            soup = BeautifulSoup(req.content, 'lxml')
            table = soup.find('table', class_='tableEx').find('tr').find('strong')
            name = ' '.join(table.text.split()[:2])
        except Exception as ex:
            if retry:
                print(f'[error] retry={retry}')
                return self.get_name(retry=(retry - 1))
            else:
                logging.warning('Сервер не отвечает')
        else:
            return name

    def dump_cookies(self):
        cookies = []
        for c in self.session.cookies:
            cookies.append({
                "name": c.name,
                "value": c.value,
                "domain": c.domain,
                "path": c.path,
                "expires": c.expires
            })
        return cookies

    def load_cookies(self, cookies):
        for c in cookies:
            self.session.cookies.set(**c)


# a = DataParser()
# a.login(ma_login, ma_pass)
# ck = a.dump_cookies()
# print(ck)
# b = DataParser()
# b.load_cookies(ck)
# print(b.schcedule())
