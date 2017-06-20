# coding: utf8
# попробовать что-либо вида
response.title=T("Вопросы о сервисе")
response.logo2 = IMG(_src=URL('static','images/7P-35.png'), _width=156)

def index():
    session.forget(response)
    return dict(message="hello from why.py")
