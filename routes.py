# -*- coding: utf-8 -*-

routes_in = (
    (r'/favicon.ico', r'/7pay_in/static/images/favicon.png'),
    (r'/favicon.png', r'/7pay_in/static/images/favicon.png'),
    (r'/robots.txt', r'/7pay_in/static/robots.txt'),
    (r'/', r'/7pay_in/default/index/'),
    (r'/index/$anything', r'/7pay_in/default/index/$anything'),
    (r'/index', r'/7pay_in/default/index'),
    ## if need in admin
    (r'/admin/$anything', r'/admin/$anything'),
    (r'/$anything', r'/7pay_in/$anything'),
    )

routes_out = [
    (x, y) for (y, x) in routes_in
    ]
