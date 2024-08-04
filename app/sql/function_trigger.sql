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
    IF TG_OP = 'INSERT' THEN
        INSERT INTO activity_detail (metric, count, date)
        VALUES ('Users_Added', 1, NOW())
        ON CONFLICT (metric, date)
        DO UPDATE SET count = activity_detail.count + 1;
    
    ELSIF TG_OP = 'UPDATE' THEN
        -- Increment the count for the new status
        INSERT INTO activity_detail (metric, count, date)
        VALUES (
            CASE 
                WHEN NEW.status = 'ACT' AND OLD.status = 'INA' AND NEW.is_verified = TRUE THEN 'Users_Active'
                WHEN NEW.status = 'INA' THEN 'Users_Inactive'
                WHEN NEW.status = 'RSP' THEN 'Users_Restricted_Partial'
                WHEN NEW.status = 'RSF' THEN 'Users_Restricted_Full'
                WHEN NEW.status = 'DAH' THEN 'Users_Deactivated'
                WHEN NEW.status = 'PDH' THEN 'Users_Pending_Delete'
                WHEN NEW.status = 'TBN' THEN 'Users_Banned_Temp'
                WHEN NEW.status = 'PBN' THEN 'Users_Banned_Perm'
                WHEN NEW.status = 'PDI' THEN 'Users_Pending_Delete'
                WHEN NEW.status = 'PDB' THEN 'Users_Pending_Delete'
                WHEN NEW.status = 'DEL' AND NEW.is_deleted = TRUE THEN 'Users_Deleted'
                WHEN NEW.status = 'ACT' AND OLD.status = 'RSP' THEN 'Users_Unrestricted_Partial'
                WHEN NEW.status = 'ACT' AND OLD.status = 'RSF' THEN 'Users_Unrestricted_Full'
                WHEN NEW.status = 'ACT' AND OLD.status = 'TBN' THEN 'Users_Unbanned_Temp'
                WHEN NEW.status = 'ACT' AND OLD.status = 'PBN' THEN 'Users_Unbanned_Perm'
                WHEN NEW.status = 'ACT' AND OLD.status IN ('DAH', 'INA') THEN 'Users_Reactivated'
                WHEN NEW.status = 'ACT' AND OLD.status = 'PDH' THEN 'Users_Restored'
                ELSE NULL
            END,
            1, NOW()
        )
        ON CONFLICT (metric, date)
        DO UPDATE SET count = activity_detail.count + 1;

        -- Decrement the count for the old status
        INSERT INTO activity_detail (metric, count, date)
        VALUES (
            CASE 
                WHEN OLD.status = 'ACT' THEN 'Users_Active'
                WHEN OLD.status = 'INA' AND OLD.is_verified = TRUE THEN 'Users_Inactive'
                WHEN OLD.status = 'RSP' THEN 'Users_Restricted_Partial'
                WHEN OLD.status = 'RSF' THEN 'Users_Restricted_Full'
                WHEN OLD.status = 'DAH' THEN 'Users_Deactivated'
                WHEN OLD.status IN ('PDH', 'PDB', 'PDI') THEN 'Users_Pending_Delete'
                WHEN OLD.status = 'TBN' THEN 'Users_Banned_Temp'
                WHEN OLD.status = 'PBN' THEN 'Users_Banned_Perm'
                ELSE NULL
            END,
            -1, NOW()
        )
        ON CONFLICT (metric, date)
        DO UPDATE SET count = activity_detail.count - 1;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


CREATE TRIGGER user_insert_activity_detail_trigger
AFTER INSERT ON "user"
FOR EACH ROW
EXECUTE FUNCTION update_activity_detail();

