import collections

from .constants import (
    DEFAULT_V3_FOLDER_FIELDS,
    DEFAULT_FOLDER_FIELDS,
    DEFAULT_SUBSET_FIELDS,
    DEFAULT_VERSION_FIELDS,
    DEFAULT_REPRESENTATION_FIELDS,
)
from .graphql import GraphQlQuery
from .graphql_queries import (
    project_graphql_query,
    projects_graphql_query,
    folders_graphql_query,
    tasks_graphql_query,
    folders_tasks_graphql_query,
    subsets_graphql_query,
    versions_graphql_query,
    representations_graphql_query,
    reprersentations_parents_qraphql_query,
)
from .server import get_server_api_connection
from .conversion_utils import (
    project_fields_v3_to_v4,
    convert_v4_project_to_v3,

    folder_fields_v3_to_v4,
    convert_v4_folder_to_v3,

    subset_fields_v3_to_v4,
    convert_v4_subset_to_v3,

    version_fields_v3_to_v4,
    convert_v4_version_to_v3,

    representation_fields_v3_to_v4,
    convert_v4_representation_to_v3,
)


def get_v4_projects(active=None, library=None, fields=None, con=None):
    """Get v4 projects.

    Args:
        active (Union[bool, None]): Filter active or inactive projects. Filter
            is disabled when 'None' is passed.
        library (Union[bool, None]): Filter library projects. Filter is
            disabled when 'None' is passed.
        fields (Union[Iterable(str), None]): fields to be queried for project.

    Returns:
        List[Dict[str, Any]]: List of queried projects.
    """

    if con is None:
        con = get_server_api_connection()
    if not fields:
        for project in con.get_rest_projects(active, library):
            yield project

    else:
        query = projects_graphql_query(fields)
        for parsed_data in query.continuous_query(con):
            for project in parsed_data["projects"]:
                yield project


def get_v4_project(project_name, fields=None, con=None):
    """Get v4 project.

    Args:
        project_name (str): Nameo project.
        fields (Union[Iterable(str), None]): fields to be queried for project.

    Returns:
        Union[Dict[str, Any], None]: Project entity data or None if project was
            not found.
    """

    if con is None:
        con = get_server_api_connection()

    if not fields:
        return con.get_rest_project(project_name)

    fields = set(fields)
    query = project_graphql_query(fields)
    query.set_variable_value("projectName", project_name)

    parsed_data = query.query(con)

    data = parsed_data["project"]
    if data is not None:
        data["name"] = project_name
    return data


def get_v4_project_anatomy_presets(add_default=True, con=None):
    if con is None:
        con = get_server_api_connection()
    result = con.get("anatomy/presets")
    return result.data


def get_v4_project_anatomy_preset(preset_name=None, con=None):
    if con is None:
        con = get_server_api_connection()

    if preset_name is None:
        preset_name = "_"
    result = con.get("anatomy/presets/{}".format(preset_name))
    return result.data


