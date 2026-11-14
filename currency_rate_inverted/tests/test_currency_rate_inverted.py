# Copyright 2019 Brainbean Apps
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import timedelta

from lxml import etree

from odoo import fields
from odoo.tests import TransactionCase


class TestCurrencyRateInverted(TransactionCase):
    def setUp(self):
        super().setUp()

        self.today = fields.Date.today()
        self.Currency = self.env["res.currency"]
        self.SudoCurrency = self.Currency.sudo()
        # A new 18.0 database (company in USD) ships EUR and GBP inactive.
        self.eur = self.SudoCurrency.with_context(active_test=False).search(
            [("name", "=", "EUR")], limit=1
        )
        self.usd = self.SudoCurrency.search([("name", "=", "USD")], limit=1)
        self.gbp = self.SudoCurrency.with_context(active_test=False).search(
            [("name", "=", "GBP")], limit=1
        )
        (self.eur | self.gbp).active = True

    def _convert(self, from_currency, to_currency):
        return from_currency._convert(
            1.0,
            to_currency,
            self.env.company,
            self.today + timedelta(days=10),
            round=False,
        )

    def test_1(self):
        self.eur.write(
            {"rate_ids": [(0, False, {"name": self.today + timedelta(days=10)})]}
        )
        self.usd.write(
            {
                "rate_ids": [
                    (0, False, {"name": self.today + timedelta(days=10), "rate": 0.8})
                ],
            }
        )
        self.gbp.write(
            {
                "rate_ids": [
                    (0, False, {"name": self.today + timedelta(days=10), "rate": 1.1})
                ],
            }
        )

        self.usd.rate_inverted = True
        self.assertAlmostEqual(self._convert(self.eur, self.usd), 1.25, 2)
        self.assertAlmostEqual(self._convert(self.usd, self.eur), 0.8, 2)

        self.gbp.rate_inverted = True
        self.assertAlmostEqual(self._convert(self.gbp, self.usd), 1.38, 2)
        self.gbp.rate_inverted = False
        self.assertAlmostEqual(self._convert(self.gbp, self.usd), 1.14, 2)

        self.usd.rate_inverted = False
        self.assertAlmostEqual(self._convert(self.eur, self.usd), 0.8, 2)
        self.assertAlmostEqual(self._convert(self.usd, self.eur), 1.25, 2)

        self.gbp.rate_inverted = True
        self.assertAlmostEqual(self._convert(self.gbp, self.usd), 0.88, 2)
        self.gbp.rate_inverted = False
        self.assertAlmostEqual(self._convert(self.gbp, self.usd), 0.73, 2)

    def test_views(self):
        """The flag is on the currency form and list, not in the embedded rate list."""
        form = etree.fromstring(self.Currency.get_view(view_type="form")["arch"])
        self.assertTrue(form.xpath("//field[@name='rate_inverted']"))
        self.assertFalse(
            form.xpath("//field[@name='rate_ids']//field[@name='rate_inverted']")
        )
        liste = etree.fromstring(self.Currency.get_view(view_type="list")["arch"])
        self.assertTrue(liste.xpath("//field[@name='rate_inverted']"))
