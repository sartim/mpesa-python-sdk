#!/usr/bin/python

"""
Mpesa REST API for Python.

All class functions take in keyword arguments (data) and
response returned is a response object from (python requests).
From this object you can retrieve the response parameters
as text or json.
"""
from __future__ import unicode_literals

import os
import logging
import base64
import requests

from datetime import datetime
from urls import URL

logger = logging.getLogger()


class Gateway:

    def __init__(self, access_token, env=os.environ.get('ENV'), version="v1", timeout=None):
        self.headers = {"Authorization": "Bearer %s" % access_token}
        self.env = env
        self.version = version
        self.timeout = timeout

    def make_request(self, url, payload, method):

        """Invoke url and return a python request object"""

        if self.timeout:
            return requests.request(method, url, headers=self.headers, json=payload, timeout=self.timeout)
        else:
            return requests.request(method, url, headers=self.headers, json=payload)

    def b2b_payment_request(self, data):

        """Mpesa Transaction from one company to another.

        https://developer.safaricom.co.ke/b2b/apis/post/paymentrequest
        """

        expected_keys = ["Initiator", "SecurityCredential",
                         "CommandID", "SenderIdentifierType",
                         "RecieverIdentifierType", "Amount",
                         "PartyA", "PartyB", "AccountReference",
                         "Remarks", "QueueTimeOutURL", "ResultURL"]
        payload = process_data(expected_keys, data)
        r = self.make_request(URL[self.env][self.version]["b2b_payment_request"],
                                     payload, "POST")
        response = r.json()

        return response

    def b2c_payment_request(self, data):

        """
        B2B
        Mpesa Transaction from company to client.

        https://developer.safaricom.co.ke/b2c/apis/post/paymentrequest
        """

        expected_keys = ["InitiatorName", "SecurityCredential",
                         "CommandID", "Amount", "PartyA",
                         "PartyB", "Remarks", "QueueTimeOutURL",
                         "ResultURL", "Occasion"]
        payload = process_data(expected_keys, data)
        url = URL[self.env][self.version]["b2c_payment_request"]
        r = self.make_request(url, payload, "POST")

        response = r.json()

        return response

    def c2b_register_url(self, data):

        """Use this API to register validation and confirmation URLs on M-Pesa.

        https://developer.safaricom.co.ke/c2b/apis/post/registerurl
        """
        expected_keys = ["ShortCode", "ResponseType",
                         "ConfirmationURL", "ValidationURL"]
        payload = process_data(expected_keys, data)
        url = URL[self.env][self.version]["c2b_register_url"]
        r = self.make_request(url, payload, "POST")
        response = r.json()

        return response

    def c2b_simulate_transaction(self, data):

        """
        C2B Simulate Transaction

        Use this API to simulate a C2B transaction.

        https://developer.safaricom.co.ke/c2b/apis/post/simulate
        """

        expected_keys = ["ShortCode", "Amount",
                         "Msisdn"]
        payload = process_data(expected_keys, data)
        payload["CommandID"] = "CustomerPayBillOnline"
        url = URL[self.env][self.version]["c2b_simulate_transaction"]
        r = self.make_request(url, payload, "POST")
        response = r.json()

        return response

    def transation_status_request(self, data):

        """Use this API to check the status of transaction.

        https://developer.safaricom.co.ke/transaction-status/apis/post/query
        """

        expected_keys = ["Initiator", "SecurityCredential",
                         "TransactionID", "PartyA",
                         "ResultURL", "QueueTimeOutURL",
                         "Remarks", "Occasion"]
        payload = process_data(expected_keys, data)
        payload["CommandID"] = "TransactionStatusQuery"
        payload["IdentifierType"] = "1"
        r = self.make_request(
            URL[self.env][self.version]["transation_status_request"], payload, "POST")
        response = r.json()

        return response

    def account_balance_request(self, data):

        """Use this API to enquire the balance on an M-Pesa BuyGoods (Till Number).

        https://developer.safaricom.co.ke/account-balance/apis/post/query
        """

        expected_keys = ["Initiator", "SecurityCredential", "PartyA",
                         "Remarks", "QueueTimeOutURL", "ResultURL"]
        payload = process_data(expected_keys, data)
        payload["CommandID"] = "AccountBalance"
        payload["IdentifierType"] = "4"
        response = self.make_request(
            URL[self.env][self.version]["account_balance_request"], payload, "POST")

        return response

    def reversal_request(self, data):

        """Use this API for reversal transaction.

        https://developer.safaricom.co.ke/reversal/apis/post/request
        """

        expected_keys = ["Initiator", "SecurityCredential",
                         "TransactionID", "Amount",
                         "ReceiverParty", "ResultURL",
                         "QueueTimeOutURL", "Remarks", "Occasion"]
        payload = process_data(expected_keys, data)
        payload["CommandID"] = "TransactionReversal"
        payload["RecieverIdentifierType"] = "4"
        response = self.make_request(
            URL[self.env][self.version]["reversal_request"], payload, "POST")

        logger.info('Success: %s' % (response))

        return response

    def lipa_na_mpesa_online_query(self, data):

        """For Lipa Na M-Pesa online payment using STK Push.

        https://developer.safaricom.co.ke/lipa-na-m-pesa-online/apis/post/stkpushquery/v1/query
        """

        expected_keys = ['BusinessShortCode', 'Password', 'Timestamp', 'CheckoutRequestID']
        payload = process_data(expected_keys, data)
        payload["Timestamp"] = generate_timestamp()
        url = URL[self.env][self.version]["lipa_na_mpesa_online_query"]
        r = self.make_request(url, payload, "POST")
        response = r.json()

        return response

    def lipa_na_mpesa_online_payment(self, data):

        """For Lipa Na M-Pesa online payment using STK Push.

        Use this API to initiate online payment on behalf of a customer.

        https://developer.safaricom.co.ke/lipa-na-m-pesa-online/apis/post/stkpush/v1/processrequest
        """

        expected_keys = ["BusinessShortCode", "Password",
                         "Amount", "PartyA", "PartyB",
                         "PhoneNumber", "CallBackURL",
                         "AccountReference", "TransactionDesc"]
        payload = process_data(expected_keys, data)
        payload["Timestamp"] = generate_timestamp()
        payload["TransactionType"] = "CustomerPayBillOnline"
        response = self.make_request(
            URL[self.env][self.version]["lipa_na_mpesa_online_payment"], payload, "POST")

        logger.info('Success: %s' % (response))

        return response


