# -*- coding: utf-8 -*-
{
	'name': 'Import Chart of Accounts from CSV or Excel File',	
	'summary': 'This apps helps to import chart of accounts using CSV or Excel file',
	'description': '''Using this module Charts os accounts is imported using excel sheets
	import accounts using csv 
	import accounts using xls
	import accounts using excel
	import Chart of account using csv 
	import Chart of account using xls
	import chart of accounts using excel
	import COA using csv 
	import COA using xls
	import COA using excel
	''',
	'author': 'BrowseInfo',	
	'website': 'https://www.browseinfo.in',
	'category': 'Accounting',
	'version': '13.0.0.3',
	'depends': ['base','account'],	
	'data': [
		'security/ir.model.access.csv',
		'wizard/view_import_chart.xml',
		],

	'installable': True,
	'live_test_url'	:'https://youtu.be/ONRtviwfs1s',
    'application': True,
    'qweb': [
    		],
    "images":['static/description/Banner.png']
}

