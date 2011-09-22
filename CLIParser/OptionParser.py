import sys
import time
import logging
import logging.handlers
import re
try:
    import curses
except:
    curses = None

class OptionParser(object):
    class _CliOpts(dict):
        @classmethod
        def instance(cls):
            if not hasattr(cls, "_instance"):
                cls._instance = cls()
            return cls._instance
    
        def __getattr__(self, name):
            if isinstance(self.get(name), OptionParser._CliOpt):
                return self[name].value()
            raise AttributeError("Unrecognized option %r" % name)
    
    
    class _CliOpt(object):
        def __init__(self, name, default=None, type=str, help=None, metavar=None,
                     multiple=False, file_name=None):
            if default is None and multiple:
                default = []
            self.name = name
            self.type = type
            self.help = help
            self.metavar = metavar
            self.multiple = multiple
            self.file_name = file_name
            self.default = default
            self._value = None
    
        def value(self):
            if self._value is None:
                return self.default
            else:
                return self._value
    
    
        def parse(self, value):
            _parse = {
                bool: self._parse_bool,
                str: self._parse_string,
            }.get(self.type, self.type)
            if self.multiple:
                if self._value is None:
                    self._value = []
                for part in value.split(","):
                    if self.type in (int, long):
                        lo, _, hi = part.partition(":")
                        lo = _parse(lo)
                        hi = _parse(hi) if hi else lo
                        self._value.extend(range(lo, hi+1))
                    else:
                        self._value.append(_parse(part))
            else:
                self._value = _parse(value)
            return self.value()
    
        def set(self, value):
            if self.multiple:
                if not isinstance(value, list):
                    raise OptionParser.Error("Option %r is required to be a list of %s" %
                                (self.name, self.type.__name__))
                for item in value:
                    if item != None and not isinstance(item, self.type):
                        raise OptionParser.Error("Option %r is required to be a list of %s" %
                                    (self.name, self.type.__name__))
            else:
                if value != None and not isinstance(value, self.type):
                    raise OptionParser.Error("Option %r is required to be a %s" %
                                (self.name, self.type.__name__))
            self._value = value
    
        
        def _parse_bool(self, value):
            return value.lower() not in ("false", "0", "f")
    
        def _parse_string(self, value):
            return value.decode("utf-8")
    
    class Error(Exception):
        pass
    
    class _LogFormatter(logging.Formatter):
        def __init__(self, color, *args, **kwargs):
            logging.Formatter.__init__(self, *args, **kwargs)
            self._color = color
            if color:
                fg_color = curses.tigetstr("setaf") or curses.tigetstr("setf") or ""
                self._colors = {
                        logging.DEBUG: curses.tparm(fg_color, 4), # Blue
                        logging.INFO: curses.tparm(fg_color, 2), # Green
                        logging.WARNING: curses.tparm(fg_color, 3), # Yellow
                        logging.ERROR: curses.tparm(fg_color, 1), # Red
                    }
                self._normal = curses.tigetstr("sgr0")
        
        def format(self, record):
            try:
                record.message = record.getMessage()
            except Exception, e:
                record.message = "Bad message (%r): %r" % (e, record.__dict__)
            record.asctime = time.strftime(
                    "%y-%m-%d %H:%M:%S", self.converter(record.created))
            if record.__dict__['levelname'] == "ERROR":
                prefix = '[%(levelname)s %(asctime)s %(module)s (%(lineno)d)]' % \
                    record.__dict__
            else:
                prefix = '[%(levelname)s %(asctime)s %(module)s]' % \
                    record.__dict__  
            if self._color:
                prefix = (self._colors.get(record.levelno, self._normal) +
                              prefix + self._normal)
            formatted = prefix + " " + record.message
            if record.exc_info:
                if not record.exc_text:
                    record.exc_text = self.formatException(record.exc_info)
            if record.exc_text:
                formatted = formatted.rstrip() + "\n" + record.exc_text
            return formatted.replace("\n", "\n    ")
    
    @classmethod
    def instance(cls, params=None):
        if not hasattr(cls, "_instance"):
            if params is None:
                cls._instance = cls()
            else:
                cls._instance = cls(params)
        return cls._instance
    
    def __init__(self, params=None):
        self.options = OptionParser._CliOpts.instance()
        self.params = params
    
    def option(self,name, default=None, type=str, help=None, metavar=None,
           multiple=False):
        if name in self.options:
            raise OptionParser.Error("Option %r already defined in %s", name,
                        self.options[name].file_name)
        frame = sys._getframe(0)
        options_file = frame.f_code.co_filename
        file_name = frame.f_back.f_code.co_filename
        if file_name == options_file: file_name = ""
        self.options[name] = OptionParser._CliOpt(name, file_name=file_name, default=default,
                                type=type, help=help, metavar=metavar,
                                multiple=multiple)
    
    
    def parse_command_line(self,args=None):
        if args is None: args = sys.argv
        remaining = []
        for i in xrange(1, len(args)):
            if not args[i].startswith("-"):
                remaining = args[i:]
                break
            if args[i] == "--":
                remaining = args[i+1:]
                break
            arg = args[i].lstrip("-")
            name, equals, value = arg.partition("=")
            name = name.replace('-', '_')
            if not name in self.options:
                self.print_help()
                raise OptionParser.Error('Unrecognized command line option: %r' % name)
            option = self.options[name]
            if not equals:
                if option.type == bool:
                    value = "true"
                else:
                    raise OptionParser.Error('Option %r requires a value' % name)
            option.parse(value)
        if self.options.help:
            self.print_help()
            sys.exit(0)
    
        if self.options.logging != 'none':
            logging.getLogger().setLevel(getattr(logging, self.options.logging.upper()))
            self.enable_pretty_logging()
    
        return remaining   
    
    def parse_config_file(self,path):
        config = {}
        execfile(path,config,config)
        for name in config:
            if name in self.options:
                self.options[name].set(config[name])
    
    def print_help(self,file=sys.stdout):
        if self.params is not None:
            print >> file, "Usage: %s [OPTIONS] %s" % (sys.argv[0],self.params)
        else:
            print >> file, "Usage: %s [OPTIONS]" % sys.argv[0]
        print >> file, ""
        print >> file, "Options:"
        by_file = {}
        for option in self.options.itervalues():
            by_file.setdefault(option.file_name, []).append(option)
    
        for filename, o in sorted(by_file.items()):
            if filename: print >> file, filename
            o.sort(key=lambda option: option.name)
            for option in o:
                prefix = option.name
                if option.metavar:
                    prefix += "=" + option.metavar
                print >> file, "  --%-30s %s" % (prefix, option.help or "")
        print >> file
        
    def enable_pretty_logging(self):
        root_logger = logging.getLogger()
        color = False
        if curses and sys.stderr.isatty():
            try:
                curses.setupterm()
                if curses.tigetnum("colors") > 0:
                    color = True
            except:
                pass
        channel = logging.StreamHandler()
        channel.setFormatter(OptionParser._LogFormatter(color=color))
        root_logger.addHandler(channel)