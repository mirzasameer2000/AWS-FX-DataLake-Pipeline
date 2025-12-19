CREATE EXTERNAL TABLE IF NOT EXISTS fx_lake.fx_rates_raw (
  date string,
  base string,
  currency string,
  rate double,
  source string,
  ingested_at string
)
PARTITIONED BY (dt string)
ROW FORMAT SERDE 'org.openx.data.jsonserde.JsonSerDe'
WITH SERDEPROPERTIES ('ignore.malformed.json'='true')
LOCATION 's3://fx-lake-sameer-24169956/raw/';