CREATE TRIGGER user_update_activity_detail_trigger
AFTER UPDATE OF status ON "user"
FOR EACH ROW
WHEN
    (
        (OLD.status = 'INA' AND NEW.status = 'ACT' AND NEW.is_verified = TRUE) OR
        (OLD.status IN ('ACT', 'RSP', 'RSF', 'TBN') AND NEW.status = 'INA') OR
        (OLD.status IN ('ACT', 'INA', 'DAH', 'PDH', 'RSF', 'TBN') AND NEW.status = 'RSP') OR
        (OLD.status IN ('ACT', 'INA', 'DAH', 'PDH', 'RSP', 'TBN') AND NEW.status = 'RSF') OR
        (OLD.status IN ('ACT', 'RSP', 'RSF') AND NEW.status = 'DAH') OR
        ((OLD.status IN ('ACT', 'RSP', 'RSF') AND NEW.status = 'PDH') OR (OLD.status = 'PBN' AND NEW.status = 'PDB') OR (OLD.status = 'INA' AND NEW.status = 'PDI')) OR
        (OLD.status IN ('ACT', 'INA', 'RSP', 'RSF', 'DAH', 'PDH') AND NEW.status = 'TBN') OR
        (OLD.status IN ('ACT', 'INA', 'RSP', 'RSF', 'DAH', 'PDH', 'TBN') AND NEW.status = 'PBN') OR
        (OLD.status = 'RSP' AND NEW.status = 'ACT') OR
        (OLD.status = 'RSF' AND NEW.status = 'ACT') OR
        (OLD.status = 'TBN' AND NEW.status = 'ACT') OR
        (OLD.status = 'PBN' AND NEW.status = 'ACT') OR
        (OLD.status IN ('DAH', 'INA') AND NEW.status = 'ACT') OR
        (OLD.status = 'PDH' AND NEW.status = 'ACT') OR
        (OLD.status IN ('PDH', 'PDB', 'PDI') AND NEW.status = 'DEL' AND NEW.is_deleted = TRUE)
    )
EXECUTE FUNCTION update_activity_detail();


/*Based on user logout from one session and logout from all devices*/
CREATE OR REPLACE FUNCTION update_user_auth_track()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE user_auth_track 
    SET user_auth_track.status='INV', user_auth_track.updated_at = NOW()
    WHERE user_id=OLD.user_id AND device_info=OLD.device_info;
   
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

/*trigger upon update user_session when is_active changes to FALSE*/
CREATE TRIGGER user_auth_track_logout_trigger
AFTER UPDATE OF is_active ON user_session
FOR EACH ROW
WHEN (NEW.is_active = FALSE)
EXECUTE FUNCTION update_user_auth_track();



/*Based on status update (DAH/PDH/PBN/PDI) in user table, update 5 tables post, comment, post_like, comment_like and user_follow_association*/
CREATE OR REPLACE FUNCTION update_user_info_status()
RETURNS TRIGGER AS $$
DECLARE
    user_id_param UUID;
BEGIN
    user_id_param := OLD.id;
    
    -- Update 'post' table
    UPDATE post
    SET status = CASE 
        WHEN post.status = 'PUB' THEN 'HID' 
        WHEN post.status = 'HID' THEN 'PUB'
        END,
        post.updated_at = NOW()
    WHERE user_id = user_id_param;

    -- Update 'comment' table
    UPDATE comment
    SET status = CASE 
        WHEN comment.status = 'PUB' THEN 'HID' 
        WHEN comment.status = 'HID' THEN 'PUB'
        END,
        comment.updated_at = NOW()
    WHERE user_id = user_id_param;

    -- Update 'post_like' table
    UPDATE post_like
    SET status = CASE 
        WHEN post_like.status = 'ACT' THEN 'HID' 
        WHEN post_like.status = 'HID' THEN 'ACT'
        END,
        post_like.updated_at = NOW()
    WHERE user_id = user_id_param;

    -- Update 'comment_like' table
    UPDATE comment_like
    SET status = CASE 
        WHEN comment_like.status = 'ACT' THEN 'HID'
        WHEN comment_like.status = 'HID' THEN 'ACT'
        END,
        comment_like.updated_at = NOW()
    WHERE user_id = user_id_param;

    -- Update 'user_follow_association' table
    UPDATE user_follow_association
    SET status = CASE
        WHEN user_follow_association.status = 'ACP' THEN 'HID'
        WHEN user_follow_association.status = 'HID' THEN 'ACP'
        END,
        user_follow_association.updated_at = NOW()
    WHERE follower_user_id = user_id_param OR followed_user_id = user_id_param;
    
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;


