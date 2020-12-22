import re
import os
import base64
import pytz
import zipfile
import calendar

from io import BytesIO
from dateutil.relativedelta import relativedelta
from requests import get
from datetime import timedelta

from odoo import models, fields, _
from odoo.exceptions import UserError, ValidationError

from ..controllers.my_ip import MY_IP_ROUTE


class TOBase(models.AbstractModel):
    _name = 'to.base'
    _description = 'TVTMA Base Model'

    def barcode_exists(self, barcode, model_name=None, barcode_field='barcode', inactive_rec=True):
        """
        Method to check if the barcode exists in the input model

        @param barcode: the barcode to check its existance in the model
        @param model_name: The technical name of the model to check. For example, product.template, product.product, etc. If not passed, the current model will be used
        @param barcode_field: the name of the field storing barcode in the corresponding model
        @param inactive_rec: search both active and inactive records of the model for barcode existance check. Please pass False for this arg if the model does not have active field

        @return: Boolean
        """
        Object = model_name and self.env[model_name] or self
        domain = [(barcode_field, '=', barcode)]
        if inactive_rec:
            found = Object.with_context(active_test=False).search(domain)
        else:
            found = Object.search(domain)
        if found:
            return True
        return False

    def get_ean13(self, base_number):
        if len(str(base_number)) > 12:
            raise UserError(_("Invalid input base number for EAN13 code"))
        # weight number
        ODD_WEIGHT = 1
        EVEN_WEIGHT = 3
        # Build a 12 digits base_number_str by adding 0 for missing first characters
        base_number_str = '%s%s' % ('0' * (12 - len(str(base_number))), str(base_number))
        # sum_value
        sum_value = 0
        for i in range(0, 12):
            if i % 2 == 0:
                sum_value += int(base_number_str[i]) * ODD_WEIGHT
            else:
                sum_value += int(base_number_str[i]) * EVEN_WEIGHT
        # calculate the last digit
        sum_last_digit = sum_value % 10
        calculated_digit = 0
        if sum_last_digit != 0:
            calculated_digit = 10 - sum_last_digit
        barcode = base_number_str + str(calculated_digit)
        return barcode

    def convert_time_to_utc(self, dt, tz_name=None, is_dst=None):
        """
        :param dt: datetime obj to convert to UTC
        :param tz_name: the name of the timezone to convert. In case of no tz_name passed, this method will try to find the timezone in context or the login user record
        :param is_dst: respecting daylight saving time or not

        :return: an instance of datetime object
        """
        tz_name = tz_name or self._context.get('tz') or self.env.user.tz
        if not tz_name:
            raise ValidationError(_("Local time zone is not defined. You may need to set a time zone in your user's Preferences."))
        local = pytz.timezone(tz_name)
        local_dt = local.localize(dt, is_dst=is_dst)
        return local_dt.astimezone(pytz.utc)

    def convert_utc_time_to_tz(self, utc_dt, tz_name=None, is_dst=None):
        """
        Method to convert UTC time to local time
        :param utc_dt: datetime in UTC
        :param tz_name: the name of the timezone to convert. In case of no tz_name passed, this method will try to find the timezone in context or the login user record
        :param is_dst: respecting daylight saving time or not
        
        :return: datetime object presents local time
        """
        tz_name = tz_name or self._context.get('tz') or self.env.user.tz
        if not tz_name:
            raise ValidationError(_("Local time zone is not defined. You may need to set a time zone in your user's Preferences."))
        tz = pytz.timezone(tz_name)
        return pytz.utc.localize(utc_dt, is_dst=is_dst).astimezone(tz)

    def time_to_float_hour(self, dt):
        """
        This method will convert a datetime object to a float that present the corresponding time without date. For example,
            datetime.datetime(2019, 3, 24, 12, 44, 0, 307664) will become 12.733418795555554
        @param dt: datetime object
        @param type: datetime
        
        @return: The extracted time in float. For example, 12.733418795555554 for datetime.time(12, 44, 0, 307664)
        @rtype: float
        """
        return dt.hour + dt.minute / 60.0 + dt.second / (60.0 * 60.0) + dt.microsecond / (60.0 * 60.0 * 1000000.0)

    def _find_last_date_of_period_from_period_start_date(self, period_name, period_start_date):
        """
        This method finds the last date of the given period defined by the period_name and the start date of the period. For example:
        - if you pass 'monthly' as the period_name, date('2018-05-20') as the period_start_date, the result will be date('2018-02-20')
        - if you pass 'quarterly' as the period_name, date('2018-05-20') as the date, the result will be date('2018-08-20')
        
        @param period_name: (string) the name of the given period which is either 'weekly' or 'monthly' or 'quarterly' or 'biannually' or 'annually'
        @param period_start_date: (datetime.datetime) the starting date of the period from which the period will be started
        @return: (datetime.datetime) the last date of the period
        @raise ValidationError: when the passed period_name is invalid
        """
        if period_name not in ('weekly', 'monthly', 'quarterly', 'biannually', 'annually'):
            raise ValidationError(_("Wrong value passed to the argument `period_name` of the method `find_last_date_of_period`."
                                    " The value for `period_name` should be either 'weekly' or 'monthly' or 'quarterly' or 'biannually' or 'annually'"))
        if period_name == 'weekly':
            dt = period_start_date + relativedelta(days=6)
        elif period_name == 'monthly':
            dt = period_start_date + relativedelta(months=1) - relativedelta(days=1)
        elif period_name == 'quarterly':
            dt = period_start_date + relativedelta(months=3) - relativedelta(days=1)
        elif period_name == 'biannually':
            dt = period_start_date + relativedelta(months=6) - relativedelta(days=1)
        else:
            dt = period_start_date + relativedelta(years=1) - relativedelta(days=1)
        return dt

    def _validate_period_name(self, period_name):
        msg = ''
        if period_name not in ('weekly', 'monthly', 'quarterly', 'biannually', 'annually'):
            msg = _("Wrong value passed to the argument `period_name` of the method `find_last_date_of_period`."
                    " The value for `period_name` should be either 'weekly' or 'monthly' or 'quarterly' or 'biannually' or 'annually'")
            return False, msg
        else:
            return True, msg

    def find_first_date_of_period(self, period_name, date):
        """
        This method finds the first date of the given period defined by period name and any date of the period
        @param period_name: (string) the name of the given period which is either 'weekly' or 'monthly' or 'quarterly' or 'biannually' or 'annually'
        @param date: (datetime.datetime) any date of the period to find
        @return: (datetime.datetime) the first date of the period
        """
        ret, msg = self._validate_period_name(period_name)
        if not ret:
            raise ValidationError(msg)

        if period_name == 'weekly':
            dt = date - relativedelta(days=date.weekday())
        elif period_name == 'monthly':
            dt = date + relativedelta(day=1)  # force day as 1 while keep year and month unchanged
        elif period_name == 'quarterly':
            if date.month >= 1 and date.month <= 3:
                dt = fields.Date.from_string('%s-%s-%s' % (date.year, 1, 1))
            elif date.month >= 4 and date.month <= 6:
                dt = fields.Date.from_string('%s-%s-%s' % (date.year, 4, 1))
            elif date.month >= 7 and date.month <= 9:
                dt = fields.Date.from_string('%s-%s-%s' % (date.year, 7, 1))
            else:
                dt = fields.Date.from_string('%s-%s-%s' % (date.year, 10, 1))
        elif period_name == 'biannually':
            if date.month <= 6:
                dt = fields.Date.from_string('%s-01-01' % date.year)
            else:
                dt = fields.Date.from_string('%s-07-01' % date.year)
        else:
            dt = fields.Date.from_string('%s-01-01' % date.year)
        return dt

    def find_last_date_of_period(self, period_name, date, date_is_start_date=False):
        """
        This method finds the last date of the given period defined by period name and any date of the period. For example:
        - if you pass 'monthly' as the period_name, date('2018-05-20') as the date, the result will be date('2018-05-31')
        - if you pass 'quarterly' as the period_name, date('2018-05-20') as the date, the result will be date('2018-06-30')
        @param period_name: (string) the name of the given period which is either 'weekly' or 'monthly' or 'quarterly' or 'biannually' or 'annually'
        @param date: (datetime.datetime) either the start date of the given period or any date of the period, depending on the passed value of the arg. date_is_start_date
        @param date_is_start_date: (bool) True to indicate the given date is also the starting date of the given period_name, otherwise, the given date is any of the period's dates
        @return: (datetime.datetime) the last date of the period
        @raise ValidationError: when the passed period_name is invalid
        """
        ret, msg = self._validate_period_name(period_name)
        if not ret:
            raise ValidationError(msg)

        # If the given date is the start date of the period
        if date_is_start_date:
            return self._find_last_date_of_period_from_period_start_date(period_name=period_name, period_start_date=date)

        # else
        if period_name == 'weekly':
            dt = date + relativedelta(days=6 - date.weekday())
        elif period_name == 'monthly':
            days_of_month = self.get_days_of_month_from_date(date)
            dt = fields.Datetime.from_string('%s-%s-%s' % (date.year, date.month, days_of_month))
        elif period_name == 'quarterly':
            if date.month >= 1 and date.month <= 3:
                dt = fields.Datetime.from_string('%s-%s-%s' % (date.year, 3, 31))
            elif date.month >= 4 and date.month <= 6:
                dt = fields.Datetime.from_string('%s-%s-%s' % (date.year, 6, 30))
            elif date.month >= 7 and date.month <= 9:
                dt = fields.Datetime.from_string('%s-%s-%s' % (date.year, 9, 30))
            else:
                dt = fields.Datetime.from_string('%s-%s-%s' % (date.year, 12, 31))
        elif period_name == 'biannually':
            if date.month <= 6:
                dt = fields.Datetime.from_string('%s-%s-%s' % (date.year, 6, 30))
            else:
                dt = fields.Datetime.from_string('%s-12-31' % date.year)
        else:
            dt = fields.Datetime.from_string('%s-12-31' % date.year)
        return dt

    def period_iter(self, period_name, dt_start, dt_end, start_day_offset=0):
        """
        Method to generate sorted dates for periods of the given period_name and dt_start and dt_end
        @param period_name: (string) the name of the given period which is either 'weekly' or 'monthly' or 'quarterly' or 'biannually' or 'annually'
        @param dt_start: (datetime.datetime)
        @param dt_end: (datetime.datetime)
        @param start_day_offset: default value is zero, which means that the start days are always the very first day of the period
        @return: [list] list of datetime objects contain dt_start and end dates of found periods. For example:
                if we pass [datetime.date(2018, 7, 4) and datetime.date(2018, 10, 31) and 0 as the dt_start and the dt_end and the
                start_day_offset correspondingly, the result will be
                    [datetime.date(2018, 7, 4),
                    datetime.date(2018, 7, 31), datetime.date(2018, 8, 31), datetime.date(2018, 9, 30), datetime.date(2018, 10, 31)]
        """
        if not start_day_offset >= 0:
            raise ValidationError(_("The `start_day_offset` passed to the method `period_iter` must be greater than or equal to zero!"))
        res = [dt_start]
        period_start_date = self.find_first_date_of_period(period_name, dt_start) + relativedelta(days=start_day_offset)
        if period_start_date > dt_start:
            res.append(period_start_date - relativedelta(days=1))

        while period_start_date <= dt_end:
            last_dt = self._find_last_date_of_period_from_period_start_date(period_name=period_name, period_start_date=period_start_date)
            if last_dt > dt_end:
                last_dt = dt_end
            res.append(last_dt)
            period_start_date = last_dt + relativedelta(days=1)

        res.sort()
