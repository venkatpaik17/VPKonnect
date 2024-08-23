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
                ELSE 'Status_No_Match'
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
                ELSE 'Status_No_Match'
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
    SET status='INV', updated_at = NOW()
    WHERE status='ACT' AND user_id=OLD.user_id AND device_info=OLD.device_info;
   
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
        WHEN status = 'PUB' THEN 'HID' 
        WHEN status = 'HID' THEN 'PUB'
        ELSE status
        END,
        updated_at = NOW()
    WHERE user_id = user_id_param;

    -- Update 'comment' table
    UPDATE comment
    SET status = CASE 
        WHEN status = 'PUB' THEN 'HID' 
        WHEN status = 'HID' THEN 'PUB'
        ELSE status
        END,
        updated_at = NOW()
    WHERE user_id = user_id_param;

    -- Update 'post_like' table
    UPDATE post_like
    SET status = CASE 
        WHEN status = 'ACT' THEN 'HID' 
        WHEN status = 'HID' THEN 'ACT'
        ELSE status
        END,
        updated_at = NOW()
    WHERE user_id = user_id_param;

    -- Update 'comment_like' table
    UPDATE comment_like
    SET status = CASE 
        WHEN status = 'ACT' THEN 'HID'
        WHEN status = 'HID' THEN 'ACT'
        ELSE status
        END,
        updated_at = NOW()
    WHERE user_id = user_id_param;

    -- Update 'user_follow_association' table
    UPDATE user_follow_association
    SET status = CASE
        WHEN status = 'ACP' THEN 'HID'
        WHEN status = 'HID' THEN 'ACP'
        ELSE status
        END,
        updated_at = NOW()
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
    WHERE status='ACT' AND employee_id=OLD.employee_id AND device_info=OLD.device_info;
   
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
                    info := ' account restricted';
                ELSIF user_status = 'TBN' THEN
                    info := ' account temp banned';
                ELSIF user_status = 'PBN' THEN
                    info := ' account perm banned';
                END IF;
            ELSE
                info := report_content_type || ' removed';
            END IF;
        END;
        event := 'Resolved';
        
    ELSIF action = 'CLS' THEN
        DECLARE
            action_info TEXT;
        BEGIN
            IF report_content_type = 'account' THEN
                action_info := ' no action';
            ELSE
                IF NEW.moderator_note = 'RF' THEN
                    action_info := ' not removed';
                ELSIF NEW.moderator_note = 'RNB' THEN
                    action_info := ' already banned';
                ELSIF NEW.moderator_note = 'RNF' THEN
                    action_info := ' already flagged for future ban';
                ELSIF NEW.moderator_note = 'RND' THEN
                    action_info := ' not found';
                ELSIF NEW.moderator_note = 'RNU' THEN
                    action_info := ' user not found';
                ELSIF NEW.moderator_note = 'SE' THEN
                    action_info := ' System error';
                ELSIF NEW.moderator_note = 'UD' THEN
                    action_info := ' user deleted';
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
WHEN (OLD.status IN ('OPN', 'URV') AND NEW.status = 'CSD')
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
    report_id_var UUID;
    user_status TEXT := NULL;
