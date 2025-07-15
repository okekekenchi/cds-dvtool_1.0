from enum import Enum, unique

@unique
class ListType(Enum):
    Master = 'master'
    Sheet = 'sheet'
    Checklist = 'checklist'