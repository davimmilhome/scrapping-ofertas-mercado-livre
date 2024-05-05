from datetime import datetime

class TimeUtils:
    @staticmethod
    def get_current_iso_datetime():
        current_datetime = datetime.now().isoformat()
        return current_datetime

    @staticmethod
    def get_current_ddmmyy_date():
        current_date = datetime.now()
        ddmmyy_date = current_date.strftime("%d-%m-%y")
        return ddmmyy_date