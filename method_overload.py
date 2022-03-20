import itertools
from typing import List, Set
import re
from io import StringIO
import random
import os


class method_overload():

	def __init__(self):
		self.content = None
		self.filename = None
		self.is_adding_methods = True

		self.param_types = ["Ljava/lang/String;", "Z", "B", "S", "C", "I", "F"]

	def read_smali(self, filename):
		self.filename = filename

		# Read Smali file
		with open(self.filename, "r") as f:
			self.content = f.read()

	def get_smali_method_overload(self):
		with open("body.txt") as fp:
			data = fp.read()
		return data

	def add_method_overloads(self, smali_files: List[str], class_names_to_ignore: Set[str]):
		overloaded_method_body = self.get_smali_method_overload()
		added_methods = 0

		for smali_file in smali_files:
			added_methods += self.add_method_overloads_to_file( smali_file, overloaded_method_body,class_names_to_ignore)

		print(added_methods,' new overloaded methods were added!')


	def add_method_overloads_to_file(self,smali_file: str, overloaded_method_body: str, class_names_to_ignore: Set[str]):
		new_methods_num: int = 0
		self.read_smali(smali_file)

		# .class <other_optional_stuff> <class_name;>  # Every class name ends with ;
		class_pattern = re.compile(r"\.class.+?(?P<class_name>\S+?;)", re.UNICODE)

		# .method <other_optional_stuff> <method_name>(<param>)<return_type>
		method_pattern = re.compile(
			r"\.method.+?(?P<method_name>\S+?)"
			r"\((?P<method_param>\S*?)\)"
			r"(?P<method_return>\S+)",
			re.UNICODE,
		)
		s = StringIO(self.content)

		with open( "changed_"+smali_file , "w") as out_file:
			skip_remaining_lines = False
			class_name = None
			for line in s:

				if skip_remaining_lines:
					out_file.write(line)
					continue

				if not class_name:
					class_match = class_pattern.match(line)
					# If this is an enum class, skip it.
					if " enum " in line:
						skip_remaining_lines = True
						out_file.write(line)
						continue
					elif class_match:
						class_name = class_match.group("class_name")
						if class_name in class_names_to_ignore:
							# The methods of this class should be ignored when
							# renaming, so proceed with the next class.
							skip_remaining_lines = True
						out_file.write(line)
						continue

				# Skip virtual methods, consider only the direct methods defined
				# earlier in the file.
				# if line.startswith("# virtual methods"):
				# 	skip_remaining_lines = True
				# 	out_file.write(line)
				# 	continue

				# Method declared in class.
				method_match = method_pattern.match(line)

				# Avoid constructors, native and abstract methods.
				if (
						method_match
						and "<init>" not in line
						and "<clinit>" not in line
						and " native " not in line
						and " abstract " not in line
				):
					# Create lists with random parameters to be added to the method
					# signature. Add 4 overloads for each method and for each overload
					# use 3 random params.
					for params in get_random_list_permutations(random.sample(self.param_types, 3))[:4]:
						new_param = "".join(params)
						# Update parameter list and add void return type.
						overloaded_signature = line.replace(
							"({0}){1}".format(
								method_match.group("method_param"),
								method_match.group("method_return"),
							),
							"({0}{1})V".format(
								method_match.group("method_param"), new_param
							),
						)
						out_file.write(overloaded_signature)
						out_file.write(overloaded_method_body)
						new_methods_num += 1

					# Print original method.
					out_file.write(line)
				else:
					out_file.write(line)

		return new_methods_num


def get_android_class_names():
	with open('android_class_names_api_27.txt', "r") as file:
		# Return a list with the non blank lines contained in the file.
		return list(filter(None, (line.rstrip() for line in file)))


def get_random_list_permutations(input_list: list) -> list:
	permuted_list = list(itertools.permutations(input_list))
	random.shuffle(permuted_list)
	return permuted_list


def main():
	android_class_names: Set[str] = set(get_android_class_names())
	a = method_overload()
	b=[f for f in os.listdir('app-release\smali\com\example\hello') if f.endswith('.smali')]
	a.add_method_overloads(b, android_class_names)


if __name__ == '__main__':
	main()
