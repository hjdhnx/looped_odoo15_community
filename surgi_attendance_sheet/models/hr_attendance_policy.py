# -*- coding: utf-8 -*-

##############################################################################
#    Copyright (C) 2020.
#    Author: Eng.Ramadan Khalil (<rkhalil1990@gmail.com>)
#    website': https://www.linkedin.com/in/ramadan-khalil-a7088164
#
#    It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
##############################################################################

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, date, timedelta, time
class hrContract(models.Model):
    _inherit = 'hr.contract'

    def get_salary_based_on(self,based_on):
        for rec in self:
            amount = 0
            if based_on == 'basic':
                amount = rec.basic_salary
            elif based_on  == 'total':
                amount = rec.total
            return amount
            
class HrAttendancePolicy(models.Model):
    _inherit = 'hr.attendance.policy'

    miss_rule_id = fields.Many2one(comodel_name="hr.miss.rule",
                                   string="Missed Punch Rule", required=False)

    def last_day_of_month(self,date):
        if date.month == 12:
            return date.replace(day=31)
        date = date.replace(month=date.month+1, day=1) - timedelta(days=1)
        return date.day

    def get_late(self,period, cnt,contract_id=False,month_days=1):
        res = period
        flag = False
        no = 1
        cnt_flag = False
        factor = 1
        if period <= 0:
            return 0, cnt
        if self.late_rule_id:
            time_ids = self.late_rule_id.line_ids.sorted(
                key=lambda r: r.time, reverse=True)
            for line in time_ids:
                if period >= line.time:
                    for counter in cnt:
                        if counter[0] == line.time:
                            cnt_flag = True
                            no = counter[1]
                            counter[1] += 1
                            break
                    if no >= 5 and line.fifth > 0:
                        factor = line.fifth
                    elif no >= 4 and line.fourth > 0:
                        factor = line.fourth
                    elif no >= 3 and line.third > 0:
                        factor = line.third
                    elif no >= 2 and line.second > 0:
                        factor = line.second
                    elif no >= 1 and line.first > 0:
                        factor = line.first
                    elif no == 0:
                        factor = 0
                    if not cnt_flag:
                        cnt.append([line.time, 2])
                    flag = True
                    if line.type == 'rate':
                        res = line.rate * period * factor
                    elif line.type == 'fix':
                        res = line.amount * factor
                    elif line.type == 'percentage_based':
                        amount = contract_id.get_salary_based_on(line.late_id.deduction_based_on)
                        amount = (amount/month_days)
                        res = amount * (factor/100)

                    break

            if not flag:
                res = 0
        return res, cnt

    def get_diff(self, period, diff_cnt,contract_id=False,month_days=1):
        res = period
        flag = False
        no = 1
        cnt_flag = False
        factor = 1
        if period <= 0:
            return 0, diff_cnt
        if self.diff_rule_id:
            time_ids = self.diff_rule_id.line_ids.sorted(
                key=lambda r: r.time, reverse=True)
            for line in time_ids:
                if period >= line.time:
                    for counter in diff_cnt:
                        if counter[0] == line.time:
                            cnt_flag = True
                            no = counter[1]
                            counter[1] += 1
                            break
                    if no >= 5:
                        factor = line.fifth
                    elif no >= 4:
                        factor = line.fourth
                    elif no >= 3:
                        factor = line.third
                    elif no >= 2:
                        factor = line.second
                    elif no >= 1:
                        factor = line.first
                    elif no >= 0:
                        factor = 1
                    if not cnt_flag:
                        diff_cnt.append([line.time, 2])
                    flag = True
                    if line.type == 'rate':
                        res = line.rate * period * factor
                    elif line.type == 'fix':
                        res = line.amount * factor
                    elif line.type == 'percentage_based':
                        amount = contract_id.get_salary_based_on(line.diff_id.deduction_based_on)
                        amount = (amount/month_days)
                        res = amount * (factor/100)
                    break
            if not flag:
                res = 0
        return res, diff_cnt

    def get_miss(self, cnt):
        self.ensure_one()
        res = 0
        flag = False
        if self:
            if self.miss_rule_id:
                miss_ids = self.miss_rule_id.line_ids.sorted(
                    key=lambda r: r.counter, reverse=True)
                for ln in miss_ids:
                    if cnt >= int(ln.counter):
                        res = ln.amount
                        flag = True
                        break
                if not flag:
                    res = 0
        return res

class HrLateRuleLine(models.Model):
    _inherit = 'hr.late.rule.line'
    
    type = [
        ('fix', 'Fixed'),
        ('rate', 'Rate'),
        ('percentage_based','Percentage From Based On/Month Days')
    ]

    type = fields.Selection(string="Type", selection=type, required=True, )
    first = fields.Float('First Time', default=1)
    second = fields.Float('Second Time', default=1)
    third = fields.Float('Third Time', default=1)
    fourth = fields.Float('Fourth Time', default=1)
    fifth = fields.Float('Fifth Time', default=1)


class HrDiffRuleLine(models.Model):
    _inherit = 'hr.diff.rule.line'

    type = [
        ('fix', 'Fixed'),
        ('rate', 'Rate'),
        ('percentage_based','Percentage From Based On/Month Days')
    ]

    type = fields.Selection(string="Type", selection=type, required=True, )
    first = fields.Float('First Time', default=1)
    second = fields.Float('Second Time', default=1)
    third = fields.Float('Third Time', default=1)
    fourth = fields.Float('Fourth Time', default=1)
    fifth = fields.Float('Fifth Time', default=1)

class hr_miss_rule(models.Model):
    _name = 'hr.miss.rule'

    name = fields.Char(string='name', required=True,translate=True)
    line_ids = fields.One2many(comodel_name='hr.miss.rule.line', inverse_name='miss_id', string='Missed punchis rules')
    deduction_based_on = fields.Selection([
        ('basic', 'Basic Salary'),
        
        ('total', 'Total salary'),
    ], string='Deduction based on')


class hr_miss_rule_line(models.Model):
    _name = 'hr.miss.rule.line'

    times = [
        ('1', 'First Time'),
        ('2', 'Second Time'),
        ('3', 'Third Time'),
        ('4', 'Fourth Time'),
        ('5', 'Fifth Time'),

    ]

    miss_id = fields.Many2one(comodel_name='hr.miss.rule', string='name')
    amount = fields.Float(string='amount',required=True)
    counter = fields.Selection(string="Times", selection=times, required=True, )

    _sql_constraints = [
        ('miss_rule_cons', 'unique(miss_id,counter)',
         'The counter Must Be unique Per Rule'),
    ]






