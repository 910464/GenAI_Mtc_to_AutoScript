# import csv
# import javalang
# import json
# import os
#
# class ParseMethodToCsv:
#
#     def __init__(self):
#         pass
#
#     def get_documentation(self, node):
#         if node.documentation:
#             # Join the lines of documentation with a space to remove line breaks
#             return ' '.join(node.documentation.splitlines())
#         return ""
#
#     def extract_java_info(self, file_path):
#         with open(file_path, 'r') as file:
#             java_code = file.read()
#
#         tree = javalang.parse.parse(java_code)
#         result = []
#         package_name = ""  # Initialize with a default value
#
#         for path, node in tree:
#             if isinstance(node, javalang.tree.PackageDeclaration):
#                 package_name = node.name
#             elif isinstance(node, javalang.tree.ClassDeclaration):
#                 class_name = node.name
#                 public_methods = []
#                 constructors = []
#
#                 for member in node.body:
#                     if isinstance(member, javalang.tree.MethodDeclaration) and ('public' in member.modifiers or 'protected' in member.modifiers):
#                         method_name = member.name
#                         parameters = ", ".join(str(param.name) for param in member.parameters)
#                         documentation = self.get_documentation(member)
#                         public_methods.append(method_name +"("+ parameters +")")
#                     elif isinstance(member, javalang.tree.ConstructorDeclaration) and ('public' in member.modifiers or 'protected' in member.modifiers):
#                         method_name = "Constructor"
#                         parameters = ", ".join(str(param.name) for param in member.parameters)
#                         documentation = self.get_documentation(member)
#                         constructors.append(method_name +"("+ parameters +")")
#
#                 result.append({'package_name': package_name, 'class_name': class_name, 'methods': public_methods + constructors})
#
#         return result
#
#     def write_to_csv(self, output_file, data):
#         with open(output_file, 'w', newline='') as csvfile:
#             fieldnames = ['package_name', 'class_name', 'methods']
#             writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
#             writer.writeheader()
#
#             for class_info in data:
#                 writer.writerow({
#                     'package_name': class_info['package_name'],
#                     'class_name': class_info['class_name'],
#                     'methods': json.dumps(class_info['methods'], indent=4)
#                 })
#
#     def parse_data(self, folder_path, folder_name):
#         for filename in os.listdir(folder_path):
#             file_path = os.path.join(folder_path, filename)
#             if os.path.isfile(file_path):
#                 with open(file_path, 'r') as file:
#                     class_info_list = self.extract_java_info(file_path)
#                     output_path = file_path.split("\\")[-1].strip(".java")
#                     self.write_to_csv(f"./data/{folder_name}/{output_path}.csv", class_info_list)
import glob
import os
import re
from typing import List, Tuple

import javalang
import csv
import ast


class ParseMethodToCsv:

    def __init__(self):
        pass

    def extract_method_info(self, file_path):
        with open(file_path, 'r') as java_file:
            source_code = java_file.read()

        tree = javalang.parse.parse(source_code)

        method_info_list = []

        package_name = None
        class_name = None

        for path, node in tree:
            if isinstance(node, javalang.tree.PackageDeclaration):
                package_name = node.name
            elif isinstance(node, javalang.tree.ClassDeclaration):
                class_name = node.name
            elif isinstance(node, javalang.tree.MethodDeclaration):
                method_name = node.name
                method_docs = node.documentation

                # Extract method parameters
                parameter_names = [param.name for param in node.parameters]
                parameters_str = ",".join(parameter_names)
                method_data = method_name + "(" + parameters_str + ")"

                method_info = {
                    'Package': package_name,
                    'Class': class_name,
                    'Method': method_data,
                    'Documentation': method_docs
                }

                method_info_list.append(method_info)

        return method_info_list

    def extract_full_method(self, file_path):
        with open(file_path, 'r', encoding="utf8") as java_file:
            source_code = java_file.read()

        tree = javalang.parse.parse(source_code)

        method_info_list = []

        package_name = None
        class_name = None
        method_buffer = None

        for path, node in tree:
            if isinstance(node, javalang.tree.PackageDeclaration):
                package_name = node.name
            elif isinstance(node, javalang.tree.ClassDeclaration):
                class_name = node.name
            elif isinstance(node, javalang.tree.MethodDeclaration):
                method_name = node.name
                method_docs = node.documentation
                # print(node)

                # Extract method parameters
                parameter_names = [param.name for param in node.parameters]

                parameters_str = ",".join(parameter_names)
                # print(node.body)
                # Find the method's source code
                start_line, start_column = node.position
                # end_line, end_column = node.end_position
                end_line = start_line + 4
                method_source = source_code.splitlines()[start_line - 1:end_line]
                # method_source = source_code[start_line:end_line]

                method_source = '\n'.join(method_source)
                print(method_source)
                # method_data = f"{method_name}({parameters_str})"
                method_info = {
                    'Package': package_name,
                    'Class': class_name,
                    'Method': method_source,
                    'Documentation': method_docs
                }

                method_info_list.append(method_info)

        return method_info_list

    def save_to_csv(self, file_path, method_info_list):
        with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['Package', 'Class', 'Method', 'Documentation']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            writer.writerows(method_info_list)

    def parse_data(self, input_path, output_path):
        if not os.path.exists(output_path):
            os.makedirs(output_path)
        for filename in os.listdir(input_path):
            file_path = os.path.join(input_path, filename)
            if os.path.isfile(file_path):
                with open(file_path, 'r') as file:
                    try:
                        method_info_list = self.extract_method_info(file_path)
                        output_file = file_path.split("\\")[-1].strip(".java")
                        self.save_to_csv(f"{output_path}/{output_file}.csv", method_info_list)
                    except:
                        print("Cannot parse Java")

    def parse_full_data(self, input_path, output_path):
        if not os.path.exists(output_path):
            os.makedirs(output_path)
        for filename in os.listdir(input_path):
            file_path = os.path.join(input_path, filename)
            if os.path.isfile(file_path):
                with open(file_path, 'r') as file:
                    try:
                        method_info_list = self.extract_full_method(file_path)
                        output_file = file_path.split("\\")[-1].strip(".java")
                        self.save_to_csv(f"{output_path}/{output_file}.csv", method_info_list)
                    except:
                        print("Cannot parse Java")

    def parse_data_python(self, input_path, output_path):
        if not os.path.exists(output_path):
            os.makedirs(output_path)

        file_path = input_path
        if os.path.isfile(file_path):
            with open(file_path, 'r') as file:
                try:
                    method_info_list = self.extract_method_info_python(file_path)
                    output_file = os.path.splitext(os.path.basename(file_path))[0]
                    # print(output_file)
                    self.save_to_csv(f"{output_path}/{output_file}.csv", method_info_list)
                except:
                    print("Cannot parse Python")

    def extract_method_info_python(self, file_path):
        with open(file_path, 'r') as python_file:
            source_code = python_file.read()

        tree = ast.parse(source_code)

        method_info_list = []

        package_name = None
        class_name = None

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_name = node.name
            if isinstance(node, ast.FunctionDef):
                method_name = node.name
                method_docs = ast.get_docstring(node)

                # Extract method parameters
                parameter_names = [arg.arg for arg in node.args.args]
                parameters_str = ",".join(parameter_names)
                method_data = method_name + "(" + parameters_str + ")"

                method_info = {
                    'Class': class_name,
                    'Method': method_data,
                    'Documentation': method_docs
                }
                # print(method_info)
                method_info_list.append(method_info)

        return method_info_list

