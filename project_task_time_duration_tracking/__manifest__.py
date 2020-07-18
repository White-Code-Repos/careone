# -*- coding: utf-8 -*-

{
    'name': 'Project Task Time Duration Tracking',
    'summary': """Project Task Time Duration Tracking""",
    'version': '13.0.0.0.1',
    'category': 'Project',
    'depends': ['project'],
    'description': """ Project Task Time Duration Tracking """,
    'data': [
        'security/ir.model.access.csv',
        'views/project_task_view.xml',
        'report/task_time_tracking_report_view.xml',
    ],
    'installable': True,
    'auto_install': False
}
