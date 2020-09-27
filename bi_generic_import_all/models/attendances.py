# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

import tempfile
import binascii
import logging
import io
from odoo.tools import ustr
from odoo.exceptions import Warning
from odoo import models, fields, api, exceptions, _
_logger = logging.getLogger(__name__)
try:
    import csv
except ImportError:
    _logger.debug('Cannot `import csv`.')
try:
    import xlwt
except ImportError:
    _logger.debug('Cannot `import xlwt`.')
try:
    import base64
except ImportError:
    _logger.debug('Cannot `import base64`.')
try:
    import xlrd
except ImportError:
    _logger.debug('Cannot `import xlrd`.')


class import_attendance(models.TransientModel):
    _name = "import.attendance"

    file = fields.Binary('File')
    file_opt = fields.Selection([('csv','CSV'),('excel','EXCEL')])

    
    def import_file(self):
        if self.file_opt == 'csv':
            try:
                keys = ['name','check_in','check_out']  
                csv_data = base64.b64decode(self.file)
                data_file = io.StringIO(csv_data.decode("utf-8"))
                data_file.seek(0)
                file_reader = []
                csv_reader = csv.reader(data_file, delimiter=',')
                file_reader.extend(csv_reader)
            except Exception:
                raise exceptions.Warning(_("Please select an CSV/XLS file or You have selected invalid file"))
            values = {}
            for i in range(len(file_reader)):
                field = list(map(str, file_reader[i]))
                values = dict(zip(keys, field))
                if values:
                    if i == 0:
                        continue
                    else:
                        res = self._create_timesheet(values)
        else:
            try:
                fp = tempfile.NamedTemporaryFile(delete= False,suffix=".xlsx")
                fp.write(binascii.a2b_base64(self.file))
                fp.seek(0)
                values = {}
                workbook = xlrd.open_workbook(fp.name)
                sheet = workbook.sheet_by_index(0)
                for row_no in range(sheet.nrows):
                    if row_no <= 0:
                        fields = map(lambda row:row.value.encode('utf-8'), sheet.row(row_no))
                    else:
                        line = list(map(lambda row:isinstance(row.value, bytes) and row.value.encode('utf-8') or str(row.value), sheet.row(row_no)))
                        values.update( {'name':line[0],
                                        'check_in': line[1],
                                        'check_out': line[2],
                                        })
                        res = self._create_timesheet(values)
            except Exception:
                raise exceptions.Warning(_("Please select an CSV/XLS file or You have selected invalid file"))
                        
        return res

    
    def _create_timesheet(self,val):
        emp_id = self._find_employee(val.get('name'))
        if not emp_id:
            raise Warning('Employee Not Found')
        if not val.get('check_in'):
            raise Warning('Please Provide Sign In Time')
        if not val.get('check_out'):
            self._cr.execute("insert into hr_attendance (employee_id,check_in) values (%s,%s)", (emp_id.id, val.get('check_in')))
        else:
            self._cr.execute("insert into hr_attendance (employee_id,check_in,check_out) values (%s,%s,%s)", (emp_id.id, val.get('check_in'), val.get('check_out')))
        return True

    def _find_employee(self,name):
        emp_id = self.env['hr.employee'].search([('name','=',name)])
        if emp_id:
            return emp_id
        else:
            raise Warning(_("Employee '%s' Not Found!") % ustr(name))



