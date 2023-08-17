import ulid


# function to generate ulid and return as uuid (used ulid-py package)
def get_ulid():
    return ulid.new().uuid
