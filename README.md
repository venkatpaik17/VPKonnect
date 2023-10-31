
# VPKonnect

A basic social media application. Personal project in-progress.


## Tech Stack

**Client:** HTMX, Jinja, TailwindCSS

**Server:** FastAPI, SQLAlchemy, PostgreSQL, Alembic


## Requirements

Current requirements:
- User Registration
- User Login
- User Logout
- Forgot/Reset Password
- User Profile
- Username Change
- Posting
- Likes
- Comments
- Following/Followers
- Admin Dashboard
- Delete Account
- News feed/timeline

Future Requirements (Advanced):
- Chat (messaging)
- Notifications
- Search
- Settings and Privacy
- User analytics
- Community Guidelines - Report User/Post
- Account Center
- Hashtags
- Follow Suggestions and Post Suggestions
- Tag a user
- Share Posts

## Database Relational Schema

Table: "user"
    
    id (UUID, Primary Key, Not Null)
    first_name (String, Length: 50, Not Null)
    last_name (String, Length: 50, Not Null)
    username (String, Length: 320, Unique, Not Null)
    password (String, Length: 65, Not Null)
    email (String, Length: 30, Unique, Not Null)
    date_of_birth (Date, Not Null)
    age (Integer, Not Null)
    profile_picture (String, Nullable)
    gender (String, Length: 1, Not Null)
    bio (String, Length: 150, Nullable)
    country (String, Length: 3, Nullable)
    account_visibility (Enum, Not Null)
    status (Enum, Not Null)
    type (Enum, Not Null)
    is_deleted (Boolean, Not Null)
    created_at (Timestamp, Not Null)
    updated_at (Timestamp, Nullable)
    is_verified (Boolean, Not Null)

Table: "user_follow_association"

    id (UUID, Primary Key, Not Null)
    status (Enum, Not Null)
    created_at (Timestamp, Not Null)
    follower_user_id (UUID, Primary Key, Not Null)
    followed_user_id (UUID, Primary Key, Not Null)

Table: "username_change_history"

    id (UUID, Primary Key, Not Null)
    previous_username (String, Length: 30, Not Null)
    created_at (Timestamp, Not Null)
    user_id (UUID, Not Null)

Table: "password_change_history"

    id (UUID, Primary Key, Not Null)
    created_at (Timestamp, Not Null)
    user_id (UUID, Not Null)

Table: "user_session"

    id (UUID, Primary Key, Not Null)
    device_info (String, Not Null)
    login_at (Timestamp, Not Null)
    logout_at (Timestamp, Nullable)
    user_id (UUID, Not Null)
    is_active (Boolean, Not Null)

Table: "post"

    id (UUID, Primary Key, Not Null)
    image (String, Not Null)
    caption (String, Length: 2200, Nullable)
    status (String, Length: 3, Not Null)
    is_deleted (Boolean, Not Null)
    created_at (Timestamp, Not Null)
    updated_at (Timestamp, Nullable)
    user_id (UUID, Not Null)

Table: "post_like"

    id (UUID, Unique, Not Null)
    is_deleted (Boolean, Not Null)
    created_at (Timestamp, Not Null)
    user_id (UUID, Primary Key, Not Null)
    post_id (UUID, Primary Key, Not Null)
    status (String, Length: 3, Not Null)

Table: "post_activity"

    id (UUID, Primary Key, Not Null)
    total_likes (BigInteger, Not Null)
    post_id (UUID, Not Null)

Table: "comment"

    id (UUID, Primary Key, Not Null)
    content (String, Length: 2200, Not Null)
    status (String, Length: 3, Not Null)
    is_deleted (Boolean, Not Null)
    created_at (Timestamp, Not Null)
    updated_at (Timestamp, Nullable)
    user_id (UUID, Not Null)
    post_id (UUID, Not Null)

Table: "comment_like"

    id (UUID, Unique, Not Null)
    is_deleted (Boolean, Not Null)
    created_at (Timestamp, Not Null)
    user_id (UUID, Primary Key, Not Null)
    comment_id (UUID, Primary Key, Not Null)
    status (String, Length: 3, Not Null)

Table: "comment_activity"

    id (UUID, Primary Key, Not Null)
    total_likes (BigInteger, Not Null)
    comment_id (UUID, Not Null)

Table: "user_auth_track"

    id (UUID, Primary Key, Not Null)
    refresh_token_id (String, Unique, Not Null)
    status (String, Length: 3, Not Null)
    device_info (String, Not Null)
    created_at (Timestamp, Not Null)
    updated_at (Timestamp, Nullable)
    user_id (UUID, Not Null)

