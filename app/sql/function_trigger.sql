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

/*
trigger upon update
#updating User_Added trigger
#instead of ON INSERT it will be ON UPDATE after verification
*/
CREATE TRIGGER user_add_activity_detail_trigger
AFTER UPDATE ON "user"
FOR EACH ROW
WHEN (OLD.status = 'INA' AND NEW.status = 'ACT' AND NEW.is_verified = TRUE)
EXECUTE FUNCTION update_activity_detail('Users_Added');

/*trigger upon status for deactivated, restored and deleted user*/
CREATE TRIGGER user_deactivate_activity_detail_trigger
AFTER UPDATE ON "user"
FOR EACH ROW
WHEN (NEW.status IN ('PDK', 'PDH', 'DAH', 'DAK'))
EXECUTE FUNCTION update_activity_detail('Users_Deactivated');

/*updating User_restored trigger*/
CREATE TRIGGER user_active_activity_detail_trigger
AFTER UPDATE ON "user"
FOR EACH ROW
WHEN (OLD.status IN ('PDK', 'PDH', 'DAH', 'DAK') AND NEW.status = 'ACT')
EXECUTE FUNCTION update_activity_detail('Users_Restored');

CREATE TRIGGER user_delete_activity_detail_trigger
AFTER UPDATE ON "user"
FOR EACH ROW
WHEN (NEW.status = 'DEL' AND NEW.is_deleted = TRUE)
EXECUTE FUNCTION update_activity_detail('Users_Deleted');



/*Based on user logout from one session and logout from all devices*/
/*update to simplify operation based on no of rows updated, this makes updates redundant, unnecessary*/
/*updated to accomodate enums*/
CREATE OR REPLACE FUNCTION update_user_auth_track()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE user_auth_track 
    SET status='INV', updated_at = NOW()
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
#removed enum, but string values are kept as it is
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
    
    IF action = 'keep' OR (action = 'unhide' AND (OLD.status = 'PDK' OR OLD.status = 'DAK')) THEN
        -- Check if there are posts related to the user
        IF EXISTS (SELECT 1 FROM post WHERE user_id = user_id_param) THEN
            -- Update 'post' table
            UPDATE post
            SET status = CASE 
                WHEN post.status = 'DEL'THEN post.status
                ELSE new_status
                END
            WHERE user_id = user_id_param;
        END IF;
        
    ELSIF action = 'hide' OR (action = 'unhide' AND (OLD.status = 'PDH' OR OLD.status = 'DAH')) OR action = 'delete' THEN
        -- Check if there are posts related to the user
        IF EXISTS (SELECT 1 FROM post WHERE user_id = user_id_param) THEN
            -- Update 'post' table
            UPDATE post
            SET status = CASE 
                WHEN post.status = 'DEL' THEN post.status
                ELSE new_status
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
                WHEN comment.status = 'DEL' THEN comment.status 
                ELSE new_status
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
                WHEN post_like.status = 'DEL' THEN post_like.status 
                WHEN action = 'unhide' THEN 'ACT' 
                ELSE new_status
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
                WHEN comment_like.status = 'DEL' THEN comment_like.status 
                WHEN action = 'unhide' THEN 'ACT' 
                ELSE new_status
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
WHEN (NEW.status = 'PDH' OR NEW.status = 'DAH')
EXECUTE FUNCTION update_user_info_status('hide');

CREATE TRIGGER user_delete_status_keep_trigger
AFTER UPDATE ON "user"
FOR EACH ROW
WHEN (NEW.status = 'PDK' OR NEW.status = 'DAK')
EXECUTE FUNCTION update_user_info_status('keep');

CREATE TRIGGER user_delete_status_unhide_trigger
AFTER UPDATE ON "user"
FOR EACH ROW
WHEN (OLD.status <> 'INA' AND NEW.status = 'ACT')
EXECUTE FUNCTION update_user_info_status('unhide');

CREATE TRIGGER user_delete_status_delete_trigger
AFTER UPDATE ON "user"
FOR EACH ROW
WHEN (NEW.status = 'DEL' AND NEW.is_deleted = TRUE)
EXECUTE FUNCTION update_user_info_status('delete');


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