CREATE TRIGGER user_status_update_hide_trigger
AFTER UPDATE OF status ON "user"
FOR EACH ROW
WHEN ((OLD.status IN ('ACT', 'RSP', 'RSF', 'TBN') AND NEW.status IN ('DAH', 'PDH', 'PBN')) OR (OLD.status = 'INA' AND NEW.status IN ('PBN', 'PDI')))
EXECUTE FUNCTION update_user_info_status();

CREATE TRIGGER user_status_update_unhide_trigger
AFTER UPDATE OF status ON "user"
FOR EACH ROW
WHEN (OLD.status IN ('DAH', 'PDH', 'PBN') AND NEW.status IN ('ACT', 'RSP', 'RSF', 'TBN'))
EXECUTE FUNCTION update_user_info_status();



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
    SET employee_auth_track.status='INV', employee_auth_track.updated_at = NOW()
    WHERE employee_id=OLD.employee_id AND device_info=OLD.device_info;
   
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

/*trigger upon update employee_session when is_active changes to FALSE*/
CREATE TRIGGER employee_auth_track_logout_trigger
AFTER UPDATE OF is_active ON "employee_session"
FOR EACH ROW
WHEN (NEW.is_active = FALSE)
EXECUTE FUNCTION update_employee_auth_track();



/* 
Triggers and function to handle report events
post/comment/message and account report events combined in one
Close event has moderator_note considered for proper info
*/
CREATE OR REPLACE FUNCTION insert_report_event_timeline()
RETURNS TRIGGER AS $$
DECLARE
    action TEXT;
    report_content_type TEXT;
    event TEXT;
    info TEXT;
    
BEGIN
    IF TG_NARGS <> 1 THEN
        RAISE EXCEPTION 'Wrong number of arguments for insert_report_event_timeline()';
    END IF;
    
    action := TG_ARGV[0];
    report_content_type := OLD.reported_item_type;
    
    IF action = 'SUB' THEN
        event := 'Submitted';
        info := 'Report Received';
    ELSIF action = 'REV' THEN
        event := 'Under Review';
        info := 'Review in progress';
    ELSIF action = 'RES' THEN
        DECLARE
            user_status TEXT;
        BEGIN
            IF report_content_type = 'account' THEN
                SELECT status INTO user_status FROM "user_restrict_ban_detail" WHERE user_id = OLD.reported_user_id AND content_id = OLD.reported_item_id AND content_type = OLD.reported_item_type AND is_active = TRUE;
                IF user_status IN ('RSF', 'RSP') THEN
                    info := 'account restricted';
                ELSIF user_status = 'TBN' THEN
                    info := 'account temp banned';
                ELSIF user_status = 'PBN' THEN
                    info := 'account perm banned';
                END IF;
            ELSE
                info := report_content_type || ' Removed';
            END IF;
        END;
        event := 'Resolved';
        
    ELSIF action = 'CLS' THEN
        DECLARE
            action_info TEXT;
        BEGIN
            IF report_content_type = 'account' THEN
                action_info := 'No Action';
            ELSE
                IF NEW.moderator_note = 'RF' THEN
                    action_info := 'Not Removed';
                ELSIF NEW.moderator_note = 'RNB' THEN
                    action_info := 'Already Banned';
                ELSIF NEW.moderator_note = 'RNF' THEN
                    action_info := 'Already Flagged for future ban';
                ELSIF NEW.moderator_note = 'RND' THEN
                    action_info := 'Not Found';
                END IF;
            END IF;
            
            info := report_content_type || action_info;
        END;
        event := 'Closed';
        
    END IF;
    
    INSERT INTO "user_content_report_event_timeline" (event_type, detail, report_id) 
    VALUES (event, info, NEW.id);
    
    RETURN NEW;
    
