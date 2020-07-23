from __future__ import print_function

__author__    = 'Tim Tomes (@LaNMaSteR53)'
__email__     = 'tjt1980[at]gmail.com'
execfile('VERSION')

import errno
import imp
import json
import os
import random
import re
import sys
import traceback
import __builtin__
import framework

# colors for output
__builtin__.N  = '\033[m' # native
__builtin__.R  = '\033[31m' # red
__builtin__.G  = '\033[32m' # green
__builtin__.O  = '\033[33m' # orange
__builtin__.B  = '\033[34m' # blue

# mode flags
__builtin__.script = 0
__builtin__.load = 0

# framework variables
__builtin__.global_options = framework.Options()
__builtin__.keys = {}
__builtin__.loaded_modules = {}
__builtin__.workspace = ''
__builtin__.home = ''
__builtin__.record = None
__builtin__.spool = None

# spooling system
def spool_print(*args, **kwargs):
    if __builtin__.spool:
        __builtin__.spool.write('%s\n' % (args[0]))
        __builtin__.spool.flush()
    if 'console' in kwargs and kwargs['console'] is False:
        return
    # new print function must still use the old print function via the backup
    __builtin__._print(*args, **kwargs)
# make a builtin backup of the original print function
__builtin__._print = print
# override the builtin print function with the new print function
__builtin__.print = spool_print

