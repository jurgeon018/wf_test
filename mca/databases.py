from mca.entities import Advance


# TODO: use relational database

class Database:

    def __init__(self):
        # int - Advance.id
        # dict is used in order to perform O(1) lookup of duplicates in Database.create_advances
        self.advances: dict[int, Advance] = {}

    def create_new_advances(self, advances: list[Advance]) -> None:
        for advance in advances:
            if not self.advances.get(advance.id):
                self.advances[advance.id] = advance

    def get_all_advances(self) -> list[Advance]:
        return self.advances.values()
