# -*- coding: utf-8 -*-

{
    'name': 'Project Task Time Duration Tracking',
    'version': '13.0.1.0.0',
    'summary': """Project Task Time Duration Tracking""",
    'category': 'Project',
    'depends': ['project'],
    'URL':"https://system.white-code.co.uk/web?#id=2113&action=395&model=project.task&view_type=form&menu_id=263",
    'description': """ Project Task Time Duration Tracking """,
    'data': [
        'security/ir.model.access.csv',
        'views/project_task_view.xml',
        'report/task_time_tracking_report_view.xml',
    ],
    'author': 'White-code',
    'installable': True,
    'auto_install': False
}
