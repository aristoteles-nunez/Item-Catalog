from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, User, Category, Item
import json
import sys

engine = create_engine('sqlite:///item_catalog.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
db_session = DBSession()


def read_data_from_json_file(file_name):
    """Method that reads a file with JSON content.
    Args:
        file_name: Exactly path of the file, if the file is in the same
                   directory of the program just pass the name.
    Returns:
        A python Dict Object from a valid Json Document.
    Raises:
        An Exception if the data being deserialized is not a valid JSON
        document or the file isn't found.
    """
    try:
        data = json.load(open(file_name))
    except Exception as e1:
        print("Error  failed to open file: {}".format(file_name))
        print(e1)
        sys.exit(0)
    return data


def main():
    """ Method that insert one user and adds a set of categories with items into database
    """
    user = User(name="Sotsir", email="sotshiro@gmail.com", picture="")
    db_session.add(user)
    db_session.commit()
    data = read_data_from_json_file("sample_data.json")
    for element in data:
        category = Category(name=element["name"], image_path=element["image_path"],
                            user_id=element["user_id"])
        db_session.add(category)
        db_session.commit()


if __name__ == '__main__':
    main()