/*Trigger for getting age for employee*/
CREATE TRIGGER get_age_from_dob_1_trigger
BEFORE INSERT ON "employee"
FOR EACH ROW
EXECUTE FUNCTION get_age_from_dob();


CREATE OR REPLACE FUNCTION update_employee_auth_track()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE employee_auth_track 
    SET status='INV', updated_at = NOW()
    WHERE employee_id=OLD.employee_id AND device_info=OLD.device_info;
   
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

/*trigger upon update employee_session when is_active changes to FALSE*/
CREATE TRIGGER employee_auth_track_logout_trigger
AFTER UPDATE ON "employee_session"
FOR EACH ROW
WHEN (NEW.is_active = FALSE)
EXECUTE FUNCTION update_employee_auth_track();


/*trigger function for user follow association to hide and delete follows when user is deactivated/reactivated or deleted*/
CREATE OR REPLACE FUNCTION update_user_follow_association_status()
RETURNS TRIGGER AS $$
DECLARE
    action TEXT;
    new_status TEXT;
    user_id_param UUID;
BEGIN
    IF TG_NARGS <> 1 THEN
        RAISE EXCEPTION 'Wrong number of arguments for update_user_follow_association_status()';
    END IF;
    
    IF TG_ARGV[0]='hide' or TG_ARGV[0]='keep' THEN
        -- Handle 'PDH', 'DAH' and 'PDK', 'DAK' case
        action := TG_ARGV[0];
        new_status := 'HID';
        user_id_param := OLD.id;
       
    ELSIF TG_ARGV[0]='unhide' THEN
        -- Handle 'ACT' case
        action := TG_ARGV[0];
        new_status := 'ACP';
        user_id_param := OLD.id;

    ELSIF TG_ARGV[0]='delete' THEN
        -- Handle 'DEL' case
        action := TG_ARGV[0];
        new_status := 'DEL';
        user_id_param := OLD.id;

    END IF;

    IF action = 'hide' OR action = 'keep' THEN
        IF EXISTS (SELECT 1 FROM user_follow_association WHERE (follower_user_id = user_id_param OR followed_user_id = user_id_param) AND status = 'ACP') THEN
            UPDATE user_follow_association
            SET status = new_status
            WHERE (follower_user_id = user_id_param OR followed_user_id = user_id_param) AND status = 'ACP';
        END IF;
    ELSIF (action = 'unhide' AND (OLD.status IN ('PDH', 'PDK', 'DAH', 'DAK'))) OR action = 'delete' THEN
        IF EXISTS (SELECT 1 FROM user_follow_association WHERE (follower_user_id = user_id_param OR followed_user_id = user_id_param) AND status = 'HID') THEN
            UPDATE user_follow_association
            SET status = new_status
            WHERE (follower_user_id = user_id_param OR followed_user_id = user_id_param) AND status = 'HID';
        END IF;
    END IF;
    
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;


CREATE TRIGGER user_deactivate_delete_follow_status_hide_trigger
AFTER UPDATE ON "user"
FOR EACH ROW
WHEN (NEW.status = 'PDH' OR NEW.status = 'DAH')
EXECUTE FUNCTION update_user_follow_association_status('hide');

CREATE TRIGGER user_deactivate_delete_follow_status_keep_trigger
AFTER UPDATE ON "user"
FOR EACH ROW
WHEN (NEW.status = 'PDK' OR NEW.status = 'DAK')
EXECUTE FUNCTION update_user_follow_association_status('keep');

CREATE TRIGGER user_deactivate_delete_follow_status_unhide_trigger
AFTER UPDATE ON "user"
FOR EACH ROW
WHEN (OLD.status <> 'INA' AND NEW.status = 'ACT')
EXECUTE FUNCTION update_user_follow_association_status('unhide');

CREATE TRIGGER user_deactivate_delete_follow_status_delete_trigger
AFTER UPDATE ON "user"
FOR EACH ROW
WHEN (NEW.status = 'DEL' AND NEW.is_deleted = TRUE)
EXECUTE FUNCTION update_user_follow_association_status('delete');