def oauth_generate_token(consumer_key, consumer_secret, grant_type="client_credentials", env="sandbox", version="v1"):

    """Authenticate your app and return an OAuth access token.

       This token gives you time bound access token to call allowed APIs.
       NOTE: The OAuth access token expires after an hour (3600 seconds),
             after which, you will need to generate another access token
             so you need to keep track of this.
    """
    response = requests.get(URL[env][version]["oauth_generate_token"],
                        params=dict(grant_type=grant_type),
                        auth=requests.auth.HTTPBasicAuth(consumer_key, consumer_secret))
    if response.status_code == 200:
        response_ = response.json()
    else:
        response_ = {"access_token": ""}
    logger.info("Generated new token")

    return response


def encode_password(shortcode, passkey, timestamp):
    """Generate and return a base64 encoded password for online access.
    """
    return base64.encode(shortcode + passkey + timestamp)


def generate_timestamp():
    """Return the current timestamp formated as YYYYMMDDHHMMSS"""
    return datetime.strftime(datetime.now(), "%Y%m%d%H%M%S")


def process_data(expected_keys, data):
    """Check for any expected but missing keyword arguments
       and raise a TypeError else return the keywords arguments
       repackaged in a dictionary i.e the payload.
    """
    payload = {}
    for key in expected_keys:
        value = data.pop(key, False)
        if not value:
            raise TypeError("Missing value on key {0}".format(key))
        else:
            payload[key] = value
    return payload
