import re
import string


class VariablesAreNotProvided(Exception):
    def __init__(self):
        self.type = "input_error"
        self.msg = "Variables were not provided"


class VariableDoesNotExist(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return f"Add {self.value} to headers"


class TruthTable:
    def __init__(self) -> None:
        self.table = []
        self.headers = []
        self.solution = []
        self.current_action = 0     # Текущее действие

    @staticmethod
    def get_rotated_matrix(matrix: list) -> list:
        """Rotate matrix to 90 degrees clckwise"""
        return list(list(x)[::-1] for x in zip(*matrix))

    @staticmethod
    def get_bin(number: int, length: int) -> str:
        """Returns bin number in format value:length.f"""
        number = bin(number)[2:]
        length_delta = len(number) - length
        if length_delta < 0:
            for _ in range(-length_delta):
                number = "0" + number
        elif length_delta > 0:
            number = number[:-length_delta]
        return number

    def get_dict(self) -> dict:
        """
        returns table as a dict
        """
        output_dict = {}
        for i, header in enumerate(self.headers):
            try:
                h = int(header)
            except ValueError:
                h = header
            output_dict.update({h: list(map(int, self.table[i]))})

        return output_dict

    def get_solution(self) -> list:
        """
        Returns a list of steps to solve the equation
        """
        solutions = []
        for j, solution in enumerate(self.solution):
            for i, sol in enumerate(self.solution):
                solution = solution.replace(str(i + 1), sol)
            self.solution[j] = solution
            solutions.append(solution)
        return solutions

    def __repr__(self) -> str:
        str_table = " ".join(header for header in self.headers) + "\n"
        power = len(self.headers) - self.current_action
        horizontal_power = len(self.headers)
        for i in range(2**power):
            for j in range(horizontal_power):
                str_table += self.table[j][i] + " "
            str_table += "\n"

        return str_table

    def get_values_by_headers(self, headers: list) -> tuple:
        try:
            return self.table[self.headers.index(headers[0])], self.table[self.headers.index(headers[1])]
        except ValueError:
            raise VariableDoesNotExist(value=headers)

    def make_implication(self, headers: list) -> None:
        self.current_action += 1
        new_values = ["1" if not (a == "1" and b == "0") else "0" for a, b in zip(*self.get_values_by_headers(headers))]
        self.add_column(str(self.current_action), new_values)

    def make_disjunction(self, headers: list) -> None:
        self.current_action += 1
        new_values = ["1" if a == "1" or b == "1" else "0" for a, b in zip(*self.get_values_by_headers(headers))]
        self.add_column(str(self.current_action), new_values)

    def make_conjunction(self, headers: list) -> None:
        self.current_action += 1
        new_values = ["1" if a == "1" and b == "1" else "0" for a, b in zip(*self.get_values_by_headers(headers))]
        self.add_column(str(self.current_action), new_values)

    def make_equation(self, headers: list) -> None:
        self.current_action += 1
        new_values = ["1" if a == b else "0" for a, b in zip(*self.get_values_by_headers(headers))]
        self.add_column(str(self.current_action), new_values)

    def make_inversion(self, header: str) -> None:
        self.current_action += 1
        try:
            values = self.table[self.headers.index(header)]
        except ValueError:
            raise VariableDoesNotExist(value=header)
        new_values = ["0" if value == "1" else "1" for value in values]
        self.add_column(str(self.current_action), new_values)

    def cut_instance(self, instance: str, span: tuple) -> str:
        return instance[:span[0]] + str(self.current_action) + instance[span[1]:]

    @staticmethod
    def get_headers(instance: str) -> list:
        headers = set()
        instance = instance.replace("INV", "")
        for symbol in instance:
            if symbol in string.ascii_letters:
                headers.add(symbol)

        return sorted(list(headers))

    #TODO: Split it into small functions
    def solve_instance(self, instance: str) -> None:
        instance = instance.replace(" ", "")
        inversion = re.search(r"INV\(.[^INV()]?\)", instance)
        conjunction = re.search(r".?/\\.?", instance)
        disjunction = re.search(r".?\\/.?", instance)
        implication = re.search(r".?->[^INV]", instance)
        equation = re.search(r".?=.?", instance)

        if inversion:
            self.solution.append(instance[inversion.start():inversion.end()])
            self.make_inversion(inversion.group()[4:-1])
            instance = self.cut_instance(instance, inversion.span())

        elif conjunction:
            self.solution.append(instance[conjunction.start():conjunction.end()])
            self.make_conjunction(conjunction.group().split("/\\"))
            instance = self.cut_instance(instance, conjunction.span())

        elif disjunction:
            self.solution.append(instance[disjunction.start():disjunction.end()])
            self.make_disjunction(disjunction.group().split("\\/"))
            instance = self.cut_instance(instance, disjunction.span())

        elif implication:
            self.solution.append(instance[implication.start():implication.end()])
            self.make_implication(implication.group().split("->"))
            instance = self.cut_instance(instance, implication.span())

        elif equation:
            self.solution.append(instance[equation.start():equation.end()])
            self.make_equation(equation.group().split("="))
            instance = self.cut_instance(instance, equation.span())

        else:
            return

        self.solve_instance(instance)

    def add_column(self, variable: str, values: list) -> None:
        self.headers.append(variable)
        self.table.append(values)

    def set_start_columns(self, instance: str) -> None:
        """Sets up the initial table. For example, if the instance has 3 variables,
        there will be 3 columns, each iterating through all possible values."""
        variables = self.get_headers(instance)
        if not variables:
            raise VariablesAreNotProvided()

        for variable in variables:
            self.headers.append(variable)
            self.table.append([])
        power = len(variables)
        for i in range(2**power):
            number = self.get_bin(i, power)
            for j in range(len(number)):
                self.table[j].append(number[j])
