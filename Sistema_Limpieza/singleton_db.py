from models import db

class SingletonDB:
    __instance = None

    def __new__(cls, app=None):
        if cls.__instance is None:
            cls.__instance = super(SingletonDB, cls).__new__(cls)
            if app is not None:
                db.init_app(app)
            cls.__instance.db = db
        return cls.__instance