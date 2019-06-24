# -*- coding: utf-8 -*-

name = 'python'

version = 'rezpy-2.7.16'

tools = ['python']

variants = [['platform-linux', 'arch-x86_64']]

def commands():
    env.PATH.append('{this.root}/bin')

def post_commands():
    # these are the builtin modules for this python executable. If we don't
    # include these, some python behavior can be incorrect.
    import os, os.path
    
    path = os.path.join(this.root, "python")
    for dirname in os.listdir(path):
        path_ = os.path.join(path, dirname)
        env.PYTHONPATH.append(path_)

format_version = 2
