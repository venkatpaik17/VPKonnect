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
/* updated to manage deactivated, restored and deleted user, accomodate enums*/
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

/*trigger upon status for deactivated, restored and deleted user*/
CREATE TRIGGER user_deactivate_activity_detail_trigger
AFTER UPDATE ON "user"
FOR EACH ROW
WHEN (NEW.status = 'PDH'::user_status_enum OR NEW.status = 'PDK'::user_status_enum)
EXECUTE FUNCTION update_activity_detail('Users_Deactivated');

CREATE TRIGGER user_active_activity_detail_trigger
AFTER UPDATE ON "user"
FOR EACH ROW
WHEN (NEW.status = 'ACT'::user_status_enum)
EXECUTE FUNCTION update_activity_detail('Users_Restored');

CREATE TRIGGER user_delete_activity_detail_trigger
AFTER UPDATE ON "user"
FOR EACH ROW
WHEN (NEW.status = 'DEL'::user_status_enum AND NEW.is_deleted = TRUE)
EXECUTE FUNCTION update_activity_detail('Users_Deleted');



/*Based on user logout from one session and logout from all devices*/
/*update to simplify operation based on no of rows updated, this makes updates redundant, unnecessary*/
/*updated to accomodate enums*/
CREATE OR REPLACE FUNCTION update_user_auth_track()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE user_auth_track 
    SET status='INV'::user_auth_track_status_enum, updated_at = NOW()
    WHERE user_id=OLD.user_id AND device_info=OLD.device_info;
   
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
# If any interaction is deleted or removed by user then it should not be hidden or restored during hide/keep/unhide. i.e., if post, comment, post_like, comment_like 'status' is 'deleted' and is_deleted is TRUE then keep it as it is. No update.
#updated to accommodate the enum
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
        -- Handle 'PDH' and 'PDK' case
        action := TG_ARGV[0];
        new_status := 'HID';
        user_id_param := OLD.id;
       
    ELSIF TG_ARGV[0]='unhide' THEN
        -- Handle 'ACT' case
        action := TG_ARGV[0];
        new_status := 'PUB';
        user_id_param := OLD.id;

    ELSIF TG_ARGV[0]='delete' THEN
        -- Handle 'DEL' case
        action := TG_ARGV[0];
        new_status := 'DEL';
        user_id_param := OLD.id;

    END IF;
    
    IF action = 'keep' OR (action = 'unhide' AND OLD.status = 'PDK'::user_status_enum) THEN
        -- Check if there are posts related to the user
        IF EXISTS (SELECT 1 FROM post WHERE user_id = user_id_param) THEN
            -- Update 'post' table
            UPDATE post
            SET status = CASE 
                WHEN post.status = 'DEL'::post_status_enum THEN post.status::post_status_enum 
                ELSE new_status::post_status_enum 
                END
            WHERE user_id = user_id_param;
        END IF;
        
    ELSIF action = 'hide' OR (action = 'unhide' AND OLD.status = 'PDH'::user_status_enum) OR action = 'delete' THEN
        -- Check if there are posts related to the user
        IF EXISTS (SELECT 1 FROM post WHERE user_id = user_id_param) THEN
            -- Update 'post' table
            UPDATE post
            SET status = CASE 
                WHEN post.status = 'DEL'::post_status_enum THEN post.status::post_status_enum 
                ELSE new_status::post_status_enum 
                END, 
                is_deleted = CASE 
                WHEN action = 'delete' OR post.is_deleted = TRUE THEN new_is_deleted 
                ELSE FALSE 
                END
            WHERE user_id = user_id_param;
        END IF;
        
        -- Check if there are comments related to the user
        IF EXISTS (SELECT 1 FROM comment WHERE user_id = user_id_param) THEN
            -- Update 'comment' table
            UPDATE comment
            SET status = CASE 
                WHEN comment.status = 'DEL'::comment_status_enum THEN comment.status::comment_status_enum 
                ELSE new_status::comment_status_enum 
                END, 
                is_deleted = CASE 
                WHEN action = 'delete' OR comment.is_deleted = TRUE THEN new_is_deleted 
                ELSE FALSE 
                END
            WHERE user_id = user_id_param;
        END IF;
    
        -- Check if there are post likes related to the user
        IF EXISTS (SELECT 1 FROM post_like WHERE user_id = user_id_param) THEN
            -- Update 'post_like' table
            UPDATE post_like
            SET status = CASE 
                WHEN post_like.status = 'DEL'::post_like_status_enum THEN post_like.status::post_like_status_enum 
                WHEN action = 'unhide' THEN 'ACT'::post_like_status_enum 
                ELSE new_status::post_like_status_enum
                END, 
                is_deleted = CASE 
                WHEN action = 'delete' OR post_like.is_deleted = TRUE THEN new_is_deleted 
                ELSE FALSE 
                END
            WHERE user_id = user_id_param;
        END IF;
    
        -- Check if there are comment likes related to the user
        IF EXISTS (SELECT 1 FROM comment_like WHERE user_id = user_id_param) THEN
            -- Update 'comment_like' table
            UPDATE comment_like
            SET status = CASE 
                WHEN comment_like.status = 'DEL'::comment_like_status_enum THEN comment_like.status::comment_like_status_enum 
                WHEN action = 'unhide' THEN 'ACT'::comment_like_status_enum 
                ELSE new_status::comment_like_status_enum
                END, 
                is_deleted = CASE 
                WHEN action = 'delete' OR comment_like.is_deleted = TRUE THEN new_is_deleted 
                ELSE FALSE 
                END
            WHERE user_id = user_id_param;
        END IF;
    END IF;
    
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER user_delete_status_hide_trigger
AFTER UPDATE ON "user"
FOR EACH ROW
WHEN (NEW.status = 'PDH'::user_status_enum)
EXECUTE FUNCTION update_user_info_status('hide');

CREATE TRIGGER user_delete_status_keep_trigger
AFTER UPDATE ON "user"
FOR EACH ROW
WHEN (NEW.status = 'PDK'::user_status_enum)
EXECUTE FUNCTION update_user_info_status('keep');

CREATE TRIGGER user_delete_status_unhide_trigger
AFTER UPDATE ON "user"
FOR EACH ROW
WHEN (NEW.status = 'ACT'::user_status_enum)
EXECUTE FUNCTION update_user_info_status('unhide');

CREATE TRIGGER user_delete_status_delete_trigger
AFTER UPDATE ON "user"
FOR EACH ROW
WHEN (NEW.status = 'DEL'::user_status_enum AND NEW.is_deleted = TRUE)
EXECUTE FUNCTION update_user_info_status('delete');