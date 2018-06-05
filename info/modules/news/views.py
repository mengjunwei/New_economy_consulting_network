from . import news_blue
from info.utils.common import user_login_data
from flask import render_template, g, current_app, jsonify, request, abort
from info.models import News, Comment, CommentLike
from info import constants, response_code, db


@news_blue.route('/news_commentlike', methods=['POST'])
@user_login_data
def news_commentlike():
    '''
    1.判断用户是否登录，只有用户登录才能进行评论
    2.接受参数
    3.校验参数
    4.根据评论ID查询数据库，判断评论是否存在
    5查询是否该用户是否已经对该评论点赞
    6点赞和取消点赞
    7将结果同步到数据
    :return: 返回结果
    '''

    #1.判断用户是否登录，只有用户登录才能进行评论
    user = g.user
    if not user:
        return jsonify(errno=response_code.RET.SESSIONERR, errmsg='用户未登录')

    #2.接受参数
    comment_id = request.json.get('comment_id')
    action = request.json.get('action')

    #3.校验参数
    if not all ([comment_id, action]):
        return jsonify(errno=response_code.RET.PARAMERR, errmsg='缺少参数')
    try:
        comment_id = int(comment_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=response_code.RET.PARAMERR, errmsg='参数错误')
    if action not in ['add', 'remove']:
        return jsonify(errno=response_code.RET.PARAMERR, errmsg='参数错误')

    #4.根据评论ID查询数据库，判断评论是否存在
    try:
        comment = Comment.query.get(comment_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=response_code.RET.DBERR, errmsg='查询点赞评论失败')
    if not comment:
        return jsonify(errno=response_code.RET.NODATA, errmsg='评论不存在')

    #5查询是否该用户是否已经对该评论点赞
    try:
        commentlike = CommentLike.query.filter(CommentLike.user_id==user.id, CommentLike.comment_id==comment_id).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=response_code.RET.DBERR, errmsg='查询点赞失败')

    #6点赞和取消点赞
    if action == 'add':
        if not commentlike:
            comment_like = CommentLike()
            comment_like.user_id = user.id
            comment_like.comment_id = comment_id
            comment.like_count += 1
            db.session.add(comment_like)

    else:
        if commentlike:
            comment.like_count -= 1
            db.session.delete(commentlike)

    #7将结果同步到数据库
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=response_code.RET.DBERR, errmsg='更新点赞失败')

    #8返回结果
    return jsonify(errno=response_code.RET.OK, errmsg='操作成功')


@news_blue.route('/news_comment', methods=['POST'])
@user_login_data
def news_comment():
    '''
    1.判断用户是否登录，只有登录用户才能进行评论
    2.接受参数(news_id,content,parent_id)
    3.参数校验
    4查看新闻是否存在
    5.若存在parent_id,查询该条评论是否存在
    6.新建模型类对象
    7.同步到数据库
    :return: 返回结果响应
    '''

    #1.判断用户是否登录，只有登录用户才能进行评论
    user = g.user
    if not user:
        return jsonify(errno=response_code.RET.SESSIONERR, errmsg='用户未登录')

    #2.接受参数(news_id,content,parent_id)
    news_id = request.json.get('news_id')
    comment = request.json.get('comment')
    parent_id = request.json.get('parent_id')

    #3.参数校验
    if not all([news_id, comment]):
        return jsonify(errno=response_code.RET.PARAMERR, errmsg='缺少参数')
    try:
        news_id = int(news_id)
        if parent_id:
            parent_id = int(parent_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=response_code.RET.PARAMERR, errmsg='参数错误')

    #4查看新闻是否存在
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=response_code.RET.DBERR, errmsg='查询新闻失败')
    if not news:
        return jsonify(errno=response_code.RET.NODATA, errmsg='新闻不存在')

    #5.若存在parent_id,查询该条评论是否存在
    try:
        parent_comment = Comment.query.filter(Comment.parent_id==parent_id, Comment.news_id==news_id, Comment.user_id==user.id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=response_code.RET.DBERR, errmsg='查询评论失败')
    if not parent_comment:
        return jsonify(errno=response_code.RET.NODATA, errmsg='评论不存在')

    #6.新建模型类对象
    comment_model = Comment()
    comment_model.user_id = user.id
    comment_model.news_id = news_id
    comment_model.content = comment
    if parent_comment:
        comment_model.parent_id = parent_id

    #7.同步到数据库
    try:
        db.session.add(comment_model)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=response_code.RET.DBERR, errmsg='添加评论失败')

    #8返回响应
    return jsonify(errno=response_code.RET.OK, errmsg='评论成功', data=comment_model.to_dict())


