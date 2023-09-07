/*------------------------------------- Used ----------------------------------------*/
/*function and trigger for getting age from dob*/
CREATE OR REPLACE FUNCTION get_age_from_dob()
RETURNS TRIGGER AS $$
BEGIN
    NEW.age := CAST(EXTRACT(YEAR FROM AGE(current_date, NEW.date_of_birth)) AS integer);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

/*trigger before insert*/
CREATE TRIGGER get_age_from_dob_trigger
BEFORE INSERT ON "user"
FOR EACH ROW
EXECUTE FUNCTION get_age_from_dob();



/*function and triggers for activity_detail table*/
CREATE OR REPLACE FUNCTION update_activity_detail()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_NARGS <> 1 THEN
        RAISE EXCEPTION 'Wrong number of arguments for update_activity_detail()';
    END IF;

    INSERT INTO activity_detail (metric, count, date)
    VALUES (TG_ARGV[0], 1, NOW())
    ON CONFLICT (metric, date)
    DO UPDATE SET count = activity_detail.count + 1;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

/*trigger upon insert user*/
CREATE TRIGGER user_add_activity_detail_trigger
AFTER INSERT ON "user"
FOR EACH ROW
EXECUTE FUNCTION update_activity_detail('Users_Added');

/*trigger upon delete user*/
CREATE TRIGGER user_delete_activity_detail_trigger
AFTER DELETE ON "user"
FOR EACH ROW
EXECUTE FUNCTION update_activity_detail('Users_Deleted');



/*Based on user logout from one session and logout from all devices*/
CREATE OR REPLACE FUNCTION update_user_auth_track()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_NARGS <> 1 THEN
        RAISE EXCEPTION 'Wrong number of arguments for update_user_auth_track()';
    END IF;
    
    IF TG_ARGV[0]='one' THEN
        UPDATE user_auth_track 
        SET status='invalid', updated_at = NOW()
        WHERE user_id=OLD.user_id AND device_info=OLD.device_info;
    ELSIF TG_ARGV[0]='all' THEN
        UPDATE user_auth_track 
        SET status='invalid', updated_at = NOW()
        WHERE user_id=OLD.user_id;
    END IF;
    
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

/*trigger upon update user_session logout one device/session*/
CREATE TRIGGER user_auth_track_logout_one_trigger
AFTER UPDATE ON user_session
FOR EACH ROW
EXECUTE FUNCTION update_user_auth_track('one');

/*trigger upon update user_session logout all devices/sessions*/
CREATE TRIGGER user_auth_track_logout_all_trigger
AFTER UPDATE ON user_session
FOR EACH STATEMENT
EXECUTE FUNCTION update_user_auth_track('all');






/*------------------------------------- Not used ----------------------------------------*/
/*function and trigger for user_auth_track table upon user logout*/
CREATE OR REPLACE FUNCTION update_user_auth_track()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE user_auth_track 
    SET status='invalid' 
    WHERE user_id=OLD.user_id AND device_info=OLD.device_info;
    
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

/*trigger upon update user_session*/
CREATE TRIGGER user_auth_track_logout_trigger
AFTER UPDATE ON user_session
FOR EACH ROW
EXECUTE FUNCTION update_user_auth_track();


