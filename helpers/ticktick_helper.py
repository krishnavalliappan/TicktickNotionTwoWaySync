def modification_check_with_prev_data(latest_data: list,
                                      prev_data: list,
                                      keys_to_check: list):
    modi_list = []
    for i in range(len(latest_data)):
        unchanged = True
        for j in range(len(prev_data)):
            if latest_data[i]["id"] == prev_data[j]["id"]:
                for key in keys_to_check:
                    if key in latest_data[i].keys() and key in prev_data[j].keys():
                        if latest_data[i][key] != prev_data[j][key]:
                            unchanged = False
        if not unchanged:
            modi_list.append(latest_data[i])
    return modi_list


def missing_data_check_with_prev_state(prev_data: list,
                                       latest_data: list):
    missing_list = []
    for i in range(len(prev_data)):
        match_found = False
        for j in range(len(latest_data)):
            if prev_data[i]["id"] == latest_data[j]["id"]:
                match_found = True
        if not match_found:
            missing_list.append(prev_data[i])
    return missing_list


def priority_convert_to_ticktick(priority):
    if priority == "Low":
        return 1
    elif priority == "Medium":
        return 3
    elif priority == "High 🔥":
        return 5
    else:
        return 0


def area_id_finder(project_notion, client):
    if project_notion['Area']["select"]:
        area = project_notion['Area']["select"]["name"]
    else:
        area = None

    if area is not None:
        area_ticktick = client.get_by_fields(name=area, search='project_folders')

        if not area_ticktick and not area == "No Area":
            created_folder = client.project.create_folder(area)
            area_ticktick = client.get_by_id(obj_id=created_folder["id"], search='project_folders')

        if area != "No Area":
            if type(area_ticktick) == list:
                area_id = area_ticktick[0]["id"]
            else:
                area_id = area_ticktick["id"]
        else:
            area_id = None
    else:
        area_id = None

    return area_id
