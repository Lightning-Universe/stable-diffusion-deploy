from pkg_resources import parse_requirements


def load_requirements(file_path: str):
    with open(file_path) as fr:
        requires = parse_requirements(fr.readlines())
    return list(requires)
