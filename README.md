# VPKonnect <!-- omit in toc -->

*A simple Instagram-inspired customized API project.*

## Table of Contents <!-- omit in toc -->

- [Introduction](#introduction)
  - [What is VPKonnect?](#what-is-vpkonnect)
  - [Why VPKonnect?](#why-vpkonnect)
  - [How did it start?](#how-did-it-start)
- [Functional Requirements](#functional-requirements)
- [Work Done](#work-done)
- [Project Structure](#project-structure)
  - [Some File Descriptions](#some-file-descriptions)
- [Tech Stack](#tech-stack)
- [Project Setup](#project-setup)
  - [Download and Install Docker](#download-and-install-docker)
  - [Clone the Project Repository](#clone-the-project-repository)
  - [Create Environment Variables Files](#create-environment-variables-files)
  - [Set up Mail Server for Testing (Mailtrap)](#set-up-mail-server-for-testing-mailtrap)
  - [Run the Application](#run-the-application)
  - [Access and Test the API](#access-and-test-the-api)
  - [Managing Containers](#managing-containers)
  - [Download and Install Postman](#download-and-install-postman)
  - [Import Postman Collection, Environment and Package Library](#import-postman-collection-environment-and-package-library)
  - [Install a Database Management Tool](#install-a-database-management-tool)
  - [Getting Started](#getting-started)
- [Database Schema](#database-schema)
  - [Project Database Tables Schemas](#project-database-tables-schemas)
- [Code Documentation](#code-documentation)
  - [Admin Routes](#admin-routes)
    - [Reports Dashboard](#reports-dashboard)
    - [Reports Dashboard - Admin](#reports-dashboard---admin)
    - [Get Report](#get-report)
    - [Get Related Open Reports](#get-related-open-reports)
    - [Put Reports Under Review](#put-reports-under-review)
    - [Assign Reports](#assign-reports)
    - [Close Report](#close-report)
    - [Report Action - Auto](#report-action---auto)
    - [Report Action - Manual](#report-action---manual)
    - [Appeal Dashboard - Admin](#appeal-dashboard---admin)
    - [Appeals Dashboard](#appeals-dashboard)
    - [Get Appeal](#get-appeal)
    - [Get Related Open Appeals](#get-related-open-appeals)
    - [Put Appeals Under Review](#put-appeals-under-review)
    - [Assign Appeals](#assign-appeals)
    - [Check Appeal Policy](#check-appeal-policy)
    - [Close Appeal](#close-appeal)
    - [Appeal Action](#appeal-action)
    - [Get Users - Admin](#get-users---admin)
    - [Get User - Admin](#get-user---admin)
    - [Get Posts - Admin](#get-posts---admin)
    - [Get Employees - Admin](#get-employees---admin)
    - [Get Post - Admin](#get-post---admin)
    - [Get Comment - Admin](#get-comment---admin)
    - [App Activity Metrics - Admin](#app-activity-metrics---admin)
  - [Auth Routes](#auth-routes)
    - [User Login](#user-login)
    - [Token Refresh - User](#token-refresh---user)
    - [User logout](#user-logout)
    - [Employee Login](#employee-login)
    - [Token Refresh - Employee](#token-refresh---employee)
    - [Employee Logout](#employee-logout)
  - [Comment Routes](#comment-routes)
    - [Edit Comment](#edit-comment)
    - [Remove Comment](#remove-comment)
    - [Like/Unlike Comment](#likeunlike-comment)
    - [Get Comment Like Users](#get-comment-like-users)
  - [Employee Routes](#employee-routes)
    - [Create Employee](#create-employee)
  - [Post Routes](#post-routes)
    - [Create Post](#create-post)
    - [Get Post](#get-post)
    - [Edit Post](#edit-post)
    - [Remove Post](#remove-post)
    - [Like/Unlike Post](#likeunlike-post)
    - [Get Post Like Users](#get-post-like-users)
    - [Create Comment](#create-comment)
    - [Get Post Comments](#get-post-comments)
  - [User Routes](#user-routes)
    - [Create User](#create-user)
    - [Send Verification Mail](#send-verification-mail)
    - [Verification of Registered User](#verification-of-registered-user)
    - [Password Reset](#password-reset)
    - [Password Change - Reset](#password-change---reset)
    - [Password Change - Update](#password-change---update)
    - [Follow/Unfollow User](#followunfollow-user)
    - [Accept/Reject Follow Request](#acceptreject-follow-request)
    - [Followers/Following of a User](#followersfollowing-of-a-user)
    - [Follow Requests of User](#follow-requests-of-user)
    - [Remove Follower](#remove-follower)
    - [Username Change](#username-change)
    - [User profile](#user-profile)
    - [User Posts](#user-posts)
    - [User Feed](#user-feed)
    - [Deactivate/Delete User](#deactivatedelete-user)
    - [Report item](#report-item)
    - [Appeal Content](#appeal-content)
    - [Send Ban Mail](#send-ban-mail)
    - [Send Delete Mail](#send-delete-mail)
    - [User Violation Status](#user-violation-status)
    - [About User](#about-user)
  - [Scheduled Jobs](#scheduled-jobs)
    - [Delete User After Deactivation Period Expiration](#delete-user-after-deactivation-period-expiration)
    - [Remove Restriction After Duration Expiration](#remove-restriction-after-duration-expiration)
    - [Remove Ban After Duration Expiration](#remove-ban-after-duration-expiration)
    - [User Inactivity - Delete](#user-inactivity---delete)
    - [User Inactivity - Inactive](#user-inactivity---inactive)
    - [Delete User After Permanent Ban Appeal Limit Duration Expiration](#delete-user-after-permanent-ban-appeal-limit-duration-expiration)
    - [Content Delete After Ban Appeal Limit Duration Expiration](#content-delete-after-ban-appeal-limit-duration-expiration)
    - [Close Appeal After Process Duration Expiration](#close-appeal-after-process-duration-expiration)
    - [Violation Scores Reduction - Quarterly](#violation-scores-reduction---quarterly)
  - [Operations](#operations)
    - [Appeal Accept](#appeal-accept)
    - [Appeal Reject](#appeal-reject)
    - [Consecutive Violation](#consecutive-violation)
    - [Manage User Restriction/Ban](#manage-user-restrictionban)
    - [Manage Guideline Violation Score and Last Added Score](#manage-guideline-violation-score-and-last-added-score)
    - [Manage Post/Comment](#manage-postcomment)
  - [Events](#events)
    - [Logout After User Status Specific Change](#logout-after-user-status-specific-change)
  - [Main](#main)
    - [Root Route](#root-route)
    - [Token Refresh Request Function](#token-refresh-request-function)
    - [Token Expiry Exception Handler](#token-expiry-exception-handler)
- [Project Notes](#project-notes)
  - [Consecutive Violation Actions](#consecutive-violation-actions)
  - [Check Appeal Policy](#check-appeal-policy-1)
  - [Report/Appeal Handling Flow](#reportappeal-handling-flow)
  - [User Restrictions Based on Restriction Level](#user-restrictions-based-on-restriction-level)
  - [FLB, FLD, and BAN Status for Posts/Comments](#flb-fld-and-ban-status-for-postscomments)
  - [Non-Adaptive User Restrictions (RSF/RSP)](#non-adaptive-user-restrictions-rsfrsp)
  - [Postman Testing Involving Redirection](#postman-testing-involving-redirection)
  - [Appeal Action Mechanism](#appeal-action-mechanism)
- [Project Experience, Mistakes, What Next?](#project-experience-mistakes-what-next)
  - [Experience](#experience)
  - [Mistakes](#mistakes)
  - [What Next?](#what-next)
- [Reference and Credits](#reference-and-credits)
  - [Concepts \& Implementations](#concepts--implementations)
  - [Project Structure \& Design](#project-structure--design)
  - [Authentication \& Security](#authentication--security)
  - [Libraries \& Tools](#libraries--tools)
  - [Official Documentation \& Learning Resources](#official-documentation--learning-resources)
  - [General Resources \& Community Help](#general-resources--community-help)
- [Feedback and Suggestions](#feedback-and-suggestions)


## Introduction

### What is VPKonnect?

VPKonnect is a personal project focused on developing a basic social media API, conceptually inspired from Instagram's design. This project reflects my current, limited understanding of the complexities of social media platform functionality.

### Why VPKonnect?

I started this project to gain a basic understanding of API design and implementation, while also exploring the complexities of application development. I wanted to see how different technologies connect and interact, opening myself up to new possibilities and concepts in backend development. More than that, this was my way of breaking out of the "tutorial loop". I wanted to get past the need to know everything before starting and just dive in with an idea and learn as I developed, even if it meant feeling a bit lost and uncomfortable along the way. This is a brute-force project where the focus is purely on getting things to work rather than efficiency or best practices. It has been more of a test for myself to see if I have the patience, the persistence to push through challenges, and the curiosity to keep learning as I go.

### How did it start?

It all started with a simple goal that I wanted to build an application while keeping it easy to understand and implement. I came across a Python API development tutorial by Sanjeev Thiyagarajan on FreeCodeCamp, followed along, and worked through it. After completing it, I wanted to take things a step further and build something of my own using the basics I had learned. That’s when I decided to create a basic Instagram-like backend API and named it VPKonnect. 

---

## Functional Requirements

- User Registration
- User Verification
- User Login
- User Logout
- Change/Reset Password
- User Profile
- Username Change
- Posts Management
- Likes Management
- Comments Management
- Following/Followers Management
- Admin Dashboard
- Deactivate/Delete Account
- User Feed
- Community Guidelines
  - Content Moderation
  - Reports and Appeals Management
- Employee Registration
- Mail Management
- Chat (messaging)
- Notifications
- Search
- Settings and Privacy
- User analytics
- Account Center
- Hashtags
- Follow Suggestions and Post Suggestions
- Tag a user
- Share Posts

---

## Work Done

- User Registration
- User Verification
  - JWT Token verification
- User Login
  - JWT
  - Access and Refresh Token
- User Logout
- Password Change
  - Reset - JWT Token Verification
  - Update
- User Profile
  - Basic Details
  - Posts
- Username Change
- Posts Management
  - Create (Publish/Draft), Fetch, Edit, Remove, Delete
- Likes Management
  - Like, Unlike
- Comments Management
  - Create, Fetch, Edit, Remove, Delete
- Following/Followers Management
  - Follow/Unfollow, Follow Requests (Accept/Reject), Remove Follower
- Admin Dashboard
  - Metrics
- Deactivate/Delete Account
- User Feed
  - Following Posts
- Admin Management
- Community Guidelines
  - Content Moderation
    - Types of reports
    - Severity groups/scores, Content weightage
    - Violation Scores
  - Reports and Appeals Management
    - Handling Restrictions and Bans
    - Submit, Assign, Review, Resolve, Close Reports
    - Submit, Assign, Review, Policy check, Accept, Reject Appeals
- Employee Registration
- Mail Management
  - FastApi-Mail
  - Email Testing (Mailtrap)

---

## Project Structure

```
VPKonnect
├── alembic
│   ├── versions
│   │   ├── revision_1.py
│   │   ├── revision_2.py
│   │   └── ...
│   ├── env.py
│   ├── README
│   └── script.py.mako
├── app
│   ├── api
│   │   ├── v0
│   │   │   ├── routes
│   │   │   │   ├── __init__.py
│   │   │   │   ├── admin.py
│   │   │   │   ├── auth.py
│   │   │   │   ├── comment.py
│   │   │   │   ├── employee.py
│   │   │   │   ├── post.py
│   │   │   │   └── user.py
│   │   │   ├── __init__.py
│   │   │   └── api_routes.py
│   │   ├── __init__.py
│   ├── config
│   │   ├── __init__.py
│   │   ├── app.py
│   │   ├── base.py
│   │   ├── email.py
│   │   └── log_config.json
│   ├── db
│   │   ├── __init__.py
│   │   ├── db_sqlalchemy.py
│   │   └── session.py
│   ├── init_sql
│   │   └── init_function.sql
│   ├── logs
│   ├── models
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── auth.py
│   │   ├── comment.py
│   │   ├── employee.py
│   │   ├── post.py
│   │   └── user.py
│   ├── schemas
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── auth.py
│   │   ├── comment.py
│   │   ├── employee.py
│   │   ├── post.py
│   │   └── user.py
│   ├── services
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── auth.py
│   │   ├── comment.py
│   │   ├── employee.py
│   │   ├── post.py
│   │   └── user.py
│   ├── sql
│   │   └── function_trigger.sql
│   ├── templates
│   │   └── [HTML files for email body]
│   ├── utils
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── basic.py
│   │   ├── email.py
│   │   ├── enum.py
│   │   ├── event.py
│   │   ├── exception.py
│   │   ├── image.py
│   │   ├── job_task.py
│   │   ├── log.py
│   │   ├── map.py
│   │   ├── operation.py
│   │   ├── password.py
│   ├── __init__.py
│   └── main.py
├── images
│   ├── employee
│   └── user
├── Postman
|   ├── package.js
|   ├── VPKonnect.postman_collection.json
|   └── VPKonnect.postman_environment.json
├── tests
│   ├── test_v0_endpoints
│   │   └── __init__.py
│   └── __init__.py
├── .app.env
├── .dockerignore
├── .env
├── .gitattributes
├── .gitignore
├── alembic.ini
├── docker-compose.yml
├── Dockerfile
├── entrypoint.sh
├── README.md
├── requirements.txt
└── vpkonnect.png
```

### Some File Descriptions

- **`app/init_sql/init_function.sql`** – Contains SQL functions and plugins setup required for future database operations.  
- **`package.js`** - Custom package library for some Postman operations.  
- **`.app.env`** – Defines environment variables specifically for application settings.  
- **`.env`** – Stores environment variables for Docker Compose configurations.  
- **`entrypoint.sh`** – Executes necessary operations before starting the application, including:  
  - Checking PostgreSQL status  
  - Handling Alembic migrations  
  - Running required SQL scripts  
- **`vpkonnect.png`** – Application logo.  

---

## Tech Stack

>[!WARNING]
> PostgreSQL 12.xx is deprecated and hence no longer available on Docker Hub. While PostgreSQL 13 is a viable alternative, it hasn’t been integrated yet. For now, the Docker setup pulls the required version from a private registry to prevent compatibility issues. Once the application is tested and verified on PostgreSQL 13, the repository will be updated accordingly.

- **Python 3.10.13/3.10.16**
- **FastAPI 0.100.0**
- **PostgreSQL 12.19/12.22**
- **SQLAlchemy 1.4.49**
- **Alembic 1.11.2**
- **pgAdmin4 8.xx/9.xx**
- **Postman**

---

## Project Setup

### Download and Install Docker
- **Docker Engine (Linux):** 
  - [Install Guide](https://docs.docker.com/engine/install/)
- **Docker Desktop (Windows and macOS):**  
  - [Windows Install Guide](https://docs.docker.com/desktop/setup/install/windows-install/)  
  - [Mac Install Guide](https://docs.docker.com/desktop/setup/install/mac-install/) <br>

### Clone the Project Repository

>[!NOTE]
> Remove the **dummy.txt** files from `./images/user/`, `./images/employee/`, and `./app/logs/`

```sh
# choose any one
git clone https://github.com/venkatpaik17/VPKonnect.git     # clone over HTTPS
git clone git@github.com:venkatpaik17/VPKonnect.git      # clone over SSH

cd VPKonnect/
```

### Create Environment Variables Files

>[!NOTE]
>- Add in your own values here.  
>- For secret keys (`ACCESS_TOKEN_SECRET_KEY`, `REFRESH_TOKEN_SECRET_KEY`, `RESET_TOKEN_SECRET_KEY`, `USER_VERIFY_TOKEN_SECRET_KEY`), you can generate it using 
>`openssl rand -hex 32`
>- Email credentials can be obtained from mail servers, you can use [Mailtrap for Email Testing](#set-up-mail-server-for-testing-mailtrap)
     
  - `.app.env` for app environment variables  

      ```sh
         APP_ENVIRONMENT=dev
         DATABASE_USERNAME=<db_username>
         DATABASE_PASSWORD=<db_password>
         DATABASE_NAME=<db_name>
         DATABASE_HOSTNAME=db    # postgres db service name in docker-compose.yml
         DATABASE_PORT=5432
         ALLOWED_CORS_ORIGIN=http://localhost:8000,http://127.0.0.1:8000
         ACCESS_TOKEN_SECRET_KEY=<secret_key>
         REFRESH_TOKEN_SECRET_KEY=<secret_key>
         TOKEN_ALGORITHM=HS256
         ACCESS_TOKEN_EXPIRE_MINUTES=<expire_minutes>    # ex: 20
         REFRESH_TOKEN_EXPIRE_MINUTES=<expire_minutes>   # ex: 120
         EMAIL_HOST=<mail_host>
         EMAIL_PORT=<mail_port>
         EMAIL_USERNAME=<mail_username>
         EMAIL_PASSWORD=<mail_password>
         EMAIL_FROM=admin@vpkonnect.in
         RESET_TOKEN_SECRET_KEY=<secret_key>
         RESET_TOKEN_EXPIRE_MINUTES=<expire_minutes>     # ex: 60
         USER_VERIFY_TOKEN_SECRET_KEY=<secret_key>
         USER_VERIFY_TOKEN_EXPIRE_MINUTES=<expire_minutes>     #ex: 60
         IMAGE_MAX_SIZE=5242880  # 5MB
         TTLCACHE_MAX_SIZE=1000  # customise
      ```

  - `.env` for docker compose database service environment variables  

      ```sh
         DATABASE_USERNAME=<db_username>
         DATABASE_PASSWORD=<db_password>
         DATABASE_NAME=<db_name>
      ```

### Set up Mail Server for Testing (Mailtrap)
  - **Sign up:** [Mailtrap](https://mailtrap.io/)  
  - **Setup Guide:** [Mailtrap Setup Guide](https://help.mailtrap.io/article/109-getting-started-with-mailtrap-email-testing)  

### Run the Application
```sh
docker compose up -d
```
- `-d`: Runs in detached mode (background)

### Access and Test the API
  - **Root API Endpoint:**  
  ```
  http://127.0.0.1:8000/api/v0/
  ```

### Managing Containers

```sh
# View Running Containers
docker compose ps -a

# Stop Services
docker compose stop

# Restart Services
docker compose restart

# Shut Down and Remove Containers/Volumes
docker compose down -v

# View Logs
docker compose logs -f    # Logs for all services
docker compose logs <service-name> -f  # Logs for a specific service

# Access Running Containers
docker compose exec <service-name> /bin/bash
docker exec -it <container-name> /bin/bash
```

- `-a`: List all containers 
- `-v`: Volumes  
- `-f`: Follow mode, real-time log streaming  
- `-i`: Interactive, interact with container
- `-t`: TTY (terminal), pseudo-terminal insider container


### Download and Install Postman
- [Postman Download](https://www.postman.com/downloads/)

### Import Postman Collection, Environment and Package Library

>[!IMPORTANT]
> 1. Postman requires **Account Sign-In** to access collections and environments.
> 2. If you find other alternatives to Postman that are compatible with Postman collections, environments, and package scripts, you can use those as well.

  1. Open Postman -> Create Account/Sign-In.
  2. Create New Workspace.
  3. Click on **Import** button on the top-left side of the app screen.
  4. Select the files `VPKonnect.postman_collection.json` and `VPKonnect.postman_environment.json` from the [Postman folder](./Postman/) and import.
  5. You can now access APIs and Environment.
  6. Go to Collections, click on any request which has scripts (Ex: User Register).
  7. Go to **Scripts** tab, on the right side, click on **Open package library**.
  8. Click on **New Package** to create a package, name it `vpkonnect_scripts`.
  9. Copy the JS code from [package.js](./Postman/package.js) to `vpkonnect_scripts` package and Save.
  10. Click the **No environment** dropdown on top-right side of the app screen and select **VPKonnect** from the list.

### Install a Database Management Tool
- **pgAdmin 4:** [Download](https://www.pgadmin.org/download/)  
- **Alternative:** DBeaver or any other PostgreSQL client

Open pgAdmin 4 -> Servers -> Register. Add details and connect to database  

### Getting Started

> [!NOTE] 
> 1. Read [Project Notes](#project-notes)
> 2. Refer [Full API Documentation (Redoc)](https://venkatpaik17.github.io/VPKonnect/)
> 3. Refer [schemas](app/schemas/), [enum.py](app/utils/enum.py), and [map.py](app/utils/map.py) for certain column attributes and other route parameters.  
> 4. Refer [init_function.sql](app/init_sql/init_function.sql), and [function_trigger.sql](app/sql/function_trigger.sql) for sql functions and triggers.  
> 5. While testing APIs in Postman, you can monitor the execution of pre-request and post-response scripts using the *Console* located at the bottom-left of the Postman app.

#### User & Employee Registration <!-- omit in toc -->
- **Register New Users**  
  - Create multiple user accounts with different privacy settings (public/private).  
- **Register New Employees**  
  - Add Content Moderator Admins and Content Moderators.  
  - Use the Aadhaar generation code to get valid Aadhaar numbers for registration (to mimic real-world validation).  

#### Social & Content Interactions <!-- omit in toc -->
- **Create Posts & Comments**    
- **Like Posts & Comments**    
- **Follow Other Users**  
  - Test follow/unfollow mechanics for both public and private accounts.  

#### Content Moderation & Appeals <!-- omit in toc -->
- **Report & Appeal Content**  
  - Submit different types of reports.  
  - Test report and appeal system considering various scenarios.

#### Database Experimentation & Scheduled Jobs <!-- omit in toc -->
- **Manually Modify Certain Columns to Experiment with Different Scenarios**  
  - Directly update database fields (e.g., user restrictions, post status, violation duration).  
- **Test Scheduled Jobs**  
  - Set specific scenarios and test the scheduled jobs.

---

## Database Schema

### Project Database Tables Schemas

``` sql
account_report_flagged_content:
    id (UUID, PRIMARY KEY, default: generate_ulid())
    valid_flagged_content (UUID, NOT NULL)
    report_id (UUID, NOT NULL, FOREIGN KEY referencing user_content_report_detail(id) ON DELETE CASCADE)
    is_deleted (BOOLEAN, NOT NULL, default: False)
    created_at (TIMESTAMP WITH TIME ZONE, NOT NULL, default: NOW())

activity_detail:
    id (UUID, PRIMARY KEY, default: generate_ulid())
    metric (VARCHAR(50), NOT NULL)
    count (BIGINT, NOT NULL, default: 0)
    date (DATE, NOT NULL, default: now())
    UNIQUE (metric, date)

comment:
    id (UUID, PRIMARY KEY, default: generate_ulid())
    content (VARCHAR(2200), NOT NULL)
    status (VARCHAR(3), NOT NULL, default: 'PUB')
    is_deleted (BOOLEAN, NOT NULL, default: False)
    created_at (TIMESTAMP WITH TIME ZONE, NOT NULL, default: NOW())
    updated_at (TIMESTAMP WITH TIME ZONE)
    user_id (UUID, NOT NULL, FOREIGN KEY referencing user(id) ON DELETE CASCADE)
    post_id (UUID, NOT NULL, FOREIGN KEY referencing post(id) ON DELETE CASCADE)
    is_ban_final (BOOLEAN, NOT NULL, default: False)

comment_like:
    id (UUID, PRIMARY KEY, default: generate_ulid())
    is_deleted (BOOLEAN, NOT NULL, default: False)
    created_at (TIMESTAMP WITH TIME ZONE, NOT NULL, default: NOW())
    user_id (UUID, NOT NULL, FOREIGN KEY referencing user(id) ON DELETE CASCADE)
    comment_id (UUID, NOT NULL, FOREIGN KEY referencing comment(id) ON DELETE CASCADE)
    status (VARCHAR(3), NOT NULL, default: 'ACT')
    updated_at (TIMESTAMP WITH TIME ZONE)
    UNIQUE (user_id, comment_id, status, created_at)

employee:
    id (UUID, PRIMARY KEY, default: generate_ulid())
    emp_id (VARCHAR(16), NOT NULL, UNIQUE)
    first_name (VARCHAR(50), NOT NULL)
    last_name (VARCHAR(50), NOT NULL)
    password (VARCHAR(65), NOT NULL)
    personal_email (VARCHAR(320), NOT NULL, UNIQUE)
    work_email (VARCHAR(320), NOT NULL, UNIQUE)
    country_phone_code (VARCHAR(10), NOT NULL)
    phone_number (VARCHAR(12), NOT NULL)
    date_of_birth (DATE, NOT NULL)
    age (INTEGER, NOT NULL)
    profile_picture (VARCHAR)
    gender (VARCHAR(1), NOT NULL)
    aadhaar (VARCHAR(12), NOT NULL, UNIQUE)
    pan (VARCHAR(10), NOT NULL, UNIQUE)
    address_line_1 (TEXT, NOT NULL)
    address_line_2 (TEXT)
    city (VARCHAR, NOT NULL)
    state_province (VARCHAR, NOT NULL)
    zip_postal_code (VARCHAR(16), NOT NULL)
    country (VARCHAR(3), NOT NULL)
    join_date (DATE, NOT NULL)
    termination_date (DATE)
    status (VARCHAR(3), NOT NULL, default: 'ACP')
    type (VARCHAR(3), NOT NULL)
    designation (VARCHAR(10), NOT NULL)
    supervisor_id (UUID, FOREIGN KEY referencing employee(id) ON DELETE CASCADE)
    is_deleted (BOOLEAN, NOT NULL, default: False)
    created_at (TIMESTAMP WITH TIME ZONE, NOT NULL, default: NOW())
    updated_at (TIMESTAMP WITH TIME ZONE)

employee_auth_track:
    id (UUID, PRIMARY KEY, default: generate_ulid())
    refresh_token_id (VARCHAR, NOT NULL, UNIQUE)
    status (VARCHAR(20), NOT NULL, default: 'ACT')
    device_info (VARCHAR, NOT NULL)
    created_at (TIMESTAMP WITH TIME ZONE, NOT NULL, default: NOW())
    updated_at (TIMESTAMP WITH TIME ZONE)
    employee_id (UUID, NOT NULL, FOREIGN KEY referencing employee(id) ON DELETE CASCADE)
    is_deleted (BOOLEAN, NOT NULL, default: False)

employee_session:
    id (UUID, PRIMARY KEY, default: generate_ulid())
    device_info (VARCHAR, NOT NULL)
    login_at (TIMESTAMP WITH TIME ZONE, NOT NULL, default: NOW())
    logout_at (TIMESTAMP WITH TIME ZONE)
    employee_id (UUID, NOT NULL, FOREIGN KEY referencing employee(id) ON DELETE CASCADE)
    is_active (BOOLEAN, NOT NULL, default: True)
    is_deleted (BOOLEAN, NOT NULL, default: False)

guideline_violation_last_added_score:
    id (UUID, PRIMARY KEY, default: generate_ulid())
    last_added_score (INTEGER, NOT NULL)
    is_removed (BOOLEAN, NOT NULL, default: False)
    is_deleted (BOOLEAN, NOT NULL, default: False)
    score_id (UUID, NOT NULL, FOREIGN KEY referencing guideline_violation_score(id) ON DELETE CASCADE)
    report_id (UUID, NOT NULL, FOREIGN KEY referencing user_content_report_detail(id) ON DELETE CASCADE)
    created_at (TIMESTAMP WITH TIME ZONE, NOT NULL, default: NOW())
    updated_at (TIMESTAMP WITH TIME ZONE)
    is_added (BOOLEAN, NOT NULL, default: True)

guideline_violation_score:
    id (UUID, PRIMARY KEY, default: generate_ulid())
    post_score (INTEGER, NOT NULL, default: 0)
    comment_score (INTEGER, NOT NULL, default: 0)
    message_score (INTEGER, NOT NULL, default: 0)
    final_violation_score (INTEGER, NOT NULL, default: 0)
    user_id (UUID, NOT NULL, FOREIGN KEY referencing user(id) ON DELETE CASCADE)
    created_at (TIMESTAMP WITH TIME ZONE, NOT NULL, default: NOW())
    updated_at (TIMESTAMP WITH TIME ZONE)
    is_deleted (BOOLEAN, NOT NULL, default: False)

password_change_history:
    id (UUID, PRIMARY KEY, default: generate_ulid())
    created_at (TIMESTAMP WITH TIME ZONE, NOT NULL, default: NOW())
    user_id (UUID, NOT NULL, FOREIGN KEY referencing user(id) ON DELETE CASCADE)
    is_deleted (BOOLEAN, NOT NULL, default: False)

post:
    id (UUID, PRIMARY KEY, default: generate_ulid())
    image (VARCHAR, NOT NULL)
    caption (VARCHAR(2200))
    status (VARCHAR(3), NOT NULL)
    is_deleted (BOOLEAN, NOT NULL, default: False)
    created_at (TIMESTAMP WITH TIME ZONE, NOT NULL, default: NOW())
    updated_at (TIMESTAMP WITH TIME ZONE)
    user_id (UUID, NOT NULL, FOREIGN KEY referencing user(id) ON DELETE CASCADE)
    is_ban_final (BOOLEAN, NOT NULL, default: False)

post_like:
    id (UUID, PRIMARY KEY, default: generate_ulid())
    is_deleted (BOOLEAN, NOT NULL, default: False)
    created_at (TIMESTAMP WITH TIME ZONE, NOT NULL, default: NOW())
    user_id (UUID, NOT NULL, FOREIGN KEY referencing user(id) ON DELETE CASCADE)
    post_id (UUID, NOT NULL, FOREIGN KEY referencing post(id) ON DELETE CASCADE)
    status (VARCHAR(3), NOT NULL, default: 'ACT')
    updated_at (TIMESTAMP WITH TIME ZONE)
    UNIQUE (user_id, post_id, status, created_at)

user:
    id (UUID, PRIMARY KEY, default: generate_ulid())
    first_name (VARCHAR(50), NOT NULL)
    last_name (VARCHAR(50), NOT NULL)
    username (VARCHAR(30), NOT NULL, UNIQUE)
    password (VARCHAR(65), NOT NULL)
    email (VARCHAR(320), NOT NULL, UNIQUE)
    date_of_birth (DATE, NOT NULL)
    age (INTEGER, NOT NULL)
    profile_picture (VARCHAR)
    gender (VARCHAR(1), NOT NULL)
    bio (VARCHAR(150))
    country (VARCHAR(3))
    account_visibility (VARCHAR(3), NOT NULL, default: 'PBC')
    status (VARCHAR(3), NOT NULL, default: 'INA')
    type (VARCHAR(3), NOT NULL, default: 'STD')
    is_deleted (BOOLEAN, NOT NULL, default: False)
    created_at (TIMESTAMP WITH TIME ZONE, NOT NULL, default: NOW())
    updated_at (TIMESTAMP WITH TIME ZONE)
    is_verified (BOOLEAN, NOT NULL, default: False)
    repr_id (UUID, NOT NULL)
    inactive_delete_after (INTEGER, NOT NULL, default: 183)
    country_phone_code (VARCHAR(10))
    phone_number (VARCHAR(12))

user_account_history:
    id (UUID, PRIMARY KEY, default: generate_ulid())
    account_detail_type (VARCHAR, NOT NULL)
    event_type (VARCHAR, NOT NULL)
    new_detail_value (VARCHAR)
    previous_detail_value (VARCHAR)
    user_id (UUID, NOT NULL, FOREIGN KEY referencing user(id) ON DELETE CASCADE)
    created_at (TIMESTAMP WITH TIME ZONE, NOT NULL, default: NOW())
    is_deleted (BOOLEAN, NOT NULL, default: False)

user_auth_track:
    id (UUID, PRIMARY KEY, default: generate_ulid())
    refresh_token_id (VARCHAR, NOT NULL, UNIQUE)
    status (VARCHAR(3), NOT NULL, default: 'ACT')
    device_info (VARCHAR, NOT NULL)
    created_at (TIMESTAMP WITH TIME ZONE, NOT NULL, default: NOW())
    updated_at (TIMESTAMP WITH TIME ZONE)
    user_id (UUID, NOT NULL, FOREIGN KEY referencing user(id) ON DELETE CASCADE)
    is_deleted (BOOLEAN, NOT NULL, default: False)

user_content_report_detail:
    id (UUID, PRIMARY KEY, default: generate_ulid())
    reporter_user_id (UUID, NOT NULL, FOREIGN KEY referencing user(id) ON DELETE CASCADE)
    reported_item_id (UUID, NOT NULL)
    reported_item_type (VARCHAR, NOT NULL)
    reported_user_id (UUID, NOT NULL, FOREIGN KEY referencing user(id) ON DELETE CASCADE)
    case_number (BIGINT, NOT NULL, UNIQUE, default: get_next_value_from_sequence())
    report_reason (VARCHAR(10), NOT NULL)
    report_reason_user_id (UUID, FOREIGN KEY referencing user(id) ON DELETE CASCADE)
    status (VARCHAR(3), NOT NULL, default: 'OPN')
    moderator_note (VARCHAR)
    is_deleted (BOOLEAN, NOT NULL, default: False)
    created_at (TIMESTAMP WITH TIME ZONE, NOT NULL, default: NOW())
    updated_at (TIMESTAMP WITH TIME ZONE)
    moderator_id (UUID, FOREIGN KEY referencing employee(id) ON DELETE CASCADE)

user_content_report_event_timeline:
    id (UUID, PRIMARY KEY, default: generate_ulid())
    event_type (VARCHAR, NOT NULL)
    created_at (TIMESTAMP WITH TIME ZONE, NOT NULL, default: NOW())
    detail (VARCHAR)
    report_id (UUID, NOT NULL, FOREIGN KEY referencing user_content_report_detail(id) ON DELETE CASCADE)

user_content_restrict_ban_appeal_detail:
    id (UUID, PRIMARY KEY, default: generate_ulid())
    case_number (BIGINT, NOT NULL, UNIQUE, default: get_next_value_from_sequence_ban_appeal_table())
    user_id (UUID, NOT NULL, FOREIGN KEY referencing user(id) ON DELETE CASCADE)
    report_id (UUID, NOT NULL, FOREIGN KEY referencing user_content_report_detail(id) ON DELETE CASCADE)
    content_type (VARCHAR, NOT NULL)
    content_id (UUID, NOT NULL)
    appeal_detail (VARCHAR, NOT NULL)
    attachment (VARCHAR)
    status (VARCHAR(3), NOT NULL, default: 'OPN')
    moderator_id (UUID, FOREIGN KEY referencing employee(id) ON DELETE CASCADE)
    moderator_note (VARCHAR)
    is_deleted (BOOLEAN, NOT NULL, default: False)
    created_at (TIMESTAMP WITH TIME ZONE, NOT NULL, default: NOW())
    updated_at (TIMESTAMP WITH TIME ZONE)
    is_policy_followed (BOOLEAN)

user_content_restrict_ban_appeal_event_timeline:
    id (UUID, PRIMARY KEY, default: generate_ulid())
    event_type (VARCHAR, NOT NULL)
    created_at (TIMESTAMP WITH TIME ZONE, NOT NULL, default: NOW())
    detail (VARCHAR)
    appeal_id (UUID, NOT NULL, FOREIGN KEY referencing user_content_restrict_ban_appeal_detail(id) ON DELETE CASCADE)

user_follow_association:
    id (UUID, PRIMARY KEY, default: generate_ulid())
    status (VARCHAR(3), NOT NULL)
    created_at (TIMESTAMP WITH TIME ZONE, NOT NULL, default: NOW())
    follower_user_id (UUID, NOT NULL, FOREIGN KEY referencing user(id) ON DELETE CASCADE)
    followed_user_id (UUID, NOT NULL, FOREIGN KEY referencing user(id) ON DELETE CASCADE)
    is_deleted (BOOLEAN, NOT NULL, default: False)
    updated_at (TIMESTAMP WITH TIME ZONE)
    UNIQUE (follower_user_id, followed_user_id, status, created_at)

user_restrict_ban_detail:
    id (UUID, PRIMARY KEY, default: generate_ulid())
    status (VARCHAR(3), NOT NULL)
    duration (INTEGER, NOT NULL)
    user_id (UUID, NOT NULL, FOREIGN KEY referencing user(id) ON DELETE CASCADE)
    created_at (TIMESTAMP WITH TIME ZONE, NOT NULL, default: NOW())
    updated_at (TIMESTAMP WITH TIME ZONE)
    is_deleted (BOOLEAN, NOT NULL, default: False)
    is_active (BOOLEAN, NOT NULL, default: True)
    content_type (VARCHAR, NOT NULL)
    content_id (UUID, NOT NULL)
    report_id (UUID, NOT NULL, FOREIGN KEY referencing user_content_report_detail(id) ON DELETE CASCADE)
    enforce_action_at (TIMESTAMP WITH TIME ZONE)
    is_enforce_action_early (BOOLEAN, NOT NULL, default: False)

user_session:
    id (UUID, PRIMARY KEY, default: generate_ulid())
    device_info (VARCHAR, NOT NULL)
    login_at (TIMESTAMP WITH TIME ZONE, NOT NULL, default: NOW())
    logout_at (TIMESTAMP WITH TIME ZONE)
    user_id (UUID, NOT NULL, FOREIGN KEY referencing user(id) ON DELETE CASCADE)
    is_active (BOOLEAN, NOT NULL, default: True)
    is_deleted (BOOLEAN, NOT NULL, default: False)

user_verification_code_token:
    id (UUID, UNIQUE, NOT NULL, default: generate_ulid())
    code_token_id (VARCHAR, PRIMARY KEY)
    type (VARCHAR(3), NOT NULL)
    user_id (UUID, PRIMARY KEY, FOREIGN KEY referencing user(id) ON DELETE CASCADE)
    is_deleted (BOOLEAN, NOT NULL, default: False)
    created_at (TIMESTAMP WITH TIME ZONE, NOT NULL, default: NOW())

username_change_history:
    id (UUID, PRIMARY KEY, default: generate_ulid())
    previous_username (VARCHAR(30), NOT NULL)
    created_at (TIMESTAMP WITH TIME ZONE, NOT NULL, default: NOW())
    user_id (UUID, NOT NULL, FOREIGN KEY referencing user(id) ON DELETE CASCADE)
    is_deleted (BOOLEAN, NOT NULL, default: False)
```

---


## Code Documentation

### Admin Routes

#### Reports Dashboard

- **Access Control**   

   This endpoint requires the user to have one of the following roles:
   - **content_admin**
   - **content_mgmt**

- **Abstract Pseudocode for `get_reports_dashboard`** 

  1. **Initialize Function**:  
     - Accept status (optional, `open`, `closed`, `review`, `resolved`, `future_resolved`), database session, and current employee as inputs.

  2. **Validate Report Status**:
     - If a report status is provided in the request, transform it to its code form.
     - If status is invalid or cannot be transformed, raise a bad request error.

  3. **Fetch Current Employee**:
     - Query the database to fetch the current employee using the work email.
     - Ensure that the employee is not suspended or terminated.

  4. **Fetch Reports**:
     - Query the database to fetch the reports based on the provided report status and the current employee as the moderator.
     - If no reports are found, return an empty list.

  5. **Format Report Details**:
     - Prepare the report response containing case number, status and reported at.
     - Do this for all the fetched reports.

  6. **Return Response**:
     - Provide the response containing the list of reports.

- **API Documentation** 

  [Get Resports Dashboard Doc](https://venkatpaik17.github.io/VPKonnect/#tag/Admin/operation/get_reports_dashboard_api_v0_admin_reports_dashboard_get)

- **Database Tables Affected and Triggers involved** 

  *(NA)*

- **Postman Scripts Flow**  
   - **Pre-request**: 
     1. Manage Authorization
        - Gets the value of the `JWT` environment variable.
        - If the `JWT` variable is empty or doesn't exist, removes the `Authorization` header from the request.

   - **Post-response**: 
     1. Set New Access Token
        - Parse Response JSON.
        - Checks if the response code is 200 (OK) and the response contains an access_token.
        - If both are true, saves the access_token to the `JWT` environment variable, and indicates to resend the request.

<br>

#### Reports Dashboard - Admin

- **Access Control** 

   This endpoint requires the user to have one of the following roles:
   - **content_admin**

- **Abstract Pseudocode for `get_reports_admin_dashboard`** 

  1. **Initialize Function**:  
     - Accept type (`new`, `assigned`), status (optional, `open`, `closed`, `review`, `resolved`, `future_resolved`), emp ID, reported date, database session, and current employee as inputs.

  2. **Validate Parameters**:  
     - Check if the status and type combination is valid. If status is not `open` and type is `new`, raise a bad request error, indicating invalid type for status.
     - If type is `new` and emp ID is provided, raise a bad request error, indicating it is invalid to provide emp ID for new type.

  3. **Transform Report Status**:  
     - If status is provided in the request, transform it to its code form.
     - If status is invalid or cannot be transformed, raise a bad request error.

  4. **Fetch Moderator (if applicable)**:
     - If emp ID is provided:
       - Query the database to fetch the current employee using the emp ID.
       - Ensure that the employee is not suspended or terminated.

  5. **Fetch Reports**:  
     - Query the database to fetch the reports based on the provided report status, type, moderator, and reported date.
     - If no reports are found, return an empty list.

  6. **Format Report Details**:  
     - Prepare the report response containing case number, status and reported at.
     - Do this for all the fetched reports.

  7. **Return Response**:  
     - Provide the response containing the list of reports.

- **API Documentation** 

   [Get Reports Admin Dashboard Doc](https://venkatpaik17.github.io/VPKonnect/#tag/Admin/operation/get_reports_admin_dashboard_api_v0_admin_reports_admin_dashboard_get)

- **Database Tables Affected and Triggers involved** 

   *(NA)*

- **Postman Scripts Flow**   
  - **Pre-request**: 
    1. Manage Authorization
       - Gets the value of the `JWT` environment variable.
       - If the `JWT` variable is empty or doesn't exist, removes the `Authorization` header from the request.

  - **Post-response**: 
    1. Set New Access Token
       - Parse Response JSON.
       - Checks if the response code is `200 (OK)` and the response contains an access_token.
       - If both are true, saves the access_token to the `JWT` environment variable, and indicates to resend the request.

<br>

#### Get Report

- **Access Control** 

   This endpoint requires the user to have one of the following roles:
   - **content_admin**
   - **content_mgmt**

- **Abstract Pseudocode for `get_requested_report`** 

  1. **Initialize Function**:
     - Accept case number, database session, and current employee as inputs.

  2. **Fetch Report**:
     - Query the database to fetch the report using the provided case number.
     - If no report is found, raise a not found error.

  3. **Authorization Check**:
     - If the report is open and currently unassigned, only content admin can access the report.
     - If the current employee's role is not content admin, raise an unauthorized error.

  4. **Fetch Flagged/Banned Posts for Account Report (if applicable)**:
     - If the reported item type is `account` and the report is resolved/resolved related/future resolved/future resolved related:
       - Query the database to fetch all valid flagged content(posts) related to the account report.
       - If no posts are found, raise a not found error.

  5. **Prepare Report Data**:
     - Create the report data dictionary including case number, reporter and reported user details, reported item type and details, flagged/banned posts IDs, report reason, report reason user(impersonation), status, moderator note, account restriction/ban, effective user status, moderator details, reported at and last updated at.

  6. **Return Response**:
     - Parse the dictionary into the response schema and return the response with the report details.

- **API Documentation** 

   [Get Requested Report Doc](https://venkatpaik17.github.io/VPKonnect/#tag/Admin/operation/get_requested_report_api_v0_admin_reports__case_number__get)

- **Database Tables Affected and Triggers involved** 

   *(NA)*

- **Postman Scripts Flow** 
  - **Pre-request**: 
    1. Manage Authorization
       - Gets the value of the `JWT` environment variable.
       - If the `JWT` variable is empty or doesn't exist, removes the `Authorization` header from the request.

  - **Post-response**: 
    1. Set New Access Token
       - Parse Response JSON.
       - Checks if the response code is `200 (OK)` and the response contains an access_token.
       - If both are true, saves the access_token to the `JWT` environment variable, and indicates to resend the request.

<br>

#### Get Related Open Reports 

- **Access Control** 

   This endpoint requires the user to have one of the following roles:
   - **content_admin**
   - **content_mgmt**

- **Abstract Pseudocode for `get_all_related_open_reports_for_specific_report`** 

  1. **Initialize Function**:  
     - Accept case number, admin flag, database session, and current employee as inputs.

  2. **Fetch Current Employee**:  
     - Query the database to fetch the current employee using their work email.  
     - Ensure that the employee is not suspended or terminated.

  3. **Process Flow**:  
     - If the admin flag is true:
       - Query the database to fetch the report by case number with status open.
       - If the report is not found, raise a not found error.
       - If the report is already assigned to a moderator, raise a conflict error. 
     - If the admin flag is false:
       - Use the current employee's ID as the moderator ID.
       - Query the database to fetch the report by case number with status open/under review
       - If the report is not found, raise a not found error.
       - If the report is unassigned to any moderator, raise a forbidden error.

  4. **Fetch Related Open Reports**:  
     - Query the database to fetch all open reports related to the specific report (same reported item ID and type) using the moderator ID.
     - If no related reports are found, return an empty list.

  5. **Format Report Details**:  
     - Prepare the report response containing case number, status, and reported date.
     - Do this for all the fetched related open reports.

  6. **Return Response**:  
     - Provide the response containing the list of related open reports.

- **API Documentation** 

   [Get All Related Open Reports For Specific Report Doc](https://venkatpaik17.github.io/VPKonnect/#tag/Admin/operation/get_all_related_open_reports_for_specific_report_api_v0_admin_reports__case_number__related_get)

- **Database Tables Affected and Triggers involved** 

   *(NA)*

- **Postman Scripts Flow** 
  - **Pre-request**: 
    1. Manage Authorization
       - Gets the value of the `JWT` environment variable.
       - If the `JWT` variable is empty or doesn't exist, removes the `Authorization` header from the request.

  - **Post-response**: 
    1. Set New Access Token
       - Parse Response JSON.
       - Checks if the response code is `200 (OK)` and the response contains an access_token.
       - If both are true, saves the access_token to the `JWT` environment variable, and indicates to resend the request.

<br>

#### Put Reports Under Review

- **Access Control** 

   This endpoint requires the user to have one of the following roles:
   - **content_admin**
   - **content_mgmt**

- **Abstract Pseudocode for `selected_reports_under_review_update`** 

  1. **Initialize Function**:  
     - Accept a list of report case numbers, database session, logger, current employee, and a function call flag.

  2. **Fetch Current Employee**:  
     - Query the database to fetch the current employee using their work email.  
     - Ensure that the employee is not suspended or terminated.

  3. **Initialize Lists**:  
     - Create empty lists for valid reports, invalid reports, already under review reports, error messages, and success messages.

  4. **Process Each Report**:
     - For each case number in the provided list:
       - Query the database to check if the report exists with an open or under review status.
       - If the report does not exist or is not assigned to the current employee, add it to the invalid reports list.
       - If the report is already under review, add it to the already under review reports list.
       - If the report is valid and not under review, update its status to *under review* and add it to the valid reports list.
     - Commit the changes to the database.

  5. **Handle Errors**:
     - Rollback the transaction on any error.  
     - Log the error and raise an appropriate error response.

  6. **Function Call Response (if applicable)**:
     - If this function was called as part of another function/route (function call flag), return the list of valid reports.

  7. **Prepare Report Update Details**:  
     - If not a function call, prepare a response message:
       - Success message for reports successfully marked under review.
       - Error message for reports that could not be marked due to internal errors or those already under review.

  8. **Return Final Response**:  
     - Provide a response containing the success and error messages.

- **API Documentation** 

   [Selected Reports Under Review Update Doc](https://venkatpaik17.github.io/VPKonnect/#tag/Admin/operation/selected_reports_under_review_update_api_v0_admin_reports_review_patch)

- **Database Tables Affected and Triggers involved** 
  - **Tables**: `user_content_report_detail`, `user_content_report_event_timeline` 
   
  - **Triggers**: `user_content_report_review_event_trigger`

- **Postman Scripts Flow** 
  - **Pre-request**: 
    1. Manage Authorization
       - Gets the value of the `JWT` environment variable.
       - If the `JWT` variable is empty or doesn't exist, removes the `Authorization` header from the request.

  - **Post-response**: 
    1. Set New Access Token
       - Parse Response JSON.
       - Checks if the response code is `200 (OK)` and the response contains an access_token.
       - If both are true, saves the access_token to the `JWT` environment variable, and indicates to resend the request.

<br>

#### Assign Reports

- **Access Control** 

   This endpoint requires the user to have one of the following roles:
   - **content_admin**

- **Abstract Pseudocode for `selected_reports_assign_update`** 

  1. **Initialize Function**:  
     - Accept a list of report case numbers, moderator employee ID, database session, logger, and current employee as inputs.

  2. **Fetch Current Employee**:  
     - Query the database to fetch the current employee using their work email.  
     - Ensure that the employee is not suspended or terminated.

  3. **Fetch Moderator**:  
     - Query the database to fetch the moderator using the provided employee ID.  
     - Ensure that the moderator is not suspended or terminated.  
     - If not found, raise a not found error.

  4. **Initialize Lists**:  
     - Create empty lists for valid reports, invalid reports, already assigned reports, success messages, and error messages.

  5. **Process Each Report**:  
     - For each case number in the list:
       - Query the database to check if the report exists with an open status.  
       - If the report does not exist, add it to the invalid reports list.  
       - If the report is already assigned, add it to the already assigned reports list.  
       - If the report is valid and not assigned, update the report with moderator's ID and add it to the valid reports list.
     - Commit the changes to the database. 

  6. **Handle Errors**:
     - Rollback the transaction on any error.  
     - Log the error and raise an appropriate error response.

  7. **Prepare Report Update Details**:  
     - Prepare response messages:
       - Success message for reports successfully assigned to a moderator.
       - Error message for reports that could not be assigned due to internal errors or those already assigned.  

  8. **Return Final Response**:  
     - Provide the response containing the success and error messages.

- **API Documentation** 

   [Selected Reports Assign Update Doc](https://venkatpaik17.github.io/VPKonnect/#tag/Admin/operation/selected_reports_assign_update_api_v0_admin_reports_assign_patch)

- **Database Tables Affected and Triggers involved** 
  - **Tables**: `user_content_report_detail` 
   
  - **Triggers**: None

- **Postman Scripts Flow** 
  - **Pre-request**: 
    1. Manage Authorization
       - Gets the value of the `JWT` environment variable.
       - If the `JWT` variable is empty or doesn't exist, removes the `Authorization` header from the request.

  - **Post-response**: 
    1. Set New Access Token
       - Parse Response JSON.
       - Checks if the response code is `200 (OK)` and the response contains an access_token.
       - If both are true, saves the access_token to the `JWT` environment variable, and indicates to resend the request.

<br>

#### Close Report

- **Access Control** 

   This endpoint requires the user to have one of the following roles:
   - **content_admin**
   - **content_mgmt**

- **Abstract Pseudocode for `close_report`** 

  1. **Initialize Function**:  
     - Accept report case number, moderator note, database session, logger, and current employee as inputs.

  2. **Fetch Current Employee**:  
     - Query the database to fetch the current employee using their work email.  
     - Ensure the employee is not suspended or terminated.

  3. **Fetch the Report**:  
     - Query the database to fetch the report using the given case number with close or under review status.  
     - If the report is not found, raise a not found error.  
     - If there is a moderator mismatch, raise a forbidden error, indicating they cannot close the report.  
     - If the report is already closed, raise a conflict error.

  4. **Process Close Report**:  
     - Query the database to fetch any open reports related to the current report (same reported item ID, reason, reason user and type) using moderator ID.  
     - If such reports exist
       - Update these reports to under review.
       - Prepare an additional message summarizing these updates.
     - Update the current report's status to closed and include the provided moderator note.  
     - Query the database to fetch any under review reports related to the current report (same reported item ID, reason, reason user and type) using moderator ID.
     - If other related reports with the same reason exist:
       - Update their status to closed and apply the same moderator note.
     - Commit the changes to the database.

  5. **Handle Errors**:  
     - Rollback the transaction on any error.  
     - Log the error and raise an appropriate error response.

  6. **Generate Moderator Note**:  
     - Create a detailed moderator note using the report details, including the case number, username, content type, and report reason.

  7. **Prepare Response Message**:  
      - Construct a success message summarizing the results of the operation.  
      - Include additional messages for any open related reports that were put under review.

  8. **Return Final Response**:  
      - Provide the response containing the success message, detailed moderator note, and additional message (if any).

- **API Documentation** 

   [Close Report Doc](https://venkatpaik17.github.io/VPKonnect/#tag/Admin/operation/close_report_api_v0_admin_reports__case_number__close_patch)

- **Database Tables Affected and Triggers involved** 
  - **Tables**: `user_content_report_detail`, `user_content_report_event_timeline` 
   
  - **Triggers**: `user_content_report_close_event_trigger`

- **Postman Scripts Flow** 
  - **Pre-request**: 
    1. Manage Authorization
       - Gets the value of the `JWT` environment variable.
       - If the `JWT` variable is empty or doesn't exist, removes the `Authorization` header from the request.

  - **Post-response**: 
    1. Set New Access Token
       - Parse Response JSON.
       - Checks if the response code is `200 (OK)` and the response contains an access_token.
       - If both are true, saves the access_token to the `JWT` environment variable, and indicates to resend the request.

<br>

#### Report Action - Auto

- **Access Control** 

   This endpoint requires the user to have one of the following roles:
   - **content_admin**
   - **content_mgmt**

- **Abstract Pseudocode for `enforce_report_action_auto`** 

  1. **Initialize Function**:
     - Accept action details (case number and reported username), background tasks, database session, logger, and current employee as inputs.

  2. **Fetch Current Employee**:  
     - Query the database to fetch the current employee using their work email.  
     - Ensure the employee is not suspended or terminated.

  3. **Fetch the Report**:
     - Query the database to fetch the report using the given case number.
     - If the report is not found, raise a not found error.
     - If there is a moderator mismatch, raise a forbidden error, indicating they cannot take action on the report.  
     - If the report is open, raise a conflict error, indicating the report should be under review.
     - If the report is closed, raise a conflict error.
     - If the report is already resolved, raise a conflict error, indicating the action on report is already taken.

  4. **Check Reported Item Type**:
     - If the reported item type is `account`, raise a bad request error, indicating to use manual action.

  5. **Fetch Reported Item (Post/Comment)**:
     - If the reported item type is `post`:
       - Query the database to retrieve the post using the reported item ID.
       - Ensure the post is not draft, flagged deleted, or removed.
       - If no post is found, raise a not found error.
       - If the post is banned flagged to be banned, raise a conflict error.
     - If the reported item type is `comment`:
       - Query the database to retrieve the comment using the reported item ID.
       - Ensure the comment is not flagged deleted, or removed.
       - If no comment is found, raise a not found error.
       - If the comment is banned or flagged to be banned, raise a conflict error.

  6. **Fetch Reported User**:
     - Query the database to fetch the reported user using their username, not in deleted status.
     - If the reported user is not found, raise a not found error.
     - If the reported user is permanently banned, raise a forbidden error.

  7. **Handle Related Open Reports**:
     - Query the database to fetch any open reports related to the current report (same reported item ID and type) using moderator ID.  
     - If such reports exist:
       - Update these reports to *under review*.
       - Prepare an additional message summarizing these updates.

  8. **Determine Severity Group**:
     - Determine the severity group based on the report reason.
     - If the severity group cannot be determined, raise a not found error.
     - If the severity is Content Moderator Decision, raise a bad request error, indicating to use manual action..

  9. **Fetch Severity Score**:
     - Fetch the severity score based on the severity group and content type.
     - If no score is found, raise a not found error.

  10. **Fetch Content Type Weights**:
      - Get the weights based on content type.
      - If no weight is found, raise a not found error.

  11. **Fetch Current Final Violation Score**:
      - Query the database to retrieve the current final violation score for the reported user.
      - If no score is found, raise a not found error.

  12. **Calculate New Final Violation Score**:
      - Calculate the new final violation score by adding the weight adjusted severity score (effective score) to the current final violation score.

  13. **Determine Action and Duration**:
      - If the user's final violation score hasn't changed, no action is needed.
      - Else:
        - Determine the appropriate action and duration based on the new final violation score.
        - If no action is found for the score, raise a not found error.
        - If the action is Not Applicable, then no action is needed.

  14. **Determine Content Violation Score Type and Current Content Violation Score**:
      - Determine the specific content violation score type (post, comment, or message).
      - Get the current content violation score.
      - If the reported item type is `account`, use *post score* as a default.

  15. **Process Report Action**:
      - If no action is needed:
        - Prepare a success message for report resolve.
      - If action is needed:
        - Find existing restrictions/bans for the reported user.
        - Based on active and future restrictions/ban (if any), determine if the new action is immediate or scheduled for the future.
        - Create a new restriction/ban entry based on the provided details.
        - Prepare a success message for action and report resolve.

  16. **Report Action Effective Operations**:
      - If a new restriction/ban entry was created:
        - Add the restriction/ban entry to the database.
      - If no action or the new action is immediate:
        - Update the report status to *resolved* with moderator note.
        - Update the content violation score and final violation score.
        - Record the last added score (effective score)
        - Update the reported content (if post or comment) status to *banned*.
      - If the action is scheduled for the future:
        - Update the report status to *future resolved*.
        - Record the last added score (effective score), marked for future.
        - Update the reported content (if post or comment) status to *flagged to be banned*.
      - Query the database to fetch any under review reports related to the current report (same reported item ID, user ID, and type) using moderator ID.
        - If other related reports with the same reason exist:
          - For each related report:
            - Update their status to *resolved* or *future resolved* (based on action) with appropriate moderator note
            - Else, update their status to closed with appropriate moderator note.
      - Update reported user status appropriately if needed based on action, current reported user status and restriction/ban.
      - Commit the changes to the database.

  17. **Send Email Notification (If Applicable)**:
      - If the action is immediate and action is a ban (temporary or permanent):
        - Construct an email with subject, body, and template to notify the user about the ban.
        - Dispatch the ban notification email using background tasks.

  18. **Handle Errors**:  
      - Rollback the transaction on any error.  
      - Log the error and raise an appropriate error response.

  19. **Generate Moderator Note**:  
      - Create a detailed moderator note using the report details, including the case number, username, content type, and report reason.

  20. **Return Response**:
      - Provide a success message indicating the report action was successfully processed, detailed moderator note and additional message (if any).

- **API Documentation** 

   [Enforce Report Action Auto Doc](https://venkatpaik17.github.io/VPKonnect/#tag/Admin/operation/enforce_report_action_auto_api_v0_admin_reports_action_auto_post)

- **Database Tables Affected and Triggers involved** 
  - **Tables**: `user_content_report_detail`, `user_content_report_event_timeline`, `user_restrict_ban_detail`, `guideline_violation_score`, `guideline_violation_last_added_score`, `post`, `comment`, `user`, `activity_detail`, `user_account_history`, `post_like`, `comment_like`, `user_follow_association`, `user_session`, `user_auth_track` 
   
  - **Triggers**: `user_content_report_resolve_event_trigger`, `user_restrict_ban_account_resolve_insert_event_trigger`, `user_update_activity_detail_trigger`, `update_user_account_history_trigger`, `user_status_update_hide_trigger`, `post_status_update_hide_trigger`, `comment_status_update_hide_trigger`, `post_status_update_ban`, `comment_status_update_ban_trigger`, `user_auth_track_logout_trigger`

- **Postman Scripts Flow** 
  - **Pre-request**: 
    1. Manage Authorization
       - Gets the value of the `JWT` environment variable.
       - If the `JWT` variable is empty or doesn't exist, removes the `Authorization` header from the request.

  - **Post-response**: 
    1. Set New Access Token
       - Parse Response JSON.
       - Checks if the response code is `200 (OK)` and the response contains an access_token.
       - If both are true, saves the access_token to the `JWT` environment variable, and indicates to resend the request.

<br>

#### Report Action - Manual

- **Access Control** 

   This endpoint requires the user to have one of the following roles:
   - **content_admin**
   - **content_mgmt**

- **Abstract Pseudocode for `enforce_report_action_manual`** 

  1. **Initialize Function**:
     - Accept action details (case number, reported username, action, duration, and list of contents to be banned), background tasks, database session, logger, and current employee as inputs.

  2. **Fetch Current Employee**:
     - Query the database to fetch the current employee using their work email.
     - Ensure the employee is not suspended or terminated.

  3. **Fetch the Report**:
     - Query the database to fetch the report using the given case number.
     - If the report is not found, raise a not found error.
     - If there is a moderator mismatch, raise a forbidden error, indicating they cannot take action on the report.  
     - If the report is open, raise a conflict error, indicating the report should be under review.
     - If the report is closed, raise a conflict error.
     - If the report is already resolved, raise a conflict error, indicating the action on report is already taken.

  4. **Fetch Reported Item (Post/Comment)**:
     - If the reported item type is `post`:
       - Query the database to retrieve the post using the reported item ID.
       - Ensure the post is not draft, flagged deleted, or removed.
       - If no post is found, raise a not found error.
       - If the post is banned flagged to be banned, raise a conflict error.
     - If the reported item type is `comment`:
       - Query the database to retrieve the comment using the reported item ID.
       - Ensure the comment is not flagged deleted, or removed.
       - If no comment is found, raise a not found error.
       - If the comment is banned or flagged to be banned, raise a conflict error.

  5. **Fetch Reported User**:
     - Query the database to fetch the reported user using their username, not in deleted status.
     - If the reported user is not found, raise a not found error.
     - If the reported user is permanently banned, raise a forbidden error.

  6. **Handle Related Open Reports**:
      - Query the database to fetch any open reports related to the current report (same reported item ID and type) using the moderator ID.
      - If such reports exist:
        - Update these reports to *under review*.
        - Prepare an additional message summarizing these updates.

  7. **Fetch Minimum Required Violation Score**:
      - Fetch the minimum required violation score based on the requested action and duration.
      - If no score is found, raise a not found error.

  8. **Fetch Current Final Violation Score**:
      - Query the database to retrieve the current final violation score for the reported user.
      - If no score is found, raise a not found error.

  9. **Determine Content Violation Score Type and Current Content Violation Score**:
     - Determine the specific content violation score type (post, comment, or message).
     - Get the current content violation score.
     - If the reported item type is `account`, use *post score* as a default.

  10. **Determine Action Timing**:
      - Find existing restrictions/bans for the reported user.
        - Based on active and future restrictions/ban (if any), determine if the new action is immediate or scheduled for the future.

  11. **Adjust New Violation Scores**:
      - If there are future restrictions/bans:
        - Query the database to fetch last added score of the latest future restriction/ban.
        - If no last added score found, raise a not found error. 
        - Adjust the the new final violation score, content score, last added score if the minimum required violation score is larger than the latest future restriction/ban's last added score and current final violation score.
      - Else, adjust the new final violation score, content score, last added score if the minimum required violation score is larger than the current final violation score.

  12. **Add the New Restriction/Ban**:
      - Create a new restriction/ban entry based on the provided details.
      - Add the entry to the database.

  13. **Handle Account-Specific Content Ban**:
      - If the reported item type is `account` and content IDs (post IDs) to be banned are provided:
        - Create an empty list for flagged posts not found.
        - Query the database to fetch the content using content ID, in published/hidden status.
        - If the content is not found, add it to the flagged posts not found list and continue.
        - If the content is found, create an account report flagged content entry and add it to the database.
        - If the action is immediate, update the content status to *banned*.
        - Else, update the content status to *flagged to be banned*.
        - If all provided content IDs are do not translate to the content being found, raise a not found error.
        - Adjust new final violation score, content score, last added score based on the number of valid flagged content items (making it divisible).

  14. **Report Action Effective Operations**:
      - If no action or the new action is immediate:
        - Update the report status to *resolved* with moderator note.
        - Update the content violation score and final violation score.
        - Record the new last added score.
        - Update the reported content (if post or comment) status to *banned*.
      - If the action is scheduled for the future:
        - Update the report status to *future resolved*.
        - Record the new last added score, marked for future.
        - Update the reported content (if post or comment) status to *flagged to be banned*.
      - Query the database to fetch any under review reports related to the current report (same reported item ID, user ID, and type) using moderator ID.
        - If other related reports with the same reason exist:
          - For each related report: 
            - Update their status to *resolved* or *future resolved* (based on action) with appropriate moderator note
            - Else, update their status to closed with appropriate moderator note.
      - Update reported user status appropriately if needed based on action, current reported user status and restriction/ban.
      - Commit the changes to the database.

  15. **Send Email Notification (If Applicable)**:
      - If the action is immediate and action is a ban (temporary or permanent):
        - Construct an email with subject, body, and template to notify the user about the ban.
        - Dispatch the ban notification email using background tasks.

  16. **Handle Errors**:
      - Rollback the transaction on any error.
      - Log the error and raise an appropriate error response.

  17. **Generate Moderator Note**:
       Create a detailed moderator note using the report details, including the case number, username, content type, and report reason.

  18. **Return Response**:
      - Provide a success message indicating the report action was successfully processed, detailed moderator note and additional message (if any).

- **API Documentation** 

   [Enforce Report Action Manual Doc](https://venkatpaik17.github.io/VPKonnect/#tag/Admin/operation/enforce_report_action_manual_api_v0_admin_reports_action_manual_post)

- **Database Tables Affected and Triggers involved** 
  - **Tables**: `user_content_report_detail`, `user_content_report_event_timeline`, `user_restrict_ban_detail`, `account_report_flagged_content`, `post`, `comment`, `guideline_violation_score`, `guideline_violation_last_added_score`, `user`, `activity_detail`, `user_account_history`, `post_like`, `comment_like`, `user_follow_association`, `user_session`, `user_auth_track` 
     
  - **Triggers**: `user_content_report_resolve_event_trigger`, `user_restrict_ban_account_resolve_insert_event_trigger`, `user_update_activity_detail_trigger`, `update_user_account_history_trigger`, `user_status_update_hide_trigger`, `post_status_update_hide_trigger`, `comment_status_update_hide_trigger`, `post_status_update_ban`, `comment_status_update_ban_trigger`, `user_auth_track_logout_trigger`

- **Postman Scripts Flow** 
  - **Pre-request**: 
    1. Manage Authorization
       - Gets the value of the `JWT` environment variable.
       - If the `JWT` variable is empty or doesn't exist, removes the `Authorization` header from the request.

  - **Post-response**: 
    1. Set New Access Token
       - Parse Response JSON.
       - Checks if the response code is `200 (OK)` and the response contains an access_token.
       - If both are true, saves the access_token to the `JWT` environment variable, and indicates to resend the request.

<br>

#### Appeal Dashboard - Admin

- **Access Control** 

   This endpoint requires the user to have one of the following roles:
   - **content_admin**

- **Abstract Pseudocode for `get_appeals_admin_dashboard`** 

  1. **Initialize Function**:  
     - Accept type (`new` or `assigned`), status (optional, `open`, `closed`, `review`, `accepted`, `rejected`), emp ID, reported date, database session, and current employee as inputs.

  2. **Validate Parameters**:  
     - Check if the status and type combination is valid. If status is not `open` and type is `new`, raise a bad request error, indicating invalid type for status.
     - If type is `new` and emp ID is provided, raise a bad request error, indicating it is invalid to provide emp ID for new type.

  3. **Transform Appeal Status**:  
     - If status is provided in the request, transform it to its code form.
     - If status is invalid or cannot be transformed, raise a bad request error.

  4. **Fetch Moderator (if applicable)**:
     - If emp ID is provided:
       - Query the database to fetch the current employee using the emp ID.
       - Ensure that the employee is not suspended or terminated.

  5. **Fetch Appeals**:  
     - Query the database to fetch the appeals based on the provided appeal status, type, moderator, and reported date.
     - If no appeals are found, return an empty list.

  6. **Format Appeal Details**:  
     - Prepare the appeal response containing case number, status, and appealed at.
     - Do this for all the fetched appeals.

  7. **Return Response**:  
     - Provide the response containing the list of appeals.

- **API Documentation** 

   [Get Appeals Admin Dashboard Doc](https://venkatpaik17.github.io/VPKonnect/#tag/Admin/operation/get_appeals_admin_dashboard_api_v0_admin_appeals_admin_dashboard_get)

- **Database Tables Affected and Triggers involved** 

   *(NA)*

- **Postman Scripts Flow** 
  - **Pre-request**: 
    1. Manage Authorization
       - Gets the value of the `JWT` environment variable.
       - If the `JWT` variable is empty or doesn't exist, removes the `Authorization` header from the request.

  - **Post-response**: 
    1. Set New Access Token
       - Parse Response JSON.
       - Checks if the response code is `200 (OK)` and the response contains an access_token.
       - If both are true, saves the access_token to the `JWT` environment variable, and indicates to resend the request.

<br>

#### Appeals Dashboard

- **Access Control** 

   This endpoint requires the user to have one of the following roles:
   - **content_admin**
   - **content_mgmt**

- **Abstract Pseudocode for `get_appeals_dashboard`** 

  1. **Initialize Function**:  
     - Accept status (optional, `open`, `closed`, `review`, `accepted`, or `rejected`), database session, and current employee as inputs.

  2. **Validate Appeal Status**:
     - If an appeal status is provided in the request, transform it to its code form.
     - If status is invalid or cannot be transformed, raise a bad request error.

  3. **Fetch Current Employee**:
     - Query the database to fetch the current employee using their work email.
     - Ensure that the employee is not suspended or terminated.

  4. **Fetch Appeals**:
     - Query the database to fetch the appeals based on the provided appeal status and the current employee as the moderator.
     - If no appeals are found, return an empty list.

  5. **Format Appeal Details**:
     - Prepare the appeal response containing case number, status, and appealed at.
     - Do this for all the fetched appeals.

  6. **Return Response**:
     - Provide the response containing the list of appeals.

- **API Documentation** 

   [Get Appeals Dashboard Doc](https://venkatpaik17.github.io/VPKonnect/#tag/Admin/operation/get_appeals_dashboard_api_v0_admin_appeals_dashboard_get)

- **Database Tables Affected and Triggers involved** 

   *(NA)*

- **Postman Scripts Flow** 
  - **Pre-request**: 
    1. Manage Authorization
       - Gets the value of the `JWT` environment variable.
       - If the `JWT` variable is empty or doesn't exist, removes the `Authorization` header from the request.

  - **Post-response**: 
    1. Set New Access Token
       - Parse Response JSON.
       - Checks if the response code is `200 (OK)` and the response contains an access_token.
       - If both are true, saves the access_token to the `JWT` environment variable, and indicates to resend the request.

<br>

#### Get Appeal

- **Access Control** 

   This endpoint requires the user to have one of the following roles:
   - **content_admin**
   - **content_mgmt**

- **Abstract Pseudocode for `get_requested_appeal`** 

  1. **Initialize Function**:
     - Accept case number, database session, and current employee as inputs.

  2. **Fetch Appeal**:
     - Query the database to fetch the appeal using the provided case number.
     - If no appeal is found, raise a not found error.

  3. **Authorization Check**:
     - If the appeal is open and unassigned, only content admin can access the appeal.
     - If the current employee's role is not content admin, raise an unauthorized error.

  4. **Prepare Appeal Data**:
     - Create the appeal data dictionary including case number, appeal user details, report details, content type, appealed content, appeal detail, attachment, status, moderator note, moderator details, appealed at, and last updated at.

  5. **Return Response**:
     - Parse the dictionary into the response schema and return the response with the appeal details.

- **API Documentation** 

   [Get Requested Appeal Doc](https://venkatpaik17.github.io/VPKonnect/#tag/Admin/operation/get_requested_appeal_api_v0_admin_appeals__case_number__get)

- **Database Tables Affected and Triggers involved** 

   *(NA)*

- **Postman Scripts Flow** 
  - **Pre-request**: 
    1. Manage Authorization
       - Gets the value of the `JWT` environment variable.
       - If the `JWT` variable is empty or doesn't exist, removes the `Authorization` header from the request.

  - **Post-response**: 
    1. Set New Access Token
       - Parse Response JSON.
       - Checks if the response code is `200 (OK)` and the response contains an access_token.
       - If both are true, saves the access_token to the `JWT` environment variable, and indicates to resend the request.

<br>

#### Get Related Open Appeals

- **Access Control** 

   This endpoint requires the user to have one of the following roles:
   - **content_admin**
   - **content_mgmt**

- **Abstract Pseudocode for `get_all_related_open_appeals_for_specific_appeal`** 

  1. **Initialize Function**:  
     - Accept case number, admin flag, database session, and current employee as inputs.

  2. **Fetch Current Employee**:  
     - Query the database to fetch the current employee using their work email.  
     - Ensure that the employee is not suspended or terminated.

  3. **Process Flow**:  
     - If the admin flag is true:
       - Query the database to fetch the appeal by case number with status open.
       - If the appeal is not found, raise a not found error.
       - If the appeal is already assigned to a moderator, raise a conflict error. 
     - If the admin flag is false:
       - Use the current employee's ID as the moderator ID.
       - Query the database to fetch the appeal by case number with status open/under review.
       - If the appeal is not found, raise a not found error.
       - If the appeal is unassigned to any moderator, raise a forbidden error.

  4. **Fetch Related Open Appeals**:  
     - Query the database to fetch all open appeals related to the specific appeal (same content ID and type) using the moderator ID.
     - If no related appeals are found, return an empty list.

  5. **Format Appeal Details**:  
     - Prepare the appeal response containing case number, status, and appealed date.
     - Do this for all the fetched related open appeals.

  6. **Return Response**:  
     - Provide the response containing the list of related open appeals.

- **API Documentation** 

   [Get All Related Open Appeals For Specific Appeal Doc](https://venkatpaik17.github.io/VPKonnect/#tag/Admin/operation/get_all_related_open_appeals_for_specific_appeal_api_v0_admin_appeals__case_number__related_get)

- **Database Tables Affected and Triggers involved** 

   *(NA)*

- **Postman Scripts Flow** 
  - **Pre-request**: 
    1. Manage Authorization
       - Gets the value of the `JWT` environment variable.
       - If the `JWT` variable is empty or doesn't exist, removes the `Authorization` header from the request.

  - **Post-response**: 
    1. Set New Access Token
       - Parse Response JSON.
       - Checks if the response code is `200 (OK)` and the response contains an access_token.
       - If both are true, saves the access_token to the `JWT` environment variable, and indicates to resend the request.

<br>

#### Put Appeals Under Review

- **Access Control** 

   This endpoint requires the user to have one of the following roles:
   - **content_admin**
   - **content_mgmt**

- **Abstract Pseudocode for `selected_appeals_under_review_update`** 

  1. **Initialize Function**:  
     - Accept a list of appeal case numbers, database session, logger, current employee, and a function call flag.

  2. **Fetch Current Employee**:  
     - Query the database to fetch the current employee using their work email.  
     - Ensure that the employee is not suspended or terminated.

  3. **Initialize Lists**:  
     - Create empty lists for valid appeals, invalid appeals, already under review appeals, error messages, and success messages.

  4. **Process Each Appeal**:
     - For each case number in the provided list:
       - Query the database to check if the appeal exists with an open or under review status.
       - If the appeal does not exist, is unassigned, or is not assigned to the current employee, add it to the invalid appeals list.
       - If the appeal is already under review, add it to the already under review appeals list.
       - If the appeal is valid and not under review, update its status to *under review* and add it to the valid appeals list.
     - Commit the changes to the database.

  5. **Handle Errors**:
     - Rollback the transaction on any error.  
     - Log the error and raise an appropriate error response.

  6. **Function Call Response (if applicable)**:
     - If this function was called as part of another function/route (function call flag), return the list of valid appeals.

  7. **Prepare Appeal Update Details**:  
     - If not a function call, prepare a response message:
       - Success message for appeals successfully marked under review.
       - Error message for appeals that could not be marked due to internal errors or those already under review.

  8. **Return Final Response**:  
     - Provide a response containing the success and error messages.

- **API Documentation** 

   [Selected Appeals Under Review Update Doc](https://venkatpaik17.github.io/VPKonnect/#tag/Admin/operation/selected_appeals_under_review_update_api_v0_admin_appeals_review_patch)

- **Database Tables Affected and Triggers involved** 
  - **Tables**: `user_content_restrict_ban_appeal_detail`, `user_content_restrict_ban_appeal_event_timeline`

  - **Triggers**: `user_content_restrict_ban_appeal_review_event_trigger`

- **Postman Scripts Flow** 
  - **Pre-request**: 
    1. Manage Authorization
       - Gets the value of the `JWT` environment variable.
       - If the `JWT` variable is empty or doesn't exist, removes the `Authorization` header from the request.

  - **Post-response**: 
    1. Set New Access Token
       - Parse Response JSON.
       - Checks if the response code is `200 (OK)` and the response contains an access_token.
       - If both are true, saves the access_token to the `JWT` environment variable, and indicates to resend the request.

<br>

#### Assign Appeals

- **Access Control** 

   This endpoint requires the user to have one of the following roles:
   - **content_admin**

- **Abstract Pseudocode for `selected_appeals_assign_update`** 

  1. **Initialize Function**:  
     - Accept a list of appeal case numbers, moderator employee ID, database session, logger, and current employee as inputs.

  2. **Fetch Current Employee**:  
     - Query the database to fetch the current employee using their work email.  
     - Ensure that the employee is not suspended or terminated.

  3. **Fetch Moderator**:  
     - Query the database to fetch the moderator using the provided employee ID.  
     - Ensure that the moderator is not suspended or terminated.  
     - If not found, raise a not found error.

  4. **Initialize Lists**:  
     - Create empty lists for valid appeals, invalid appeals, already assigned appeals, success messages, and error messages.

  5. **Process Each Appeal**:  
     - For each case number in the list:
       - Query the database to check if the appeal exists with an open status.  
       - If the appeal does not exist, add it to the invalid appeals list.  
       - If the appeal is already assigned, add it to the already assigned appeals list.  
       - If the appeal is valid and not assigned, update the appeal with moderator's ID and add it to the valid appeals list.
     - Commit the changes to the database.

  6. **Handle Errors**:  
     - Rollback the transaction on any error.  
     - Log the error and raise an appropriate error response.

  7. **Prepare Appeal Update Details**:  
     - Prepare response messages:
       - Success message for appeals successfully assigned to the moderator.  
       - Error messages for appeals that could not be assigned due to internal errors or those already assigned.

  8. **Return Final Response**:  
     - Provide a response containing the success and error messages.

- **API Documentation** 

   [Selected Appeals Assign Update Doc](https://venkatpaik17.github.io/VPKonnect/#tag/Admin/operation/selected_appeals_assign_update_api_v0_admin_appeals_assign_patch)

- **Database Tables Affected and Triggers involved** 
  - **Tables**: `user_content_restrict_ban_appeal_detail`

  - **Triggers**: None

- **Postman Scripts Flow** 
  - **Pre-request**: 
    1. Manage Authorization
       - Gets the value of the `JWT` environment variable.
       - If the `JWT` variable is empty or doesn't exist, removes the `Authorization` header from the request.

  - **Post-response**: 
    1. Set New Access Token
       - Parse Response JSON.
       - Checks if the response code is `200 (OK)` and the response contains an access_token.
       - If both are true, saves the access_token to the `JWT` environment variable, and indicates to resend the request.

<br>

#### Check Appeal Policy

- **Access Control** 

   This endpoint requires the user to have one of the following roles:
   - **content_admin**
   - **content_mgmt**

- **Abstract Pseudocode for `check_appeal_policy`** 

  1. **Initialize Function**:  
     - Accept appeal case number, database session, logger, and current employee as inputs.

  2. **Fetch Current Employee**:  
     - Query the database to fetch the current employee using their work email.  
     - Ensure that the employee is not suspended or terminated.

  3. **Fetch the Appeal**:  
     - Query the database to fetch the appeal entry using the given case number.  
     - If the appeal is not found, raise a not found error.  
     - If the appeal's moderator ID does not match the current employee, raise a forbidden error.  
     - If the appeal is open, raise a bad request error, indicating appeal should be under review.
     - If the appeal is already accepted or rejected, raise a bad request error, indicating the policy check and action is already taken.
     - If the appeal is already closed, raise a bad request error, indicating invalid check.

  4. **Fetch the Associated Report**:  
     - Query the database to fetch the report entry associated with the appeal, in resolved status.  
     - If the report is not found, raise a not found error.

  5. **Fetch Restrict/Ban Entry**:  
     - Query the database to fetch the restrict/ban entry related to the report and user.  

  6. **Process Check Appeal Policy**:  
     - If appeal content type is `account`:
       - If the restrict/ban contetnt type is `account`:
         - Query the database for all flagged posts and check for rejected appeals.  
         - If rejected appeals are found:
           - Update the appeal to indicate the policy is not followed.  
           - Update the message and detail to reflect rejection.  
         - Else, update the appeal to indicate the policy is followed.  
       - If the restrict/ban content type is `post` or `comment`:
         - Query the database for any rejected appeal against the content.  
         - If rejected appeal is found:
           - Update the appeal to indicate the policy is not followed.  
           - Update the message and detail to reflect rejection.  
         - Else, update the appeal to indicate the policy is followed.
     - If appeal content type is `post` and restrict/ban content type is `account`:
       - Query the database for any rejected appeal against the account.  
       - If rejected appeal is found:
         - Update the appeal to indicate the policy is not followed.  
         - Update the message and detail to reflect rejection.  
       - Else, update the appeal to indicate the policy is followed.
     - If appeal content type is `post` or `comment` restrict/ban content type is `post` or `comment`:
       - Query the database for any rejected appeal against the associated account.  
       - If rejected appeal is found:
         - Update the appeal to indicate the policy is not followed.  
         - Update the message and detail to reflect rejection.  
       - Else, update the appeal to indicate the policy is followed.
     - If the content type combination is invalid, log the error and raise an internal server error.

  7. **Handle Errors**:  
     - Rollback the transaction on any error.  
     - Log the error and raise an appropriate error response.

  8. **Return Final Response**:  
     - Provide the response containing the status message and detail.

- **API Documentation** 

   [Check Appeal Policy Doc](https://venkatpaik17.github.io/VPKonnect/#tag/Admin/operation/check_appeal_policy_api_v0_admin_appeals__case_number__check_policy_patch)

- **Database Tables Affected and Triggers involved** 
  - **Tables**: `user_content_restrict_ban_appeal_detail`

  - **Triggers**: None

- **Postman Scripts Flow** 
  - **Pre-request**: 
    1. Manage Authorization
       - Gets the value of the `JWT` environment variable.
       - If the `JWT` variable is empty or doesn't exist, removes the `Authorization` header from the request.

  - **Post-response**: 
    1. Set New Access Token
       - Parse Response JSON.
       - Checks if the response code is `200 (OK)` and the response contains an access_token.
       - If both are true, saves the access_token to the `JWT` environment variable, and indicates to resend the request.

<br>

#### Close Appeal

- **Access Control** 

   This endpoint requires the user to have one of the following roles:
   - **content_admin**
   - **content_mgmt**

- **Abstract Pseudocode for `close_appeal`** 

  1. **Initialize Function**:  
     - Accept appeal case number, moderator note, database session, logger, and current employee as inputs.

  2. **Fetch Current Employee**:  
     - Query the database to fetch the current employee using their work email.  
     - Ensure the employee is not suspended or terminated.

  3. **Fetch the Appeal**:  
     - Query the database to fetch the appeal using the given case number with close or under review status.  
     - If the appeal is not found, raise a not found error.  
     - If there is a moderator mismatch, raise a forbidden error, indicating they cannot close the appeal.  
     - If the appeal is already closed, raise a conflict error.

  4. **Process Close Appeal**:  
     - Query the database to fetch any open appeals related to the current appeal (same content ID and type) using moderator ID.  
     - If such appeals exist:
       - Update these appeals to under review.
       - Prepare an additional message summarizing these updates.  
     - Update the current appeal's status to closed and include the provided moderator note.  
     - Query the database to fetch any under review appeals related to the current appeal (same content ID and type) using moderator ID.  
     - If other related appeals exist:
       - Update the appeal policy followed to True, appeal status to closed and apply the same moderator note.  
     - Commit the changes to the database.

  5. **Handle Errors**:  
     - Rollback the transaction on any error.  
     - Log the error and raise an appropriate error response.

  6. **Generate Moderator Note**:  
     - Create a detailed moderator note using the appeal details, including the case number, username, and content type.

  7. **Prepare Response Message**:  
      - Construct a success message summarizing the results of the operation.  
      - Include additional messages for any open related appeals that were put under review.

  8. **Return Final Response**:  
      - Provide the response containing the success message, detailed moderator note, and additional message (if any).

- **API Documentation** 

   [Close Appeal Doc](https://venkatpaik17.github.io/VPKonnect/#tag/Admin/operation/close_appeal_api_v0_admin_appeals__case_number__close_patch)

- **Database Tables Affected and Triggers involved** 
  - **Tables**: `user_content_restrict_ban_appeal_detail`, `user_content_restrict_ban_appeal_event_timeline`

  - **Triggers**: `user_content_restrict_ban_appeal_close_event_trigger`

- **Postman Scripts Flow** 
  - **Pre-request**: 
    1. Manage Authorization
       - Gets the value of the `JWT` environment variable.
       - If the `JWT` variable is empty or doesn't exist, removes the `Authorization` header from the request.

  - **Post-response**: 
    1. Set New Access Token
       - Parse Response JSON.
       - Checks if the response code is `200 (OK)` and the response contains an access_token.
       - If both are true, saves the access_token to the `JWT` environment variable, and indicates to resend the request.

<br>

#### Appeal Action

- **Access Control** 

   This endpoint requires the user to have one of the following roles:
   - **content_admin**
   - **content_mgmt**

- **Abstract Pseudocode for `appeal_action`** 

  1. **Initialize Function**:  
     - Accept appeal action details (case number, action (`accept`, `reject`), appeal_username, moderator_note), background tasks, database session, logger, and current employee as inputs.

  2. **Fetch Current Employee**:  
     - Query the database to fetch the current employee using their work email.  
     - Ensure the employee is not suspended or terminated.

  3. **Fetch the Appeal User**:  
     - Query the database to fetch the user associated with the appeal based on the provided username, not in deleted status.  
     - If the user is not found, raise a not found error.
     - If the user is inactive, raise a conflict error.

  4. **Fetch the Appeal**:  
     - Query the database to fetch the appeal using the given case number.
     - If the appeal is not found, raise a not found error.
     - If there is a moderator mismatch, raise a forbidden error, indicating they cannot take action on the appeal.  
     - If the appeal is open, raise a conflict error, indicating the appeal should be under review.
     - If the appeal is closed, raise a conflict error.
     - If the appeal is already accepted or rejected, raise a conflict error, indicating the action on appeal is already taken.

  5. **Verify Check Appeal Policy**:  
     - Ensure the appeal policy has been followed. If not, raise a bad request error.

  6. **Handle Related Open Appeals**:
     - Query the database to fetch any open appeals related to the current appeal (same content ID and type) using moderator ID.  
     - If such appeals exist:
       - Update these appeals to *under review*.
       - Prepare an additional message summarizing these updates.

  7. **Get Associated Report and Restrict/Ban Entry**:  
     - Query the database to fetch the report associated with the appeal. If the report is missing, raise a not found error.  
     - Ensure a restriction/ban entry is found based on the report type (posts, comments, or accounts).  
       - If no restriction/ban entry exists for a post/comment appeal, proceed.
       - For account type appeals, ensure such entries exist, if not, raise a not found error.

  8. **Fetch Other Related Appeals**:  
     - Query the database to fetch all under review appeals related to the specific appeal (same content ID and type) using the moderator ID.

  9. **Process the Appeal Action**:  
     - If action is `accept`:
       - Update the appeal policy followed to True, appeal status to *accepted* and moderator note.
       - Perform necessary operations after accepting the appeal (updating the report, handling content, enforcing next violation, updating appeal user etc).
     - If action is `reject`:
       - Update the appeal policy followed to True, appeal status to *rejected* and moderator note.
       - Perform necessary operations after rejecting the appeal (handling the content, updating appeal user etc).
     - If action is invalid, raise a bad request error.
     - Commit the changes to the database.

  10. **Handle Email Notifications**:  
      - If appeal user is banned upon consecutive violation:
        - Construct an email with subject, body, and template to notify the user about the ban.
        - Dispatch the ban notification email using background tasks.

  11. **Handle Errors**:
      - Rollback the transaction on any error.
      - Log the error and return an appropriate error response.

  12. **Generate Moderator Note**:  
      - Create a detailed moderator note using the appeal details, including the case number, username, and content type.

  13. **Return Response**:  
      - Provide a success message indicating the appeal action was successfully processed, along with the detailed moderator note.

- **API Documentation** 

   [Appeal Action Doc](https://venkatpaik17.github.io/VPKonnect/#tag/Admin/operation/appeal_action_api_v0_admin_appeals_action_post)

- **Database Tables Affected and Triggers involved** 
  - **Tables**: `user_content_restrict_ban_appeal_detail`, `user_content_restrict_ban_appeal_event_timeline`, `post`, `comment`, `guideline_violation_last_added_score`, `guideline_violation_score`, `user_restrict_ban_detail`, `user_content_report_detail`, `user_content_report_event_timeline`, `user`, `activity_detail`, `user_account_history`, `post_like`, `comment_like`, `user_follow_association`, `user_session`, `user_auth_track`  

  - **Triggers**: `user_content_restrict_ban_appeal_accept_event_trigger`, `user_content_restrict_ban_appeal_reject_event_trigger`, `user_update_activity_detail_trigger`, `update_user_account_history_trigger`, `user_status_update_unhide_trigger`, `post_status_update_unhide_trigger`, `comment_status_update_unhide_trigger`, `post_status_update_unban_trigger`, `comment_status_update_unban_trigger`, `user_content_report_resolve_event_trigger`, `post_status_update_ban_trigger`, `comment_status_update_ban_trigger`, `user_restrict_ban_account_resolve_update_event_trigger`, `user_auth_track_logout_trigger`, `user_status_update_hide_trigger`, `post_status_update_hide_trigger`, `comment_status_update_hide_trigger`, `user_status_update_pdb_trigger`, `user_content_report_close_event_trigger`

- **Postman Scripts Flow** 
  - **Pre-request**: 
    1. Manage Authorization
       - Gets the value of the `JWT` environment variable.
       - If the `JWT` variable is empty or doesn't exist, removes the `Authorization` header from the request.

  - **Post-response**: 
    1. Set New Access Token
       - Parse Response JSON.
       - Checks if the response code is `200 (OK)` and the response contains an access_token.
       - If both are true, saves the access_token to the `JWT` environment variable, and indicates to resend the request.

<br>

#### Get Users - Admin

- **Access Control** 

   This endpoint requires the user to have one of the following roles:
   - **management**
   - **software_dev**
   - **content_admin**
   - **content_mgmt**

- **Abstract Pseudocode for `get_users`** 

  1. **Initialize Function**:  
     - Accept status (optional, `active`, `inactive`, `partial_restrict`, `full_restrict`, `deactivated`, `pending_delete`, `temp_ban`, `perm_ban`, `pending_delete_ban`, `pending_delete_inactive`, `deleted`),  
       sort (optional, `asc`, `desc`), database session, and current employee as inputs.

  2. **Transform Status**:
     - If a status is provided in the request, transform it to its code form.
     - If status is invalid or cannot be transformed, raise a bad request error.

  3. **Fetch Users**:
     - Query the database to fetch the users based on the provided status and sort criteria.

  4. **Return Response**:
     - If no users are found, return a response indicating no users yet.
     - Else, provide the response containing the list of users.

- **API Documentation** 

   [Get Users Admin Doc](https://venkatpaik17.github.io/VPKonnect/#tag/Admin/operation/get_users_api_v0_admin_users_get)

- **Database Tables Affected and Triggers involved** 

   *(NA)*

- **Postman Scripts Flow** 
  - **Pre-request**: 
    1. Manage Authorization
       - Gets the value of the `JWT` environment variable.
       - If the `JWT` variable is empty or doesn't exist, removes the `Authorization` header from the request.

  - **Post-response**: 
    1. Set New Access Token
       - Parse Response JSON.
       - Checks if the response code is `200 (OK)` and the response contains an access_token.
       - If both are true, saves the access_token to the `JWT` environment variable, and indicates to resend the request.

<br>

#### Get User - Admin

- **Access Control** 

   This endpoint requires the user to have one of the following roles:
   - **content_admin**
   - **content_mgmt**

- **Abstract Pseudocode for `user_profile_details`** 

  1. **Initialize Function**:  
     - Accept username, database session, and current employee as inputs.

  2. **Fetch User**:  
     - Query the database to fetch the user using the provided username.  
     - If the user is not found, raise a not found error.

  3. **Fetch Number of Posts**:  
     - Query the database to fetch the number of posts for the user.

  4. **Fetch Number of Followers and Following**:  
     - Query the database to fetch the number of followers and following for the user.

  5. **Format User Details**:  
     - Prepare the user details response containing profile information (profile picture, representation ID, name, username, email, phone number, dob, age, gender, country, account visibility, bio, status, type, verification, user creation datetime), along with the number of posts, followers, and following.

  6. **Return Response**:  
     - Provide the formatted user details as the response.

- **API Documentation** 

   [User Profile Details Admin Doc](https://venkatpaik17.github.io/VPKonnect/#tag/Admin/operation/user_profile_details_api_v0_admin_users__username__get)

- **Database Tables Affected and Triggers involved** 

   *(NA)*

- **Postman Scripts Flow** 
  - **Pre-request**: 
    1. Manage Authorization
       - Gets the value of the `JWT` environment variable.
       - If the `JWT` variable is empty or doesn't exist, removes the `Authorization` header from the request.

  - **Post-response**: 
    1. Set New Access Token
       - Parse Response JSON.
       - Checks if the response code is `200 (OK)` and the response contains an access_token.
       - If both are true, saves the access_token to the `JWT` environment variable, and indicates to resend the request.

<br>

#### Get Posts - Admin

- **Access Control** 

   This endpoint requires the user to have one of the following roles:
   - **content_admin**
   - **content_mgmt**

- **Abstract Pseudocode for `get_all_user_posts`** 

  1. **Initialize Function**:  
     - Accept username, status (optional, `published`, `draft`, `banned`, `flagged_banned`, `hidden`, `removed`, `flagged_deleted`), limit, last post ID, database session, and current employee as inputs.

  2. **Transform Status**:  
     - If status is provided, transform it to its code form.  
     - If status is invalid or cannot be transformed, raise a bad request error.

  3. **Fetch User**:  
     - Query the database to fetch the user by username.  
     - If the user is not found, raise a not found error.

  4. **Fetch Posts**:  
     - Query the database to fetch posts based on the provided status, limit, and last post ID.  
     - If no posts are found:
       - If last post ID is provided, return a message indicating no more posts available.  
       - Else, return a message indicating no posts exist.

  5. **Format Post Details**:  
     - Prepare the post response containing the post ID, image, number of likes, and number of comments.  
     - Do this for all the fetched posts.

  6. **Return Response**:  
     - If there are posts, provide the response containing the list of posts.

- **API Documentation** 

   [Get All User Posts Admin Doc](https://venkatpaik17.github.io/VPKonnect/#tag/Admin/operation/get_all_user_posts_api_v0_admin_users__username__posts_get)

- **Database Tables Affected and Triggers involved** 

   *(NA)*

- **Postman Scripts Flow** 
  - **Pre-request**: 
    1. Manage Authorization
       - Gets the value of the `JWT` environment variable.
       - If the `JWT` variable is empty or doesn't exist, removes the `Authorization` header from the request.

  - **Post-response**:
    1. Get Feed Posts
       - Parse Response JSON.
       - Calls a function (`myPackage.getPostsResponse`) from a required package (`vpkonnect_scripts`) and passes the JSON response to it.
       - Handle errors appropriately.

<br>

#### Get Employees - Admin

- **Access Control** 

   This endpoint requires the user to have one of the following roles:
   - **management**
   - **hr**

- **Abstract Pseudocode for `get_employees`** 

  1. **Initialize Function**:  
     - Accept status (optional, `active_regular`, `active_probationary`, `inactive_emp`, `terminated`, `suspended`), type (optional, `full_time`, `part_time`, `contract`), level (optional, `management`, `software_dev`, `hr`, `content_admin`, `content_mgmt`), sort (optional, `asc`, `desc`), database session, and current employee as inputs.

  2. **Transform Status and Type**:  
     - If status is provided, transform it to its code form.  
     - If type is provided, transform it to its code form.  
     - If level is provided, transform it to its code form.  
     - If any transformation fails, raise a bad request error.

  3. **Fetch Employees**:  
     - Query the database to fetch employees based on the provided status, type, level, and sorting order.  
     - If no employees are found, return a message indicating no employees exist.

  4. **Format Employee Details**:  
     - Prepare the employee response containing the employee details such as emp ID, name, work email, designation, profile picture, dob, age, gender, join date, type, supervisor (if applicable), contact info, location info, aadhaar, pan, status and employee creation datetime.
     - Do this for all the fetched employees.

  5. **Return Response**:  
     - If there are employees, provide the response containing the list of employees.

- **API Documentation** 

   [Get Employees Admin Doc](https://venkatpaik17.github.io/VPKonnect/#tag/Admin/operation/get_employees_api_v0_admin_employees_get)

- **Database Tables Affected and Triggers involved** 

   *(NA)*

- **Postman Scripts Flow** 
  - **Pre-request**: 
    1. Manage Authorization
       - Gets the value of the `JWT` environment variable.
       - If the `JWT` variable is empty or doesn't exist, removes the `Authorization` header from the request.

  - **Post-response**: 
    1. Set New Access Token
       - Parse Response JSON.
       - Checks if the response code is `200 (OK)` and the response contains an access_token.
       - If both are true, saves the access_token to the `JWT` environment variable, and indicates to resend the request.

<br>

#### Get Post - Admin

- **Access Control** 

   This endpoint requires the user to have one of the following roles:
   - **content_admin**
   - **content_mgmt**

- **Abstract Pseudocode for `get_post`** 

  1. **Initialize Function**:  
     - Accept post ID, database session, and current employee as inputs.

  2. **Fetch Post**:  
     - Query the database to fetch the post using the given post ID.  
     - If the post is not found, raise a not found error.

  3. **Fetch Post Owner**:  
     - Query the database to fetch the user (post owner) using the user ID.  
     - If the user is not found, raise a not found error.

  4. **Format Post Details**:
     - Prepare the post response containing post ID, image, caption, status, number of likes, number of comments, post owner details, time since post creation, post creation datetime, ban status, deletion status.

  5. **Return Response**:  
     - Provide the response containing the formatted post details.

- **API Documentation** 

   [Get Post Admin Doc](https://venkatpaik17.github.io/VPKonnect/#tag/Admin/operation/get_post_api_v0_admin_posts__post_id__get)

- **Database Tables Affected and Triggers involved** 

   *(NA)*

- **Postman Scripts Flow** 
  - **Pre-request**: 
    1. Manage Authorization
       - Gets the value of the `JWT` environment variable.
       - If the `JWT` variable is empty or doesn't exist, removes the `Authorization` header from the request.

  - **Post-response**: 
    1. Set New Access Token
       - Parse Response JSON.
       - Checks if the response code is `200 (OK)` and the response contains an access_token.
       - If both are true, saves the access_token to the `JWT` environment variable, and indicates to resend the request.

<br>

#### Get Comment - Admin

- **Access Control** 

   This endpoint requires the user to have one of the following roles:
   - **content_admin**
   - **content_mgmt**

- **Abstract Pseudocode for `get_comment`** 

  1. **Initialize Function**:  
     - Accept comment ID, database session, and current employee as inputs.

  2. **Fetch Comment**:  
     - Query the database to fetch the comment using the given comment ID.  
     - If the comment is not found, raise a not found error.

  3. **Fetch Comment Owner**:  
     - Query the database to fetch the user (comment owner) using the user ID.  
     - If the user is not found, raise a not found error.

  4. **Format Comment Details**:  
     - Prepare the comment response containing comment ID, content, status, number of likes, comment owner details, time since comment creation, comment creation datetime, ban status, deletion status.

  5. **Return Response**:  
     - Provide the response containing the formatted comment details.

- **API Documentation** 

   [Get Comment Admin Doc](https://venkatpaik17.github.io/VPKonnect/#tag/Admin/operation/get_comment_api_v0_admin_comments__comment_id__get)

- **Database Tables Affected and Triggers involved** 

   *(NA)*

- **Postman Scripts Flow** 
  - **Pre-request**: 
    1. Manage Authorization
       - Gets the value of the `JWT` environment variable.
       - If the `JWT` variable is empty or doesn't exist, removes the `Authorization` header from the request.

  - **Post-response**: 
    1. Set New Access Token
       - Parse Response JSON.
       - Checks if the response code is `200 (OK)` and the response contains an access_token.
       - If both are true, saves the access_token to the `JWT` environment variable, and indicates to resend the request.

<br>

#### App Activity Metrics - Admin

- **Access Control** 

   This endpoint requires the user to have one of the following roles:
   - **management**
   - **software_dev**
   - **content_admin**

- **Abstract Pseudocode for `app_activity_metrics`** 

  1. **Initialize Function**:  
     - Accept start date, end date, database session, and current employee as inputs.

  2. **Fetch Metrics**:
     - Query the database to:
       - Get app user metrics for the specified date range.
       - Get app post metrics for the specified date range.
       - Get app comment metrics for the specified date range.
       - Get app post like metrics for the specified date range.
       - Get app comment like metrics for the specified date range.
       - Get users with the maximum number of posts for the specified date range.
       - Get users who commented the most for the specified date range.
       - Get posts with the maximum number of comments for the specified date range.
       - Get posts with the maximum number of likes for the specified date range.
       - Get comments with the maximum number of likes for the specified date range.
       - Get users with the maximum number of followers for the specified date range.
       - Get users with the maximum number of following for the specified date range.

  3. **Format Response**:  
     - Prepare a response containing:
       - User metrics
       - Post metrics
       - Comment metrics
       - Post like metrics
       - Comment like metrics
       - Users with the maximum number of posts
       - Users who commented the most
       - Posts with the maximum number of comments
       - Posts with the maximum number of likes
       - Comments with the maximum number of likes
       - Users with the maximum number of followers
       - Users with the maximum number of following

  4. **Return Response**:  
     - Provide the response containing the formatted app activity metrics.

- **API Documentation** 

   [App Activity Metrics Doc](https://venkatpaik17.github.io/VPKonnect/#tag/Admin/operation/app_activity_metrics_api_v0_admin_app_metrics_get)

- **Database Tables Affected and Triggers involved** 

   *(NA)*

- **Postman Scripts Flow** 
  - **Pre-request**: 
    1. Manage Authorization
       - Gets the value of the `JWT` environment variable.
       - If the `JWT` variable is empty or doesn't exist, removes the `Authorization` header from the request.

  - **Post-response**: 
    1. Set New Access Token
       - Parse Response JSON.
       - Checks if the response code is `200 (OK)` and the response contains an access_token.
       - If both are true, saves the access_token to the `JWT` environment variable, and indicates to resend the request.

<br>

### Auth Routes 

#### User Login

- **Access Control** 

   *(NA)*

- **Abstract Pseudocode for `user_login`** 

  1. **Initialize Function**:  
     - Accept user credentials (`username` and `password`), device info, database session, and logger as inputs.

  2. **Prepare Login Request Object**:
     - Create an request object to hold username, password, and device info.

  3. **Validate Username**:  
     - Check if the username is an email or standard username.

  4. **Fetch User**:  
     - Query the database to retrieve the user using the provided username or email, not in deleted status. 
     - If no user is found, raise a forbidden error.

  5. **Verify Password**:  
     - Compare the provided password with the stored hashed password.  
     - If the passwords do not match, raise a forbidden error.

  6. **Account Verification Check**:  
     - If the account is not verified, raise a forbidden error instructing the user to verify their account.

  7. **Handle Deleted Accounts**:  
     - If the account status is pending delete inactive or pending delete ban, raise a gone error with the appropriate message.

  8. **Fetch Active Restriction/Ban Details**:  
     - Query the database to fetch any active restriction or ban entry for the user.  

  9. **Activate or Restrict/Ban Account**:  
     - If the user account is deactivated or inactive, activate it.  
     - If a restriction or ban exists, update the user status accordingly as per restriction or ban.

  10. **Validate Ban Status**:  
     - If the user is under temporary or permanent ban, raise a forbidden error with the appropriate ban details.

  11. **Generate Tokens**:  
     - Create access and refresh tokens using user-specific claims (user details and device info).  

  12. **Handle Existing Sessions**:  
     - Invalidate any previous active session for the same device info.  
     
  13. **Prepare User Session and User Auth Track Entry**
     - Create a new user session and auth track entry with provided details.  
     - Add the user session and auth track to the database and commit the changes.

  14. **Handle Errors**:  
     - Rollback the transaction on any error. 
     - Blacklist refresh token if generated.
     - Log the error and return an appropriate error response.

  15. **Prepare Token Data**:  
     - Encode the access token as JSON.  
     - Set the refresh token as an HTTP-only, secure cookie.

  16. **Return Response**:  
     - Provide the response containing the access token with refresh token as cookie.

- **API Documentation** 

   [User Login Doc](https://venkatpaik17.github.io/VPKonnect/#tag/Authentication/operation/user_login_api_v0_users_login_post)

- **Database Tables Affected and Triggers involved** 
  - **Tables**: `user`, `user_session`, `user_auth_track`, `activity_detail`, `user_account_history`, `post`, `comment`, `post_like`, `comment_like`, `user_follow_association`  

  - **Triggers**: `user_auth_track_logout_trigger`, `user_update_activity_detail_trigger`, `update_user_account_history_trigger`, `user_status_update_unhide_trigger`, `post_status_update_unhide_trigger`, `comment_status_update_unhide_trigger`

- **Postman Scripts Flow** 
  - **Pre-request**: None

  - **Post-response**: 
    1. Saving Access Token from the Response to Postman Environment Variable
       - Parse Response JSON.
       - Checks if the response code is `200 (OK)`.
       - If so, checks if the JSON response contains an `access_token`.
       - If the `access_token` exists, it saves it to an environment variable named `JWT`.
       - Handle errors appropriately.
    2. Saving Device Info from the Form-data to Postman Environment Variable
       - Gets form data from the request body.
       - Searches the form data for a parameter named `user_device_info`.
       - If found, saves the value of `user_device_info` to an environment variable named `device_info`.
       - Handle errors appropriately.

<br>

#### Token Refresh - User

- **Access Control** 

   *(NA)*

- **Abstract Pseudocode for `refresh_token_user`** 

  1. **Initialize Function**:  
     - Accept refresh token (as a cookie), database session, and logger as inputs.

  2. **Validate Refresh Token in Request**:  
     - Check if the refresh token is provided in the request.
     - If not, raise a bad request error, indicating refresh token required.

  3. **Verify Refresh Token**:  
     - Decode and verify the refresh token.  
     - Retrieve the token claims (e.g., email, type, device info).  

  4. **Check Token Blacklist**:  
     - Verify the token's unique ID against the blacklist.  
     - If the token is blacklisted, raise an unauthorized error indicating denied access, token invalid/revoked.

  5. **Generate New Access Token**:  
     - Generate a new access token using the extracted claims.
     - Prepare a response object for the access token.
     - Encode the new access token as JSON. 

  6. **Handle Expired Refresh Token**:
     - If the refresh token is expired:
       - Generate a new refresh token using the extracted claims.  
       - Set the new refresh token in the response as a secure, HTTP-only cookie.  

  7. **Fetch User**:
     - Query the database to fetch the user using their email, not in deleted status
     - If user is not found, raise a not found error.
     - If user’s profile is deactivated, raise a profile not found error.
     - If user is banned, raise a forbidden error.

  8. **Update User Auth Track Entries**:  
     - Retrieve the current active refresh token entry using its unique ID.  
     - Update the existing refresh token entry as expired.
     - Add a new user auth track entry for the new refresh token.  
     - Commit the changes to the database.

  9. **Handle Errors**:  
     - Rollback the transaction on any error.  
     - Log the error and raise an appropriate error response.

  10. **Validate Active Refresh Token**:
     - If the refresh token is not expired, check its active status.  
     - If the token is not active, raise an unauthorized error indicating denied access, token invalid/revoked.

  11. **Return Response**:  
     - Provide the response containing the access token with refresh token as cookie.

- **API Documentation** 

   [Refresh Token User Doc](https://venkatpaik17.github.io/VPKonnect/#tag/Authentication/operation/refresh_token_user_api_v0_users_token_refresh_post)

- **Database Tables Affected and Triggers involved** 
  - **Tables**: `user_auth_track`  

  - **Triggers**: None

- **Postman Scripts Flow** 

   *(NA)*

<br>

#### User logout

- **Access Control** 

   *(NA)*

- **Abstract Pseudocode for `user_logout`** 

  1. **Initialize Function**:  
     - Accept username, device_info, flow  (`user`, `admin`), action (`one`, `all`), refresh token (as a cookie), database session, and logger as inputs.  

  2. **User Logout Flow**:  
     - If the flow is `user`:
       - Check for the presence of the refresh token.  
       - If refresh token is missing, raise a bad request error indicating refresh token required.
       - Decode the refresh token to extract the token claims (user email and refresh token ID).  
       - Query the database to fetch the user using their email, not in deleted status.  
       - If user is not found, raise a not found error. 
       - If there is a username mismatch, raise a forbidden error.
     - If the flow is `admin`:
       - Query the database to fetch the user using their username, not in deleted status.  
       - If user is not found, raise a not found error.
     - If the flow is not valid, raise a bad request error.

  3. **Process Logout Action**:
     - If the logout action is `one`:
       - Fetch the active user session entry using the user ID and device info.
       - If no active session is found, raise a not found error.
       - Mark the user session as not active.
     - If the logout action is `all`:
       - Fetch all active user auth track entries.
       - If not found:
         - If logout flow is `admin`, return user is already logged out.
         - If not, raise a not found error.
       - Fetch all active user session entries.
       - If not found:
         - If logout flow is `admin`, return user is already logged out.
         - If not, raise a not found error.
       - Mark the user sessions as not active.
       - Commit the changes to the database.

  4. **Blacklist Refresh Token**:
     - If logout action is `one` and a refresh token ID is provided, blacklist the refresh token.  
     - If logout action is `all`, blacklist all refresh tokens associated with the user.

  5. **Handle Errors**:
     - Rollback the transaction on any error.  
     - Log the error and raise an appropriate error response.

  6. **Prepare Logout Response**:
     - Prepare a response indicating the successful logout of the user.
     - Delete the refresh token cookie from the response.

  7. **Print Blacklist Cache**:  
     - Print the blacklist cache to check which tokens have been blacklisted for debugging.

  8. **Return Response**:  
     - Provide a response with a success message indicating the user has been logged out.

- **API Documentation** 

   [User Logout Doc](https://venkatpaik17.github.io/VPKonnect/#tag/Authentication/operation/user_logout_api_v0_users_logout_post)

- **Database Tables Affected and Triggers involved** 
  - **Tables**: `user_session`, `user_auth_track`  

  - **Triggers**: `user_auth_track_logout_trigger`

- **Postman Scripts Flow** 
  - **Pre-request**: None
   
  - **Post-response**:
    1. Unset Environment variables
       - Checks if the response code is `200 (OK)`.
       - If so, removes the `JWT` and `device_info` environment variables.

<br>

#### Employee Login

- **Access Control** 

   *(NA)*

- **Abstract Pseudocode for `employee_login`** 

  1. **Initialize Function**:  
     - Accept employee credentials (`username` and `password`), device info, database session, and logger as inputs.

  2. **Prepare Login Request Object**:
     - Create an request object to hold username, password, and device info.

  3. **Validate Username**:  
     - Check if the username is an email or standard username.

  4. **Fetch Employee**:  
     - Query the database to retrieve the employee using the employee ID or email, not in terminated status. 
     - If no employee is found, raise a forbidden error.
     - If employee is suspended, raise a forbidden error.

  5. **Verify Password**:  
     - Compare the provided password with the stored hashed password.  
     - If the passwords do not match, raise a forbidden error.

  6. **Generate Tokens**:  
     - Create access and refresh tokens using employee-specific claims (work email, designation, and device info).
     - Retrieve refresh token unique ID.

  7. **Prepare Employee Session and Employee Auth Track Entries**:  
     - Create a new employee session and auth track entry with provided details.  
     - Add the employee session and auth track to the database and commit the changes.

  8. **Handle Errors**:
     - Rollback the transaction on any error. 
     - Blacklist the refresh token.
     - Log the error and return an appropriate error response.

  9. **Prepare Token Data**:  
     - Encode the access token as JSON.  
     - Set the refresh token as an HTTP-only, secure cookie.

  10. **Return Response**:  
     - Provide the response containing the access token with refresh token as cookie.

- **API Documentation** 

   [Employee Login Doc](https://venkatpaik17.github.io/VPKonnect/#tag/Authentication/operation/employee_login_api_v0_employees_login_post)

- **Database Tables Affected and Triggers involved** 
  - **Tables**: `employee_session`, `employee_auth_track`  

  - **Triggers**: None

- **Postman Scripts Flow** 
  - **Pre-request**: None

  - **Post-response**: 
    1. Saving Access Token from the Response to Postman Environment Variable
       - Parse Response JSON.
       - Checks if the response code is `200 (OK)`.
       - If so, checks if the JSON response contains an `access_token`.
       - If the `access_token` exists, it saves it to an environment variable named `JWT`.
       - Handle errors appropriately.
    2. Saving Device Info from the Form-data to Postman Environment Variable
       - Gets form data from the request body.
       - Searches the form data for a parameter named `employee_device_info`.
       - If found, saves the value of `employee_device_info` to an environment variable named `device_info`.
       - Handle errors appropriately.

<br>

#### Token Refresh - Employee

- **Access Control** 

   *(NA)*

- **Abstract Pseudocode for `refresh_token_employee`** 

  1. **Initialize Function**:  
     - Accept refresh token (as a cookie), database session, and logger as inputs.

  2. **Validate Refresh Token in Request**:  
     - Check if the refresh token is provided in the request.
     - If not, raise a bad request error, indicating refresh token required.

  3. **Verify Refresh Token**:  
     - Decode and verify the refresh token.  
     - Retrieve the token claims (e.g., work email, designation, device info).  

  4. **Check Token Blacklist**:  
     - Verify the token's unique ID against the blacklist.  
     - If the token is blacklisted, raise an unauthorized error indicating denied access, token invalid/revoked.

  5. **Generate New Access Token**:  
     - Generate a new access token using the extracted claims.
     - Prepare a response object for the access token.
     - Encode the new access token as JSON. 

  6. **Handle Expired Refresh Token**:
     - If the refresh token is expired:
       - Generate a new refresh token using the extracted claims.  
       - Set the new refresh token in the response as a secure, HTTP-only cookie.  

  7. **Fetch Employee**:
     - Query the database to fetch the employee using their work email, not in suspended or terminated status
     - If employee is not found, raise a not found error.

  8. **Update Employee Auth Track Entries**:  
     - Retrieve the current active refresh token entry using its unique ID.  
     - Update the existing refresh token entry as expired.
     - Add a new employee auth track entry for the new refresh token.  
     - Commit the changes to the database.

  9. **Handle Errors**:  
     - Rollback the transaction on any error.  
     - Log the error and raise an appropriate error response.

  10. **Validate Active Refresh Token**:
     - If the refresh token is not expired, check its active status.  
     - If the token is not active, raise an unauthorized error indicating denied access, token invalid/revoked.

  11. **Return Response**:  
     - Provide the response containing the access token with refresh token as cookie.

- **API Documentation** 

   [Refresh Token Employee Doc](https://venkatpaik17.github.io/VPKonnect/#tag/Authentication/operation/refresh_token_employee_api_v0_employees_token_refresh_post)

- **Database Tables Affected and Triggers involved** 
  - **Tables**: `employee_auth_track`  

  - **Triggers**: None

- **Postman Scripts Flow** 

   *(NA)*

<br>

#### Employee Logout

- **Access Control** 

   *(NA)*

- **Abstract Pseudocode for `employee_logout`** 

  1. **Initialize Function**:  
     - Accept emp ID, device_info, action (`one`, `all`), refresh token (as a cookie), database session, and logger as inputs.  

  2. **Validate Refresh Token in Request**:  
     - Check if the refresh token is provided in the request.
     - If not, raise a bad request error, indicating refresh token required.

  3. **Decode Refresh Token**:  
     - Decode the refresh token and extract the token claims (e.g., work email, designation, device info).

  4. **Fetch Employee**:
     - Query the database to fetch the employee using their work email, not in suspended or terminated status
     - If employee is not found, raise a not found error.
     - If there is emp ID mismatch, raise a forbidden error.

  5. **Process Logout Action**:
     - If the logout action is `one`:
       - Fetch the active employee session entry using the employee ID and device info.
       - If no active session is found, raise a not found error.
       - Mark the employee session as not active.
     - If the logout action is `all`:
       - Fetch all active employee auth track entries.
       - If not found, raise a not found error.
       - Fetch all active employee session entries.
       - If not found, raise a not found error.
       - Mark the employee sessions as not active.
       - Commit the changes to the database.

  6. **Blacklist Refresh Token**:
     - If logout action is `one` and a refresh token ID is provided, blacklist the refresh token.  
     - If logout action is `all`, blacklist all refresh tokens associated with the employee.

  7. **Handle Errors**:
     - Rollback the transaction on any error.  
     - Log the error and raise an appropriate error response.

  8. **Prepare Logout Response**:
     - Prepare a response indicating the successful logout of the employee.
     - Delete the refresh token cookie from the response.

  9.  **Print Blacklist Cache**:  
     - Print the blacklist cache to check which tokens have been blacklisted for debugging.

  10. **Return Response**:
     - Provide a response with a success message indicating the employee has been logged out.

- **API Documentation** 

   [Employee Logout Doc](https://venkatpaik17.github.io/VPKonnect/#tag/Authentication/operation/employee_logout_api_v0_employees_logout_post)

- **Database Tables Affected and Triggers involved** 
  - **Tables**: `employee_session`, `employee_auth_track`  

  - **Triggers**: `employee_auth_track_logout_trigger`

- **Postman Scripts Flow** 
  - **Pre-request**: None

  - **Post-response**:
    1. Unset Environment variables
       - Checks if the response code is `200 (OK)`.
       - If so, removes the `JWT` and `device_info` environment variables.

<br>

### Comment Routes

#### Edit Comment

- **Access Control** 

   This endpoint requires the user to have one of the following roles:
   - **user**

- **Abstract Pseudocode for `edit_comment`** 

  1. **Initialize Function**:  
     - Accept comment ID, content, database session, logger, and current user as inputs.

  2. **Retrieve Current User**:  
     - Query the database to fetch the current user using their email.  
     - Ensure the current user's status is not inactive/deactivated/banned/deleted.  

  3. **Check User Restriction**:  
     - If the user is under full or partial restriction, raise a bad request error indicating they cannot edit comments.  

  4. **Fetch Comment**:  
     - Query the database to retrieve the comment using the provided comment ID.  
     - Ensure the comment is not hidden, flagged deleted, or removed.  
     - If no comment is found, raise a not found error.  

  5. **Validate Comment Ownership**:  
     - Check if the current user is the owner of the comment.  
     - If not, raise a forbidden error.  

  6. **Comment Status Validation**:  
     - If the comment is banned or flagged to be banned, raise a bad request error indicating the comment cannot be edited.  

  7. **Process Comment Update**:  
     - Update the comment content in the database.  
     - Commit the changes.

  8. **Handle Errors**:  
     - Rollback the transaction on any error.  
     - Log the error and return an appropriate error response.  

  9. **Format Comment Details**:  
     - Construct a response object with comment ID, user details, updated content, number of likes, time since comment creation, current user’s like status and tag.  

  10. **Return Response**:  
     - Provide a success message with the updated comment details in a structured response.

- **API Documentation** 

   [Edit Comment Doc](https://venkatpaik17.github.io/VPKonnect/#tag/Comments/operation/edit_comment_api_v0_comments__comment_id__put)

- **Database Tables Affected and Triggers involved** 
  - **Tables**: `comment`    

  - **Triggers**: None

- **Postman Scripts Flow** 
  - **Pre-request**: 
    1. Manage Authorization
       - Gets the value of the `JWT` environment variable.
       - If the `JWT` variable is empty or doesn't exist, removes the `Authorization` header from the request.

  - **Post-response**: 
    1. Set New Access Token
       - Parse Response JSON.
       - Checks if the response code is `200 (OK)` and the response contains an access_token.
       - If both are true, saves the access_token to the `JWT` environment variable, and indicates to resend the request.

<br>

#### Remove Comment

- **Access Control** 

   This endpoint requires the user to have one of the following roles:
   - **user**

- **Abstract Pseudocode for `remove_comment`** 

  1. **Initialize Function**:  
     - Accept comment ID, database session, logger, and current user as inputs.

  2. **Retrieve Current User**:  
     - Query the database to fetch the current user using their email.  
     - Ensure the current user's status is not inactive/deactivated/banned/deleted.

  3. **Fetch Comment**:  
     - Query the database to retrieve the comment using the provided comment ID.  
     - Ensure the comment is not hidden, flagged deleted, or removed.  
     - If no comment is found, raise a not found error.

  4. **Comment Status Validation**:  
     - If the comment is banned, raise a bad request error indicating the comment cannot be deleted.

  5. **Fetch Post**:  
     - Query the database to retrieve the post associated with the comment.  
     - Ensure the post is not hidden, in draft, banned, flagged to be banned, flagged deleted, or removed.  
     - If no post is found, raise a not found error.

  6. **Check Authorization**:  
     - Ensure the current user is either the post owner or the comment owner.  
     - If not, raise a forbidden error, indicating they cannot delete the comment.

  7. **Check User Restriction**:  
     - If the current user is under full restriction and is not the post owner, raise a bad request error if trying to delete a flagged to be banned comment.

  8. **Track Comment Status**:  
     - Store the current status of the comment before making any changes.

  9. **Process Comment Deletion**:  
     - If the comment is *flagged to be banned*, change the status to *flagged deleted*.
     - If the comment is not flagged, change the status to *removed*.
     - Commit the changes to the database.

  10. **Handle Errors**:  
     - Rollback the transaction on any error.  
     - Log the error and return an appropriate error response.

  11. **Return Response**:  
     - Provide a success message indicating the comment has been successfully deleted, including the previous status of the comment.

- **API Documentation** 

   [Remove Comment Doc](https://venkatpaik17.github.io/VPKonnect/#tag/Comments/operation/remove_comment_api_v0_comments__comment_id__delete)

- **Database Tables Affected and Triggers involved** 
  - **Tables**: `comment`, `comment_like`  

  - **Triggers**: `comment_status_update_delete_trigger`

- **Postman Scripts Flow** 
  - **Pre-request**: 
    1. Manage Authorization
       - Gets the value of the `JWT` environment variable.
       - If the `JWT` variable is empty or doesn't exist, removes the `Authorization` header from the request.

  - **Post-response**: 
    1. Set New Access Token
       - Parse Response JSON.
       - Checks if the response code is `200 (OK)` and the response contains an access_token.
       - If both are true, saves the access_token to the `JWT` environment variable, and indicates to resend the request.

<br>

#### Like/Unlike Comment

- **Access Control** 

   This endpoint requires the user to have one of the following roles:
   - **user**

- **Abstract Pseudocode for `like_unlike_comment`** 

  1. **Initialize Function**:  
     - Accept comment ID, action (`like`, `unlike`), database session, logger, and current user as inputs.

  2. **Retrieve Current User**:  
     - Query the database to fetch the current user using their email.  
     - Ensure the current user's status is not inactive/deactivated/banned/deleted.

  3. **Check User Restriction**:  
     - If the current user is under full or partial restriction, raise a bad request error indicating they cannot like or unlike comments.

  4. **Fetch Comment**:  
     - Query the database to retrieve the comment using the provided comment ID.  
     - Ensure the comment is not hidden, flagged deleted, or removed.  
     - If no comment is found, raise a not found error.

  5. **Comment Status Validation**:  
     - If the comment is banned or flagged to be banned, raise a bad request error indicating the comment cannot be liked or unliked.

  6. **Handle Like/Unlike Action**:
     - **If the action is `like`**:
       - Check if the user has already liked the comment. If so, raise a conflict error.
       - Create a new like entry for the comment and add it to the database.
     - **If the action is `unlike`**:
       - Check if the user has already liked the comment. If not, raise a not found error.
       - Update the existing status of like entry from *active* to *removed*.
     - Commit the changes to the database.

  7. **Handle Errors**:  
     - Rollback the transaction on any error.  
     - Log the error and return an appropriate error response.

  8. **Return Response**:  
     - Provide a success message indicating the comment has been liked or unliked successfully.

- **API Documentation** 

   [Like Unlike Comment Doc](https://venkatpaik17.github.io/VPKonnect/#tag/Comments/operation/like_unlike_comment_api_v0_comments__comment_id__like_post)

- **Database Tables Affected and Triggers involved** 
  - **Tables**: `comment_like`  

  - **Triggers**: None

- **Postman Scripts Flow** 
  - **Pre-request**: 
    1. Manage Authorization
       - Gets the value of the `JWT` environment variable.
       - If the `JWT` variable is empty or doesn't exist, removes the `Authorization` header from the request.

  - **Post-response**: 
    1. Set New Access Token
       - Parse Response JSON.
       - Checks if the response code is `200 (OK)` and the response contains an access_token.
       - If both are true, saves the access_token to the `JWT` environment variable, and indicates to resend the request.

<br>

#### Get Comment Like Users

- **Access Control** 

   This endpoint requires the user to have one of the following roles:
   - **user**

- **Abstract Pseudocode for `get_comment_like_users`** 

  1. **Initialize Function**:  
     - Accept comment ID, limit, last like user ID, database session, and current user as inputs.

  2. **Retrieve Current User**:  
     - Query the database to fetch the current user using their email.  
     - Ensure the current user's status is not inactive/deactivated/banned/deleted.

  3. **Fetch Comment**:  
     - Query the database to retrieve the comment using the provided comment ID.  
     - Ensure the comment is not hidden, flagged deleted, or removed.  
     - If no comment is found, raise a not found error.

  4. **Comment Status Validation**:  
     - If the comment is banned or flagged to be banned, raise a bad request error indicating an invalid request.

  5. **Fetch Like Users**:  
     - Query the database to retrieve users who liked the comment using the comment ID, limit and last like user ID.  
     - Use the user ID of the last like user to fetch the next batch of users.

  6. **Handle No Like Users Found**:  
     - If no like users are found:  
       - If last like user ID is provided, return a message indicating no more users are available.  
       - Else, return a message indicating no users have liked the comment yet.

  7. **Format Comment Like Users Details**:  
     - For each user who liked the comment, construct a response object containing profile picture, username, whether the current user follows them. 

  8. **Return Response**:  
     - Provide the list of comment like users and pagination cursor.

- **API Documentation** 

   [Get Comment Like Users Doc](https://venkatpaik17.github.io/VPKonnect/#tag/Comments/operation/get_comment_like_users_api_v0_comments__comment_id__like_get)

- **Database Tables Affected and Triggers involved** 

   *(NA)*

- **Postman Scripts Flow** 
  - **Pre-request**: 
    1. Manage Authorization
       - Gets the value of the `JWT` environment variable.
       - If the `JWT` variable is empty or doesn't exist, removes the `Authorization` header from the request.

  - **Post-response**:
    1. Get Feed Posts
       - Parse Response JSON.
       - Calls a function (`myPackage.getAllCommentLikeUsersResponse`) from a required package (`vpkonnect_scripts`) and passes the JSON response to it.
       - Handle errors appropriately.

<br>

### Employee Routes

#### Create Employee

- **Access Control** 

   *(NA)*

- **Abstract Pseudocode for `create_employee`** 

  1. **Initialize Function**:  
     - Accept image, employee registration data, database session, and logger as inputs.

  2. **Validate Passwords**:
     - Ensure the provided password matches the confirmation password.
     - If they do not match, raise a bad request error.

  3. **Check Employee Existence**:  
     - Query the database to check if an employee with the provided work email already exists (excluding terminated employees).  
     - If an employee exists, raise a conflict error.

  4. **Hash Password**:  
     - Securely hash the provided password and update the request.

  5. **Generate Employee ID**:  
     - Use a database function to generate a unique employee ID based on the first name, last name, and join date.

  6. **Fetch Supervisor ID** (if applicable):  
     - If a supervisor is provided:  
       - Query the database to fetch the supervisor's ID using the supervisor’s employee ID, not in suspended or terminated status.  
       - If the supervisor is not found, raise a not found error.

  7. **Prepare Employee Entry**:  
     - Create a new employee entry with the provided details, including the generated employee ID and supervisor ID (if any).

  8. **Handle Employee-Specific Folders**:  
     - Create a subfolder for the employee's uploads, including a profile images subfolder.  
     - If these folders already exist, retrieve their paths.

  9. **Handle Profile Image**:  
     - Validate the and generate a unique name for the image.  
     - Save the image to the appropriate profile image folder.  
     - Update the employee's profile picture field with the image name.

  10. **Add the New Employee**:  
      - Add the new employee entry to the database and commit the changes.

  11. **Handle Errors**:  
      - Rollback the transaction on any error.  
      - Remove the created employee-specific folder..  
      - Log the error and return an appropriate error response.

  12. **Return Response**:  
      - Provide the new employee's details in the response.

- **API Documentation** 

   [Create Employee Doc](https://venkatpaik17.github.io/VPKonnect/#tag/Employees/operation/create_employee_api_v0_employees_register_post)

- **Database Tables Affected and Triggers involved** 
  - **Tables**: `employee`  

  - **Triggers**: `get_age_from_dob_1_trigger`

- **Postman Scripts Flow** 

   *(NA)*

<br>

### Post Routes

#### Create Post

- **Access Control** 

   This endpoint requires the user to have one of the following roles:
   - **user**

- **Abstract Pseudocode for `create_post`** 

  1. **Initialize Function**:  
     - Accept image file, post type (`publish`, `draft`), caption, database session, logger, and current user as inputs.  

  2. **Prepare Post Request Object**:  
     - Create a request object for the post using post type and caption.  

  3. **Retrieve Current User**:  
     - Query the database to fetch the current user using their email.
     - Ensure the current user's status is not inactive/deactivated/banned/deleted.  

  4. **Check User Restriction**:  
     - If the user is under full restriction, raise a bad request error, indicating they cannot create a new post.  

  5. **Process Image**:  
     - Validate and generate a unique name for the image.
     - Save the image to the appropriate posts subfolder.

  6. **Prepare Post Entry**:  
     - Create a new post entry with details.
     - Add the post to the database and commit the changes.  

  7. **Handle Errors**:  
     - Rollback the transaction on any error.
     - If an image was uploaded, remove the image from the storage.
     - Log the error and return an appropriate error response.  

  8. **Format Post Details**:
     - If the post is a draft:  
       - Construct a response object with post ID, status, image, and caption.  
       - Set the success message for saving a draft.  
     - If the post is published:  
       - Construct a response object with post ID, image, caption, number of likes, number of comments, current user’s like status, and time since post creation.  
       - Set the success message for publishing a post.  

  9. **Return Response**:  
     - Provide the success message and post details in a structured response.

- **API Documentation** 

   [Create Post Doc](https://venkatpaik17.github.io/VPKonnect/#tag/Posts/operation/create_post_api_v0_posts__post)

- **Database Tables Affected and Triggers involved** 
  - **Tables**: `post`
    
  - **Triggers**: None

- **Postman Scripts Flow** 
  - **Pre-request**: 
    1. Manage Authorization
       - Gets the value of the `JWT` environment variable.
       - If the `JWT` variable is empty or doesn't exist, removes the `Authorization` header from the request.

  - **Post-response**: 
    1. Set New Access Token
       - Parse Response JSON.
       - Checks if the response code is `200 (OK)` and the response contains an access_token.
       - If both are true, saves the access_token to the `JWT` environment variable, and indicates to resend the request.

<br>

#### Get Post

> [!IMPORTANT] 
> Make sure the **Automatically follow redirects** is **OFF** in Postman

- **Access Control** 

   This endpoint requires the user to have one of the following roles:
   - **user**

- **Abstract Pseudocode for `get_post`** 

  1. **Initialize Function**:  
     - Accept post ID, database session, and current user as inputs.  

  2. **Retrieve Current User**:  
     - Query the database to fetch the current user using their email.
     - Ensure the current user's status is not inactive/deactivated/banned/deleted.  

  3. **Fetch Post**:  
     - Query the database to retrieve the post using the provided post ID.
     - Ensure the post is not hidden, flagged deleted, or removed.
     - If no post is found, raise a not found error.  

  4. **Fetch Post Owner**:  
     - Query the database to retrieve the post owner using the post’s user ID.
     - If no owner is found, raise a not found error.  

  5. **Check Post Owner Status**:  
     - If the post owner is deactivated or permanently banned or deleted, redirect to the user profile.  

  6. **Check User Follower and Post Status**:  
     - Check if the current user follows the post owner.
     - If post owner is different than current user
        - If the post owner's account is private and the current user does not follow, redirect to the profile.  
        - If the post is banned, raise a forbidden error.
        - If the post is flagged for ban, set the `flagged` status and assign a tag indicating it is flagged.
        - If the post is in draft status, raise a forbidden error, indicating the user cannot access it.  

  7. **Format Post Details**:  
     - If the post is a draft:
       - Construct a response object with post ID, status, image, and caption.  
     - If the post is not a draft:
       - Construct a response object with Post ID, image, number of likes, number of comments, user details, caption, time since post creation, current user’s like status, post creation date and tag.  

  8. **Return Response**:  
     - Provide the post details in a structured response.

- **API Documentation** 

   [Get Post Doc](https://venkatpaik17.github.io/VPKonnect/#tag/Posts/operation/get_post_api_v0_posts__post_id__get)

- **Database Tables Affected and Triggers involved** 

   *(NA)*

- **Postman Scripts Flow** 
  - **Pre-request**:  
    1. Manage Authorization
       - Gets the value of the `JWT` environment variable.
       - If the `JWT` variable is empty or doesn't exist, removes the `Authorization` header from the request.

  - **Post-response**:  
    1. Set New Access Token, Get User Profile and Posts
       - Parse Response JSON.
       - Checks if the response code is `200 (OK)`.
       - If so, checks for an `access_token` and saves it to the `JWT` environment variable if found, indicates to resend request, and stops.
       - Checks if the response code is `303 (Redirect)`.
       - If it's a `303`, extracts the `Location` header.
       - If the `Location` header exists and contains a username and `profile` segment, fetches the user's profile using the `Location` URL.
       - If the profile fetch is successful, fetches the user's published posts using the username and the existing `Authorization` header.
       - If the posts fetch is successful, calls a function (`myPackage.getPostsResponse`) from a required package (`vpkonnect_scripts`) to process the posts.
       - Handle errors appropriately.

<br>

#### Edit Post

- **Access Control** 

   This endpoint requires the user to have one of the following roles:
   - **user**

- **Abstract Pseudocode for `edit_post`** 

  1. **Initialize Function**:  
     - Accept post ID, post type (`published`, `draft`), action (`edit`, `publish`), caption, image, database session, logger, and current user as inputs.  

  2. **Prepare Edit Request**:  
     - Create a request object for editing or publishing the post with the provided post ID, post type, action, and caption.

  3. **Retrieve Current User**:  
     - Query the database to fetch the current user using their email.
     - Ensure the current user's status is not inactive/deactivated/banned/deleted.  

  4. **Check User Restriction**:  
     - If the current user is under full restriction, raise a bad request error, indicating the user cannot edit posts.

  5. **Fetch Post**:  
     - Query the database to retrieve the post using the provided post ID.
     - Ensure the post is not hidden, flagged deleted, or removed.  
     - If no post is found, raise a not found error.

  6. **Check Post Ownership**:  
     - Ensure the current user is the owner of the post.
     - If not, raise a forbidden error.

  7. **Post Status Validation**:  
     - If the post is banned or flagged to be banned, raise a bad request error indicating no edits can be made.
     - If the post is published
        - If the post type is draft, raise a bad request error.
        - If image is uploaded, raise bad request error, indicating image cannot be replaced/updated.
     - If the post is in draft status and the post type is published, raise a bad request error.

  8. **Process Image**:  
     - If an image is provided:
        - Validate and generate a unique name for the image.
        - Save the image to the appropriate posts folder.
     - If no image is provided, keep the existing image.

  9. **Process Post Update**:  
     - If the action is to publish:
        - Change the post status to *published* and update the caption and image.
     - If the action is to edit:
        - Update the post's caption and image based on the post type (draft or published).
     - Commit the changes to the database.

  10. **Handle Errors**:  
     - Rollback the transaction on any error.
     - If an image was uploaded, remove the image from the storage.
     - Log the error and return an appropriate error response.

  11. **Format Post Details**:  
     - If the post is a draft and the action is edit, construct the response with the post's ID, status, caption, and image.
     - If the post is published, construct the response with the post’s ID, image, number of likes, number of comments, caption, user details, time since post creation, current user's like status, post creation date and tag.

  12. **Return Success Response**:  
     - Provide the success message along with the post details in a structured response.

- **API Documentation** 

   [Edit Post Doc](https://venkatpaik17.github.io/VPKonnect/#tag/Posts/operation/edit_post_api_v0_posts__post_id__put)

- **Database Tables Affected and Triggers involved** 
  - **Tables**: `post`  

  - **Triggers**: None

- **Postman Scripts Flow** 
  - **Pre-request**: 
    1. Manage Authorization
       - Gets the value of the `JWT` environment variable.
       - If the `JWT` variable is empty or doesn't exist, removes the `Authorization` header from the request.

  - **Post-response**: 
    1. Set New Access Token
       - Parse Response JSON.
       - Checks if the response code is `200 (OK)` and the response contains an access_token.
       - If both are true, saves the access_token to the `JWT` environment variable, and indicates to resend the request.

<br>

#### Remove Post

- **Access Control** 

   This endpoint requires the user to have one of the following roles:
   - **user**

- **Abstract Pseudocode for `remove_post`** 

  1. **Initialize Function**:  
     - Accept post ID, database session, logger, and current user as inputs.  

  2. **Retrieve Current User**:  
     - Query the database to fetch the current user using their email.
     - Ensure the current user's status is not inactive/deactivated/banned/deleted.  

  3. **Fetch Post**:  
     - Query the database to retrieve the post using the provided post ID.
     - Ensure the post is not hidden, flagged deleted, or removed.  
     - If no post is found, raise a not found error.

  4. **Post Status Validation**:  
     - If the post is banned, raise a bad request error indicating that banned posts cannot be deleted.

  5. **Check User Restriction**:  
     - If the current user is under full restriction:
       - Allow deletion only if the post status is flagged to be banned.
       - If the post status is not flagged to be banned, raise a bad request error.

  6. **Check Post Ownership**:  
     - Ensure the current user is the owner of the post.
     - If not, raise a forbidden error.

  7. **Track Post Status**:  
     - Store the current status of the post before making any changes.

  8. **Process Post Delete**:  
     - If the post is flagged to be banned, change the status to *flagged deleted*.
     - If the post is not flagged, change the status to *removed*.
     - Commit the changes to the database.

  9. **Handle Errors**:  
     - Rollback the transaction on any error.
     - Log the error and return an appropriate error response.

  10. **Return Success Response**:  
     - Provide a success message indicating the post has been successfully deleted, including the previous status of the post.

- **API Documentation** 

   [Remove Post Doc](https://venkatpaik17.github.io/VPKonnect/#tag/Posts/operation/remove_post_api_v0_posts__post_id__delete)

- **Database Tables Affected and Triggers involved** 
  - **Tables**: `post`, `post_like`, `comment`, `comment_like`
      
  - **Triggers**: `post_status_update_delete_trigger`, `comment_status_update_delete_trigger`

- **Postman Scripts Flow** 
  - **Pre-request**: 
    1. Manage Authorization
       - Gets the value of the `JWT` environment variable.
       - If the `JWT` variable is empty or doesn't exist, removes the `Authorization` header from the request.

  - **Post-response**: 
    1. Set New Access Token
       - Parse Response JSON.
       - Checks if the response code is `200 (OK)` and the response contains an access_token.
       - If both are true, saves the access_token to the `JWT` environment variable, and indicates to resend the request.

<br>

#### Like/Unlike Post

- **Access Control** 

   This endpoint requires the user to have one of the following roles:
   - **user**

- **Abstract Pseudocode for `like_unlike_post`** 

  1. **Initialize Function**:  
     - Accept post ID, action (`like`, `unlike`), database session, logger, and current user as inputs.

  2. **Retrieve Current User**:  
     - Query the database to fetch the current user using their email.
     - Ensure the current user's status is not inactive/deactivated/banned/deleted.

  3. **User Restriction Check**:  
     - If the current user is under full or partial restriction, raise a bad request error indicating they cannot like or unlike posts.

  4. **Fetch Post**:  
     - Query the database to retrieve the post using the provided post ID.
     - Ensure the post is not hidden, flagged deleted, or removed.  
     - If no post is found, raise a not found error.

  5. **Post Status Validation**:   
     - If the post is banned or flagged to be banned, or in draft status, raise a bad request error indicating the post cannot be liked/unliked.

  6. **Handle Like/Unlike Action**:
     - **If the action is `like`**:
       - Check if the user has already liked the post. If so, raise a conflict error.
       - Create a new like entry for the post and add it to the database.
     - **If the action is `unlike`**:
       - Check if the user has already liked the post. If not, raise a not found error.
       - Update the existing like entry from *active* to *removed*.
     - Commit the changes to the database.

  7. **Handle Errors**:  
     - Rollback the transaction on any error.
     - Log the error and return an appropriate error response.

  8. **Return Success Response**:  
     - Provide a message indicating the post has been liked or unliked successfully.

- **API Documentation** 

   [Like Unlike Post Doc](https://venkatpaik17.github.io/VPKonnect/#tag/Posts/operation/like_unlike_post_api_v0_posts__post_id__like_post)

- **Database Tables Affected and Triggers involved** 
  - **Tables**: `post_like`    

  - **Triggers**: None

- **Postman Scripts Flow** 
  - **Pre-request**: 
    1. Manage Authorization
       - Gets the value of the `JWT` environment variable.
       - If the `JWT` variable is empty or doesn't exist, removes the `Authorization` header from the request.

  - **Post-response**: 
    1. Set New Access Token
       - Parse Response JSON.
       - Checks if the response code is `200 (OK)` and the response contains an access_token.
       - If both are true, saves the access_token to the `JWT` environment variable, and indicates to resend the request.

<br>

#### Get Post Like Users 

- **Access Control** 

   This endpoint requires the user to have one of the following roles:
   - **user**

- **Abstract Pseudocode for `get_post_like_users`** 

  1. **Initialize Function**:  
     - Accept post ID, limit, last_like_user_id, database session, and current user as inputs.

  2. **Retrieve Current User**:  
     - Query the database to fetch the current user using their email.  
     - Ensure the current user's status is not inactive/deactivated/banned/deleted.  

  3. **Fetch Post**:  
     - Query the database to retrieve the post using the provided post ID.  
     - Ensure the post is not hidden, flagged deleted, or removed.  
     - If no post is found, raise a not found error.

  4. **Post Status Validation**:  
     - If the post is banned, flagged to be banned, or in draft status, raise a bad request error indicating an invalid request.

  5. **Fetch Like Users**:  
     - Query the database to retrieve users who liked the post using the post ID, limit and last like user ID.
     - Use the user ID of the last like user to fetch the next batch of users.

  6. **Handle No Like Users Found**:  
     - If no like users are found:  
       - If last like user ID is provided, return a message indicating no more users are available.  
       - Else, return a message indicating no users have liked the post yet.

  7. **Format Post Like Users Details**:  
     - For each user who liked the post, construct a response object containing profile picture, username, whether the current user follows them. 

  8. **Return Response**:  
     - Provide the list of post like users and pagination cursor.

- **API Documentation** 

   [Get Post Like Users Doc](https://venkatpaik17.github.io/VPKonnect/#tag/Posts/operation/get_post_like_users_api_v0_posts__post_id__like_get)

- **Database Tables Affected and Triggers involved** 

   *(NA)*

- **Postman Scripts Flow** 
  - **Pre-request**: 
    1. Manage Authorization
       - Gets the value of the `JWT` environment variable.
       - If the `JWT` variable is empty or doesn't exist, removes the `Authorization` header from the request.

  - **Post-response**:
    1. Get Feed Posts
       - Parse Response JSON.
       - Calls a function (`myPackage.getAllPostLikeUsersResponse`) from a required package (`vpkonnect_scripts`) and passes the JSON response to it.
       - Handle errors appropriately.

<br>

#### Create Comment

- **Access Control** 

   This endpoint requires the user to have one of the following roles:
   - **user**

- **Abstract Pseudocode for `create_comment`** 

  1. **Initialize Function**:  
     - Accept post ID, content, database session, logger, and current user as inputs.

  2. **Retrieve Current User**:  
     - Query the database to fetch the current user using their email.  
     - Ensure the current user's status is not inactive/deactivated/banned/deleted.

  3. **Check User Restriction**:  
     - If the current user is under full or partial restriction, raise a bad request error, indicating they cannot comment on the post.

  4. **Fetch Post**:  
     - Query the database to retrieve the post using the provided post ID.  
     - Ensure the post is not hidden, flagged deleted, or removed.  
     - If no post is found, raise a not found error.

  5. **Post Status Validation**:   
     - If the post is banned, flagged to be banned, or in draft status, raise a bad request error, indicating the post cannot be commented on.

  6. **Create a Comment**:  
     - Create a new comment entry with the provided details.
     - Add the comment to the database and commit the changes.

  7. **Handle Errors**:  
     - Rollback the transaction on any error.  
     - Log the error and return an appropriate error response.

  8. **Format Comment Details**:  
     - Construct a response object with comment ID, user details, content, number of likes, time since comment creation, current user’s like status and tag.

  9. **Return Response**:  
     - Provide a success message with the comment details in a structured response.

- **API Documentation** 

   [Create Comment Doc](https://venkatpaik17.github.io/VPKonnect/#tag/Posts/operation/create_comment_api_v0_posts__post_id__comments_post)

- **Database Tables Affected and Triggers involved** 
  - **Tables**: `comment`  

  - **Triggers**: None

- **Postman Scripts Flow** 
  - **Pre-request**: 
    1. Manage Authorization
       - Gets the value of the `JWT` environment variable.
       - If the `JWT` variable is empty or doesn't exist, removes the `Authorization` header from the request.

  - **Post-response**: 
    1. Set New Access Token
       - Parse Response JSON.
       - Checks if the response code is `200 (OK)` and the response contains an access_token.
       - If both are true, saves the access_token to the `JWT` environment variable, and indicates to resend the request.

<br>

#### Get Post Comments

- **Access Control** 

   This endpoint requires the user to have one of the following roles:
   - **user**

- **Abstract Pseudocode for `get_all_comments`** 

  1. **Initialize Function**:  
     - Accept post ID, limit, last comment ID, database session, and current user as inputs.

  2. **Retrieve Current User**:  
     - Query the database to fetch the current user using their email.  
     - Ensure the current user's status is not inactive/deactivated/banned/deleted.

  3. **Fetch Post**:  
     - Query the database to retrieve the post using the provided post ID.  
     - Ensure the post is not hidden, flagged deleted, or removed.  
     - If no post is found, raise a not found error.

  4. **Post Status Validation**:   
     - If the post is in draft, banned, or flagged to be banned status, raise a bad request error indicating the comments cannot be retrieved.

  5. **Retrieve Comments**:  
     - Fetch all comments for the post using the provided post ID and pagination parameters (limit, last comment ID).  
     - Ensure the comments retrieved are in published or flagged to be banned status.

  6. **Handle No Comments**:  
     - If no comments are found:  
       - If last comment ID is provided, return a message indicating no more comments are available.  
       - Else, return a message indicating no users have commented on the post yet.  

  7. **Aggregate Comment Data**:  
     - Extract all comment IDs from the retrieved comments.  
     - Fetch the like counts for these comment IDs.  
     - Determine which of these comments are liked by the current user.

  8. **Format Comment Details**:  
     - For each comment:  
       - Include ID, user details, content, number of likes, time since comment creation, current user's like status, and tag.
     - Construct a response object for each comment.

  9. **Return Response**:  
     - Provide the list of comments and pagination cursor in a structured response.

- **API Documentation** 

   [Get All Comments Doc](https://venkatpaik17.github.io/VPKonnect/#tag/Posts/operation/get_all_comments_api_v0_posts__post_id__comments_get)

- **Database Tables Affected and Triggers involved** 

   *(NA)*

- **Postman Scripts Flow** 
  - **Pre-request**: 
    1. Manage Authorization
       - Gets the value of the `JWT` environment variable.
       - If the `JWT` variable is empty or doesn't exist, removes the `Authorization` header from the request.

  - **Post-response**:
    1. Get Feed Posts
       - Parse Response JSON.
       - Calls a function (`myPackage.getAllCommentsResponse`) from a required package (`vpkonnect_scripts`) and passes the JSON response to it.
       - Handle errors appropriately.

<br>

### User Routes

#### Create User

- **Access Control** 

   *(NA)*

- **Abstract Pseudocode for `create_user`** 

  1. **Initialize Function**:
     - Accept user registration data, database session, logger, and optional profile image as inputs.

  2. **Check for Unverified Registration**:
     - Query the database for any unverified user with the same email.
     - If found, raise a conflict error.

  3. **Validate Passwords**:
     - Ensure the provided password matches the confirmation password.
     - If they do not match, raise a bad request error.

  4. **Check for Username or Email Duplicates**:
     - Verify that the username does not already exist.
     - Verify that the email is not already registered.
     - If either check fails, raise a conflict error.

  5. **Hash Password**:
     - Securely hash the provided password and update the user request.

  6. **Prepare User Entry**:
     - Generate a unique identifier for the user.
     - Create a new user entry using the registration data.

  7. **Create User-Specific Subfolders**:
     - Create subfolders for:
       - User-specific uploads.
       - Profile images.
       - Post images.
       - Appeal attachments.
     - If these folders already exist, retrieve their paths.

  8. **Handle Profile Image (If Provided)**:
     - Validate and generate a unique name for the image.
     - Save the image to the appropriate profile image subfolder.
     - Update the user's profile picture field with the image name.

  9. **Add User to Database**:
     - Add the new user to the database.
     - Commit the changes.

  10. **Error Handling**:
      - Rollback the transaction on database error.
      - Remove the user-specific folder.
      - If an image was uploaded, remove the image from the storage.
      - Log the error and return an appropriate error response.

  11. **Generate Verification Token**:
      - Create a verification token with user-specific claims.
      - Generate a verification link using the token.

  12. **Send Verification Email**:
      - Prepare email content, including the verification link.
      - Add the token to the verification token table.
      - Send the email using background tasks.

  13. **Error Handling**:
      - Rollback the transaction on any error
      - Log the error and return an appropriate error response.

  14. **Return Success Response**:
      - Notify the user that a verification email has been sent to their registered email address. 


- **API Documentation** 

   [Create User Doc](https://venkatpaik17.github.io/VPKonnect/#tag/Users/operation/create_user_api_v0_users_register_post)

- **Database Tables Affected and Triggers involved** 
  - **Tables**: `user`, `user_verification_code_token`, `activity_detail`  

  - **Triggers**: `get_age_from_dob_trigger`, `user_insert_activity_detail_trigger`

- **Postman Scripts Flow** 
  - **Pre-request**: None

  - **Post-response**: 
    1. Resend Email for User Verification (User has registered but not verified)
       - Parse Response JSON.
       - Checks if a request resulted in a `conflict` error.
       - If so, checks if the error message mentions *Pending* and an email.
       - If both are true, extracts the email address.
       - Sends a new request to resend a verification email to that address.
       - Handle errors appropriately.

<br>

#### Send Verification Mail

- **Access Control** 

   *(NA)*

- **Abstract Pseudocode for `send_verification_email_user`** 

  1. **Initialize Function**:
     - Accept user email, request type, database session, logger, and background tasks as inputs.

  2. **Retrieve User by Email**:
     - Query the database for a user matching the provided email and not in deleted status.
     - If the user is not found, reject the request with a not found error.

  3. **Initialize Email Parameters**:
     - Prepare variables for the email subject, email details, token ID, and return message.

  4. **Handle Email Request Based on Type**:
     - **User Verification (USV)**:
       - If the user is already verified or ineligible for verification, reject the request with a conflict error.
       - Generate a verification token with user-specific claims.
       - Construct a verification link using the token.
       - Set the email subject, email template, and verification link details.
       - Prepare a success message indicating the verification email was sent.
     - **Password Reset (PWR)**:
       - If the user is banned, reject the request with a forbidden error.
       - Generate a reset token with user-specific claims.
       - Construct a password reset link using the token.
       - Set the email subject, email template, and reset link details.
       - Prepare a success message indicating the password reset email will be sent if the user exists.

  5. **Save Token and Send Email**:
     - Create a new entry in the verification token table using the generated token.
     - Commit the database changes.
     - Send the email using background tasks.

  6. **Error Handling**:
     - Rollback the transaction on any error
     - Log the error and return an appropriate error response.

  7. **Return Success Response**:
     - Provide a success message indicating the email process status.

- **API Documentation** 

   [Send Verification Mail Doc](https://venkatpaik17.github.io/VPKonnect/#tag/Users/operation/send_verification_email_user_api_v0_users_send_verify_email_post)

- **Database Tables Affected and Triggers involved** 
  - **Tables**: `user_verification_code_token`  

  - **Triggers**: None

- **Postman Scripts Flow** 

   *(NA)*

<br>

#### Verification of Registered User

- **Access Control** 

   *(NA)*

- **Abstract Pseudocode for `verify_user_`** 

  1. **Initialize Function**:
     - Accept a user verification token, database session, and logger as inputs.

  2. **Decode and Validate Token**:
     - Decode the provided user verification token.
     - Check if the token ID is blacklisted.
     - If the token is invalid or revoked, reject the request with an unauthorized error.

  3. **Retrieve User Details**:
     - Query the database for a user matching the email in the token, inactive and unverified.
     - If the user is not found, reject the request with a not found error.

  4. **Retrieve and Verify Token ID**:
     - Query the database for all user verification tokens of the type `USV` associated with the user.
     - Filter for the token ID provided in the request, ensuring it is not marked as deleted.
     - If the token ID does not exist, reject the request with a not found error.

  5. **Process User Verification**:
     - Mark all related user verification tokens as deleted.
     - Collect the token IDs for blacklisting.
     - Update the user to be active and verified.
     - Add an entry in the guidelines violation score table for the user.
     - Commit the changes to the database and refresh the user object.

  6. **Blacklist Tokens**:
     - Blacklist all collected token IDs to prevent reuse.

  7. **Error Handling**:
     - Rollback the transaction on any error.
     - Log the error and return an appropriate error response.

  8. **Return Success Response**:
     - Provide a success message confirming user verification.
     - Include the verified user’s details in the response.

- **API Documentation** 

   [Verify User Doc](https://venkatpaik17.github.io/VPKonnect/#tag/Users/operation/verify_user__api_v0_users_register_verify_post)

- **Database Tables Affected and Triggers involved** 
  - **Tables**: `user_verification_code_token`, `user`, `guideline_violation_score`, `activity_detail`, `user_account_history`  

  - **Triggers**: `user_update_activity_detail_trigger`, `update_user_account_history_trigger`

- **Postman Scripts Flow** 

   *(NA)*

<br>

#### Password Reset

- **Access Control** 

   *(NA)*

- **Abstract Pseudocode for `reset_password`** 

  1. **Initialize Function**:
     - Accept background tasks, user email, database session, and logger as inputs.

  2. **Validate User**:
     - Parse and validate the provided email.
     - Query the database for a user matching the email and not in deleted status
     - If the user is not found, raise a not found error.
     - If the user's status is banned, reject the request with a forbidden error.

  3. **Generate Reset Token**:
     - Create a password reset token with user claims (email and role).
     - Extract the token and its unique ID.

  4. **Create Reset Link**:
     - Generate a password reset link using the token.

  5. **Prepare Email**:
     - Construct the email subject and body, embedding the reset link and user information.
     - Set the email template.

  6. **Store Reset Token**:
     - Add the reset token ID to the user token table with the type `PWR`.
     - Commit the changes to the database.

  7. **Send Email**:
     - Initiate the email sending process using background tasks.

  8. **Handle Errors**:
     - If any error occurs duting processing:
       - Blacklist the reset token.
       - Rollback the transaction.
       - Log the error and return an appropriate error response.

  9. **Return Success Response**:
     - Provide a response indicating an email will be sent if the account exists for the given email.

- **API Documentation** 

   [Reset Password Doc](https://venkatpaik17.github.io/VPKonnect/#tag/Users/operation/reset_password_api_v0_users_password_reset_post)

- **Database Tables Affected and Triggers involved** 
  - **Tables**: `user_verification_code_token`  

  - **Triggers**: None

- **Postman Scripts Flow** 

   *(NA)*

<br>

#### Password Change - Reset

- **Access Control** 

   *(NA)*

- **Abstract Pseudocode for `change_password_reset`** 

  1. **Initialize Function**:
     - Accept background tasks, password, confirm password, reset token, database session, and logger as inputs.

  2. **Validate Passwords**:
     - Ensure the provided password matches the confirmation password
     - If they do not match, raise a bad request error.

  3. **Decode and Verify Reset Token**:
     - Decode the reset token to extract claims.
     - Check if the token is blacklisted; if yes, raise an unauthorized error.

  4. **Fetch User**:
     - Query the database to fetch the user associated with the email from token claims.
     - Ensure the user is not in banned and deleted status. If invalid, raise an appropriate error.

  5. **Validate Token ID**:
     - Query the database for all the reset tokens of type `PWR` associated with the user. 
     - Filter for the token ID provided in the request, ensuring it is not marked as deleted.
     - If the token ID does not exist, reject the request with a not found error.

  6. **Prepare Notification Email**:
     - Construct an email with email subject, body and template to notify the user of the password reset action.

  7. **Process Password Reset**:
     - Update all related reset tokens as deleted.
     - Hash the new password and update it in the database.
     - Add an entry to the password change history table.
     - Commit the changes to the database

  8. **Blacklist All Tokens**:
     - Blacklist all tokens related to the reset process.

  9. **Send Notification Email**:
     - Dispatch the password reset notification email using background tasks.

  10. **Handle Errors**:
      - Rollback the transaction on any error.
      - Log the error and return an appropriate error response.

  11. **Return Success Response**:
      - Confirm the password change was successful.

- **API Documentation** 

   [Change Password - Reset Doc](https://venkatpaik17.github.io/VPKonnect/#tag/Users/operation/change_password_reset_api_v0_users_password_change_post)

- **Database Tables Affected and Triggers involved** 
  - **Tables**: `user_verification_code_token`, `user`, `password_change_history`  
    
  - **Triggers**: None

- **Postman Scripts Flow** 

   *(NA)*

<br>

#### Password Change - Update

- **Access Control** 

   This endpoint requires the user to have one of the following roles:
   - **user**

- **Abstract Pseudocode for `change_password_update`** 

  1. **Initialize Function**:
     - Accept background tasks, old password, new password, confirm new password, database session, logger, and current user as inputs.

  2. **Prepare Password Update Request Object**:
     - Create an request object to hold the old password, new password, and confirm new password.

  3. **Fetch Current User**:
     - Query the database to fetch the current user using the email from the token claims.
     - Ensure the user's status is not inactive/deactivated/banned/deleted.

  4. **Validate Passwords**:
     - Ensure the new password is not the same as the old password.
     - If they are the same, raise a bad request error.

  5. **Verify Old Password**:
     - Check if the entered old password matches the stored hashed password in the database.
     - If the old password is incorrect, raise an unauthorized error.

  6. **Validate New and Confirm New Passwords**:
     - Ensure the new password matches the confirm new password.
     - If they do not match, raise a bad request error.

  7. **Prepare Notification Email**:
     - Construct an email with subject, body, and template to notify the user about the password update.

  8. **Process Password Update**:
     - Hash the new password and update the password in the user table.
     - Add an entry to the password change history table to track the password update.
     - Commit the changes to the database.

  9. **Send Notification Email**:
     - Dispatch the password change notification email using background tasks.

  10. **Handle Errors**:
      - Rollback the transaction on any error.
      - Log the error and return an appropriate error response.

  11. **Return Success Response**:
      - Confirm the password change was successful.

- **API Documentation** 

   [Change Password - Update Doc](https://venkatpaik17.github.io/VPKonnect/#tag/Users/operation/change_password_update_api_v0_users_password_update_post)

- **Database Tables Affected and Triggers involved** 
  - **Tables**: `user`, `password_change_history`, `user_session`, `user_auth_track`  

  - **Triggers**: `user_auth_track_logout_trigger`

- **Postman Scripts Flow** 
  - **Pre-request**:
    1. Manage Authorization
       - Gets the value of the `JWT` environment variable.
       - If the `JWT` variable is empty or doesn't exist, removes the `Authorization` header from the request.

  - **Post-response**:
    1. Set New Access Token and User Logout
       - Parse Response JSON.
       - Checks if the response code is `200 (OK)`.
       - If so, checks for an `access_token` in the response. If found, saves the token to `JWT` environment variable, indicates to resend request, and stops.
       - If no `access_token` is found, checks for a `user` property in the response.
       - If a `user` property exists, extracts the username.
       - Sends a logout request to a specific endpoint with the username.
       - If the logout is successful `(200 OK)`, removes the `JWT` and `device_info` environment variables.
       - Handle errors appropriately.

<br>

#### Follow/Unfollow User

- **Access Control** 

   This endpoint requires the user to have one of the following roles:
   - **user**

- **Abstract Pseudocode for `follow_user`** 

  1. **Initialize Function**:
     - Accept the followed user data, database session, logger, and current user as inputs.

  2. **Retrieve User to be Followed**:
     - Query the database for the user to be followed using the provided username, not in deleted status.
     - If the user is not found, raise a not found error.
     - If the user’s profile is deactivated, raise a profile not found error.
     - If the user is permanently banned, raise a forbidden error.

  3. **Retrieve Follower User**:
     - Query the database to fetch the follower user using the email from the current user.
     - Ensure the follower’s status is not inactive/deactivated/banned/deleted.

  4. **Check for Restricted Follower**:
     - If the follower user is under full restriction, raise a bad request error indicating they cannot follow/unfollow other users.

  5. **Prevent Self-Following**:
     - If the followed user and follower user are the same, raise a bad request error indicating that a user cannot follow/unfollow themselves.

  6. **Retrieve List of Followers of Followed User**:
     - Get the list of usernames that are following the user to be followed.

  7. **Handle Follow Action**:
     - **If the action is to follow**:
       - Check if the follower is already following the user. If so, raise a conflict error.
       - If the user’s account is private, check if a follow request has already been sent. If so, raise a conflict error.
       - If no follow request exists, create a follow request with a pending status and save it to the database.
       - If the account is not private, directly create a follow association with an accepted status and save it to the database.
     - **If the action is to unfollow**:
       - Check if the follower is already following the user. If not, raise a bad request error.
       - Retrieve the follow association entry and ensure it exists. If not, raise a not found error.
       - Update the follow association status to *unfollow* and save the changes.
     - Commit the changes to the database.

  8. **Handle Errors**:
      - Rollback the transaction on any error.
      - Log the error and return an appropriate error response.

  9. **Return Success Response**:
      - Provide a success message indicating whether the user is now following or has unfollowed the target user.

- **API Documentation** 

   [Follow User Doc](https://venkatpaik17.github.io/VPKonnect/#tag/Users/operation/follow_user_api_v0_users_follow_post)

- **Database Tables Affected and Triggers involved** 
  - **Tables**: `user_follow_association`  

  - **Triggers**: None

- **Postman Scripts Flow** 
  - **Pre-request**: 
    1. Manage Authorization
       - Gets the value of the `JWT` environment variable.
       - If the `JWT` variable is empty or doesn't exist, removes the `Authorization` header from the request.

  - **Post-response**: 
    1. Set New Access Token
       - Parse Response JSON.
       - Checks if the response code is `200 (OK)` and the response contains an access_token.
       - If both are true, saves the access_token to the `JWT` environment variable, and indicates to resend the request.

<br>

#### Accept/Reject Follow Request

- **Access Control** 

   This endpoint requires the user to have one of the following roles:
   - **user**

- **Abstract Pseudocode for `manage_follow_request`** 

  1. **Initialize Function**:
     - Accept the username of the user making the follow request, follow request data, database session, logger, and current user as inputs.

  2. **Retrieve Follower User**:
     - Query the database for the user who is trying to follow using the provided username, not in deleted status.
     - If the follower user is not found, raise a not found error.
     - If the follower user's profile is deactivated, raise a profile not found error.
     - If the follower user is permanently banned, raise a forbidden error.

  3. **Retrieve Current User**:
     - Query the database to fetch the current user using the email from the current user.
     - Ensure the current user's status is not inactive/deactivated/banned/deleted.

  4. **Check for Pending Follow Request**:
     - Query the database to check if there is a pending follow request between the follower user and the current user.
     - If no such request is found, raise a not found error indicating no follow entry exists.

  5. **Handle Follow Request Action**:
     - **If the action is to accept**:
       - Update the follow request status to *accepted* and save the association in the database.
       - Set a success message indicating the current user is now following the follower user.

     - **If the action is to reject**:
       - Update the follow request status to *rejected* and save the changes in the database.
       - Set a success message indicating the follow request was rejected.
     - Commit the changes to the database.

  6. **Handle Errors**:
      - Rollback the transaction on any error.
      - Log the error and return an appropriate error response.

  7. **Return Success Response**:
      - Provide a success message indicating whether the follow request was accepted or rejected.

- **API Documentation** 

   [Manage Follow Request Doc](https://venkatpaik17.github.io/VPKonnect/#tag/Users/operation/manage_follow_request_api_v0_users_follow_requests__username__put)

- **Database Tables Affected and Triggers involved** 
  - **Tables**: `user_follow_association`  

  - **Triggers**: None

- **Postman Scripts Flow** 
  - **Pre-request**: 
    1. Manage Authorization
       - Gets the value of the `JWT` environment variable.
       - If the `JWT` variable is empty or doesn't exist, removes the `Authorization` header from the request.

  - **Post-response**: 
    1. Set New Access Token
       - Parse Response JSON.
       - Checks if the response code is `200 (OK)` and the response contains an access_token.
       - If both are true, saves the access_token to the `JWT` environment variable, and indicates to resend the request.

<br>

#### Followers/Following of a User

- **Access Control** 

   This endpoint requires the user to have one of the following roles:
   - **user**

- **Abstract Pseudocode for `get_user_followers_following`** 

  1. **Initialize Function**:
     - Accept the username, fetch (`followers`, `following`), database session, and current user as inputs.

  2. **Retrieve User by Username**:
     - Query the database for the user matching the provided username, not in deleted status.
     - If the user is not found, raise a not found error.
     - If the user's profile is deactivated, raise a profile not found error.
     - If the user is permanently banned, raise a forbidden error.

  3. **Retrieve Current User**:
     - Query the database to fetch the current user using their email.
     - Ensure the current user's status is not inactive/deactivated/banned/deleted.

  4. **Check User Authorization**:
     - Ensure the current user is authorized to access the requested user's followers or following list:
       - If the current user is not the profile owner and the requested user’s account is private, check if the current user is following the requested user. If not, raise a forbidden error.

  5. **Initialize Lists**:
     - Prepare empty lists for followers and following (i.e., `followers_list`, `following_list`).

  6. **Retrieve List of Following of Current User**:
     - Get the list of usernames that the current user is following.

  7. **Handle `followers` Fetch**:
     - Each follower will be presented with its profile picture, username, and current user follow status.
     - Query the database to get the followers of the requested user.
     - For each follower:
       - If the follower is already being followed by the current user, mark them as followed (`follows_user: True`).
       - If the follower is the current user, mark them as None (`follows_user: None`).
       - Else, mark them as not followed (`follows_user: False`).
     - Return the `followers_list`.

  8. **Handle `following` Fetch**:
     - Each following will be presented with its profile picture, username, and current user follow status.
     - Query the database to get the users that the requested user is following.
     - For each user:
       - If the user is already being followed by the current user, mark them as followed (`follows_user: True`).
       - If the user is the current user, mark them as None (`follows_user: None`).
       - Else, mark them as not followed (`follows_user: False`).
     - Return the `following_list`.

  9. **Handle Invalid Fetch Type**:
     - If the fetch parameter is not `followers` or `following`, raise a bad request error.

  10. **Return Success Response**:
     - Return the appropriate list (`followers_list` or `following_list`) based on the fetch parameter.

- **API Documentation** 

   [Get User Followers Following Doc](https://venkatpaik17.github.io/VPKonnect/#tag/Users/operation/get_user_followers_following_api_v0_users__username__follow_get)

- **Database Tables Affected and Triggers involved** 

   *(NA)*

- **Postman Scripts Flow** 
  - **Pre-request**: 
    1. Manage Authorization
       1. Gets the value of the `JWT` environment variable.
       2. If the `JWT` variable is empty or doesn't exist, removes the `Authorization` header from the request.

  - **Post-response**: 
    1. Set New Access Token
       1. Parse Response JSON.
       2. Checks if the response code is `200 (OK)` and the response contains an access_token.
       3. If both are true, saves the access_token to the `JWT` environment variable, and indicates to resend the request.

<br>

#### Follow Requests of User

- **Access Control** 

   This endpoint requires the user to have one of the following roles:
   - **user**

- **Abstract Pseudocode for `get_follow_requests`** 

  1. **Initialize Function**:  
     - Accept database session and current user as inputs.

  2. **Retrieve Current User**:  
     - Query the database for the current user using their email.  
     - Ensure the current user’s status is is not inactive/deactivated/banned/deleted.

  3. **Retrieve Follow Requests**:  
     - Query the database for all follow requests where:  
       - The followed ID matches the current user’s ID.  
       - The request status is pending.
     - Extract the user ID for each pending follow request.

  4. **Fetch Follower Details**:  
     - Query the user table for users matching the extracted user ID list with the following conditions:  
       - The user’s status is active/inactive/restricted/temp banned.  
       - The user is verified.
       - The user is not deleted.

  5. **Return Success Response**:  
     - Return a list of users who have sent follow requests, with profile picture and username.

- **API Documentation** 

   [Get Follow Requests Doc](https://venkatpaik17.github.io/VPKonnect/#tag/Users/operation/get_follow_requests_api_v0_users_follow_requests_get)

- **Database Tables Affected and Triggers involved** 

   *(NA)*

- **Postman Scripts Flow** 
  - **Pre-request**: 
    1. Manage Authorization
       1. Gets the value of the `JWT` environment variable.
       2. If the `JWT` variable is empty or doesn't exist, removes the `Authorization` header from the request.

  - **Post-response**: 
    1. Set New Access Token
       1. Parse Response JSON.
       2. Checks if the response code is `200 (OK)` and the response contains an access_token.
       3. If both are true, saves the access_token to the `JWT` environment variable, and indicates to resend the request.

<br>

#### Remove Follower

- **Access Control** 

   This endpoint requires the user to have one of the following roles:
   - **user**

- **Abstract Pseudocode for `remove_follower`** 

  1. **Initialize Function**:
     - Accept the follower username, database session, logger, and current user as inputs.

  2. **Retrieve Follower User**:
     - Query the database for the follower user using the provided username, not in deleted status.
     - If the follower user is not found, raise a not found error.
     - If the follower user’s profile is deactivated, raise a profile not found error.
     - If the follower user is permanently banned, raise a forbidden error.

  3. **Retrieve Current User**:
     - Query the database to fetch the current user using their email.
     - Ensure the current user's status is not inactive/deactivated/banned/deleted.

  4. **Retrieve User Follow Association Entry**:
     - Query the database for the follow association between the current user and the follower user, where the status is *accepted*.
     - If no such entry is found, raise a not found error.

  5. **Handle Remove Follower Action**:
     - If the follow entry exists, update the status to *removed*.
     - Commit the changes to the database.

  6. **Handle Errors**:
     - Rollback the transaction on any error.
     - Log the error and return an appropriate error response.

  7. **Return Success Response**:
     - Provide a success message indicating that the follower has been successfully removed.

- **API Documentation** 

   [Remove Follower Doc](https://venkatpaik17.github.io/VPKonnect/#tag/Users/operation/remove_follower_api_v0_users_follow_remove__username__put)

- **Database Tables Affected and Triggers involved** 
  - **Tables**: `user_follow_association`  
  - **Triggers**: None

- **Postman Scripts Flow** 
  - **Pre-request**: 
    1. Manage Authorization
       1. Gets the value of the `JWT` environment variable.
       2. If the `JWT` variable is empty or doesn't exist, removes the `Authorization` header from the request.

  - **Post-response**: 
    1. Set New Access Token
       1. Parse Response JSON.
       2. Checks if the response code is `200 (OK)` and the response contains an access_token.
       3. If both are true, saves the access_token to the `JWT` environment variable, and indicates to resend the request.

<br>

#### Username Change

- **Access Control** 

   This endpoint requires the user to have one of the following roles:
   - **user**

- **Abstract Pseudocode for username_change** 

  1. **Initialize Function**:
     - Accept the new username, database session, logger, and current user as inputs.

  2. **Retrieve Current User**:
     - Query the database to fetch the current user using their email.
     - Ensure the current user's status is not inactive/deactivated/banned/deleted.

  3. **Check for Matching Username**:
     - If the new username is the same as the old username, raise a bad request error indicating the username cannot be the same.

  4. **Check for Username Availability**:
     - Query the database to check if the new username already exists.
     - If it exists, raise a conflict error indicating the username is already taken.

  5. **Process Username Update**:
     - Update the current user's username in the database.
     - Add an entry to the username change history table to track the username update.
     - Commit the changes to the database.

  6. **Handle Errors**:
     - Rollback the transaction on any error.
     - Log the error and return an appropriate error response.

  7. **Return Success Response**:
     - Provide a success message indicating the username change was successful.

- **API Documentation** 

   [Username Change Doc](https://venkatpaik17.github.io/VPKonnect/#tag/Users/operation/username_change_api_v0_users_username_change_post)

- **Database Tables Affected and Triggers involved** 
  - **Tables**: `user`, `username_change_history`  

  - **Triggers**: None

- **Postman Scripts Flow** 
  - **Pre-request**: 
    1. Manage Authorization
       1. Gets the value of the `JWT` environment variable.
       2. If the `JWT` variable is empty or doesn't exist, removes the `Authorization` header from the request.

  - **Post-response**: 
    1. Set New Access Token
       1. Parse Response JSON.
       2. Checks if the response code is `200 (OK)` and the response contains an access_token.
       3. If both are true, saves the access_token to the `JWT` environment variable, and indicates to resend the request.

<br>

#### User profile

- **Access Control** 

   This endpoint requires the user to have one of the following roles:
   - **user**

- **Abstract Pseudocode for user_profile** 

  1. **Initialize Function**:
     - Accept the username, database session, and current user as inputs.

  2. **Retrieve User by Username**:
     - Query the database for the user using the provided username, not in deleted status.
     - If the user is not found, raise a not found error.
     - If the user’s profile is deactivated, raise a profile not found error.
     - If the user is permanently banned, raise a forbidden error.

  3. **Retrieve Current User**:
     - Query the database to fetch the current user using their email.
     - Ensure the current user's status is not inactive/deactivated/banned/deleted.

  4. **Check if Current User Follows the Target User**:
     - Query the database to check if the current user follows the target user.
     - If the current user follows the target user, set `follows_user` to True; otherwise, set it to False.

  5. **Retrieve Profile Information**:
     - Get the number of posts of the user by querying the posts API.
     - Get the number of followers and following of the user.
     - Query the database to find which users follow the current user and also follow the target user.

  6. **Format the User Profile Details**:
     - Create a response with the following information: username, profile picture, number of posts, followers, following, bio, followed by users, and whether the current user follows the target user.

  7. **Return Profile Response**:
     - Provide the user profile details in a structured response.

- **API Documentation** 

   [Get User Profile Doc](https://venkatpaik17.github.io/VPKonnect/#tag/Users/operation/user_profile_api_v0_users__username__profile_get)

- **Database Tables Affected and Triggers involved** 

   *(NA)*

- **Postman Scripts Flow** 
  - **Pre-request**: 
    1. Manage Authorization
       - Gets the value of the `JWT` environment variable.
       - If the `JWT` variable is empty or doesn't exist, removes the `Authorization` header from the request.

  - **Post-response**:
    1. Set New Access Token and Get User Posts
       - Parse Response JSON.
       - Checks if the response code is `200 (OK)`.
       - If so, checks for an `access_token` and saves it to the `JWT` environment variable if found, indicates to resend request, and stops.
       - If no `access_token`, checks for a `username` in the response.
       - If a `username` exists, fetches the user's published posts using the username and the existing `Authorization` header.
       - If the post fetch is successful, calls a function (`myPackage.getPostsResponse`) from a required package (`vpkonnect_scripts`) to process the posts.
       - Handle errors appropriately.

<br>

#### User Posts

- **Access Control** 

   This endpoint requires the user to have one of the following roles:
   - **user**

- **Abstract Pseudocode for get_all_user_posts** 

  1. **Initialize Function**:
     - Accept the username, post status, limit, last post ID, database session, and current user as inputs.

  2. **Transform Post Status**:
     - Attempt to transform the provided status into a valid post status using a utility function.
     - If transformation fails, raise an error.

  3. **Retrieve User by Username**:
     - Query the database for the user using the provided username, not in deleted status.
     - If the user is not found, raise a not found error.
     - If the user’s profile is deactivated, raise a profile not found error.
     - If the user is banned, raise a forbidden error.

  4. **Retrieve Current User**:
     - Query the database to fetch the current user using their email.
     - Ensure the current user's status is not inactive/deactivated/banned/deleted.

  5. **Check if Current User Follows the Target User**:
     - Query the database to check if the current user follows the target user.

  6. **Check if Current User and Target User are same**
     - If current user and target user are different
        - If the target user’s account is private and the current user does not follow them, raise a message indicating the profile is private.
        - If the post is banned or flagged to be banned, or in draft status, raise a forbidden error.

  7. **Retrieve User’s Posts**:
     - Query the database to get the posts for the user based on the status, limit, and last post ID.
     - If no posts are found, return a message indicating there are no posts.

  8. **Format Post Details**:
     - For each post, retrieve the number of likes and comments, ensuring they are counted only for active posts (not drafts).
     - Create a response with the post ID, image, number of likes, and number of comments.

  9. **Return Posts Response**:
     - Provide the formatted list of posts for the target user.

- **API Documentation** 

   [Get All User Posts Doc](https://venkatpaik17.github.io/VPKonnect/#tag/Users/operation/get_all_user_posts_api_v0_users__username__posts_get)

- **Database Tables Affected and Triggers involved** 

   *(NA)*

- **Postman Scripts Flow** 
  - **Pre-request**: 
    1. Manage Authorization
       - Gets the value of the `JWT` environment variable.
       - If the `JWT` variable is empty or doesn't exist, removes the `Authorization` header from the request.

  - **Post-response**:
    1. Get User Posts
       - Parse Response JSON.
       - Calls a function (`myPackage.getPostsResponse`) from a required package (`vpkonnect_scripts`) and passes the JSON response to it.
       - Handle errors appropriately.

<br>

#### User Feed

- **Access Control** 

   This endpoint requires the user to have one of the following roles:
   - **user**

- **Abstract Pseudocode for user_feed** 

  1. **Initialize Function**:
     - Accept database session, last seen post ID, limit, and current user as inputs.

  2. **Retrieve Current User**:
     - Query the database to fetch the current user using their email.
     - Ensure the current user's status is not inactive/deactivated/banned/deleted.

  3. **Retrieve User's Following IDs**:
     - Query the database to get the list of user IDs the current user is following.
     - If the list is empty, raise a message indicating the user needs to follow others to see updates.

  4. **Retrieve Feed Posts**:
     - Query the database to fetch posts from users the current user is following.
     - Limit posts to the specified number and fetch only posts from the last 3 days.
     - Use the post ID of the last seen post to fetch the next batch of posts.

  5. **Handle Empty Feed**:
     - If no posts are retrieved, return a message indicating the user has caught up on posts from the past 3 days.

  6. **Format Feed Post Details**:
     - For each post, retrieve the following details:
       - Post ID, image, caption, and time posted.
       - Number of likes and comments.
       - Whether the current user has liked the post.
       - Information about the post owner.
     - Construct a response object for each post.

  7. **Prepare Feed Response**:
     - Include the formatted list of posts and pagination cursor.

  8. **Return Feed Response**:
     - Provide the user feed response.

- **API Documentation** 

   [User Feed Doc](https://venkatpaik17.github.io/VPKonnect/#tag/Users/operation/user_feed_api_v0_users_feed_get)

- **Database Tables Affected and Triggers involved** 

   *(NA)*

- **Postman Scripts Flow** 
  - **Pre-request**: 
    1. Manage Authorization
       - Gets the value of the `JWT` environment variable.
       - If the `JWT` variable is empty or doesn't exist, removes the `Authorization` header from the request.

  - **Post-response**:
    1. Get User Posts
       - Parse Response JSON.
       - Calls a function (`myPackage.getAllFeedPostsResponse`) from a required package (`vpkonnect_scripts`) and passes the JSON response to it.
       - Handle errors appropriately.

<br>

#### Deactivate/Delete User

- **Access Control** 

   This endpoint requires the user to have one of the following roles:
   - **user**

- **Abstract Pseudocode for `deactivate_or_soft_delete_user`** 

  1. **Initialize Function**:
     - Accept background tasks, password, action (`deactivate` or `delete`), database session, logger, and current user as inputs.

  2. **Prepare Deactivation/Deletion Request Object**:
     - Create an request object with the password and action.

  3. **Retrieve Current User**:
     - Query the database to fetch the current user using their email.
     - Ensure the current user's status is not inactive/deactivated/banned/deleted.

  4. **Check for Password in Request**:
     - If no password is provided, raise a bad request error.

  5. **Verify Password**:
     - Check if the entered password matches the stored hashed password in the database.
     - If the password is incorrect, raise an unauthorized error.

  6. **Process Action**:
     - If action is `deactivate`:
       - Update the current user's status to *deactivate*.
       - Set a success message indicating the account was deactivated.
     - If action is `delete`:
       - Construct an email with subject, body, and template to notify the user about the account deletion.
       - Update the current user's status to *pending delete*.
       - Set a success message indicating the deletion request was accepted.
     - Commit the changes to the database.

  7. **Send Email**:
     - If action is `delete`, send an email about the account deletion.

  8. **Handle Errors**:
     - Rollback the transaction on any error.
     - Log the error and return an appropriate error response.

  9. **Return Success Response**:
     - Provide a success message indicating the result of the action.

- **API Documentation** 

   [Deactivate or Soft Delete User Doc](https://venkatpaik17.github.io/VPKonnect/#tag/Users/operation/deactivate_or_soft_delete_user_api_v0_users_deactivate_patch)

- **Database Tables Affected and Triggers involved** 
  - **Tables**: `user`, `activity_detail`, `user_account_history`, `user_session`, `user_auth_track`, `post`, `comment`, `post_like`, `comment_like`, `user_follow_association`  

  - **Triggers**: `user_update_activity_detail_trigger`, `update_user_account_history_trigger`, `user_auth_track_logout_trigger`, `user_status_update_hide_trigger`, `post_status_update_hide_trigger`, `comment_status_update_hide_trigger`

- **Postman Scripts Flow** 
  - **Pre-request**: 
    1. Manage Authorization
       - Gets the value of the `JWT` environment variable.
       - If the `JWT` variable is empty or doesn't exist, removes the `Authorization` header from the request.

  - **Post-response**:
    1. Set New Access Token and Remove Required Environment Variables and Cookie
       - Parse Response JSON.
       - Checks if the response code is `200 (OK)`.
       - If so, checks for an `access_token` and saves it to the `JWT` environment variable if found, indicates to resend request, and stops.
       - If no `access_token`, then removes the `JWT` and `device_info` environment variables.
       - Clears all cookies associated with the current request URL.
       - Handle errors appropriately.

<br>

#### Report item

- **Access Control** 

   This endpoint requires the user to have one of the following roles:
   - **user**

- **Abstract Pseudocode for `report_item`** 

  1. **Initialize Function**:
     - Accept reported item details, database session, logger, and current user as inputs.

  2. **Validate Reported Item**:
     - If the reported item type is `post`:
       - Query the database to fetch the post using ID, not in draft/hidden/removed/flagged deleted status.
       - If the post does not exist, raise a not found error.
       - If the post status is banned, raise a already banned error.
       - If the post status is flagged for ban, raise a already flagged to be banned error.
     - If the reported item type is `comment`:
       - Query the database to fetch the comment using ID, not in hidden/removed/flagged deleted status.
       - If the comment does not exist, raise a not found error.
       - If the comment status is banned, raise a already banned error.
       - If the comment status is flagged for ban, raise a already flagged to be banned error.

  3. **Fetch Reporter User**:
     - Retrieve the reporter user using their email.
     - Ensure the reporter user’s status is not inactive/deactivated/banned/deleted.

  4. **Fetch Reported User**:
     - Query the database to fetch the reported user using their username, not in deleted status
     - If the reported user is not found, raise a not found error.
     - If the reported user’s profile is deactivated, raise a profile not found error.
     - If the reported user is permanently banned, raise a forbidden error.

  5. **Handle Impersonation Reports**:
     - If the reported item type is `account and a username is provided for impersonation:
       - Query the database to fetch the user corresponding to the username, not in deleted status.
       - If the user is not found, raise a not found error.
       - If the user’s profile is deactivated, raise a profile not found error.
       - If the user is permanently banned, raise a forbidden error.

  6. **Validate Reporter and Reported User**:
     - Ensure the reporter user is not reporting their own content.
     - If the reporter is reporting their own content, raise a report own content error.

  7. **Check for Existing Report**:
     - Query the database to check if a report exists for the same user, same item, and same reason.
     - If an existing report is found, return a response indicating the item has already been reported.

  8. **Add Report to Database**:
     - Create a new report entry.
     - Add the report to the database and commit the changes.

  9. **Handle Errors**:
     - Rollback the transaction on any error.
     - Log the error and return an appropriate error response.

  10. **Return Success Response**:
      - Provide a success message indicating the item has been reported anonymously and will be handled by the content moderator.

- **API Documentation** 

   [Report Item Doc](https://venkatpaik17.github.io/VPKonnect/#tag/Users/operation/report_item_api_v0_users_report_post)

- **Database Tables Affected and Triggers involved** 
  - **Tables**: `user_content_report_detail`, `user_content_report_event_timeline`  

  - **Triggers**: `user_content_report_submit_event_trigger`

- **Postman Scripts Flow** 
  - **Pre-request**: 
    1. Manage Authorization
       - Gets the value of the `JWT` environment variable.
       - If the `JWT` variable is empty or doesn't exist, removes the `Authorization` header from the request.

  - **Post-response**: 
    1. Set New Access Token
       - Parse Response JSON.
       - Checks if the response code is `200 (OK)` and the response contains an access_token.
       - If both are true, saves the access_token to the `JWT` environment variable, and indicates to resend the request.

<br>

#### Appeal Content

- **Access Control** 

   *(NA)*

- **Abstract Pseudocode for `appeal_content`** 

  1. **Initialize Function**:
     - Accept appeal request details, attachment file, database session, and logger as inputs.

  2. **Validate Content Type**:
     - If the content type is `account`:
       - Query the database to fetch the user using username and email, not in active/delete/pending delete inactive status.
       - If the user is not found, raise a not found error.
       - If the user's status indicates the appeal period is over, raise a gone error.
       - Query the database to fetch the active restriction or ban entry for the user.
         - If no active restriction/ban entry is found, raise a not found error.
       - Update the user's status to match the ban status if appeal user's status is deactivated/inactive.
       - Check for any previously rejected appeals for the same account and report.
         - If found, raise a forbidden error.

     - If the content type is `post` or `comment`:
       - Query the database to fetch the user using username and email, in active/restricted status.
         - If the user is not found, raise a not found error.
       - Validate the appeal submission limit:
         - If the content appeal submission period has expired, raise a gone error.
       - Verify the content is banned:
         - If not banned, raise a not found error.
       - Check for any previously rejected appeals for the same content and report.
         - If found, raise a forbidden error.
       - Retrieve the report entry associated with the content:
         - If no report entry is found, check the report flagged content and resolve its report.
           - If unresolved, raise a not found error.
     - If the content type is invalid, raise a bad request error.

  3. **Create an Appeal**:
     - Get the report ID from the restriction/ban or report.
     - Create a new appeal entry.

  4. **Process Attachment**:
     - If an attachment is provided:
       - Validate and generate a unique name for the image.
       - Save the image to the appropriate appeal subfolder.
       - Update the appeal's attachment field with the image name.

  5. **Add Appeal to Database**:
     - Add the appeal to the database and commit the changes.

  6. **Error Handling**:
      - Rollback the transaction on any error.
      - If an image was uploaded, remove the image from the storage.
      - Log the error and return an appropriate error response.

  7. **Return Success Response**:
     - Provide a message indicating the appeal for the account, post, or comment was successfully submitted and will be reviewed by the content moderator.

- **API Documentation** 

   [Appeal Content Doc](https://venkatpaik17.github.io/VPKonnect/#tag/Users/operation/appeal_content_api_v0_users_appeal_post)

- **Database Tables Affected and Triggers involved** 
  - **Tables**: `user`, `user_content_restrict_ban_appeal_detail`, `activity_detail`, `user_account_history`, `user_content_restrict_ban_appeal_event_timeline`, `post`, `comment`, `post_like`, `comment_like`, `user_follow_association`  

  - **Triggers**: `user_content_restrict_ban_appeal_submit_event_trigger`, `user_status_update_unhide_trigger`, `user_update_activity_detail_trigger`, `update_user_account_history_trigger`, `post_status_update_unhide_trigger`, `comment_status_update_unhide_trigger`

- **Postman Scripts Flow** 

   *(NA)*

<br>

#### Send Ban Mail

- **Access Control** 

   *(NA)*

- **Abstract Pseudocode for `send_ban_mail`** 

  1. **Initialize Function**:
     - Accept email parameters containing user ban details and background tasks as inputs.

  2. **Prepare Ban Notification Email **:
     - Construct an email with subject, body, and template to notify the user about the ban.

  3. **Send Email**:
     - Dispatch the ban notification email using background tasks.

  4. **Handle Errors**:
     - If any error occurs, propagate it further.

- **API Documentation** 

   [Send Ban Mail Doc](https://venkatpaik17.github.io/VPKonnect/#tag/Users/operation/send_ban_mail_api_v0_users_send_ban_mail_post)

- **Database Tables Affected and Triggers involved** 

   *(NA)*

- **Postman Scripts Flow** 

   *(NA)*

<br>

#### Send Delete Mail

- **Access Control** 

   *(NA)*

- **Abstract Pseudocode for `send_delete_mail`** 

  1. **Initialize Function**:
     - Accept email parameters containing user delete details and background tasks as inputs.

  2. **Prepare Delete Notification Email **:
     - Construct an email with subject, body, and template to notify the user about the deletion.

  3. **Send Email**:
     - Dispatch the delete notification email using background tasks.

  4. **Handle Errors**:
     - If any error occurs, propagate it further.

- **API Documentation** 

   [Send Delete Mail Doc](https://venkatpaik17.github.io/VPKonnect/#tag/Users/operation/send_delete_mail_api_v0_users_send_delete_mail_post)

- **Database Tables Affected and Triggers involved** 

   *(NA)*

- **Postman Scripts Flow** 

   *(NA)*

<br>

#### User Violation Status

- **Access Control** 

   This endpoint requires the user to have one of the following roles:
   - **user**

- **Abstract Pseudocode for `get_user_violation_status_details`** 

  1. **Initialize Function**:
     - Accept database session and current user as inputs.

  2. **Retrieve Current User**:
     - Query the database to fetch the current user using their email.
     - Ensure the current user's status is not inactive/deactivated/banned/deleted.

  3. **Fetch Violation Details**:
     - Query the database to retrieve the user's violation details.

  4. **Fetch Active Restriction/Ban**:
     - Query the database to check if the user has any active restriction or ban.

  5. **Fetch Guideline Violation Score**:
     - Query the database to retrieve the user's final guideline violation score.

  6. **Format User Violation Details**:
     - Construct a response object containing:
       - Number of post, comment, and account violations without restriction/ban.
       - Total number of violations without restriction/ban.
       - Number of partial/full account restrictions.
       - Number of temporary/permanent bans.
       - Total number of account restrictions and bans.
       - Active restriction/ban details.
       - User's final guideline violation score.

  7. **Return Response**:
     - Provide the user violation details in a structured response.

- **API Documentation** 

   [Get User Violation Status Details Doc](https://venkatpaik17.github.io/VPKonnect/#tag/Users/operation/get_user_violation_status_details_api_v0_users_violation_get)

- **Database Tables Affected and Triggers involved** 

   *(NA)*

- **Postman Scripts Flow** 
  - **Pre-request**: 
    1. Manage Authorization
       - Gets the value of the `JWT` environment variable.
       - If the `JWT` variable is empty or doesn't exist, removes the `Authorization` header from the request.

  - **Post-response**: 
    1. Set New Access Token
       - Parse Response JSON.
       - Checks if the response code is `200 (OK)` and the response contains an access_token.
       - If both are true, saves the access_token to the `JWT` environment variable, and indicates to resend the request.

<br>

#### About User

- **Access Control** 

   This endpoint requires the user to have one of the following roles:
   - **user**

- **Abstract Pseudocode for `about_user`** 

  1. **Initialize Function**:
     - Accept username, database session, and current user as inputs.

  2. **Retrieve Current User**:
     - Query the database to fetch the current user using their email.
     - Ensure the current user's status is not inactive/deactivated/banned/deleted.

  3. **Retrieve User**:
     - Query the database for the user using username, not in deleted status.
     - If the user is not found, raise a not found error.
     - If the user's profile is deactivated, raise a profile not found error.
     - If the user is permanently banned, raise a forbidden error.

  4. **Format About User Details**:
     - Construct a about user object containing:
        - If the current user is viewing their own profile:
           - profile picture, username, account creation date, account country, former usernames, and the count of former usernames.
        - If the current user is viewing another user's profile:
           - profile picture, username, account creation date, and account country.

  5. **Return Response**:
     - Provide the user's profile details in a structured response.

- **API Documentation** 

   [About User Doc](https://venkatpaik17.github.io/VPKonnect/#tag/Users/operation/about_user_api_v0_users__username__about_get)

- **Database Tables Affected and Triggers involved** 

   *(NA)*

- **Postman Scripts Flow** 
  - **Pre-request**: 
    1. Manage Authorization
       - Gets the value of the `JWT` environment variable.
       - If the `JWT` variable is empty or doesn't exist, removes the `Authorization` header from the request.

  - **Post-response**: 
    1. Set New Access Token
       - Parse Response JSON.
       - Checks if the response code is `200 (OK)` and the response contains an access_token.
       - If both are true, saves the access_token to the `JWT` environment variable, and indicates to resend the request.

<br>

### Scheduled Jobs

#### Delete User After Deactivation Period Expiration

- **Abstract Pseudocode for `delete_user_after_deactivation_period_expiration`** 

  1. **Initialize Function**:
     - Get database session and logger.

  2. **Fetch Scheduled Delete Entries**:
     - Query the database to fetch entries where deactivation period for scheduled deletion has expired.

  3. **Process Scheduled Delete Entries**:
     - If scheduled delete entries exist:
       - Extract user IDs from the scheduled delete entries.
       - Query the database to fetch users with extracted user IDs, in pending delete/pending delete ban/pending delete inactive status.
         - If users to be deleted are found:
           - For each user:
             - Update the user status to *deleted*.
             - Mark the user as deleted.
             - Commit the changes to the database.

  4. **Handle Errors**:
     - Rollback the transaction on any database error.
     - Log the error.

  5. **Finalize**:
     - Close the database session.

  6. **Log Completion**:
     - Log job completion message.
     - Print completion message.

- **Database Tables Affected and Triggers involved** 
  - **Tables**: `user`, `activity_detail`, `user_account_history`, `user_restrict_ban_detail`, `guideline_violation_last_added_score`, `account_report_flagged_content`, `user_content_restrict_ban_appeal_detail`, `user_content_restrict_ban_appeal_event_timeline`, `user_content_report_detail`, `user_content_report_event_timeline`, `comment`, `post`, `post_like`, `comment_like`, `guideline_violation_score`, `password_change_history`, `user_auth_track`, `user_follow_association`, `user_session`, `username_change_history`  

  - **Triggers**: `user_update_activity_detail_trigger`, `update_user_account_history_trigger`, `user_status_update_delete_one_trigger`, `user_status_update_delete_two_trigger`, `user_content_restrict_ban_appeal_close_event_trigger`, `user_content_report_close_event_trigger`, `post_is_deleted_update_trigger`, `comment_is_deleted_update_trigger`
   
<br>

#### Remove Restriction After Duration Expiration

- **Abstract Pseudocode for `remove_restriction_on_user_after_duration_expiration`** 

  1. **Initialize Function**:
     - Get database session and logger.

  2. **Fetch Expired Restriction Entries**:
     - Query the database to fetch entries where restriction duration has expired.

  3. **Process Expired Restriction Entries**:
     - If expired restriction entries exist:
       - Mark all expired restrictions as not active.
       - Extract report IDs from the expired restriction entries.
       - Fetch pending appeals related to the expired restrictions (account type).
       - If pending appeals exist:
         - For each appeal:
           - Update the appeal status to *closed* with appropriate moderator note.
         - Extract user IDs, report IDs and restriction enforcement times from the expired restriction entries.
         - For each user ID, report ID, and enforcement time:
           - Query the database to fetch the user, in restricted status.
           - If the user is found:
             - Query the database to find the next consecutive restriction for the user (excluding the current expired one).
             - If a consecutive restriction is found:
               - Mark the consecutive restriction as active.
               - Perform consecutive violation specific operations.
               - Update reported user status appropriately if needed based on user's current status and consecutive ban.
             - Else, update the user status to *active* if user is not deactivated/inactive.
           - Else, raise an exception indicating the user associated with the restriction was not found.
       - Commit the changes to the database.

  4. **Send Email Notification (If Applicable)**:
     - If restricted user is found and consecutive violation action is a ban (temporary or permanent):
     - Construct a request body for the ban mail API.
     - Make a POST request to the ban mail API.
     - Log success or handle potential errors/exceptions.
              
  5. **Handle Errors**:
     - Rollback the transaction on any error.
     - Log the error.

  6. **Finalize**:
     - Close the database session.

  7. **Log Completion**:
     - Log job completion message.
     - Print completion message.

- **Database Tables Affected and Triggers involved** 
  - **Tables**: `user_restrict_ban_detail`, `user_content_restrict_ban_appeal_detail`, `user_content_restrict_ban_appeal_event_timeline`, `user`, `activity_detail`, `user_account_history`, `user_session`, `user_auth_track`, `user_content_report_detail`, `user_content_report_event_timeline`, `post`, `comment`, `post_like`, `comment_like`, `user_follow_association`, `guideline_violation_score`, `guideline_violation_last_added_score`  

  - **Triggers**: `user_content_restrict_ban_appeal_close_event_trigger`, `user_update_activity_detail_trigger`, `update_user_account_history_trigger`, `user_restrict_ban_account_resolve_update_event_trigger`, `user_auth_track_logout_trigger`, `user_content_report_resolve_event_trigger`, `user_status_update_hide_trigger`, `post_status_update_ban_trigger`, `comment_status_update_ban_trigger`, `post_status_update_hide_trigger`, `comment_status_update_hide_trigger`

<br>

#### Remove Ban After Duration Expiration

- **Abstract Pseudocode for `remove_ban_on_user_after_duration_expiration`** 

  1. **Initialize Function**:
     - Get database session and logger.

  2. **Fetch Expired Ban Entries**:
     - Query the database to fetch entries where ban duration has expired.

  3. **Process Expired Ban Entries**:
     - If expired ban entries exist:
       - Mark all expired bans as not active.
       - Extract report IDs from the expired ban entries.
       - Fetch pending appeals related to the expired bans (account type).
       - If pending appeals exist:
         - For each appeal:
         - Update the appeal status to *closed* with appropriate moderator note.
       - Extract user IDs, report IDs and ban enforcement times from the expired ban entries.
       - For each user ID, report ID, and enforcement time:
         - Query the database to fetch the user, in banned status.
         - If the user is found:
           - Query the database to find the next consecutive ban for the user (excluding the current expired one).
           - If a consecutive ban is found:
             - Mark the consecutive ban as *active*.
             - Perform consecutive violation specific operations.
             - Update reported user status appropriately if needed based on user's current status and consecutive ban.
           - Else, update the user status to *active* if user is not deactivated/inactive.
         - Else, raise an exception indicating the user associated with the ban was not found.
       - Commit the changes to the database.

  4. **Send Email Notification (If Applicable)**:
     - If banned user is found and consecutive violation action is a ban (temporary or permanent):
       - Construct a request body for the ban mail API.
       - Make a POST request to the ban mail API.
       - Log success or handle potential errors/exceptions.

  5. **Handle Errors**:
     - Rollback the transaction on any error.
     - Log the error.

  6. **Finalize**:
     - Close the database session.

  7. **Log Completion**:
     - Log job completion message.
     - Print completion message.

- **Database Tables Affected and Triggers involved** 
  - **Tables**: `user_restrict_ban_detail`, `user_content_restrict_ban_appeal_detail`, `user_content_restrict_ban_appeal_event_timeline`, `user`, `activity_detail`, `user_account_history`, `user_session`, `user_auth_track`, `user_content_report_detail`, `user_content_report_event_timeline`, `post`, `comment`, `post_like`, `comment_like`, `user_follow_association`, `guideline_violation_score`, `guideline_violation_last_added_score`  

  - **Triggers**: `user_content_restrict_ban_appeal_close_event_trigger`, `user_update_activity_detail_trigger`, `update_user_account_history_trigger`, `user_restrict_ban_account_resolve_update_event_trigger`, `user_auth_track_logout_trigger`, `user_content_report_resolve_event_trigger`, `user_status_update_hide_trigger`, `post_status_update_ban_trigger`, `comment_status_update_ban_trigger`, `post_status_update_hide_trigger`, `comment_status_update_hide_trigger`

<br>

#### User Inactivity - Delete

- **Abstract Pseudocode for `user_inactivity_delete`** 

  1. **Initialize Function**:
     - Get database session and logger.

  2. **Fetch Inactive User Auth Entries**:
     - Query the database to fetch recent user auth track entries indicating inactivity (6/12 months old).

  3. **Process Inactive User Auth Entries**:
     - If inactive auth entries exist:
       - Query the database to find any active restrictions/bans for the inactive users.
         - If active restrictions/bans exist:
           - Mark all active restrictions/bans as not active.
           - Extract user IDs from the inactive auth entries.
           - Extract user emails from the inactive auth entries.
           - Query the database to fetch open/under review reports associated with the inactive users.
           - For each open/under review report:
             - Update report status to *closed* with appropriate moderator note.
           - For each inactive user:
             - Update user status to *pending delete inactive*.
     - Commit the changes to the database.

  4. **Send Email Notification (If Applicable)**:
     - If inactive user emails exist and the email flag is set:
       - Construct a request body for the delete mail API.
       - Make a POST request to the delete mail API.
       - Log success or handle potential errors/exceptions.

  5. **Handle Errors**:
      - Rollback the transaction on any error.
      - Log the error.

  6. **Finalize**:
      - Close the database session.

  7. **Log Completion**:
      - Log job completion message.
      - Print completion message.

- **Database Tables Affected and Triggers involved** 
  - **Tables**: `user`, `user_restrict_ban_detail`, `user_content_report_detail`, `user_content_report_event_timeline`, `user_account_history`, `activity_detail`, `post`, `comment`, `post_like`, `comment_like`, `user_follow_association`  

  - **Triggers**: `user_content_report_close_event_trigger`, `update_user_account_history_trigger`, `user_update_activity_detail_trigger`, `user_status_update_hide_trigger`, `post_status_update_hide_trigger`, `comment_status_update_hide_trigger`

<br>

#### User Inactivity - Inactive

- **Abstract Pseudocode for `user_inactivity_inactive`** 

  1. **Initialize Function**:
     - Get database session and logger.

  2. **Fetch Inactive User Auth Entries**:
     - Query the database to fetch recent user auth track entries indicating inactivity (3 months old).

  3. **Process Inactive User Auth Entries**:
     - If inactive auth entries exist:
       - Extract user IDs from the inactive auth entries.
       - Query the database to fetch users with extracted user IDs, in active/restricted/temp ban status.
         - If users to be inactivated are found:
           - For each user:
             - Update user status to *inactive*.
             - Commit the changes to the database.

  4. **Handle Errors**:
     - Rollback the transaction on any error.
     - Log the error.

  5. **Finalize**:
     - Close the database session.

  6. **Log Completion**:
     - Log job completion message.
     - Print completion message.

- **Database Tables Affected and Triggers involved** 
  - **Tables**: `user`, `activity_detail`, `user_account_history`, `user_session`, `user_auth_track`  

  - **Triggers**: `user_update_activity_detail_trigger`, `update_user_account_history_trigger`, `user_auth_track_logout_trigger`

<br>

#### Delete User After Permanent Ban Appeal Limit Duration Expiration

- **Abstract Pseudocode for `delete_user_after_permanent_ban_appeal_limit_expiry`** 

  1. **Initialize Function**:
     - Get database session and logger.

  2. **Fetch Permanently Banned Users with No Pending or Rejected Appeals**:
     - Query the database to find permanently banned users with no pending or rejected appeals older than the appeal limit.

  3. **Process Permanently Banned Users**:
     - If such users with no pending or rejected appeals are found:
       - Extract user IDs from the results.
       - Extract ban entry IDs from the results.
       - Query the database to fetch the corresponding ban entries using the extracted ban IDs.
       - Query the database to fetch the users with the extracted user IDs with permanently banned status.
       - For each ban entry:
         - Mark the ban entry as *not active*.
       - Extract user emails from the fetched users.
       - For each user:
         - Update user status to *pending delete ban*.
     - Commit the changes to the database.

  4. **Send Email Notification (If Applicable)**:
     - If user emails exist and the email flag is set:
       - Construct a request body for the delete mail API.
       - Make a POST request to the delete mail API.
       - Log success or handle potential errors/exceptions.

  5. **Handle Errors**:
     - Rollback the transaction on any error.
     - Log the error.

  6. **Finalize**:
     - Close the database session.

  7. **Log Completion**:
     - Log job completion message.
     - Print completion message.

- **Database Tables Affected and Triggers involved** 
  - **Tables**: `user`, `user_restrict_ban_detail`, `activity_detail`, `user_account_history`, `post`, `comment`, `user_content_report_detail`, `user_content_report_event_timeline`  

  - **Triggers**: `user_status_update_pdb_trigger`, `user_update_activity_detail_trigger`, `update_user_account_history_trigger`, `user_content_report_close_event_trigger`

<br>

#### Content Delete After Ban Appeal Limit Duration Expiration

- **Abstract Pseudocode for `delete_content_after_ban_appeal_limit_expiry`** 

  1. **Initialize Function**:
     - Get database session and logger.

  2. **Fetch Banned Posts with No Pending or Rejected Appeals**:
     - Query the database to find banned posts with no pending or rejected appeals older than the appeal limit.

  3. **Fetch Banned Comments with No Pending Appeals**:
     - Query the database to find banned comments with no pending or rejected appeals older than the appeal limit.

  4. **Process Banned Content**:
     - If banned posts with no pending or rejected appeals are found:
       - Extract post IDs from the banned posts.
       - Query the database to fetch the corresponding posts using the extracted post IDs with banned status.
       - Mark the ban on these posts as final.
     - If banned comments with no pending or rejected appeals are found:
       - Extract comment IDs from the results.
       - Query the database to fetch the corresponding comments using the extracted comment IDs with banned status.
       - Mark the ban on these comments as final.
     - Commit the changes to the database.

  5. **Handle Errors**:
     - Rollback the transaction on any database error.
     - Log the error.

  6. **Finalize**:
     - Close the database session.

  7. **Log Completion**:
     - Log job completion message.
     - Print completion message.

- **Database Tables Affected and Triggers involved** 
  - **Tables**: `post`, `comment`

  - **Triggers**: None

<br>

#### Close Appeal After Process Duration Expiration

- **Abstract Pseudocode for `close_appeal_after_duration_limit_expiration`** 

  1. **Initialize Function**:
     - Get database session and logger.

  2. **Process Pending Appeals**:
     - Query the database to find permanently banned users' pending appeals older than the process limit.
     - If such appeals exist:
       - Extract ban IDs, user IDs, and appeal IDs from the appeals.
       - Query the database to fetch the corresponding ban entries.
       - Query the database to fetch the users with the extracted user IDs with permanently banned status.
       - Query the database to fetch the appeals using the extracted appeal IDs.
       - For each appeal:
         - Update appeal status to *closed* with appropriate moderator note.
       - For each ban entry:
         - Mark the ban entry as *not active*.
       - For each user:
         - Update user status to *pending delete ban*.
     - Query the database to find posts/comment pending appeals older than the process limit.
     - If such appeals exist:
       - For each appeal:
         - Update appeal status to *closed* with appropriate moderator note.
         - Extract post and comment IDs from the appeals.
         - Query the database to fetch the corresponding posts using the extracted post IDs with banned status.
         - Query the database to fetch the corresponding comments using the extracted comment IDs with banned status.
         - Mark the ban on these posts as *final*.
         - Mark the ban on these comments as *final*.
     - Commit the changes to the database.

  3. **Handle Errors**:
     - Rollback the transaction on any database error.
     - Log the error.

  4. **Finalize**:
     - Close the database session.

  5. **Log Completion**:
     - Log job completion message.
     - Print completion message.

- **Database Tables Affected and Triggers involved** 
  - **Tables**: `user`, `user_restrict_ban_detail`, `user_content_restrict_ban_appeal_detail`, `user_content_restrict_ban_appeal_event_timeline`, `activity_detail`, `user_account_history`, `post`, `comment`, `user_content_report_detail`, `user_content_report_event_timeline`  

  - **Triggers**: `user_status_update_pdb_trigger`, `user_update_activity_detail_trigger`, `update_user_account_history_trigger`, `user_content_report_close_event_trigger`, `user_content_restrict_ban_appeal_close_event_trigger`

<br>

#### Violation Scores Reduction - Quarterly

- **Abstract Pseudocode for `reduce_violation_score_quarterly`** 

  1. **Initialize Function**:
     - Get database session and logger.

  2. **Fetch Users Eligible for Score Reduction**:
     - Query the database to find user IDs from latest resolved reports older than 3 months, with no accepted or active appeals.

  3. **Fetch Guideline Violation Score Entries**:
     - Query the database to fetch guideline violation score entries for those users.
     - Filter the entries to include only those where the last update was older than 3 months.

  4. **Reduce Violation Scores**:
     - If eligible guideline violation score entries are found:
       - Set the reduction rate to 50%.
       - For each entry:
         - Reduce post score, comment score, message score and final violation score by 50%.
     - Commit the changes to the database.

  5. **Handle Errors**:
     - Rollback the transaction on any database error.
     - Log the error.

  6. **Finalize**:
     - Close the database session.

  7. **Log Completion**:
     - Log job completion message.
     - Print completion message.

- **Database Tables Affected and Triggers involved** 
  - **Tables**: `guideline_violation_score`

  - **Triggers**: None

<br>

### Operations

#### Appeal Accept

- **Abstract Pseudocode for `operations_after_appeal_accept`** 

  1. **Initialize Function**:
     - Accept user ID, report ID, appeal content ID, appeal content type, restriction/ban content ID, restriction/ban content type, restriction/ban status, restriction/ban active flag, and database session as inputs.

  2. **Handle Appeal Based on Content Type**:
     - If appeal content type is `account`:
       - If restriction/ban content type is `account`:
         - Query the database to fetch all valid flagged content for the account report.
         - Get the count of flagged posts.
         - Query the database to fetch all the flagged posts with banned status.
         - Get count of banned posts.
         - For each banned post:
           - Update banned post status to *published*.
         - Perform operations to handle updates to guideline violation score and last added score.
         - Perform operations to handle updates to user and its restriction/ban.
       - If restriction/ban content type is `post` or `comment`:
         - Perform operations to handle updates to post/comment.
         - Perform operations to handle updates of guideline violation score and last added score.
         - Perform operations to handle updates to user and its restriction/ban.
     - If appeal content type is `post` or `comment`:
       - If appeal content type is `post` and restriction/ban content type is `account`:
         - Query the database to fetch all valid flagged content for the account report.
         - Get count of flagged posts.
         - Query the database to fetch all the flagged posts with published status (unbanned posts)
         - Get count of already unbanned posts.
         - Perform operations to handle updates to posts
         - Perform operations to handle updates of guideline violation score and last added score.
         - If restriction/ban is active:
           - If all flagged posts are *published*:
             - Perform operations to handle updates to user and its restriction/ban.
         - Else, no additional operations needed.
       - If restriction/ban content type is `post` or `comment`:
         - Perform operations to handle updates to post/comment.
           - If restriction/ban is active:
             - Perform operations to handle updates of guideline violation score and last added score.
             - Perform operations to handle updates to user and its restriction/ban.
           - Else, perform operations to handle updates of guideline violation score and last added score.
     - If no restriction/ban content type (no restriction/ban associated):
       - Perform operations to handle updates to post/comment.
       - Perform operations to handle updates of guideline violation score and last added score.

  3. **Return Response**:
     - Return the consecutive violation and flag to notify the notification email status.

<br>

#### Appeal Reject

- **Abstract Pseudocode for `operations_after_appeal_reject`** 

  1. **Initialize Function**:
     - Accept user ID, report ID, appeal content ID, appeal content type, restriction/ban content ID, restriction/ban content type, restriction/ban status, restriction/ban enforce action at, and database session as inputs.

  2. **Handle Account Appeal Rejection**:
     - If appeal content type is `account`:
       - If restriction/ban content type is `account`:
         - Query the database to fetch all valid flagged content for the account report.
         - If no valid flagged content are found, raise a not found error.
         - Query the database to fetch all the flagged posts with banned status.
         - If no posts are found, raise a not found error.
         - For each post:
           - Mark the ban on the post as final.
         - If restriction/ban status is *permanently banned*:
           - If the appeal limit expiration time has passed:
             - Query the database to fetch the ban entry.
             - If no ban entry is found, raise a not found error.
             - Query the database to fetch the permanently banned user.
             - Update the user status to *pending delete ban*.
             - Mark the ban entry as not active.
       - If restriction/ban content type is `post` or `comment`:
         - If restriction/ban content type is `post`:
           - Query the database to fetch the post with banned status.
           - If no post is found, raise a not found error.
             - Mark the ban on the post as final.
         - If restriction/ban content type is `comment`:
           - Query the database to fetch the comment with banned status.
           - If no comment is found, raise a not found error.
             - Mark the ban on the comment as final.

  3. **Handle Post/Comment Appeal Rejection**:
     - If appeal content type is `post` or `comment`:
       - If restriction/ban content type is `account`:
         - Check if the content ID is present in the valid flagged content, if not, raise a not found error.
         - Query the database to fetch the post with banned status.
           - If no post is found, raise a not found error.
             - Mark the ban on the post as final.
       - If restriction/ban content type is `post` or `comment`:
         - If restriction/ban content type is `post`:
           - Query the database to fetch the post with banned status.
           - If no post is found, raise a not found error.
             - Mark the ban on the post as final.
         - If restriction/ban content type is `comment`:
           - Query the database to fetch the comment with banned status.
           - If no comment is found, raise a not found error.
             - Mark the ban on the comment as final.   

<br>

#### Consecutive Violation

- **Abstract Pseudocode for `consecutive_violation_operations`** 

  1. **Initialize Function**:
     - Accept consecutive violation and database session as inputs.

  2. **Fetch Consecutive Violation Report**:
     - Query the database to fetch the report using the report ID with future resolved status.
     - If no such report is found, raise a not found error.

  3. **Update Report Status**:
     - Update the consecutive violation report status to *resolved*.

  4. **Handle Related Reports**:
     - Query the database to fetch any future resolved related reports related to the consecutive violation report (same reported item ID, user ID, and type) using moderator ID.
       - If other related reports with the same reason exist:
         - Update the status of these reports to *resolved*.

  5. **Handle Guideline Violation Score**:
     - Query the database to fetch the guideline violation score using the reported user ID.
     - If no such score is found, raise a not found error.
     - Query the database to fetch the last added score associated with the report using the score ID, report ID.
     - If no such score is found, raise a not found error.

  6. **Determine Content Violation Score Type and Current Content Violation Score**:
     - Determine the specific content violation score type (post, comment, or message).
     - Get the current content violation score.
     - If the reported item type is `account`, use *post score* as a default.

  7. **Update Scores**:
     - Calculate the new content score by adding the last added score to the current content score.
     - Calculate the new final violation score by adding the last added score to the current final violation score.
     - Update the guideline violation score entry with the new scores.
     - Mark the last added score as *added*.

  8. **Handle Content Status Update**:
     - If the reported item type is `account`:
       - Query the database to fetch the valid flagged content related to the account report.
       - If no valid flagged content is found, raise a not found error.
         - Get the valid flagged content IDs.
         - For each content ID:
           - Query the database to fetch the post using the content ID, not in published/draft/hidden/removed status.
           - If no post is found, raise a not found error.
           - If the post status is banned, raise a conflict error, indicating the flagged post is already banned.
           - If the post status is flagged deleted, print a message, indicating the flagged post is already deleted.
           - If the post status is flagged to be banned, update the post status to *banned*.
     - Else:
       - If the reported item type is `post`:
         - Query the database to fetch the post using the reported item ID, not in published/draft/hidden/removed status.
           - If no post is found, raise a not found error.
           - If the post status is banned, raise a conflict error, indicating the post is already banned.
           - If the post status is flagged deleted, print a message, indicating the post is already deleted.
           - If the post status is flagged to be banned, update the post status to *banned*.
       - If the reported item type is `comment`:
         - Query the database to fetch the comment using the reported item ID, not in published/hidden/removed status.
           - If no comment is found, raise a not found error.
           - If the comment status is banned, raise a conflict error, indicating the comment is already banned.
           - If the comment status is flagged deleted, print a message, indicating the comment is already deleted.
           - If the comment status is flagged to be banned, update the comment status to *banned*.

<br>

#### Manage User Restriction/Ban

- **Abstract Pseudocode for `user_restrict_ban_detail_user_operation`** 

  1. **Initialize Function**:
     - Accept user ID, report ID, restriction status, and database session as inputs.

  2. **Fetch Active Restriction/Ban**:
     - Query the database to fetch the active restriction/ban entry.
     - If no such entry is found, raise a not found error.

  3. **Handle Current Restriction/Ban Entry**:
     - Mark the current restriction/ban entry as not active.

  4. **Fetch User**:
     - Query the database to fetch the user using the user ID, not in active/deleted status.

  5. **Process Update**:
     - If the user is found:
       - Query the database to find the next consecutive restriction/ban for the user (excluding the current expired one).
         - If a consecutive restriction/ban is found:
           - Mark the consecutive restriction/ban as active.
           - Update the enforce action time to current time.
           - Mark action enforced as early.
           - Perform consecutive violation specific operations.
           - Update reported user status appropriately if needed based on user's current status and consecutive ban.
           - If consecutive violation is a ban (temporary or permanent), mark send email flag as True.
         - Else, update the user status to *active* if user is not deactivated/inactive.
     - Else, raise an exception indicating the user associated with the restriction/ban was not found.

  6. **Return Response**:
     - Return the consecutive violation and flag to notify the notification email status.

<br>

#### Manage Guideline Violation Score and Last Added Score

- **Abstract Pseudocode for `guideline_violation_score_last_added_score_operation`** 

  1. **Initialize Function**:
     - Accept user ID, report ID, ban content type, database session, content to be unbanned count, content already unbanned count, and account report flagged content count (optional) as inputs.

  2. **Fetch Guideline Violation Score Entry**:
     - Query the database to fetch the guideline violation score entry using the user ID.
     - If no such entry is found, raise a not found error.

  3. **Fetch Last Added Score Entry**:
     - Query the database to fetch the last added score entry using the score ID and report ID.
     - If no such entry is found, raise a not found error.

  4. **Determine Content Violation Score Type and Current Content Violation Score**:
     - Determine the specific content violation score type (post, comment, or message).
     - Get the current content violation score.
     - If the reported item type is `account`, use *post score* as a default.

  5. **Calculate Effective Last Added Score**:
     - Get the last added score associated with the report.
     - Get the current final violation score.
     - If account report flagged content count is provided:
       - Calculate the effective last added score as a fraction of the last added score.
     - Else, effective last added score will be the last added score.

  6. **Adjust Scores**:
     - Calculate the new content violation score as the maximum of the current content violation score minus the effective last added score, or zero (if difference is negative).
     - Calculate the new final violation score as the maximum of the current final violation score minus the effective last added score, or zero (if difference is negative).

  7. **Update Last Added Score Status**:
     - If the ban content type is `account`:
       - If the sum of content already unbanned count and content to be unbanned count is equal to the account report valid flagged content count or ban content type is `post` or `comment`:
         - Mark the last added score as removed.

  8. **Update Guideline Violation Score Entry**:
     - Update the guideline violation score entry with the new content violation score and the new final violation score.

<br>

#### Manage Post/Comment

- **Abstract Pseudocode for `post_comment_operation`** 

  1. **Initialize Function**:
     - Accept ban content ID, ban content type, and database session as inputs.

  2. **Handle the Post**:
     - If ban content type is `post`:
       - Query the database to fetch the post using the ban content ID with banned status.
       - If no such post is found, raise a not found error.
       - Update the post status to *published*.

  3. **Handle the Comment**:
     - If ban content type is `comment`:
       - Query the database to fetch the comment using the ban content ID with banned status.
       - If no such comment is found, raise a not found error.
       - Update the comment status to *published*.

<br>

### Events

#### Logout After User Status Specific Change

- **Abstract Pseudocode for `send_logout_request`** 

  1. **Initialize Function**:
     - Accept a target user object as input.
     - Get the logger.

  2. **Send Logout Request**:
     - Construct the logout request URL.
     - Construct the request body with username, device info, action, and flow for logout API.
     - Make a `POST` request to the logout API.
     - Log success or handle potential errors/exceptions.

  3. **Print Success Message**:
     - Print a message indicating the user was logged out successfully.

- **Abstract Pseudocode for `call_logout_after_update_user_status_attribute_listener`** 

  1. **Initialize Function**:
     - Accept the target user object, the new status value, the old status value, and the initiator as input.

  2. **Check for Status Change**:
     - Print the new status value.
     - If the old status value exists and the user not in deactivated/banned/inactive status is updated to a deactivated/banned/inactive status:
       - Get the database session associated with the target user object.
       - If a session is found:
         - Listen for the *after commit* event on the session.
         - When the *after commit* event occurs, call the `send_logout_request` function with the target user object.

- **Abstract Pseudocode for Event Listener** 

  1. **Listen for Status Changes**:
     - Listen for changes to the user status..
     - When the user status is set, call the `call_logout_after_update_user_status_attribute_listener` function with the target user object, the new status value, the old status value, and the initiator.

- **Database Tables Affected and Triggers involved** 
  - **Tables**: `user_session`, `user_auth_track`

  - **Triggers**: `user_auth_track_logout_trigger`

<br>

### Main

#### Root Route

> [!IMPORTANT] 
> Make sure the **Automatically follow redirects** is **ON** in Postman

- **Access Control** 

   *(NA)*

- **Abstract Pseudocode for `root`** 

  1. **Initialize Function**:
     - Accept request and optional refresh token (from cookie) as inputs.
     - Set main page message.
     - Set URL for token refresh.

  2. **Check for Refresh Token**:
     - If refresh token is not provided:
       - Return main page message.

  3. **Check for Authorization Header**:
     - If authorization header is present:
       - Extract the access token from authorization header.
       - Verify access token:
         - If access token is valid, redirect to the user feed.

  4. **Handle Errors**:
     - Print the exception/error
     - Call refresh request function with refresh token and token refresh URL and return the response.

- **API Documentation** 

   [Root Doc](https://venkatpaik17.github.io/VPKonnect/#operation/root_api_v0__get)

- **Database Tables Affected and Triggers involved** 
  - **Tables**: `user_auth_track`, `employee_auth_track`  

  - **Triggers**: None

- **Postman Scripts Flow** 
  - **Pre-request**:
    1. Set Authorization Header if applicable
       - Checks if a `JWT` environment variable exists.
       - If it exists, adds an `Authorization` header to the request with the value `Bearer` followed by the JWT.

  - **Post-response**:
    1. Saving Access Token from the Response to Postman Environment Variable and Get User Feed
       - Parse Response JSON.
       - Checks if the response code is `200 (OK)`.
       - If so, checks for an `access_token` in the response.
       - If an `access_token` exists, saves it to the `JWT` environment variable and constructs an `Authorization` header.
       - Fetch the user's feed using the generated `Authorization` header.
       - If the user's feed fetch is successful, display the feed response.
       - Handle errors appropriately.

<br>

#### Token Refresh Request Function

- **Abstract Pseudocode for `refresh_request`** 

  1. **Initialize Function**:
     - Accept refresh token and token refresh URL as inputs.
     - Consider the refresh token to be set a cookie.

  2. **Send Refresh Request**:
     - Make a POST request to the token refresh API to get a new access token.
     - Get the response containing new access token and format it to JSON.
     - Get the refresh token from the cookie.
     - If no refresh token is found, raise a internal server error.
     - Set the refresh token as an HTTP-only, secure cookie.
     - Log success or handle potential errors/exceptions.

  3. **Return Response**:
     - Return the JSON response.

<br>

#### Token Expiry Exception Handler

- **Abstract Pseudocode for `token_expiry_exception_handler`** 

  1. **Initialize Function**:
     - Accept request and token expiry exception as inputs.

  2. **Extract Token Type**:
     - Extract the token type from the exception detail message.

  3. **Get Refresh Token**:
     - Get the refresh token from the request cookies.

  4. **Handle Token Refresh**:
     - If the token type is user:
       - Call the refresh request function with the refresh token and the user token refresh URL and return the response.
     - Else (token type is employee), call the refresh request function with the refresh token and the employee token refresh URL and return the response.


---

## Project Notes

### Consecutive Violation Actions

The system manages consecutive violation actions (such as restrictions and bans) that are stacked sequentially. Here’s how it works:

- **Active Violation Action:**
   - If there is already an active violation action (like a restriction or ban), any subsequent violation that occurs is handled as a *future action*.
   - The *future action* is scheduled to be enforced once the current action expires. 

- **Appeal Handling (Early Action Enforcement):**
   - If an appeal is submitted for the current active violation action, and the appeal is accepted, the current action is revoked immediately.
   - The next violation action in the sequence is then enforced right away, even before the original action duration expires. This is referred to as *early action enforcement*.

#### Flow: <!-- omit in toc -->

- A violation occurs -> A current action (restriction/ban) is enforced.
- Another violation is reported and resolved -> The *future action* is queued up to be enforced after the current action finishes.
- If the current action is appealed and accepted -> The action is revoked immediately, and the next action is enforced right away.


### Check Appeal Policy  

1. **Appeal Type: Account | Report Type: Account**  
   - If a previous appeal to revoke a ban on at least one valid flagged content post linked to the account restriction/ban was rejected (REJ), an appeal to revoke the restriction/ban on that account cannot be made.  

2. **Appeal Type: Account | Report Type: Post/Comment**  
   - If a previous appeal to revoke a ban on a post/comment linked to the account restriction/ban was rejected (REJ), an appeal to revoke the restriction/ban on that account cannot be made.  

3. **Appeal Type: Post | Report Type: Account**  
   - If a previous appeal to revoke an account restriction/ban linked to the valid flagged content post ban was rejected (REJ), an appeal to revoke the ban on those valid flagged content posts cannot be made.  

4. **Appeal Type: Post/Comment | Report Type: Post/Comment**  
   - If a previous appeal to revoke an account restriction/ban linked to a post/comment ban was rejected (REJ), an appeal to revoke the ban on that post/comment cannot be made.  


### Report/Appeal Handling Flow  

1. Content Moderator Admins review all submitted reports and appeals on the Admin Dashboard.  
2. They assign all these reports and appeals to appropriate content moderators for further review and action.  
3. Content Moderators access their dashboards to view assigned reports and appeals.  
4. Moderators place necessary reports and appeals under review before proceeding.  
5. For appeals, moderators must verify compliance with the appeal policy before making a decision.  
6. Moderators thoroughly review each case and take appropriate action based on the findings.  


### User Restrictions Based on Restriction Level  

#### Partial Restriction (RSP) User:  <!-- omit in toc -->
- Cannot like a post.  
- Cannot comment on a post.  
- Can follow/unfollow users.  
- User profile remains visible.  
- Other users (followers for private accounts and everyone for public accounts) can interact with the RSP user’s posts (like, comment, follow, etc.).  
- Can publish new posts.  
- Can edit posts.  
- Can delete any post except for banned (BAN) posts.  
- Cannot like a comment.  
- Cannot edit comments.  
- Can delete comments (own or others').  

#### Full Restriction (RSF) User:  <!-- omit in toc -->
- Cannot like a post.  
- Cannot comment on a post.  
- Cannot follow/unfollow users.  
- User profile remains visible.  
- Other users (followers for private accounts and everyone for public accounts) can interact with the RSF user’s posts (like, comment, follow, etc.).  
- Cannot publish new posts.  
- Cannot edit posts.  
- Cannot delete posts except those flagged to be banned (FLB).  
- Cannot like a comment.  
- Cannot edit comments.  
- Comment Deletion Rules:  
    - If the RSF user is the post owner, they can delete only other users' comments but not their own.  
    - If the RSF user is the comment owner, they cannot delete their own comments.  
    - Exception: Comments flagged to be banned (FLB) can be deleted.


### FLB, FLD, and BAN Status for Posts/Comments  

- **BAN** (Banned): Used for immediate removal of content due to policy violations.  
- **FLB** (Flagged to be Banned): Used for future action, marking the post/comment for a scheduled ban.  
- **FLD** (Flagged Deleted): Applied when an FLB post/comment is deleted by the user.  

#### Behavior of FLB Posts/Comments:  <!-- omit in toc -->
- **Visibility:**  
  - FLB posts are visible only to the owner on their profile.  
  - FLB posts are hidden from followers (private accounts) and public (public accounts). 
  - FLB posts do not appear in user feeds but can still be fetched if the post ID is known.  
  - FLB comments will be listed under the "flagged comments" section of a post.  

- **Restrictions on FLB Content:**  
  - Cannot be edited.
  - Cannot be liked/unliked. 
  - Users who liked an FLB post/comment cannot be fetched.

- **Enforcement & Deletion Rules:**  
  - When the scheduled future action is enforced, FLB content changes to BAN.  
  - If a post/comment is FLB, FLD, or BAN and the user deactivates (DAH/PDH), the status does not change to HID (Hidden).  
  - If a user deletes an FLB post/comment (FLD), it does not affect the scheduled enforcement, the violation action will still be applied.  
  - When a post/comment with FLD/BAN status is deleted (e.g., due to account deletion), the status remains unchanged, but `is_deleted = True` is set to indicate deletion.


### Non-Adaptive User Restrictions (RSF/RSP)  

The current restriction system applies a fixed set of limitations when a user is placed under Partial (RSP) or Full (RSF) Restriction. However, these restrictions are not adaptive to the user's specific violation patterns.  

For example:  
- If a user repeatedly violates policies through posts, the restriction should focus more on limiting post-related actions rather than comments.  
- If a user’s violations are mostly comment-related, the restriction should prioritize comment limitations instead of broadly applying both post and comment restrictions.  

A more dynamic approach should assess the user’s violation history and apply tailored restrictions based on their behavior. This would ensure more effective moderation while preventing unnecessary limitations on areas where the user has not shown problematic activity.


### Postman Testing Involving Redirection  

> [!NOTE]
> Go to Postman -> Settings -> Under **Headers** section, look for **Automatically follow redirects**

- **Root Endpoint (`GET localhost:8000/api/v0/`)**  
  - Automatic Redirection: **ON**  
  - Required to properly handle potential redirects automatically 

- **Get Post Endpoint (`GET localhost:8000/api/v0/posts/{post_id}`)**  
  - Automatic Redirection: **OFF**  
  - Redirection is handled in post-response script


### Appeal Action Mechanism

*(To be included)*

---


## Project Experience, Mistakes, What Next?

### Experience

I started this project as a challenge, thinking I could wrap it up in a few months and maybe even take it end to end. But as time went on, I realized just how complex things could get. It was a roller coaster ride, some nights, I would literally dream about code, and at times, I'd wake up with solutions in my head.

There were days of intense progress and days where nothing moved forward. Sometimes, I would be completely blank, and other times, I felt like quitting altogether. I’d fix one thing only to realize something else had broken. Some debugging sessions stretched for hours, only to end with the realization that it was a small mistake or a misunderstanding on my part.

Despite all the ups and downs, it was a valuable experience. I gained confidence, not that I could do it perfectly, but that I could do it. More importantly, this whole journey sparked a deeper interest and curiosity in me to keep learning, improving, and exploring new things.

### Mistakes

1. **REST API Design Fundamentals** – Due to limited knowledge, I lacked clarity on properly implementing REST principles. I tried my best to do it right, but with more understanding, I know I can improve significantly.
2. **Ignoring Unit Testing** – This was my biggest mistake in the project. Debugging became a painful process, and evaluating different use cases was much harder than it should have been. I had to rely on manual testing and intuition, which was inefficient and unreliable. Proper unit testing would have given me better test coverage and a structured framework to validate functionality after making changes.
3. **Improper Exception Handling** – I realized I lacked fundamental knowledge in handling exceptions effectively. I used them to the best of my understanding, but as the project grew and involved multiple and nested functions, it became difficult to track errors. Additionally, I could have implemented custom exceptions to handle specific errors more efficiently. A structured approach would have improved debugging and made error responses more meaningful.
4. **Logging** – I have used logging in my project, but I feel I could do much better. More practical usage examples, such as structured logging, logging levels, and proper log management, would help me implement it more effectively. Right now, my logging approach is okay, and improving it could enhance debugging, monitoring, and troubleshooting.
5. **Poor Documentation of Changes** – I didn't properly track or document design and business logic changes. Additionally, I didn't account for dependencies, making it harder to assess the impact of modifications.
6. **Lack of Strong Fundamentals** – Since this project was an extension of a basic tutorial, gaps in my foundational knowledge affected how I used frameworks, libraries, and packages. This led to errors and non-standard practices.
7. **Neglecting Clean Code & Refactoring** – I didn’t prioritize clean coding practices or refactoring, which resulted in messy and hard-to-maintain code. My focus was primarily on making things functional rather than writing well-structured, readable, and efficient code. While this approach helped me move forward quickly, it also made debugging and future modifications more challenging.
8. **Handling Reports During DAH/PDH** – When a user was Deactivated (DAH) or Permanently Deactivated (PDH), I should have ensured their reports were hidden (HID). This oversight led to inconsistencies in report management.
9. **Inconsistent Consecutive Violation Handling for PBN** – When handling consecutive violations, I overlooked a key inconsistency in report actions. If a Permanent Ban (PBN) was already scheduled for a future violation, another PBN triggered by a separate report action created conflicts. Since PBN is the final stage of a ban, stacking multiple PBNs does not make sense and leads to enforcement inconsistencies.
10. **Dependent on Postman** – The project relies on Postman for API testing, including the use of Postman scripts. While there are alternative tools compatible with Postman files, the project should not be tightly coupled to a specific tool for better flexibility and maintainability.
11. **Use of PostgreSQL Triggers** – Using PostgreSQL triggers unnecessarily increased system complexity and made tracking operations harder. A better approach would have been to manage most operations in the application code, reserving triggers for shared and repetitive tasks across multiple routes.

### What Next?

1. **Deep Dive into Core Concepts** – Explore in-depth the technologies and principles I used in this project, ensuring I fully understand their capabilities and best practices.  
2. **Adopt Best Practices** – Focus on writing maintainable, scalable, and efficient code by following industry standards and design principles.  
3. **Prioritize Clean Code** – Improve code readability, structure, and organization to make it easier to maintain and extend.  
4. **Learn System Design** – Get familiar with designing scalable and efficient systems, understanding architecture patterns, and making better design decisions.  
5. **Work on Side Projects** – Apply what I’ve learned by building new projects, refining my skills, and exploring different problem domains.  
6. **Master Testing** – Focus on unit testing, integration testing, and automation to ensure reliability and maintainability of code.  
7. **Read Professional Codebases** – Analyze well-structured open-source projects and production-level code to understand how experienced developers write and organize their code.  
8. **Improve Documentation** – Develop the habit of documenting code, design decisions, and API structures to improve clarity and maintainability.  
9. **Experiment with Different Technologies** – Explore new frameworks, tools, and approaches to expand my knowledge and adaptability in backend development.

---

## Reference and Credits

### Concepts & Implementations  
- **[ULID Generation in UUID Format](https://blog.daveallie.com/ulid-primary-keys/)**  
- **[Aadhaar Generation & Validation](https://github.com/NikhilPanwar/aadharCardValidatorAndGenerator/)**  
- **[RBAC Using Decorators & Wrappers](https://github.com/rajansahu713/FastAPI-Projects/blob/main/Role%20Base%20Authentication/authorizations.py/)**  
- **[Uploading & Saving Files in FastAPI](https://medium.com/@bcenterezdhar.ezy/how-to-save-uploaded-files-in-fastapi-e6dcb312cd84/)**  
- **[Python Logging](https://www.youtube.com/watch?v=9L77QExPmI0)**  
- **[Customized Structured Logging](https://stackoverflow.com/questions/70891687/how-do-i-get-my-fastapi-applications-console-log-in-json-format-with-a-differen)**  
- **Violation Score Mechanism** – Dr. Shrinivas Pai  

### Project Structure & Design  
- **[FastAPI Real-World Example App](https://github.com/nsidnev/fastapi-realworld-example-app/tree/master/app/core/settings/)**  
- **[FastAPI Best Practices](https://github.com/zhanymkanov/fastapi-best-practices?tab=readme-ov-file/)**  
- **[Choosing a PostgreSQL Primary Key](https://supabase.com/blog/choosing-a-postgres-primary-key/)**  

### Authentication & Security  
- **[Forgot Password Token Handling](https://hackernoon.com/how-to-implement-a-forgot-password-flow-with-pseudo-code-7u1j379a/)**  

### Libraries & Tools  
- **[pyfa_converter](https://github.com/dotX12/pyfa-converter/)**  
- **[fastapi-mail](https://sabuhish.github.io/fastapi-mail/)**  

### Official Documentation & Learning Resources  
- **[FastAPI Documentation](https://fastapi.tiangolo.com/)**  
- **[Pydantic v1.10 Documentation](https://docs.pydantic.dev/1.10/)**  
- **[SQLAlchemy Documentation](https://docs.sqlalchemy.org/en/14/)**  
- **[Alembic for Migrations](https://alembic.sqlalchemy.org/en/latest/)**  
- **[PostgreSQL Tutorial](https://neon.tech/postgresql/tutorial/)**  
- **[Python 3.10 Official Docs](https://docs.python.org/3.10/)**  

### General Resources & Community Help  
- **[Stack Overflow](https://stackoverflow.com/)**  
- **AI Assistance**:  
  - **[ChatGPT](https://chatgpt.com/)**  
  - **[Gemini AI](https://gemini.google.com/)** 

---

## Feedback and Suggestions

*(Encourage feedback and contributions)*