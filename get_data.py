#!/usr/local/bin/python

import re
import sh
import sys
import os

#####################
# Comment functions #
#####################
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


####################
# Method functions #
####################
def get_method_name(method_list):
    parsed_method_list = []
    for method in method_list:
        second_sep = method.find(':')
        parsed_method_list.append(method[method.index(')')+1:second_sep])
    return parsed_method_list

def get_methods(file):
    regex = re.compile('(^- \(.*[^;]({|\n)(.|\n)*?^})', re.MULTILINE)
    return get_matches_from_file(regex, file)


def get_method_headers(file):
    regex = re.compile('(^- \(.*[^;]({|\n))', re.MULTILINE)
    return get_matches_from_file(regex, file)


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

##################
# Nesting functions #
##################
def update_max_nesting(curr, max):
    if (curr > max):
        return curr
    return max

def update_nesting(line, curr):
    opening_brace_regex = '{'
    closing_brace_regex = '}'
    opening = re.findall(opening_brace_regex, line)
    closing = re.findall(closing_brace_regex, line)
    return curr + len(opening) - len(closing)

def get_nesting_level(file):
    flist = open(file).readlines()
    method_regex = '(if|for|while|else).*\('
    parsing = False
    current_nesting_depth = 0
    max_nesting_depth = 0
    for line in flist:
        match = re.findall(method_regex, line);
        if match:
            parsing = True
        if parsing:
            current_nesting_depth = update_nesting(line, current_nesting_depth)
            max_nesting_depth = update_max_nesting(current_nesting_depth, max_nesting_depth)
            if (current_nesting_depth == 0):
                parsing = False

    return max_nesting_depth


##################
# LCOM functions #
##################
def get_attr(match):
    attr = []
    front_delim = match.find('{')+1
    back_delim = match.find('}')
    rows = match[front_delim:back_delim].split('\n')
    for r in rows:
        if r is not "":
            tmp = r.rsplit(None, 1)[-1]
            attr.append(re.search('\w+', tmp).group(0))
    return attr

def get_attributes(file):
    attributes = []
    interface_regex = '(@interface(.|\n)*{(.|\n)*})'
    property_regex = '(@property .*)'
    interface_matches = get_matches_from_file(interface_regex, file)[0]
    property_matches = get_matches_from_file(property_regex, file)
    for m in interface_matches:
        attributes.append(get_attr(m))
    for m in property_matches:
        attributes.append(get_attr(m))

    return [y for x in attributes for y in x]


def attribute_in_method(attribute, method):
    if re.search(attribute, method) is None:
        return 0
    return 1

def get_lcom(file, header):
    matches = get_methods(file)
    attributes = get_attributes(header)
    methods = []
    m_a = 0
    for m in matches:
        methods.append(m[0])
    for a in attributes:
        for m in methods:
            m_a = float(m_a + attribute_in_method(a, m))
    
    return round(((m_a / len(attributes) - (len(methods))) / (1 - len(methods))),2)


##################
# File functions #
##################
def get_matches_from_file(regex, file):
    with open(file, 'r') as f:
        s = f.read()
        return re.findall(regex, s)

def get_inheritable_methods(pattern):
    inherited_method_list = []
    for root, dirs, files in os.walk("../Classes"):
        for basename in files:
            if basename in pattern:
                inherited_method_list = get_interface_methods(inherited_method_list, root+'/'+basename)
    return [y for x in inherited_method_list for y in x]


def get_superclass_headers(file):
    header_list = []
    regex = str('#import \"PRJ.*\.h\"')
    matches = get_matches_from_file(regex, file)
    for m in matches:
        index = m.index('"')
        header_list.append(m[index+1:-1])

    for root, dirs, files in os.walk("../Classes"):
        for basename in files:
            if basename in header_list:
                for e in get_superclass_headers(root+'/'+basename):
                    header_list.append(e)
    return header_list


def get_superclass_methods(headers):
    method_list = []
    method_name_list = []
    for root, dirs, files in os.walk("../Classes"):
        for basename in files:
            if basename in headers:
                for m in get_method_headers(root+'/'+basename[:-1]+'m'):
                    method_list.append(m[0])
    for m in method_list:
        method_name = re.findall('- \(.*?\)\w+', m)[0]
        method_name_list.append(method_name[method_name.index(')')+1:])
    return method_name_list

# could be extended to search transitive subclasses
def get_subclasses(name):
    try:
        res = sh.grep("-r", str("@interface \w* : " + name), ".")
        return len(res.splitlines())
    except:
        return 0


#################
# Program start #
#################
if len(sys.argv) >= 2:
    file_name = sys.argv[1][sys.argv[1].rfind('/')+1:]
    location = sys.argv[1][:sys.argv[1].rfind('/')+1]
    file_path = sys.argv[1]
    header_file_name = file_name[:-1] + 'h'
    header_file_path = location + header_file_name
else:
    print("Usage examples: \n./get_data.py Controllers/Menu/PRJMenuViewController.m")
    exit(1)


loc = 0
with open(file_path, 'r') as f:
    for line in f:
        if line != '\n':
            loc+=1

nrComments=0
with open(file_path, 'r') as f:
    s = f.read()
    nrComments = len(re.findall('\/\/', s)) + find_multiline_comments(s)

nrMethods = 0
methods = []
with open(file_path, 'r') as f:
    s = f.read()
    regex_matches = re.findall('[-+] \(.*',s)
    for match in regex_matches:
        methods.append(match[match.find(')')+1:match.find(':')])
    nrMethods = len(methods)

superclass_headers = get_superclass_headers(header_file_path)
inheritable_methods = get_inheritable_methods(superclass_headers)
superclass_methods = get_superclass_methods(superclass_headers)

nrOvMethods = 0
for method in methods:
    if (method in inheritable_methods) or (method in superclass_methods):
        nrOvMethods = nrOvMethods + 1

effCoupling = 0
with open(file_path, 'r') as f:
    s = f.read()
    matches = re.findall('#import \".*\.h\"',s)
    effCoupling = len(matches) - 1

import_regexp = str("#import " + '"' + header_file_name + '"')
affCoupling = len(sh.grep("-r", import_regexp, ".").splitlines()) - 1

rfc = 0
with open(file_path, 'r') as f:
    s = f.read()
    matches = re.findall('\[', s)
    rfc = len(matches) - 1

nsb = get_nesting_level(file_path)

lcom = get_lcom(file_path, header_file_path)

sub = get_subclasses(file_name[:-2])

print(str(loc-nrComments) + "\t" +
      str(nrMethods) + "\t" +
      str(nrOvMethods) + "\t" +
      str(len(inheritable_methods)) + "\t" +
      str(rfc) + "\t" +
      str(affCoupling) + "\t" +
      str(effCoupling) + "\t" +
      str(nsb) + "\t" +
      str(lcom) + "\t" +
      str(sub))

# print("____ Metrics data for: " + class_name + " ____")
# print("Size: " + str(loc-nrComments))
# print("No. of methods: " + str(nrMethods))
# print("No. of ovr. methods: " + str(nrOvMethods))
# print("No. of inh. methods: " + str(len(inheritable_methods)))
# print("Communication: " + str(rfc))
# print("Afferent coupling: " + str(affCoupling))
# print("Efferent coupling: " + str(effCoupling))
# print("\n")

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