END;
$$ LANGUAGE plpgsql;


CREATE TRIGGER user_content_report_submit_event_trigger
AFTER INSERT ON "user_content_report_detail"
FOR EACH ROW
EXECUTE FUNCTION insert_report_event_timeline('SUB');

CREATE TRIGGER user_content_report_review_event_trigger
AFTER UPDATE OF status ON "user_content_report_detail"
FOR EACH ROW
WHEN (OLD.status = 'OPN' AND NEW.status = 'URV')
EXECUTE FUNCTION insert_report_event_timeline('REV');

CREATE TRIGGER user_content_report_resolve_event_trigger
AFTER UPDATE OF status ON "user_content_report_detail"
FOR EACH ROW
WHEN (OLD.status IN ('URV', 'FRS', 'FRR') AND NEW.status IN ('RSD', 'RSR'))
EXECUTE FUNCTION insert_report_event_timeline('RES');

CREATE TRIGGER user_content_report_close_event_trigger
AFTER UPDATE OF status ON "user_content_report_detail"
FOR EACH ROW
WHEN (OLD.status = 'URV' AND NEW.status = 'CSD')
EXECUTE FUNCTION insert_report_event_timeline('CLS');



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
AFTER INSERT ON "user_content_restrict_ban_appeal_detail"
FOR EACH ROW
EXECUTE FUNCTION insert_appeal_event_timeline('SUB');

CREATE TRIGGER user_content_restrict_ban_appeal_review_event_trigger
AFTER UPDATE OF status ON "user_content_restrict_ban_appeal_detail"
FOR EACH ROW
WHEN (OLD.status = 'OPN' AND NEW.status = 'URV')
EXECUTE FUNCTION insert_appeal_event_timeline('REV');

CREATE TRIGGER user_content_restrict_ban_appeal_accept_event_trigger
AFTER UPDATE OF status ON "user_content_restrict_ban_appeal_detail"
FOR EACH ROW
WHEN (OLD.status = 'URV' AND NEW.status IN ('ACP', 'ACR'))
EXECUTE FUNCTION insert_appeal_event_timeline('ACP');

CREATE TRIGGER user_content_restrict_ban_appeal_reject_event_trigger
AFTER UPDATE OF status ON "user_content_restrict_ban_appeal_detail"
FOR EACH ROW
WHEN (OLD.status = 'URV' AND NEW.status IN ('REJ', 'RJR'))
EXECUTE FUNCTION insert_appeal_event_timeline('REJ');

CREATE TRIGGER user_content_restrict_ban_appeal_close_event_trigger
AFTER UPDATE OF status ON "user_content_restrict_ban_appeal_detail"
FOR EACH ROW
WHEN (OLD.status = 'URV' AND NEW.status = 'CSD')
EXECUTE FUNCTION insert_appeal_event_timeline('CLS');


/*Function and trigger to manage user_account_history*/
CREATE OR REPLACE FUNCTION update_user_account_history()
RETURNS TRIGGER AS $$
DECLARE
    attr TEXT;
    detail_type TEXT;
    event_type TEXT;
