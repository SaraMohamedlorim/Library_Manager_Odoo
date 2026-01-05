from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import timedelta

class LibraryMember(models.Model):
    _name = 'library.member'
    _description = 'Library Member'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Full Name', required=True, tracking=True)
    email = fields.Char(string='Email', tracking=True)
    phone = fields.Char(string='Phone', tracking=True)
    created_date = fields.Date(string='Created Date', default=fields.Date.today)

    # Relations
    borrowing_ids = fields.One2many('library.borrowing', 'member_id', string='Borrowings')

    # Computed fields
    active_borrowings_count = fields.Integer(string='Active Borrowings', compute='_compute_active_borrowings')
    total_borrowings_count = fields.Integer(string='Total Borrowings', compute='_compute_total_borrowings')
    user_id = fields.Many2one('res.users', string="Related User", required=True)

     # الربط مع الـ Expense Tracker
    budget_id = fields.Many2one('expense.budget', string='Expense Budget', ondelete='set null')
    
    @api.model
    def create(self, vals):
        # إنشاء العضو
        member = super(LibraryMember, self).create(vals)

            # البحث عن أول category متاحة أو إنشاء واحدة
        category = self.env['expense.category'].search([], limit=1)
        if not category:
            category = self.env['expense.category'].create({
                'name': 'Books',
                'code': 'BOOKS'
            })
        
        # إنشاء budget جديد في expense tracker لهذا العضو
        budget = self.env['expense.budget'].create({
        'name': 'Book Budget - {}'.format(member.name),
        'category_id': category.id,
        'amount': 500.0,
        'period_type': 'monthly',
        'date_from': fields.Date.today(),
        'date_to': fields.Date.today() + timedelta(days=30),
        'state': 'active',
        })

        member.budget_id = budget.id
        return member

    @api.depends('borrowing_ids.returned')
    def _compute_active_borrowings(self):
        for member in self:
            member.active_borrowings_count = self.env['library.borrowing'].search_count([
                ('member_id', '=', member.id),
                ('returned', '=', False)
            ])

    @api.depends('borrowing_ids')
    def _compute_total_borrowings(self):
        for member in self:
            member.total_borrowings_count = len(member.borrowing_ids)

    @api.depends('borrowing_ids')
    def _compute_borrowings_count(self):
        for rec in self:
            rec.active_borrowings_count = len(rec.borrowing_ids.filtered(lambda b: not b.returned))
            rec.total_borrowings_count = len(rec.borrowing_ids)

    def action_view_borrowings(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Borrowings - {}'.format(self.name),
            'res_model': 'library.borrowing',
            'domain': [('member_id', '=', self.id)],
            'view_mode': 'tree,form',
            'context': {'default_member_id': self.id}
        }