def get_v4_folders(
    project_name,
    folder_ids=None,
    folder_paths=None,
    folder_names=None,
    parent_ids=None,
    active=None,
    fields=None,
    con=None
):
    """Query folders from server.

    Todos:
        Folder name won't be unique identifier so we should add folder path
            filtering.

    Notes:
        Filter 'active' don't have direct filter in GraphQl.

    Args:
        folder_ids (Iterable[str]): Folder ids to filter.
        folder_paths (Iterable[str]): Folder paths used for filtering.
        folder_names (Iterable[str]): Folder names used for filtering.
        parent_ids (Iterable[str]): Ids of folder parents. Use 'None' if folder
            is direct child of project.
        active (Union[bool, None]): Filter active/inactive folders. Both are
            returned if is set to None.
        fields (Union[Iterable(str), None]): Fields to be queried for folder.
            All possible folder fields are returned if 'None' is passed.

    Returns:
        List[Dict[str, Any]]: Queried folder entities.
    """

    if not project_name:
        return []

    filters = {
        "projectName": project_name
    }
    if folder_ids is not None:
        folder_ids = set(folder_ids)
        if not folder_ids:
            return []
        filters["folderIds"] = list(folder_ids)

    if folder_paths is not None:
        folder_paths = set(folder_paths)
        if not folder_paths:
            return []
        filters["folderPaths"] = list(folder_paths)

    if folder_names is not None:
        folder_names = set(folder_names)
        if not folder_names:
            return []
        filters["folderNames"] = list(folder_names)

    if parent_ids is not None:
        parent_ids = set(parent_ids)
        if not parent_ids:
            return []
        if None in parent_ids:
            # Replace 'None' with '"root"' which is used during GraphQl query
            #   for parent ids filter for folders without folder parent
            parent_ids.remove(None)
            parent_ids.add("root")

        if project_name in parent_ids:
            # Replace project name with '"root"' which is used during GraphQl
            #   query for parent ids filter for folders without folder parent
            parent_ids.remove(project_name)
            parent_ids.add("root")

        filters["parentFolderIds"] = list(parent_ids)

    if not fields:
        fields = DEFAULT_FOLDER_FIELDS
    fields = set(fields)
    if active is not None:
        fields.add("active")

    query = folders_graphql_query(fields)
    for attr, filter_value in filters.items():
        query.set_variable_value(attr, filter_value)

    if con is None:
        con = get_server_api_connection()

    for parsed_data in query.continuous_query(con):
        for folder in parsed_data["project"]["folders"]:
            if active is None or active is folder["active"]:
                yield folder


def get_v4_tasks(
    project_name,
    task_ids=None,
    task_names=None,
    task_types=None,
    folder_ids=None,
    active=None,
    fields=None,
    con=None
):
    if not project_name:
        return []

    filters = {
        "projectName": project_name
    }

    if task_ids is not None:
        task_ids = set(task_ids)
        if not task_ids:
            return []
        filters["taskIds"] = list(task_ids)

    if task_names is not None:
        task_names = set(task_names)
        if not task_names:
            return []
        filters["taskNames"] = list(task_names)

    if task_types is not None:
        task_types = set(task_types)
        if not task_types:
            return []
        filters["taskTypes"] = list(task_types)

    if folder_ids is not None:
        folder_ids = set(folder_ids)
        if not folder_ids:
            return []
        filters["folderIds"] = list(folder_ids)

    if not fields:
        fields = DEFAULT_FOLDER_FIELDS
    fields = set(fields)
    if active is not None:
        fields.add("active")

    query = tasks_graphql_query(fields)
    for attr, filter_value in filters.items():
        query.set_variable_value(attr, filter_value)

    if con is None:
        con = get_server_api_connection()

    parsed_data = query.query(con)
    tasks = parsed_data["project"]["tasks"]

    if active is None:
        return tasks
    return [
        task
        for task in tasks
        if task["active"] is active
    ]