BEGIN
    IF TG_NARGS <> 1 THEN
        RAISE EXCEPTION 'Wrong number of arguments for update_user_account_history()';
    END IF;
    
    attr := TG_ARGV[0];
    
    IF attr = 'status' THEN
        IF (OLD.status = 'INA' AND NEW.status = 'ACT') AND (OLD.is_verified = FALSE AND NEW.is_verified = TRUE) THEN
            event_type := 'CRT';
        ELSIF OLD.status IN ('ACT', 'RSP', 'RSF') AND NEW.status = 'DAH' THEN
            event_type := 'DAV';
        ELSIF OLD.status IN ('ACT', 'RSP', 'RSF') AND NEW.status = 'PDH' THEN
            event_type := 'DDS';
        ELSIF OLD.status IN ('ACT', 'INA', 'DAH', 'PDH', 'RSF', 'TBN') AND NEW.status = 'RSP' THEN
            event_type := 'RSP';
        ELSIF OLD.status IN ('ACT', 'INA', 'DAH', 'PDH', 'RSP', 'TBN') AND NEW.status = 'RSP' THEN
            event_type := 'RSF';
        ELSIF OLD.status IN ('ACT', 'INA', 'RSP', 'RSF', 'DAH', 'PDH') AND NEW.status = 'TBN' THEN
            event_type := 'BNT';
        ELSIF OLD.status IN ('ACT', 'INA', 'RSP', 'RSF', 'DAH', 'PDH', 'TBN') AND NEW.status = 'PBN' THEN
            event_type := 'BNP';
        ELSIF OLD.status = 'INA' AND NEW.status = 'PDI' THEN
            event_type := 'IDS';
        ELSIF OLD.status = 'PBN' AND NEW.status = 'PDB' THEN
            event_type := 'BDS';
        ELSIF OLD.status IN ('INA', 'DAH') AND NEW.status = 'ACT' THEN
            event_type := 'RAV';
        ELSIF OLD.status = 'PDH' and NEW.status = 'ACT' THEN
            event_type := 'RST';
        ELSIF OLD.status = 'RSP' and NEW.status = 'ACT' THEN
            event_type := 'URP';
        ELSIF OLD.status = 'RSF' and NEW.status = 'ACT' THEN
            event_type := 'URF';
        ELSIF OLD.status = 'TBN' and NEW.status = 'ACT' THEN
            event_type := 'UBT';
        ELSIF OLD.status = 'PBN' and NEW.status = 'ACT' THEN
            event_type := 'UBP';
        ELSIF OLD.status IN ('PDH', 'PDI', 'PDB') AND NEW.status = 'DEL' AND NEW.is_deleted = TRUE THEN
            event_type := 'DEL';
        END IF;
        detail_type := 'Account';
    END IF;

    IF event_type IS NOT NULL THEN
        INSERT INTO "user_account_history" (account_detail_type, event_type, user_id) 
        VALUES (detail_type, event_type, OLD.id);
    END IF;

    RETURN NEW;

END;
$$ LANGUAGE plpgsql;


CREATE TRIGGER update_user_account_history_user_register_trigger
AFTER UPDATE OF status ON "user"
FOR EACH ROW
EXECUTE FUNCTION update_user_account_history('status');



/* user status DEL, is_deleted to TRUE*/
CREATE OR REPLACE FUNCTION delete_user_info_status()
RETURNS TRIGGER AS $$
DECLARE
    param INTEGER;
    user_id_param UUID;
    report_id_param UUID;
