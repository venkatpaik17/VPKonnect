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
/*update to simplify operation based on no of rows updated, this makes updates redundant, unnecessary*/
CREATE OR REPLACE FUNCTION update_user_auth_track()
RETURNS TRIGGER AS $$
DECLARE
    num_rows_affected INT;
BEGIN
    GET DIAGNOSTICS num_rows_affected = ROW_COUNT;

    IF num_rows_affected = 1 THEN
        -- Handle single row update
        UPDATE user_auth_track 
        SET status = 'invalid', updated_at = NOW()
        WHERE user_id = OLD.user_id AND device_info = OLD.device_info;
    ELSE
        -- Handle multiple row update
        UPDATE user_auth_track 
        SET status = 'invalid', updated_at = NOW()
        WHERE user_id = OLD.user_id;
    END IF;

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

/*trigger upon update user_session when is_active changes to FALSE*/
CREATE TRIGGER user_auth_track_logout_trigger
AFTER UPDATE ON user_session
FOR EACH ROW
WHEN (NEW.is_active = FALSE)
EXECUTE FUNCTION update_user_auth_track();



/*Based on update in user table, update 4 tables post, comment, post_like and comment_like when user is deleted (soft delete)*/
/* changed the mechanism of deactivate and delete, updated
# If the action is 'hide,' it updates all four tables with the status 'hidden'
# If the action is 'keep,' it updates only the 'post' table with the status 'hidden'
# If the action is 'unhide' and the previous status was 'pending_delete_hide,' it updates all four tables, setting the 'post' and 'comment' tables with the status 'published' and the 'post_like' and 'comment_like' tables with status 'active.'
# If the action is 'unhide' and the previous status was 'pending_delete_keep,' it updates only the 'post' table, with the status 'published.'
# If the action is 'delete', it updates all four tables with status 'deleted' and is_deleted = TRUE
*/
CREATE OR REPLACE FUNCTION update_user_info_status()
RETURNS TRIGGER AS $$
DECLARE
    action TEXT;
    new_status TEXT;
    user_id_param UUID;
    new_is_deleted BOOLEAN:= TRUE;
BEGIN
    IF TG_NARGS <> 1 THEN
        RAISE EXCEPTION 'Wrong number of arguments for update_user_info_status()';
    END IF;
    
    IF TG_ARGV[0]='hide' or TG_ARGV[0]='keep' THEN
        -- Handle 'pending_delete_hide' and 'pending_delete_keep' case
        action := TG_ARGV[0];
        new_status := 'hidden';
        user_id_param := OLD.id;
       
    ELSIF TG_ARGV[0]='unhide' THEN
        -- Handle 'active' case
        action := TG_ARGV[0];
        new_status := 'published';
        user_id_param := OLD.id;

    ELSIF TG_ARGV[0]='delete' THEN
        -- Handle 'deleted' case
        action := TG_ARGV[0];
        new_status := 'deleted';
        user_id_param := OLD.id;

    END IF;
    
    IF action = 'keep' OR (action = 'unhide' AND OLD.status = 'pending_delete_keep') THEN
        -- Check if there are posts related to the user
        IF EXISTS (SELECT 1 FROM post WHERE user_id = user_id_param) THEN
            -- Update 'post' table
            UPDATE post
            SET status = new_status
            WHERE user_id = user_id_param;
        END IF;
        
    ELSIF action = 'hide' OR (action = 'unhide' AND OLD.status = 'pending_delete_hide') OR action = 'delete' THEN
        -- Check if there are posts related to the user
        IF EXISTS (SELECT 1 FROM post WHERE user_id = user_id_param) THEN
            -- Update 'post' table
            UPDATE post
            SET status = new_status, is_deleted = CASE WHEN action = 'delete' THEN new_is_deleted ELSE FALSE END
            WHERE user_id = user_id_param;
        END IF;
        
        -- Check if there are comments related to the user
        IF EXISTS (SELECT 1 FROM comment WHERE user_id = user_id_param) THEN
            -- Update 'comment' table
            UPDATE comment
            SET status = new_status, is_deleted = CASE WHEN action = 'delete' THEN new_is_deleted ELSE FALSE END
            WHERE user_id = user_id_param;
        END IF;
    
        -- Check if there are post likes related to the user
        IF EXISTS (SELECT 1 FROM post_like WHERE user_id = user_id_param) THEN
            -- Update 'post_like' table
            UPDATE post_like
            SET status = CASE WHEN action = 'unhide' THEN 'active' ELSE new_status END, is_deleted = CASE WHEN action = 'delete' THEN new_is_deleted ELSE FALSE END
            WHERE user_id = user_id_param;
        END IF;
    
        -- Check if there are comment likes related to the user
        IF EXISTS (SELECT 1 FROM comment_like WHERE user_id = user_id_param) THEN
            -- Update 'comment_like' table
            UPDATE comment_like
            SET status = CASE WHEN action = 'unhide' THEN 'active' ELSE new_status END, is_deleted = CASE WHEN action = 'delete' THEN new_is_deleted ELSE FALSE END
            WHERE user_id = user_id_param;
        END IF;
    END IF;
    
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER user_delete_status_hide_trigger
AFTER UPDATE ON "user"
FOR EACH ROW
WHEN (NEW.status = 'pending_delete_hide')
EXECUTE FUNCTION update_user_info_status('hide');

CREATE TRIGGER user_delete_status_keep_trigger
AFTER UPDATE ON "user"
FOR EACH ROW
WHEN (NEW.status = 'pending_delete_keep')
EXECUTE FUNCTION update_user_info_status('keep');

CREATE TRIGGER user_delete_status_unhide_trigger
AFTER UPDATE ON "user"
FOR EACH ROW
WHEN (NEW.status = 'active')
EXECUTE FUNCTION update_user_info_status('unhide');

CREATE TRIGGER user_delete_status_delete_trigger
AFTER UPDATE ON "user"
FOR EACH ROW
WHEN (NEW.status = 'deleted' AND NEW.is_deleted = TRUE)
EXECUTE FUNCTION update_user_info_status('delete');