#!/usr/bin/env python
# coding=UTF-8

__author__ = u"Mickaël Zhu"
__license__ = u"MIT"
__version__ = u"0.1"
__status__ = u"Prototype"

# core libs
import os
import sys
import json

# 3rd party libs
import termcolor
from redmine import Redmine


# print color

print_debug = lambda x: termcolor.cprint(x, 'white')
print_info = lambda x: termcolor.cprint(x, 'white')
print_title = lambda x: termcolor.cprint(x, 'green')
print_warning = lambda x: termcolor.cprint(x, 'magenta')
print_error = lambda x: termcolor.cprint(x, 'red')
print_fatal = lambda x: termcolor.cprint(x, 'red', 'on_white')


# Redmine config

class RedmineConfig(object):
    url = u"http://localhost/"
    api_key = u""


home = os.getenv("HOME")
config_file = home + '/.redmine_cli'
config = RedmineConfig()

# config loader

def load_config():
    """Load config file"""
    with open(config_file, 'r') as infile:
        loadedJson = json.load(infile)
        if 'url' in loadedJson:
            config.url = loadedJson['url']
        if 'api_key' in loadedJson:
            config.api_key = loadedJson['api_key']


# config writer
def save_config():
    """Save config file"""
    with open(config_file, 'w') as outfile:
        json.dump(
            {
                'url': config.url,
                'api_key': config.api_key
            },
            outfile
        )


# getter for redmine lib

redmine = None


def get_redmine():
    """
    :return: Redmine instance
    :rtype: Redmine
    """
    global redmine
    if redmine is None:
        redmine = Redmine(config.url, key=config.api_key)
    return redmine


# function

def _input_int():
    response = raw_input('> ').strip()
    try:
        return int(response, 10)
    except ValueError:
        return -1


def print_issues():
    list = get_redmine().issue.filter(assigned_to_id="me", status_id=1)
    if len(list) == 0:
        print_warning("No issues")
        return

    id_max_length = len(str(max(map(lambda x: x.id, list))))
    for issue in list:
        id_length = len(str(issue.id))
        print_title(
            u"#%d %s %s [%s]" %
            (
                issue.id,
                " " * (id_max_length - id_length),
                issue.subject,
                issue.project.name
            )
        )
        print_debug(
            u"%s- status : %s" %
            (
                " " * (id_max_length + 4),
                issue.status.name
            )
        )
        print_debug(
            u"%s- auteur : %s" %
            (
                " " * (id_max_length + 4),
                issue.author.name
            )
        )


def print_projects():
    list = get_redmine().project.all()
    if len(list) == 0:
        print_warning("No projects")
        return

    id_max_length = len(str(max(map(lambda x: x.id, list))))
    for project in list:
        id_length = len(str(project.id))
        print_title(
            u"#%d %s %s" %
            (
                project.id,
                " " * (id_max_length - id_length),
                project.name
            )
        )
        print_debug(
            u"%s- identifier : %s" %
            (
                " " * (id_max_length + 4),
                project.identifier
            )
        )


def create_issue():
    # Select the project
    print_title(u"Which project?")
    project_list = get_redmine().project.all()
    for n, project in enumerate(project_list):
        print_info(" %d: %s" % (n + 1, project.name))
    while True:
        project_i = _input_int()
        if project_i <= 0 or project_i > len(project_list):
            print_error("Invalid number")
            continue

        project = project_list[project_i - 1]
        break
    print_info("You selected %s" % (project.name))

    # Select the issue category
    print_title(u"Which tracker?")
    tracker_list = project.trackers
    for n, tracker in enumerate(tracker_list):
        print_info(" %d: %s" % (n + 1, tracker.name))
    while True:
        tracker_i = _input_int()
        if tracker_i <= 0 or tracker_i > len(tracker_list):
            print_error("Invalid number")
            continue

        tracker = tracker_list[tracker_i - 1]
        break
    print_info("You selected %s" % (tracker.name))

    # Type subject
    print_title(u"Subject?")
    while True:
        subject = raw_input("> ").strip()
        if subject:
            break
        print_error("Please define a subject")

    # Type description
    print_title("Description?")
    descriptionList = []
    while True:
        line = raw_input("> ").strip()
        if line:
            descriptionList.append(line)
            continue
        break
    description = "\n".join(descriptionList)

    # Select the assigned user
    print_title(u"Which assigned user?")
    user_list = get_redmine().user.all()
    for n, user in enumerate(user_list):
        print_info(" %d: %s" % (n + 1, user.login))
    while True:
        user_i = _input_int()
        if user_i <= 0 or user_i > len(user_list):
            print_error("Invalid number")
            continue

        user = user_list[user_i - 1]
        break
    print_info("You selected %s" % (user.login))

    # Send issue

    print_title("Create this issue (y/n)")
    print_info("Project : %s" % (project.name))
    print_info("Tracker : %s" % (tracker.name))
    print_info("Subject : %s" % (subject))
    print_info("Description : %s" % (description))
    print_info("Assigned to : %s" % (user.login))

    while True:
        confirm = raw_input("> ").strip().lower()
        if confirm == "n":
            return
        if confirm == "y":
            break
        print_error("Invalid response")

    issue = get_redmine().issue.new()
    issue.project_id = project.id
    issue.tracker_id = tracker.id
    issue.subject = subject
    issue.description = description
    issue.assigned_to_id = user.id
    issue.status_id = 1
    issue.priority_id = 1
    if issue.save():
        print_info("Done")
    else:
        print_error("Error")


def install():
    global redmine

    print_info(u"Type root url of redmine (don't forget scheme)")
    url = raw_input('> ').strip()
    if url:
        config.url = url
    elif config.url:
        print_info(u"Use default url : " + config.url)

    print_info(u"Type your api key")
    api_key = raw_input('> ').strip()
    if api_key:
        config.api_key = api_key
    elif config.api_key:
        print_info(u"Use default api key : " + config.api_key)

    try:
        len(get_redmine().project.all())
    except Exception as e:
        redmine = None
        print_error(str(e))
        return install()

    save_config()


def prompt_main():
    print_title(u"\n\nSelect your action")
    print_info(u" 1: Show projects")
    print_info(u" 2: Show issues")
    print_info(u" 3: Create an issue")
    print_info(u" 0: Quit the program")

    i = _input_int()

    if i == 0:
        sys.exit(0)
    if i == 1:
        print_projects()
    elif i == 2:
        print_issues()
    elif i == 3:
        create_issue()
    else:
        print_error(u"Unknown command")


# main program

termcolor.cprint(u"REDMINE CLI", "blue", "on_white")

if __name__ == '__main__':
    if os.path.isfile(config_file):
        try:
            load_config()
        except ValueError as e:
            print_fatal(u"Invalid json config file")
            print_fatal(e.message)
            print_fatal(u"Please delete .redmine_cli in your home")
            sys.exit(0)
    else:
        print_warning("Redmine config not found. Please configure")
        install()

    while True:
        prompt_main()