def get_v4_folders_tasks(
    project_name,
    folder_ids=None,
    folder_paths=None,
    folder_names=None,
    parent_ids=None,
    active=None,
    fields=None,
    con=None
):
    """Query folders with tasks from server.

    This is for v4 compatibility where tasks were stored on assets. This is
    inefficient way how folders and tasks are queried so it was added only
    as compatibility function.

    Todos:
        Folder name won't be unique identifier so we should add folder path
            filtering.

    Notes:
        Filter 'active' don't have direct filter in GraphQl.

    Args:
        folder_ids (Iterable[str]): Folder ids to filter.
        folder_paths (Iterable[str]): Folder paths used for filtering.
        folder_names (Iterable[str]): Folder names used for filtering.
        parent_ids (Iterable[str]): Ids of folder parents. Use 'None' if folder
            is direct child of project.
        active (Union[bool, None]): Filter active/inactive folders. Both are
            returned if is set to None.
        fields (Union[Iterable(str), None]): Fields to be queried for folder.
            All possible folder fields are returned if 'None' is passed.

    Returns:
        List[Dict[str, Any]]: Queried folder entities.
    """

    if not project_name:
        return []

    filters = {
        "projectName": project_name
    }
    if folder_ids is not None:
        folder_ids = set(folder_ids)
        if not folder_ids:
            return []
        filters["folderIds"] = list(folder_ids)

    if folder_paths is not None:
        folder_paths = set(folder_paths)
        if not folder_paths:
            return []
        filters["folderPaths"] = list(folder_paths)

    if folder_names is not None:
        folder_names = set(folder_names)
        if not folder_names:
            return []
        filters["folderNames"] = list(folder_names)

    if parent_ids is not None:
        parent_ids = set(parent_ids)
        if not parent_ids:
            return []
        if None in parent_ids:
            # Replace 'None' with '"root"' which is used during GraphQl query
            #   for parent ids filter for folders without folder parent
            parent_ids.remove(None)
            parent_ids.add("root")

        if project_name in parent_ids:
            # Replace project name with '"root"' which is used during GraphQl
            #   query for parent ids filter for folders without folder parent
            parent_ids.remove(project_name)
            parent_ids.add("root")

        filters["parentFolderIds"] = list(parent_ids)

    if not fields:
        fields = DEFAULT_V3_FOLDER_FIELDS
    fields = set(fields)
    if active is not None:
        fields.add("active")

    query = folders_tasks_graphql_query(fields)
    for attr, filter_value in filters.items():
        query.set_variable_value(attr, filter_value)

    if con is None:
        con = get_server_api_connection()
    parsed_data = query.query(con)
    folders = parsed_data["project"]["folders"]
    if active is None:
        return folders
    return [
        folder
        for folder in folders
        if folder["active"] is active
    ]


def get_v4_versions(
    project_name,
    version_ids=None,
    subset_ids=None,
    versions=None,
    hero=True,
    standard=True,
    latest=None,
    fields=None,
    con=None
):
    """Get version entities based on passed filters from server.

    Args:
        project_name (str): Name of project where to look for versions.
        version_ids (Iterable[str]): Version ids used for version filtering.
        subset_ids (Iterable[str]): Subset ids used for version filtering.
        versions (Iterable[int]): Versions we're interested in.
        hero (bool): Receive also hero versions when set to true.
        standard (bool): Receive versions which are not hero when set to true.
        latest (bool): Return only latest version of standard versions.
            This can be combined only with 'standard' attribute set to True.
        fields (Union[Iterable(str), None]): Fields to be queried for version.
            All possible folder fields are returned if 'None' is passed.

    Returns:
        List[Dict[str, Any]]: Queried version entities.
    """

    if not fields:
        fields = DEFAULT_VERSION_FIELDS
    fields = set(fields)

    filters = {
        "projectName": project_name
    }
    if version_ids is not None:
        version_ids = set(version_ids)
        if not version_ids:
            return []
        filters["versionIds"] = list(version_ids)

    if subset_ids is not None:
        subset_ids = set(subset_ids)
        if not subset_ids:
            return []
        filters["subsetIds"] = list(subset_ids)

    # TODO versions can't be used as fitler at this moment!
    if versions is not None:
        versions = set(versions)
        if not versions:
            return []
        filters["versions"] = list(versions)

    if not hero and not standard:
        return []

    # Add filters based on 'hero' and 'stadard'
    if hero and not standard:
        filters["heroOnly"] = True
    elif hero and latest:
        filters["heroOrLatestOnly"] = True
    elif latest:
        filters["latestOnly"] = True

    # Make sure fields have minimum required fields
    fields |= {"id", "version"}

    query = versions_graphql_query(fields)

    for attr, filter_value in filters.items():
        query.set_variable_value(attr, filter_value)

    if con is None:
        con = get_server_api_connection()
    parsed_data = query.query(con)

    return parsed_data.get("project", {}).get("versions", [])


