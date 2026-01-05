from odoo import models, fields, api, _
from datetime import datetime, timedelta


class LibraryReportWizard(models.TransientModel):
    _name = 'library.report.wizard'
    _description = 'Library Report Wizard'

    report_type = fields.Selection([
        ('borrowing_activity', 'Borrowing Activity'),
        ('book_popularity', 'Book Popularity'),
        ('member_activity', 'Member Activity'),
        ('overdue_books', 'Overdue Books'),
    ], string='Report Type', required=True, default='borrowing_activity')

    date_from = fields.Date(string='From Date')
    date_to = fields.Date(string='To Date', default=fields.Date.today)
    group_by = fields.Selection([
        ('day', 'Daily'),
        ('week', 'Weekly'),
        ('month', 'Monthly'),
        ('year', 'Yearly'),
    ], string='Group By')

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        # Set default date range (last 30 days)
        if 'date_from' in fields:
            res['date_from'] = fields.Date.today() - timedelta(days=30)
        return res

    def action_generate_report(self):
        """Generate report based on selected criteria"""
        self.ensure_one()

        report_action = {
            'borrowing_activity': self._generate_borrowing_activity_report,
            'book_popularity': self._generate_book_popularity_report,
            'member_activity': self._generate_member_activity_report,
            'overdue_books': self._generate_overdue_books_report,
        }

        return report_action[self.report_type]()

    def _generate_borrowing_activity_report(self):
        """Generate borrowing activity report"""
        domain = []
        if self.date_from:
            domain.append(('borrow_date', '>=', self.date_from))
        if self.date_to:
            domain.append(('borrow_date', '<=', self.date_to))

        return {
            'type': 'ir.actions.act_window',
            'name': _('Borrowing Activity Report'),
            'res_model': 'library.borrowing',
            'view_mode': 'tree,pivot,graph',
            'domain': domain,
            'context': {
                'group_by': ['borrow_date:' + self.group_by] if self.group_by else [],
                'search_default_group_by_borrow_date': 1,
            }
        }

    def _generate_book_popularity_report(self):
        """Generate book popularity report"""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Book Popularity Report'),
            'res_model': 'library.book',
            'view_mode': 'tree,pivot,graph',
            'context': {
                'search_default_top_borrowed': 1,
            }
        }

    def _generate_member_activity_report(self):
        """Generate member activity report"""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Member Activity Report'),
            'res_model': 'library.member',
            'view_mode': 'tree,pivot,graph',
            'context': {
                'search_default_most_active': 1,
            }
        }

    def _generate_overdue_books_report(self):
        """Generate overdue books report"""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Overdue Books Report'),
            'res_model': 'library.borrowing',
            'view_mode': 'tree,form',
            'domain': [('returned', '=', False), ('due_date', '<', fields.Date.today())],
            'context': {'search_default_overdue': 1}
        }