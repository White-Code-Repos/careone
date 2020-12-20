{
    "name" : "ZK Biometric Device Integration Kware (ZKTECO) Demo (UDP)",
    "version" : "1.0",
    "author" : "JUVENTUD PRODUCTIVA VENEZOLANA",
    "category" : "HR",
    "website" : "https://www.youtube.com/channel/UCTj66IUz5M-QV15Mtbx_7yg",
    "description": "Module for the connection between odoo and zkteco devices for the control of employee assistance. This module is a demo version to test the compatibility of your device with our module.d Odoo.",
    'license': 'AGPL-3',
    "depends" : ["base","hr","hr_attendance"],
    "data" : [
				"views/biometric_machine_view.xml",
				"secuirty/res_groups.xml",
				"secuirty/ir.model.access.csv"
			],
	'images': ['static/images/zk_screenshot.jpg'],
    "active": True,
    "installable": True,
}
