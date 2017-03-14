#!/usr/local/bin/python

import re
import sh
import sys
import os

def find_substring(substring, string):
    indices = []
    index = -1  # Begin at -1 so index + 1 is 0
    while True:
        # Find next index of substring, by starting search from index + 1
        index = string.find(substring, index + 1)
        if index == -1:
            break  # All occurrences have been found
        indices.append(index)
    return len(indices)

def find_multiline_comments(string):
    multiline_count = 0
    comments = re.findall('(/\*([^*]|(\*+[^*/]))*\*+/)|(//.*)', string)
    for comment_tup in comments:
        for comment in comment_tup:
            block_comment_lines = find_substring("\n", comment)
            if block_comment_lines is not 0:
                multiline_count = multiline_count + find_substring("\n", comment) + 1
    return multiline_count

def get_imports(file):
    return

def get_method_name(method_list):
    for method in method_list:
        second_sep = method.find(':')
        return method[method.index(')')+1:second_sep]

def get_interface_methods(method_list, file):
    flist = open(file).readlines()
    method_regex = '- \([A-Za-z \*]*.*'
    parsing = False
    for line in flist:
        if line.startswith("@interface"):
            parsing = True
            continue
        if parsing:
            match = re.findall(method_regex, line)
            method = get_method_name(match)
            if method is not None:
                method_list.append(method)
    return method_list


if len(sys.argv) >= 3:
    class_name = sys.argv[2]
    file_name = sys.argv[1] + '/' + class_name + '.m'
    header_file = sys.argv[1] + '/' + class_name + '.h'
else:
    print("Usage examples: \n./get_data.py Controllers/Menu PRJMenuViewController")
    exit(1)

loc = 0
with open(file_name, 'r') as f:
    for line in f:
        if line != '\n':
            loc+=1

nrComments=0
with open(file_name, 'r') as f:
    s = f.read()
    nrComments = len(re.findall('\/\/', s)) + find_multiline_comments(s)

nrMethods = 0
methods = []
with open(file_name, 'r') as f:
    s = f.read()
    regex_matches = re.findall('[-+] \(.*',s)
    for match in regex_matches:
        methods.append(match[match.find(')')+1:match.find(':')])
    nrMethods = len(methods)

def find_file(pattern):
    inherited_method_list = []
    for root, dirs, files in os.walk("../Classes"):
        for basename in files:
            if basename in pattern:
                inherited_method_list = get_interface_methods(inherited_method_list, root+'/'+basename)
    return inherited_method_list


def get_superclasses(file):
    class_list = []
    regex = str('#import \"PRJ.*\.h\"')
    with open(file, 'r') as f:
        s = f.read()
        regex_superclasses = re.findall(regex, s)
        for superclass in regex_superclasses:
            index = superclass.index('"')
            class_list.append(superclass[index+1:-1])

        for root, dirs, files in os.walk("../Classes"):
            for basename in files:
                if basename in class_list:
                    class_list.append(get_superclasses(root+'/'+basename))
    return class_list

superclasses = get_superclasses(header_file)
inheritable_methods = find_file(superclasses)


nrOvMethods = 0
for method in methods:
    if method in inheritable_methods:
        nrOvMethods = nrOvMethods + 1

effCoupling = 0
with open(file_name, 'r') as f:
    s = f.read()
    matches = re.findall('#import \".*\.h\"',s)
    effCoupling = len(matches) - 1

import_regexp = "#import " + '"' + class_name + ".h" + '"'
affCoupling = len(sh.grep("-r", import_regexp, ".").splitlines()) - 1


print("____ Metrics data for: " + class_name + " ____")
print("avgSize: " + str((loc-nrComments)/nrMethods))
print("Comments (%): " + str(nrComments/float(loc)))
print("Afferent coupling: " + str(affCoupling))
print("Efferent coupling: " + str(effCoupling))
print("Coupling: " + str(affCoupling+effCoupling))
print("Polymorph (NORM/NOM): " + str(nrOvMethods/float(nrMethods)))
print("Size: " + str(loc-nrComments))
print(nrComments)
print("\n")

# print("____ List of metrics for: " + class_name + " ____")
# print("avgSize: " + str((loc-nrComments)/nrMethods))
# print("Comments (%): " + str(nrComments/float(loc)))
# print("Communication (RFC): " + "\nResponse for a class, 'measures the number of different methods that can be executed when an object of that class receives a message'")
# print("Complexity (WMC): " + "\nWeighted methods per class. Sum of the complexities of its methods. Cyclomatic complexity could be used as complexity value")
# print("Afferent coupling: " + str(affCoupling))
# print("Efferent coupling: " + str(effCoupling))
# print("Coupling: " + str(affCoupling+effCoupling))
# print("Hierarchies (DIT): " + "\nAlways 1?")
# print("LCohesion (LCOM): " + "\nm(A)- number of methods accessing A, #m - number of methods. ((Sum(m(A))/k)-#m)/(1-m)")
# print("MethodInheri (MFA): " + "\nShould decide how to calculate")
# print("Nesting (NBD): " + "\nNesting in methdods, how deep are the deepest nested thing in the class?")
# print("Polymorph (NORM/NOM): " + str(nrOvMethods/float(nrMethods)))
# print("Size: " + str(loc-nrComments))
# print("Subclasses (NSC): " + "\nAlways 0?")
# print("Cohesion: " + "\n1-LCOM")
# print("Messaging: " + "\nNumber of public methods in the class?")