BEGIN
    IF TG_NARGS <> 1 THEN
        RAISE EXCEPTION 'Wrong number of arguments for delete_user_info_status()';
    END IF;    
    
    param := TG_ARGV[0]::INTEGER;
    user_id_param := OLD.id;
    
    IF param = 1 THEN
        IF OLD.status = 'PDH' THEN
            -- update is_active to FALSE in 'user_restrict_ban_detail' table 
            UPDATE user_restrict_ban_detail
            SET user_restrict_ban_detail.is_active = FALSE, user_restrict_ban_detail.updated_at = NOW()
            WHERE user_restrict_ban_detail.user_id = user_id_param AND user_restrict_ban_detail.is_active = TRUE;

            -- update status to CSD and moderator_note to UD in 'user_content_restrict_ban_appeal_detail' table
            UPDATE user_content_restrict_ban_appeal_detail
            SET user_content_restrict_ban_appeal_detail.status = 'CSD', user_content_restrict_ban_appeal_detail.moderator_note = 'UD', user_content_restrict_ban_appeal_detail.updated_at = NOW()
            WHERE user_content_restrict_ban_appeal_detail.user_id = user_id_param AND user_content_restrict_ban_appeal_detail.status IN ('OPN', 'URV');

            -- update status to CSD and moderator_note to UD in 'user_content_report_detail' table
            UPDATE user_content_report_detail
            SET user_content_report_detail.status = 'CSD', user_content_report_detail.moderator_note = 'UD', user_content_report_detail.updated_at = NOW()
            WHERE user_content_report_detail.user_id = user_id_param AND user_content_report_detail.status IN ('OPN', 'URV');
            
        END IF;

        -- update 'comment' table
        UPDATE comment
        SET comment.is_deleted = TRUE, comment.updated_at = NOW()
        WHERE comment.user_id = user_id_param;
        
        -- update 'comment_like' table
        UPDATE comment_like
        SET comment_like.is_deleted = TRUE, comment_like.updated_at = NOW()
        WHERE comment_like.user_id = user_id_param;
        
        -- update 'guideline_violation_score' table
        UPDATE guideline_violation_score
        SET guideline_violation_score.is_deleted = TRUE, guideline_violation_score.updated_at = NOW()
        WHERE guideline_violation_score.user_id = user_id_param;
        
        -- update 'password_change_history' table
        UPDATE password_change_history
        SET password_change_history.is_deleted = TRUE, password_change_history.updated_at = NOW()
        WHERE password_change_history.user_id = user_id_param;
        
        -- update 'post' table
        UPDATE post
        SET post.is_deleted = TRUE, post.updated_at = NOW()
        WHERE post.user_id = user_id_param;
        
        -- update 'post_like' table
        UPDATE post_like
        SET post_like.is_deleted = TRUE, post_like.updated_at = NOW()
        WHERE post_like.user_id = user_id_param;
        
        -- update 'user_auth_track' table
        UPDATE user_auth_track
        SET user_auth_track.is_deleted = TRUE, user_auth_track.updated_at = NOW()
        WHERE user_auth_track.user_id = user_id_param;
        
        -- update 'user_content_report_detail' table
        UPDATE user_content_report_detail
        SET user_content_report_detail.is_deleted = TRUE, user_content_report_detail.updated_at = NOW()
        WHERE user_content_report_detail.reporter_user_id = user_id_param;
        
        -- update 'user_content_restrict_ban_appeal_detail' table
        UPDATE user_content_restrict_ban_appeal_detail
        SET user_content_restrict_ban_appeal_detail.is_deleted = TRUE, user_content_restrict_ban_appeal_detail.updated_at = NOW()
        WHERE user_content_restrict_ban_appeal_detail.user_id = user_id_param;
        
        -- update 'user_follow_association' table
        UPDATE user_follow_association
        SET user_follow_association.is_deleted = TRUE, user_follow_association.updated_at = NOW()
        WHERE follower_user_id = user_id_param OR followed_user_id = user_id_param;
        
        -- update 'user_restrict_ban_detail' table
        UPDATE user_restrict_ban_detail
        SET user_restrict_ban_detail.is_deleted = TRUE, user_restrict_ban_detail.updated_at = NOW()
        WHERE user_restrict_ban_detail.user_id = user_id_param;
        
        -- update 'user_session' table
        UPDATE user_session
        SET user_session.is_deleted = TRUE, user_session.updated_at = NOW()
        WHERE user_session.user_id = user_id_param;
        
        -- update 'username_change_history' table
        UPDATE username_change_history
        SET username_change_history.is_deleted = TRUE, username_change_history.updated_at = NOW()
        WHERE username_change_history.user_id = user_id_param;
    
    ELSIF param = 2 THEN
        report_id_param := OLD.report_id;
        
        -- update 'guideline_violation_last_added_score' table
        UPDATE guideline_violation_last_added_score
        SET guideline_violation_last_added_score.is_deleted = TRUE, guideline_violation_last_added_score.updated_at = NOW()
        WHERE guideline_violation_last_added_score.report_id = report_id_param;
        
        -- update 'account_report_flagged_content' table
        UPDATE account_report_flagged_content
        SET account_report_flagged_content.is_deleted = TRUE, account_report_flagged_content.updated_at = NOW()
        WHERE account_report_flagged_content.report_id = report_id_param;
    
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER user_status_update_delete_one_trigger
AFTER UPDATE OF status ON "user"
FOR EACH ROW
WHEN (OLD.status IN ('PDH', 'PDI', 'PDB') AND NEW.status = 'DEL' AND NEW.is_deleted = TRUE)
EXECUTE FUNCTION delete_user_info_status(1);