def extract_required_java_context(source_code: str) -> str:
    """
    Extracts high level method information from a Java source code string
    Parameters:
        source_code: Java source code
    Returns:
        A string containing high level class information
    """
    tree = javalang.parse.parse(source_code)

    method_info_list = []
    constructor_info_list = []

    package_name = None
    class_name = None

    for path, node in tree:
        if isinstance(node, javalang.tree.PackageDeclaration):
            package_name = node.name
        elif isinstance(node, javalang.tree.ClassDeclaration):
            class_name = node.name
        elif isinstance(node, javalang.tree.MethodDeclaration):
            method_name = node.name
            method_docs = node.documentation

            # Extract method parameters
            parameter_names = [param.name for param in node.parameters]
            parameters_str = ",".join(parameter_names)
            method_data = method_name + "(" + parameters_str + ")"

            method_info_list.append(f"""
            'Method': {method_data},
            'Documentation': {method_docs}
            """)

        elif isinstance(node, javalang.tree.ConstructorDeclaration):
            constructor_name = class_name
            constructor_doc = node.documentation

            # Extract method parameters
            parameter_names = [param.name for param in node.parameters]
            parameters_str = ",".join(parameter_names)
            constructor_data = constructor_name + "(" + parameters_str + ")"

            constructor_info = f"""
            'Constructor': {constructor_data},
            'Documentation': {constructor_doc}
            """

            constructor_info_list.append(constructor_info)

    method_info_list = '\n'.join(method_info_list)
    constructor_info_list = '\n'.join(constructor_info_list)

    return f"""
    'Package': {package_name}
    'Class': {class_name}
    'Constructors': 
    {constructor_info_list}
    'Methods':
    {method_info_list}
    """

def get_node_source_code(node, source_code):
    start_line = node.position.line
    start_column = node.position.column
    # To get end line, traverse to the last node in method body
    end_line = start_line
    for sub_node in node.body:
        if hasattr(sub_node, 'position') and sub_node.position:
            end_line = max(end_line, sub_node.position.line)

    source_lines = source_code.splitlines()
    method_source_lines = source_lines[start_line - 1:end_line]
    method_source = '\n'.join(method_source_lines)

    return method_source

def extract_required_full_method_java_context(source_code: str) -> str:
    tree = javalang.parse.parse(source_code)
    method_info_list = []

    package_name = None
    class_name = None

    for path, node in tree:
        if isinstance(node, javalang.tree.PackageDeclaration):
            package_name = node.name
        elif isinstance(node, javalang.tree.ClassDeclaration):
            class_name = node.name
        elif isinstance(node, javalang.tree.MethodDeclaration):
            method_name = node.name
            method_docs = node.documentation
            method_source = get_node_source_code(node, source_code)

            method_info_list.append(f"""
            'Method Source': 
            {method_source}
            'Documentation': 
            {method_docs}
            """)

    method_info_list = '\n'.join(method_info_list)

    return f"""
    'Package': '{package_name}',
    'Class': '{class_name}',
    'Methods': [
    {method_info_list}
    ]
    """
