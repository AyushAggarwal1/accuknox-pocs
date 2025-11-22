-- show all tables in steampipe where user can query based on compartment_id
select table_schema || '.' || table_name
from information_schema.columns
where column_name = 'compartment_id'
group by table_schema, table_name
order by 1;

-- show all availability domains in a compartment
with recursive comps as (
  select id from oci_identity_compartment where id = '<<compartment_id>>'
  union all
  select c.id
  from oci_identity_compartment c
  join comps p on c.compartment_id = p.id
  where c.lifecycle_state = 'ACTIVE'
)
select *
from <<table_name>>
where compartment_id in (select id from comps);

-- sample query 1 to get all compartments and sub-compartments
with recursive comps as (
  select id from oci_identity_compartment where id = '<<compartment_id>>'
  union all
  select c.id
  from oci_identity_compartment c
  join comps p on c.compartment_id = p.id
  where c.lifecycle_state = 'ACTIVE'
)
select *
from oci_identity_availability_domain
where compartment_id in (select id from comps);

-- sample query 2 only for compartment
select *
from <<table_name>>
where compartment_id = '<<compartment_id>>';
