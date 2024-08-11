CREATE EXTENSION IF NOT EXISTS pgcrypto;

/*Author: Dave Allie
Link:https://blog.daveallie.com/ulid-primary-keys/
*/
CREATE OR REPLACE FUNCTION generate_ulid() RETURNS uuid
AS $$
    SELECT (lpad(to_hex(floor(extract(epoch FROM clock_timestamp()) * 1000)::bigint), 12, '0') || encode(gen_random_bytes(10), 'hex'))::uuid;
$$ LANGUAGE SQL;


/*getting next value from bigint sequence*/
CREATE SEQUENCE IF NOT EXISTS num_bigint_sequence;

CREATE OR REPLACE FUNCTION get_next_value_from_sequence()
RETURNS INTEGER AS $$
BEGIN
    RETURN nextval('num_bigint_sequence');
END;
$$ LANGUAGE plpgsql;


/*getting next value from bigint sequence*/
CREATE SEQUENCE IF NOT EXISTS num_bigint_sequence_ban_appeal_table;

CREATE OR REPLACE FUNCTION get_next_value_from_sequence_ban_appeal_table()
RETURNS INTEGER AS $$
BEGIN
    RETURN nextval('num_bigint_sequence_ban_appeal_table');
END;
$$ LANGUAGE plpgsql;


/*Sequence for getting a number from 1 to 9999*/
CREATE SEQUENCE IF NOT EXISTS num_int_1_9999
AS INT 
MINVALUE 1 
MAXVALUE 9999 
CYCLE;


/*Function to generate employee id*/
CREATE OR REPLACE FUNCTION generate_employee_id(
    first_name character varying,
    last_name character varying,
    join_date date
)
RETURNS character varying AS $$
DECLARE
    result_id character varying;
BEGIN
    result_id := 'V' || TO_CHAR(join_date, 'yyyymmdd') ||
                 SUBSTRING(first_name, 1, 2) ||
                 SUBSTRING(last_name, 1, 1) ||
                 LPAD(nextval('num_int_1_9999')::TEXT, 4, '0');
    RETURN result_id;
END;
$$ LANGUAGE plpgsql;