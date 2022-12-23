# -*- coding: utf-8 -*-

from openerp import models, fields, api
import os
import ftplib


class attachment_file_save(models.Model):
    _name = 'attachment.file.save'

    file_compute = fields.Binary(compute="_get_computed_file", inverse='_set_computed_file')
    file = fields.Binary(string='File', store=True)
    name = fields.Char(string='Name', required=True)
    model = fields.Char(compute='get_model_name', multi=True)
    res_id = fields.Float(string='res_id', compute='get_model_name', multi=True)
    attachment_location_paramter = fields.Char()
    database_file = fields.Boolean('Database File')
    filename = fields.Char('File name')
    source_id = fields.Many2one('res.users')

    #@api.one
    @api.depends('source_id')
    def get_model_name(self):
        self.model = self.source_id._name
        self.res_id = self.source_id.id

    @api.model
    def get_file_name(self):
        return "%s-%s%s-%s" % (str(int(self.id)), str(int(self.res_id)), self.name, self.filename)

    #@api.one
    def _set_computed_file(self):
        system_parameter_obj = self.env['ir.config_parameter'].search([('key', '=', 'ir_attachment.location')])
        use_server_to_transfer_file = self.env['ir.config_parameter'].search([('key', '=', 'use_server_to_transfer_file')])
        ServerConfiguration_obj = self.env['sever.configuration'].search([])
        if system_parameter_obj:
            if use_server_to_transfer_file and self.model and ServerConfiguration_obj:
                path = system_parameter_obj[0].value + "/" + self.model.replace('.', '_')
                # Open a transport
                import paramiko

                paramiko.util.log_to_file('/tmp/paramiko.log')
                transport = paramiko.Transport(ServerConfiguration_obj[0].host, ServerConfiguration_obj[0].port)
                # Auth
                transport.connect(username=ServerConfiguration_obj[0].user_name, password=ServerConfiguration_obj[0].password)
                # Go!
                sftp = paramiko.SFTPClient.from_transport(transport)
                
                # copy this demo onto the server
                try:
                    sftp.mkdir(path)
                except IOError:
                    print("(assuming path already exists)")
                with sftp.open(path + "/" + self.get_file_name(), 'w') as f:
                    f.write(self.file_compute.decode('base64'))
                self.database_file = False

                sftp.close()
                transport.close()
            else:

                if system_parameter_obj and self.model:
                    path = system_parameter_obj[0].value + "/" + self.model.replace('.', '_')
                    if not os.path.exists(path):
                        os.makedirs(path)
                    open(path + "/" + self.get_file_name(), 'w').write(self.file_compute.decode('base64'))

                    self.database_file = False

                else:
                    self.database_file = True
                    self.file = self.file_compute

        else:
            self.database_file = True
            self.file = self.file_compute

    #@api.multi
    def _get_computed_file(self):
        system_parameter_obj = self.env['ir.config_parameter'].search([('key', '=', 'ir_attachment.location')])
        use_server_to_transfer_file = self.env['ir.config_parameter'].search(
            [('key', '=', 'use_server_to_transfer_file')])
        ServerConfiguration_obj = self.env['sever.configuration'].search([])
        for record in self:
            if system_parameter_obj:
                if ServerConfiguration_obj and use_server_to_transfer_file:
                    path = system_parameter_obj[0].value + "/" + record.model.replace('.', '_') + "/" + self.get_file_name()
                    # Open a transport
                    import paramiko
                    paramiko.util.log_to_file('/tmp/paramiko.log')
                    transport = paramiko.Transport(ServerConfiguration_obj[0].host, ServerConfiguration_obj[0].port)
                    # Auth
                    transport.connect(username=ServerConfiguration_obj[0].user_name,
                                      password=ServerConfiguration_obj[0].password)
                    # Go!
                    sftp = paramiko.SFTPClient.from_transport(transport)

                    # copy this demo onto the server
                    try:
                        sftp.mkdir(path)
                    except IOError:
                        print("(assuming path already exists)")
                    with sftp.open(path, 'r') as f:
                        record.file_compute = f.read().encode('base64')

                    sftp.close()
                    transport.close()
                else:
                    if system_parameter_obj and record.model:
                        path = system_parameter_obj[0].value + "/" + record.model.replace('.', '_') + "/" + self.get_file_name()
                        if os.path.exists(path):
                            print(os.path.exists(path))
                            record.file_compute = open(path, 'r').read().encode('base64')


                    else:
                        record.file_compute = record.file

            else:
                record.file_compute = record.file

    @api.model
    def create(self, vals):
        system_parameter_obj = self.env['ir.config_parameter'].search([('key', '=', 'ir_attachment.location')])
        if system_parameter_obj:
            vals['attachment_location_paramter'] = system_parameter_obj[0].value
        return super(attachment_file_save, self).create(vals)

    #@api.multi
    def unlink(self):
        for record in self:
            if record.database_file == False:
                if record.attachment_location_paramter:
                    path = record.attachment_location_paramter + "/" + self.model.replace('.', '_') + "/" + self.get_file_name()
                    if os.path.exists(path):
                        os.remove(path)
        return super(attachment_file_save, self).unlink()
