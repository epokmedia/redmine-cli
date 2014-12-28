import time
import atexit
import json
import os

def _timestamp():
    return int(time.time())

class Task(object):
    total = 0
    start = None
    issue_id = None
    description = ""


class Tasks(object):
    file = ""
    list = []

    def __init__(self, file):
        self.file = file
        atexit.register(self.stop_all_tasks)

    def load(self):
        """
        Load config from file
        """
        if os.path.isfile(self.file):
            try:
                with open(self.file, 'r') as infile:
                    content = json.load(infile)
                    for row in content.get('tasks', []):
                        task = Task()
                        task.total = row.get('total', 0)
                        task.start = row.get('start', None)
                        task.issue_id = row.get('issue_id', None)
                        task.description = row.get('description', "")
                        self.list.append(task)
            except Exception as e:
                print(e)


    def save(self):
        """
        Save config to file
        """
        with open(self.file, 'w') as outfile:
            list = []
            for task in self.list:
                list.append({
                    'total': task.total,
                    'start': task.start,
                    'issue_id': task.issue_id,
                    'description': task.description,
                });
            json.dump(
                {
                    'tasks': list,
                },
                outfile
            )

    def find_from_issue(self, issue_id):
        filtered = [t for t in self.list if t.issue_id == issue_id]
        return filtered[0] if len(filtered) > 0 else None


    def start_task(self, issue_id, description):
        task = self.find_from_issue(issue_id)
        if task is None:
            task = Task()
            task.issue_id = issue_id
            self.list.append(task)
        task.description = description
        task.start = _timestamp()
        self.save()

    def stop_task(self, issue_id):
        task = self.find_from_issue(issue_id)
        if task and task.start:
            task.total += _timestamp() - task.start
            task.start = None
        self.save()

    def stop_all_tasks(self):
        filtered = [t for t in self.list if t.start is not None]
        for task in filtered:
            task.total += _timestamp() - task.start
            task.start = None
        self.save()

    def delete_task(self, issue_id):
        task = self.find_from_issue(issue_id)
        if task:
            self.list.remove(task)
        self.save()