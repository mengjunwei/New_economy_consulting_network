from . import index_blue
from flask import render_template, current_app, session, jsonify, request, g
from info.models import News, Category
from info import constants, response_code
from info.utils.common import user_login_data


@index_blue.route('/news_list')
def index_news_list():
    '''
    1,接受参数（当前页，每页多少条，新闻分类
    :return: 
    '''
    # http://127.0.0.1:5000/news_list?cid=1&page=1&per_page=10
    cid = request.args.get('cid', '1')
    page = request.args.get('page', '1')
    per_pape = request.args.get('per_pape', '10')

    try:
        cid = int(cid)
        page = int(page)
        per_pape = int(per_pape)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=response_code.RET.PARAMERR, errmsg='参数错误')

    try:
        if cid == 1:
            paginate = News.query.order_by(News.create_time.desc()).paginate(page, per_pape, False)
        else:
            paginate = News.query.filter(News.category_id==cid).order_by(News.create_time.desc()).paginate(page, per_pape, False)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=response_code.RET.DBERR, errmsg='查询新闻数据失败')

    #构造新闻响应数据
    new_list = paginate.items
    total_page = paginate.pages
    current_page = paginate.pages

    news_dict_list = []
    for news in new_list:
        news_dict_list.append(news.to_basic_dict())

    data = {
        'news_dict_list': news_dict_list,
        'total_page': total_page,
        'current_page': current_page
    }
    return jsonify(errno=response_code.RET.OK, errmsg='OK', data=data)


@index_blue.route('/')
@user_login_data
def index():
    '''
    1,查询用户登录状态
    2点击排行数据的显示
    :return: 
    '''
    #1,查询用户登录状态
    user = g.user

    #2点击排行数据的显示
    news_click = None
    try:
        news_click = News.query.order_by(News.clicks.desc()).limit(constants.CLICK_RANK_MAX_NEWS)
    except Exception as e:
        current_app.logger.error(e)

    #查看新闻分类，渲染到模板中
    categorys = []
    try:
        categorys = Category.query.all()
    except Exception as e:
        current_app.logger.error(e)

    context = {
        'user':user.to_dict() if user else None,
        'news_click':news_click,
        'categorys':categorys
    }
    return render_template('news/index.html', context=context)


@index_blue.route('/favicon.ico')
def favicon():
    return current_app.send_static_file('news/favicon.ico')