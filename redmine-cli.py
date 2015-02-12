#!/usr/bin/env python
# coding=UTF-8

__author__ = u"Mickaël Zhu"
__license__ = u"MIT"
__version__ = u"0.1"
__status__ = u"Prototype"

# core libs
import sys
import os
import shlex

# 3rd party libs
from redmine import Redmine
import redmine.exceptions as exceptions

# libs
from redminecli.server.config import Config as ServerConfig
from redminecli.context import Context
import redminecli.printer as printer
import redminecli.history as history
from redminecli.task import *

# print banner

printer.banner(u"===========")
printer.banner(u"Redmine cli")
printer.banner(u"===========")

# create config directory
config_dir = os.path.expanduser("~/.redmine-cli")
if not os.path.exists(config_dir):
    os.mkdir(config_dir)

# register cli persistent history
history.register(config_dir + '/history')

# init server config
config = ServerConfig(config_dir + '/server.json')
if config.exists():
    try:
        config.load()
    except ValueError as e:
        printer.fatal(u"Invalid json config file")
        printer.fatal(e.message)
        printer.fatal(u"Please delete .redmine-cli/server.json in your home")
        sys.exit(0)
else:
    printer.warning("Redmine config not found. Please configure")
    config.install()


# init tasks
tasks = Tasks(config_dir + '/tasks.json')
tasks.load()

# init context
context = Context()


# init redmine. Use getter to initialize it
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


def _input_int():
    response = raw_input('> ').strip()
    try:
        return int(response, 10)
    except ValueError:
        return -1


def create_issue():
    project = context.project

    # Select the issue category
    printer.title(u"Which tracker?")
    tracker_list = project.trackers
    for n, tracker in enumerate(tracker_list):
        printer.info(" %d: %s" % (n + 1, tracker.name))
    while True:
        tracker_i = _input_int()
        if tracker_i <= 0 or tracker_i > len(tracker_list):
            printer.error("Invalid number")
            continue

        tracker = tracker_list[tracker_i - 1]
        break
    printer.info("You selected %s" % (tracker.name))

    # Type subject
    printer.title(u"Subject?")
    while True:
        subject = raw_input("> ").strip()
        if subject:
            break
        printer.error("Please define a subject")

    # Type description
    printer.title("Description?")
    descriptionList = []
    while True:
        line = raw_input("> ").strip()
        if line:
            descriptionList.append(line)
            continue
        break
    description = "\n".join(descriptionList)

    # Select the assigned user
    printer.title(u"Which assigned user?")
    user_list = get_redmine().user.all()
    for n, user in enumerate(user_list):
        printer.info(" %d: %s" % (n + 1, user.login))
    while True:
        user_i = _input_int()
        if user_i <= 0 or user_i > len(user_list):
            printer.error("Invalid number")
            continue

        user = user_list[user_i - 1]
        break
    printer.info("You selected %s" % (user.login))

    # Send issue

    printer.title("Create this issue (y/n)")
    printer.info("Project : %s" % (project.name))
    printer.info("Tracker : %s" % (tracker.name))
    printer.info("Subject : %s" % (subject))
    printer.info("Description : %s" % (description))
    printer.info("Assigned to : %s" % (user.login))

    while True:
        confirm = raw_input("> ").strip().lower()
        if confirm == "n":
            return
        if confirm == "y":
            break
        printer.error("Invalid response")

    issue = get_redmine().issue.new()
    issue.project_id = project.id
    issue.tracker_id = tracker.id
    issue.subject = subject
    issue.description = description
    issue.assigned_to_id = user.id
    issue.status_id = 1
    issue.priority_id = 1
    if issue.save():
        printer.success("Done")
    else:
        printer.error("Error")