def get_v4_representations(
    project_name,
    representation_ids=None,
    representation_names=None,
    version_ids=None,
    names_by_version_ids=None,
    active=None,
    fields=None,
    con=None
):
    """Get version entities based on passed filters from server.

    Todo:
        Add separated function for 'names_by_version_ids' filtering. Because
            can't be combined with others.

    Args:
        project_name (str): Name of project where to look for versions.
        representation_ids (Iterable[str]): Representaion ids used for
            representation filtering.
        representation_names (Iterable[str]): Representation names used for
            representation filtering.
        version_ids (Iterable[str]): Version ids used for
            representation filtering. Versions are parents of representations.
        names_by_version_ids (bool): Find representations by names and
            version ids. This filter discard all other filters.
        active (bool): Receive active/inactive representaions. All are returned
            when 'None' is passed.
        fields (Union[Iterable(str), None]): Fields to be queried for
            representation. All possible fields are returned if 'None' is
            passed.

    Returns:
        List[Dict[str, Any]]: Queried representation entities.
    """

    if not fields:
        fields = DEFAULT_REPRESENTATION_FIELDS
    fields = set(fields)

    if active is not None:
        fields.add("active")

    filters = {
        "projectName": project_name
    }

    if representation_ids is not None:
        representation_ids = set(representation_ids)
        if not representation_ids:
            return []
        filters["representationIds"] = list(representation_ids)

    version_ids_filter = None
    representaion_names_filter = None
    if names_by_version_ids is not None:
        version_ids_filter = set()
        representaion_names_filter = set()
        for version_id, names in names_by_version_ids.items():
            version_ids_filter.add(version_id)
            representaion_names_filter |= set(names)

        if not version_ids_filter or not representaion_names_filter:
            return []

    else:
        if representation_names is not None:
            representaion_names_filter = set(representation_names)
            if not representaion_names_filter:
                return []

        if version_ids is not None:
            version_ids_filter = set(version_ids)
            if not version_ids_filter:
                return []

    if version_ids_filter:
        filters["versionIds"] = list(version_ids_filter)

    if representaion_names_filter:
        filters["representationNames"] = list(representaion_names_filter)

    query = representations_graphql_query(fields)

    for attr, filter_value in filters.items():
        query.set_variable_value(attr, filter_value)

    if con is None:
        con = get_server_api_connection()
    parsed_data = query.query(con)

    representations = parsed_data.get("project", {}).get("representations", [])
    if active is None:
        representations = [
            repre
            for repre in representations
            if repre["active"] == active
        ]
    return representations


def get_projects(
    active=True, inactive=False, library=None, fields=None, con=None
):
    if not active and not inactive:
        return []

    if active and inactive:
        active = None
    elif active:
        active = True
    elif inactive:
        active = False

    if con is None:
        con = get_server_api_connection()

    fields = project_fields_v3_to_v4(fields)
    for project in get_v4_projects(active, library, fields, con=con):
        yield convert_v4_project_to_v3(project)


def get_project(
    project_name, active=True, inactive=False, fields=None, con=None
):
    # Skip if both are disabled
    fields = project_fields_v3_to_v4(fields)

    return convert_v4_project_to_v3(
        get_v4_project(project_name, fields=fields, con=con)
    )


def get_whole_project(*args, **kwargs):
    raise NotImplementedError("'get_whole_project' not implemented")


