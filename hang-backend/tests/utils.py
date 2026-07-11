from sqlalchemy.orm import Session


def populate_db(db: Session, data: dict) -> dict:
    created: dict = {}

    for model, rows in data.items():
        created[model] = []
        for row in rows:
            resolved_row = {
                key: (value(created) if callable(value) else value)
                for key, value in row.items()
            }
            obj = model(**resolved_row)
            db.add(obj)
            db.flush()
            created[model].append(obj)

    db.commit()
    return created
