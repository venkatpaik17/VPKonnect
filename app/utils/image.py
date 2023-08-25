from pathlib import Path

image_folder = Path("images")


# def get_or_create_user_image_subfolder(username: str):
#     user_subfolder = image_folder / username
#     user_subfolder.mkdir(parents=True, exist_ok=True)

#     return user_subfolder


def get_or_create_user_image_subfolder(user_id: str):
    user_subfolder = image_folder / user_id
    user_subfolder.mkdir(parents=True, exist_ok=True)

    return user_subfolder


def get_or_create_user_profile_image_subfolder(user_subfolder: Path):
    profile_subfolder = user_subfolder / "profile"
    profile_subfolder.mkdir(parents=True, exist_ok=True)

    return profile_subfolder


def get_or_create_user_posts_image_subfolder(user_subfolder: Path):
    posts_subfolder = user_subfolder / "posts"
    posts_subfolder.mkdir(parents=True, exist_ok=True)

    return posts_subfolder
