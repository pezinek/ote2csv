OTE2CSV
=======

This tool will download daily electricity prices from https://www.ote-cr.cz/cs/kratkodobe-trhy/elektrina/denni-trh
re-comuptes the missing CZK or EUR prices by using exchagne rates from CNB.
(in 2009-02-01 OTE switched from using CZK to EUR)


How to use
----------

To download all the prices from OTE do:

```shell
make run
```

the prices will end up in `ote_prices.csv`

if the download fails or you need to fetch the latest missing prices, 
just re-run the `make run` command and the download will continue.
