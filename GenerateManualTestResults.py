import sys
import configparser
from us_to_mtc_file.ModelManualTestLLM import LLM
from colorama import init, Fore, Style
import warnings

config_path = 'Config'
warnings.filterwarnings("ignore")


class ManualTestGenerator:
    def __init__(self, llm_family):
        """

        :param llm_family: LLM Family chosen (GPT/Gemini)
        """
        init()

        self.llm_family = llm_family

        if self.llm_family == 'GPT':
            self.config_parser_gpt = configparser.ConfigParser()
            self.config_parser_gpt.read(config_path + '/ConfigGPT.properties')
            self.positive_instruction = self.config_parser_gpt.get('Prompt', 'positive_instruction')
            self.negative_instruction = self.config_parser_gpt.get('Prompt', 'negative_instruction')
            self.both_instruction = self.config_parser_gpt.get('Prompt', 'both_instruction')
            self.instructions = self.config_parser_gpt.get('Prompt', 'instructions')
            self.reuse_instruction = self.config_parser_gpt.get('Prompt', 'reuse_instruction')
            self.additional_intelligence_instructions = (self.config_parser_gpt.get
                                                         ('Prompt', 'additional_intelligence_instructions'))
            self.acceptance_criteria_instruction = (self.config_parser_gpt.get
                                                    ('AdditionalAcceptanceCriteria', 'acceptance_criteria_prompt'))
            self.acceptance_criteria_input = (self.config_parser_gpt.get
                                              ('AdditionalAcceptanceCriteria', 'input_user_story'))
            self.manual_test_prompt = self.config_parser_gpt.get('Context', 'manual_test_prompt')
            self.manual_test_context = self.config_parser_gpt.get('Context', 'manual_test_context')
            self.manual_test_prompt_instruction = self.config_parser_gpt.get('Context',
                                                                             'manual_test_prompt_instruction')
            self.manual_test_instruction = self.config_parser_gpt.get('Context', 'manual_test_instruction')
            self.manual_test_userStory_instruction = self.config_parser_gpt.get('Context',
                                                                                'manual_test_userStory_instruction')
            self.manual_test_userStory = self.config_parser_gpt.get('Context', 'manual_test_userStory')

            self.manual_test_noContext_prompt = self.config_parser_gpt.get('NoContext', 'manual_test_noContext_prompt')
            self.manual_test_noContext_instruction = self.config_parser_gpt.get('NoContext',
                                                                                'manual_test_noContext_instruction')
            self.manual_test_noContext_instruction_userStory =\
                self.config_parser_gpt.get('NoContext', 'manual_test_noContext_instruction_userStory')
            self.manual_test_noContext_userStory = self.config_parser_gpt.get('NoContext',
                                                                              'manual_test_noContext_userStory')

    def get_manual_test_no_context(self, test_type, input_length, query):
        model = LLM(self.llm_family)
        instruction = self.instructions + '\n' + self.reuse_instruction + '\n'
        if test_type == 'Both':
            instruction += self.both_instruction + '\n '
        elif test_type == 'Positive':
            instruction += self.positive_instruction + '\n '
        elif test_type == 'Negative':
            instruction += self.negative_instruction + '\n '
        additional_intelligence_choice = input("\nDo you want to enable additional intelligence? (yes or no): ")
        additional_criteria_choice = input(
            "\nDo you want to generate additional Acceptance Criteria? (yes or no): ")

        additional_criteria_prompt = (
                self.acceptance_criteria_instruction + '\n' + self.acceptance_criteria_input
                + '\nAcceptance Criteria: ')

        if additional_criteria_choice in ("yes", "Yes"):
            ac_generated = model.send_request(additional_criteria_prompt, ["UserStory"], {"UserStory": query})
            query += '\n'
            query += ac_generated
        if additional_intelligence_choice in ("no", "No"):
            instruction += self.additional_intelligence_instructions
        manual_test_prompt = (
                self.manual_test_noContext_prompt + '\n' + self.manual_test_noContext_instruction + '\n' +
                self.manual_test_noContext_instruction_userStory + '\n' + self.manual_test_noContext_userStory +
                '\nManual Test:')
        print_prompt = (self.manual_test_noContext_prompt + '\n' + instruction + '\n' +
                        self.manual_test_noContext_instruction_userStory + '\n' + query + '\nManual Test:')
        print("\nThe Prompt passed to the LLM is : \n")
        print(Fore.YELLOW + print_prompt + Style.RESET_ALL)

        choice_prompt = input("\nDo you want to pass this prompt to LLM? (yes or no): ")
        if choice_prompt == 'no' or choice_prompt == 'No':
            if input_length != 1:
                choice_prompt2 = input("\nDo you want to proceed to next User Story? (yes or no): ")
                if choice_prompt2 == "yes" or choice_prompt2 == 'Yes':
                    return ""
                else:
                    print(Fore.RED + "\nPlease change the prompt in your configPrompt configuration file" +
                          Style.RESET_ALL)
                    return "exit"
            else:
                print(
                    Fore.RED + "\nPlease change the prompt in your configPrompt configuration file" + Style.RESET_ALL)
                return "exit"

        output = model.send_request(manual_test_prompt, ["instruction", "UserStory"],
                                    {"instruction": instruction, "UserStory": query})

        return [output]

    def get_manual_test(self, test_type, input_length, query, context):
        model = LLM(self.llm_family)

        instruction = self.instructions + '\n' + self.reuse_instruction + '\n'
        if test_type == 'Both':
            instruction += self.both_instruction + '\n'
        elif test_type == 'Positive':
            instruction += self.positive_instruction + '\n '
        elif test_type == 'Negative':
            instruction += self.negative_instruction + '\n '
        additional_intelligence_choice = input("\nDo you want to enable additional intelligence? (yes or no): ")
        additional_criteria_choice = input(
            "\nDo you want to generate additional Acceptance Criteria? (yes or no): ")

        additional_criteria_prompt = (self.acceptance_criteria_instruction + '\n' + self.acceptance_criteria_input
                                      + '\nAcceptance Criteria: ')

        if additional_criteria_choice in ("yes", "Yes"):
            ac_generated = model.send_request(additional_criteria_prompt, ["UserStory"], {"UserStory": query})
            query += '\n'
            query += ac_generated
        if additional_intelligence_choice in ("no", "No"):
            instruction += self.additional_intelligence_instructions
        manual_test_prompt_mtc = (
                self.manual_test_prompt + '\n' + self.manual_test_context + '\n' + self.manual_test_prompt_instruction +
                '\n' + self.manual_test_instruction + '\n' + self.manual_test_userStory_instruction + '\n' +
                self.manual_test_userStory + '\nManual Test :')
        print_prompt = (self.manual_test_prompt + '\n' + context + '\n' + self.manual_test_prompt_instruction + '\n' +
                        instruction + '\n' + self.manual_test_userStory_instruction + '\n' + query + '\nManual Test :')
        print("\nThe Prompt passed to the LLM is : \n")
        print(Fore.YELLOW + print_prompt + Style.RESET_ALL)

        choice_prompt = input("\nDo you want to pass this prompt to LLM? (yes or no): ")
        if choice_prompt == 'no' or choice_prompt == 'No':
            if input_length != 1:
                choice_prompt2 = input("\nDo you want to proceed to next User Story? (yes or no): ")
                if choice_prompt2 == "yes" or choice_prompt2 == 'Yes':
                    return ""
                else:
                    print(Fore.RED + "\nPlease change the prompt in your configPrompt configuration file" +
                          Style.RESET_ALL)
                    return "exit"
            else:
                print(
                    Fore.RED + "\nPlease change the prompt in your configPrompt configuration file" + Style.RESET_ALL)
                return "exit"

        output = model.send_request(manual_test_prompt_mtc
                                    , ["context", "instruction", "UserStory"],
                                    {"context": context, "instruction": instruction, "UserStory": query})

        return [output]