def issue_task_upload():
    task = tasks.find_from_issue(context.issue.id)
    if not task:
        printer.warning("No task")
        return

    # Select the issue category
    printer.title(u"Which activity?")
    activity_list = redmine.enumeration.filter(resource='time_entry_activities')
    for n, activity in enumerate(activity_list):
        printer.info(" %d: %s" % (n + 1, activity.name))
    while True:
        activity_i = _input_int()
        if activity_i <= 0 or activity_i > len(activity_list):
            printer.error("Invalid number")
            continue

        activity = activity_list[activity_i - 1]
        break
    printer.info("You selected %s" % (activity.name))

    # Type subject
    printer.title(u"Commentaire?")
    comments = raw_input("> ").strip()

    time_entry = get_redmine().time_entry.new()
    time_entry.issue_id = context.issue.id
    time_entry.hours = task.total // 3600
    time_entry.activity_id = activity.id
    time_entry.comments = comments
    time_entry.save()
    issue_task_delete()

    printer.title(u"Update done ratio? [%d]" % (context.issue.done_ratio))
    while True:
        response = raw_input('> ').strip()
        if not response:
            return

        try:
            done_ratio = int(response, 10)
            if done_ratio >= 0 and done_ratio <= 100:
                break
            printer.error("Invalid number")

        except ValueError:
            printer.error("Invalid number")

    get_redmine().issue.update(context.issue.id, done_ratio=done_ratio)


def select_project(id=None):
    if not id:
        printer.title(u"Select by typing the id or identifier")
        project_list = get_redmine().project.all()
        for n, project in enumerate(project_list):
            printer.info("%s [%d] (%s)" % (project.name, project.id, project.identifier))

        id = raw_input('> ')

    try:
        context.project = get_redmine().project.get(id)
        context.issue = None
    except exceptions.ResourceNotFoundError:
        printer.error("No project found with id %s" % (id))
        return


def unselect_project():
    context.project = None
    context.issue = None


def select_issue(id=None):
    if not id:
        if context.project:
            issue_list = get_redmine().issue.filter(assigned_to_id="me", project_id=context.project.id)
        else:
            issue_list = get_redmine().issue.filter(assigned_to_id="me")

        if len(issue_list) > 0:
            printer.title(u"Select by typing the id")
        else:
            printer.warning(u"No issues found")
            return

        if context.project:
            issue_list = get_redmine().issue.filter(assigned_to_id="me", status_id=1, project_id=context.project.id)
            for n, issue in enumerate(issue_list):
                printer.info("#%d %s" % (issue.id, issue.subject))
        else:
            issue_list = get_redmine().issue.filter(assigned_to_id="me", status_id=1)
            for n, issue in enumerate(issue_list):
                printer.info("#%d %s [%s]" % (issue.id, issue.subject, issue.project.name))

        id = raw_input('> ')

    try:
        context.issue = get_redmine().issue.get(id)
    except exceptions.ResourceNotFoundError:
        printer.error("No id found with id %s" % (id))
        return

    if not context.project or context.project.id != context.issue.project.id:
        context.project = get_redmine().project.get(context.issue.project.id)


def unselect_issue():
    context.issue = None


def show_issue():
    issue = context.issue
    printer.title(issue.subject)
    printer.info("ID : %d" % (issue.id))
    printer.info("Project : %s" % (issue.project.name))
    printer.info("Tracker : %s" % (issue.tracker.name))
    printer.info("Status : %s" % (issue.status.name))
    printer.info("Priority : %s" % (issue.priority.name))
    printer.info("Author : %s" % (issue.author.name))
    printer.info("Assigned to : %s" % (issue.assigned_to.name))
    printer.info("Description : %s" % (issue.description))
    printer.info("Start date : %s" % (issue.start_date))
    printer.info("Done ratio : %d" % (issue.done_ratio))
    printer.info("Spent hours : %f" % (issue.spent_hours))


def _format_duration(seconds):
    value = ''
    if seconds % 60 > 0:
        value = str((seconds % 60)) + 's'
    minutes = seconds / 60
    if minutes % 60 > 0:
        value = str((minutes % 60)) + 'm' + value
    return str(minutes / 60) + 'h' + value


def show_all_tasks():
    for task in tasks.list:
        printer.info("%s : %s %s" % (task.description, _format_duration(task.total), "*" if task.start else ""))


def issue_task_start():
    tasks.start_task(context.issue.id, " [%s] %s" % (context.project.name, context.issue.subject))


def issue_task_stop():
    tasks.stop_task(context.issue.id)