/* 
#update the function to customize more
# For content_type account, closed means 'No Action' instead of 'Not Removed'
# For content_type account, we can't resolve directly, we need to check if the action is enforced now or later, also we need to know what action is enforced,
  # so we need have a seperate trigger for handling that
# this function and resolve trigger is only for post/comment/message
*/
CREATE OR REPLACE FUNCTION insert_report_event_timeline()
RETURNS TRIGGER AS $$
DECLARE
    action TEXT;
    content_type TEXT;
    event TEXT;
    info TEXT;
BEGIN
    IF TG_NARGS <> 1 THEN
        RAISE EXCEPTION 'Wrong number of arguments for insert_report_event_timeline()';
    END IF;
    
    action = TG_ARGV[0];
    content_type = OLD.reported_item_type;
    
    IF action = 'SUB' THEN
        event := 'Submitted';
        info := 'Report Received';
    ELSIF action = 'REV' THEN
        event := 'Under Review';
        info := 'Review in progress';
    ELSIF action = 'RES' THEN
        event := 'Resolved';
        info := content_type || ' Removed';
    ELSIF action = 'CLS' THEN
        IF content_type = 'account' THEN
            info := content_type || ' No Action';
        ELSE
            info := content_type || ' Not Removed';
        END IF;
        event := 'Closed';
        
    END IF;
    
    INSERT INTO "user_content_report_event_timeline" (event_type, detail, report_id) 
    VALUES (event, info, NEW.id);
    
    RETURN NEW;
    
END;
$$ LANGUAGE plpgsql;


CREATE TRIGGER user_content_report_submit_event_trigger
AFTER INSERT on "user_content_report_detail"
FOR EACH ROW
EXECUTE FUNCTION insert_report_event_timeline('SUB');

CREATE TRIGGER user_content_report_review_event_trigger
AFTER UPDATE on "user_content_report_detail"
FOR EACH ROW
WHEN (OLD.status = 'OPN' AND NEW.status = 'URV')
EXECUTE FUNCTION insert_report_event_timeline('REV');

CREATE TRIGGER user_content_report_resolve_event_trigger
AFTER UPDATE on "user_content_report_detail"
FOR EACH ROW
WHEN (OLD.reported_item_type IN ('post', 'comment', 'message') AND (OLD.status = 'URV' AND NEW.status = 'RSD'))
EXECUTE FUNCTION insert_report_event_timeline('RES');

CREATE TRIGGER user_content_report_close_event_trigger
AFTER UPDATE on "user_content_report_detail"
FOR EACH ROW
WHEN (OLD.status = 'URV' AND NEW.status = 'CSD')
EXECUTE FUNCTION insert_report_event_timeline('CLS');



/*function and trigger for handling resolved status for content_type account*/
CREATE OR REPLACE FUNCTION insert_report_event_timeline_account_resolve()
RETURNS TRIGGER AS $$
DECLARE
    report_id UUID;
    event TEXT;
    info TEXT;
    status TEXT;
    
BEGIN
    IF TG_OP = 'INSERT' THEN
        status := NEW.status;
        report_id := NEW.report_id;
    ELSE
        status := OLD.status;
        report_id := OLD.report_id;
    END IF;
    
    event := 'Resolved';
    
    IF status IN ('RSF', 'RSP') THEN
        info := 'account restricted';
    ELSIF status = 'TBN' THEN
        info := 'account temp banned';
    ELSIF status = 'PBN' THEN
        info := 'account perm banned';
    END IF;
    
    INSERT INTO "user_content_report_event_timeline" (event_type, detail, report_id) 
    VALUES (event, info, report_id);
    
    RETURN NEW;

END;
$$ LANGUAGE plpgsql;


CREATE TRIGGER user_content_report_account_resolve_event_update_trigger
AFTER UPDATE on "user_restrict_ban_detail"
FOR EACH ROW
WHEN (OLD.content_type = 'account' AND (OLD.is_active = FALSE AND NEW.is_active = TRUE))
EXECUTE FUNCTION insert_report_event_timeline_account_resolve();

CREATE TRIGGER user_content_report_account_resolve_event_insert_trigger
AFTER INSERT on "user_restrict_ban_detail"
FOR EACH ROW
WHEN (NEW.content_type = 'account')
EXECUTE FUNCTION insert_report_event_timeline_account_resolve();



