from pony.orm import db_session
from app.models.Estado import Estado

@db_session
def get_estado_by_id(id):
    return Estado.get(id=id)
