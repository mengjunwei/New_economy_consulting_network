from . import news_blue
from info.utils.common import user_login_data
from flask import render_template



@news_blue.route('/news_detal/<int:news_id>')
@user_login_data
def news_detal(news_id):
    return render_template('/news/detail.html')