{
    'name': "Biometric Attendance Device",
    'name_vi_VN': "Tích hợp Máy chấm công Sinh trắc học",

    'summary': """
Integrate all kinds of ZKTeco based attendance devices with Odoo""",
    'summary_vi_VN': """
Tích hợp tất cả các loại máy chấm công nền tảng ZKTeco với Odoo""",

    'description': """
Key Features
============

* Support both UDP and TCP for large attendance data (tested with a real machine that store more than 90 thousand attendance records)
* Support connection with either domain name or IP
* Authenticate devices with password.
* Multiple Devices for multiple locations
* Multiple device time zones at multiple locations
* Multiple Attendance Status support (e.g. Check-in, Check-out, Start Overtime, End Overtime, etc)
* Store fingerprint templates in employee profiles to quickly set up new device (Added since version 1.1.0)
* Delete Device's Users from Odoo
* Upload new users into the devices from Odoo's Employee database
* Auto Map Device Users with Odoo employee base on Badge ID mapping, or name search mapping if no Badge ID match found
* Store Device Attendance data permanently
* Manual/Automatic download attendance data from all your devices into Odoo (using scheduled actions)
* Manual/Automatic synchronize device attendance data with HR Attendance so that you can access them in your salary rules for payslip computation
* Automatically Clear Attendance Data from the Device periodically, which is configurable.
* Designed to work with all attendance devices that based on ZKTeco platform.

    * Fully TESTED with the following devices:
    
      * RONALD JACK B3-C
      * ZKTeco K50
      * ZKTeco MA300
      * ZKTeco U580
      * ZKTeco T4C
      * ZKTeco G3
      * RONALD JACK iClock260
    
    * Reported by clients that the module has worked great with the following devices

      * ZKTeco K40
      * ZKTeco U580
      * iFace402/ID
      * ZKTeco MB20
      * ZKteco IN0A-1
      * Uface 800
      * ... (please advise us your devices. Tks!)

Credit
======
Tons of thanks to fananimi for his pyzk library @ https://github.com/fananimi/pyzk

We got inspired from that and customize it for more features (device information, Python 3 support,
TCP/IP support, etc) then we integrated into Odoo by this great Attendance Device application

Editions Supported
==================
1. Community Edition
2. Enterprise Edition

    """,
      'description_vi_VN': """
Tính năng
=========

* Hỗ trợ cả UDP và TCP cho lượng dữ liệu điểm danh lớn (được thử nghiệm với lưu trữ hơn 90 nghìn dữ liệu điểm danh cho một máy chấm công)
* Hỗ trợ kết nối bằng IP hoặc tên miền thiết bị
* Xác thực kết nối thiết bị bằng mật khẩu.
* Nhiều thiết bị cho nhiều địa điểm điểm danh.
* Có thể sử dụng thiết bị với nhiều múi giờ tại nhiều địa điểm
* Hỗ trợ nhiều trạng thái điểm danh (ví dụ: Check-in, Check-out, Bắt đầu thêm giờ, kết thúc thêm giờ, etc, v.v.)
* Xóa dữ liệu chấm công từ Odoo
* Nhập dữ liệu người dùng mới từ dữ liệu nhân viên trong Odoo.
* Có thể khớp dữ liệu người dùng với hồ sơ nhân viên trong Odoo bằng cách ánh xạ ID điểm dnah hoặc tìm kiếm theo tên nếu không thấy kết của ID phù hợp.
* Lưu dữ liệu trên máy chấm công vĩnh viễn.
* Dữ liệu điểm danh có thể tải tự động hoặc thủ công từ tất cả các máy vào Odoo (sử dụng hành động định kỳ)
* Đồng bộ hóa dữ liệu điểm danh trên thiết bị và module điểm danh trên phần mềm tự động hoặc thủ công để có thể lấy dữ liệu đưa vào tính tón tại các quy tắc lương trên phiếu lương của nhân viên.
* Tự động xóa dữ liệu trên thiết bị theo định kỳ được cài đặt trước.
* Được thiết kế để hoạt động với tất cả các thiết bị chấm công với nền tảng ZKTeco. Đã được KIỂM THỬ đầy đủ với các thiết bị sau:
    * RONALD JACK B3-C
    * ZKTeco K50
    * ZKTeco MA300
    * ZKTeco U580
    * ZKTeco T4C
    * RONALD JACK iClock260

Credit
======
Xin gửi lời cảm ơn chân thành đến fananimi vì thư viện pyzk của anh ấy @ https://github.com/fananimi/pyzk

Chúng tôi đã lấy ý tưởng từ đó và tùy chỉnh để có nhiều tính năng hơn (thông tin thiết bị, hỗ trợ Python 3,
Hỗ trợ TCP / IP, v.v.) sau đó chúng tôi tích hợp vào Odoo bằng ứng dụng máy chấm công tuyệt vời này

Phiên bản hỗ trợ
================
1. Community Edition
2. Enterprise Edition

    """,

    'author': "T.V.T Marine Automation (aka TVTMA)",
    'website': 'https://www.tvtmarine.com',
    'live_test_url': 'https://v12demo-int.erponline.vn',
    'support': 'support@ma.tvtmarine.com',

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Human Resources',
    'version': '1.1.1',

    # any module necessary for this one to work correctly
    'depends': ['hr_attendance', 'to_base', 'to_safe_confirm_button'],

    # always loaded
    'data': [
        'data/scheduler_data.xml',
        'data/attendance_state_data.xml',
        'data/mail_template_data.xml',
        'security/module_security.xml',
        'security/ir.model.access.csv',
        'views/menu_view.xml',
        'views/attendance_device_views.xml',
        'views/attendance_state_views.xml',
        'views/device_user_views.xml',
        'views/hr_attendance_views.xml',
        'views/hr_employee_views.xml',
        'views/user_attendance_views.xml',
        'views/attendance_activity_views.xml',
        'views/finger_template_views.xml',
        'wizard/attendance_wizard.xml',
        'wizard/employee_upload_wizard.xml',

    ],
    'images' : ['static/description/main_screenshot.png'],
    'installable': True,
    'application': True,
    'auto_install': False,
    'price': 198.9,
    'currency': 'EUR',
    'license': 'OPL-1',
}
