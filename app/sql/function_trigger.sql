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



/*Based on update in user table, update 4 tables post, comment, post_like and comment_like when user is deleted (soft delete)*/
CREATE OR REPLACE FUNCTION update_user_info_status()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_NARGS <> 1 THEN
        RAISE EXCEPTION 'Wrong number of arguments for update_user_info_status()';
    END IF;
    
    IF TG_ARGV[0]='hide' THEN
        -- Handle 'true' and 'deactivated' case
        PERFORM update_all_user_related_data(OLD.id, 'hidden', TRUE, TG_ARGV[0]);
    ELSIF TG_ARGV[0]='unhide' THEN
        -- Handle 'false' and 'active' case
        PERFORM update_all_user_related_data(OLD.id, 'published', FALSE, TG_ARGV[0]);
    END IF;
  
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Helper function to update related data in 'post', 'comment', 'post_like' and 'comment_like' tables
CREATE OR REPLACE FUNCTION update_all_user_related_data(user_id_param UUID, new_status TEXT, new_is_deleted BOOLEAN, action TEXT)
RETURNS VOID AS $$
BEGIN
    -- Check if there are posts related to the user
    IF EXISTS (SELECT 1 FROM post WHERE user_id = user_id_param) THEN
        -- Update 'post' table
        UPDATE post
        SET status = new_status, is_deleted = new_is_deleted
        WHERE user_id = user_id_param;
    END IF;
    
    -- Check if there are comments related to the user
    IF EXISTS (SELECT 1 FROM comment WHERE user_id = user_id_param) THEN
        -- Update 'comment' table
        UPDATE comment
        SET status = new_status, is_deleted = new_is_deleted
        WHERE user_id = user_id_param;
    END IF;
    
    -- Check if there are post likes related to the user
    IF EXISTS (SELECT 1 FROM post_like WHERE user_id = user_id_param) THEN
        -- Update 'post_like' table
        UPDATE post_like
        SET status = CASE WHEN action = 'unhide' THEN 'active' ELSE new_status END, is_deleted = new_is_deleted
        WHERE user_id = user_id_param;
    END IF;
    
    -- Check if there are comment likes related to the user
    IF EXISTS (SELECT 1 FROM comment_like WHERE user_id = user_id_param) THEN
        -- Update 'comment_like' table
        UPDATE comment_like
        SET status = CASE WHEN action = 'unhide' THEN 'active' ELSE new_status END, is_deleted = new_is_deleted
        WHERE user_id = user_id_param;
    END IF;
END;
$$ LANGUAGE plpgsql;

/*Trigger upon update true, deactivated*/
CREATE TRIGGER user_delete_status_hide_trigger
AFTER UPDATE ON "user"
FOR EACH ROW
WHEN (NEW.is_deleted = TRUE AND NEW.status = 'deactivated')
EXECUTE FUNCTION update_user_info_status('hide');

/*Trigger upon update false, active*/
CREATE TRIGGER user_delete_status_unhide_trigger
AFTER UPDATE ON "user"
FOR EACH ROW
WHEN (NEW.is_deleted = FALSE AND NEW.status = 'active')
EXECUTE FUNCTION update_user_info_status('unhide');





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


