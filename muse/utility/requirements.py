def file_to_list(filepath: str):
    with open(filepath) as fr:
        data = fr.readlines()
    data = list(map(lambda x: x.replace("\n", ""), data))
    return data