#         print(res)
        return res

    def get_days_of_month_from_date(self, dt):
        return calendar.monthrange(dt.year, dt.month)[1]

    def get_day_of_year_from_date(self, date):
        """
        Return the day of year from date. For example, 2018-01-06 will return 6
        """
        first_date = fields.Date.from_string('%-01-01' % date.year)
        day = self.get_days_between_dates(first_date, date) + 1
        return day

    def get_days_between_dates(self, dt_from, dt_to):
        """
        Return number of days between two dates
        """
        return (dt_to - dt_from).days

    def get_weekdays_for_period(self, dt_from, dt_to):
        """
        Method to return the a dictionary in form of {int0:date, wd1:date, ...} where int0/int1
            are integer 0~6 presenting weekdays and date1/date2 are dates that are the correspong weekdays
        @param dt_from: datetime.datetime|datetime.date
        @param dt_to: datetime.datetime|datetime.date
        @return: dict{int0:date, wd1:date, ...}
        """
        nb_of_days = self.get_days_between_dates(dt_from, dt_to) + 1
        if nb_of_days > 7:
            raise ValidationError(_("The method get_weekdays_for_period(dt_from, dt_to) does not support the periods having more than 7 days"))
        weekdays = {}
        for day in range(0, nb_of_days):
            day_rec = dt_from + timedelta(days=day)
            weekdays[day_rec.weekday()] = day_rec.date()
        return weekdays

    def next_weekday(self, date, weekday=None):
        """
        Method to get the date in the nex tweek of the given `date`'s week with weekday is equal to the given `weekday`. For example,
        - date: 2018-10-18 (Thursday)
        - weekday:
            0: will return 2018-10-22 (Monday next week)
            1: will return 2018-10-23 (Tuesday next week)
            2: will return 2018-10-24 (Wednesday next week)
            3: will return 2018-10-25 (Thursday next week)
            4: will return 2018-10-26 (Friday next week)
            5: will return 2018-10-27 (Saturday next week)
            6: will return 2018-10-28 (Sunday next week)
            None: will return 2018-10-25 (the same week day next week)        
        @param date: (datetime.datetime or datetime.date) the given date to find the date next week
        @param weekday: week day of the next week which is an integer from 0 to 6 presenting a day of week, or None to find the date of the same week day next week

        @return: date of the same weekday next week
        """
        # if weekday is None, set it as the same as the weekday of the given date
        if weekday is None:
            weekday = date.weekday()

        days_ahead = weekday - date.weekday()
        if days_ahead <= 0:  # Target day already happened this week
            days_ahead += 7
        return date + timedelta(days_ahead)

    def split_date(self, date):
        """
        Method to split a date into year,month,day separatedly
        @param date date:
        """
        year = date.year
        month = date.month
        day = date.day
        return year, month, day

    def hours_time_string(self, hours):
        """ convert a number of hours (float) into a string with format '%H:%M' """
        minutes = int(round(hours * 60))
        return "%02d:%02d" % divmod(minutes, 60)

    def _zip_dir(self, path, zf, incl_dir=False):
        """
        @param path: the path to the directory to zip
        @param zf: the ZipFile object which is an instance of zipfile.ZipFile
        @type zf: ZipFile
        
        @return: zipfile.ZipFile object that contain all the content of the path
        """
        path = os.path.normpath(path)

        dlen = len(path)
        if incl_dir:
            dir_name = os.path.split(path)[1]
            minus = len(dir_name) + 1
            dlen -= minus
        for root, dirs, files in os.walk(path):
            for name in files:
                full = os.path.join(root, name)
                rel = root[dlen:]
                dest = os.path.join(rel, name)
                zf.write(full, dest)
        return zf

    def zip_dir(self, path, incl_dir=False):
        """
        zip a directory tree into a bytes object which is ready for storing in Binary field

        @param path: the absolute path to the directory to zip
        @type path: string
        
        @return: return bytes object containing data for storing in Binary fields
        @rtype: bytes
        """
        # initiate A BytesIO object
        file_data = BytesIO()

        # open file_data as ZipFile with write mode
        with zipfile.ZipFile(file_data, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            self._zip_dir(path, zf, incl_dir=incl_dir)

        # Change the stream position to the start of the stream
        # see https://docs.python.org/3/library/io.html#io.IOBase.seek
        file_data.seek(0)
        # read bytes to the EOF
        file_data_read = file_data.read()
        # encode bytes for output to return
        out = base64.encodebytes(file_data_read)
        return out

    def zip_dirs(self, paths):
        """
        zip a tree of directories (defined by paths) into a bytes object which is ready for storing in Binary field

        @param paths: list of absolute paths (string) to the directories to zip
        @type paths: list
        
        @return: return bytes object containing data for storing in Binary fields
        @rtype: bytes
        """
        # initiate A BytesIO object
        file_data = BytesIO()

        # open file_data as ZipFile with write mode
        with zipfile.ZipFile(file_data, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for path in paths:
                self._zip_dir(path, zf, incl_dir=True)

        # Change the stream position to the start of the stream
        # see https://docs.python.org/3/library/io.html#io.IOBase.seek
        file_data.seek(0)
        # read bytes to the EOF
        file_data_read = file_data.read()
        # encode bytes for output to return
        out = base64.encodebytes(file_data_read)
        return out

    def guess_lang(self, sample):
        """
        This method is for others to implement.
        """
        raise NotImplementedError(_("the method guess_lang has not been implemented yet"))

    def no_accent_vietnamese(self, s):
        """
        Convert Vietnamese unicode string from 'Tiếng Việt có dấu' thanh 'Tieng Viet khong dau'
        :param s: text: input string to be converted
        :return : string converted
        """
    #     s = s.decode('utf-8')
        s = re.sub(u'[àáạảãâầấậẩẫăằắặẳẵ]', 'a', s)
        s = re.sub(u'[ÀÁẠẢÃĂẰẮẶẲẴÂẦẤẬẨẪ]', 'A', s)
        s = re.sub(u'[èéẹẻẽêềếệểễ]', 'e', s)
        s = re.sub(u'[ÈÉẸẺẼÊỀẾỆỂỄ]', 'E', s)
        s = re.sub(u'[òóọỏõôồốộổỗơờớợởỡ]', 'o', s)
        s = re.sub(u'[ÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠ]', 'O', s)
        s = re.sub(u'[ìíịỉĩ]', 'i', s)
        s = re.sub(u'[ÌÍỊỈĨ]', 'I', s)
        s = re.sub(u'[ùúụủũưừứựửữ]', 'u', s)
        s = re.sub(u'[ƯỪỨỰỬỮÙÚỤỦŨ]', 'U', s)
        s = re.sub(u'[ỳýỵỷỹ]', 'y', s)
        s = re.sub(u'[ỲÝỴỶỸ]', 'Y', s)
        s = re.sub(u'[Đ]', 'D', s)
        s = re.sub(u'[đ]', 'd', s)
        return s

    def sum_digits(self, n, number_of_digit_return=None):
        """
        This will sum all digits of the given number until the result has x digits where x is number_of_digit_return
        @param n: the given number for sum of its digits
        @type n: int|float
        @param number_of_digit_return: the number of digist in the return result.
            For example, if n=178 and number_of_digit_return=2, the result will be 16. However, if number_of_digit_return <= 1, the result will be 7 (=1+6 again)
            
        @return: the sum of all the digits until the result has `number_of_digit_return` digits
        @rtype: int
        """
        s = 0
        for d in str(n):
            if d.isdigit():
                s += int(d)

        str_len = len(str(s))
        if isinstance(number_of_digit_return, int) and str_len > number_of_digit_return and str_len > 1 :
            return self.sum_digits(s)
        return s

    def find_nearest_lucky_number(self, n, rounding=0, round_up=False):
        """
        9 is lucky number
        This will find the nearest integer if the given number that have digits sum = 9 (sum digits until 1 digit is returned)
        @param n: the given number for finding its nearest lucky number
        @type n: int|float
        @param rounding: the number of digist for rounding
            For example, if n=178999 and rounding=2, the result will be 178900. However, if rounding = 4, the result will be 170000
            
        @return: the lucky number
        @rtype: int
        """
        if rounding < 0:
            rounding = 0
        # replace last x digits with zero by rounding up/down, where x is the given round_digits
        n = round(n, rounding) if round_up else round(n, -rounding)
        # calculate adjusting step
        step = 1
        for x in range(rounding):
            step = step * 10

        while self.sum_digits(n, 1) != 9:
            if isinstance(n, int):
                if round_up:
                    n += step
                else:
                    n -= step
            else:
                n = round(n)
        return n

    def get_host_ip(self):
        """
        This method return the IP of the host where the Odoo instance is running.
        """
        url = self.env['ir.config_parameter'].sudo().get_param('web.base.url') + MY_IP_ROUTE
        respond = get(url)
        return respond.text

