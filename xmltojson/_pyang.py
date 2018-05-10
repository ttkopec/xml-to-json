import sys
import os
import optparse
import io
import pyang
import re
from pyang import plugin
from pyang import error
from pyang import hello

if sys.version < '3':
    import codecs


def run(models, format, output_file, yang_directory, **options):
    usage = """%prog [options] [<filename>...]

Validates the YANG module in <filename> (or stdin), and all its dependencies."""

    if len(plugin.plugins) < 1:
        plugindirs = []
        # check for --plugindir
        idx = 1
        while '--plugindir' in sys.argv[idx:]:
            idx = idx + sys.argv[idx:].index('--plugindir')
            plugindirs.append(sys.argv[idx + 1])
            idx = idx + 1
        plugin.init(plugindirs)

    fmts = {}
    for p in plugin.plugins:
        p.add_output_format(fmts)

    optlist = [
        # use capitalized versions of std options help and version
        optparse.make_option("-h", "--help",
                             action="help",
                             help="Show this help message and exit"),
        optparse.make_option("-v", "--version",
                             action="version",
                             help="Show version number and exit"),
        optparse.make_option("-V", "--verbose",
                             action="store_true"),
        optparse.make_option("-e", "--list-errors",
                             dest="list_errors",
                             action="store_true",
                             help="Print a listing of all error and warning " \
                                  "codes and exit."),
        optparse.make_option("--print-error-code",
                             dest="print_error_code",
                             action="store_true",
                             help="On errors, print the error code instead " \
                                  "of the error message."),
        optparse.make_option("-W",
                             dest="warnings",
                             action="append",
                             default=[],
                             metavar="WARNING",
                             help="If WARNING is 'error', treat all warnings " \
                                  "as errors, except any listed WARNING. " \
                                  "If WARNING is 'none', do not report any " \
                                  "warnings."),
        optparse.make_option("-E",
                             dest="errors",
                             action="append",
                             default=[],
                             metavar="WARNING",
                             help="Treat each WARNING as an error.  For a " \
                                  "list of warnings, use --list-errors."),
        optparse.make_option("--ignore-error",
                             dest="ignore_error_tags",
                             action="append",
                             default=[],
                             metavar="ERROR",
                             help="Ignore ERROR.  Use with care.  For a " \
                                  "list of errors, use --list-errors."),
        optparse.make_option("--ignore-errors",
                             dest="ignore_errors",
                             action="store_true",
                             help="Ignore all errors.  Use with care."),
        optparse.make_option("--canonical",
                             dest="canonical",
                             action="store_true",
                             help="Validate the module(s) according to the " \
                                  "canonical YANG order."),
        optparse.make_option("--max-line-length",
                             type="int",
                             dest="max_line_len"),
        optparse.make_option("--max-identifier-length",
                             type="int",
                             dest="max_identifier_len"),
        optparse.make_option("-f", "--format",
                             dest="format",
                             default=format,
                             help="Convert to FORMAT.  Supported formats " \
                                  "are: " + ', '.join(list(fmts.keys()))),
        optparse.make_option("-o", "--output",
                             dest="outfile",
                             default=output_file,
                             help="Write the output to OUTFILE instead " \
                                  "of stdout."),
        optparse.make_option("-F", "--features",
                             metavar="FEATURES",
                             dest="features",
                             default=[],
                             action="append",
                             help="Features to support, default all. " \
                                  "<modname>:[<feature>,]*"),
        optparse.make_option("", "--max-status",
                             metavar="MAXSTATUS",
                             dest="max_status",
                             help="Max status to support, one of: " \
                                  "current, deprecated, obsolete"),
        optparse.make_option("", "--deviation-module",
                             metavar="DEVIATION",
                             dest="deviations",
                             default=[],
                             action="append",
                             help="Deviation module"),
        optparse.make_option("-p", "--path",
                             dest="path",
                             default=[yang_directory],
                             action="append",
                             help=os.pathsep + "-separated search path for yin"
                                               " and yang modules"),
        optparse.make_option("--plugindir",
                             dest="plugindir",
                             help="Load pyang plugins from PLUGINDIR"),
        optparse.make_option("--strict",
                             dest="strict",
                             action="store_true",
                             help="Force strict YANG compliance."),
        optparse.make_option("--lax-quote-checks",
                             dest="lax_quote_checks",
                             action="store_true",
                             help="Lax check of backslash in quoted strings."),
        optparse.make_option("--lax-xpath-checks",
                             dest="lax_xpath_checks",
                             action="store_true",
                             help="Lax check of XPath expressions."),
        optparse.make_option("--trim-yin",
                             dest="trim_yin",
                             action="store_true",
                             help="In YIN input modules, trim whitespace "
                                  "in textual arguments."),
        optparse.make_option("-L", "--hello",
                             dest="hello",
                             action="store_true",
                             help="Filename of a server's hello message is "
                                  "given instead of module filename(s)."),
        optparse.make_option("--keep-comments",
                             dest="keep_comments",
                             action="store_true",
                             help="Pyang will not discard comments; \
                                   has effect if the output plugin can \
                                   handle comments."),
        optparse.make_option("--no-path-recurse",
                             dest="no_path_recurse",
                             action="store_true",
                             help="Do not recurse into directories in the \
                                   yang path."),
    ]

    optparser = optparse.OptionParser(usage, add_help_option=False)
    optparser.version = '%prog ' + pyang.__version__
    optparser.add_options(optlist)

    for p in plugin.plugins:
        p.add_opts(optparser)

    (o, args) = optparser.parse_args()

    for key, val in options.items():
        setattr(o, key, val)

    args = models

    if o.list_errors:
        for tag in error.error_codes:
            (level, fmt) = error.error_codes[tag]
            if error.is_warning(level):
                print("Warning: %s" % tag)
            elif error.allow_warning(level):
                print("Minor Error:   %s" % tag)
            else:
                print("Error:   %s" % tag)
            print("Message: %s" % fmt)
            print("")
        sys.exit(0)

    if o.outfile is not None and o.format is None:
        sys.stderr.write("no format specified\n")
        sys.exit(1)

    # patch the error spec so that -W errors are treated as warnings
    for w in o.warnings:
        if w in error.error_codes:
            (level, wstr) = error.error_codes[w]
            if error.allow_warning(level):
                error.error_codes[w] = (4, wstr)

    filenames = args

    # Parse hello if present
    if o.hello:
        if len(filenames) > 1:
            sys.stderr.write("multiple hello files given\n")
            sys.exit(1)
        if filenames:
            try:
                fd = open(filenames[0], "rb")
            except IOError as ex:
                sys.stderr.write("error %s: %s\n" % (filenames[0], str(ex)))
                sys.exit(1)
        elif sys.version < "3":
            fd = sys.stdin
        else:
            fd = sys.stdin.buffer
        hel = hello.HelloParser().parse(fd)

    path = os.pathsep.join(o.path)

    # add standard search path
    if len(o.path) == 0:
        path = "."
    else:
        path += os.pathsep + "."

    repos = pyang.FileRepository(path, no_path_recurse=o.no_path_recurse)

    ctx = pyang.Context(repos)

    ctx.opts = o
    ctx.canonical = o.canonical
    ctx.max_line_len = o.max_line_len
    ctx.max_identifier_len = o.max_identifier_len
    ctx.trim_yin = o.trim_yin
    ctx.lax_xpath_checks = o.lax_xpath_checks
    ctx.lax_quote_checks = o.lax_quote_checks
    ctx.strict = o.strict
    ctx.max_status = o.max_status

    # make a map of features to support, per module
    if o.hello:
        for (mn, rev) in hel.yang_modules():
            ctx.features[mn] = hel.get_features(mn)
    for f in ctx.opts.features:
        (modulename, features) = parse_features_string(f)
        ctx.features[modulename] = features

    for p in plugin.plugins:
        p.setup_ctx(ctx)

    if o.format is not None:
        if o.format not in fmts:
            sys.stderr.write("unsupported format '%s'\n" % o.format)
            sys.exit(1)
        emit_obj = fmts[o.format]
        if o.keep_comments and emit_obj.handle_comments:
            ctx.keep_comments = True
        emit_obj.setup_fmt(ctx)
    else:
        emit_obj = None

    for p in plugin.plugins:
        p.pre_load_modules(ctx)

    exit_code = 0
    modules = []

    if o.hello:
        ctx.capabilities = hel.registered_capabilities()
        for (mn, rev) in hel.yang_modules():
            mod = ctx.search_module(0, mn, rev)
            if mod is None:
                emarg = mn
                if rev:
                    emarg += "@" + rev
                sys.stderr.write(
                    "module '%s' specified in hello not found.\n" % emarg)
                sys.exit(1)
            modules.append(mod)
    else:
        if len(filenames) == 0:
            text = sys.stdin.read()
            module = ctx.add_module('<stdin>', text)
            if module is None:
                exit_code = 1
            else:
                modules.append(module)
        if (len(filenames) > 1 and
                emit_obj is not None and
                not emit_obj.multiple_modules):
            sys.stderr.write("too many files to convert\n")
            sys.exit(1)

        r = re.compile(r"^(.*?)(\@(\d{4}-\d{2}-\d{2}))?\.(yang|yin)$")
        for filename in filenames:
            try:
                fd = io.open(filename, "r", encoding="utf-8")
                text = fd.read()
            except IOError as ex:
                sys.stderr.write("error %s: %s\n" % (filename, str(ex)))
                sys.exit(1)
            except UnicodeDecodeError as ex:
                s = str(ex).replace('utf-8', 'utf8')
                sys.stderr.write("%s: unicode error: %s\n" % (filename, s))
                sys.exit(1)
            m = r.search(filename)
            ctx.yin_module_map = {}
            if m is not None:
                (name, _dummy, rev, format) = m.groups()
                name = os.path.basename(name)
                module = ctx.add_module(filename, text, format, name, rev,
                                        expect_failure_error=False)
            else:
                module = ctx.add_module(filename, text)
            if module is None:
                exit_code = 1
            else:
                modules.append(module)

    modulenames = []
    for m in modules:
        modulenames.append(m.arg)
        for s in m.search('include'):
            modulenames.append(s.arg)

    # apply deviations
    for filename in ctx.opts.deviations:
        try:
            fd = io.open(filename, "r", encoding="utf-8")
            text = fd.read()
        except IOError as ex:
            sys.stderr.write("error %s: %s\n" % (filename, str(ex)))
            sys.exit(1)
        except UnicodeDecodeError as ex:
            s = str(ex).replace('utf-8', 'utf8')
            sys.stderr.write("%s: unicode error: %s\n" % (filename, s))
            sys.exit(1)
        m = ctx.add_module(filename, text)
        if m is not None:
            ctx.deviation_modules.append(m)

    for p in plugin.plugins:
        p.pre_validate_ctx(ctx, modules)

    if emit_obj is not None and len(modules) > 0:
        emit_obj.pre_validate(ctx, modules)

    ctx.validate()

    # verify the given features
    for m in modules:
        if m.arg in ctx.features:
            for f in ctx.features[m.arg]:
                if f not in m.i_features:
                    sys.stderr.write("unknown feature %s in module %s\n" %
                                     (f, m.arg))
                    sys.exit(1)

    if emit_obj is not None and len(modules) > 0:
        emit_obj.post_validate(ctx, modules)

    for p in plugin.plugins:
        p.post_validate_ctx(ctx, modules)

    def keyfun(e):
        if e[0].ref == filenames[0]:
            return 0
        else:
            return 1

    ctx.errors.sort(key=lambda e: (e[0].ref, e[0].line))
    if len(filenames) > 0:
        # first print error for the first filename given
        ctx.errors.sort(key=keyfun)

    if o.ignore_errors:
        ctx.errors = []

    for (epos, etag, eargs) in ctx.errors:
        if etag in o.ignore_error_tags:
            continue
        if (ctx.implicit_errors is False and
                hasattr(epos.top, 'i_modulename') and
                epos.top.arg not in modulenames and
                epos.top.i_modulename not in modulenames and
                epos.ref not in filenames):
            # this module was added implicitly (by import); skip this error
            # the code includes submodules
            continue
        elevel = error.err_level(etag)
        if error.is_warning(elevel) and etag not in o.errors:
            kind = "warning"
            if 'error' in o.warnings and etag not in o.warnings:
                kind = "error"
                exit_code = 1
            elif 'none' in o.warnings:
                continue
        else:
            kind = "error"
            exit_code = 1
        if o.print_error_code is True:
            sys.stderr.write(str(epos) + ': %s: %s\n' % (kind, etag))
        else:
            sys.stderr.write(str(epos) + ': %s: ' % kind +
                             error.err_to_str(etag, eargs) + '\n')

    if emit_obj is not None and len(modules) > 0:
        tmpfile = None
        if o.outfile is None:
            if sys.version < '3':
                fd = codecs.getwriter('utf8')(sys.stdout)
            else:
                fd = sys.stdout
        else:
            tmpfile = o.outfile + ".tmp"
            if sys.version < '3':
                fd = codecs.open(tmpfile, "w+", encoding="utf-8")
            else:
                fd = io.open(tmpfile, "w+", encoding="utf-8")
        try:
            emit_obj.emit(ctx, modules, fd)
        except error.EmitError as e:
            if e.msg != "":
                sys.stderr.write(e.msg + '\n')
            if tmpfile is not None:
                fd.close()
                os.remove(tmpfile)
            sys.exit(e.exit_code)
        except:
            if tmpfile is not None:
                fd.close()
                os.remove(tmpfile)
            raise
        if tmpfile is not None:
            fd.close()
            os.rename(tmpfile, o.outfile)

    if exit_code != 0:
        sys.exit(exit_code)


def parse_features_string(s):
    if s.find(':') == -1:
        return s, []
    else:
        [modulename, rest] = s.split(':', 1)
        if rest == '':
            return modulename, []
        else:
            features = rest.split(',')
            return modulename, features
