from odoo import models, fields, api, tools, _

class LibraryDashboard(models.Model):
    _name = 'library.dashboard'
    _description = 'Library Dashboard'
    _auto = False

    total_books = fields.Integer(string='Total Books')
    available_books = fields.Integer(string='Available Books')
    borrowed_books = fields.Integer(string='Borrowed Books')
    total_members = fields.Integer(string='Total Members')
    active_borrowings = fields.Integer(string='Active Borrowings')
    overdue_borrowings = fields.Integer(string='Overdue Borrowings')

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW library_dashboard AS (
                SELECT 
                    row_number() OVER () as id,
                    (SELECT COUNT(*) FROM library_book) as total_books,
                    (SELECT COUNT(*) FROM library_book WHERE status = 'available') as available_books,
                    (SELECT COUNT(*) FROM library_book WHERE status = 'checked_out') as borrowed_books,
                    (SELECT COUNT(*) FROM library_member) as total_members,
                    (SELECT COUNT(*) FROM library_borrowing WHERE returned = false) as active_borrowings,
                    (SELECT COUNT(*) FROM library_borrowing WHERE returned = false AND due_date < CURRENT_DATE) as overdue_borrowings
            )
        """)

    def action_open_books(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Books'),
            'res_model': 'library.book',
            'view_mode': 'tree,form,kanban',
        }

    def action_open_members(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Members'),
            'res_model': 'library.member',
            'view_mode': 'tree,form',
        }

    def action_open_borrowings(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Borrowings'),
            'res_model': 'library.borrowing',
            'view_mode': 'tree,form',
        }

    def refresh_dashboard(self):
        """Refresh the dashboard by reloading the SQL view data"""
        self.env.cr.execute("REFRESH MATERIALIZED VIEW IF EXISTS library_dashboard")
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }