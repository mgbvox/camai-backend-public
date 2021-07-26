from datetime import datetime


def create_hl7(data: dict):
    place_order_number = ""
    universal_service_id = ""
    requested_datetime = ""
    observation_datetime = data['specimen_collection_datetime']
    transaction_datetime = datetime.now()
    enterer_location = ""
    ordering_provider = ""
    priority_code = ""
    order_status_number = 'R'
    priority_code = 'R'
    set_id = '1'
    msh = 'MSH|^~\&|ApteryxDataService|CamaiCHC|HC_ORU_OUT|JungleRoomUC|20210428104804||ORU^R01|866733|P|2.4|||AL'
    pid = f'PID|1|{data["patient_id"]}|500475620||{data["fname"]}^${data["lname"]}||{data["dob"]}|{data["sex"]}|||{data["address"]["street_name_number"]}^^{data["address"]["city"]}^{data["address"]["state"]}^{data["address"]["zipcode"]}|||||||{data["patient_acct_no"]}|||||||||||||'
    orc = f'ORC|{set_id}|{place_order_number}|||{order_status_number}||||{transaction_datetime}|||{ordering_provider}|{enterer_location}||||||'
    obr = f'OBR|{set_id}|{place_order_number}||{universal_service_id}|{priority_code}|{requested_datetime}|{observation_datetime}|||||||||LabPhyId1^Provider^Test|||||||||||^^^^^R|^ ~^ ~^ |||||'