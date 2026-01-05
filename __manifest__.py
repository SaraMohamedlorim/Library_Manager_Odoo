{
    'name': 'Library Manager',
    'version': '1.0',
    'license': 'LGPL-3',
    'summary': 'Comprehensive Library Management System',
    'description': """
        Complete Library Management System
        ==================================

        Features:
        • Book Catalog Management
        • Member Management
        • Borrowing & Return System
        • Dashboard with Analytics
        • Reports and Notifications

        This module provides a comprehensive solution for managing libraries.
    """,
    'category': 'Education',
    'author': 'Sara Mohamed',
    'website': 'https://www.Sara.com',
    'depends': ['base', 'web','mail','Advanced_Expense_Tracker',],
    'data': [
        'security/ir.model.access.csv',
        'security/library_security.xml',
        'data/library_data.xml',

        'wizards/quick_borrow_wizard_views.xml',
        'views/books_views.xml',
        'views/members_views.xml',
        'views/borrowing_views.xml',
        'views/borrowing_kanban_views.xml',
        'views/dashboard_views.xml',
        
        'views/library_menus.xml',
        'views/templates.xml',

        
        'wizards/book_borrow_wizard_views.xml',
        'wizards/book_return_wizard_views.xml',
        'wizards/library_report_wizard_views.xml',
        'wizards/mass_operation_wizard_views.xml',

        'reports/book_report.xml',

    ],
    'demo': ['data/library_demo.xml'],
    'images': [
        'static/description/icon.png',
        'static/description/banner.png',
        'static/description/screenshot1.png',
        'static/description/screenshot2.png'
    ],
    'icon': '/Library_Manager/static/description/library.png',
    'assets': {
        'web.assets_backend': [
            'Library_Manager/static/src/js/chart_manager.js',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}