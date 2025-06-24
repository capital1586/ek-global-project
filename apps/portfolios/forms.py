from django import forms
import decimal
import typing

from .models import Portfolio, Investment
from apps.stocks.models import Stock


class PortfolioCreateForm(forms.ModelForm):
    """Portfolio creation form."""

    class Meta:
        model = Portfolio
        fields = ("owner", "name", "capital", "brokerage_percentage", "description")


class PortfolioUpdateForm(forms.ModelForm):
    """Portfolio update form."""

    cash_addition = forms.DecimalField(required=False, max_digits=12, decimal_places=2)

    class Meta:
        model = Portfolio
        fields = (
            "name",
            "brokerage_percentage",
            "description",
            "cash_addition",
            "dividends",
        )

    def clean_dividends(self):
        dividends = self.cleaned_data["dividends"]
        if not dividends:
            return self.instance.dividends

        if self.instance:
            dividends += self.instance.dividends
        return dividends

    def save(self, commit: bool = True) -> Portfolio:
        portfolio: Portfolio = super().save(commit=False)
        cash_addition = self.cleaned_data.get("cash_addition")
        if cash_addition:
            portfolio.capital += cash_addition

        if commit:
            portfolio.save()
        return portfolio


ModelForm = typing.TypeVar("ModelForm", bound=forms.ModelForm)


def _clean_percentage_to_decimal(*fields: str):
    """
    Private decorator

    Adds a clean method to the form class for each field in the fields list.
    The clean method added converts a percentage string to a decimal value,
    calculated from the rate field of the form.

    Regular integer strings are also converted to their decimal equivalent
    """

    def make_clean_method_for_field(field: str):
        def _clean_method(form: ModelForm):
            value: str = form.cleaned_data[field]
            rate = form.cleaned_data["rate"]
            if not value:
                return decimal.Decimal(0)

            if value.endswith("%"):
                value = (decimal.Decimal(value.removesuffix("%")) / 100) * rate
            else:
                # Check if the value does not exceed the rate
                # Normally, it should not exceed the rate
                if decimal.Decimal(value) > rate:
                    raise forms.ValidationError(
                        f"{field} should not exceed the stock rate of {rate}".capitalize()
                    )

            # Round to two decimal places
            return decimal.Decimal(value).quantize(
                decimal.Decimal("0.01"), rounding=decimal.ROUND_HALF_UP
            )

        _clean_method.__name__ = f"clean_{field}"
        _clean_method.__qualname__ = f"clean_{field}"
        return _clean_method

    def form_decorator(form_class: typing.Type[ModelForm]):
        for field in fields:
            if field not in form_class._meta.fields:
                continue
            setattr(form_class, f"clean_{field}", make_clean_method_for_field(field))
        return form_class

    return form_decorator


@_clean_percentage_to_decimal(*Investment.ADDITIONAL_FEES, "brokerage_fee")
class InvestmentAddForm(forms.ModelForm):
    portfolio = forms.UUIDField()
    stock = forms.CharField()
    brokerage_fee = forms.CharField(required=True, strip=True)
    commission = forms.CharField(required=False, strip=True)
    cdc = forms.CharField(required=False, strip=True)
    psx = forms.CharField(required=False, strip=True)
    secp = forms.CharField(required=False, strip=True)
    nccpl = forms.CharField(required=False, strip=True)
    cvt = forms.CharField(required=False, strip=True)
    whts = forms.CharField(required=False, strip=True)
    whtc = forms.CharField(required=False, strip=True)
    adv_tax = forms.CharField(required=False, strip=True)
    sst = forms.CharField(required=False, strip=True)
    laga = forms.CharField(required=False, strip=True)
    nlaga = forms.CharField(required=False, strip=True)
    fed = forms.CharField(required=False, strip=True)
    misc = forms.CharField(required=False, strip=True)

    class Meta:
        model = Investment
        fields = (
            "portfolio",
            "transaction_type",
            "stock",
            "transaction_date",
            "transaction_time",
            "settlement_date",
            "rate",
            "quantity",
            "brokerage_fee",
            "commission",
            "cdc",
            "psx",
            "secp",
            "nccpl",
            "cvt",
            "whts",
            "whtc",
            "adv_tax",
            "sst",
            "laga",
            "nlaga",
            "fed",
            "misc",
        )

    def clean_portfolio(self):
        portfolio = self.cleaned_data["portfolio"]
        try:
            portfolio = Portfolio.objects.get(id=portfolio)
        except Portfolio.DoesNotExist as exc:
            raise forms.ValidationError(str(exc))
        return portfolio

    def clean_stock(self):
        stock = self.cleaned_data["stock"]
        try:
            stock = Stock.objects.get(ticker=stock)
        except Stock.DoesNotExist as exc:
            raise forms.ValidationError(str(exc))
        return stock

    def save(self, commit: bool = True) -> Investment:
        investment: Investment = super().save(commit=False)
        if investment.portfolio.cash_balance < investment.cost:
            raise forms.ValidationError("Insufficient capital in portfolio.")
        if commit:
            investment.save()
        return investment
