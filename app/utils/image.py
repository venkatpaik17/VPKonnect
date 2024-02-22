from pathlib import Path

image_folder = Path("images")


# def get_or_create_user_image_subfolder(username: str):
#     user_subfolder = image_folder / username
#     user_subfolder.mkdir(parents=True, exist_ok=True)

#     return user_subfolder


def get_or_create_entity_image_subfolder(entity: str, repr_id: str):
    entity_subfolder = image_folder / entity / repr_id
    entity_subfolder.mkdir(parents=True, exist_ok=True)

    return entity_subfolder


def get_or_create_entity_profile_image_subfolder(entity_subfolder: Path):
    profile_subfolder = entity_subfolder / "profile"
    profile_subfolder.mkdir(parents=True, exist_ok=True)

    return profile_subfolder


def get_or_create_user_posts_image_subfolder(user_subfolder: Path):
    posts_subfolder = user_subfolder / "posts"
    posts_subfolder.mkdir(parents=True, exist_ok=True)

    return posts_subfolder
