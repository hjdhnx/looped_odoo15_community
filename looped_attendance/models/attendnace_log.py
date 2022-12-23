# -*- coding: utf-8 -*-

from odoo import models, fields
import pytz
from pytz import timezone

class AttendanceLog(models.Model):
    _name = 'attendance.log'
    _description = 'attendance.log'

    name = fields.Char()
    loging_date = fields.Datetime('Loging Date')
    finger_print_pin = fields.Integer()
    check_type = fields.Integer()
    verify_code = fields.Integer()
    device_id = fields.Many2one('attendance.device', string='Device')



    def upset_datetime(self,datetime_wo_tz, tzone):
        """"  takes naive datetime (datetime_wo_tz) and it's timezone (tzone)
				returns the datetime aware with timezone changed to UTC
			"""
        localized_datetime = pytz.UTC.localize(datetime_wo_tz)
        datetime_with_tz = localized_datetime.astimezone(timezone(tzone))
        return datetime_with_tz
   
    
    def un_upset_datetime(self,datetime_wo_tz, tzone):
        """"  takes naive datetime (datetime_wo_tz) and it's timezone (tzone)
			returns the datetime aware with timezone changed to UTC
        """
        aware_datetime = pytz.timezone(tzone).localize(datetime_wo_tz)
        aware_datetime_utc = aware_datetime.astimezone(pytz.UTC)
        return aware_datetime_utc
    
