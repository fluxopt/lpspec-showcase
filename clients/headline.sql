-- The four headline numbers off a directory of archives, for every scenario at
-- once, in a DuckDB shell with nothing installed:
--
--     duckdb -c ".read clients/headline.sql"
--
-- The record tables carry `run` already. A value frame carries the model's own
-- columns only, so `run` comes off the path, which `filename = true` gives.
-- Point the four globs at another directory and the query is unchanged.
with objective as (
    select run, year, objective
    from read_parquet('runs/*/answer/objective.parquet', union_by_name = true)
),
period as (select run, min(year) as first, max(year) as last from objective group by run),
value_of as (
    select regexp_extract(filename, '([^/]+)/answer/', 1) as run, quantity, year, generator, value from (
        select filename, 'emissions' as quantity, year, null as generator, value
            from read_parquet('runs/*/answer/expression/emissions/*.parquet', filename = true)
        union all by name
        select filename, 'carbon' as quantity, year, null as generator, value
            from read_parquet('runs/*/answer/dual/carbon/*.parquet', filename = true)
        union all by name
        select filename, 'total' as quantity, year, generator, value
            from read_parquet('runs/*/answer/primal/total/*.parquet', filename = true)
    )
),
clean as (
    select regexp_extract(filename, '([^/]+)/sources/', 1) as run, generator
    from read_parquet('runs/*/sources/rate.parquet', filename = true)
    where value = 0
)
select
    p.run,
    (select sum(objective) from objective o where o.run = p.run) as pathway_cost,
    1 - (select sum(value) from value_of v where v.run = p.run and v.quantity = 'emissions' and v.year = p.last)
      / (select sum(value) from value_of v where v.run = p.run and v.quantity = 'emissions' and v.year = p.first) as emissions_cut,
    (select sum(value) from value_of v join clean c on c.run = v.run and c.generator = v.generator
        where v.run = p.run and v.quantity = 'total' and v.year = p.last)
      / (select sum(value) from value_of v where v.run = p.run and v.quantity = 'total' and v.year = p.last) as zero_carbon_share,
    -coalesce((select sum(value) from value_of v where v.run = p.run and v.quantity = 'carbon' and v.year = p.last), 0) + 0.0 as carbon_price
from period p
order by p.run;