def issue_task_delete():
    tasks.delete_task(context.issue.id)


def issue_task_info():
    task = tasks.find_from_issue(context.issue.id)
    if task:
        printer.info("Total time %s" % (_format_duration(task.total)))
    else:
        printer.info("No task defined")


def interpret_from_project(args):
    if args[0] == 'help':
        printer.info(" - createissue : create issue")
        printer.info(" - tasks : show all tasks")
        printer.info(" - project [id|identifier] : select another project")
        printer.info(" - unselect : unselect the project")
        printer.info(" - issue [id] : select an issue")
        printer.info(" - exit : exit the program")
    elif args[0] == 'tasks':
        show_all_tasks()
    elif args[0] == 'createissue':
        create_issue()
    elif args[0] == 'project':
        select_project(args[1] if len(args) > 1 else None)
    elif args[0] == 'unselect':
        unselect_project()
    elif args[0] == 'issue':
        select_issue(args[1] if len(args) > 1 else None)
    else:
        printer.error("Invalid command. Type help")


def issue_task_edit():
    task = tasks.find_from_issue(context.issue.id)
    if not task:
        printer.warning("No task")
        return

    printer.title(u"Set second elapsed [%d]" % (task.total))
    while True:
        response = raw_input('> ').strip()
        if not response:
            return

        try:
            total = int(response, 10)
            break
        except ValueError:
            printer.error("Invalid number")
    task.total = total
    tasks.save()

def interpret_from_issue_context(args):
    if args[0] == 'help':
        printer.info(" - show_all_tasks : show all task")
        printer.info(" - tasks : show all tasks")
        printer.info(" - taskstart : start task counter")
        printer.info(" - taskstop : stop task counter")
        printer.info(" - taskinfo : show task info")
        printer.info(" - taskedit : edit task")
        printer.info(" - taskdelete : delete task")
        printer.info(" - taskupload : upload task")
        printer.info(" - project [id|identifier] : select another project")
        printer.info(" - unselect : unselect the issue")
        printer.info(" - issue [id] : select another issue")
        printer.info(" - info : info about this issue")
        printer.info(" - exit : exit the program")
    elif args[0] == 'tasks':
        show_all_tasks()
    elif args[0] == 'taskstart':
        issue_task_start()
    elif args[0] == 'taskstop':
        issue_task_stop()
    elif args[0] == 'taskedit':
        issue_task_edit()
    elif args[0] == 'taskdelete':
        issue_task_delete()
    elif args[0] == 'taskinfo':
        issue_task_info()
    elif args[0] == 'taskupload':
        issue_task_upload()
    elif args[0] == 'project':
        select_project(args[1] if len(args) > 1 else None)
    elif args[0] == 'unselect':
        unselect_issue()
    elif args[0] == 'issue':
        select_issue(args[1] if len(args) > 1 else None)
    elif args[0] == 'info':
        show_issue()
    elif args[0] == 'cd':
        if len(args) < 2:
            unselect_project()
        elif args[1] == '..':
            unselect_issue()
    else:
        printer.error("Invalid command. Type help")


def interpret(args):
    """

    :rtype : list
    """
    if len(args) == 0:
        return

    if args[0] == 'exit':
        sys.exit(0)

    if context.issue and context.project:
        return interpret_from_issue_context(args)
    elif context.project:
        return interpret_from_project(args)

    if args[0] == 'help':
        printer.info(" - project [id|identifier] : select a project")
        printer.info(" - exit : exit the program")
    elif args[0] == 'project':
        select_project(args[1] if len(args) > 1 else None)
    elif args[0] == 'issue':
        select_issue(args[1] if len(args) > 1 else None)
    else:
        printer.error("Invalid command. Type help")


def prompt():
    if context.issue and context.project:
        user_input = raw_input("[%s] #%d > " % (context.project.identifier, context.issue.id))
    elif context.project:
        user_input = raw_input('[%s] > ' % (context.project.identifier))
    else:
        user_input = raw_input('[] > ')
    user_input_splitted = shlex.split(user_input)
    interpret(user_input_splitted)

while True:
    prompt()