@news_blue.route('/news_collect', methods=['POST'])
@user_login_data
def news_collect():
    '''
    1，查看用户是否登录
    2,接受参数，判断参数是否合法
    3，根据news_id 查找news对象
    4,查询该用户收藏的新闻列表
    5收藏的增加与取消
    6同步到数据库中
    7返回响应
    :return: 
    '''

    # 1，查看用户是否登录
    user = g.user
    if not user:
        return jsonify(errno=response_code.RET.SESSIONERR, errmsg='用户未登录')

    #2,接受参数，判断参数是否合法
    json_dict = request.json
    news_id = json_dict.get('news_id')
    action = json_dict.get('action')
    if not all([news_id, action]):
        return jsonify(errno=response_code.RET.PARAMERR, errmsg='参数错误')
    if action not in ['cancel_collect', 'collect']:
        return jsonify(errno=response_code.RET.PARAMERR, errmsg='参数错误')

    #3，根据news_id 查找news对象
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=response_code.RET.DBERR, errmsg='查询新闻对象错误')
    if not news:
        return jsonify(errno=response_code.RET.NODATA, errmsg='无此新闻')

    #4,查询该用户收藏的新闻列表
    try:
        user_news_list = user.collection_news
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=response_code.RET.DBERR, errmsg='查询收藏的新闻列表失败')

    #5收藏的增加与取消
    if action == 'collect':
        if news not in user_news_list:
            user_news_list.append(news)
    else:
        if news in user_news_list:
            user_news_list.remove(news)

    #6同步到数据库中
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=response_code.RET.DBERR, errmsg='同步收藏失败')

    #7返回响应
    return jsonify(errno=response_code.RET.OK, errmsg='操作成功')


@news_blue.route('/news_detal/<int:news_id>')
@user_login_data
def news_detal(news_id):
    '''
    1，查看用户是否登录
    2，点击排行的显示
    3，根据news_id查询新闻
    4，新闻点击量加1
    :param news_id: 
    :return: 
    '''

    #1，查看用户是否登录
    user = g.user

    #2，点击排行的显示
    news_clicks = []
    try:
        news_clicks = News.query.order_by(News.clicks.desc()).limit(constants.CLICK_RANK_MAX_NEWS)
    except Exception as e:
        current_app.logger.error(e)


    #3，根据news_id查询新闻
    news = None
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=response_code.RET.DBERR, errmsg='查询新闻数据错误')

    #4，新闻点击量加1
    if news:
        news.clicks += 1
    else:
        abort(404)

    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=response_code.RET.DBERR, errmsg='跟新新闻点击量失败')

    #5.判断该新闻是否被该登录用户收藏，以便界面显示
    is_collect = False
    if user:
        if news in user.collection_news:
            is_collect = True

    #6.查询该新闻的所有评论
    comments = None
    try:
        comments = Comment.query.filter(Comment.news_id == news_id).order_by(Comment.create_time.desc()).all()
    except Exception as e:
        current_app.logger.error(e)
    comments_dict_list = []
    if comments:
        for comment in comments:
            commentlike = None
            try:
                commentlike = CommentLike.query.filter(CommentLike.comment_id == comment.id, CommentLike.user_id == user.id).first()
            except Exception as e:
                current_app.logger.error(e)
            comment_dict = comment.to_dict()
            if not commentlike:
                comment_dict['is_commentlike'] = False
            else:
                comment_dict['is_commentlike'] = True
            comments_dict_list.append(comment_dict)

    context = {
        'user':user.to_dict() if user else None,
        'news':news.to_dict() if news else None,
        'news_clicks':news_clicks,
        'is_collect':is_collect,
        'comments':comments_dict_list
    }
    return render_template('news/detail.html', context=context)