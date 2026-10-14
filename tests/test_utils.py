from lino_dev_tools import *

# # select option
# nums = [i for i in range(1,48)]
# print(nums)

# selection = select_option(nums)
# if selection:
#     print(f"Selection: {selection}")
# else:
#     print("No selection!")

# select options
nums = [i for i in range(1,48)]
print(nums)

selections = select_options(nums, max_selections=5)
if selections:
    print(f"Selections: {selections}")
else:
    print("No selections!")

# # select folder
# selected_folder = select_folder()
# if selected_folder:
#     print(f"Selected folder: {selected_folder}")
# else:
#     print("No folder selected")
