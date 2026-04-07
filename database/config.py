import os

DATABASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.environ.get('DATABASE_PATH', 
                               os.path.join(DATABASE_DIR, 'attention.db'))

DATABASE_CONFIG = {
    'db_path': DATABASE_PATH
}
