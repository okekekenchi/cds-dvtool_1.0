import json
from database.database import engine, Base, get_db
from models.user import User
from models.session import Session
from models.validation_checklist import ValidationChecklist
from models.bh_task_type import BhTaskType
from models.bh_task_type_vs_mb import BhTaskTypeVsMb
from models.ca_scheduled_task import CaScheduledTask
from models.ca_task_code_interval import CaTaskCodeInterval
from models.ca_task_code_vs_hg_smr_code import CaTaskCodeVsHgSmrCode
from models.ca_task_code_vs_task_id import CaTaskCodeVsTaskId
from models.hg_smr_vs_icc import HgSmrVsIcc
from models.xb_lcn_indenture import XbLcnIndenture
from models.tag import Tag
from utils import get_model_class

def init_db():
    """Initialize the database, creating all tables"""
    Base.metadata.create_all(bind=engine)
    
    # Load master data
    with open("config/master.json", "r") as file:
        masters = (json.load(file))
    
    for table in masters.keys():
        for data in masters.get(table, {}).get("data", []):
            with get_db() as db:
                model = get_model_class(table)
                model.first_or_create(db, find_by="code", **data)
    