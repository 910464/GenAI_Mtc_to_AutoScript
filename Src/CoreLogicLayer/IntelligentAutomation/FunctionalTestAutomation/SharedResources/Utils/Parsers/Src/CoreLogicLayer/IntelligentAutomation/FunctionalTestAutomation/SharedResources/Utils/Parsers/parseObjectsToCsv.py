import csv
from typing import Set

import javalang
from javalang.tree import PackageDeclaration


class ParseObjectsToCsv:
    def __init__(self, source_code):
        self.source_code = source_code
        self.tree = javalang.parse.parse(source_code)
        self.variable_info = []

    def extract_variables_info(self):
        # extract field variable, local variable and parameter variable with package, class, variable_declaration, variable_type, variable_name and variable_value
        package_name = None
        class_name = None
        for path, node in self.tree:
            if isinstance(node, PackageDeclaration):
                package_name = node.name
            elif isinstance(node, javalang.tree.ClassDeclaration):
                class_name = node.name
            elif isinstance(node, javalang.tree.FieldDeclaration):
                for declarator in node.declarators:
                    variable_name = declarator.name
                    variable_type = node.type.name if isinstance(node.type,
                                                                 javalang.tree.BasicType) else node.type.name.value
                    value = self.extract_variable_value(node.position)
                    self.variable_info.append(
                        {'Package': package_name, 'Class': class_name, 'Field': variable_name, 'Type': variable_type,
                         'Value': value})
            elif isinstance(node, javalang.tree.LocalVariableDeclaration):
                for declarator in node.declarators:
                    variable_name = declarator.name
                    variable_type = node.type.name if isinstance(node.type,
                                                                 javalang.tree.BasicType) else node.type.name.value
                    value = self.extract_variable_value(node.position)
                    self.variable_info.append(
                        {'Package': package_name, 'Class': class_name, 'Field': variable_name, 'Type': variable_type,
                         'Value': value})
            elif isinstance(node, javalang.tree.MethodDeclaration):
                for parameter in node.parameters:
                    variable_name = parameter.name
                    variable_type = parameter.type.name if isinstance(parameter.type,
                                                                      javalang.tree.BasicType) else parameter.type.name.value
                    value = self.extract_variable_value(parameter.position)
                    self.variable_info.append(
                        {'Package': package_name, 'Class': class_name, 'Field': variable_name, 'Type': variable_type,
                         'Value': value})
        return self.variable_info

    def extract_variable_value(self, position):
        start_line, start_column, _, end_line, end_column, _ = position
        start_index = self.source_code.index('\n', self.source_code.index(f'\n{start_line}') + 1) + 1 + start_column
        end_index = self.source_code.index('\n', self.source_code.index(f'\n{end_line}') + 1) + end_column
        return self.source_code[start_index:end_index]

    def get_variable_names(self, type:Set[str]):
        return [variable['Field'] for variable in self.variable_info if variable['Type'] in type]

    def save_to_csv(self, file_path, field_variables_info):
        with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['Package', 'Class', 'Field', 'Type', 'Value']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(field_variables_info)