def _get_subsets(
    project_name,
    subset_ids=None,
    subset_names=None,
    folder_ids=None,
    names_by_folder_ids=None,
    archived=False,
    fields=None,
    con=None
):
    if not project_name:
        return []

    if subset_ids is not None:
        subset_ids = set(subset_ids)
        if not subset_ids:
            return []

    filter_subset_names = None
    if subset_names is not None:
        filter_subset_names = set(subset_names)
        if not filter_subset_names:
            return []

    filter_folder_ids = None
    if folder_ids is not None:
        filter_folder_ids = set(folder_ids)
        if not filter_folder_ids:
            return []

    # This will disable 'folder_ids' and 'subset_names' filters
    #   - maybe could be enhanced in future?
    if names_by_folder_ids is not None:
        filter_subset_names = set()
        filter_folder_ids = set()

        for folder_id, names in names_by_folder_ids.items():
            if folder_id and names:
                filter_folder_ids.add(folder_id)
                filter_subset_names |= set(names)

        if not filter_subset_names or not filter_folder_ids:
            return []

    # Convert fields and add minimum required fields
    fields = subset_fields_v3_to_v4(fields)
    if fields is not None:
        for key in (
            "id",
            "active"
        ):
            fields.add(key)

    if fields is None:
        fields = set(DEFAULT_SUBSET_FIELDS)

    # Add 'name' and 'folderId' if 'name_by_asset_ids' filter is entered
    if names_by_folder_ids:
        fields.add("name")
        fields.add("folderId")

    # Prepare filters for query
    filters = {
        "projectName": project_name
    }
    if filter_folder_ids:
        filters["folderIds"] = list(filter_folder_ids)

    if subset_ids:
        filters["subsetIds"] = list(subset_ids)

    if filter_subset_names:
        filters["subsetNames"] = list(filter_subset_names)

    query = subsets_graphql_query(fields)
    for attr, filter_value in filters.items():
        query.set_variable_value(attr, filter_value)

    if con is None:
        con = get_server_api_connection()
    parsed_data = query.query(con)

    subsets = parsed_data.get("project", {}).get("subsets", [])

    # Filter subsets by 'names_by_folder_ids'
    if names_by_folder_ids:
        subsets_by_folder_id = collections.defaultdict(list)
        for subset in subsets:
            folder_id = subset["folderId"]
            subsets_by_folder_id[folder_id].append(subset)

        filtered_subsets = []
        for folder_id, names in names_by_folder_ids.items():
            for folder_subset in subsets_by_folder_id[folder_id]:
                if folder_subset["name"] in names:
                    filtered_subsets.append(subset)
        subsets = filtered_subsets

    return [
        convert_v4_subset_to_v3(subset)
        for subset in subsets
    ]


def _get_versions(
    project_name,
    version_ids=None,
    subset_ids=None,
    versions=None,
    hero=True,
    standard=True,
    latest=None,
    fields=None,
    con=None
):
    if con is None:
        con = get_server_api_connection()

    fields = version_fields_v3_to_v4(fields)
    # Make sure 'subsetId' and 'version' are available when hero versions
    #   are queried
    if fields and hero:
        fields = set(fields)
        fields |= {"subsetId", "version"}

    queried_versions = get_v4_versions(
        project_name,
        version_ids,
        subset_ids,
        versions,
        hero,
        standard,
        latest,
        fields=fields,
        con=con
    )

    versions = []
    hero_versions = []
    for version in queried_versions:
        if version["version"] < 0:
            hero_versions.append(version)
        else:
            versions.append(convert_v4_version_to_v3(version))

    if hero_versions:
        subset_ids = set()
        versions_nums = set()
        for hero_version in hero_versions:
            versions_nums.add(abs(hero_version["version"]))
            subset_ids.add(hero_version["subsetId"])

        hero_eq_versions = get_v4_versions(
            project_name,
            subset_ids=subset_ids,
            versions=versions_nums,
            hero=False,
            fields=["id", "version", "subsetId"],
            con=con
        )
        hero_eq_by_subset_id = collections.defaultdict(list)
        for version in hero_eq_versions:
            hero_eq_by_subset_id[version["subsetId"]].append(version)

        for hero_version in hero_versions:
            abs_version = abs(hero_version["version"])
            subset_id = hero_version["subsetId"]
            version_id = None
            for version in hero_eq_by_subset_id.get(subset_id, []):
                if version["version"] == abs_version:
                    version_id = version["id"]
                    break
            conv_hero = convert_v4_version_to_v3(hero_version)
            conv_hero["version_id"] = version_id

    return versions


