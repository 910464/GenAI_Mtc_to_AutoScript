import glob
import os
import re
from collections import defaultdict
from typing import Union, Set, List, Dict

import tree_sitter
from tree_sitter import Language, Parser, Node

from Src.CoreLogicLayer.IntelligentAutomation.FunctionalTestAutomation.SharedResources.Utils.Parsers.parseMethodToCsv import \
    ParseMethodToCsv
from Src.DAOLayer.ChromaDBConnector import ChromaDBConnector

# Load the Python grammar
Language.build_library(
  'build/my-languages.so',
  [
    '../Utilities/tree-sitter-java'
  ]
)
JAVA_LANGUAGE = Language('build/my-languages.so', 'java')

# Initialize the parser
parser = Parser()
parser.set_language(JAVA_LANGUAGE)

reusable_class_used = {}

# Define a function to traverse the syntax tree
# def extract_class_names(node, class_names):
#     if node.type == 'import_declaration':
#         class_name = ''
#         for child in node.children:
#             if child.type == 'scoped_identifier':
#                 class_name = child.text.decode("utf-8").split(".")[-1]
#         if class_name:
#             class_names.add(class_name)
#     elif node.type == 'class_declaration':
#         for child in node.children:
#             if child.type == 'superclass':
#                 class_names.add(child.text.decode("utf-8").split(' ')[-1])
#     return class_names

# Define a function to traverse the syntax tree
def extract_class_names(root_node: Node, class_names: set) -> set:
    """
    Sometimes imports might have wild cards(*), To handle this
    Looking for Field variables, Param variables and Local variables
        to fetch class instances more precisely
    """
    for node in root_node.children:
        if node.type == 'import_declaration':
            class_name = ''
            for child in node.children:
                if child.type == 'scoped_identifier':
                    class_name = child.text.decode("utf-8").split(".")[-1]
            if class_name:
                class_names.add(class_name)
        elif node.type == 'class_declaration':
            for child in node.children:
                if child.type == 'superclass':
                    class_names.add(child.text.decode("utf-8").split(' ')[-1])
        elif node.type == 'variable_declarator':
            for child in node.children:
                if child.type == 'identifier':
                    class_names.add(child.text.decode("utf-8").split(' ')[-1])

        extract_class_names(node, class_names)

    return class_names


def required_imports(framework_code_folder_path, existing_scripts_folder_path, exclude_files, include_folders, extension: str):
    for root, dirs, files in os.walk(existing_scripts_folder_path):
        for dir_name in dirs:
            if dir_name in include_folders:
                all_files = glob.glob(os.path.join(root, dir_name, f'**/*.{extension}'), recursive=True)
                for file in all_files:
                    if not file.endswith(tuple(exclude_files)):
                        class_names = set()
                        # dir_name = os.path.basename(root)  # Get the directory name from 'root'
                        script_file = os.path.join(root, file).replace('\\', '/')
                        # Load your Python source code with global default encoding
                        with open(script_file, 'r') as file:
                            source_code = file.read()
                        # Parse the code
                        tree = parser.parse(bytes(source_code, "utf8"))
                        reusable_class_used[dir_name]: Set[str] = extract_class_names(tree.root_node, class_names)
                        break

        # for file in files:
        #     if not file.endswith(".zip"):
        #         # Extract imported and extended class names
        #         class_names = set()
        #         dir_name = os.path.basename(root)  # Get the directory name from 'root'
        #         script_file = os.path.join(root, file).replace('\\', '/')
        #         # Load your Python source code
        #         with open(script_file, 'r') as file:
        #             source_code = file.read()
        #         # Parse the code
        #         tree = parser.parse(bytes(source_code, "utf8"))
        #
        #         # Traverse the syntax tree
        #         # for node in tree.root_node.children:
        #         #     class_names = extract_class_names(node, class_names)
        #
        #         # The previous approach only traverses the Level 1 nodes - Class declaration, Import declaration,
        #         # Package declaration. Only looking for Imports and Super class declaration won't result in the
        #         # collection of all reusable components. For example: In case of imports with wild-cards(*) we need to
        #         # look for Variable Types as well. So replaced the logic with a recursive traversal to visit all nodes.
        #
        #         reusable_class_used[dir_name]: Set[str] = extract_class_names(tree.root_node, class_names)
        #         break
    print(reusable_class_used)

    reusable_class_list = []
    for root, dirs, files in os.walk(framework_code_folder_path):
        for file in files:
            reusable_class_list.append(file.split('.')[0])
    print(reusable_class_list)

    for key, value_set in reusable_class_used.items():
        reusable_class_used[key] = value_set.intersection(reusable_class_list)
    print(reusable_class_used)

    for key, value_set in reusable_class_used.items():
        reusable_class_used[key] = value_set.difference(exclude_files)
    print(reusable_class_used)

    return reusable_class_used

def get_imports(existing_scripts_folder_path):
    for root, dirs, files in os.walk(existing_scripts_folder_path):
        for file in files:
            if not file.endswith(".zip"):
                # Extract imported and extended class names
                class_names = set()
                dir_name = os.path.basename(root)  # Get the directory name from 'root'
                script_file = os.path.join(root, file)
                # Load your Python source code
                with open(script_file, 'r') as file:
                    source_code = file.read()
                # Parse the code
                tree = parser.parse(bytes(source_code, "utf8"))
                # Traverse the syntax tree
                for node in tree.root_node.children:
                    class_names = extract_class_names(node, class_names)
                reusable_class_used[dir_name] = class_names
                break
    print("reusable_class_used", reusable_class_used)
    return reusable_class_used


