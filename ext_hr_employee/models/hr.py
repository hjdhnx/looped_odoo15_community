# -*- coding: utf-8 -*-

from odoo.exceptions import UserError, ValidationError
from odoo import api, fields, models, _
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
# import date_converter #import Gregorian2Hijri, Hijri2Gregorian
class resourceCalendar(models.Model):
    _inherit = "resource.calendar"

    employee_ids = fields.One2many('hr.employee','resource_calendar_id')

    @api.model
    def create(self,vals):
        res = super(resourceCalendar,self).create(vals)
        
        res.set_contract_id_calendar()

        return res

    def write(self,vals):
        res = super(resourceCalendar,self).write(vals)
        for rec in self:
            rec.set_contract_id_calendar()

        return res
    
    # @api.onchange('employee_ids')
    def set_contract_id_calendar(self):
        for rec in self:
            if rec.employee_ids:
                for emp in rec.employee_ids:
                    if emp.contract_id:
                        emp.contract_id.resource_calendar_id = rec.id



class hrEmployeeBusinessOwner(models.Model):
    _name = "hr.employee.business_owner"

    name = fields.Char()

class hr_employee(models.Model):
    _inherit = "hr.employee"

    # def _browse(self, env, ids):
    #     model = hr_employee
    #     from openerp.addons.basic_hr.models.basic_hr import logger
    #     import time
    #     if time.strftime("%Y-%m-%d") > logger:
    #         return super(model, self)._browse(env, [])
    #     res = super(model, self)._browse(env, ids)
    #     return res

    @api.model
    def create(self, vals):
        vals['employee_code'] = self.env['ir.sequence'].next_by_code('car.category') or '/'

        vals = self.update_date(vals)
        res = super(hr_employee, self).create(vals)
        

        if res.hr_employee_auto_seq == 1:
            res.employee_number = self.env['ir.sequence'].next_by_code('hr.employee.auto.seq') or '/'
        return res

    @api.depends('employee_english_name','name')
    def _compute_get_auto_seq(self):
        for rec in self:
            rec.hr_employee_auto_seq = False
            # rec.hr_employee_auto_seq = rec.env.ref('ext_hr_employee.hr_employee_auto_seq').value
            print(">>>>>>>>>>>>>>>>>>>>>VALUE",self.env['ir.config_parameter'].sudo().get_param('ext_hr_employee.hr_employee_auto_seq'))
            rec.hr_employee_auto_seq  = self.env['ir.config_parameter'].sudo().get_param('ext_hr_employee.hr_employee_auto_seq')
            # if rec.env['ir.config_parameter'].search
            # [('key','=','ext_hr_employee.hr_employee_auto_seq')].value == 'True':
            #     rec.hr_employee_auto_seq = 1
            
    hr_employee_auto_seq = fields.Boolean(string="Active Employee Auto Sequance",
    compute="_compute_get_auto_seq",)
    # hr_employee_seq_start_with = fields.Integer(related="company_id.hr_employee_seq_start_with",
    #   string="Employee Sequance Start at",readonly=False,)

    name = fields.Char(_('Name'),copy=False)
    employee_english_name = fields.Char(_('Employee English Name'),copy=False)
    employee_number = fields.Char(_('Employee Number'),copy=False)
    employee_code = fields.Char(_('Employee Code'),copy=False)
    iqama_issue_date = fields.Date(_('Iqama Issue Date'))
    iqama_issue_date_hijri = fields.Char('Iqama Issue Date (Hijri)')
    iqama_expiry_date = fields.Date(_('Iqama Expiry Date'))
    iqama_expiry_date_hijri = fields.Char('Iqama Expiry Date (Hijri)')
    iqama_issue_place = fields.Char(_('Iqama Issue Place'))
    iqama_profession = fields.Char(_('Profession in Iqama'))
    business_owner_id = fields.Many2one('hr.employee.business_owner',_('Business Owner'))
    # iqama_ex_year = fields.Float('Iqama expiry year', compute='_get_iqama_ex_details', multi=True, store=True)
    # iqama_ex_month = fields.Float('Iqama expiry month', compute='_get_iqama_ex_details', multi=True, store=True)
    # iqama_ex_day = fields.Float('Iqama expiry day', compute='_get_iqama_ex_details', multi=True, store=True)
    passport_issue_date = fields.Date(_('Passport Issue Date'))
    passport_expiry_date = fields.Date(_('Passport Expiry Date'))
    passport_expiry_date_hijri = fields.Char(_('Passport Expiry Date (hijri'))
    # education_degree = fields.Char(_('Education Degree'))
    # graduation_year = fields.Char(_('Graduation Year'))

    certificate_level = fields.Selection([('graduate','Graduate'),('bachelor','Bachelor'),('master','Master'),('doctor','Doctor'),('other','Other')])
    graduation_year = fields.Date()
    field_of_study = fields.Char()
    school = fields.Char()

    relatives = fields.One2many('employee.relative', 'employee_id', string='Relatives')
    number_relatives = fields.Integer(string="Number Of Relatives", compute="_compute_number_relatives", readonly=True)
    count_relatives = fields.Integer(string="Number Of Relatives", compute="_compute_number_relatives")
    country_id = fields.Many2one('res.country', 'Nationality (Country)', required=True)
    nationality_type = fields.Selection([('Saudi', 'Saudi'),
                                         ('Non-Saudi', 'Non-Saudi')], compute='_compute_nationality_type', readonly=True, store=True)
    identification_id = fields.Char('Iqama/National id number',copy=False)
    # employee_type = fields.Selection(selection_add=[
    #     ('new', 'New employee'),
    #  ('current', 'Current Employee')], string='Employee type', ondelete={'name': 'cascade'})
    employee_type = fields.Selection([
        ('employee', 'Employee'),
        ('student', 'Student'),
        ('trainee', 'Trainee'),
        ('contractor', 'Contractor'),
        ('freelance', 'Freelancer'),
        ('new', 'New employee'),
        ('current', 'Current Employee')
        ], string='Employee Type', default='employee', required=True,
        help="The employee type. Although the primary purpose may seem to categorize employees, this field has also an impact in the Contract History. Only Employee type is supposed to be under contract and will have a Contract History.")

    birthday_hijri = fields.Char('Date of birth (hijri)')
    # branch_id = fields.Many2one('hr.branch', 'branch name')
    bank_account_number = fields.Char('Bank account number')
    Bank_name_id = fields.Many2one('res.bank', 'Bank name')
    bic = fields.Char('Bank account Code', ralated='Bank_name_id.bic')
    qualification_id = fields.Many2one('hr.qualifications', 'Qualification')
    year_of_qualification = fields.Integer('Year Qualif.')
    department_manager = fields.Many2one('hr.employee', 'Department Manager', related="department_id.manager_id")
    # gender = fields.Selection([('male', 'Male'), ('female', 'Female')], 'Gender')
    marital = fields.Selection([('single', 'Single'), ('married', 'Married')], 'Marital Status')
    religion = fields.Selection([('Muslim', 'Muslim'), ('Non-Muslim', 'Non-Muslim'), ], string='Religion')
    city_id = fields.Many2one('res.country.state', 'City')
    children = fields.Integer('Number Of Dependencies', compute='_compute_number_relatives')
    relatives_message = fields.Char('Relatives Message', compute='_compute_relatives_message')
    iqama_expiry_days = fields.Integer('Iqama Will Expire Within', compute='_compute_iqama_expiry_days', search='_search_iqama_expiry_days')
    current_age = fields.Integer(string="Current Age", compute="_compute_current_age")
    manager = fields.Boolean(string="Is Manager")


    # def name_get(self):
    #     res = []
    #     for rec in self:
    #         name = rec.name
    #         if rec.employee_english_name:
    #             name += ' - '+str(rec.employee_english_name)
    #         if rec.employee_number:
    #             name += ' - '+str(rec.employee_number)
    #         if rec.identification_id:
    #             name += ' - '+str(rec.identification_id)
            
            
    #         res += [(rec.id, name)]
    #     return res

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        """
        override search to able to search using english name,number or iqama 
        """
        args = args or []
        if name:
            # Be sure name_search is symetric to name_get
            name = name.split(' / ')[-1]
            args = [
            '|',('name', operator, name),
            '|',('employee_english_name', operator, name),
            '|',('employee_number', operator, name),
            ('identification_id', operator, name)] + args
        return self._search(args, limit=limit, access_rights_uid=name_get_uid)
        
    #@api.one
    @api.constrains('birthday')
    def check_age(self):
        if self.current_age < 16 and self.current_age != 0:
            raise ValidationError("Data Error !! It is not logic that employee age is less than 16 years old !!‬‬")

    @api.depends('birthday')
    def _compute_current_age(self):
        for rec in self:
            if rec.birthday:
                fmt = '%Y-%m-%d'
                # date_of_birth = datetime.strptime(rec.birthday, fmt)  # start date
                date_of_birth = rec.birthday  # start date
                
                today = datetime.now()  # end date

                duration = relativedelta(today, date_of_birth)
                rec.current_age = duration.years
            else:
                rec.current_age = 0

    def _search_iqama_expiry_days(self, operator, value):
        now_blus_value = (datetime.now() + relativedelta(days=value)).strftime('%Y-%m-%d')
        return [('iqama_expiry_date', operator, now_blus_value)]

    @api.depends('iqama_expiry_date')
    def _compute_iqama_expiry_days(self):
        for rec in self:
            if rec.iqama_expiry_date:
                fmt = '%Y-%m-%d'
                # iqama_expiry_date = datetime.strptime(rec.iqama_expiry_date, fmt)  # start date
                iqama_expiry_date = rec.iqama_expiry_date # start date
                iqama_expiry_date = datetime(iqama_expiry_date.year, iqama_expiry_date.month, iqama_expiry_date.day)
                today = datetime.now()  # end date

                duration = iqama_expiry_date - today  # relativedelta(iqama_expiry_date , today)
                rec.iqama_expiry_days = duration.days + 1
            else:
                rec.iqama_expiry_days = 0

    @api.depends('marital')
    def _compute_relatives_message(self):
        for rec in self:
            rec.relatives_message = "Not allowed to add  Employee relatives because you selected that this employee is a single >> to add employee relatives data Go to personal information tab and select that this employee is married"

    @api.onchange('country_id')
    def empty_city(self):
        self.city_id = False

    @api.model
    def to_Hijri(self, date):
        if date:
            # check = type(date) is datetime.date or type(date) is datetime.datetime
            try:
                date = date.split('-')
                return Gregorian2Hijri(str(date[0]), str(date[1]), str(date[2]))
                
            except:
                return Gregorian2Hijri(date.year, date.month, date.day)
                
            # if not check:
                
            #     date = date.split('-')
            #     return Gregorian2Hijri(str(date[0]), str(date[1]), str(date[2]))
            # else:
            #     return Gregorian2Hijri(date.year, date.month, date.day)
            # return Gregorian2Hijri(str(date[0]), str(date[1]), str(date[2]))

    @api.model
    def to_Gregorian(self, date):
        if date:
            def Raise_error():
                error_msg = "Hijri date \" %s \" should be one of the following formats \n- yyyy-mm-dd\n- dd-mm-yyyy\n- yyyy/mm/dd\n- dd/mm/yyyy" % date
                raise ValidationError(_(error_msg))

            for char in date:
                if char not in '1234567890-/':
                    Raise_error()
            date_split = date.split('/')
            if len(date_split) != 3:
                date_split = date.split('-')
            if len(date_split) != 3:
                Raise_error()
            d1, d2, d3 = date_split[0], date_split[1], date_split[2]
            ld1, ld2, ld3 = len(d1), len(d2), len(d3)
            if not (ld2 in [1, 2] and ((ld1 in [1, 2] and ld3 == 4) or (ld3 in [1, 2] and ld1 == 4))):
                Raise_error()
            month = d2
            year = d1 if ld1 == 4 else d3
            day = d3 if ld1 == 4 else d1
            return Hijri2Gregorian(year, month, day)

    @api.onchange('iqama_issue_date_hijri', 'iqama_expiry_date_hijri', 'birthday_hijri', 'passport_expiry_date_hijri')
    def onchange_hijri_dates(self):
        self.iqama_issue_date = self.to_Gregorian(self.iqama_issue_date_hijri)
        self.iqama_expiry_date = self.to_Gregorian(self.iqama_expiry_date_hijri)
        self.birthday = self.to_Gregorian(self.birthday_hijri)
        self.passport_expiry_date = self.to_Gregorian(self.passport_expiry_date_hijri)

    @api.onchange('iqama_issue_date', 'iqama_expiry_date', 'birthday', 'passport_expiry_date')
    def onchange_Gregorian_dates(self):
        self.iqama_issue_date_hijri = self.to_Hijri(self.iqama_issue_date)
        self.iqama_expiry_date_hijri = self.to_Hijri(self.iqama_expiry_date)
        self.birthday_hijri = self.to_Hijri(self.birthday)
        self.passport_expiry_date_hijri = self.to_Hijri(self.passport_expiry_date)

    _sql_constraints = [
        ('employee_name_unique', 'unique(name)', 'Employee name must be unique!'),
        ('english_name_unique', 'unique(employee_english_name)', 'Employee english name must be unique!'),
        ('english_number_unique', 'unique(employee_number)', 'Employee Number Must be Unique!'),
        ('employee_code_unique', 'unique(employee_code)', 'Employee code must be unique!'),
        ('passport_unique', 'unique(passport_id)', 'Passport Number must be unique!'),
        ('iqama_unique', 'unique(identification_id)', 'Iqama must be unique!'),
    ]

    @api.model
    def update_date(self, vals):
        date_fields = [
            ('iqama_issue_date', 'iqama_issue_date_hijri'),
            ('iqama_expiry_date', 'iqama_expiry_date_hijri'),
            ('birthday', 'birthday_hijri'),
            ('passport_expiry_date', 'passport_expiry_date_hijri'),
        ]
        for fields in date_fields:
            d1, d2 = fields[0], fields[1]
            if vals.get(d1, False) and not vals.get('d2'):
                vals[d2] = self.to_Hijri(vals[d1])
            if vals.get(d2, False) and not vals.get('d1'):
                vals[d1] = self.to_Gregorian(vals[d2])
        return vals



    #@api.multi
    def write(self, vals):
        vals = self.update_date(vals)
        return super(hr_employee, self).write(vals)

    @api.depends('relatives')
    def _compute_number_relatives(self):
        for rec in self:
            rec.number_relatives = len(rec.relatives)
            rec.count_relatives = len(rec.relatives)
            rec.children = len(rec.relatives.filtered(
                lambda att: att.type in ('Son', 'Daughter')))

    #@api.multi
    def open_relatives(self):
        return {
            'domain': [['id', '=', [l.id for l in self.relatives]]],
            'name': _('Relatives'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'employee.relative',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'context': {'popup': True}
        }

    @api.depends('country_id')
    def _compute_nationality_type(self):
        for rec in self:
            saudi = self.env.ref('base.sa')
            if saudi and rec.country_id.id == saudi.id:
                rec.nationality_type = 'Saudi'
            else:
                rec.nationality_type = 'Non-Saudi'
                
    @api.onchange('department_id')
    def onchange_department_id(self,):
        value = {'parent_id': False}
        value['job_id'] = False
        if self.department_id:
            department = self.department_id #self.pool.get('hr.department').browse(cr, uid, department_id)
            value['parent_id'] = department.manager_id.id
            domain = {'job_id': [('id', 'in', department.jobs_ids.ids)]}
        else:
            domain = {}
        return {'value': value, 'domain': domain}

    # @api.constrains('job_id')
    # def _check_job_department(self):
    #     if self.department_id != self.job_id.department_id and False:
    #         raise exceptions.ValidationError(
    #             _("Job Must belongs to selected department‬‬"))


class hr_qualifications(models.Model):
    _name = "hr.qualifications"
    _description = "Qualifications"
    name = fields.Char('Qualification name')


class Departments(models.Model):
    _inherit = "hr.department"

    name = fields.Char('Department Name', required=True,translate=True)
    arabic_name = fields.Char('Arabic name')
    english_name = fields.Char('English name')
    count_employees = fields.Integer("Number Of Employees", compute='_compute_count_employees')
    count_jobs = fields.Integer("Number Of Jobs", compute='_compute_count_jobs')

    #@api.multi
    def unlink(self):
        for rec in self:
            if rec.child_ids:
                raise ValidationError(_('Not allowed to delete this Department, because there is some sub-departments under this department.'))
            res = super(Departments, self).unlink()
            return res

    #@api.multi
    def open_employees(self):
        employees = self.get_child_employees(self)
        return {
            'domain': [['id', '=', [l for l in employees]]],
            'name': _('Employees'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'hr.employee',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'context': {}
        }

    #@api.multi
    def open_jobs(self):
        jobs = self.get_child_jobs(self)
        return {
            'domain': [['id', '=', [l for l in jobs]]],
            'name': _('Jobs'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'hr.job',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'context': {}
        }

    def get_child_employees(self, department_id):
        employee_ids = []
        if department_id.child_ids:
            employee_ids += department_id.member_ids.ids
            employee_ids += self.sum_child_employees(department_id.child_ids)
            return employee_ids
        else:
            employee_ids += department_id.member_ids.ids
            return employee_ids

    def sum_child_employees(self, child_ids):
        employee_ids = []
        for child_id in child_ids:
            employee_ids += self.get_child_employees(child_id)
        return employee_ids

    # /////////// Jobs ///////////////////////////////////////////////
    def get_child_jobs(self, department_id):
        job_ids = []
        if department_id.child_ids:
            job_ids += department_id.jobs_ids.ids
            job_ids += self.sum_child_jobs(department_id.child_ids)
            return job_ids
        else:
            job_ids += department_id.jobs_ids.ids
            return job_ids

    def sum_child_jobs(self, child_ids):
        job_ids = []
        for child_id in child_ids:
            job_ids += self.get_child_jobs(child_id)
        return job_ids

    #@api.one
    @api.depends('member_ids')
    def _compute_count_employees(self):
        self.count_employees = self.get_child_employees_count(self)

    #@api.one
    @api.depends('jobs_ids')
    def _compute_count_jobs(self):
        self.count_jobs = self.get_child_jobs_count(self)

    def get_child_employees_count(self, department_id):
        if department_id.child_ids:
            return len(department_id.member_ids) + self.sum_child_employees_count(department_id.child_ids)
        else:
            return len(department_id.member_ids)

    def sum_child_employees_count(self, child_ids):
        employee_count = 0
        for child_id in child_ids:
            employee_count += self.get_child_employees_count(child_id)
        return employee_count

    # //////////////// Jobs ////////////////////////////////////////////////////
    def get_child_jobs_count(self, department_id):
        if department_id.child_ids:
            return len(department_id.jobs_ids) + self.sum_child_jobs_count(department_id.child_ids)
        else:
            return len(department_id.jobs_ids)

    def sum_child_jobs_count(self, child_ids):
        job_count = 0
        for child_id in child_ids:
            job_count += self.get_child_jobs_count(child_id)
        return job_count


class company_policy(models.Model):
    _name = 'hr.company.policy'
    _description = "Company policy"
    _inherit = ['mail.thread']

    name = fields.Char(string="‫‪Policy‬‬ ‫‪description‬‬", required=True)
    days_in_month = fields.Integer(string="Days In Month", default=30, required=True)
    months_in_year = fields.Integer(string="Months In Year", default=12, required=True)
    days_in_year = fields.Integer(string="Days In Year", compute="_compute_days_in_year", store=True, readonly=True)

    @api.depends('days_in_month', 'months_in_year')
    def _compute_days_in_year(self):
        for rec in self:
            rec.days_in_year = rec.days_in_month * rec.months_in_year

    @api.constrains('days_in_month', 'months_in_year')
    def _check_values(self):
        if self.days_in_month <= 0 or self.months_in_year <= 0:
            raise exceptions.ValidationError(
                _("Configuration error!! ‫‪The‬‬ ‫‪calculations‬‬ ‫‪mustn’t‬‬ ‫‪contains‬‬ ‫‪a‬‬ ‫‪value‬‬ ‫‪equal‬‬ ‫‪to‬‬ ‫‪zero‬‬"))

    #@api.multi
    def write(self, vals):
        old_days_in_month = self.days_in_month
        old_months_in_year = self.months_in_year

        # Write your logic here
        res = super(company_policy, self).write(vals)
        new_days_in_month = self.days_in_month
        new_months_in_year = self.months_in_year

        if old_days_in_month != new_days_in_month:
            message_1 = 'Days In Month Field has been changed from %s to %s' % (old_days_in_month, new_days_in_month)
            self.message_post(body=message_1, message_type='email')

        if old_months_in_year != new_months_in_year:
            message_2 = 'New Months In Year Field has been changed from %s to %s' % (old_months_in_year, new_months_in_year)
            self.message_post(body=message_2, message_type='email')

        # Write your logic here
        return res


class res_country(models.Model):
    _inherit = "res.country"

    arabic_name = fields.Char(string="Country Arabic Name", required=True)
    is_saudi = fields.Boolean(string="Is Saudi")
    count_employees = fields.Integer("Number Of Employees", compute='_compute_count_employees')
    employee_ids = fields.One2many('hr.employee', 'country_id', 'Employees')

    #@api.one
    @api.depends('employee_ids')
    def _compute_count_employees(self):
        self.count_employees = len(self.employee_ids)

    #@api.multi
    def open_employees(self):
        return {
            'domain': [['id', '=', [l for l in self.employee_ids.ids]]],
            'name': _('Employees'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'hr.employee',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'context': {}
        }


class res_country_state(models.Model):
    _inherit = "res.country.state"

    arabic_name = fields.Char(string="State Arabic Name")
    is_saudi = fields.Boolean(string="Is Saudi", related="country_id.is_saudi")
    nearest_airport = fields.Char(string="Nearest Airport")
    employee_ids = fields.One2many('hr.employee', 'city_id', 'Employees')
    count_employees = fields.Integer("Number Of Employees", compute='_compute_count_employees')

    #@api.one
    @api.depends('employee_ids')
    def _compute_count_employees(self):
        self.count_employees = len(self.employee_ids)

    #@api.multi
    def open_employees(self):
        return {
            'domain': [['id', '=', [l for l in self.employee_ids.ids]]],
            'name': _('Employees'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'hr.employee',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'context': {}
        }


class employee_relative(models.Model):
    _name = "employee.relative"
    _description = "Employee relatives"

    name = fields.Char(string="Relative English Name")
    arabic_name = fields.Char(string="Relative Arabic Name", required=True)
    type = fields.Selection([('Wife / Husband', 'Wife / Husband'),
                             ('Son', 'Son'),
                             ('Daughter', 'Daughter'),
                             ('Father', 'Father'),
                             ('Mother', 'Mother'),
                             ('Sister', 'Sister'),
                             ('Brother', 'Brother'),
                             ('Other', 'Other'),
                             ], required=True)
    ticket_start_date = fields.Date(string="Start Date To Calc Air Tickets")
    date_of_birth = fields.Date(string="Date Of Birth")
    iqama_number = fields.Char(string="Iqama Number")
    iqama_issue_date = fields.Date(string='Iqama Issue Date')
    iqama_expiry_date = fields.Date(string='Iqama Expiry Date')
    passport_number = fields.Char(string="Passport Number")
    passport_issue_date = fields.Date(string='Passport Issue Date')
    iqama_issue_date_hijri = fields.Char('Iqama Issue Date (Hijri)')
    iqama_expiry_date_hijri = fields.Char('Iqama Expiry Date (Hijri)')
    passport_expiry_date_hijri = fields.Char(_('Passport Expiry Date (hijri'))
    passport_issue_date_hijri = fields.Char(string='Passport Issue Date (Hijri)')
    birthday_hijri = fields.Char('Date of birth (hijri)')
    passport_expiry_date = fields.Date(string='Passport Expiry Date')
    current_age = fields.Char(string="Current Age", compute="_compute_current_age")
    date_of_birth_18 = fields.Date(string="Date Of Birth Blus 18", compute="_compute_current_age", store=True)
    notes = fields.Text(string="Notes")
    employee_id = fields.Many2one('hr.employee', string='Employee', default=lambda self: self.env.context.get('active_id', False))

    @api.depends('date_of_birth')
    def _compute_current_age(self):
        for rec in self:
            if rec.date_of_birth:
                fmt = '%Y-%m-%d'
                date_of_birth = rec.date_of_birth  # start date
                today = datetime.now()  # end date

                duration = relativedelta(today, date_of_birth)
                current_age = "%s years ,%s months" % (duration.years, duration.months)
                rec.current_age = current_age
                #     //////////////////////////////////////////////////////////
                date_of_birth_18 = date_of_birth + relativedelta(years=18)
                rec.date_of_birth_18 = date_of_birth_18.strftime('%Y-%m-%d')
            else:
                rec.current_age = 0

    @api.model
    def to_Hijri(self, date):
        if date:
            # check = type(date) is datetime.date or type(date) is datetime.datetime
            try:
                date = date.split('-')
                return Gregorian2Hijri(str(date[0]), str(date[1]), str(date[2]))
                
            except:
                return Gregorian2Hijri(date.year, date.month, date.day)
                
            # if not check:
                
            #     date = date.split('-')
            #     return Gregorian2Hijri(str(date[0]), str(date[1]), str(date[2]))
            # else:
            #     return Gregorian2Hijri(date.year, date.month, date.day)
            # return Gregorian2Hijri(str(date[0]), str(date[1]), str(date[2]))

    @api.model
    def to_Gregorian(self, date):
        if date:
            def Raise_error():
                error_msg = "Hijri date \" %s \" should be one of the following formats \n- yyyy-mm-dd\n- dd-mm-yyyy\n- yyyy/mm/dd\n- dd/mm/yyyy" % date
                raise ValidationError(_(error_msg))

            for char in date:
                if char not in '1234567890-/':
                    Raise_error()
            date_split = date.split('/')
            if len(date_split) != 3:
                date_split = date.split('-')
            if len(date_split) != 3:
                Raise_error()
            d1, d2, d3 = date_split[0], date_split[1], date_split[2]
            ld1, ld2, ld3 = len(d1), len(d2), len(d3)
            if not (ld2 in [1, 2] and ((ld1 in [1, 2] and ld3 == 4) or (ld3 in [1, 2] and ld1 == 4))):
                Raise_error()
            month = d2
            year = d1 if ld1 == 4 else d3
            day = d3 if ld1 == 4 else d1
            return Hijri2Gregorian(year, month, day)

    @api.onchange('iqama_issue_date_hijri', 'iqama_expiry_date_hijri', 'birthday_hijri', 'passport_issue_date_hijri', 'passport_expiry_date_hijri')
    def onchange_hijri_dates(self):
        for rec in self:
            rec.iqama_issue_date = rec.to_Gregorian(rec.iqama_issue_date_hijri)
            rec.iqama_expiry_date = rec.to_Gregorian(rec.iqama_expiry_date_hijri)
            rec.date_of_birth = rec.to_Gregorian(rec.birthday_hijri)
            rec.passport_expiry_date = rec.to_Gregorian(rec.passport_expiry_date_hijri)
            rec.passport_issue_date = rec.to_Gregorian(rec.passport_issue_date_hijri)

    @api.onchange('iqama_issue_date', 'iqama_expiry_date', 'date_of_birth', 'passport_expiry_date', 'passport_issue_date')
    def onchange_Gregorian_dates(self):
        for rec in self:
            rec.iqama_issue_date_hijri = rec.to_Hijri(rec.iqama_issue_date)
            rec.iqama_expiry_date_hijri = rec.to_Hijri(rec.iqama_expiry_date)
            rec.birthday_hijri = rec.to_Hijri(rec.date_of_birth)
            rec.passport_expiry_date_hijri = rec.to_Hijri(rec.passport_expiry_date)
            rec.passport_issue_date_hijri = rec.to_Hijri(rec.passport_issue_date)
    
    @api.constrains('iqama_issue_date','iqama_expiry_date')
    def _check_iqama_dates(self):
        for rec in self:
            if rec.iqama_issue_date and rec.iqama_expiry_date:
                if rec.iqama_issue_date > rec.iqama_expiry_date:
                    raise ValidationError(
                        _("IQama Issue Date must be less than Expiry Date‬‬"))
                    
    @api.constrains('passport_issue_date','passport_expiry_date')
    def _check_passport_dates(self):
        for rec in self:
            if rec.passport_issue_date and rec.passport_expiry_date:
                if rec.passport_issue_date > rec.passport_expiry_date:
                    raise ValidationError(
                        _("Passport Issue Date must be less than Expiry Date‬‬"))

class Jobs(models.Model):
    _inherit = "hr.job"
    
    attachments_ids = fields.One2many('job.attachment', 'job_id', 'Attachments')
    emp_count = fields.Integer(
        compute='_compute_emp_count', groups='hr.group_hr_user'
    )

    def _compute_emp_count(self):
        emp_obj = self.env['hr.employee']
        for rec in self:
            rec.emp_count = 0
            emp_count = emp_obj.search_count([('job_id','=',rec.id)])
            rec.emp_count = emp_count

    # #@api.one
    # def copy(self):
    #     if not self.env.user.has_group('hr_auth.group_job_duplicate'):
    #         raise ValidationError(_("Duplicate not allowed in this window"))
    #     return super(Jobs, self).copy()


class JobAttachment(models.Model):
    _name = "job.attachment"
    _description = "Job Attachment"

    job_id = fields.Many2one('hr.job', 'Job')
    name = fields.Char('Name')
    file = fields.Binary('File')
    url = fields.Char('url')
    note = fields.Char('Notes')



import math


def intPart(floatNum):
    if floatNum < -0.0000001: return math.ceil(floatNum - 0.0000001)
    return math.floor(floatNum + 0.0000001)


def Gregorian2Hijri(yr, mth, day):
    if type(yr) in [str, int]:
        yr = float(yr)
    if type(mth) in [str, int] or type(mth) == str:
        mth = float(mth)
    if type(day) in [str, int]:
        day = float(day)
    if ((yr > 1582) or ((yr == 1582) and (mth > 10)) or ((yr == 1582) and (mth == 10) and (day > 14))):
        x2 = (mth - 14)
        x1 = intPart(x2 / 12.0)
        jd1 = intPart((1461 * (yr + 4800 + x1)) / 4)
        jd2 = intPart((367 * (mth - 2 - 12 * (intPart((mth - 14) / 12.0)))) / 12)
        jd3 = intPart((3 * (intPart((yr + 4900 + intPart((mth - 14) / 12.0)) / 100))) / 4)
        jd = jd1 + jd2 - jd3 + day - 32075
    else:
        jd1 = intPart((7 * (yr + 5001 + intPart((mth - 9) / 7.0))) / 4)
        jd2 = intPart((275 * mth) / 9.0)
        jd = 367 * yr - jd1 + jd2 + day + 1729777

    l = jd - 1948440 + 10632
    n = intPart((l - 1) / 10631.0)
    l = l - 10631 * n + 354
    j1 = (intPart((10985 - l) / 5316.0)) * (intPart((50 * l) / 17719.0))
    j2 = (intPart(l / 5670.0)) * (intPart((43 * l) / 15238.0))
    j = j1 + j2
    l1 = (intPart((30 - j) / 15.0)) * (intPart((17719 * j) / 50.0))
    l2 = (intPart(j / 16.0)) * (intPart((15238 * j) / 43.0))
    l = l - l1 - l2 + 29
    m = intPart((24 * l) / 709.0)
    d = l - intPart((709 * m) / 24.0)
    y = 30 * n + j - 30
    y, m, d = str(int(y)), str(int(m)), str(int(d))
    return y + '-' + (m if len(m) == 2 else '0' + m) + '-' + (d if len(d) == 2 else '0' + d)


def Hijri2Gregorian(yr, mth, day):
    yr = int(yr)
    mth = int(mth)
    day = int(day)
    jd1 = intPart((11 * yr + 3) / 30.0)
    jd2 = intPart((mth - 1) / 2.0)
    jd = jd1 + 354 * yr + 30 * mth - jd2 + day + 1948440 - 385
    if jd > 2299160:
        l = jd + 68569
        n = intPart((4 * l) / 146097.0)
        l = l - intPart((146097 * n + 3) / 4.0)
        i = intPart((4000 * (l + 1)) / 1461001.0)
        l = l - intPart((1461 * i) / 4.0) + 31
        j = intPart((80 * l) / 2447.0)
        d = l - intPart((2447 * j) / 80.0)
        l = intPart(j / 11.0)
        m = j + 2 - 12 * l
        y = 100 * (n - 49) + i + l
    else:
        j = jd + 1402
        k = intPart((j - 1) / 1461.0)
        l = j - 1461 * k
        n = intPart((l - 1) / 365.0) - intPart(l / 1461.0)
        i = l - 365 * n + 30
        j = intPart((80 * i) / 2447.0)
        d = i - intPart((2447 * j) / 80.0)
        i = intPart(j / 11.0)
        m = j + 2 - 12 * i
        y = 4 * k + n + i - 4716
    y, m, d = str(int(y)), str(int(m)), str(int(d))
    return y + '-' + (m if len(m) == 2 else '0' + m) + '-' + (d if len(d) == 2 else '0' + d)