def get_asset_by_id(project_name, asset_id, fields=None, con=None):
    assets = get_assets(
        project_name, asset_ids=[asset_id], fields=fields, con=con
    )
    for asset in assets:
        return asset
    return None


def get_asset_by_name(
    project_name, asset_name, fields=None, con=None
):
    assets = get_assets(
        project_name, asset_names=[asset_name], fields=fields, con=con
    )
    for asset in assets:
        return asset
    return None


def get_assets(
    project_name,
    asset_ids=None,
    asset_names=None,
    parent_ids=None,
    archived=False,
    fields=None,
    con=None
):
    if not project_name:
        return []

    active = True
    if archived:
        active = False

    if con is None:
        con = get_server_api_connection()
    fields = folder_fields_v3_to_v4(fields)
    kwargs = dict(
        folder_ids=asset_ids,
        folder_names=asset_names,
        parent_ids=parent_ids,
        active=active,
        fields=fields,
        con=con
    )

    if "tasks" in fields:
        folders = get_v4_folders_tasks(project_name, **kwargs)
    else:
        folders = get_v4_folders(project_name, **kwargs)

    for folder in folders:
        yield convert_v4_folder_to_v3(folder, project_name)


def get_archived_assets(*args, **kwargs):
    raise NotImplementedError("'get_archived_assets' not implemented")


def get_asset_ids_with_subsets(project_name, asset_ids=None, con=None):
    if asset_ids is not None:
        asset_ids = set(asset_ids)
        if not asset_ids:
            return set()

    query = folders_graphql_query({"id"})
    query.set_variable_value("projectName", project_name)
    query.set_variable_value("folderHasSubsets", True)
    if asset_ids:
        query.set_variable_value("folderIds", list(asset_ids))

    if con is None:
        con = get_server_api_connection()

    parsed_data = query.query(con)
    folders = parsed_data["project"]["folders"]
    return {
        folder["id"]
        for folder in folders
    }


def get_subset_by_id(project_name, subset_id, fields=None, con=None):
    subsets = get_subsets(
        project_name, subset_ids=[subset_id], fields=fields, con=con
    )
    if subsets:
        return subsets[0]
    return None


def get_subset_by_name(
    project_name, subset_name, asset_id, fields=None, con=None
):
    subsets = get_subsets(
        project_name,
        subset_names=[subset_name],
        asset_ids=[asset_id],
        fields=fields,
        con=con
    )
    if subsets:
        return subsets[0]
    return None


def get_subsets(
    project_name,
    subset_ids=None,
    subset_names=None,
    asset_ids=None,
    names_by_asset_ids=None,
    archived=False,
    fields=None,
    con=None
):
    return _get_subsets(
        project_name,
        subset_ids,
        subset_names,
        asset_ids,
        names_by_asset_ids,
        archived,
        fields=fields,
        con=con
    )


def get_subset_families(project_name, subset_ids=None, con=None):
    if con is None:
        con = get_server_api_connection()
    if subset_ids is not None:
        subsets = get_subsets(
            project_name,
            subset_ids=subset_ids,
            fields=["data.family"],
            con=con
        )
        return {
            subset["data"]["family"]
            for subset in subsets
        }

    query = GraphQlQuery("SubsetFamilies")
    project_name_var = query.add_variable(
        "projectName", "String!", project_name
    )
    project_query = query.add_field("project")
    project_query.set_filter("name", project_name_var)
    project_query.add_field("subsetFamilies")

    parsed_data = query.query(con)

    return set(parsed_data.get("project", {}).get("subsetFamilies", []))


def get_version_by_id(project_name, version_id, fields=None, con=None):
    versions = get_versions(
        project_name,
        version_ids=[version_id],
        fields=fields,
        hero=True,
        con=con
    )
    if versions:
        return versions[0]
    return None


