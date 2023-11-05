import inspect

from os import remove
from os.path import exists
from json import dump, load
from datetime import datetime

import sqlalchemy.orm.decl_api
from sqlalchemy import DateTime

from data.db_session import *
import data.models as models

path, tmp = "db/data.sqlite3", "tables/tables.json"


def migrate():
    bases = {}
    for key, data in inspect.getmembers(models, inspect.isclass):
        if type(data) is sqlalchemy.orm.decl_api.DeclarativeMeta and data.__name__ != "Base":
            bases[data.__name__] = data

    if not exists(tmp):
        global_init(path)
        db_sess = create_session()
        db = {}

        for name, data in bases.items():
            db[name] = [obj.to_dict() for obj in db_sess.query(data).all()]

        with open(tmp, 'x', encoding='utf-8') as json:
            dump(db, json, indent=4, ensure_ascii=False)

        print("Отредактируйте модель и перезапустите этот скрипт")
    else:
        if exists(path):
            remove(path)

        global_init(path)
        db_sess = create_session()

        with open(tmp, 'r', encoding='utf-8') as json:
            db = load(json)

        for model_name in db:
            model = bases[model_name]

            columns = [column for column in model().__table__.columns]

            for item in db[model_name]:
                item: dict
                item_data = {}

                for key in item.keys():
                    for column in columns:
                        if key == column.key:
                            if item[key] is not None:
                                if isinstance(column.type, DateTime):
                                    item_data[key] = datetime.strptime(item[key], "%Y-%m-%d %H:%M:%S")
                                else:
                                    item_data[key] = item[key]
                item_model = model(**item_data)
                db_sess.add(item_model)
        db_sess.commit()

        remove(tmp)
        print("Успешно")


if __name__ == '__main__':
    migrate()
