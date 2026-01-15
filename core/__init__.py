import inspect
commands = {}

def register_methods(instance):
    # Only register methods that don't start with '_'
    for name, func in inspect.getmembers(instance, inspect.ismethod):
        if not name.startswith('_'):
            commands[name] = func