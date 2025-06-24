class CriteriaException(Exception):
    pass


class ValidationError(CriteriaException):
    pass


class FunctionSpecValidationError(ValidationError):
    pass


class UnsupportedFunction(FunctionSpecValidationError):
    pass


class CriterionValidationError(ValidationError):
    pass


class ComparisonExecutorNotFound(CriteriaException):
    pass


class FunctionEvaluationError(CriteriaException):
    """Error occurred while evaluating a TA-LIB function on an object"""

    pass
