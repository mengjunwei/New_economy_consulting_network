from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
from info import create_app, db


app = create_app('pro')
manager = Manager(app)
Migrate(app, db)
manager.add_command('mysql', MigrateCommand)


@app.route('/')
def index():

    return 'in index'

if __name__ == '__main__':
    manager.run()