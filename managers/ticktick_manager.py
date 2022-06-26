import pickle
from datetime import datetime, timedelta

import helpers.ticktick_helper as ticktick_helper
from ticktick.oauth2 import OAuth2  # OAuth2 Manager
from ticktick.api import TickTickClient  # Main Interface


class TicktickManager:

    def __init__(self, client_id, client_secret, redirect_uri, username, password):
        self.auth_client = OAuth2(client_id=client_id,
                                  client_secret=client_secret,
                                  redirect_uri=redirect_uri)
        self.username = username
        self.password = password
        # authenticate the client
        self.client = TickTickClient(self.username,
                                     self.password,
                                     self.auth_client)

        # data in ticktick
        self.latest_tasks_in_ticktick = None
        self.latest_project_in_ticktick = None
        self.closed_projects = None
        self.latest_project_folder_in_ticktick = None
        self.inbox_id = None
        self.prev_data_ticktick = None

        # keys_to_check
        self.keys_to_check_task = [
            "title",
            "desc",
            "startDate",
            "dueDate",
            "projectId",
            "priority",
            "progress",
            "focusSummaries"
            "kind",
            "content"
        ]
        self.keys_to_check_project = [
            "name",
            "groupId"
        ]
        self.keys_to_check_project_folder = [
            "name"
        ]

        # modified data compared to prev. data
        # tasks
        self.new_tasks = None
        self.modified_tasks = None
        self.completed_tasks = None
        self.deleted_tasks = None
        # projects
        self.new_projects = None
        self.modified_projects = None
        self.archived_projects = None
        self.deleted_projects = None

    def read_data_in_ticktick(self, sync=False):
        """
        This method will sync and read the latest tasks in Ticktick
        
        :return: It will return none but update the content of the latest tasks, projects and project_folders
        """
        if sync:
            self.client.sync()
        current_data = self.client.state
        #       saving the state as latest
        self.inbox_id = self.client.inbox_id
        self.latest_tasks_in_ticktick = current_data["tasks"]
        projects = []
        closed_projects = []
        for project in current_data["projects"]:
            if not project["closed"]:
                projects.append(project)
            else:
                closed_projects.append(project)
        self.latest_project_in_ticktick = projects
        self.latest_project_folder_in_ticktick = current_data["project_folders"]
        self.closed_projects = closed_projects

        return {
            "tasks": self.latest_tasks_in_ticktick,
            "projects": self.latest_project_in_ticktick,
            "project_folders": self.latest_project_folder_in_ticktick
        }

    def saving_data_ticktick(self):
        """
        This method will read_latest_task and  save the latest tasks, project and
        project_folder to 'prev_data_ticktick.pkl'
        
        :return: return none, just save the file
        """
        self.read_data_in_ticktick()
        current_data = {
            "tasks": self.latest_tasks_in_ticktick,
            "projects": self.latest_project_in_ticktick,
            "project_folders": self.latest_project_folder_in_ticktick
        }

        with open('prev_data_ticktick.pkl', 'wb') as f:
            pickle.dump(current_data, f)

    def loading_prev_data_ticktick(self):
        """
        This method will load prev_data of ticktick from 'prev_data_ticktick.pkl' 
        and store it in "self.prev_data" variable.
        :return: load the data and store it in 'self.prev_data'
        """
        try:
            with open("prev_data_ticktick.pkl", "rb") as f:
                self.prev_data_ticktick = pickle.load(f)
        except:
            self.prev_data_ticktick = self.read_data_in_ticktick()

    def modified_task_check_ticktick(self):
        """
        Compare and check if any task is modified from the previous data of tasks.
        if any task is modified, then it will update the "self.modified_task"
        """
        modi_list = ticktick_helper.modification_check_with_prev_data(latest_data=self.latest_tasks_in_ticktick,
                                                                      prev_data=self.prev_data_ticktick["tasks"],
                                                                      keys_to_check=self.keys_to_check_task)
        if modi_list:
            self.modified_tasks = modi_list
        else:
            self.modified_tasks = None

    def completed_deleted_task_check(self):
        missing_list = ticktick_helper.missing_data_check_with_prev_state(prev_data=self.prev_data_ticktick["tasks"],
                                                                          latest_data=self.latest_tasks_in_ticktick)

        completed_list = []
        deleted_list = []
        last_one_day_comp_task = self.client.task.get_completed(datetime.today() - timedelta(days=1), datetime.today())
        if missing_list:
            for task in missing_list:
                match_found = False
                for comp_task in last_one_day_comp_task:
                    if task["id"] == comp_task["id"]:
                        match_found = True
                        completed_list.append(task)
                if not match_found:
                    deleted_list.append(task)

        if completed_list:
            self.completed_tasks = completed_list
        else:
            self.completed_tasks = None
        if deleted_list:
            self.deleted_tasks = deleted_list
        else:
            self.deleted_tasks = None

    def modified_project_check(self):
        modi_list = ticktick_helper.modification_check_with_prev_data(latest_data=self.latest_project_in_ticktick,
                                                                      prev_data=self.prev_data_ticktick["projects"],
                                                                      keys_to_check=self.keys_to_check_project)

        if modi_list:
            self.modified_projects = modi_list
        else:
            self.modified_projects = None

    def archived_deleted_project_check(self):
        missing_list = ticktick_helper.missing_data_check_with_prev_state(prev_data=self.prev_data_ticktick["projects"],
                                                                          latest_data=self.latest_project_in_ticktick)

        deleted_list = []
        archived_list = []

        if missing_list:
            for project in missing_list:
                match_found = False
                for project_all in self.client.state["projects"]:
                    if project["id"] == project_all["id"]:
                        match_found = True
                        archived_list.append(project)
                if not match_found:
                    deleted_list.append(project)

        if archived_list:
            self.archived_projects = archived_list
        else:
            self.archived_projects = None

        if deleted_list:
            self.deleted_projects = deleted_list
        else:
            self.deleted_projects = None

    def task_dic_builder(self, task_notion: dict, project_notion: list):
        """
        This method will create task dictionary for the task.
        :return: return none, just create the task
        """
        title = task_notion['Title']["title"][0]['plain_text']
        # Project details
        project_id = None
        if task_notion["Project"]['relation']:
            for project in project_notion:
                if project["id"] == task_notion["Project"]['relation'][0]['id']:
                    if project['properties']["Id_ticktick"]["rich_text"]:
                        project_id = project['properties']["Id_ticktick"]["rich_text"][0]["plain_text"]
        # desc
        desc = None
        if task_notion["Description"]['rich_text']:
            desc = task_notion["Description"]['rich_text'][0]['plain_text']
        # startDate
        start_date = None
        if task_notion["Start Date"]["date"]:
            start_date = datetime.fromisoformat(task_notion["Start Date"]["date"]["start"])
        # end date
        end_date = None
        if task_notion["End Date"]["date"]:
            end_date = datetime.fromisoformat(task_notion["End Date"]["date"]["start"])
            if not end_date > start_date:
                end_date = None
        priority = None
        if task_notion["Priority"]["select"]:
            priority = ticktick_helper.priority_convert_to_ticktick(task_notion["Priority"]["select"]["name"])
        task_dic = self.client.task.builder(title=title, projectId=project_id, desc=desc,
                                            startDate=start_date, dueDate=end_date, priority=priority)

        return task_dic

    def create_new_task_in_ticktick(self, task_notion: dict, project_notion: list):
        """
        This method will create new task in ticktick.
        :return: return created task
        """
        task_dic = self.task_dic_builder(task_notion, project_notion)
        created_task = self.client.task.create(task_dic)

        if created_task:
            return created_task
        else:
            return None

    def create_new_project_in_ticktick(self, project_notion: dict):
        """
        This method will create new project in ticktick.
        :return: return created project
        """
        project_name = project_notion['Project Name']["title"][0]['plain_text']

        created_project = self.client.project.create(name=project_name,
                                                     folder_id=ticktick_helper.area_id_finder(project_notion,
                                                                                              self.client))

        if created_project:
            return created_project
        else:
            return None

    def update_task_in_ticktick(self, task_notion: dict, project_notion: list):
        """
        This method will update task in ticktick.
        :return: return updated task
        """
        task_dic = self.task_dic_builder(task_notion, project_notion)
        updated_task = None
        if task_notion["Id_ticktick"]["rich_text"]:
            ticktick_id = task_notion["Id_ticktick"]["rich_text"][0]["plain_text"]
            task_ticktick = self.client.get_by_id(obj_id=ticktick_id, search="tasks")
            for keys, values in task_dic.items():
                task_ticktick[keys] = values
            updated_task = self.client.task.update(task_ticktick)

        return updated_task

    def update_project_in_ticktick(self, project_notion: dict):
        """
                This method will update project in ticktick.
                :return: return updated project, if project already exist in ticktick or else return none
                """

        # checking task id is available
        if project_notion["Id_ticktick"]["rich_text"]:
            project_id = project_notion["Id_ticktick"]["rich_text"][0]["plain_text"]

            project_ticktick = self.client.get_by_id(obj_id=project_id, search="projects")

            if project_ticktick:
                project_ticktick["name"] = project_notion['Project Name']["title"][0]['plain_text']
                area_id = ticktick_helper.area_id_finder(project_notion, self.client)
                if area_id is not None:
                    project_ticktick["groupId"] = area_id
                else:
                    project_ticktick["groupId"] = None
                updated_project = self.client.project.update(project_ticktick)

                return updated_project

        else:
            return None

    def complete_task_in_ticktick(self, task_notion: dict):
        """
        This method will complete task in ticktick.
        :return: return completed task
        """
        completed_task = None
        if task_notion["Id_ticktick"]["rich_text"]:
            ticktick_id = task_notion["Id_ticktick"]["rich_text"][0]["plain_text"]
            task_ticktick = self.client.get_by_id(obj_id=ticktick_id, search="tasks")
            completed_task = self.client.task.complete(task_ticktick)

        return completed_task

    def archive_project_in_ticktick(self, project_notion: dict):
        """
        This method will archive project in ticktick.
        :return: return archived project
        """
        archived_project = None
        if project_notion["Id_ticktick"]["rich_text"]:
            project_id = project_notion["Id_ticktick"]["rich_text"][0]["plain_text"]
            archived_project = self.client.project.archive(project_id)

        return archived_project

    def un_archive_project_in_ticktick(self, project_id):
        """
        This method will un archive project in ticktick.
        :return: return un archived project
        """
        un_archived_project = None
        project = self.client.get_by_id(obj_id=project_id, search="projects")
        if project:
            project["closed"] = False
            un_archived_project = self.client.project.update(project)

        return un_archived_project

    def delete_task_in_ticktick(self, task_notion: dict):
        """
        This method will delete task in ticktick.
        :return: return deleted task
        """
        deleted_task = None
        if task_notion["Id_ticktick"]["rich_text"]:
            ticktick_id = task_notion["Id_ticktick"]["rich_text"][0]["plain_text"]
            task_ticktick = self.client.get_by_id(obj_id=ticktick_id, search="tasks")
            deleted_task = self.client.task.delete(task_ticktick)

        return deleted_task

    def delete_project_in_ticktick(self, project_notion: dict):
        """
        This method will delete project in ticktick.
        :return: return deleted project
        """
        deleted_project = None
        if project_notion["Id_ticktick"]["rich_text"]:
            project_id = project_notion["Id_ticktick"]["rich_text"][0]["plain_text"]
            deleted_project = self.client.project.delete(project_id)

        return deleted_project
