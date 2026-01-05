from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import timedelta

class MassOperationWizard(models.TransientModel):
    _name = 'library.mass.operation.wizard'
    _description = 'Mass Operation Wizard'

    operation_type = fields.Selection([
        ('change_status', 'Change Book Status'),
        ('update_rating', 'Update Book Rating'),
        ('send_reminder', 'Send Due Date Reminder'),
    ], string='Operation Type', required=True)

    new_status = fields.Selection([
        ('available', 'Available'),
        ('checked_out', 'Checked Out'),
        ('maintenance', 'Under Maintenance'),
    ], string='New Status')

    new_rating = fields.Selection([
        ('1', '★☆☆☆☆'),
        ('2', '★★☆☆☆'),
        ('3', '★★★☆☆'),
        ('4', '★★★★☆'),
        ('5', '★★★★★'),
    ], string='New Rating')

    reminder_type = fields.Selection([
        ('due_today', 'Due Today'),
        ('due_soon', 'Due in 3 Days'),
        ('overdue', 'Overdue'),
    ], string='Reminder Type')

    book_ids = fields.Many2many('library.book', string='Books')
    member_ids = fields.Many2many('library.member', string='Members')

    def action_execute_operation(self):
        """Execute the selected mass operation"""
        self.ensure_one()

        operations = {
            'change_status': self._execute_change_status,
            'update_rating': self._execute_update_rating,
            'send_reminder': self._execute_send_reminder,
        }

        return operations[self.operation_type]()

    def _execute_change_status(self):
        """Change status for selected books"""
        if not self.new_status:
            raise ValidationError(_("Please select a new status."))

        if self.book_ids:
            self.book_ids.write({'status': self.new_status})
            message = _("Status updated for %s books") % len(self.book_ids)
        else:
            message = _("No books selected")

        return self._show_success_message(message)

    def _execute_update_rating(self):
        """Update rating for selected books"""
        if not self.new_rating:
            raise ValidationError(_("Please select a new rating."))

        if self.book_ids:
            self.book_ids.write({'rating': self.new_rating})
            message = _("Rating updated for %s books") % len(self.book_ids)
        else:
            message = _("No books selected")

        return self._show_success_message(message)

    def _execute_send_reminder(self):
        """Send due date reminders"""
        today = fields.Date.today()
        domain = [('returned', '=', False)]

        if self.reminder_type == 'due_today':
            domain.append(('due_date', '=', today))
        elif self.reminder_type == 'due_soon':
            domain.append(('due_date', '<=', today + timedelta(days=3)))
            domain.append(('due_date', '>=', today))
        elif self.reminder_type == 'overdue':
            domain.append(('due_date', '<', today))

        borrowings = self.env['library.borrowing'].search(domain)

        # In a real scenario, you would send emails here
        message = _("Reminders prepared for %s borrowings") % len(borrowings)

        return self._show_success_message(message)

    def _show_success_message(self, message):
        """Show success message and close wizard"""
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': message,
                'type': 'success',
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }