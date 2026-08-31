import typing as t

from marshmallow import Schema, fields
from marshmallow import ValidationError



class InvalidInputError(Exception):
    """Invalid model input."""


SYNTAX_ERROR_FIELD_MAP = {
    '1stFlrSF': 'FirstFlrSF',
    '2ndFlrSF': 'SecondFlrSF',
    '3SsnPorch': 'ThreeSsnPortch'
}


# In the Ames dataset a missing value often *is* the value: "NA" means "no
# garage", "no basement", "no masonry veneer". None of the fields below is a
# model feature, so a null there cannot change a prediction - flagging them
# would reject the shipped Kaggle test set over data that is perfectly valid.
# Nulls in the four fields the model DOES use (MSZoning, KitchenQual,
# BsmtFullBath, GarageCars) stay errors and still fail the request.
class HouseDataRequestSchema(Schema):
    Alley = fields.Str(allow_none=True)
    BedroomAbvGr = fields.Integer()
    BldgType = fields.Str()
    BsmtCond = fields.Str(allow_none=True)
    BsmtExposure = fields.Str(allow_none=True)
    BsmtFinSF1 = fields.Float(allow_none=True)
    BsmtFinSF2 = fields.Float(allow_none=True)
    BsmtFinType1 = fields.Str(allow_none=True)
    BsmtFinType2 = fields.Str(allow_none=True)
    BsmtFullBath = fields.Float()
    BsmtHalfBath = fields.Float(allow_none=True)
    BsmtQual = fields.Str(allow_none=True)
    BsmtUnfSF = fields.Float(allow_none=True)
    CentralAir = fields.Str()
    Condition1 = fields.Str()
    Condition2 = fields.Str()
    Electrical = fields.Str()
    EnclosedPorch = fields.Integer()
    ExterCond = fields.Str()
    ExterQual = fields.Str()
    Exterior1st = fields.Str(allow_none=True)
    Exterior2nd = fields.Str(allow_none=True)
    Fence = fields.Str(allow_none=True)
    FireplaceQu = fields.Str(allow_none=True)
    Fireplaces = fields.Integer()
    Foundation = fields.Str()
    FullBath = fields.Integer()
    Functional = fields.Str(allow_none=True)
    GarageArea = fields.Float(allow_none=True)
    GarageCars = fields.Float()
    GarageCond = fields.Str(allow_none=True)
    GarageFinish = fields.Str(allow_none=True)
    GarageQual = fields.Str(allow_none=True)
    GarageType = fields.Str(allow_none=True)
    GarageYrBlt = fields.Float(allow_none=True)
    GrLivArea = fields.Integer()
    HalfBath = fields.Integer()
    Heating = fields.Str()
    HeatingQC = fields.Str()
    HouseStyle = fields.Str()
    Id = fields.Integer()
    KitchenAbvGr = fields.Integer()
    KitchenQual = fields.Str()
    LandContour = fields.Str()
    LandSlope = fields.Str()
    LotArea = fields.Integer()
    LotConfig = fields.Str()
    LotFrontage = fields.Float(allow_none=True)
    LotShape = fields.Str()
    LowQualFinSF = fields.Integer()
    MSSubClass = fields.Integer()
    MSZoning = fields.Str()
    MasVnrArea = fields.Float(allow_none=True)
    MasVnrType = fields.Str(allow_none=True)
    MiscFeature = fields.Str(allow_none=True)
    MiscVal = fields.Integer()
    MoSold = fields.Integer()
    Neighborhood = fields.Str()
    OpenPorchSF = fields.Integer()
    OverallCond = fields.Integer()
    OverallQual = fields.Integer()
    PavedDrive = fields.Str()
    PoolArea = fields.Integer()
    PoolQC = fields.Str(allow_none=True)
    RoofMatl = fields.Str()
    RoofStyle = fields.Str()
    SaleCondition = fields.Str()
    SaleType = fields.Str(allow_none=True)
    ScreenPorch = fields.Integer()
    Street = fields.Str()
    TotRmsAbvGrd = fields.Integer()
    TotalBsmtSF = fields.Float(allow_none=True)
    Utilities = fields.Str(allow_none=True)
    WoodDeckSF = fields.Integer()
    YearBuilt = fields.Integer()
    YearRemodAdd = fields.Integer()
    YrSold = fields.Integer()
    FirstFlrSF = fields.Integer()
    SecondFlrSF = fields.Integer()
    ThreeSsnPortch = fields.Integer()


def _filter_error_rows(errors: dict,
                       validated_input: t.List[dict]
                       ) -> t.List[dict]:
    """Remove input data rows with errors."""

    indexes = errors.keys()
    # delete them in reverse order so that you
    # don't throw off the subsequent indexes.
    for index in sorted(indexes, reverse=True):
        del validated_input[index]

    return validated_input


def validate_inputs(input_data):
    """Check prediction inputs against schema."""

    # set many=True to allow passing in a list
    schema = HouseDataRequestSchema(many=True)

    # convert syntax error field names (beginning with numbers)
    for row in input_data:
        for original, safe_name in SYNTAX_ERROR_FIELD_MAP.items():
            row[safe_name] = row[original]
            del row[original]

    errors = None
    try:
        schema.load(input_data)
    except ValidationError as exc:
        errors = exc.messages

    # convert syntax error field names back
    # this is a hack - never name your data
    # fields with numbers as the first letter.
    for row in input_data:
        for original, safe_name in SYNTAX_ERROR_FIELD_MAP.items():
            row[original] = row[safe_name]
            del row[safe_name]

    if errors:
        validated_input = _filter_error_rows(
            errors=errors,
            validated_input=input_data)
    else:
        validated_input = input_data

    return validated_input, errors
