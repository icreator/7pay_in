# coding: utf8
# попробовать что-либо вида
def index():
    session.forget(response)
    v = {}
    #for r in db(db.news).select(orderby=~db.news.on_create, limitby=(0, 100)):
    #    v[ r.head] = r.body
    #rec
    #response.vars = { 'r': v}
    #print response._vars
    rs=db(db.news).select(orderby=~db.news.on_create, limitby=(0, 100))
    
    stats = []
    sum_ = db.currs_stats.count_.sum()
    recs = db(
           db.currs.id == db.currs_stats.curr_id).select(sum_, db.currs.ALL, groupby=db.currs_stats.curr_id, orderby=~sum_)
    for r in recs:
        stats.append('%s: %s' % (r.currs.name, r._extra['SUM(currs_stats.count_)']))
    
    return dict(rs=rs, stats=stats, message="")
