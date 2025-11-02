# functions
def function(param):
    print(param)


# parameters
## parameters are variables that represents functions input
# arguments
## arguments are actually the value we pass to the function

# positional argument <==> positional invocation
function(1)
# passing argument by name <==> named invocation
function(param=2)  # multiple parameters


# default value
def function(param=1):
    print(param)


function()


# return value
def function(param=1):
    return param * 2


a = function(2)
print(a)


# type hints
def function(param: int) -> int:
    return param * 2


a = function(2)
print(a)

# docstrings
## special comments that can be multiple lines that we write between 3 quotation marks used for documentation
## we write docstrings at the beginning of our function body
### docstrings might contains the explanation of the function in general
### explanation of the parameters (type, default value)
### what the function returns and the type of return

# help(function) # without parenthesis we referencing the function itself
## will print the docstrings of the function

# scope
# LGEB : Local, Enclosing, Global, Built-in

# built-in functions
print()
len("aaa")
max(1, 2)
