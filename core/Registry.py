commands = {}   # { "SDGSetArb": <function(instr, args)> }
devices = {}    # { "SDG1": <instance>, "Scope1": <instance> }

def register_command(func):
    commands[func.__name__] = func
    return func

def register_device(name, instance):
    print(f'Succesfully registered {name} as an instance of {instance.__class__.__name__}')
    devices[name] = instance