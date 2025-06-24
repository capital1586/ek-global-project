import typing
from django import forms
from django.utils.itercompat import is_iterable


from .models import RiskProfile
from .criteria import converter
from .criteria.criteria import Criteria, make_criterion


def criterion_data(data: typing.Iterable[typing.Dict]):
    """
    Creates and yields criterion objects from iterable of criterion data

    :param data: An iterable of criterion data
    """
    if not is_iterable(data):
        raise ValueError("data must be an iterable")

    for criterion_data in data:
        if not isinstance(criterion_data, dict):
            raise ValueError("Criterion data must be a dictionary")

        func1 = criterion_data.get("func1", None)
        func2 = criterion_data.get("func2", None)
        op = criterion_data.get("op", None)
        if not all((func1, func2, op)):
            raise ValueError("Criterion data must have func1, func2, and op")

        yield make_criterion(
            func1=func1, func2=func2, op=op, ignore_unsupported_func=False
        )


class RiskProfileForm(forms.ModelForm):
    class Meta:
        model = RiskProfile
        fields = (
            "name",
            "description",
            "criteria",
            "owner",
            "period_return_start",
            "period_return_end",
        )

    def clean_criteria(self):
        criteria = self.cleaned_data.get("criteria")
        if not criteria:
            return criteria

        criterion_list = list(set(criterion_data(criteria)))
        criteria = Criteria(criterion_list)
        criteria = converter.unstructure(criteria)
        return criteria["criterion_list"]

    def clean(self) -> typing.Dict[str, typing.Any]:
        cleaned_data = super().clean()
        period_return_start = cleaned_data.get("period_return_start", None)
        period_return_end = cleaned_data.get("period_return_end", None)

        if any((period_return_start, period_return_end)):
            if not all((period_return_start, period_return_end)):
                raise forms.ValidationError(
                    {
                        "period_return_end": [
                            "Both start and end periods are required"
                        ],
                        "period_return_start": [
                            "Both start and end periods are required"
                        ],
                    }
                )

            if period_return_start >= period_return_end:
                raise forms.ValidationError(
                    {
                        "period_return_end": [
                            "End period must be greater than start period"
                        ]
                    }
                )
        return cleaned_data


class RiskProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = RiskProfile
        fields = (
            "name",
            "description",
            "criteria",
            "period_return_start",
            "period_return_end",
        )

    def clean_criteria(self):
        criteria = self.cleaned_data.get("criteria")
        if not criteria:
            return criteria

        criterion_list = list(set(criterion_data(criteria)))
        criteria = Criteria(criterion_list)
        criteria = converter.unstructure(criteria)
        return criteria["criterion_list"]

    def clean(self) -> typing.Dict[str, typing.Any]:
        cleaned_data = super().clean()
        period_return_start = cleaned_data.get("period_return_start", None)
        period_return_end = cleaned_data.get("period_return_end", None)

        if any((period_return_start, period_return_end)):
            if not all((period_return_start, period_return_end)):
                raise forms.ValidationError(
                    {
                        "period_return_end": [
                            "Both start and end periods are required"
                        ],
                        "period_return_start": [
                            "Both start and end periods are required"
                        ],
                    }
                )

            if period_return_start >= period_return_end:
                raise forms.ValidationError(
                    {
                        "period_return_end": [
                            "End period must be greater than start period"
                        ]
                    }
                )
        return cleaned_data
