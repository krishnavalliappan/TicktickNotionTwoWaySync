import secrets

from managers.ticktick_manager import TicktickManager
from managers.notion_manager import NotionManager


# from action.ticktick_action import TicktickAction
def check_ticktick_with_notion_using_ID(ticktick_list, notion_list):
    """This function will compare main list with comparer list and return a list which does not have a match """
    if notion_list:
        updated_list = []
        for ticktick in ticktick_list:
            match_found = False
            for notion in notion_list:
                if notion["properties"]["Id_ticktick"]["rich_text"]:
                    condition = notion["properties"]["Id_ticktick"]["rich_text"][0]["plain_text"] == ticktick["id"]
                    if condition:
                        match_found = True
            if not match_found:
                updated_list.append(ticktick)
        return updated_list
    else:
        return ticktick_list


class TicktickNotionConnector:
    def __init__(self):
        self.ticktick = TicktickManager(secrets.client_id,
                                        secrets.client_secret,
                                        secrets.uri,
                                        secrets.username,
                                        secrets.password)

        self.notion = NotionManager(secrets.secret_token,
                                    secrets.task_database_id,
                                    secrets.project_database_id)

    def ticktick_loop_init(self):
        self.ticktick.read_data_in_ticktick(sync=True)
        self.ticktick.loading_prev_data_ticktick()

    def notion_loop_init(self):
        self.notion.reading_data_in_notion()
        self.notion.loading_prev_data_notion()

    def ticktick_check(self):
        #     new task added check
        self.new_task_created_in_ticktick_check()
        # modified task check
        self.ticktick.modified_task_check_ticktick()
        # completed task check and deleted task check
        self.ticktick.completed_deleted_task_check()

        # new project added check
        self.new_project_created_in_ticktick_check()
        # modifies project check
        self.ticktick.modified_project_check()
        # deleted and archived projects check
        self.ticktick.archived_deleted_project_check()

    def notion_check(self):
        # new task added check
        self.new_task_created_in_notion_check()
        # modified task check
        self.notion.modified_task_check_notion()
        # completed task check and deleted task check
        self.notion.completed_deleted_task_check()

        #     new project added check
        self.new_project_created_in_notion_check()
        # modified project check
        self.notion.modified_project_check_notion()
        # archived and deleted project check
        self.notion.archived_deleted_project_check()

    def un_archive_check_and_action(self):
        self.un_archive_project_ticktick_check_action()
        self.un_archive_project_notion_check_action()

    def ticktick_action_project(self):
        # create a new project if new project added in notion
        self.create_new_project_in_ticktick()
        # update the project if project is updated in notion
        self.update_project_in_ticktick()
        # archive the project if project is archived in notion
        self.archive_project_in_ticktick()
        # delete the project if project is deleted in notion
        self.delete_project_in_ticktick()

    def ticktick_action_task(self):
        # create a new task in ticktick if new task is added in notion.
        self.create_new_task_in_ticktick()
        # update a task if modified in notion
        self.update_task_in_ticktick()
        # complete a task if completed in notion
        self.complete_task_in_ticktick()
        # delete a task in notion if deleted in notion
        self.delete_task_in_ticktick()

    def notion_action_project(self):
        # create a new project
        self.inbox_check_and_create_in_notion()
        self.create_new_project_in_notion()
        # update project
        self.update_project_in_notion()
        # archiving a project
        self.archive_project_in_notion()
        # deleting
        self.delete_project_in_notion()

    def notion_action_task(self):
        # create a new task
        self.create_new_task_in_notion()

        # update a task if modified in ticktick
        self.update_task_in_notion()

        # complete a task if completed in ticktick
        self.complete_task_in_notion()

        # delete a task in notion if deleted in ticktick
        self.delete_task_in_notion()

    def ticktick_loop_end(self):
        self.ticktick.saving_data_ticktick()

    def notion_loop_end(self):
        self.notion.saving_data_notion()

    def new_task_created_in_ticktick_check(self):
        new_tasks = check_ticktick_with_notion_using_ID(
            ticktick_list=self.ticktick.latest_tasks_in_ticktick,
            notion_list=self.notion.all_tasks)
        if self.notion.deleted_tasks:
            new_tasks_with_out_deleted_tasks = []
            for new_task in new_tasks:
                for task in self.notion.deleted_tasks:
                    if task["properties"]["Id_ticktick"]["rich_text"]:
                        if new_task["id"] == task["properties"]["Id_ticktick"]["rich_text"][0]["plain_text"]:
                            pass
                        else:
                            new_tasks_with_out_deleted_tasks.append(new_task)
            new_tasks = new_tasks_with_out_deleted_tasks

        if new_tasks:
            self.ticktick.new_tasks = new_tasks
        else:
            self.ticktick.new_tasks = None

    def new_project_created_in_ticktick_check(self):
        new_projects = check_ticktick_with_notion_using_ID(ticktick_list=self.ticktick.latest_project_in_ticktick,
                                                           notion_list=self.notion.all_projects)

        if self.notion.deleted_projects:
            new_project_with_out_deleted_projects = []
            for new_project in new_projects:
                for project in self.notion.deleted_projects:
                    if project["properties"]["Id_ticktick"]["rich_text"]:
                        if new_project["id"] == project["properties"]["Id_ticktick"]["rich_text"][0]["plain_text"]:
                            pass
                        else:
                            new_project_with_out_deleted_projects.append(new_project)
            new_projects = new_project_with_out_deleted_projects

        if new_projects:
            self.ticktick.new_projects = new_projects
        else:
            self.ticktick.new_projects = None

    def new_task_created_in_notion_check(self):
        new_tasks = []
        for task in self.notion.latest_tasks_in_notion:
            if not task["properties"]["Id_ticktick"]["rich_text"]:
                new_tasks.append(task)

        if new_tasks:
            self.notion.new_tasks = new_tasks
        else:
            self.notion.new_tasks = None

    def new_project_created_in_notion_check(self):
        new_projects = []
        for project in self.notion.latest_projects_in_notion:
            if not project["properties"]["Id_ticktick"]["rich_text"]:
                new_projects.append(project)

        if new_projects:
            self.notion.new_projects = new_projects
        else:
            self.notion.new_projects = None

    def un_archive_project_ticktick_check_action(self):
        for closed_project_ticktick in self.ticktick.closed_projects:
            match_found = False
            for closed_project_notion in self.notion.closed_projects:
                if closed_project_notion["properties"]["Id_ticktick"]["rich_text"]:
                    if closed_project_ticktick["id"] == closed_project_notion["properties"]["Id_ticktick"]["rich_text"][0]["plain_text"]:
                        match_found = True
            if not match_found:
                for projects in self.notion.latest_projects_in_notion:
                    if closed_project_ticktick["id"] == projects["properties"]["Id_ticktick"]["rich_text"][0]["plain_text"]:
                        un_archived_project = self.ticktick.un_archive_project_in_ticktick(closed_project_ticktick["id"])

                        if un_archived_project:
                            print("Project successfully un-archived in Ticktick")

                        else:
                            print("Error in un-archiving project - Ticktick")

    def un_archive_project_notion_check_action(self):
        for closed_project_notion in self.notion.closed_projects:
            match_found = False
            for closed_project_ticktick in self.ticktick.closed_projects:
                if closed_project_notion["properties"]["Id_ticktick"]["rich_text"]:
                    if closed_project_ticktick["id"] == closed_project_notion["properties"]["Id_ticktick"]["rich_text"][0]["plain_text"]:
                        match_found = True
            if not match_found:
                self.notion.un_archive_project_page_in_notion(closed_project_notion["id"])

    def create_new_task_in_notion(self):
        if self.ticktick.new_tasks is not None:
            for task in self.ticktick.new_tasks:
                self.notion.create_new_task_page_in_notion(task)

    def inbox_check_and_create_in_notion(self):
        #     check inbox id is in the queried result?
        is_inbox_created = self.notion.query_database(self.notion.project_db_id,
                                                      id_field_name="Id_ticktick",
                                                      id_field_value=self.ticktick.inbox_id)["results"]
        if not is_inbox_created:
            self.notion.create_inbox_project_page_in_notion(self.ticktick.inbox_id)

    def create_new_project_in_notion(self):
        if self.ticktick.new_projects is not None:
            for project in self.ticktick.new_projects:
                is_project_archived = self.notion.query_database(self.notion.project_db_id,
                                                                 id_field_name="Id_ticktick",
                                                                 id_field_value=project["id"],
                                                                 bool_field_name="Archive",
                                                                 bool_field_value=True)["results"]
                if is_project_archived:
                    self.notion.update_project_page_in_notion(project=project, ticktick_client=self.ticktick.client)
                else:
                    self.notion.create_new_project_page_in_notion(project, self.ticktick.client)

    def update_task_in_notion(self):
        if self.ticktick.modified_tasks is not None:
            for task in self.ticktick.modified_tasks:
                self.notion.update_task_page_in_notion(task=task)

    def update_project_in_notion(self):
        if self.ticktick.modified_projects is not None:
            for project in self.ticktick.modified_projects:
                self.notion.update_project_page_in_notion(project=project, ticktick_client=self.ticktick.client)

    def complete_task_in_notion(self):
        if self.ticktick.completed_tasks is not None:
            for task in self.ticktick.completed_tasks:
                self.notion.complete_task_page_in_notion(task=task)

    def archive_project_in_notion(self):
        if self.ticktick.archived_projects is not None:
            for project in self.ticktick.archived_projects:
                self.notion.archive_project_page_in_notion(project=project)

    def delete_task_in_notion(self):
        if self.ticktick.deleted_tasks is not None:
            for task in self.ticktick.deleted_tasks:
                self.notion.delete_task_page_in_notion(task=task)

    def delete_project_in_notion(self):
        if self.ticktick.deleted_projects:
            for project in self.ticktick.deleted_projects:
                self.notion.deleting_project_page_in_notion(project=project)

    #     Ticktick
    # create a task in ticktick if a new_notion task created
    def create_new_project_in_ticktick(self):
        if self.notion.new_projects is not None:
            for project in self.notion.new_projects:
                # checking if project is empty or not by checking title of the project
                if project["properties"]['Project Name']["title"]:
                    created_project = self.ticktick.create_new_project_in_ticktick(project["properties"])

                    if created_project:
                        response = self.notion.update_project_request_data(
                            project=self.ticktick.client.get_by_id(obj_id=created_project["id"], search="projects"),
                            ticktick_client=self.ticktick.client, notion_id=project["id"])

                        if response.status_code == 200:
                            print("Project successfully created in Ticktick")

                        else:
                            print("Error in creating project - Ticktick")
                            print(response.json())

    def create_new_task_in_ticktick(self):
        if self.notion.new_tasks:
            for task in self.notion.new_tasks:
                if task["properties"]['Title']["title"]:
                    created_task = self.ticktick.create_new_task_in_ticktick(task["properties"],
                                                                             self.notion.latest_projects_in_notion)

                    if created_task:
                        response = self.notion.update_task_request_data(
                            task=self.ticktick.client.get_by_id(obj_id=created_task["id"], search="tasks")
                            , notion_id=task["id"])

                        if response.status_code == 200:
                            print("Task successfully created in Ticktick")

                        else:
                            print("Error in creating Task - Ticktick")
                            print(response.json())

    def update_project_in_ticktick(self):
        if self.notion.modified_projects is not None:
            for project in self.notion.modified_projects:
                # checking if project is empty or not by checking title of the project
                if project["properties"]["Id_ticktick"]["rich_text"]:
                    updated_project = self.ticktick.update_project_in_ticktick(project["properties"])

                    if updated_project:
                        response = self.notion.update_project_request_data(
                            project=self.ticktick.client.get_by_id(obj_id=updated_project["id"], search="projects"),
                            ticktick_client=self.ticktick.client, notion_id=project["id"])

                        if response.status_code == 200:
                            print("Project successfully updated in Ticktick")

                        else:
                            print("Error in creating project - Ticktick")
                            print(response.json())

    def update_task_in_ticktick(self):
        if self.notion.modified_tasks:
            for task in self.notion.modified_tasks:
                if task["properties"]["Id_ticktick"]["rich_text"]:
                    updated_task = self.ticktick.update_task_in_ticktick(task["properties"],
                                                                         self.notion.latest_projects_in_notion)
                    if updated_task:
                        response = self.notion.update_task_request_data(
                            task=self.ticktick.client.get_by_id(obj_id=updated_task["id"], search="tasks"),
                            notion_id=task["id"])

                        if response.status_code == 200:
                            print("Task successfully updated in Ticktick")
                        else:
                            print("Error in updating Task - Ticktick")
                            print(response.json())

    def complete_task_in_ticktick(self):
        if self.notion.completed_tasks:
            for task in self.notion.completed_tasks:
                if task["properties"]["Id_ticktick"]["rich_text"]:
                    completed_task = self.ticktick.complete_task_in_ticktick(task["properties"])
                    if completed_task:
                        print("Task successfully completed in Ticktick")
                    else:
                        print("Error in completing Task - Ticktick")

    def archive_project_in_ticktick(self):
        if self.notion.archived_projects:
            for project in self.notion.archived_projects:
                if project["properties"]["Id_ticktick"]["rich_text"]:
                    archived_project = self.ticktick.archive_project_in_ticktick(project["properties"])
                    if archived_project:
                        print("Project successfully archived in Ticktick")
                    else:
                        print("Error in archiving project - Ticktick")

    def delete_task_in_ticktick(self):
        if self.notion.deleted_tasks:
            for task in self.notion.deleted_tasks:
                if task["properties"]["Id_ticktick"]["rich_text"]:
                    deleted_task = self.ticktick.delete_task_in_ticktick(task["properties"])
                    if deleted_task:
                        print("Task successfully deleted in Ticktick")
                    else:
                        print("Error in deleting Task - Ticktick")

    def delete_project_in_ticktick(self):
        if self.notion.deleted_projects:
            for project in self.notion.deleted_projects:
                if project["properties"]["Id_ticktick"]["rich_text"]:
                    deleted_project = self.ticktick.delete_project_in_ticktick(project["properties"])
                    if deleted_project:
                        print("Project successfully deleted in Ticktick")
                    else:
                        print("Error in deleting Project - Ticktick")