BEGIN
    IF TG_NARGS <> 1 THEN
        RAISE EXCEPTION 'Wrong number of arguments for insert_appeal_event_timeline()';
    END IF;
    
    action = TG_ARGV[0];
    content_type = OLD.content_type;
    user_id_var = OLD.user_id;
    report_id_var = OLD.report_id;
    
    IF action = 'SUB' THEN
        event := 'Submitted';
        info := 'Appeal Received';
    ELSIF action = 'REV' THEN
        event := 'Under Review';
        info := 'Review in progress';
    ELSIF action = 'ACP' THEN
        IF content_type = 'account' THEN
            SELECT status INTO user_status FROM "user_restrict_ban_detail" WHERE user_id = user_id_var AND id = report_id_var;
            IF user_status = 'RSP' THEN
                info := content_type || ' partial restrict revoked';
            ELSIF user_status = 'RSF' THEN
                info := content_type || ' full restrict revoked';
            ELSIF user_status = 'TBN' THEN
                info := content_type || ' temp ban revoked';
            ELSIF user_status = 'PBN' THEN
                info := content_type || ' permnt ban revoked';
            END IF;
        ELSE
            info := content_type || ' ban revoked';
        END IF;
        
        event := 'Accepted';
    ELSIF action = 'REJ' THEN
        IF content_type = 'account' THEN
            SELECT status INTO user_status FROM "user_restrict_ban_detail" WHERE user_id = user_id_var AND id = report_id_var;
            IF user_status = 'RSP' THEN
                info := content_type || ' partial restrict not revoked';
            ELSIF user_status = 'RSF' THEN
                info := content_type || ' full restrict not revoked';
            ELSIF user_status = 'TBN' THEN
                info := content_type || ' temp ban not revoked';
            ELSIF user_status = 'PBN' THEN
                info := content_type || ' permnt ban not revoked';
            END IF;
        ELSE
            info := content_type || ' ban not revoked';
        END IF;
        
        event := 'Rejected';
    ELSIF action = 'CLS' THEN
        IF NEW.moderator_note = 'ANU' THEN
            info := content_type || ' user not found';
        ELSIF NEW.moderator_note = 'ANPC' THEN
            info := content_type || ' not found';
        ELSIF NEW.moderator_note = 'AE' THEN
            info := content_type || ' appeal expired';
        ELSIF NEW.moderator_note = 'SE' THEN
            info := content_type || ' System error';
        END IF;
        
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
WHEN (OLD.status IN ('OPN', 'URV') AND NEW.status = 'CSD')
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
            SET is_active = FALSE, updated_at = NOW()
            WHERE user_id = user_id_param AND is_active = TRUE;

            -- update status to CSD and moderator_note to UD in 'user_content_restrict_ban_appeal_detail' table
            UPDATE user_content_restrict_ban_appeal_detail
            SET status = 'CSD', moderator_note = 'UD', updated_at = NOW()
            WHERE user_id = user_id_param AND status IN ('OPN', 'URV');

            -- update status to CSD and moderator_note to UD in 'user_content_report_detail' table
            UPDATE user_content_report_detail
            SET status = 'CSD', moderator_note = 'UD', updated_at = NOW()
            WHERE user_id = user_id_param AND status IN ('OPN', 'URV');
            
        END IF;

        -- update 'comment' table
        UPDATE comment
        SET is_deleted = TRUE, updated_at = NOW()
        WHERE user_id = user_id_param;
        
        -- update 'comment_like' table
        UPDATE comment_like
        SET is_deleted = TRUE, updated_at = NOW()
        WHERE user_id = user_id_param;
        
        -- update 'guideline_violation_score' table
        UPDATE guideline_violation_score
        SET is_deleted = TRUE, updated_at = NOW()
        WHERE user_id = user_id_param;
        
        -- update 'password_change_history' table
        UPDATE password_change_history
        SET is_deleted = TRUE, updated_at = NOW()
        WHERE user_id = user_id_param;
        
        -- update 'post' table
        UPDATE post
        SET is_deleted = TRUE, updated_at = NOW()
        WHERE user_id = user_id_param;
        
        -- update 'post_like' table
        UPDATE post_like
        SET is_deleted = TRUE, updated_at = NOW()
        WHERE user_id = user_id_param;
        
        -- update 'user_auth_track' table
        UPDATE user_auth_track
        SET is_deleted = TRUE, updated_at = NOW()
        WHERE user_id = user_id_param;
        
        -- update 'user_content_report_detail' table
        UPDATE user_content_report_detail
        SET is_deleted = TRUE, updated_at = NOW()
        WHERE reporter_user_id = user_id_param;
        
        -- update 'user_content_restrict_ban_appeal_detail' table
        UPDATE user_content_restrict_ban_appeal_detail
        SET is_deleted = TRUE, updated_at = NOW()
        WHERE user_id = user_id_param;
        
        -- update 'user_follow_association' table
        UPDATE user_follow_association
        SET is_deleted = TRUE, updated_at = NOW()
        WHERE follower_user_id = user_id_param OR followed_user_id = user_id_param;
        
        -- update 'user_restrict_ban_detail' table
        UPDATE user_restrict_ban_detail
        SET is_deleted = TRUE, updated_at = NOW()
        WHERE user_id = user_id_param;
        
        -- update 'user_session' table
        UPDATE user_session
        SET is_deleted = TRUE, updated_at = NOW()
        WHERE user_id = user_id_param;
        
        -- update 'username_change_history' table
        UPDATE username_change_history
        SET is_deleted = TRUE, updated_at = NOW()
        WHERE user_id = user_id_param;
    
    ELSIF param = 2 THEN
        report_id_param := OLD.report_id;
        
        -- update 'guideline_violation_last_added_score' table
        UPDATE guideline_violation_last_added_score
        SET is_deleted = TRUE, updated_at = NOW()
        WHERE report_id = report_id_param;
        
        -- update 'account_report_flagged_content' table
        UPDATE account_report_flagged_content
        SET is_deleted = TRUE, updated_at = NOW()
        WHERE report_id = report_id_param;
    
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
    SET is_ban_final = TRUE, updated_at = NOW()
    WHERE status = 'BAN' AND is_ban_final = FALSE AND user_id = user_id_param;

    -- update 'comment' table
    UPDATE comment
    SET is_ban_final = TRUE, updated_at = NOW()
    WHERE status = 'BAN' AND is_ban_final = FALSE AND user_id = user_id_param;

    -- update status to CSD and moderator_note to UD in 'user_content_restrict_ban_appeal_detail' table
    UPDATE user_content_restrict_ban_appeal_detail
    SET status = 'CSD', moderator_note = 'UD', updated_at = NOW()
    WHERE user_id = user_id_param AND status IN ('OPN', 'URV');

    -- update status to CSD and moderator_note to UD in 'user_content_report_detail' table
    UPDATE user_content_report_detail
    SET status = 'CSD', moderator_note = 'UD', updated_at = NOW()
    WHERE user_id = user_id_param AND status IN ('OPN', 'URV');

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
            SET status = 'HID', updated_at = NOW()
            WHERE post_id = OLD.id AND status = 'ACT';
        WHEN 2 THEN
            UPDATE post_like
            SET status = 'RMV', updated_at = NOW()
            WHERE post_id = OLD.id AND status = 'ACT';
        WHEN 3 THEN
            UPDATE post_like
            SET status = 'ACT', updated_at = NOW()
            WHERE post_id = OLD.id AND status = 'HID';
        
        END CASE;
    END IF;
    
    IF TG_TABLE_NAME = 'comment' THEN
        CASE param
        WHEN 1 THEN
            UPDATE comment_like
            SET status = 'HID', updated_at = NOW()
            WHERE comment_id = OLD.id AND status = 'ACT';
        WHEN 2 THEN
            UPDATE comment_like
            SET status = 'RMV', updated_at = NOW()
            WHERE comment_id = OLD.id AND status = 'ACT';
        WHEN 3 THEN
            UPDATE comment_like
            SET status = 'ACT', updated_at = NOW()
            WHERE comment_id = OLD.id AND status = 'HID';
        
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