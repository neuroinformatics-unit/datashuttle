def tags(tag_name):
    tags = {
        "date": "@DATE@",
        "time": "@TIME@",
        "datetime": "@DATETIME@",
        "to": "@TO@",
        "*": "@*@",
    }
    return tags[tag_name]
