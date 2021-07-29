from enum import Enum

token = '1917677966:AAHK0LvN3S3y3vYcQjIgC3Q4mAs2PgaLwjk'
db_file = "database.vdb"

class States(Enum):
    Nothing = '0'
    HowManySeats = '1'
    CheckPass = '2'
    CreateActionName = '3'
    CreateActionTime = '4'
    CreateActionPlace = '5'
    CreateActionSeats = '6'
    CreateActionDescription = '7'