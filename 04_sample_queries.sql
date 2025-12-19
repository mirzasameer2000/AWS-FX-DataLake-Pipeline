SELECT * 
FROM fx_lake.fx_rates_raw
ORDER BY dt DESC, currency
LIMIT 8;