def get_version_by_name(
    project_name, version, subset_id, fields=None, con=None
):
    versions = get_versions(
        project_name,
        subset_ids=[subset_id],
        versions=[version],
        fields=fields,
        con=con
    )
    if versions:
        return versions[0]
    return None


def get_versions(
    project_name,
    version_ids=None,
    subset_ids=None,
    versions=None,
    hero=False,
    fields=None,
    con=None
):
    return _get_versions(
        project_name,
        version_ids,
        subset_ids,
        versions,
        hero=hero,
        standard=True,
        fields=fields,
        con=con
    )


def get_hero_version_by_id(project_name, version_id, fields=None, con=None):
    versions = get_hero_versions(
        project_name,
        version_ids=[version_id],
        fields=fields,
        con=con
    )
    if versions:
        return versions[0]
    return None


def get_hero_version_by_subset_id(
    project_name, subset_id, fields=None, con=None
):
    versions = get_hero_versions(
        project_name,
        subset_ids=[subset_id],
        fields=fields,
        con=con
    )
    if versions:
        return versions[0]
    return None


def get_hero_versions(
    project_name,
    subset_ids=None,
    version_ids=None,
    fields=None,
    con=None
):
    return _get_versions(
        project_name,
        version_ids=version_ids,
        subset_ids=subset_ids,
        hero=True,
        standard=False,
        fields=fields,
        con=con
    )


def get_last_versions(project_name, subset_ids, fields=None, con=None):
    versions = _get_versions(
        project_name,
        subset_ids=subset_ids,
        latest=True,
        fields=fields,
        con=con
    )
    return {
        version["parent"]: version
        for version in versions
    }


def get_last_version_by_subset_id(
    project_name, subset_id, fields=None, con=None
):
    versions = _get_versions(
        project_name,
        subset_ids=[subset_id],
        latest=True,
        fields=fields,
        con=con
    )
    if not versions:
        return versions[0]
    return None


def get_last_version_by_subset_name(
    project_name,
    subset_name,
    asset_id=None,
    asset_name=None,
    fields=None,
    con=None
):
    if not asset_id and not asset_name:
        return None

    if not asset_id:
        asset = get_asset_by_name(
            project_name, asset_name, fields=["_id"], con=con
        )
        if not asset:
            return None
        asset_id = asset["_id"]

    subset = get_subset_by_name(
        project_name, subset_name, asset_id, fields=["_id"], con=con
    )
    if not subset:
        return None
    return get_last_version_by_subset_id(
        project_name, subset["id"], fields=fields, con=con
    )


def get_output_link_versions(*args, **kwargs):
    raise NotImplementedError("'get_output_link_versions' not implemented")


def version_is_latest(project_name, version_id, con=None):
    query = GraphQlQuery("VersionIsLatest")
    project_name_var = query.add_variable(
        "projectName", "String!", project_name
    )
    version_id_var = query.add_variable(
        "versionId", "String!", version_id
    )
    project_query = query.add_field("project")
    project_query.set_filter("name", project_name_var)
    version_query = project_query.add_field("version")
    version_query.set_filter("id", version_id_var)
    subset_query = version_query.add_field("subset")
    latest_version_query = subset_query.add_field("latestVersion")
    latest_version_query.add_field("id")

    if con is None:
        con = get_server_api_connection()
    parsed_data = query.query(con)
    latest_version = (
        parsed_data["project"]["version"]["subset"]["latestVersion"]
    )
    return latest_version["id"] == version_id


def get_representation_by_id(
    project_name, representation_id, fields=None, con=None
):
    representations = get_representations(
        project_name,
        representation_ids=[representation_id],
        fields=fields,
        con=con
    )
    if representations:
        return representations[0]
    return None


def get_representation_by_name(
    project_name, representation_name, version_id, fields=None, con=None
):
    representations = get_representations(
        project_name,
        representation_names=[representation_name],
        version_ids=[version_id],
        fields=fields,
        con=con
    )
    if representations:
        return representations[0]
    return None