/*updating guideline_violation_last_added_score and account_report_flagged_content based on report_id when is_deleted becomes TRUE*/
CREATE TRIGGER user_status_update_delete_two_trigger
AFTER UPDATE OF is_deleted ON "user_restrict_ban_detail"
FOR EACH ROW
WHEN (NEW.is_deleted = TRUE)
EXECUTE FUNCTION delete_user_info_status(2);



/*function and trigger for PDB, update is_ban_final to True for user posts/comments in Post and Comment tables*/
/*Also close all open/under review reports and appeals*/
CREATE OR REPLACE FUNCTION update_post_comment_is_ban_final()
RETURNS TRIGGER AS $$
DECLARE
    user_id_param UUID;
BEGIN
    user_id_param := OLD.id;

    -- update 'post' table
    UPDATE post
    SET post.is_ban_final = TRUE, post.updated_at = NOW()
    WHERE post.status = 'BAN' AND post.is_ban_final = FALSE AND post.user_id = user_id_param;

    -- update 'comment' table
    UPDATE comment
    SET comment.is_ban_final = TRUE, comment.updated_at = NOW()
    WHERE comment.status = 'BAN' AND comment.is_ban_final = FALSE AND comment.user_id = user_id_param;

    -- update status to CSD and moderator_note to UD in 'user_content_restrict_ban_appeal_detail' table
    UPDATE user_content_restrict_ban_appeal_detail
    SET user_content_restrict_ban_appeal_detail.status = 'CSD', user_content_restrict_ban_appeal_detail.moderator_note = 'UD', user_content_restrict_ban_appeal_detail.updated_at = NOW()
    WHERE user_content_restrict_ban_appeal_detail.user_id = user_id_param AND user_content_restrict_ban_appeal_detail.status IN ('OPN', 'URV');

    -- update status to CSD and moderator_note to UD in 'user_content_report_detail' table
    UPDATE user_content_report_detail
    SET user_content_report_detail.status = 'CSD', user_content_report_detail.moderator_note = 'UD', user_content_report_detail.updated_at = NOW()
    WHERE user_content_report_detail.user_id = user_id_param AND user_content_report_detail.status IN ('OPN', 'URV');

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER user_status_update_pdb_trigger
AFTER UPDATE OF status ON "user"
FOR EACH ROW
WHEN (OLD.status = 'PBN' and NEW.status = 'PDB')
EXECUTE FUNCTION update_post_comment_is_ban_final();


/*update post_like and comment_like when status updates in post and comment*/
CREATE OR REPLACE FUNCTION update_postlike_commentlike_status()
RETURNS TRIGGER AS $$
DECLARE
    param INTEGER;
