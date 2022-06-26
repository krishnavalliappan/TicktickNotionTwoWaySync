import json
import pickle
from datetime import datetime

import requests
import helpers.notion_helpers as notion_helpers


class NotionManager:
    def __init__(self, token, task_db_id, project_db_id):
        # Notion Authorization header
        self.headers = {
            'Authorization': "Bearer " + token,
            'Content-Type': 'application/json',
            'Notion-Version': '2022-02-22'
        }
        # database ID's
        self.project_db_id = project_db_id
        self.task_db_id = task_db_id
        # api request url
        self.base_db_url = "https://api.notion.com/v1/databases/"
        self.page_url = 'https://api.notion.com/v1/pages'

        # data in Notion
        self.all_tasks = None
        self.all_projects = None
        self.closed_projects = None
        self.latest_tasks_in_notion = None
        self.latest_projects_in_notion = None
        self.prev_data_notion = None

        # keys to check
        self.key_to_check_tasks = ['Title',
                                   "Project",
                                   "Description",
                                   "Description",
                                   "Start Date",
                                   "End Date",
                                   "Priority",
                                   "Completed"]
        self.keys_to_check_project = ["Project Name", "Area"]

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

    def query_database(self, db_id: str,
                       id_field_name=None, id_field_value=None,
                       bool_field_name=None, bool_field_value=None):
        """
        query a database by sending post request to notion database
        :param db_id: querying database id
        :param id_field_name: if you want to filter by ID, give its field name
        :param id_field_value: if you gave field name give filtering value
        :return: Return queried data
        """
        data = None  # initializing data with none
        if id_field_name is not None and id_field_value is not None:
            filter_ = {
                "filter": {
                    "property": id_field_name,
                    "rich_text": {
                        "contains": id_field_value
                    }
                }
            }
            data = json.dumps(filter_)
        if bool_field_name is not None and bool_field_value is not None:
            filter_ = {
                "filter": {
                    "property": bool_field_name,
                    "checkbox": {
                        "equals": bool_field_value
                    }
                }
            }
            data = json.dumps(filter_)
        response_data = requests.post(f"{self.base_db_url}{db_id}/query", headers=self.headers, data=data)
        return response_data.json()

    def reading_data_in_notion(self):
        """This method will save the latest and projects as latest_tasks and latest_project"""
        self.all_tasks = self.query_database(db_id=self.task_db_id)["results"]
        self.all_projects = self.query_database(db_id=self.project_db_id)["results"]
        self.closed_projects = self.query_database(self.project_db_id,
                                                             bool_field_name="Archive",
                                                             bool_field_value=True)["results"]
        self.latest_tasks_in_notion = self.query_database(self.task_db_id,
                                                          bool_field_name="Completed",
                                                          bool_field_value=False)["results"]
        self.latest_projects_in_notion = self.query_database(self.project_db_id,
                                                             bool_field_name="Archive",
                                                             bool_field_value=False)["results"]

        return {
            "tasks": self.latest_tasks_in_notion,
            "projects": self.latest_projects_in_notion
        }

    def saving_data_notion(self):
        """This method will save the latest read data to local file"""
        self.reading_data_in_notion()
        current_data = {
            "tasks": self.latest_tasks_in_notion,
            "projects": self.latest_projects_in_notion
        }
        with open('prev_data_notion.pkl', 'wb') as f:
            pickle.dump(current_data, f)

    def loading_prev_data_notion(self):
        try:
            with open("prev_data_notion.pkl", "rb") as f:
                self.prev_data_notion = pickle.load(f)
        except:
            self.prev_data_notion = self.reading_data_in_notion()

    def modified_task_check_notion(self):
        modi_list = notion_helpers.modification_check_with_prev_data(latest_data=self.latest_tasks_in_notion,
                                                                     prev_data=self.prev_data_notion["tasks"],
                                                                     keys_to_check=self.key_to_check_tasks)

        if modi_list:
            self.modified_tasks = modi_list
        else:
            self.modified_tasks = None

    def modified_project_check_notion(self):
        modi_list = notion_helpers.modification_check_with_prev_data(latest_data=self.latest_projects_in_notion,
                                                                     prev_data=self.prev_data_notion["projects"],
                                                                     keys_to_check=self.keys_to_check_project)

        if modi_list:
            self.modified_projects = modi_list
        else:
            self.modified_projects = None

    def completed_deleted_task_check(self):
        missing_list = notion_helpers.missing_data_check_with_prev_data(prev_data=self.prev_data_notion["tasks"],
                                                                        latest_data=self.latest_tasks_in_notion)
        completed_tasks = self.query_database(self.task_db_id,
                                              bool_field_name="Completed",
                                              bool_field_value=True)["results"]
        completed_list = []
        deleted_list = []
        if missing_list:
            for task in missing_list:
                match_found = False
                for comp_task in completed_tasks:
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

    def archived_deleted_project_check(self):
        missing_list = notion_helpers.missing_data_check_with_prev_data(prev_data=self.prev_data_notion["projects"],
                                                                        latest_data=self.latest_projects_in_notion)
        archived_projects = self.query_database(self.project_db_id,
                                                bool_field_name="Archive",
                                                bool_field_value=True)["results"]

        archived_list = []
        deleted_list = []
        if missing_list:
            for project in missing_list:
                match_found = False
                for arch_project in archived_projects:
                    if project["id"] == arch_project["id"]:
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

    def page_builder_task(self,
                          task,
                          update=False,
                          completed=False,
                          deleted=False):
        project_query = self.query_database(db_id=self.project_db_id,
                                            id_field_value=task["projectId"],
                                            id_field_name="Id_ticktick")[
            "results"] if "projectId" in task.keys() else None
        project_relation_id = None
        if project_query:
            project_relation_id = project_query[0]["id"]
        page_data = {
            "parent": {"database_id": self.task_db_id},
            "properties": {
                "Title": {
                    "title": [
                        {
                            "text": {
                                "content": task["title"] if "title" in task.keys() else "Untitled Task"
                            }
                        }
                    ]
                },
                "Description": {
                    "rich_text": [
                        {
                            "text": {
                                "content": task["desc"] if "desc" in task.keys() else " "
                            }
                        }
                    ]
                },
                "Start Date": {
                    "date": {
                        "start": str(notion_helpers.ticktickDate_to_isoFormat(
                            task["startDate"], task["timeZone"])) if "startDate" in task.keys() else None
                    }
                },
                "End Date": {
                    "date": {
                        "start": str(notion_helpers.ticktickDate_to_isoFormat(
                            task["dueDate"], task["timeZone"])) if "dueDate" in task.keys() else None
                    }
                },
                "Id_ticktick": {
                    "rich_text": [
                        {
                            "text": {
                                "content": task["id"]
                            }
                        }
                    ]
                },
                "Content": {
                    "rich_text": [
                        {
                            "text": {
                                "content": task["content"] if "content" in task.keys() else " "
                            }
                        }
                    ]
                },
                "ProjectId_ticktick": {
                    "rich_text": [
                        {
                            "text": {
                                "content": task["projectId"]
                            }
                        }
                    ]
                },
                "Priority": {
                    "select": {
                        "name": notion_helpers.priority_convert(task["priority"])
                    }
                },
                "Progress_ticktick": {
                    "number": int(task["progress"]) if "progress" in task.keys() else 0
                },
                "ModifiedTime_ticktick": {
                    "date": {
                        "start": str(notion_helpers.ticktickDate_to_isoFormat(
                            task["modifiedTime"], task["timeZone"])) if "modifiedTime" in task.keys() else None
                    }
                },
                "CreatedTime_ticktick": {
                    "date": {
                        "start": str(notion_helpers.ticktickDate_to_isoFormat(
                            task["createdTime"], task["timeZone"])) if "createdTime" in task.keys() else None
                    }
                },
                "Pomo Count": {
                    "number": notion_helpers.focus_summary_convert(
                        task["focusSummaries"], "pomo") if "focusSummaries" in task.keys() else 0
                },
                "Focus Time in Min.": {
                    "number": notion_helpers.focus_summary_convert(
                        task["focusSummaries"], "focus_time") if "focusSummaries" in task.keys() else 0
                },
                "Project": {
                    "relation": [
                        {
                            "id": project_relation_id
                        }
                    ]
                },
                "Kind": {
                    "select": {
                        "name": notion_helpers.kind_converter(task["kind"]) if "kind" in task.keys() else "Task"
                    }
                },
                "Recurring Task": {
                    "checkbox": True if notion_helpers.recurring_task_check(task=task) else False
                },
                "Completed": {
                    "checkbox": completed if completed else False
                }
            },
            "archived": deleted if deleted else False,
        }

        date_keys = ["Start Date", "End Date", "ModifiedTime_ticktick", "CreatedTime_ticktick"]
        for key in date_keys:
            if page_data["properties"][key]["date"]["start"] is None:
                page_data["properties"].pop(key)
        if not "projectId" in task.keys():
            page_data["properties"].pop("End Date")
        if "startDate" in task.keys():
            if task["startDate"] == task["dueDate"]:
                page_data["properties"].pop("End Date")

        if update:
            page_data.pop("parent")

        data = json.dumps(page_data)

        return data

    def page_builder_project(self, project, ticktick_client, update=False, archived=False, deleted=False):

        if ticktick_client is not None:
            if notion_helpers.project_area_check(project):
                area = ticktick_client.get_by_id(project["groupId"], search='project_folders')["name"]
            else:
                area = "No Area"
        else:
            area = None

        if project is None:
            page_data = {
                "parent": {"database_id": self.project_db_id},
                "properties": {"Archive": {
                    "checkbox": archived if archived else False
                }}
            }
        else:
            page_data = {
                "parent": {"database_id": self.project_db_id},
                "properties": {
                    "Project Name": {
                        "title": [
                            {
                                "text": {
                                    "content": project["name"] if project["name"].replace(" ", "").isalnum() else "".join(
                                        [string for string in project["name"].replace(" ", "*") if
                                         string.isalnum() or string in ["*", "&", "'", "-"]]).replace("*", " ")
                                }
                            }
                        ]
                    },
                    "Id_ticktick": {
                        "rich_text": [
                            {
                                "text": {
                                    "content": project["id"]
                                }
                            }
                        ]
                    },
                    "ModifiedTime_Ticktick": {
                        "date": {
                            "start": str(notion_helpers.ticktickDate_to_isoFormat(
                                project["modifiedTime"])) if "modifiedTime" in project.keys() else None
                        }
                    },
                    "Area": {
                        "select": {
                            "name": area
                        }
                    },
                    "Archive": {
                        "checkbox": archived if archived else False
                    }
                },
                "archived": deleted if deleted else False,
            }

            if page_data["properties"]["ModifiedTime_Ticktick"]["date"]["start"] is None:
                page_data["properties"].pop("ModifiedTime_Ticktick")

            if not project["name"][0].isalnum():
                page_data["icon"] = {
                    "emoji": project["name"][0]
                }

            if ticktick_client is None:
                page_data["properties"].pop("Area")

        if update:
            page_data.pop("parent")

        data = json.dumps(page_data)

        return data

    def create_new_task_page_in_notion(self, task):
        response = requests.post(self.page_url, headers=self.headers,
                                 data=self.page_builder_task(task=task))
        if response.status_code == 200:
            print("Task created in Notion")
        else:
            print("Error in creating task - Notion")
            print(response.json())

    def create_new_project_page_in_notion(self, project, ticktick_client):
        response = requests.post(self.page_url, headers=self.headers,
                                 data=self.page_builder_project(project=project, ticktick_client=ticktick_client))
        if response.status_code == 200:
            print("Project created in Notion")
        else:
            print("Error in creating project - Notion")
            print(response.json())

    def create_inbox_project_page_in_notion(self, inbox_id):
        page_data = {
            "parent": {"database_id": self.project_db_id},
            "icon": {
                "emoji": "📥"
            },
            "properties": {
                "Project Name": {
                    "title": [
                        {
                            "text": {
                                "content": "Inbox"
                            }
                        }
                    ]
                },
                "Id_ticktick": {
                    "rich_text": [
                        {
                            "text": {
                                "content": inbox_id
                            }
                        }
                    ]
                },
                "ModifiedTime_Ticktick": {
                    "date": {
                        "start": str(datetime.now())
                    }
                },
                "Archive": {
                    "checkbox": False
                }
            },
            "archived": False,
        }
        data = json.dumps(page_data)

        response = requests.post(self.page_url, headers=self.headers, data=data)
        if response.status_code == 200:
            print("Inbox created in Notion")
        else:
            print("Error in creating Inbox - Notion")
            print(response.json())

    def update_task_request_data(self, task, completed=False, deleted=False, notion_id=None):
        data = self.page_builder_task(task=task, update=True, completed=completed, deleted=deleted)

        if notion_id is None:
            query_result = self.query_database(db_id=self.task_db_id,
                                               id_field_name="Id_ticktick",
                                               id_field_value=task["id"])["results"]
            if query_result:
                notion_id = query_result[0]["id"]

        response = requests.request("PATCH", f"{self.page_url}/{notion_id}", headers=self.headers,
                                    data=data)
        return response

    def update_project_request_data(self, project, ticktick_client=None, archived=False, deleted=False, notion_id=None):
        data = self.page_builder_project(project=project,
                                         ticktick_client=ticktick_client,
                                         update=True, archived=archived, deleted=deleted)

        if notion_id is None:
            query_result = self.query_database(db_id=self.project_db_id,
                                               id_field_name="Id_ticktick",
                                               id_field_value=project["id"])["results"]
            if query_result:
                notion_id = query_result[0]["id"]

        response = requests.request("PATCH", f"{self.page_url}/{notion_id}", headers=self.headers,
                                    data=data)
        return response

    def update_task_page_in_notion(self, task):
        response = self.update_task_request_data(task=task)
        if response.status_code == 200:
            print("Task updated in Notion")
        else:
            print("Error in updating task - Notion")
            print(response.json())

    def update_project_page_in_notion(self, project, ticktick_client, notion_id=None):
        response = self.update_project_request_data(project=project, ticktick_client=ticktick_client,
                                                    notion_id=notion_id)
        if response.status_code == 200:
            print("Project updated in Notion")
        else:
            print("Error in updating project - Notion")
            print(response.json())

    def complete_task_page_in_notion(self, task):
        response = self.update_task_request_data(task=task, completed=True)
        if response.status_code == 200:
            print("Task completed in Notion")
        else:
            print("Error in completing task - Notion")
            print(response.json())

    def archive_project_page_in_notion(self, project):
        response = self.update_project_request_data(project=project, archived=True)
        if response.status_code == 200:
            print("Project Archived in Notion")
        else:
            print("Error in archiving project - Notion")
            print(response.json())

    def un_archive_project_page_in_notion(self, notion_id):
        response = self.update_project_request_data(project=None, archived=False, notion_id=notion_id)
        if response.status_code == 200:
            print("Project Un-archived in Notion")
        else:
            print("Error in Un-archived project - Notion")
            print(response.json())

    def delete_task_page_in_notion(self, task):
        response = self.update_task_request_data(task=task, deleted=True)
        if response.status_code == 200:
            print("Task deleted in Notion")
        else:
            print("Error in deleting task - Notion")
            print(response.json())

    def deleting_project_page_in_notion(self, project):
        response = self.update_project_request_data(project=project, deleted=True)
        if response.status_code == 200:
            print("Project deleted in Notion")
        else:
            print("Error in deleting project - Notion")
            print(response.json())
