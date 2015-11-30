from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, User, Category, Item
import json
import sys
import time

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
    """ Method that insert users by by one,  and add them a set of categories with items into database
    """
    data = read_data_from_json_file("sample_data.json")
    for element_user in data:
        user = User(name=element_user["name"], email=element_user["email"],
                    picture=element_user["picture"])
        db_session.add(user)
        db_session.commit()
        for element_category in element_user["categories"]:
            category = Category(name=element_category["name"], user_id=user.id)
            db_session.add(category)
            db_session.commit()
            time.sleep(1)
            for element_item in element_category["items"]:
                item = Item(name=element_item["name"], description= element_item["description"],
                            category_id=category.id, image_path=element_item["image_path"],
                            user_id=user.id)
                db_session.add(item)
                db_session.commit()


if __name__ == '__main__':
    main()