/*function and triggers for inserting appeal events*/
CREATE OR REPLACE FUNCTION insert_appeal_event_timeline()
RETURNS TRIGGER AS $$
DECLARE
    action TEXT;
    content_type TEXT;
    event TEXT;
    info TEXT;
    user_id_var UUID;
    ban_restrict_id UUID;
    user_status TEXT := NULL;
BEGIN
    IF TG_NARGS <> 1 THEN
        RAISE EXCEPTION 'Wrong number of arguments for insert_appeal_event_timeline()';
    END IF;
    
    action = TG_ARGV[0];
    content_type = OLD.content_type;
    user_id_var = OLD.user_id;
    ban_restrict_id = OLD.ban_report_id;
    
    IF action = 'SUB' THEN
        event := 'Submitted';
        info := 'Appeal Received';
    ELSIF action = 'REV' THEN
        event := 'Under Review';
        info := 'Review in progress';
    ELSIF action = 'ACP' THEN
        IF content_type = 'account' THEN
            SELECT status INTO user_status FROM "user_restrict_ban_detail" WHERE user_id = user_id_var AND id = ban_restrict_id;
            IF user_status = 'RSP' THEN
                info := content_type || ' Partial Restrict revoked';
            ELSIF user_status = 'RSF' THEN
                info := content_type || ' Full Restrict revoked';
            ELSIF user_status = 'TBN' THEN
                info := content_type || ' Temp Ban revoked';
            ELSIF user_status = 'PBN' THEN
                info := content_type || ' Permnt Ban revoked';
            END IF;
        ELSE
            info := content_type || ' Ban revoked';
        END IF;
        
        event := 'Accepted';
    ELSIF action = 'REJ' THEN
        IF content_type = 'account' THEN
            SELECT status INTO user_status FROM "user_restrict_ban_detail" WHERE user_id = user_id_var AND id = ban_restrict_id;
            IF user_status = 'RSP' THEN
                info := content_type || ' Partial Restrict not revoked';
            ELSIF user_status = 'RSF' THEN
                info := content_type || ' Full Restrict not revoked';
            ELSIF user_status = 'TBN' THEN
                info := content_type || ' Temp Ban not revoked';
            ELSIF user_status = 'PBN' THEN
                info := content_type || ' Permnt Ban not revoked';
            END IF;
        ELSE
            info := content_type || ' Ban not revoked';
        END IF;
        
        event := 'Rejected';
    ELSIF action = 'CLS' THEN
        info := 'No Decision';
        event := 'Closed';
        
    END IF;
    
    INSERT INTO "user_content_restrict_ban_appeal_event_timeline" (event_type, detail, appeal_id) 
    VALUES (event, info, NEW.id);
    
    RETURN NEW;
    
END;
$$ LANGUAGE plpgsql;


CREATE TRIGGER user_content_restrict_ban_appeal_submit_event_trigger
AFTER INSERT on "user_content_restrict_ban_appeal_detail"
FOR EACH ROW
EXECUTE FUNCTION insert_appeal_event_timeline('SUB');

CREATE TRIGGER user_content_restrict_ban_appeal_review_event_trigger
AFTER UPDATE on "user_content_restrict_ban_appeal_detail"
FOR EACH ROW
WHEN (OLD.status = 'OPN' AND NEW.status = 'URV')
EXECUTE FUNCTION insert_appeal_event_timeline('REV');

CREATE TRIGGER user_content_restrict_ban_appeal_accept_event_trigger
AFTER UPDATE on "user_content_restrict_ban_appeal_detail"
FOR EACH ROW
WHEN (OLD.status = 'URV' AND NEW.status = 'ACP')
EXECUTE FUNCTION insert_appeal_event_timeline('ACP');

CREATE TRIGGER user_content_restrict_ban_appeal_reject_event_trigger
AFTER UPDATE on "user_content_restrict_ban_appeal_detail"
FOR EACH ROW
WHEN (OLD.status = 'URV' AND NEW.status = 'REJ')
EXECUTE FUNCTION insert_appeal_event_timeline('REJ');

CREATE TRIGGER user_content_restrict_ban_appeal_close_event_trigger
AFTER UPDATE on "user_content_restrict_ban_appeal_detail"
FOR EACH ROW
WHEN (OLD.status = 'URV' AND NEW.status = 'CSD')
EXECUTE FUNCTION insert_appeal_event_timeline('CLS');