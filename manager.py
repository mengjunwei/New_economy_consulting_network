from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
from info import create_app, db


app = create_app('dev')
manager = Manager(app)
Migrate(app, db)
manager.add_command('mysql', MigrateCommand)


if __name__ == '__main__':
    print(app.url_map)
    manager.run()