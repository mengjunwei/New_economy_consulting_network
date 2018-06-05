from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
from info import create_app, db, models
from info.models import User
from flask import session, current_app


app = create_app('dev')
manager = Manager(app)
Migrate(app, db)
manager.add_command('mysql', MigrateCommand)


@manager.option('-u', '-username', dest='username')
@manager.option('-m', '-mobile', dest='mobile')
@manager.option('-p', '-password', dest='password')
def create_super_user(password, mobile, username):
    if not all([password, mobile, username]):
        print('缺少参数')
    else:
        user = User()
        user.mobile = mobile
        user.nick_name = username
        user.password = password
        user.is_admin = True

        try:
            db.session.add(user)
            db.session.commit()
        except Exception as e:
            current_app.logger.error(e)
            print(e)
            db.session.rollback()


if __name__ == '__main__':
    print(app.url_map)
    manager.run()