from marshmallow import fields, Schema, EXCLUDE, validates_schema, ValidationError


class AddHousehold(Schema):
    class Meta:
        unknown = EXCLUDE

    name = fields.String(required=True, validate=lambda a: bool(a and a.strip() and len(a) <= 128))
    photo = fields.String(allow_none=True)
    language = fields.String(allow_none=True)
    planner_feature = fields.Boolean(allow_none=True)
    expenses_feature = fields.Boolean(allow_none=True)
    view_ordering = fields.List(fields.String(), allow_none=True)
    member = fields.List(fields.Integer(validate=lambda a: a > 0), required=True)

    @validates_schema
    def validate_member_list(self, data, **kwargs):
        if not data.get('member'):
            raise ValidationError('At least one member must be specified')
        if not data.get('name') or not data['name'].strip():
            raise ValidationError('Household name cannot be empty')


class UpdateHousehold(Schema):
    class Meta:
        unknown = EXCLUDE

    name = fields.String(validate=lambda a: a and not a.isspace())
    photo = fields.String()
    language = fields.String()
    planner_feature = fields.Boolean()
    expenses_feature = fields.Boolean()
    view_ordering = fields.List(fields.String)


class UpdateHouseholdMember(Schema):
    class Meta:
        unknown = EXCLUDE

    admin = fields.Boolean()