BEGIN
    IF TG_NARGS <> 1 THEN
        RAISE EXCEPTION 'Wrong number of arguments for update_postlike_commentlike_status()';
    END IF;
    
    param := TG_ARGV[0]::INTEGER;
    
    IF TG_TABLE_NAME = 'post' THEN
        CASE param
        WHEN 1 THEN
            UPDATE post_like
            SET post_like.status = 'HID', post_like.updated_at = NOW()
            WHERE post_like.post_id = OLD.id AND post_like.status = 'ACT';
        WHEN 2 THEN
            UPDATE post_like
            SET post_like.status = 'RMV', post_like.updated_at = NOW()
            WHERE post_like.post_id = OLD.id AND post_like.status = 'ACT';
        WHEN 3 THEN
            UPDATE post_like
            SET post_like.status = 'ACT', post_like.updated_at = NOW()
            WHERE post_like.post_id = OLD.id AND post_like.status = 'HID';
        
        END CASE;
    END IF;
    
    IF TG_TABLE_NAME = 'comment' THEN
        CASE param
        WHEN 1 THEN
            UPDATE comment_like
            SET comment_like.status = 'HID', comment_like.updated_at = NOW()
            WHERE comment_like.comment_id = OLD.id AND comment_like.status = 'ACT';
        WHEN 2 THEN
            UPDATE comment_like
            SET comment_like.status = 'RMV', comment_like.updated_at = NOW()
            WHERE comment_like.comment_id = OLD.id AND comment_like.status = 'ACT';
        WHEN 3 THEN
            UPDATE comment_like
            SET comment_like.status = 'ACT', comment_like.updated_at = NOW()
            WHERE comment_like.comment_id = OLD.id AND comment_like.status = 'HID';
        
        END CASE;
    END IF;
    
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER post_status_update_ban_trigger
AFTER UPDATE OF status ON post
FOR EACH ROW
WHEN (OLD.status IN ('PUB', 'HID', 'FLB') AND NEW.status = 'BAN')
EXECUTE FUNCTION update_postlike_commentlike_status(1);

CREATE TRIGGER post_status_update_delete_trigger
AFTER UPDATE OF status ON post
FOR EACH ROW
WHEN ((OLD.status = 'FLB' AND NEW.status = 'FLD') OR (OLD.status = 'PUB' AND NEW.status = 'RMV'))
EXECUTE FUNCTION update_postlike_commentlike_status(2);

CREATE TRIGGER post_status_update_unban_trigger
AFTER UPDATE OF status ON post
FOR EACH ROW
WHEN (OLD.status = 'BAN' AND NEW.status = 'PUB')
EXECUTE FUNCTION update_postlike_commentlike_status(3);


CREATE TRIGGER comment_status_update_ban_trigger
AFTER UPDATE OF status ON comment
FOR EACH ROW
WHEN (OLD.status IN ('PUB', 'HID', 'FLB') AND NEW.status = 'BAN')
EXECUTE FUNCTION update_postlike_commentlike_status(1);

CREATE TRIGGER comment_status_update_delete_trigger
AFTER UPDATE OF status ON comment
FOR EACH ROW
WHEN ((OLD.status = 'FLB' AND NEW.status = 'FLD') OR (OLD.status = 'PUB' AND NEW.status = 'RMV'))
EXECUTE FUNCTION update_postlike_commentlike_status(2);

CREATE TRIGGER comment_status_update_unban_trigger
AFTER UPDATE OF status ON comment
FOR EACH ROW
WHEN (OLD.status = 'BAN' AND NEW.status = 'PUB')
EXECUTE FUNCTION update_postlike_commentlike_status(3);



/*getting next value from bigint sequence*/
CREATE SEQUENCE num_bigint_sequence;

CREATE OR REPLACE FUNCTION get_next_value_from_sequence()
RETURNS INTEGER AS $$
BEGIN
    RETURN nextval('num_bigint_sequence');
END;
$$ LANGUAGE plpgsql;


/*getting next value from bigint sequence*/
CREATE SEQUENCE num_bigint_sequence_ban_appeal_table;

CREATE OR REPLACE FUNCTION get_next_value_from_sequence_ban_appeal_table()
RETURNS INTEGER AS $$
BEGIN
    RETURN nextval('num_bigint_sequence_ban_appeal_table');
END;
$$ LANGUAGE plpgsql;


/*Author: Dave Allie
Link:https://blog.daveallie.com/ulid-primary-keys/
*/
CREATE OR REPLACE FUNCTION generate_ulid() RETURNS uuid
AS $$
    SELECT (lpad(to_hex(floor(extract(epoch FROM clock_timestamp()) * 1000)::bigint), 12, '0') || encode(gen_random_bytes(10), 'hex'))::uuid;
$$ LANGUAGE SQL;