Table: "user_password_reset_token"

    id (UUID, Unique, Not Null)
    reset_token_id (String, Primary Key, Not Null)
    user_id (UUID, Primary Key, Not Null)
    is_deleted (Boolean, Not Null)
    created_at (Timestamp, Not Null)

Table: "user_verification_code_token"

    id (UUID, Unique, Not Null)
    code_token_id (String, Primary Key, Not Null)
    type (String, Length: 3, Not Null)
    user_id (UUID, Primary Key, Not Null)
    is_deleted (Boolean, Not Null)
    created_at (Timestamp, Not Null)

Table: "activity_detail"

    id (UUID, Primary Key, Not Null)
    metric (String, Length: 20, Not Null)
    count (BigInteger, Not Null)
    date (Date, Not Null)
    activity_detail_metric_date_unique UniqueConstraint on (metric, date) 


## Roadmap

- First Phase*: API development (Backend), In-progress
- Second Phase: API testing
- Third Phase: Frontend development and Integration
- Fourth Phase: Application testing
- Last Phase: Deployment

## API Endpoints (Considered currently)
\# - completed 

- Root <sup>#</sup>
```
GET {URL}/
```
- User Register <sup>#</sup>
```
POST {URL}/users/register
```
- User Signup Verify <sup>#</sup>
```
POST {URL}/users/register/verify
```
- User Login <sup>#</sup>
```
POST {URL}/users/login
```
- User Logout <sup>#</sup>
```
POST {URL}/users/logout
```
- User Password Reset <sup>#</sup>
```
POST {URL}/users/password/reset
```
- User Password Change - Reset <sup>#</sup>
```
POST {URL}/users/password/change
```
- User Password Change - Update <sup>#</sup>
```
POST {URL}/users/{username}/password/change
```
- User Follow/Unfollow (Done)
```
POST {URL}/users/follow
```
- User Follow Request - Accept/Reject <sup>#</sup>
```
PUT {URL}/users/follow/requests/{username}
```
- User Followers/Following <sup>#</sup>
```
GET {URL}/users/{username}/follow
```
- User Follow Requests <sup>#</sup>
```
GET {URL}/users/{username}/follow/requests
```
- User Username Change <sup>#</sup>
```
POST {URL}/users/{username}/username/change
```
- User Account Delete <sup>#</sup>
```
PATCH {URL}/users/{username}/remove
```
- User Account Deactivate
```
PATCH {URL}/users/{username}/deactivate
```
- User Profile
```
GET {URL}/users/{username}/profile
```
- User Profile - Edit
```
PATCH {URL}/users/{username}/profile
```
- User Username Validate
```
GET {URL}/users/{username}/check
```
- User Newsfeed
```
GET {URL}/users/{username}/newsfeed
```
- User Username Change History
```
GET {URL}/users/{username}/username/change-history
```
- User Password Change History
```
GET {URL}/users/{username}/password/change-history
```
- User Sessions
```
GET {URL}/users/{username}/sessions
```
- Create a Post
```
POST {URL}/posts
```
- Get a Post
```
GET {URL}/posts/{id}
```
- Edit a Post
```
PUT {URL}/posts/{id}/edit
```
- Delete a Post
```
PUT {URL}/posts/{id}/remove
```
- User Posts
```
GET {URL}/users/{username}/posts
```
- Hidden Posts
```
GET {URL}/users/{username}/posts/hidden
```
- Draft Posts
```
GET {URL}/users/{username}/posts/drafts
```
- Like a Post
```
POST {URL}/posts/{id}/likes
```
- Comment a Post
```
POST {URL}/posts/{id}/comments
```
- Hide a Post
```
PUT {URL}/posts/{id}/hide
```
- Post Likes
```
GET {URL}/posts/{id}/likes
```
- Post Comments
```
GET {URL}/posts/{id}/comments
```
- Like a Comment
```
POST {URL}/comments/{id}/likes
```
- Edit a Comment
```
PUT {URL}/comments/{id}/edit
```
- Delete a Comment
```
PUT {URL}/comments/{id}/remove
```
- Get Users - Admin
```
GET {URL}/users
```
- Get Posts - Admin
```
GET {URL}/posts
```
- Get a User - Admin
```
GET {URL}/users/{username}
```
- Get a Comment - Admin
```
GET {URL}/comments/{id}
```
- Get App Details - Admin
```
GET {URL}/statistics
```
- Restrict/Ban User - Admin
```
PATCH {URL}/users/{username}/disable
```