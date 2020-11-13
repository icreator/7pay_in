
## Bitcoin & Fiat payment service

see last version on GitLab https://gitlab.com/d.ermolaev/7pay_in

> DEMO
http://datachains.world/7pay_in


#### python +  [web2py framework](http://web2py.com/books/default/chapter/29/14/other-recipes?search=eclipse#Developing-with-IDEs--WingIDE--Rad2Py--Eclipse-and-PyCharm)

https://bitcointalk.org/index.php?topic=1927911

### Included SERVICES:
+ EXCHANGE bitcoin and crypto currencies to fiat currencies
+ payment in bitcoin and crypto currencies for mobile phone, games etc.
+ buy bitcoin and crypto currencies
+ simple shop merchant
+ API
+ auto gathering rating from bitcoin exchanges (btc-e.com poloniex.com etc.)
+ etc.

### List of cryptocurrencies
+ bitcoin
+ litecoin
+ dash
+ dogecoin
+ peercoin
+ novacoin
+ sibcoin
+ etc.

### List of FIAT money
+ Yandex.Money

### INSTALL HELP (RUS)
https://docs.google.com/document/d/1zmR4CA_e-Z0k3Z9IDlnBc87JthoEtmY2vslIvhqphRE/edit?usp=sharing

### DATABASE init
Use initial SQL statement:  
**7pay-Dump20171123.zip**

### For configure routes in web2py use:
+ Edit **routes.py** in application folder (/web2py/applications/7pay_in)
+ Edit **routes_main.py** and copy to web2py folder (/web2py)

### For switch ON DEVELOP mode
Edit **/privare/appconfig.ini**:  
[app]  
develop = 1  
It will use developer database and local (127.0.0.1:8000) URLs

### For switch OFF DEVELOP mode
Edit **/privare/appconfig.ini**:  
[app]  
develop =  

### For APACHE
see /_apache folder

### For MS IIS
see [web2py on IIS](http://web2py.com/books/default/chapter/29/13/deployment-recipes#IIS)


### AUTHOR & HELP
Skype i-creator
Mail icreator@mail.ru

> Written with [StackEdit](https://stackedit.io/).
