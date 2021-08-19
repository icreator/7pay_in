#!/usr/bin/env python
# coding: utf8

import re
from gluon import current

import urllib2
from bs4 import BeautifulSoup, SoupStrainer


def form_YD(html_in):
    '''
<div class="section shop">
<table cellspacing="0" cellpadding="0" border="0" class="l-page l-page_layout_50-30-20"><tbody><tr>
<td class="l-page__left">
<form xmlns:ym="http://money.yandex.ru/xml-page" method="post" action="/shop.xml?scid=4214&amp;from=isrch" name="mform" class=" b-form xforms-extended-validation" onload="change_rnd()">
<input type="hidden" name="rnd" value="92154736"><input type="hidden" name="scid" value="4214"><input type="hidden" name="shn" value="UNITLINE"><input type="hidden" name="targetcurrency" value="643">
<label for="FormComment">Название</label>
<><input class="b-form-input__input" id="FormComment" type="text" name="FormComment" value="UNITLINE"></span></span></div></td>
</tr>
    '''
    #<div class="section shop">
    form = None
    res = html_in.find("div", {"class": "section shop"}) #.a.contents[0]
    #input type="hidden" name="scid" value="4214"><input type="hidden" name="shn" value="UNITLINE">
    if res:
        form = res.find("form", {"name": "mform"})
    else:
        form = html_in.find("form", {"name": "mform"})
    if not form: return None, None, None
    #form = BeautifulSoup( form )
    scid = form.find('input', {'name':'scid'}).get('value')
    name = form.find('input', {'name':'shn'}).get('value')
    # все наши служебные поля скроем и удалим из формы
    for key in ['FormComment', 'netSum', 'sum']: # + acc_names :
        inpt = form.find('input', {'name': key } )
        if inpt: inpt['type'] = 'hidden'
        lbl = form.find('label', {'for': key } )
        if lbl: lbl['class'] = 'hidden'
    '''
    <tr class="">
<td class="xf_label"><div class="xf_input_label"><label for="sum">Сумма</label></div></td>
<td class="xf_field"><div class="xf_input">
<span class="b-form-input b-form-input_theme_grey b-form-input_size_ml sum i-bem" onclick="return {'b-form-input':{name:'b-form-input'}}"><span class="b-form-input__box"><input class="b-form-input__input" id="sum" name="" type="hidden" value=""/></span></span> <span class="sum-text">руб.</span>
</div></td>
</tr>
<tr class="xf_submit_row">
<td class="xf_label"></td>
<td class="xf_field"><div class="xf_submit"><span class="b-form-button b-form-button_theme_grey-l b-form-button_size_l tst-payment__submit-pay i-bem" onclick="return {'b-form-button':{name:'b-form-button'}}"><i class="b-form-button__left"></i><span class="b-form-button__content"><span class="b-form-button__text">Заплатить</span></span><input class="b-form-button__input" hidefocus="true" name="" type="hidden" value=""/></span></div></td>
</tr>
    '''
    tag = form.find('div', {'class': 'xf_submit'})
    if tag: tag['class'] = 'hidden'
    tag = form.find('span', {'class': 'sum'})
    if tag: tag['class'] = 'hidden'

    
    #inpts = []
    for inpt in form.find_all('input'):
        #inpt.empty-element()
        #print (inpt)
        #print (inpt.get('type'), u'type' in inpt and inpt[u'type'])
        t = inpt.get('type')
        if t:
            #print (t)
            if t == 'hidden':
                #inpts.append(inpt)
                #print ('expract: ',inpt['name'],'=',inpt['value'])
                #inpt.extract() нельзя потому что инпуты вложенные после разбора СУПом
                inpt['name'] = ''
                inpt['value'] = ''
            elif t == 'submit':
                inpt['value'] = '' #current.T(u'Подключить')
                inpt['value'] = '' #inpt['value'].decode('utf8')
                inpt['name'] = ''
                inpt['type'] = 'hidden'
                #inpt['value'] = 'GO'
                
            
    #<span class="b-button__inner">Заплатить</span>
    ss = form.find('span', {'class': 'b-button__inner' } )
    if ss: ss['class'] = 'hidden'

    return scid, name, form.contents

def info_YD(html_in):
    img=None
    '''
td class="l-page__center"><div class="shop-info-container">
<div class="shop-info"><div class="shop-info_info">
<img border="0" alt="Условия использования" title="Условия использования" align="" valign="" src="/i/shop/unitline.jpg" width="88" height="31">
<div class="rules"><a href="/shop.xml?show=info&amp;scid=4214" target="_blank">
Условия использования
</a></div>
</div></div>
    '''
    res = html_in.find("div", {"class": "shop-info_info"})
    if res:
        img = res.find('img')
        #src = img.get('src')
        if img: return img
    
    '''
         <div class="section shop-info-container">
              <div class="logo-here logo-here"><img border="0" align="" valign="" src="/i/shop/allods.gif" class="logo-here"></div>
    '''
    res = html_in.find("div", {"class": "shop-info-container"})
    if res:
        img = res.find('img')
        #src = img.get('src')
        if img: return img

    return img

close_inp = re.compile('<input (\w.)><')

def load_YD(url_yd, my_url):
    # https://money.yandex.ru/shop.xml?scid=4214
    try:
        f = urllib2.urlopen(url_yd)
    except Exception as e:
        print ('ERROR load ', url_yd, e)
        return None, url_yd, e, None

    #print ('BS4')
    html_in = f.read()

    #for 
    #html_in = regular_digs.sub("","%s" % acc)

    # Tag.isSelfClosing -> Tag.is_empty_element
    #print (BeautifulSoup.empty_element_tags)
    #BeautifulSoup.empty_element_tags = ['input', 'INPUT', 'br']
    openHTML = BeautifulSoup(html_in)
    #SoupStrainer - этот кодировку тогда не понимает
    scid, name, form_pars = form_YD(openHTML)
    #form['action']=my_url
    img = info_YD(openHTML)
    img = img and img['src']
    return scid, name, img, form_pars
