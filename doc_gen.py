#!/usr/bin/python3

"""
This scripts searches through the directory tree of the repository to discover
change and generate/update README.md files with appropriate links.
"""

import os
import re

PROJECT_DIR = '.'
README = 'README.md'
TABLE_OF_CONTENTS_STRING = '## Table of Contents'

PRETTY_PATTERN = '[^a-z]*[a-z]*'
TABLE_OF_CONTENTS_PATTERN = '(## Table of Contents)((.|\n)*)'
HEADER_PATTERN = '(\n#)'

BLACKLIST = [
    '.git',
    '.vs',

    'doc_gen.py',
    README,
]


def extract_name(value):
    result = re.findall('[[].*[]]', value)
    assert len(result) == 1
    return result[0][1:-1].replace(' ', '')


def generate_dir_record(directory):
    words = re.findall(PRETTY_PATTERN, directory)
    pretty_dirname = ' '.join(words).rstrip()
    return '* [' + pretty_dirname + '](' + directory + ')'


def generate_file_record(file):
    filename = os.path.splitext(file)[0]
    words = re.findall(PRETTY_PATTERN, filename)
    pretty_filename = ' '.join(words).rstrip()
    return '* [' + pretty_filename + '](' + file + ')'


def gather_files(dir_path):
    file_map = {}
    for root, subdirs, files in os.walk(dir_path):
        subdirs[:] = [d for d in subdirs if d not in BLACKLIST]
        files[:] = [f for f in files if f not in BLACKLIST]
        file_map[root] = {}
        file_map[root]['subdirs'] = [generate_dir_record(d) for d in subdirs]
        file_map[root]['files'] = [generate_file_record(f) for f in files]
    return file_map


def offset_records(root, key, file_map, offset=1):
    offset_val = '  ' * offset
    records = []
    link_prefix = '](' + key.replace(root + '\\', '') + '/'
    for target_dir in file_map[key]['subdirs']:
        value = offset_val + target_dir
        value.replace('](', link_prefix)
        records.append(value)
        records.append(offset_records(root, key + '\\' + extract_name(target_dir), file_map, offset+1))
    for target_value in file_map[key]['files']:
        value = offset_val + target_value
        value = value.replace('](', link_prefix)
        records.append(value)
    return records


def generate_docs(file_map):
    table_of_contents = {}
    for key in file_map:
        table_of_contents[key] = []
        for subdir in file_map[key]['subdirs']:
            table_of_contents[key].append(subdir)
            table_of_contents[key] += offset_records(key, key + '\\' + extract_name(subdir), file_map)
        table_of_contents[key] += file_map[key]['files']
    return table_of_contents


def write_docs(doc_map):
    for key in doc_map:
        readme = os.path.join(key, README)
        if os.path.isfile(readme):
            with open(readme, 'r') as file:
                file_contents = file.read()
        else:
            file_contents = TABLE_OF_CONTENTS_STRING

        existing_content = re.search(TABLE_OF_CONTENTS_PATTERN + HEADER_PATTERN, file_contents)
        has_additional_control = existing_content is not None
        if existing_content is None:
            existing_content = re.search(TABLE_OF_CONTENTS_PATTERN, file_contents)

        content_tail = '\n\n#' if has_additional_control else ''
        new_content = TABLE_OF_CONTENTS_STRING + '\n\n' + "\n".join(doc_map[key]) + content_tail
        file_contents = file_contents.replace(existing_content.group(0), new_content)

        with open(readme, 'w+') as file:
            file.write(file_contents)


if __name__ == '__main__':
    PROJECT_DIR = os.path.dirname(os.path.realpath(__file__))
    repo_map = gather_files(PROJECT_DIR)
    doc_map = generate_docs(repo_map)
    write_docs(doc_map)