def get_representations(
    project_name,
    representation_ids=None,
    representation_names=None,
    version_ids=None,
    context_filters=None,
    names_by_version_ids=None,
    archived=False,
    standard=True,
    fields=None,
    con=None
):
    if context_filters is not None:
        # TODO should we add the support?
        # - there was ability to fitler using regex
        raise ValueError("OP v4 can't filter by representation context.")

    if not archived and not standard:
        return []

    if archived and not standard:
        active = False
    elif not archived and standard:
        active = True
    else:
        active = None

    fields = representation_fields_v3_to_v4(fields)
    representations = get_v4_representations(
        project_name,
        representation_ids,
        representation_names,
        version_ids,
        names_by_version_ids,
        active,
        fields=fields,
        con=con
    )
    return [
        convert_v4_representation_to_v3(repre)
        for repre in representations
    ]


def get_representation_parents(project_name, representation, con=None):
    if not representation:
        return None

    repre_id = representation["_id"]
    parents_by_repre_id = get_representations_parents(
        project_name, [representation]
    )
    return parents_by_repre_id[repre_id]


def get_representations_parents(project_name, representations, con=None):
    repre_ids = {
        repre["_id"]
        for repre in representations
    }
    parents = get_v4_representations_parents(project_name, repre_ids)
    folder_ids = set()
    for parents in parents.values():
        folder_ids.add(parents[2]["id"])

    tasks_by_folder_id = {}

    new_parents = {}
    for repre_id, parents in parents.items():
        version, subset, folder, project = parents
        folder_tasks = tasks_by_folder_id.get(folder["id"]) or {}
        folder["tasks"] = folder_tasks
        new_parents[repre_id] = (
            convert_v4_version_to_v3(version),
            convert_v4_subset_to_v3(subset),
            convert_v4_folder_to_v3(folder, project_name),
            project
        )
    return new_parents


def get_v4_representations_parents(project_name, representation_ids, con=None):
    if not representation_ids:
        return {}

    project = get_project(project_name)
    repre_ids = set(representation_ids)
    output = {
        repre_id: (None, None, None, None)
        for repre_id in representation_ids
    }

    query = reprersentations_parents_qraphql_query()
    query.set_variable_value("projectName", project_name)
    query.set_variable_value("representationIds", list(repre_ids))

    con = get_server_api_connection()

    parsed_data = query.query(con)
    for repre in parsed_data["project"]["representations"]:
        repre_id = repre["id"]
        version = repre.pop("version")
        subset = version.pop("subset")
        folder = subset.pop("folder")
        output[repre_id] = (version, subset, folder, project)

    return output


def get_archived_representations(*args, **kwargs):
    raise NotImplementedError("'get_archived_representations' not implemented")


def get_thumbnail(project_name, thumbnail_id, fields=None):
    # TODO thumbnails are handled in a different way
    return None


def get_thumbnails(project_name, thumbnail_ids, fields=None):
    # TODO thumbnails are handled in a different way
    return []


def get_thumbnail_id_from_source(project_name, src_type, src_id):
    """Receive thumbnail id from source entity.

    Args:
        project_name (str): Name of project where to look for queried entities.
        src_type (str): Type of source entity ('asset', 'version').
        src_id (Union[str, ObjectId]): Id of source entity.

    Returns:
        ObjectId: Thumbnail id assigned to entity.
        None: If Source entity does not have any thumbnail id assigned.
    """

    if not src_type or not src_id:
        return None

    if src_type == "subset":
        subset = get_subset_by_id(
            project_name, src_id, fields=["data.thumbnail_id"]
        ) or {}
        return subset.get("data", {}).get("thumbnail_id")

    if src_type == "subset":
        subset = get_asset_by_id(
            project_name, src_id, fields=["data.thumbnail_id"]
        ) or {}
        return subset.get("data", {}).get("thumbnail_id")

    return None


def get_workfile_info(
    project_name, asset_id, task_name, filename, fields=None
):
    # TODO workfile info not implemented in v4 yet
    return None