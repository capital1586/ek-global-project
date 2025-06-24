from re import M
import typing
import datetime
from django.views.decorators.debug import sensitive_variables
import httpx
import inflection
from dcrypt import TextCrypt, CryptKey
from django.utils import timezone
from django.conf import settings
from dateutil.parser import parse

from helpers.exceptions.requests import RequestError
from helpers.logging import log_exception


crypt = TextCrypt(key=CryptKey(hash_algorithm="MD5"))


class MGLinkRateProvider:
    """MGLink PSX rate provider client"""

    provider_auth_url = "https://api.mg-link.net/api/auth/token"
    provider_rates_url = "https://api.mg-link.net/api/Data1/PSXStockPrices"
    provider_timezone = settings.PAKISTAN_TIMEZONE

    @sensitive_variables("username", "password")
    def __init__(self, username: str, password: str, request_timeout: float = 30.0):
        """
        Initialize the client with the necessary credentials

        :param username: client username
        :param password: client password
        :param request_timeout: client request timeout in seconds
        """
        self.username = username
        self.password = crypt.encrypt(password)
        self.authentication_required_at = timezone.now()
        self._client = httpx.Client(
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0",
            },
            timeout=httpx.Timeout(request_timeout),
        )

    def __del__(self):
        # Close the request client when the object is destroyed
        self._client.close()

    @property
    def client(self):
        """Returns request client, authenticating if necessary"""
        # Authenticate 10 seconds before the token expires
        if (self.authentication_required_at - timezone.now()).total_seconds() < 10:
            self.authenticate()
        return self._client

    def authentication_successful(self, response_data: typing.Dict):
        """Handles the response data from a successful authentication request"""
        access_token = response_data["access_token"]
        validity_period = float(response_data["expires_in"])
        self._client.headers["Authorization"] = f"Bearer {access_token}"
        self.authentication_required_at = timezone.now() + timezone.timedelta(
            seconds=validity_period
        )
        return

    def authenticate(self) -> None:
        """Authenticate with the provider"""
        try:
            response = self._client.post(
                url=type(self).provider_auth_url,
                data={
                    "grant_type": "password",
                    "username": self.username,
                    "password": crypt.decrypt(self.password),
                },
            )
            if response.status_code != 200:
                print(response.json())
                response.raise_for_status()
            else:
                self.authentication_successful(response.json())
        except Exception as exc:
            log_exception(exc)
            raise RequestError(exc) from exc

    def fetch_psx_rates(
        self,
        _from: typing.Optional[datetime.date] = None,
        _to: typing.Optional[datetime.date] = None,
        /,
    ):
        """
        Fetch PSX rates from the provider.

        Leave _from and _to empty to get the latest PSX rates

        :param _from: The date from which to fetch the rates
        :param _to: The date to which to fetch the rates
        :return: The fetched rates
        """
        request_params = {
            "StartDate": _from.strftime("%Y-%m-%d") if _from else None,
            "EndDate": _to.strftime("%Y-%m-%d") if _to else None,
        }

        try:
            response = self.client.get(
                url=type(self).provider_rates_url,
                params=request_params,
            )
            if response.status_code != 200:
                response.raise_for_status()
            return response.json()

        except Exception as exc:
            log_exception(exc)
            raise RequestError(exc) from exc


def convert_keys_to_snake_case(data: typing.Dict) -> typing.Dict:
    return {inflection.underscore(key): value for key, value in data.items()}


def clean_rate_data(data: typing.Dict) -> typing.Dict:
    """Cleans PSX rate data gotten from the provider"""
    data = convert_keys_to_snake_case(data)
    data["previous_close"] = data.get("last", 0.00)

    created_at = data.get("create_date_time", None)
    if created_at:
        created_at = parse(created_at)
        created_at.replace(microsecond=0)
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=MGLinkRateProvider.provider_timezone)

        # This needs to be done because the provider sometimes sends the time as 00:00:00
        # of which I presume they think is the end of the day but it's actually the start
        # of the day. So data that is supposed to be for the end of the day is actually
        # sent for the start of the day. Hence converting from the provider's timezone, GMT+0500,
        # 2024-02-24 00:00:00+0500 to UTC would be, 2024-02-23 17:00:00+0000 (which is the previous day)
        if created_at.time() == datetime.time(0, 0, 0, 0):
            created_at = created_at.replace(hour=23, minute=59, second=59)

        data["create_date_time"] = created_at.strftime("%Y-%m-%dT%H:%M:%S%z")
    return data


def cleaned_rates_data(rates_data: typing.List[typing.Dict]):
    """
    Cleans PSX rates data gotten from the provider.

    Yields cleaned data one at a time

    :param rates_data: The rates data to clean
    :return: The cleaned rates data
    """
    for rate_data in rates_data:
        yield clean_rate_data(rate_data)


mg_link_provider = MGLinkRateProvider(
    username=settings.MG_LINK_CLIENT_USERNAME,
    password=settings.MG_LINK_CLIENT_PASSWORD,
    request_timeout=90.0,
)