class Recon(framework.Framework):
    def __init__(self, mode=0):
        # modes:
        # 0 == console (default)
        # 1 == cli
        # 2 == gui
        self.mode = mode
        self.name = 'recon-ng' #os.path.basename(__file__).split('.')[0]
        self.prompt_template = '%s[%s] > '
        self.base_prompt = self.prompt_template % ('', self.name)
        framework.Framework.__init__(self, (self.base_prompt, 'base'))
        self.init_home()
        self.init_global_options()
        self.load_modules()
        self.load_keys()
        if self.mode == 0: self.show_banner()
        self.init_workspace('default')

    #==================================================
    # SUPPORT METHODS
    #==================================================

    def version_check(self):
        try:
            pattern = "'([\d\.]*)'"
            remote = re.search(pattern, self.request('https://bitbucket.org/LaNMaSteR53/recon-ng/raw/master/VERSION').raw).group(1)
            local = re.search(pattern, open('VERSION').read()).group(1)
            if remote != local:
                self.alert('Your version of Recon-ng does not match the latest release.')
                self.alert('Please update or use the \'--no-check\' switch to continue using the old version.')
                self.alert('Read the migration notes for pre-requisites before upgrading.')
                self.output('Migration Notes: https://bitbucket.org/LaNMaSteR53/recon-ng/wiki/#!migration-notes')
                self.output('Remote version:  %s' % (remote))
                self.output('Local version:   %s' % (local))
            return local == remote
        except:
            return True

    def init_home(self):
        self.home = __builtin__.home = '%s/.recon-ng' % os.path.expanduser('~')
        if not os.path.exists(self.home):
            os.makedirs(self.home)

    def init_global_options(self):
        self.register_option('domain', None, 'no', 'target domain')
        self.register_option('company', None, 'no', 'target company name')
        self.register_option('netblock', None, 'no', 'target netblock (CIDR)')
        self.register_option('latitude', None, 'no', 'target latitudinal position')
        self.register_option('longitude', None, 'no', 'target longitudinal position')
        self.register_option('radius', None, 'no', 'radius relative to latitude and longitude')
        self.register_option('user-agent', 'Recon-ng/v%s' % (__version__.split('.')[0]), 'yes', 'user-agent string')
        self.register_option('proxy', None, 'no', 'proxy server <address>:<port>')
        self.register_option('timeout', 10, 'yes', 'socket timeout in seconds')
        self.register_option('verbose', True,  'yes', 'enable verbose output')
        self.register_option('debug', False,  'yes', 'enable debugging output')

    def load_modules(self, reload=False):
        self.loaded_category = {}
        self.loaded_modules = __builtin__.loaded_modules
        if reload: self.output('Reloading...')
        for path in ('./modules/', '%s/modules/' % self.home):
            for dirpath, dirnames, filenames in os.walk(path):
                # remove hidden files and directories
                filenames = [f for f in filenames if not f[0] == '.']
                dirnames[:] = [d for d in dirnames if not d[0] == '.']
                if len(filenames) > 0:
                    mod_category = re.search('/modules/([^/]*)', dirpath).group(1)
                    if not mod_category in self.loaded_category: self.loaded_category[mod_category] = []
                    for filename in [f for f in filenames if f.endswith('.py')]:
                        # this (as opposed to sys.path.append) allows for module reloading
                        mod_name = filename.split('.')[0]
                        mod_dispname = '%s%s%s' % (self.module_delimiter.join(re.split('/modules/', dirpath)[-1].split('/')), self.module_delimiter, mod_name)
                        mod_loadname = mod_dispname.replace(self.module_delimiter, '_')
                        mod_loadpath = os.path.join(dirpath, filename)
                        mod_file = open(mod_loadpath, 'rb')
                        try:
                            imp.load_source(mod_loadname, mod_loadpath, mod_file)
                            __import__(mod_loadname)
                            self.loaded_category[mod_category].append(mod_loadname)
                            self.loaded_modules[mod_dispname] = mod_loadname
                        except:
                            print('-'*60)
                            traceback.print_exc()
                            print('-'*60)
                            self.error('Unable to load module: %s' % (mod_name))

    def load_keys(self):
        key_path = '%s/keys.dat' % (self.home)
        if os.path.exists(key_path):
            try:
                key_data = json.loads(open(key_path, 'rb').read())
                for key in key_data: self.keys[key] = key_data[key]
            except:
                self.error('Corrupt key file.')

    def show_banner(self):
        banner = open('./core/banner').read()
        banner_len = len(max(banner.split('\n'), key=len))
        print(banner)
        print('{0:^{1}}'.format('%s[%s v%s, %s]%s' % (O, self.name, __version__, __author__, N), banner_len+8)) # +8 compensates for the color bytes
        print('')
        counts = [(len(self.loaded_category[x]), x) for x in self.loaded_category]
        count_len = len(max([str(x[0]) for x in counts], key=len))
        for count in sorted(counts, reverse=True):
            cnt = '[%d]' % (count[0])
            print('%s%s %s modules%s' % (B, cnt.ljust(count_len+2), count[1].title(), N))
            # create dynamic easter egg command based on counts
            setattr(self, 'do_%d' % count[0], self.menu_egg)
        print('')

    def menu_egg(self, params):
        eggs = [
                'Really? A menu option? Try again.',
                'You clearly need \'help\'.',
                'That makes no sense to me.',
                '*grunt* *grunt* Nope. I got nothin\'.',
                'Wait for it...',
                'This is not the Social Engineering Toolkit.',
                'Don\'t you think if that worked the numbers would at least be in order?',
                'Reserving that option for the next-NEXT generation of the framework.',
                'You\'ve clearly got the wrong framework. Attempting to start SET...',
                'Your mother called. She wants her menu driven UI back.',
                'What\'s the samurai password?'
                ]
        print(random.choice(eggs))
        return 

    def init_workspace(self, workspace):
        workspace = '%s/workspaces/%s' % (self.home, workspace)
        try:
            os.makedirs(workspace)
        except OSError as e:
            if e.errno != errno.EEXIST:
                self.error(e.__str__())
                return False
        self.workspace = __builtin__.workspace = workspace
        self.prompt = self.prompt_template % (self.base_prompt[:-3], self.workspace.split('/')[-1])
        self.query('CREATE TABLE IF NOT EXISTS hosts (host TEXT, ip_address TEXT, region TEXT, country TEXT, latitude TEXT, longitude TEXT)')
        self.query('CREATE TABLE IF NOT EXISTS contacts (fname TEXT, lname TEXT, email TEXT, title TEXT, region TEXT, country TEXT)')
        self.query('CREATE TABLE IF NOT EXISTS creds (username TEXT, password TEXT, hash TEXT, type TEXT, leak TEXT)')
        self.query('CREATE TABLE IF NOT EXISTS pushpin (source TEXT, screen_name TEXT, profile_name TEXT, profile_url TEXT, media_url TEXT, thumb_url TEXT, message TEXT, latitude TEXT, longitude TEXT, time TEXT)')
        self.query('CREATE TABLE IF NOT EXISTS dashboard (module TEXT PRIMARY KEY, runs INT)')
        self.init_global_options()
        self.load_config()
        return True

    #==================================================
    # COMMAND METHODS
    #==================================================

    def do_reload(self, params):
        '''Reloads all modules'''
        self.load_modules(True)

    def do_info(self, params):
        '''Displays module information'''
        if not params:
            self.help_info()
            return
        try:
            modulename = self.loaded_modules[params]
            y = sys.modules[modulename].Module((None, params))
            y.do_info(None)
        except (KeyError, AttributeError):
            self.error('Invalid module name.')

    def do_banner(self, params):
        '''Displays the banner'''
        self.show_banner()

    def do_workspace(self, params):
        '''Sets the workspace'''
        if not params:
            self.help_workspace()
            return
        if not self.init_workspace(params):
            self.error('Unable to create \'%s\' workspace.' % (value))

    def do_load(self, params):
        '''Loads selected module'''
        try: self.validate_options()
        except framework.FrameworkException as e:
            self.error(e.message)
            return
        if not params:
            self.help_load()
            return
        # finds any modules that contain params
        modules = [params] if params in self.loaded_modules else [x for x in self.loaded_modules if params in x]
        # notify the user if none or multiple modules are found
        if len(modules) != 1:
            if not modules:
                self.error('Invalid module name.')
            else:
                self.output('Multiple modules match \'%s\'.' % params)
                self.display_modules(modules)
            return
        modulename = modules[0]
        loadedname = self.loaded_modules[modulename]
        prompt = self.prompt_template % (self.prompt[:-3], modulename.split(self.module_delimiter)[-1])
        # notify the user if runtime errors exist in the module
        try: y = sys.modules[loadedname].Module((prompt, modulename))
        except Exception:
            if self.options['debug']:
                print('%s%s' % (R, '-'*60))
                traceback.print_exc()
                print('%s%s' % ('-'*60, N))
            self.error('ModuleError: %s' % (traceback.format_exc().splitlines()[-1]))
            return
        # return the loaded module if in command line mode
        if self.mode == 1: return y
        try: y.cmdloop()
        except KeyboardInterrupt:
            print('')
    do_use = do_load

    def do_run(self, params):
        '''Not available'''
        self.output('Command \'run\' reserved for future use.')

    #==================================================
    # HELP METHODS
    #==================================================

    def help_info(self):
        print('Usage: info <module>')

    def help_workspace(self):
        print('Usage: workspace <string>')

    #==================================================
    # COMPLETE METHODS
    #==================================================

    def complete_workspace(self, text, *ignored):
        path = '%s/workspaces' % (self.home)
        return [name for name in os.listdir(path) if name.startswith(text) and os.path.isdir('%s/%s' % (path, name))]