def get_dependencies(file_path: str) -> set:
    """
    Get dependencies of a given file.
    Parameters:
        file_path: path to the file
    Returns:
        set of dependencies
    """
    print(file_path)
    with open(file_path, 'r') as file:
        code = file.read()

    # Parse the code
    parser = tree_sitter.Parser()
    parser.set_language(JAVA_LANGUAGE)
    tree = parser.parse(bytes(code, "utf8"))

    # Extract dependencies (for simplicity, assume imports only)
    dependencies = set()
    for node in tree.root_node.children:
        if node.type == 'import_declaration':
            import_name = code[node.start_byte:node.end_byte].strip().split()[-1].replace(";", "")
            dependencies.add(import_name)
    return dependencies


def find_dependencies(folder_path: str, extension: str) -> dict:
    """
    Find dependencies of all files in the given directory.
    Parameters:
        folder_path: path to the directory containing source files
        extension: file extension
    Returns:
        dictionary containing dependencies of all files in the given directory
    """
    dependencies_map = defaultdict(lambda: defaultdict(list))

    for root, _, files in os.walk(folder_path):
        for file in files:
            if(file.endswith("."+extension)):
                file_path = os.path.join(root, file)

                # Get dependencies of the current file
                dependencies = get_dependencies(file_path)

                # Extract filename with package
                # package_path = os.path.relpath(file_path, folder_path)[:-5].replace(os.sep, '.')

                filename_without_package = os.path.splitext(os.path.basename(file_path))[0].strip()

                # Update dependencies map
                folder_name = os.path.basename(os.path.dirname(file_path)).strip()

                for dependency in dependencies:
                    dependencies_map[folder_name][dependency.strip()].append(filename_without_package)

    return dependencies_map


def load_dependents(src_path: str, extension: str) -> dict:
    """
    Load dependencies of all files in the given directory.
    Parameters:
        src_path: path to the directory containing source files
        extension: file extension
    Returns:
        dictionary containing dependencies of all files in the given directory
    """
    dependencies_map = find_dependencies(src_path, extension)

    # Convert the dependencies map to the desired format
    output = {}
    for folder, dependencies in dependencies_map.items():
        output[folder] = []
        for dependency, files in dependencies.items():
            output[folder].append({dependency: files})

    return output


def get_dependents_by_root(module: str, root: str, dependency_schema: dict) -> Union[list, None]:
    """
    Get dependents of a component by root name.
    Parameters:
        module: component name to look for dependents
        root: file name considered as dependency
        dependency_schema: dictionary containing dependencies of all components
    Returns:
        dependents found under given module for the given dependency
    """
    try:
        if dependency_schema[module]:
            for dependents in dependency_schema[module]:
                for root_name, dependent in dependents.items():
                    if root_name.endswith("." + root):
                        return dependent if len(dependent) > 0 else None

        return None
    except Exception as e:
        return None


def get_common_dependents(module: str, identifiers: List[str], dependency_schema: Dict[str, List[Dict[str, set]]]) -> set:
    """
    Get common dependents of multiple components.
    Parameters:
        module: component name to look for dependents
        identifiers: list of file names considered as dependency
        dependency_schema: dictionary containing dependencies of all components
    Returns:
        dependents found under given module for the given dependencies
    """
    result = {}
    try:
        if dependency_schema[module]:
            for identifier in identifiers:
                result[identifier] = set()
                for dependents in dependency_schema[module]:
                    for root_name, dependent in dependents.items():
                        if root_name.endswith("." + identifier):
                            result[identifier].update(dependent)

            common_dependents = result[identifiers[0]].intersection(*[result[identifier] for identifier in identifiers[1:]])
            return common_dependents

        return set()
    except Exception as e:
        return set()

def load_src_vectors(directory: str, sub_directory: str, extension: str, data_path: str, comp_type: str, csv_ingestor: ChromaDBConnector, code_ingestor: ChromaDBConnector) -> None:
    """
    Load source code vectors to the database
    Parameters:
        directory: reviewed scripts directory
        sub_directory: component's directory name
        extension: file extension
        data_path: data folder path for current project
        comp_type: component type
        csv_ingestor: ChromaDBConnector object for csv data
        code_ingestor: ChromaDBConnector object for code data
    Returns:
        None
    """

    if os.path.exists(f"{directory}/{sub_directory}"):
        method_parser = ParseMethodToCsv()

        method_parser.parse_full_data(
            f"{directory}/{sub_directory}",
            f"{data_path}/gen_code_csv/{sub_directory}"
        )

        for filename in glob.glob(f"{directory}/{sub_directory}/*.{extension}"):
            with open(filename, encoding="utf8") as code:
                match = re.search(fr'\\(\w+)\.{extension}', filename)
                if match:
                    f_name = match.group(1)
                else:
                    match = re.search(fr'/(\w+)\.{extension}', filename)
                    if match:
                        f_name = match.group(1)

                print(f_name)

                csv_ingestor.embed_csv_with_metadata(f"{data_path}/gen_code_csv/{sub_directory}/{f_name}.csv", metadata={'component type': comp_type, 'component name': f_name})
                code_ingestor.vectordb_store_code(code.read(), f_name=f_name)
                # csv_ingestor.persist_directory

                print(f"{data_path}/gen_code_csv/{sub_directory}/{f_name}.csv")

        # print(code_ingestor.get_doc_by_id("KemperAutoPage"))
        # print(csv_ingestor.get()['ids'][0])

